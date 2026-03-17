# vitest エイリアス不整合 + auto-import モック問題

## 概要

vitest のテスト環境で2つの関連する問題がある。`@nuxt/test-utils` の導入により統合的に解決できる可能性がある。

## 問題1: エイリアスの不整合

`vitest.config.ts` の `~` エイリアスはプロジェクトルートを指すが、Nuxt の `~` は `app/` を指す。
現状は composable テストで相対パス（`../utils/sse-parser`）で回避しているが、`app/` 配下のモジュール間参照が増えると保守コストが上がる。

## 問題2: auto-import のモック

composable が Nuxt の auto-import（`ref` 等）に依存しているため、テストでは `vi.stubGlobal('ref', ref)` でグローバルに注入している。
composable が増えると `watch`, `computed`, `onMounted` 等も同様にスタブが必要になり、テストのボイラープレートが増加する。

## 解決案

- `@nuxt/test-utils` を導入し、Nuxt のエイリアス解決と auto-import を テスト環境にも適用する
- `vitest.config.ts` のエイリアス設定を見直す（`~` → `app/` へのマッピング追加）

## 発生バージョン

ver8（composable 導入時）
