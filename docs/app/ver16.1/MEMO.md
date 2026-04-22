# ver16.1 MEMO — 実装メモ・残課題

## 実装サマリ

IMPLEMENT.md の手順通りに実装完了。以下 2 機能を追加:

1. **エコーモード**: `ThreadSettings.responseMode = 'ai' | 'echo'`
   - `chat.post.ts` で echo 時は `handleEchoResponse()` に分岐し、LangGraph をバイパス
   - 8 文字単位・30ms 間隔で `token` SSE を配信後、`agent.updateState()` で `[HumanMessage, AIMessage]` を永続化
   - タイトル生成は LLM を使わず入力先頭 10 文字を流用
2. **システムプロンプト上書き**: `ThreadSettings.systemPromptOverride`
   - `buildSystemPrompt()` が `process.env.NODE_ENV !== 'production'` 下でのみベースプロンプトの先頭に `\n\n---\n\n` 区切りで追記
   - サーバー側 `settings.put.ts` は本番環境で空文字に正規化（UI 迂回防止の二重防御）
   - フロント UI は `import.meta.dev` で表示切替

## 計画との乖離

なし。REFACTOR.md は存在しないためスキップ。IMPLEMENT.md §7 の実装順序通り。

## リスク・不確実性の結果（IMPLEMENT.md §8 対応）

### R1 — `agent.updateState()` による会話履歴追加 / SQLite での型復元
- **状態**: **検証先送り（手動確認に委ねる）**
- **理由**: Vitest のモック環境では LangGraph 実機と SqliteSaver の往復を再現できず、単体テストで「送信→リロード→履歴復元」を機械検証することは設計上不可能。デプロイ環境での手動確認が必要
- **本番発生時の対応方針**: IMPLEMENT.md 4.4 のフォールバック案（`agent.updateState()` 呼び出しを削除し、エコーモードを「純粋 SSE 返却のみ・履歴保存なし」に切り替え）を採用。設定パネルに「エコーモード: リロードで消えます」の注記を追加し、追随 ISSUE を起票
- **手動確認項目（デプロイ後）**:
  1. エコーモードで 1 往復送信
  2. ページをリロードして履歴に表示されることを確認
  3. エコーで永続化したメッセージ後に AI モードに戻して送信 → `currentStep` が破綻しないかを確認

### R2 — `responseMode` 切り替え時の `currentStep` 整合性
- **状態**: **検証不要（制限事項として記録）**
- **理由**: エコーモードは `updateState` で `messages` のみ追加し `currentStep` を変更しない設計。`awaiting_selection` 状態でエコー送信→AI に戻すと、次の AI 応答が「直前のエコーメッセージ＝選択」として `solution` ノードに流れる仕様は設計意図通り
- **引き継ぎ**: 想定挙動だが UI 確認中に混乱する可能性あり → 本 MEMO で注意書きとして記録

### R3 — 環境判定（サーバー `NODE_ENV` / フロント `import.meta.dev`）の整合
- **状態**: **検証済み**
- **結果**: サーバー側 `process.env.NODE_ENV !== 'production'` 判定は `prompt-builder.test.ts` / `settings-api.test.ts` で `vi.stubEnv` により production 挙動（上書き無視・空文字正規化）を検証済み。フロント側は `import.meta.dev` のビルド時定数で DOM が除去される想定（UI テストは対象外）

### R4 — エコー配信の SSE コスト（30ms/8 文字）
- **状態**: **検証不要（現スコープ外）**
- **理由**: 動作確認便利化が目的のため、長文入力でのタイムアウトは想定外ケース。1 万文字で 37.5 秒だが、開発者が自発的に使うのみで実運用負荷にはならない
- **本番発生時の対応方針**: 必要になった時点で `chat.post.ts` のバリデーションに入力文字数上限を追加する ISSUE を起票

### R5 — 本番での `systemPromptOverride` 残留データ
- **状態**: **検証済み**
- **結果**: `settings.put.ts` が本番環境では空文字で上書きするため、次回保存で自動クリーン。`buildSystemPrompt()` も dev ガードで無視するため、仮に DB に残存していても production 動作には影響しない。`tests/server/settings-api.test.ts` の「本番環境での systemPromptOverride 正規化」ケースで確認済み

## 追加の手動確認（ユーザーへ引き継ぎ）

デプロイ後にエコーモードで 1 往復を行うと、`updateState → getState` 経路が通るため ver16.0 で起票済みの以下 ISSUES を同時に確認可能:

- `ISSUES/app/medium/getState-timing.md` — エコーで送信直後に履歴リロード → 直近 AIMessage が取れるか
- `ISSUES/app/medium/additional-kwargs-sqlite.md` — エコー専用では追加 kwargs を設定していないため直接は確認不能。AI モードでの検索結果永続化は別途必要

## 未修整のリントエラー・テストエラー

なし。全 107 テスト pass（+14 ケース追加: settings-api +4、thread-settings +2、prompt-builder +4、chat +4）。

## 今後のドキュメント更新（本フローの対象外）

- `CLAUDE.md` の「環境変数」節に `NUXT_OPENAI_API_KEY` / `NUXT_TAVILY_API_KEY` と並べて `NODE_ENV` が `systemPromptOverride` の dev ガードに使われる旨を補足するか検討（現状 Azure 側での `NODE_ENV=production` 注入は既存前提のため、明文化は低優先度）
- ver16.1 の `CURRENT.md` は不要（マイナーバージョン）。ver17.0 以降の CURRENT.md で `ThreadSettings` の 5 フィールド構成を反映すればよい

## 削除推奨なし

ISSUES/app/medium/動作確認便利化.md は本バージョン完了に伴い削除可能（別途 IMPLEMENT.md §10 参照）。本実装で該当 ISSUE の要件を全て満たしたため、次段で削除する。

---

## wrap_up 完了記録（2026-04-22）

- `npx nuxi typecheck` 実行 → 型エラーなし（vue-router volar の既知警告のみ）
- `ISSUES/app/medium/動作確認便利化.md` は既に削除済みを確認
- `getState-timing.md`・`additional-kwargs-sqlite.md` はデプロイ後手動確認待ちのため現状維持
- コード変更なし → コミットスキップ
