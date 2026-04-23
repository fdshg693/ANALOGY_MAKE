# ver6.0 ROUGH_PLAN: ISSUE ステータス・担当管理（PHASE5.0）

## 位置づけ

- **種別**: メジャーバージョン (ver6.0)
- **理由**: MASTER_PLAN PHASE5.0 に新規着手する。新規 SKILL（`issue_review`）の追加と、既存 SKILL `split_plan` / `quick_plan` の冒頭プロトコル変更を伴う。ISSUE ファイルの扱い方（着手対象の選定ルール）そのものが変わるため、ワークフロー挙動の意味論的変更に該当する
- **参照**: `docs/util/MASTER_PLAN/PHASE5.0.md`（フェーズ定義の原典）、`docs/util/ver5.0/RETROSPECTIVE.md` §3（ver6.0 として PHASE5.0 を推奨）

## 目的

ISSUE ファイルに **成熟度（status）** と **次アクション担当（assigned）** を導入し、plan ステップが拾う ISSUE を「着手可能（ready）」なものに限定することで、情報不足のまま実装方針が決まる事故を防ぐ。同時に、AI が気づいた課題を起票する際のラベル体系を整え、人間待ち / AI 側の未整理メモ / 着手可能キュー を区別する。

## スコープ（このバージョンで実現するもの）

### ユーザー体験の変化

1. **plan ステップ開始時に ISSUE レビューフェーズが挿入される**
    - `/split_plan` および `/quick_plan` の冒頭で、`status: review` の ISSUE を AI が一件ずつ確認し、`ready` または `need_human_action` のどちらかに振り分ける
    - レビュー結果と全体の ISSUE 分布がサマリとして出力される
2. **plan ステップの着手対象が `ready / assigned: ai` に限定される**
    - フロントマター無しの ISSUE は `raw / human` 扱いとなり、着手対象には入らない（人間が明示的に ready を付ける / review に回すまで放置される）
    - 未成熟な ISSUE が意図せず実装フローに乗るリスクがなくなる
3. **AI が ISSUE を起票する際の作法が定まる**
    - AI 起票時は必ず `raw | ready | need_human_action` のいずれかを付与する
    - `review` は人間 → AI へのレビュー依頼専用のステータスとして意味的に予約される
4. **人間への依頼が明示化される**
    - `need_human_action` に振り分けられた ISSUE の本文には、AI が具体的な依頼（再現手順・秘密値取得・仕様確認など）を追記する
    - 人間はそこを見れば何をすべきか分かる
5. **ISSUE の分布を一目で確認できるコマンドが入る**
    - カテゴリごと・優先度ごとに `status × assigned` の件数を表示するスクリプトを追加
    - レビュー待ち件数や人間対応待ち件数が可視化される

### 含むもの

- フロントマター仕様の策定（`status`, `assigned`, 任意の `priority` / `reviewed_at`）
- 共通 SKILL `issue_review` の新設（ISSUE スキャン → review 詳細化 → サマリ出力 まで）
- `split_plan` / `quick_plan` への組み込み（冒頭で `issue_review` 呼び出し + `ready / ai` 絞り込み）
- フロントマター仕様書 `ISSUES/README.md` の新規作成
- `scripts/issue_status.py` の新規作成（分布表示のみ、書き換えはしない）
- 既存 ISSUE の移行ガイド `docs/util/ver6.0/MIGRATION.md` の整備
- 後方互換: frontmatter 無しの既存 ISSUE はすべて `raw / human` として扱う（SKILL 側・スクリプト側の双方で同じフォールバックを適用。パース失敗時の挙動は IMPLEMENT.md で定義）

### 含まないもの

- ステータスの自動遷移（`raw → review` などは必ず明示的編集）
- `raw → review` を一括で進めるヘルパー（意図せぬレビュー起動を避けるため）
- CI / GitHub Actions でのフォーマット検査
- 過去 ISSUE の自動一括マイグレーション（ユーザーが個別に ready / review を付与）
- `assigned` を超える追加メタデータ（`team` / `estimated_hours` 等）
- `done/` への自動移動（従来どおり `quick_doc` / `wrap_up` が担当）

## 想定される差分の広さ

- 新規: `ISSUES/README.md`, `.claude/skills/issue_review/SKILL.md`, `scripts/issue_status.py`, `docs/util/ver6.0/MIGRATION.md`
- 変更: `.claude/skills/split_plan/SKILL.md`, `.claude/skills/quick_plan/SKILL.md`
- ドキュメント: `docs/util/ver6.0/` 配下（計画・実装記録）
- 既存 ISSUE ファイル（`ISSUES/**/*.md`）は **一切触らない**。移行は次バージョン以降でユーザーが手動で進める

小規模タスクの閾値（3 ファイル以内・100 行以内・新規作成不要）を超えるため、フルワークフローを継続する。

## 事前リファクタリング

不要。新規 SKILL の追加と既存 SKILL の冒頭差し込みが中心で、既存コードの構造変更を要する箇所は無い。`split_plan` / `quick_plan` の SKILL も、冒頭に `issue_review` 呼び出しを追加し、着手対象選定ロジックを `ready / ai` 絞り込みに差し替えるだけで済む。

## 成否の判定基準

- `.claude/skills/issue_review/SKILL.md` が存在し、`/issue_review` としてサブ SKILL 呼び出しが成立する
- `/split_plan` および `/quick_plan` の冒頭でレビュー結果サマリが出力される
- フロントマター無しの既存 ISSUE が、レビュー後も書き換わらず残る（後方互換の確認）
- `python scripts/issue_status.py util` が分布を出力できる
- `ISSUES/README.md` を読めば、人間が新規 ISSUE を作成するときのルールが分かる
