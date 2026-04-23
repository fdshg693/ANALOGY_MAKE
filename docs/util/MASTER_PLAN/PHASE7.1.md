# PHASE7.1: 探索・調査系ワークフロー追加と ROUGH_PLAN/通知運用の再整理

PHASE7.0 で workflow 設定、validation、FEEDBACK handoff、rules 配置を整理したあとに残る課題は、「何を実装する loop なのか」と「何を調べるだけの loop なのか」がまだ十分に分離されていないことにある。PHASE7.1 では、既存 backlog を消化する flow に加えて、潜在的な不具合やリファクタ候補を能動的に洗い出す flow と、実装を伴わず調査報告だけを返す Question flow を新設する。あわせて、`ROUGH_PLAN.md` に混在している計画本体と後続 handoff 情報を分離し、workflow 終了通知も「loop 単位」ではなく「Python スクリプト実行単位」で扱い直す。

## 実装進捗

| 節 | 内容 | 状態 | 想定バージョン |
|---|---|---|---|
| §1 | 潜在的なバグ・リファクタ候補を洗い出す `issue_scout` workflow 追加 | 実装済み（ver15.0） | ver15.0 |
| §2 | `QUESTIONS/` と調査専用 `question` workflow 追加 | 未着手 | ver15.1 |
| §3 | `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離 | 未着手 | ver15.1 |
| §4 | Python スクリプト終了時に 1 回だけ出す永続通知 | 未着手 | ver15.2 |

想定分割は ver15.0〜ver15.2 の 3 段階とし、まず探索系 workflow を追加し、その次に Question と plan artifact 分離を入れ、最後に通知仕様を run 単位へ整える。

## 概要

PHASE7.1 の主眼は、workflow automation の入口を 3 種類に分けることにある。第 1 に、既存の `ISSUES/` を起点として実装まで進む従来 flow（`auto` / `full` / `quick`）。第 2 に、まだ ISSUE 化されていない潜在的な問題を発見し、`ISSUES/` に起票するだけで止める探索 flow。第 3 に、人間の疑問や確認事項を調査し、コード変更なしで調査報告を返す Question flow である。さらに、`/issue_plan` が作る `ROUGH_PLAN.md` を「何をやるか」の文書に戻し、判断経緯や後続 step 向け補足は別ファイルへ逃がすことで、plan 文書の役割を明確化する。通知についても multi-loop 実行時のノイズを減らし、run 全体が終わった時点で 1 回だけ確実に気づける形へ寄せる。

## 動機

- 現状の workflow は、既に `ISSUES/` や `MASTER_PLAN` に現れている課題しか拾えず、大きな負債や構造的なリファクタ候補を能動的に探しにいかない
- 「まず調べたいだけ」の問いでも既存 ISSUE flow に載るため、調査だけで十分な依頼に対して実装寄りの重い step を回しがち
- `ROUGH_PLAN.md` がスコープ定義・判断理由・除外理由・後続 handoff を一度に抱え、読む側が「この版で何を達成する文書か」を見失いやすい
- 現行の Windows 通知は一定時間で消えるうえ、loop ごとに通知する設計だと `--max-loops 2` 以上の実行で完了把握がしづらい
- workflow 種別が増えるほど、「どの queue をどの flow が読むのか」「どこまで実装してよいのか」を docs で先に固定しておかないと運用がぶれやすい

## 前提条件

- PHASE7.0 までで `ISSUES/`, `FEEDBACKS/`, `.claude/rules/`, `/issue_plan`, `/retrospective` の基本運用が安定していること
- `scripts/claude_loop.py` が workflow YAML と `--workflow auto|full|quick|<path>` を起点に step 実行できること
- `ISSUES/README.md` と `issue_status.py` / `issue_worklist.py` によって、ISSUE の frontmatter 運用が既に確立していること
- `docs/{category}/ver*/ROUGH_PLAN.md` を `/split_plan` や `quick_impl` が主要入力として読んでいること
- 通知実装が現状 `scripts/claude_loop_lib/notify.py` に集約されており、run 完了時の呼び出し位置を整理しやすいこと

## やること

### 1. 潜在的なバグ・リファクタ候補を洗い出す `issue_scout` workflow を追加する

#### 1-1. 役割

- `issue_scout` は既存の `ready / ai` ISSUE を消化する flow ではなく、コードベース・tests・docs・直近 retrospective を読み、潜在的な問題を見つけて ISSUE 化する専用 workflow とする
- 本 workflow は明示実行専用とし、通常の `--workflow auto` に毎回自動混入させない。既存の実装 loop の責務を増やさず、定期監査や大きめの節目でのみ回す
- 出力は `ISSUES/{category}/{priority}/*.md` の新規起票と、その run の要約サマリに限定する。コード実装、テスト修正、デプロイ、バージョンドキュメント更新までは行わない
- AI が起票する候補は原則 `raw / ai` とし、再現条件・影響範囲・修正方向まで自力で固められた小粒課題に限り `ready / ai` を許可する
- 起票前に既存 `ISSUES/`・直近 `RETROSPECTIVE.md`・`MASTER_PLAN` を参照し、重複起票や「既に方針だけ決まっている項目」の再発見を避ける

#### 1-2. 完了条件

- 既存 ISSUE がなくても、能動探索だけを目的に 1 run 実行できる
- 1 run で 1〜3 件程度の高価値候補を抽出し、各 ISSUE に「症状」「影響」「なぜ今見る価値があるか」を残せる
- 起票された ISSUE は既存の `issue_review` / `issue_plan` の流れへ自然に接続できる
- `auto` / `full` / `quick` の既存挙動は変えず、探索 flow は opt-in の別入口として共存する

### 2. `QUESTIONS/` と調査専用 `question` workflow を追加する

#### 2-1. Question の役割

- `ISSUES/` とは別に `QUESTIONS/{category}/{high,medium,low}/` を設け、「実装依頼ではなく、まず調べたい問い」を置く場所として使う
- Question は「原因調査」「仕様確認」「設計比較」「現状把握」など、最終成果物がコードではなく報告書である依頼を表す
- 既存の `auto` / `full` / `quick` / `issue_plan` は `QUESTIONS/` を無視し、今まで通り `ISSUES/` だけを扱う
- Question 側の frontmatter は ISSUE に近い軸を使い、最低限 `status: raw | ready | need_human_action`、`assigned: human | ai`、`priority` を持たせる。調査完了後は `QUESTIONS/{category}/done/` へ移動する

#### 2-2. `question` workflow の期待挙動

- `question` workflow は `ready / ai` の Question を 1 件選び、必要な調査だけを行い、コード実装 step には進まない
- 調査結果は `docs/{category}/questions/{slug}.md` のような専用ドキュメントとして出力し、Question 本体から参照できるようにする
- 報告書には少なくとも「問い」「確認した証拠」「結論」「不確実性」「次アクション候補」を含める
- 調査の結果、実装課題が明確になった場合は、その場でコードを変える代わりに新しい ISSUE を起票して既存 flow へ渡す
- 人間の追加情報が必要なら `need_human_action / human` へ戻し、Question 本文末尾に確認事項を追記する

#### 2-3. 完了条件

- 「まず調べてほしいだけ」の依頼が、既存の full workflow を経由せずに処理できる
- Question は report doc の作成と archive だけで完了でき、実装やコミットを前提にしない
- 既存 ISSUE flow と Question flow の境界が docs 上で明確になり、どちらに起票すべきか迷いにくい

### 3. `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` を分離する

#### 3-1. 役割分担

- `ROUGH_PLAN.md` は「このバージョンで何をやるか」を記述するスコープ定義書に戻し、機能・対象範囲・含まないもの・期待成果へ集中させる
- 判断経緯、除外候補、関連 ISSUE パス、関連ファイル、前提条件、後続 step への注意点は新規 `PLAN_HANDOFF.md` に分離する
- `/issue_plan` は version 作成時に `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の両方を生成し、`/split_plan` および `quick_impl` は両方を読む
- 後続で判断が変わった場合、スコープ自体の変更は `ROUGH_PLAN.md`、実装中に見えた補足や引き継ぎは `PLAN_HANDOFF.md` または `MEMO.md` に残す

#### 3-2. 完了条件

- `ROUGH_PLAN.md` だけ読んだときに「何を達成する版か」が即座に分かる
- 後続 step は `PLAN_HANDOFF.md` を読むことで、選定理由や注意点を把握でき、`ROUGH_PLAN.md` を肥大化させずに済む
- quick / full のどちらでも、plan 本体と handoff 情報の責務が混ざらない
- version flow 文書と SKILL 指示が更新され、毎回同じ粒度で 2 ファイルを運用できる

### 4. ワークフロー終了通知を「run 単位・手動 dismiss まで残る」仕様に改める

#### 4-1. 期待される挙動

- 通知は loop ごとではなく、Python スクリプト全体が終了した時点で 1 回だけ出す
- `--max-loops 2` 以上でも、途中 loop 完了時は通知せず、最後の成功・失敗・中断結果を集約して通知する
- 通知文には workflow 種別、所要時間、loop 数、失敗時は終了コードや失敗 step など、run を把握するのに必要な情報を含める
- Windows では可能な限り「人が閉じるまで残る」通知スタイルを優先し、OS 制約で完全な常駐表示が難しい場合でも、少なくとも自動消滅しにくい fallback を用意する
- `--no-notify` と `--dry-run` は現行どおり通知抑止として維持する

#### 4-2. 完了条件

- multi-loop 実行で通知が 1 回だけ届く
- 成功・失敗・中断のすべてで通知タイミングが一貫する
- 席を外していても、戻った時に run 完了へ気づける
- 現行の PowerShell toast 依存部分と fallback 方針が docs / tests / 実装で整合する

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/claude_loop.py` | 変更予定 | `issue_scout` / `question` workflow の入口追加、run 単位通知への呼び出し整理 |
| `scripts/claude_loop_scout.yaml` | 新規作成予定 | 探索専用 `issue_scout` workflow 定義 |
| `scripts/claude_loop_question.yaml` | 新規作成予定 | 調査専用 `question` workflow 定義 |
| `scripts/claude_loop_lib/questions.py` | 新規作成予定 | Question frontmatter・一覧取得・archive 処理の共通化 |
| `scripts/question_status.py` | 新規作成予定 | `QUESTIONS/` の状態分布確認 |
| `scripts/question_worklist.py` | 新規作成予定 | Question の抽出・一覧表示 |
| `scripts/claude_loop_lib/notify.py` | 変更予定 | 永続通知と run サマリの扱いを改善 |
| `scripts/README.md` | 変更予定 | scout/question workflow、`PLAN_HANDOFF.md`、通知仕様を説明 |
| `scripts/USAGE.md` | 変更予定 | 新 workflow の起動方法と queue の違いを追記 |
| `.claude/SKILLS/issue_scout/SKILL.md` | 新規作成予定 | 潜在課題の探索と ISSUE 起票手順を定義 |
| `.claude/SKILLS/question_research/SKILL.md` | 新規作成予定 | 調査専用 workflow の報告書作成手順を定義 |
| `.claude/SKILLS/issue_plan/SKILL.md` | 変更予定 | `PLAN_HANDOFF.md` 生成と `QUESTIONS/` 非対象を明記 |
| `.claude/SKILLS/split_plan/SKILL.md` | 変更予定 | `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の読み分けを追加 |
| `.claude/SKILLS/quick_impl/SKILL.md` | 変更予定 | quick 実装時の `PLAN_HANDOFF.md` 参照ルールを追加 |
| `QUESTIONS/README.md` | 新規作成予定 | Question の frontmatter・ライフサイクル・報告書配置を定義 |
| `ISSUES/README.md` | 変更予定 | `issue_scout` が起票する `raw / ai` / `ready / ai` の扱いを追記 |
| `.claude/plans/VERSION_FLOW.md` | 変更予定 | version 配下に `PLAN_HANDOFF.md` を追加する flow を反映 |

## リスク・不確実性

- `issue_scout` の判定粒度が粗いと、価値の低い `raw / ai` が増えて `ISSUES/` のノイズ源になりうる
- Question と ISSUE の境界を曖昧にすると、「本当は実装依頼なのに Question に入る」「調査だけで済むのに ISSUE に入る」という逆流が起きる
- `PLAN_HANDOFF.md` を常に作る運用は、quick タスクでは冗長に見える可能性があるため、最小記載粒度を決めておく必要がある
- Windows 通知の永続化は OS のトースト仕様に制約される可能性があり、純標準ライブラリでどこまで実現できるかは要確認
- workflow 種別が増えることで CLI / README / SKILL の説明負荷が上がるため、`auto` に何が含まれないかを明示しないと混乱しやすい

## やらないこと

- `issue_scout` を既存 `auto` workflow に毎回自動挿入しない
- Question workflow から直接コード実装・テスト変更・デプロイまで進めない
- `QUESTIONS/` を第 2 の実装 backlog にしない
- `PLAN_HANDOFF.md` を恒久メモリや retrospective の代替にしない
- Slack/Discord など外部通知サービス連携まではこのフェーズで扱わない