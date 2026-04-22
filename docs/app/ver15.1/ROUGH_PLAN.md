# ver15.1 ROUGH_PLAN — 検索設定の動的切り替え

## バージョン種別

マイナーバージョン（15.0 → 15.1）。

理由:
- ver15.0 で構築した動的設定システム（`ThreadSettings` + `settings` カラム + 設定 API + `SettingsPanel.vue` + `useSettings` composable）を拡張するのみ
- 新アーキテクチャ・新ライブラリの導入なし
- PHASE3 項目1「動的設定システム」の残サブ項目（1.2）であり、1.1 の自然な続き

## 対象

MASTER_PLAN `PHASE3.md` 項目1.2「検索設定」に対応。

ISSUES 状況:
- `ISSUES/app/high/` は空 → MASTER_PLAN 推進を優先
- `ISSUES/app/medium/動作確認便利化.md` は PHASE3 項目4 と対応しており、項目1.2 の後で別バージョンに回す

## スコープ

Tavily Web検索のパラメータをユーザーがスレッドごとに制御できるようにする。

### 追加する設定項目

| 項目 | 型・選択肢 | デフォルト |
|---|---|---|
| Web検索 ON/OFF | boolean（トグル） | `true` |
| 検索深度 | `'basic' \| 'advanced'` | `'basic'` |
| 取得件数 | 整数 1〜10 | `3` |

### ユーザー体験の変化

- 設定パネルに「検索設定」セクションが追加される
- Web検索 OFF 時: `caseSearchNode` が Tavily を呼び出さず、LLM 内部知識のみで事例を生成
- 検索深度・件数は `performSearch()` が読み取り、Tavily 呼び出し時のパラメータに反映
- 設定変更は次回の AI 応答から即座に反映（過去の応答は変わらない）
- 設定はスレッドごとに保持（ver15.0 と同様）

### 適用範囲

- 対象ノード: `caseSearchNode` のみ（検索を呼ぶのはこのノードのみ）
- `abstraction` / `solution` / `followUp` ノードは検索設定の影響を受けない

## スコープ外（ver15.1 では実施しない）

- PHASE3 項目2「検索結果の可視化」（検索メタデータの SSE 送信・UI 表示）
- PHASE3 項目3「会話分岐」
- PHASE3 項目4「動作確認便利化」（エコーモード等）
- `abstraction` ノードへの粒度設定適用（ver15.0 の方針を継続）
- Tavily API キー未設定時の UI 上の検索設定無効化（バックエンドは従来どおりサイレントにスキップ）

## 前提条件

### 必須（ブロッカー）

- なし（ver15.0 の動的設定基盤が実装済み・テスト済み）

### 推奨（進行可能だが確認が望ましい）

- ver15.0 で導入した `SettingsPanel` の実機動作確認。未実施のままでも本バージョンの実装は進行可能だが、UI の拡張前に一度動作を見ておくと安全

※ 前提条件の分類は ver15.0 RETROSPECTIVE の改善提案 4-A に基づく。

## 事前リファクタリング不要

ver15.0 の設定基盤は `ThreadSettings` インターフェースの拡張と `config.configurable.settings` 経由の受け渡しで透過的に拡張可能な設計になっており、ver15.1 で追加する検索設定フィールドをそのまま載せられる。
