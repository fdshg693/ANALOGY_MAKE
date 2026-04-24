# PHASE8.0: 調査・実験を挟む実装 workflow と長時間タスク委譲/コスト可視化

`question` workflow により「実装しない調査」は分離できたが、「最終的には実装するが、その前に外部調査や実験検証を挟むべき課題」はまだ `full` workflow の中で十分に表現できていない。また、インフラ作業や重いテストのような長時間コマンドは Claude セッションを張り付かせたまま待つしかなく、実行コストと運用負荷が高い。PHASE8.0 では、調査・検証を正式な step として扱う新しい実装 workflow を追加し、その器の上で長時間コマンド委譲と step 単位の token cost 計測を整える。

## 実装進捗

| 節 | 内容 | 状態 | 想定バージョン |
|---|---|---|---|
| §1 | 調査・実験を挟む実装 workflow（仮称 `research`）追加 | ✅ 実装済み（ver16.0、2026-04-24） | ver16.0 |
| §2 | 長時間コマンドを登録・委譲・再開する deferred execution 追加 | ✅ 実装済み（ver16.1、2026-04-24） | ver16.1 |
| §3 | step 単位の token/cost 計測と workflow 比較ログ追加 | 未着手 | ver16.2 |

想定分割は ver16.0〜ver16.2 の 3 段階とし、まず §1 で「調べてから実装する」器を正式な workflow として追加し、その上で §2 の長時間タスク委譲、最後に §3 の cost 可視化で増えた step の妥当性を評価できる状態へ寄せる。特に §2 の対象は事前調査・試行を挟む価値が高いため、PHASE8.0 では §1 を最初に実装するのを推奨する。

## 概要

PHASE8.0 の主眼は 3 つある。第 1 に、`quick` / `full` / `question` / `scout` のあいだに残っていた「実装するが、いきなりコードに入るには不確実性が高い」課題向けの workflow を新設すること。第 2 に、Claude が長時間コマンドの登録だけ行って一度終了し、その後は Python 側がコマンド実行と結果保存を担当し、完了後に同じ session へ戻す仕組みを作ること。第 3 に、各 step の token 使用量と cost を記録し、新しい workflow や追加 step が本当に見合っているかを後から判断できるようにすること。`question` が「実装しない調査」であるのに対し、本フェーズの新 workflow は「実装に入る前の調査・検証を formalize する」ためのものという違いがある。

## 動機

- 現行 `full` workflow は `/split_plan` の次が `/imple_plan` であり、外部 API 調査・仕様確認・再現実験が必要な課題でも、計画と実装のあいだに正式な検証 step がない
- `question` workflow は報告書で完了するため、最終的にコードを変更したい課題までそこへ流すと queue の責務が崩れる
- インフラ操作、重いテスト、長めの検証スクリプトは Claude セッションを待機状態で抱え続けがちで、90 秒ごとの見守りのような高コスト運用になりやすい
- `experiments/` は存在するが、依存関係や一時スクリプトをどの粒度で残してよいかの運用ルールが明文化されていない
- 現在の workflow log からは所要時間は追えるが、step ごとの token 使用量や金額換算は残らないため、`quick` / `full` / 新 workflow の費用対効果を比較できない
- PHASE8.0 で扱う後半 2 項目自体が調査・試行を要するため、先にそれを支える workflow を整備したほうが後続実装の失敗コストを下げられる

## 前提条件

- PHASE7.1 までで `question` / `scout` / `quick` / `full` の各 workflow と `--workflow auto` の基本分岐が安定していること
- `scripts/claude_loop.py` が `ROUGH_PLAN.md` frontmatter の `workflow:` を読んで後続 YAML を切り替えられること
- `continue: true` / `claude -r <session-id>` により、session 継続実行の基盤が既にあること
- `.claude/SKILLS/use-tavily/` が存在し、Web 調査を project-specific なラッパー経由で行えること
- `experiments/` ディレクトリが既にあり、実験スクリプトの配置先を新設せずに運用ルールだけを追加しやすいこと
- `scripts/tests/` に CLI / workflow / notify / integration テスト基盤があり、新モジュール追加後も unittest で検証を広げられること

## やること

### 1. 調査・実験を挟む実装 workflow（仮称 `research`）を追加する（**ver16.0 で実装済み、2026-04-24**）

#### 1-1. 役割

