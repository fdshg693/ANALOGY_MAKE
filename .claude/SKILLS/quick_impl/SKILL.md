---
name: quick_impl
description: 軽量ワークフロー用の実装ステップ（実装 + MEMO対応を統合）
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`

## 実装

最新バージョンフォルダ配下の `ROUGH_PLAN.md`（変更方針）と `PLAN_HANDOFF.md`（後続 step への注意点・関連 ISSUE パス）に基づいて実装を行う。`PLAN_HANDOFF.md` が存在しない場合（`/issue_plan` が handoff 情報ゼロと判定し省略したケース）は `ROUGH_PLAN.md` のみで進めてよい。

- サブエージェントの利用は任意（小規模なので直接実装が効率的な場合が多い）
- 実装中に `ROUGH_PLAN.md` の計画と異なる判断をした場合は、乖離の内容と理由を `MEMO.md` に記載すること
- ワークフロー YAML（`scripts/claude_loop*.yaml`）を追加 / 削除する場合は、`.claude/rules/scripts.md` §3 / `scripts/USAGE.md` / `scripts/README.md` / 既存 YAML 先頭 NOTE の 4 箇所を同期更新すること

## 品質確認

- `npx nuxi typecheck` を最低 1 回実施
- `pnpm test` を実施（テストが存在する場合）
- `ROUGH_PLAN.md` でテスト方針が指定されている場合は、そのテストも作成・実行すること

## MEMO

実装完了後、以下のような点があれば `MEMO.md` に記載する:

- 未修整のリントエラー・テストエラー
- リファクタリングの必要性を感じた点
- 調査に時間がかかりドキュメント化されるべきと感じた点
- 更新が必要そうなドキュメントと更新内容の案
- 古くて削除が推奨されるコード・ドキュメントの提案

MEMO 項目がある場合は **その場で対応する**（wrap_up ステップが存在しないため）:
- 対応可能な項目はその場で修正する
- 対応不可能な項目は `ISSUES/{カテゴリ}` に記載する

## Git にコミットする
- 実装変更をコミットする
- コミットメッセージ: 変更内容に応じた適切なメッセージ（例: `fix(util): ログ出力エラーを修正`）
- **プッシュは不要**
