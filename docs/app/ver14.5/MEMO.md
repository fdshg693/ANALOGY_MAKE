# ver14.5 MEMO

## 計画との乖離

### フェーズ1（調査）のスキップ

IMPLEMENT.md ではフェーズ1として対話的な調査（`pnpm dev` → ブラウザ確認 → ログ確認 → CLI 確認）を計画していたが、以下の理由でスキップし直接フェーズ2（修正）を適用:

- **修正が前段階の結果に関わらず安全**: `type` プロパティベースの判定は `isInstance` の上位互換。LangChain クラスインスタンス（`type` プロパティあり）にもデシリアライズ後のプレーンオブジェクト（`type` プロパティあり、Symbol なし）にも対応する
- **調査にサーバー起動・ブラウザ操作が必要**: 非対話的セッションでは非効率
- **仮説 H1 の蓋然性が十分に高い**: `inspect-db.ts` が同じ `type` プロパティアプローチで正常動作している実績あり。LangChain のデシリアライズで Symbol が失われるのは既知パターン

## 実機確認の未実施

typecheck パス・テスト全55件パスを確認済み。ローカル dev サーバー + ブラウザでの実機確認は未実施。`ISSUES/app/medium/履歴修正-実機確認.md` の ISSUE が引き続き有効。

## 削除を推奨するもの

- **`ISSUES/app/medium/テストモック脆弱性-isInstance.md`**: `isInstance` を廃止し `type` プロパティベースに変更したため、このISSUE の前提が解消された。削除を推奨
- **ver14.4 のデバッグログ**: `server/api/chat/history.get.ts` に残っている `Raw messages from snapshot` / `Messages filtered out` のデバッグログは、本修正の効果を実機確認した後に削除を検討（確認完了まで保持が望ましい）
