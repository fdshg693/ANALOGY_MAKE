# ver6 実装メモ

## 計画との乖離

- `@types/dompurify` は deprecated（dompurify v3 自体に型定義が内包されている）。計画通りインストールしたが、実質的に不要。将来的に `pnpm remove @types/dompurify` で削除してよい
  - ✅ **対応完了**: `pnpm remove @types/dompurify` で削除済み。typecheck で型エラーがないことを確認

## 残課題・気づき

- シンタックスハイライト（コードブロックの言語別色分け）は未実装。必要であれば `highlight.js` 等の導入を検討
  - 📋 **次バージョンへ先送り**: アナロジー思考の対話フローでコードブロックが頻出する場面は少なく優先度低。`ISSUES/low/syntax-highlight.md` に追加
- ストリーミング中の Markdown パース: `marked.parse()` はトークンが途中の状態でも呼ばれるため、不完全な Markdown（例: `**太字` が閉じる前）が一瞬崩れて表示される可能性がある。体感上は高速にトークンが流れるため目立たないが、気になる場合はストリーミング完了後のみ Markdown レンダリングに切り替える方式も検討可能
  - 📋 **次バージョンへ先送り**: 体感上の影響は軽微。既存の `ISSUES/low/streaming.md` に追記