- `research` workflow は「最終的には実装まで進むが、実装前に調査と実験を formalize したい」課題向けの第 3 の実装 workflow とする。`question` のような報告書-only flow ではなく、同一 run の後半で `/imple_plan` まで進む
- 想定ステップは `/issue_plan -> /split_plan -> /research_context -> /experiment_test -> /imple_plan -> /wrap_up -> /write_current -> /retrospective` の 8 段構成とし、現行 `full` の `/split_plan` と `/imple_plan` のあいだに調査・検証 step を挿入する
- `--workflow auto` の自動選択肢は `quick | full` から `quick | full | research` へ拡張し、`/issue_plan` が `ROUGH_PLAN.md` frontmatter に `workflow: research` を書けるようにする
- `workflow: research` の選定条件は、少なくとも「外部仕様や公式 docs の確認が主要成果に影響する」「実装方式を実験で絞り込む必要がある」「長時間コマンドを使った検証が前半で必要」「既存 repo 依存の外に軽い隔離環境を作って試したい」のいずれかを含む場合とする
- `/split_plan` は従来どおり `REFACTOR.md` / `IMPLEMENT.md` を主成果物としつつ、未解決論点や仮説を `IMPLEMENT.md` の専用節へ残し、後続の `/research_context` と `/experiment_test` がそれを解決する流れにする
- `/research_context`（仮称）は repo 内コード・既存 docs・過去 version docs を先に確認し、それで足りない場合に `.claude/SKILLS/use-tavily` を前提に外部調査を行う。成果は `RESEARCH.md`（仮称）に、問い・根拠・結論・未解決点の形で残す
- `/experiment_test`（仮称）は再現スクリプト、性能確認、CLI 試行、インフラ dry-run などの「実装前に確かめるべきこと」を `experiments/` 配下で実行し、成果を `EXPERIMENT.md`（仮称）へ残す
- `experiments/` の利用ルールは明文化する。既存依存で足りる場合はそのまま使い、新しい依存が必要な場合でも `.venv` や一時 `package.json` は `experiments/` 配下で極力閉じる。後続のために実験スクリプトを残す場合は、ファイル先頭コメントに「何を確かめるためのスクリプトか」「いつ削除してよいか」を必ず書く
- `/imple_plan` は `IMPLEMENT.md` に加えて `RESEARCH.md` / `EXPERIMENT.md` を入力として読み、調査・実験結果を踏まえた実装へ進む。調査・実験の結果で計画が変わった場合は `MEMO.md` に乖離理由を残す

#### 1-2. 完了条件

- `--workflow research` で明示起動でき、`--workflow auto` でも `workflow: research` を選択されうる
- `question` と `research` の責務境界が docs / SKILL / README で明確になり、「実装しない調査」と「実装前調査」が混ざらない
- 調査成果と実験成果が `RESEARCH.md` / `EXPERIMENT.md` のような artifact として残り、`/imple_plan` から再利用できる
- `experiments/` 配下の依存・一時スクリプトの置き場がルール化され、repo ルートの依存関係や不要ファイルを増やしにくい
- §2 のような長時間コマンドを使う検証も、この workflow 上で自然に前半 step へ組み込める

### 2. 長時間コマンドを登録・委譲・再開する deferred execution を追加する

#### 2-1. 期待される実行フロー

- Claude Code は workflow 実行中に「長時間タスクとして外出ししたいコマンド群」を構造化ファイルとして登録できるようにする。登録情報には少なくとも、元 step 名、session ID、作業ディレクトリ、実行コマンド群、期待する成果物、結果出力先、再開時に必要な補足メモを含める
- 登録完了後、Claude Code はその step を「外部実行待ち」で一旦終了する。以後の長時間待機や定期 polling は Python 側ランナーが担当し、Claude セッションは占有しない
- 自動化スクリプトは登録ファイルを検知したらコマンド群を順次実行し、stdout / stderr とメタデータを結果ファイルへ保存する。結果ファイルの先頭または sidecar から、元のコマンド列・実行時刻・終了コードが分かるようにする
- 実行後は登録ファイルを必ず削除し、pending queue に残し続けない。成功・失敗どちらでも「実行済み request が残らない」ことを優先し、必要な調査材料は結果ファイル側へ残す
- 実行完了後、自動化スクリプトは `claude -r <session-id>` による session 再開を行い、「結果ファイル path」「文字数またはサイズ」「終了コード」「必要なら先頭サマリ」を追加情報として渡す。巨大ログ全文は直接 prompt に貼らず、Claude 側に必要部分だけ読ませる
- 非ゼロ終了やタイムアウトでも resume 経路は共通化し、Claude 側が「結果を読んで次の判断をする失敗」と「workflow 自体を止めるべき失敗」を切り分けられるようにする
- 登録対象は単発コマンドに限定せず、インフラ操作・重いテスト・ベンチマークなどを表す「コマンド群」を許可する。ただし、再実行時の事故を避けるため request schema は明示的に保ち、曖昧な自由記述 shell script をそのまま埋め込む設計にはしない

