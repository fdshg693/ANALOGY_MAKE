---
workflow: full
source: master_plan
---

# ROUGH_PLAN: util ver10.0 — PHASE7.0 §1 着手（workflow YAML の step 単位 system prompt / model 系 override 導入）

## ISSUE レビュー結果

今回 `review / ai` の ISSUE は util カテゴリに 0 件存在したため、状態遷移は発生しなかった（レビューフェーズはスキップ）。

- 走査対象: `ISSUES/util/{high,medium,low}/*.md`
- `review / ai` 件数: 0
- 書き換え件数: 0（`ready / ai` 遷移 0 / `need_human_action / human` 遷移 0）
- `## AI からの依頼` 追記: 該当なし

## ISSUE 状態サマリ（util、本 plan 開始時点）

`python scripts/issue_worklist.py --format json --limit 20` / `python scripts/issue_status.py util` の結果に基づく:

| assigned × status | high | medium | low | 計 |
|---|---:|---:|---:|---:|
| `ready / ai` | 0 | 1 | 0 | 1 |
| `review / ai` | 0 | 0 | 0 | 0 |
| `need_human_action / human` | 0 | 0 | 0 | 0 |
| `raw / human` | 0 | 0 | 0 | 0 |
| `raw / ai` | 0 | 0 | 0 | 0 |

対象 ISSUE 一覧:

| path | priority | status | assigned | 本 plan での扱い |
|---|---|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai | 持ち越し（util 単体では消化不能、app/infra ワークフロー起動待ち） |

## バージョン種別の判定

**メジャーバージョンアップ (ver10.0)** として進める。

判定根拠:

- `docs/util/MASTER_PLAN/PHASE7.0.md` の新項目（§1 workflow YAML の step 単位 system prompt / model override）に着手するため、CLAUDE.md の「メジャー = MASTER_PLAN の新項目着手」に合致
- workflow YAML schema の拡張（step 単位 override フィールド追加）を伴う
- `scripts/claude_loop_lib/workflow.py` の解決ロジック変更で、step 設定の継承順序を新たに規定する（既存の `defaults: → step:` 継承ルールを、新 override キーへ拡張する性質のアーキテクチャ変更）
- `docs/util/ver9.0/RETROSPECTIVE.md` §3-3 で「ver10.0 以降で PHASE7.0 骨子作成に着手」と方針が明文化されており、直近コミット `a512fb7`（PHASE7作成）で骨子ファイル `PHASE7.0.md` が既に整備済
- ver9.0/9.1/9.2 で `--workflow auto` と `--limit` 防御策がそろい、PHASE7.0 に着手する前提条件（安定基盤）は満たされている

## ワークフロー種別の選択

**`workflow: full`** を採用する。

判定根拠:

- MASTER_PLAN 新項目への着手（SKILL ガイドライン: MASTER_PLAN 新項目 → full）
- workflow YAML schema 拡張 + 解決ロジック導入というアーキテクチャ寄りの変更（SKILL ガイドライン: アーキテクチャ変更 → full）
- 変更見込みファイルは `scripts/claude_loop.py` / `scripts/claude_loop_lib/workflow.py` / `scripts/claude_loop_lib/commands.py` / 3 本の workflow YAML / `scripts/README.md` / `tests/test_claude_loop.py` など 5〜7 本規模、変更行数も合計 100 行を超える見込みのため `quick` の適合条件を外れる

`source: master_plan`（既存 ISSUE 起点ではなく、PHASE7.0 新項目起点）。

## 今回取り組む内容

PHASE7.0 §1「workflow YAML での step 単位 system prompt / model 設定 override」を ver10.0 の主対象とし、あわせて MASTER_PLAN.md 本体の軽微な表記ズレ（後述）を整理する。

### 主対象: workflow YAML step 単位 override の導入

#### 現状（ver9.x 時点の挙動）

`scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` は以下の 2 層構造:

- `defaults:` — workflow 全体の既定値（現在は `model` / `effort` のみ）
- `steps[i]:` — 各 step 個別の上書き（現在は `model` / `effort` / `continue` のみ）

