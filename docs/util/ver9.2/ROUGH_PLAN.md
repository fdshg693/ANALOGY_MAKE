---
workflow: quick
source: issues
---

# ROUGH_PLAN: util ver9.2 — `issue_worklist.py --format json` の件数上限オプション追加

## ISSUE レビュー結果

今回 `review / ai` の ISSUE は 0 件のため、状態遷移は発生しなかった（レビューフェーズはスキップ）。

## ISSUE 状態サマリ（util、本 plan 開始時点）

`python scripts/issue_status.py util` 実行結果:

| assigned × status | high | medium | low | 計 |
|---|---:|---:|---:|---:|
| `ready / ai` | 0 | 1 | 1 | 2 |
| `review / ai` | 0 | 0 | 0 | 0 |
| `need_human_action / human` | 0 | 0 | 0 | 0 |
| `raw / human` | 0 | 0 | 0 | 0 |
| `raw / ai` | 0 | 0 | 0 | 0 |

対象 ISSUE 一覧（`python scripts/issue_worklist.py --format json` 結果）:

| path | priority | status | assigned | 本 plan での扱い |
|---|---|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai | 持ち越し（util 単体では消化不能、app/infra ワークフロー起動待ち） |
| `ISSUES/util/low/issue-worklist-json-context-bloat.md` | low | ready | ai | **今回の主対象**（下記参照） |

参考（他カテゴリの ready/review 件数）:

- app: 3 ready/ai + 3 review/ai = 6
- infra: 1 ready/ai + 1 review/ai = 2
- cicd: 0
- util: 2 ready/ai

最大は app の 6 件。ISSUE 本文が想定する「20 件程度」の閾値には未到達だが、後述の通り防御的実装の価値が高いため ver9.2 で先行消化する。

## バージョン種別の判定

**マイナーバージョンアップ (ver9.2)** として進める。

判定根拠:

- `ISSUES/util/low/issue-worklist-json-context-bloat.md` の解消（既存スクリプトへのオプション追加）であり、バグ修正・既存機能改善に該当
- アーキテクチャ変更なし、新規ライブラリ導入なし、破壊的変更なし
- MASTER_PLAN の新項目着手ではない（PHASE6.0 は ver9.0 で全完了済、PHASE7.0 骨子作成は ver10.0 以降に先送り済 — `docs/util/ver9.0/RETROSPECTIVE.md` §3-3）
- 変更見込みファイルは `scripts/issue_worklist.py` + `tests/` への新規テスト + `.claude/skills/issue_plan/SKILL.md` の `!` バックティック行更新の計 3 本程度
- CLAUDE.md バージョン管理規則「マイナー = バグ修正・既存機能改善・ISSUES対応」に合致

## ワークフロー種別の選択

**`workflow: quick`** を採用する。

判定根拠:

- 選定 ISSUE は `status: ready / ai` のみ（`review` なし）→ `quick` 許容条件を満たす
- 変更ファイルは 3 本以下（`scripts/issue_worklist.py` / `tests/test_issue_worklist*.py`（新規 or 既存追記）/ `.claude/skills/issue_plan/SKILL.md`）
- 100 行以下の変更見込み（`--limit` 引数の追加と切り出しロジックのみ）
- アーキテクチャ変更なし、新規ライブラリ導入なし、MASTER_PLAN 新項目着手なし

`source: issues`（既存 ISSUE 起点、MASTER_PLAN 新項目ではない）。

## 今回取り組む内容

`ISSUES/util/low/issue-worklist-json-context-bloat.md` の解消を主眼とする。

### 主対象: `scripts/issue_worklist.py` への件数上限オプション追加

#### 現状（ver9.1 時点の挙動）

`python scripts/issue_worklist.py --format json` は、指定カテゴリの `status in {ready, review}` かつ `assigned == ai` の ISSUE を**全件**返す。`/issue_plan` SKILL の `## コンテキスト` 冒頭で `!` バックティック展開によりこの JSON が SKILL プロンプトに埋め込まれる:

```markdown
- AI 向け ready/review ISSUE: !`python scripts/issue_worklist.py --format json`
```

#### 問題点

カテゴリによっては ISSUE 件数が膨らみ、`/issue_plan` の SKILL プロンプトが想定外に肥大化する:

1. ISSUE 1 件あたり最大 7 フィールド（path / title / priority / status / assigned / reviewed_at / summary）が JSON に含まれ、トークン消費が嵩む
2. AI が全件走査できず、優先度の低い ISSUE を拾うリスクがある（プロンプト末尾切れの可能性）
3. ステップ開始前のコンテキストサイズが急増し、後続セッションのコスト・速度に影響する

ver9.2 開始時点では app カテゴリ 6 件が最大で、ISSUE 本文が想定する「20 件程度」の閾値には未到達。一方、ISSUE は ver8.0 から `ready / ai` 状態で積み残されており、件数が将来増えた瞬間に問題が顕在化する性質のため、軽量な防御的実装で先回りして閉じる価値がある。

