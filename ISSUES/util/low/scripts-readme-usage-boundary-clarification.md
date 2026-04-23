---
status: raw
assigned: ai
priority: low
reviewed_at: "2026-04-24"
---
# scripts/README.md と scripts/USAGE.md の責務境界整理

## 概要

`scripts/README.md`「拡張ガイド」節と `scripts/USAGE.md`「拡張ガイド」節に内容の重複がある。現状は rules 側へ stable 規約を集約（ver14.0 §7）して整合をとったが、README / USAGE の責務境界自体は整理されていない。

理想的な分担:
- `README.md` = 全体構成・スクリプト一覧・validation spec（**what** を記述）
- `USAGE.md` = 操作手順・CLI オプション・ワークフロー継承ルール（**how to use** を記述）

現状「拡張ガイド」が両ファイルに存在し、読み手がどちらを見ればよいか迷う可能性がある。

## 想定対応

1. `scripts/README.md` の「拡張ガイド」節を削除 or `scripts/USAGE.md` へ統合
2. `scripts/USAGE.md` 内の「拡張ガイド」を「拡張手順」として spec 寄りの内容は `README.md` に移動
3. 両ファイルに `See also:` 的な相互リンクを追記

## 参照

- ver14.0 `MEMO.md`「将来のリファクタ・ドキュメント候補」節
- `scripts/README.md` L147-149（「拡張ガイド」節）
- `scripts/USAGE.md` L235-241（「拡張ガイド」節）
- `.claude/rules/scripts.md`（stable 規約の一次資料）