`system_prompt`（CLI の `--append-system-prompt` に相当する内容）は `command.auto_args` 内にハードコードされており、step ごとに差し替えられない。`temperature` / `max_tokens` 系も同様に YAML で扱えない。

#### 問題点（PHASE7.0 §1 動機の再掲）

- step 単位で prompt / model 調整を試したいとき、YAML では表現できず、SKILL 側プロンプト本文やスクリプト側の分岐に責務が漏れる
- workflow 全体の既定値 vs step 個別値の継承ルールが、現在は `model` / `effort` の 2 キーにしか適用されておらず、他の model 系設定に拡張するための一般化が未整備
- 将来 `/retrospective` が workflow prompt / model 評価を行う（PHASE7.0 §8）際、step ごとの override を一次資料として読み書きできる必要がある

#### ver10.0 で提供する振る舞い

ユーザー体験の変化（= 機能面での効果）:

- **step 単位で system prompt / model 系設定を指定可能**: workflow YAML の各 step 配下に、`system_prompt` / `model` / `temperature` / `max_tokens` 等の model 関連キーを個別指定できる
- **未指定キーは workflow 全体の既定値を継承**: step に該当キーが無い場合は `defaults:` 側の値を引き継ぐ。`defaults:` にも無ければ実行系の規定値（Claude CLI の標準挙動）に従う
- **override 対象は限定列挙**: 実行系が安定解釈できる model 関連キーのみを対象にし、任意キーの透過 pass-through は行わない（対象キー集合は IMPLEMENT.md で確定）
- **継承結果の可視化**: 解決された各 step の有効設定は、少なくとも validation 可能な段階で一意に決まり、実行前に確認できる形にする
- **既存 YAML との後方互換**: 新しい override キーが存在しなくても、従来の `model` / `effort` / `continue` のみの step 定義はそのまま動作する
- **CLI への受け渡し**: 解決された各 step の設定は、Claude CLI 起動時の引数・`--append-system-prompt` へ反映される

PHASE7.0 §1 完了条件 3 点を踏襲する:

1. workflow YAML だけで「この step だけ prompt / model を変える」が表現できる
2. 同一 workflow 内で複数 step が異なる model 設定を持っても、継承順序が曖昧にならない
3. 無効な model 名・型不正な設定値の検出は、本バージョンでは **実行前エラー化までは踏み込まず**、後続の §2（起動前 validation、ver10.1 予定）に委ねる（YAML 解釈時点で落ちる範囲のみ担保）

### スコープ外（ver10.0 では扱わない）

以下は PHASE7.0.md の設計に沿って後続バージョンに先送りする:

- **§2 起動前 validation**（全 step の参照解決・schema 検証）: ver10.1 以降。§1 の override 仕様が固まった上に積み上げる
- **§3 legacy `--auto` と対応 YAML 設定の撤去**: ver10.1 以降。CLI 移行コミュニケーションを伴うため、§1 との同一バージョン詰め込みはリスク
- **§4〜§8**: PHASE7.0.md の計画通り ver10.1〜ver10.2 以降
- **`system_prompt` に渡せる内容の pre-processing / テンプレート展開**: 本バージョンではリテラル文字列受け渡しのみ想定
- **override を既存 SKILL に適用する本格運用**: 本バージョンでは仕組みの導入のみ。実際に step 別の prompt/model を差し替えるかは `/retrospective`（PHASE7.0 §8、ver10.2 予定）以降で判断

### 併せて整理する軽微な MASTER_PLAN 表記ズレ

直近コミット `a512fb7`（PHASE7作成）で `docs/util/MASTER_PLAN.md` の末尾が以下の状態になっている:

```
- `./MASTER_PLAN/PHASE6.0.md` — **一部実装済み**（...§3 `--workflow auto` 導入は未着手。...）
- `./MASTER_PLAN/PHASE6.0.md` — **未実装**
```

- 13 行目の `PHASE6.0.md` は ver9.0 で §3 `--workflow auto` が実装済みとなり、既に「全節完了」状態（`ver9.0/RETROSPECTIVE.md` §1-1）。サマリのみ未反映
- 14 行目の `PHASE6.0.md` は同コミットで追加された行で、コミットメッセージ「PHASE7作成」と `PHASE7.0.md` 新設の内容から、`PHASE7.0.md` と書こうとした typo と推定できる

