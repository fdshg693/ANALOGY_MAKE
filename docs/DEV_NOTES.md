# 開発メモ・注意事項

開発時に知っておくべき細かな注意事項をまとめたファイル。

## 環境変数と Nuxt runtimeConfig

- `.env` には `OPENAI_API_KEY`（実験スクリプト用）と `NUXT_OPENAI_API_KEY`（Nuxt サーバー用）の2つがある
- Nuxt の runtimeConfig は `NUXT_` プレフィックス付きの環境変数を自動マッピングする仕様
  - `nuxt.config.ts` の `runtimeConfig.openaiApiKey` → 環境変数 `NUXT_OPENAI_API_KEY` が自動で注入される
  - 参考: https://nuxt.com/docs/guide/going-further/runtime-config#environment-variables

## エージェントのシングルトンと HMR

- `server/utils/analogy-agent.ts` はモジュールスコープ変数でエージェントをシングルトン保持している
- Nuxt の HMR（Hot Module Replacement）時にエージェントが再初期化されない可能性がある
- **`.env` の API キーを変更した場合はサーバーの再起動が必要**

## 既知の TypeScript 警告

- `npx nuxi typecheck` 実行時に `vue-router/volar/sfc-route-blocks` の `@vue/language-core` モジュール解決エラーが出る
  - ver1 から存在する既知の警告
  - npx 経由の vue-tsc と node_modules 内の vue-router volar プラグインの依存不整合が原因
  - ビルド・実行には影響なし
  - 解消を検討したが、手間に見合わないため、現状は放置することにした
