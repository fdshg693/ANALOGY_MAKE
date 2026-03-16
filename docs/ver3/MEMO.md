# ver3 実装メモ

## 実装時の修正点

- `createAgent` の API パラメータ名が `prompt` ではなく `systemPrompt` だった。IMPLEMENT.md の設計と実験コード（02-memory-management.ts）の両方で `prompt` を使用していたが、TypeScript 型チェックで検出されたため `systemPrompt` に修正。実験スクリプトは `tsx` 実行のため型エラーが顕在化していなかった

## wrap_up 時の対応

- ✅ **アナロジープロンプトの二重管理解消**: `experiments/03-analogy-prompt.ts` を削除。正式版は `server/utils/analogy-prompt.ts` に一本化
- ✅ **環境変数・HMR・既知警告の注意事項**: `docs/DEV_NOTES.md` を新規作成し、`.env.example` の `NUXT_OPENAI_API_KEY` の経緯（Nuxt runtimeConfig 自動マッピング）、シングルトン+HMR の注意点、既知の TypeScript 警告をまとめて記載

## 対応不要と判断した事項

- `npx nuxi typecheck` の vue-router volar 警告: ver1 から存在する既知の問題。ビルド・実行に影響なし。`docs/DEV_NOTES.md` に記載済み