#### ver9.2 で提供する振る舞い

ユーザー体験の変化（= 機能面での効果）:

- **`--limit N` オプションの新設**: `python scripts/issue_worklist.py --limit 20 --format json` で先頭 N 件のみを返す
- **省略時は現行動作（全件）を維持**: 既存 CLI / 呼び出し元（`/retrospective` SKILL の `text` 出力など）は無変更で動き続ける
- **件数の優先順保証**: priority（high → medium → low）の順で上位 N 件が切り出される（現行の収集順序と同一）。同一 priority 内ではファイル名昇順（現行 `sorted(priority_dir.glob("*.md"))` を維持）
- **`text` / `json` 両方で `--limit` を有効化**: フォーマット差異による挙動分岐をなくし、テスト容易性を確保
- **切り捨てが発生した旨の表示**: `text` 出力末尾には `(showing first N of M issues)` 形式の補助行を出す（json 出力には `truncated: bool` / `total: M` 等のメタ情報を含めるか IMPLEMENT.md で確定）
- **`/issue_plan` SKILL のコンテキスト行を `--limit 20` 付きに更新**: 既定で SKILL プロンプトに埋め込まれる JSON が常に 20 件以内に収まる

ISSUE 本文の想定実装ステップ 4 つ（`--limit N` オプション追加 / 省略時全件維持 / SKILL コンテキスト行更新 / priority ソート保証）をそのまま踏襲する。具体的な引数名・デフォルト値・メタ情報フィールド名・truncation 表示の文面は `IMPLEMENT.md` に委ねる。

### 除外対象と除外理由

- `ISSUES/util/medium/issue-review-rewrite-verification.md`: 書き換えロジックの実動作確認には `ISSUES/app/medium/*.md` の `review / ai` ISSUE もしくは `ISSUES/infra/high/*.md` の `review / ai` ISSUE が必要。util カテゴリのワークフローでは消化不能なため持ち越し（前回 ver9.1 と同じ判断）
- PHASE7.0 骨子作成: `docs/util/ver9.0/RETROSPECTIVE.md` §3-3 で「ver10.0 以降」「`--workflow auto` を数回実走してから新フェーズの課題を具体化」する方針が確定済。ver9.1 で 1 回目の実走を終えたが、まだ「数回」とは言えず、ver9.2 でも見送る

### MASTER_PLAN 状況（参考）

- `docs/util/MASTER_PLAN/PHASE1.0.md`〜`PHASE6.0.md` はすべて実装済（`PHASE6.0.md` 進捗表は ver9.0 完了時点で全節 ✅）
- `docs/util/MASTER_PLAN.md` 本体サマリは PHASE6.0 を「一部実装済み」と表記しているが、実態とズレている。ver9.2 での修正対象には含めない（後続バージョンでまとめて整理する想定）
- `PHASE7.0.md` は未作成。`--workflow auto` を数回実走してから新フェーズの課題を具体化する方針
- 本 ver9.2 は既存 ISSUES 消化を優先し、MASTER_PLAN 新項目には着手しない（`source: issues`）

## 関連ファイル

### 主対象（コード）

- `scripts/issue_worklist.py`
  - `parse_args(argv)` （行 141〜148、`--limit` 追加先）
  - `collect(category, assigned, status_list)` （行 81〜115、件数を返した後に呼び出し側で切り出すか、`collect` 内で切り出すかは IMPLEMENT.md で確定）
  - `format_text(category, items)` / `format_json(category, assigned, status_list, items)` （行 118〜138、truncation メタ情報の埋め込み箇所）
  - `main(argv)` （行 151〜159、`--limit` 適用ポイント）

### 主対象（テスト）

- 既存 `tests/test_claude_loop.py` の `claude_loop_lib.issues` テストとは責務が異なる。`issue_worklist.py` 専用のテストファイル新設または既存テストファイルへの追記を IMPLEMENT.md で判定する
- 想定追加ケース:
  - `--limit` 省略時は全件返る（後方互換）
  - `--limit N` 指定時は先頭 N 件のみ返る
  - `--limit N` で N > 件数のとき切り捨ては発生しない
  - text / json 双方で `--limit` が等価に効く

### 主対象（SKILL）

- `.claude/skills/issue_plan/SKILL.md` 行 13:
  - 現状: `- AI 向け ready/review ISSUE: !`python scripts/issue_worklist.py --format json``
  - 変更後: `- AI 向け ready/review ISSUE: !`python scripts/issue_worklist.py --format json --limit 20``
  - **編集手段**: `.claude/` 配下のため `python scripts/claude_sync.py export` → `.claude_sync/` 編集 → `python scripts/claude_sync.py import` の手順を要する（`.claude/rules/claude_edit.md` 参照）

### 参照ドキュメント

