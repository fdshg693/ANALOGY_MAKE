# ver9 タスク概要

## 対応方針

ISSUES/high に未解決課題なし。MASTER_PLAN (PHASE1.5) の次の未着手項目を進める。

## 対応内容: 応答キャンセル機能

PHASE1.5 項目2「応答キャンセル機能」を実装する。

### 背景

現在、ストリーミング開始後はAIの応答が完了するまでユーザーが介入する手段がない。長い応答や意図しない方向の応答を途中で止めたい場面で、完了まで待つしかない状態である。

ver8で `useChat` composable が切り出し済みのため、ここに `abort()` 関数を追加する形で自然に実装できる。

### 提供される機能

- **応答の中断**: ストリーミング中にユーザーが「停止」ボタンを押すと、AIの応答生成を即座に中断できる
- **停止ボタンへの切り替え**: ストリーミング中は送信ボタンが「停止」ボタンに変化し、中断操作を直感的に行える
- **部分テキストの保持**: 中断時点までに受信済みのテキストはそのまま表示に残す（削除やエラー扱いにしない）
- **中断後の再入力**: 中断後すぐに次のメッセージを入力・送信できる

### 変更対象ファイル

- **`app/composables/useChat.ts`** — `AbortController` による `abort()` 関数の追加
- **`app/components/ChatInput.vue`** — `isStreaming` prop の追加、ストリーミング中は送信ボタンを停止ボタンに切り替え、`abort` イベントの emit
- **`app/pages/index.vue`** — `abort` 関数の受け渡し、`isStreaming` の ChatInput への prop 追加
- **`tests/composables/useChat.test.ts`** — `abort()` 関数に関するテストケースの追加、および `AbortController` 導入に伴う既存の正常系テスト（fetch 引数 assertion）の修正

### 事前リファクタリング不要

ver8で `useChat` composable が既に切り出されており、`abort()` の追加は既存構造に自然に組み込める。

### スコープ外

- ストリーミング表示の改善（チャンク粒度・Markdownパース安定化）は次バージョン以降
- ChatMessage コンポーネントの変更
- サーバーサイドの変更（fetch中断時のサーバー側処理は既存のstream closeで自然に終了する）
- 既存テスト（SSEパーサーテスト・チャットAPIテスト）の変更
