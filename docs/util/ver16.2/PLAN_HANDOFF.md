---
workflow: research
source: master_plan
---

# ver16.2 PLAN_HANDOFF — `/split_plan` 以降への引き継ぎ

## ISSUE レビュー結果

- ready/ai に遷移: 0 件（`review/ai` の対象 ISSUE なし、`issue_review` SKILL の本処理は走らせていない）
- need_human_action/human に遷移: 0 件
- 追記した `## AI からの依頼`: 0 件
- 別途 triage（AI 自走パス）: `ISSUES/util/medium/deferred-resume-twice-verification.md` を `raw/ai` → `ready/ai` に昇格。判定根拠は ROUGH_PLAN §ISSUE レビュー結果に記載。`reviewed_at: "2026-04-24"` は据え置き（本日と同日のため再上書き不要）

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 3 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

ready/ai 3 件は依然 util 単独消化不能（`issue-review-rewrite-verification` は AI 単独で挙動再現困難 / `toast-persistence-verification` は Windows 実機目視必須 / `deferred-resume-twice-verification` は ver16.2 §3 完走後に deferred 経路を実発火させてから検証）。本版スコープは PHASE8.0 §3 のみとし、ISSUE 消化は次バージョン以降に回す。

## 選定理由・除外理由

### 選定理由（PHASE8.0 §3 着手）

1. **MASTER_PLAN 明示割当**: `docs/util/MASTER_PLAN/PHASE8.0.md` §実装進捗テーブルで「§3: 想定バージョン ver16.2」と明示。ver16.1 で §1・§2 を完走しており、§3 着手の前提条件（research workflow / deferred execution の本番投入）は満たされている
2. **ver16.1 RETROSPECTIVE §3 推奨**: 次バージョン推奨で「ver16.2 minor、PHASE8.0 §3 着手」を明示
3. **FEEDBACKS handoff §次ループで試すこと §1**: 同方針を補強

### 除外理由

- **ISSUE 消化（ready/ai 3 件）**: 本版で `/issue_plan` の主スコープにすると PHASE8.0 §3 と並走になり、`research` workflow の単一テーマ集中という強みを失う。3 件とも util 単独で消化困難な性質（外部実機 / deferred 経路の本番発動待ち）であり、§3 完走後に deferred 経路が実走するため、`deferred-resume-twice-verification` だけは ver16.2+ の自然な検証機会で動かしうる
- **新 PHASE 骨子作成**: PHASE8.0 §3 が未着手のため、PHASE9.0 等の骨子作成は時期尚早。ver16.1 RETROSPECTIVE §1 でも明示
- **`write_current` effort high の他 YAML 波及**: FEEDBACKS handoff §保留事項 1 点目より、§3 完走後の `CHANGES.md` / `CURRENT_*.md` の生成品質を見て判断。本版では保留
- **`research_context` / `experiment_test` の model 下げ**: 同 §保留事項 3 点目。本版で `research` を再採用するため差分観察の好機だが、即時下げる判断は危険。観察マターに留める
- **持ち越し ready/ai 4 件の `need_human_action/human` 振り直し**: 同 §保留事項 4 点目で「検討の余地あり」とされたが、`/issue_plan` SKILL の review フェーズは `review/ai` のみが対象であり、`ready/ai` を強制的に `need_human_action/human` に降格する手順は SKILL 側に存在しない。本版では振り直しを行わず、後続バージョンで `issue_review` SKILL 側に「長期持ち越し ready/ai の再判定」手順を追加するか別運用で扱うかを別途検討（後続 step への注意点 §3 参照）

## 関連 ISSUE / 関連ファイル / 前提条件

### 関連 ISSUE

本版の主要スコープと直接連動する ISSUE はなし（PHASE8.0 §3 は MASTER_PLAN 由来）。間接的な連動:

- `ISSUES/util/medium/deferred-resume-twice-verification.md`（本版で `ready/ai` 化）— ver16.2 §3 完走後に deferred execution が実走する初のケースで履歴継承を観察できる。`/wrap_up` または `/retrospective` で副次成果として観察結果を残せれば、後続バージョンでの ISSUE クローズが早まる

### 関連ファイル（PHASE8.0 §3 が触る範囲）

- 新規: `scripts/claude_loop_lib/costs.py` / `scripts/tests/test_costs.py`
- 変更: `scripts/claude_loop_lib/logging_utils.py` / `scripts/claude_loop.py` / `scripts/claude_loop_lib/validation.py`（新キー次第）
- ドキュメント: `scripts/README.md` / `scripts/USAGE.md` / `docs/util/MASTER_PLAN/PHASE8.0.md`（§3 完了時の ✅ 追記）
- rule（候補）: `.claude/rules/scripts.md`（cost log 仕様の stable 化判断は §3 完了後に判断）

### 前提条件

- **PHASE8.0 §1（research workflow）/ §2（deferred execution）の完走**: ver16.0 / ver16.1 で確定済
- **`research` workflow YAML（`scripts/claude_loop_research.yaml`）の動作確認**: ver16.1 self-apply で計画通り 8 step 完走を確認済
- **YAML sync 契約**: ver16.1 では踏まずに済んだ（`effort` のみ調整）が、§3 で `command` / `defaults` に新キー（cost log 関連、例: cost sidecar 出力先 / 価格表バージョン）を追加する場合、ver16.0 RETROSPECTIVE §「6 YAML 手動同期」リスクが再浮上する。`/imple_plan` でキー追加が見えた時点で、6 YAML 同期 vs. 生成元 1 箇所化の選択を判断する
- **Claude CLI usage 出力の安定性**: `--output-format json` で `usage` フィールドが安定取得できる前提が成り立たない場合、`/research_context` で取得経路の代替（API 経由 / sidecar / stderr 解析）を検討する必要がある