- `ISSUES/util/low/issue-worklist-json-context-bloat.md`（本 ISSUE 本文・対応方針 4 ステップの記述あり）
- `docs/util/ver8.0/IMPLEMENT.md` §9 R5（検証先送りの経緯）
- `docs/util/MASTER_PLAN/PHASE6.0.md` §1（`issue_worklist.py` 元設計、出力項目仕様）
- `scripts/claude_loop_lib/issues.py`（`extract_status_assigned` / `VALID_STATUS` / `VALID_ASSIGNED` の共通化先。`--limit` 追加では原則無変更だが、共通ヘルパ側にロジックを寄せる選択肢もあるため IMPLEMENT.md で確認）

## 判断経緯の補足（`/split_plan` への引き継ぎ用）

### なぜ low の `issue-worklist-json-context-bloat.md` を medium より優先するか

- 優先度順（high → medium → low）の原則に反するが、残 medium 1 件は util 単独消化が不能:
  - `issue-review-rewrite-verification.md` は util カテゴリの `review / ai` ISSUE が 0 件のため、app/infra カテゴリの `/issue_plan` 起動時にしか書き換えロジックの実動作確認機会が発生しない。util ワークフローからは構造的にトリガできない
- 一方 `issue-worklist-json-context-bloat.md` は `scripts/issue_worklist.py` 単体への小規模な追加で完結し、util ワークフローで自己完結する
- ver9.0 RETROSPECTIVE §3-1 でも「件数閾値未到達（util 4 件）。当面 YAGNI」と分類されていた背景を踏まえつつ、ver9.2 開始時点で他に actionable な候補がないため先行消化に倒す

### なぜ「YAGNI 持ち越し」だった ISSUE を ver9.2 で着手するか

- `/issue_plan` SKILL の guideline 「**MASTER_PLAN 全フェーズ完了時の判断ガイドライン**」§1 が、`ready / ai` 1 件以上 + 小粒対応で区切れる場合は ISSUE 消化を優先する旨を明文化している
- 件数閾値未到達でも実装は防御的に有効（将来の急な ISSUE 増に対する保険）
- ver9.0 で導入された `--workflow auto` のデフォルト経路では、`/issue_plan` SKILL のコンテキスト埋め込み JSON が毎回プロンプトに乗る。app カテゴリ 6 件時点でも累積コストは無視できない
- 実装規模が小さく、`/split_plan` の review コストを抑えられる（`workflow: quick` 適合）

### なぜ `quick` ワークフローを選んだか

- 変更対象は `scripts/issue_worklist.py` の局所改修と対応テスト + SKILL コンテキスト行 1 行の差し替えのみ
- 選定 ISSUE に `review / ai` は含まれない（util カテゴリの `review / ai` は 0 件）
- アーキテクチャ変更なし、新規ライブラリなし、MASTER_PLAN 新項目着手なし
- 100 行以下の変更見込み

### `/split_plan` で詰めるべき事前リスク（先行列挙）

`IMPLEMENT.md` 作成時に扱うべき論点:

1. **`--limit` 適用箇所の決定**: `collect()` 内で切り出すか、`main()` で切り出すかで責務が変わる。テスト粒度・将来の再利用性で判断する
2. **デフォルト値の取り扱い**: ISSUE 本文は「デフォルト 20 件程度」を提案するが、現行の SKILL 経由呼び出しを破壊しないため、CLI デフォルトは `None`（全件維持）にし、SKILL 側で明示的に `--limit 20` を指定する 2 段階方式を推奨。最終確定は IMPLEMENT.md
3. **truncation の通知方式**: `text` 出力には末尾に補足行を、`json` 出力にはトップレベル `total` / `truncated` / `limit` フィールドを追加するか、`items` 内に閾値超過情報を持たせるか
4. **priority 順保証の追加検証**: `collect()` 現行ロジックで priority → file name の順序保証は成立しているが、テストで明示する
5. **SKILL ファイル編集経路**: `.claude/skills/issue_plan/SKILL.md` の編集には `claude_sync.py export → import` が必要（`-p` モード制約）。コミット時は `.claude/` 配下と `.claude_sync/` 配下の双方が同期されていること
6. **後続 SKILL（`/retrospective`）への影響確認**: `/retrospective` SKILL も `issue_worklist.py` を使うため（`PHASE6.0.md` §4 / ver9.0 で実装済）、`--limit` 未指定の現行呼び出しに変化が出ないことをコード読みで再確認
7. **`text` 出力のヘッダー行（`[category]`）と truncation 補助行の干渉**: 既存の text 出力フォーマットを破壊しないこと
8. **`IMPLEMENT.md` 作成後の `plan_review_agent` 観点**: `--limit` のデフォルト値（CLI レイヤと SKILL レイヤで二段構え）の意図が伝わる設計説明を含めるよう指摘されうる

上記は `IMPLEMENT.md` で詳細化・棄却判断を行う前提の論点リストであり、本 ROUGH_PLAN 時点では実装方式に踏み込まない。