#### 2-2. 自動化スクリプト自身の長時間テストへの波及

- deferred execution が入ると、将来的には `quick` / `full` workflow 自身の長時間 end-to-end テストを外部ランナーへ逃がしやすくなる
- ただし本フェーズでは、workflow 自身のセルフホスト実行は **可能性の探索と小さな試行まで** に留める。既存 workflow と混線しやすく、自己再起動のパラドックスもあるため、本実装まで一気に踏み込まない
- 調査対象は、専用 fixture/worktree を使うか、専用フォルダで模擬 queue を回すか、wrapper script や file watcher で再開を橋渡しするか、といった実現方式の比較に留める
- 本番運用の `ISSUES/` / `QUESTIONS/` / `FEEDBACKS/` / `logs/workflow/` と同じ場所をそのまま自己テストで共有しない

#### 2-3. 完了条件

- 1 件の registered command set を、登録 -> 外部実行 -> 結果保存 -> request 削除 -> session 再開まで無人で完走できる
- 結果ファイルだけを見て、何のコマンドが走ったか、成功したか、出力が大きいかを判断できる
- 90 秒ごとの見守りや Claude の長時間待機なしで、インフラ作業や重い検証を run に取り込める
- 失敗時も orphan request が残らず、resume 時に必要な情報が欠けない
- workflow 自己テストについては「有望な方式と避けるべき方式」が docs / experiments に整理されるが、標準 workflow や CI への常時組み込みまでは行わない

### 3. step 単位の token/cost 計測を追加し workflow 比較可能にする

#### 3-1. 計測対象

- 各 Claude 実行 step ごとに、少なくとも workflow 種別、step 名、model、session ID、開始/終了時刻、duration、input/output token 数、利用可能なら cache read/write 相当量、金額換算値を記録する
- 計測値は human-readable な workflow log に要約を残すだけでなく、後から集計できる machine-readable な sidecar（JSON など）にも保存する
- token/cost の取得は Claude の usage/billing 系 API またはそれに準ずる取得経路を前提とし、ログ本文の文字数や推定式だけで済ませない
- 単価テーブルや価格改定への追随方法も決めておき、「どの価格表で計算した cost か」が後から分かるようにする
- `quick` / `full` / `research` を比較できるよう、run total と step 別明細の両方を残す。特に `research` workflow の追加 step が、障害回避や手戻り削減に見合う cost かを retrospective で判断できる形にする
- deferred execution による外部コマンド待機時間は token cost と混同せず、duration と cost を別軸で扱う

#### 3-2. 完了条件