## 後続 step への注意点

### 1. `/split_plan` での未解決論点候補（`/research_context` 入力）

ver16.1 で `IMPLEMENT.md §0` が未解決論点リストの "RESEARCH/EXPERIMENT 入力点" として機能した実績があるため、本版でも同節を作る方針で `/split_plan` に入る。本版で先送りすべき論点候補:

- **U1**: Claude CLI が usage を返す経路（`--output-format json` の `usage` フィールド構造、`cache_creation_input_tokens` / `cache_read_input_tokens` の有無、stderr / sidecar / API 経由の代替）
- **U2**: 価格表のメンテ方法（hardcode 定数 vs. 設定ファイル vs. 環境変数）と「どの価格表で計算したか」の記録方法
- **U3**: deferred execution の外部コマンド時間と Claude step の cost をどう分離して残すか（duration と cost を別軸で記録する規約の具体化）
- **U4**: cost sidecar の保存先と命名（`logs/workflow/{run_id}/costs.json` 想定だが、既存 workflow log との関係を確定）
- **U5**: 欠測時の表現（usage が取れなかった step を `null` で残すか `"未取得"` 文字列で残すか、retrospective 集計側の扱いやすさで決定）

`/split_plan` はこれらを `IMPLEMENT.md §0` に列挙し、`/research_context` と `/experiment_test` がそれぞれ「外部仕様確認」「実機 sample 採取」で確定させる流れを想定。

### 2. `/research_context` のスコープガイド

- **一次資料優先**: Anthropic 公式 CLI docs（`claude --help` / `--output-format json` の出力 spec）/ 公式 SDK の usage 構造 / pricing page を最優先で当たる
- **既存 repo 内資料**: `scripts/claude_loop.py` の subprocess 呼び出し箇所、`scripts/claude_loop_lib/logging_utils.py` の現行 log 整形を読み、cost を既存 log にどう挟み込むかの肝を掴む
- **use-tavily 経由の外部調査**: 公式 docs で確定しない場合のみ。GitHub issue / community forum からの情報は補足扱い
- **`research_context` SKILL 制約**: 同期実行制約下で nested `claude` を呼ばないこと（ver16.1 RETROSPECTIVE §5 で `experiment_test` SKILL に追記したガードが、`research_context` SKILL 側にも同等に適用される）

### 3. `/experiment_test` のスコープガイド

- **再現対象**: 短い prompt（例: `claude -p "1+1=?"` 相当）を `--output-format json` で実行し、JSON 出力の usage 関連フィールドを採取する
- **配置**: `experiments/cost-usage-capture/` 配下を推奨（PHASE8.0 §1-1 の `experiments/` 運用ルール準拠、削除条件コメントを必ず先頭に書く）
- **同期実行制約**: ver16.1 EXPERIMENT.md §U2/§U3 と同様、nested `claude` CLI の実行は **観測バイアスを生むため避ける**。`experiments/` 配下のスクリプトを Bash 経由で 1 回実行する分には許容されるが、`claude` を `claude_loop.py` から呼んでいる最中に別 `claude` を起動するパターンは禁止
- **長時間化したら deferred 経路を使う**: 本版で deferred execution が本番発動する初の機会になりうる。`deferred-resume-twice-verification.md`（本版で `ready/ai` 化）の実機検証も副次的に進められる

### 4. `/imple_plan` での YAML sync 契約の事前判断

§3 で `command` / `defaults` に新キー（cost log 関連）を追加する場合、ver16.0 RETROSPECTIVE §「6 YAML 手動同期」のリスクが再浮上する。`/imple_plan` で IMPLEMENT.md にキー追加が確定した時点で、以下のどちらかを明示判断する:

- (a) 本版で 6 YAML（`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml` / `claude_loop_question.yaml` / `claude_loop_scout.yaml` / 該当する場合の他）に手動同期して進む
- (b) 本版スコープに「YAML sync 契約の生成元 1 箇所化」を含めて根本対応する

ver16.1 では (a) を踏まずに済んだ（effort 調整のみ sync 対象外）。本版で (b) に踏み込むと scope が膨らむため、§3 完了優先の場合は (a)、新キーが多く同期コスト >> 生成元一元化コストになる場合のみ (b) に振る。

### 5. 持ち越し ready/ai 4 件の長期滞留について

FEEDBACKS handoff §保留事項 4 点目で「ver16.2 で `need_human_action/human` への振り直しを検討する余地あり」と提起されているが、本版では振り直しを行わず据え置く。理由:

- `/issue_plan` SKILL の review フェーズは `review/ai` のみが対象。`ready/ai` を `need_human_action/human` に降格する手順は SKILL 側に未定義
- 強制降格は ISSUES の lifecycle ルール（README §ライフサイクル）と整合しない（`ready/ai` から `need_human_action/human` への遷移は本来「実装中に人間情報が必要だと判明した場合」に限定されるべき）

`/wrap_up` または `/retrospective` のいずれかで「長期滞留 ready/ai の再判定手順」を `issue_review` SKILL 側に追加する提案を ISSUE として起票する案を、本版 closeout 時の判断材料として残す。

### 6. `research` workflow 採用の差分観察

ver16.1 で `research_context` / `experiment_test` は初の本番投入だった。本版で 2 回目の投入になるため、ver16.1 RETROSPECTIVE §3.5 で保留した「model 下げの判断材料」が揃う機会。`/retrospective` §3.5 で 2 サンプル間の差分（artifact 分量 / 一次資料化精度 / 実装乖離率）を比較し、後続バージョンでの model 調整判断に繋げる。
