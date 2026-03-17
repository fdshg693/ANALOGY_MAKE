# ver8 リファクタリング計画

## 結論: 事前リファクタリング不要

composable 切り出し自体がリファクタリングであり、それを阻害する技術的障害は存在しない。

### 理由

- `index.vue` のロジックは単一ファイルに閉じており、他コンポーネントとの結合が薄い（`ChatInput` は `@send` イベント、`ChatMessage` は props のみ）
- SSEパーサーはver7で既に `app/utils/sse-parser.ts` に分離済み
- `Message` インターフェースは `index.vue` 内でのみ定義されており、他ファイルからの参照がないため、移動が容易
- 既存テスト（SSEパーサー・チャットAPI）は composable 切り出しの影響を受けない