- Claude を呼ぶ全 step について token usage / cost が記録され、欠測時は「未取得」と理由が分かる
- 1 run 終了時に step 別・合計 cost を確認でき、workflow 間比較の材料に使える
- docs / tests / 実装で、価格計算の前提と更新方法が一致している
- §1 の `research` workflow を導入した結果、どの step が高くつくのかを振り返りで評価できる

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/claude_loop.py` | 変更予定 | `research` workflow 分岐、deferred execution 実行ライフサイクル、step cost 集計の追加 |
| `scripts/claude_loop_research.yaml` | 新規作成予定 | 調査・実験付き実装 workflow 定義 |
| `scripts/claude_loop_lib/workflow.py` | 変更予定 | `workflow: research` 解決、YAML 同期契約、artifact/frontmatter 拡張対応 |
| `scripts/claude_loop_lib/validation.py` | 変更予定 | 新 workflow 値、registered command schema、cost 設定の検証 |
| `scripts/claude_loop_lib/deferred_commands.py` | 新規作成予定 | request 登録、外部実行、結果保存、request 削除、resume 入力生成 |
| `scripts/claude_loop_lib/costs.py` | 新規作成予定 | Claude usage/cost 情報の取得、価格計算、run 集計 |
| `scripts/claude_loop_lib/logging_utils.py` | 変更予定 | deferred result / token cost / run summary のログ整形 |
| `scripts/tests/test_claude_loop_cli.py` | 変更予定 | `--workflow research` と auto 3 分岐のテスト追加 |
| `scripts/tests/test_claude_loop_integration.py` | 変更予定 | deferred execution -> resume の統合経路を検証 |
| `scripts/tests/test_deferred_commands.py` | 新規作成予定 | request cleanup・結果ファイル・resume 情報生成の単体テスト |
| `scripts/tests/test_costs.py` | 新規作成予定 | usage 取得・単価適用・欠測時フォールバックの単体テスト |
| `scripts/README.md` | 変更予定 | `research` workflow、`experiments/` 運用、deferred execution、cost log を説明 |
| `scripts/USAGE.md` | 変更予定 | `workflow: quick | full | research`、結果ファイル仕様、cost sidecar 仕様を追記 |
| `.claude/SKILLS/issue_plan/SKILL.md` | 変更予定 | `workflow: research` の選定条件と `ROUGH_PLAN.md` frontmatter 拡張 |
| `.claude/SKILLS/split_plan/SKILL.md` | 変更予定 | 未解決論点の整理、後続 `/research_context` / `/experiment_test` への handoff 追加 |
| `.claude/SKILLS/research_context/SKILL.md` | 新規作成予定 | `use-tavily` を前提にした実装前調査 step を定義 |
| `.claude/SKILLS/experiment_test/SKILL.md` | 新規作成予定 | `experiments/` 配下での再現・検証・依存隔離ルールを定義 |
| `.claude/SKILLS/imple_plan/SKILL.md` | 変更予定 | `RESEARCH.md` / `EXPERIMENT.md` と deferred 結果を読んで実装へ進む手順を追加 |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | 変更予定 | 実装 workflow を `quick` / `full` / `research` の 3 系統として再定義 |
| `.claude/rules/scripts.md` | 変更予定 | workflow YAML 同期対象の追加、deferred execution/cost log の stable rule 化 |
| `experiments/README.md` | 新規作成予定 | 実験ファイルの残し方、依存隔離、削除条件コメントの規約を明文化 |

## リスク・不確実性

- `research` workflow の選定基準が緩すぎると、`full` で十分な課題まで毎回 2 step 増えて run time と cost が肥大化する
- `question` と `research` の境界が曖昧だと、報告書だけで済む依頼や実装前提の課題が誤った queue に流れやすい
- `use-tavily` 前提の外部調査は API キー有無や検索品質に左右されるため、repo 内調査だけで完結できるケースとの使い分けを誤ると無駄打ちが増える
- `experiments/` の自由度を上げすぎると、一時依存・仮想環境・試行スクリプトが肥大化して保守対象化する。削除条件コメントと README 規約が弱いとすぐ崩れる
- deferred execution は queue file の削除タイミング、途中失敗、resume 失敗が絡むため、二重実行・orphan request・resume 先誤りのリスクがある
- 結果ファイルが巨大になると resume prompt へ直接流し込めず、文字数・サイズ・要約だけを渡す設計を徹底しないとコンテキストを圧迫する
- Claude の usage/cost 取得経路が CLI 実行単位と 1 対 1 に結び付かない場合、正確な step 別 cost の紐付けに追加設計が必要になる
- workflow 自己テストは本 workspace と queue を共有すると既存運用を汚染しやすく、専用 fixture や worktree を使わない設計は危険

## やらないこと

- `question` workflow を廃止したり、実装前調査をすべて `question` に寄せたりしない
- `research` workflow を `auto` の常時既定値にせず、必要条件を満たす課題だけに選択させる
- 新しい依存関係や仮想環境を repo ルートへ無秩序に増やさず、実験用隔離が必要なら `experiments/` 配下で閉じる
- 実行済みの registered command request を queue に残し続けない
- workflow 自己テストをこのフェーズで本番運用や CI の常時ジョブにまで広げない
- token cost ログを「将来も完全不変の請求正本」とはみなさず、価格表と取得元の前提を明示した運用記録として扱う