ver10.0 スコープに以下を含める:

- 13 行目のステータス表記を「実装済み」に更新（ver9.0 完了内容を反映）
- 14 行目のパスを `PHASE7.0.md` に修正し、サマリとして「未実装（骨子作成済、ver10.0 で §1 着手予定）」相当の一行を添える
- 末尾行に改行を追加（現状 `No newline at end of file`）

※ 判断の自信度が曖昧な部分は IMPLEMENT.md 作成時にユーザー意図確認用リクエストを起票する選択肢も残す。

## 関連ファイル（`/split_plan` への引き継ぎ用）

### 主対象（コード）

- `scripts/claude_loop_lib/workflow.py` — workflow YAML のロード / step の有効設定解決 / `defaults:` 継承ロジック
- `scripts/claude_loop_lib/commands.py` — Claude CLI 引数組み立て。`--append-system-prompt` や model 関連フラグへの橋渡し
- `scripts/claude_loop.py` — step 実行ループ。解決済み設定を commands 層へ渡す

### 主対象（workflow YAML）

- `scripts/claude_loop.yaml`（6 step 構成、`--workflow auto` フェーズ 2 の full パス）
- `scripts/claude_loop_quick.yaml`（3 step 構成、`--workflow auto` フェーズ 2 の quick パス）
- `scripts/claude_loop_issue_plan.yaml`（1 step、`--workflow auto` フェーズ 1）

→ override キーを新設するため、3 本ともコメント or サンプル追加の可能性あり。ただし既存の `model` / `effort` 設定は原則維持し、破壊的変更は避ける。

### 主対象（テスト）

- `tests/test_claude_loop.py` — 既存 `TestWorkflowYaml` / `TestLoadWorkflow` 系クラスへの追記を想定
  - `defaults:` のみ指定時の解決結果
  - step override のみ指定時の解決結果
  - `defaults:` と step override が重なった場合の優先順位
  - 未指定キーの既定値フォールバック
  - override キー集合外のキーが YAML に書かれた場合の扱い（無視 or 警告）

### 主対象（ドキュメント）

- `scripts/README.md` — YAML schema の仕様説明を更新
- `docs/util/MASTER_PLAN.md` — 上述の表記ズレ修正

### 参照ドキュメント

- `docs/util/MASTER_PLAN/PHASE7.0.md` §1（本バージョンの一次設計書）
- `docs/util/ver9.0/RETROSPECTIVE.md` §3-3（ver10.0 で PHASE7.0 着手する方針と根拠）
- `docs/util/ver9.0/CURRENT.md`（`--workflow auto` と `defaults` 継承の現状説明）
- `docs/util/ver9.2/CHANGES.md`（直近の scripts 系変更。影響域の参照）
- `.claude/skills/issue_plan/SKILL.md`（MASTER_PLAN 全フェーズ完了時の判断ガイドライン）

### 関連 ISSUE

- `ISSUES/util/medium/issue-review-rewrite-verification.md` — 今回は扱わない（util 単体で消化不能のため持ち越し）

## 判断経緯の補足（`/split_plan` への引き継ぎ用）

### なぜ PHASE7.0 §1 のみを ver10.0 のスコープにするか

- PHASE7.0.md §1〜§3 は想定バージョンがいずれも ver10.0 だが、`/issue_plan` SKILL 指示の「**比較的小規模で完結する切りのいいタスクを切り取り、そのタスクのみにフォーカス**」「**後続のタスクの内容などは含めないこと**」に従い、最小単位で切り出す
- §1（override 仕様）は §2（validation）と §3（legacy `--auto` 撤去）の土台になるため、単独での意味は大きい。逆に §1 が不安定なまま §2 で validation を積むと、spec と実装の両方に手戻りが起きやすい
- §3 の legacy `--auto` 撤去は CLI 互換性を伴う破壊的変更で、§1 と混ぜるとコミット・レビュー単位が肥大化する
- したがって ver10.0 = §1 単体、ver10.1 = §2（validation）、ver10.1 or ver10.2 = §3（legacy 撤去）の粒度分割が安全

### なぜ `ready / ai` の ISSUE を拾わず MASTER_PLAN 起点にしたか

