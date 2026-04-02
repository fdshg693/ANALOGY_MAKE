# ver14.2 CHANGES — ストリーミング表示のレンダリング最適化

## 変更ファイル一覧

| ファイル | 変更種別 | 概要 |
|---|---|---|
| `app/components/ChatMessage.vue` | 変更 | Markdown レンダリングを `computed` から `ref` + `watch` に変更し、スロットリングを追加 |
| `app/pages/index.vue` | 変更 | ChatMessage に `isStreaming` prop を受け渡し |
| `ISSUES/app/low/streaming.md` | 削除 | 対応完了のため ISSUE をクローズ |

## 変更内容の詳細

### ChatMessage.vue — Markdown レンダリングのスロットリング

**課題**: ストリーミング中、トークンを1つ受信するたびに `marked.parse()` + `DOMPurify.sanitize()` が全文に対して実行されていた。500トークンのレスポンスでは500回の全文解析が走り、後半になるほどレンダリングが重くなる問題があった。

**変更内容**:

- `renderedHtml` を `computed` から `ref` に変更
- `renderMarkdown()` 関数を抽出し、`watch` + タイムベーススロットリング（80ms 間隔、`RENDER_THROTTLE_MS` 定数）で呼び出す方式に移行
- `props.isStreaming` を新規 prop として追加
- ストリーミング中: `content` 変更時に最大 80ms に1回だけレンダリング実行（~92% 削減）
- ストリーミング完了時: `isStreaming` が `false` になった瞬間に即座に最終レンダリング
- 履歴ロード時: `isStreaming` が `false` なので即時レンダリング（既存動作維持）
- `onBeforeUnmount` でタイマーをクリーンアップ

### index.vue — isStreaming prop の受け渡し

- ChatMessage の `v-for` ループに `:is-streaming="isStreaming && i === messages.length - 1"` を追加
- ストリーミング中のメッセージは常に `messages` 配列の最後の要素であるため、最後のメッセージにのみフラグを渡す

## 技術的判断

### スロットリング方式の選定

| 方式 | 判定 | 理由 |
|---|---|---|
| requestAnimationFrame (~16ms) | 不採用 | 60fps は Markdown パースにはまだ頻繁すぎる |
| **タイムベーススロットリング (80ms)** | **採用** | ~12.5回/秒で滑らかかつ軽量。間隔の調整も容易 |
| ストリーミング中は生テキスト表示 | 不採用 | リッチ表示がなくなり UX が低下 |

### 不完全 Markdown の修復ロジックは見送り

スロットリングにより崩れの表示時間が短縮されるため、未閉じフェンスの自動閉鎖等の追加ロジックは不要と判断。`marked` のベストエフォートレンダリングで十分。
