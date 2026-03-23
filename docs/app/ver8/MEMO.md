# ver8 実装メモ

## 計画との乖離

なし。IMPLEMENT.md の計画通りに実装完了。

## vitest エイリアスの不整合

`vitest.config.ts` の `~` エイリアスはプロジェクトルートを指すが、Nuxt の `~` は `app/` を指す。今回の composable では相対パス（`../utils/sse-parser`）で回避したが、今後 `app/` 配下のモジュール間参照が増えると、テストごとに相対パスの調整が必要になる。

vitest.config.ts にエイリアスを追加する案（例: `~/utils` → `app/utils`）を検討する価値はあるが、既存の `~/server/` パスとの共存が必要なため、単純な変更では対応できない。`@nuxt/test-utils` の導入（Nuxt のエイリアス解決をテスト環境にも適用）も選択肢。

> **📋 wrap_up 対応**: 次バージョンへ先送り。`ISSUES/low/vitest-nuxt-test-utils.md` に起票済み。

## テストにおける auto-import のモック

composable が Nuxt の auto-import（`ref`）に依存しているため、テストでは `vi.stubGlobal('ref', ref)` でグローバルに注入している。composable が増えると `watch`, `computed`, `onMounted` 等も同様にスタブが必要になる。`@nuxt/test-utils` の `mockNuxtImport` の導入を検討する価値がある。

> **📋 wrap_up 対応**: 次バージョンへ先送り。エイリアス問題と合わせて `ISSUES/low/vitest-nuxt-test-utils.md` に起票済み。

## 更新が必要なドキュメント

- `CLAUDE.md` の「ディレクトリ構成」に `app/composables/` の記載を追加
- `docs/ver8/CURRENT.md` の作成（別フローで対応）

> **✅ wrap_up 対応**: `CLAUDE.md` に `app/composables/` を追記完了。`CURRENT.md` は別フローのためスコープ外。