- util カテゴリの `ready / ai` は `issue-review-rewrite-verification.md` 1 件のみ。本 ISSUE は「util カテゴリの `review / ai` が 0 件のため、app/infra ワークフロー起動時にしか実動作確認機会が無い」という構造的制約があり、util ワークフロー内部では消化不能（ver9.0〜9.2 まで 3 バージョン連続で同判断）
- 直近コミット `a512fb7` で `PHASE7.0.md` 骨子が新たに整備されており、MASTER_PLAN 新項目起点の実装が即座に可能になった
- SKILL ガイドラインの「MASTER_PLAN 全フェーズ完了時」分岐において、①既存 ISSUES 消化可 → 不可、②新テーマ明確 → 可（PHASE7.0 骨子が既存）、の条件を満たす

### なぜ `workflow: full` を選んだか

- MASTER_PLAN 新項目着手（SKILL ガイドライン明示条件）
- アーキテクチャ寄りの変更（YAML schema 拡張 + 継承ロジック一般化）
- 変更見込みファイルが 5〜7 本、変更行数が 100 行超の見込みで、`quick` の適合条件（3 ファイル以下 / 100 行以下 / 全 `ready`）から外れる
- 選定タスクに `review / ai` は含まれないが、これは `full` への障害にならない（`full` は review 起点以外でも選択可）

### `/split_plan` で詰めるべき事前論点（先行列挙）

`IMPLEMENT.md` / `REFACTOR.md` 作成時に扱うべき論点を列挙する（ROUGH_PLAN 時点では実装方式には踏み込まない）:

1. **override 対象キー集合の確定**: `system_prompt` / `model` / `temperature` / `max_tokens` が現実に Claude CLI へ渡せる形式か（`--append-system-prompt` 以外のフラグ対応状況）を確認したうえで、本バージョンで受け入れるキーを明示列挙する
2. **`system_prompt` の解釈**: 現状 `command.auto_args` 内の `--append-system-prompt` に埋め込まれた長文（`.claude/` 編集手順等）を、step 個別 `system_prompt` で置き換えるのか、既存文字列へ追記するのか、別フラグにするか
3. **継承ルールの明文化**: `defaults:` → step override → CLI 既定、の 3 段階を公式仕様として `scripts/README.md` に書き起こす。テストも 3 段階に対応させる
4. **workflow YAML の 3 本間の同期コメント**: `claude_loop.yaml` 先頭のコメント（3 本は `command` / `mode` / `defaults` を sync する）を新 override キー仕様にも拡張する
5. **`commands.py` の CLI 組み立て層のリファクタリング判断**: step 単位で可変になる設定が増えるため、現状の単純 concat から dict-to-args 的な関数への切り出しが必要か（REFACTOR.md 対象）
6. **既存テストの破壊防止**: `tests/test_claude_loop.py` の `TestWorkflowYaml` / `TestLoadWorkflow` / `TestAutoWorkflowIntegration` 系の既存ケースは、override キー追加後も従来どおり通ることを必須とする
7. **MASTER_PLAN.md typo 修正の独立コミット化**: 本修正は PHASE7.0 §1 実装とは独立させ、レビュー容易性を確保する（`/imple_plan` 段階で別コミット指示に落とす）
8. **PHASE6.0.md / PHASE7.0.md 進捗表の更新タイミング**: ver10.0 完了時に PHASE7.0.md §1 の状態を「実装済」へ変更する運用を `/wrap_up` へ引き継ぐ（本 plan では扱わない）
9. **`plan_review_agent` 観点の先回り**: override を追加する際の「何を受け入れて何を受け入れないか」の境界（§1-2 完了条件②「継承順序が曖昧にならない」）を明記しないと指摘を受けやすい

上記は `/split_plan` 以降で詳細化・棄却判断を行う前提の論点リストであり、本 ROUGH_PLAN 時点では実装方式を確定しない。

## 事前リファクタリング判断（`/split_plan` 段階で確定）

**事前リファクタリング不要**。`build_command()` の `(key, flag)` 反復は新キー追加に十分拡張容易で、共通化抽出による事前整理は不要（IMPLEMENT.md でインライン拡張する）。
