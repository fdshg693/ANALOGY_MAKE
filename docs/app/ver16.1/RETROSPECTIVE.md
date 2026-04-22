# ver16.1 RETROSPECTIVE

## 実装サマリー

| 項目 | 内容 |
|---|---|
| カテゴリ | app |
| バージョン | 16.1（マイナー） |
| 対象 | PHASE3 項目4: 動作確認便利化（エコーモード + システムプロンプト上書き） |
| コミット範囲 | `007b74a`（split_plan）→ `84040b2`（write_current） |
| 変更規模 | 14 ファイル、+606 行 / -21 行（うちコード 6 ファイル、+136 行 / -4 行 + テスト 4 ファイル、+305 行 / -16 行） |
| テスト | 10 ファイル 93 ケース → 10 ファイル 107 ケース（+14） |

### 実装内容

`ThreadSettings` に `responseMode: 'ai'|'echo'` と `systemPromptOverride: string` を追加。エコーモードは `chat.post.ts` で LangGraph をバイパスし、ユーザー入力を 8 文字/30ms で SSE 配信、`agent.updateState()` で永続化。システムプロンプト上書きは dev 環境でのみ `buildSystemPrompt()` がベースの先頭に追記し、本番ではサーバー・UI 両面で無効化。

---

## 1. ドキュメント構成整理

### MASTER_PLAN

PHASE3 残項目:

- ✅ 1.1 AI 回答粒度設定 — ver15.0
- ✅ 1.2 検索設定 — ver15.1
- ✅ 2. 検索結果の可視化 — ver16.0
- 3. 会話分岐 — 未着手
- ✅ 4. 動作確認便利化 — ver16.1

**判断**: PHASE3 は項目3「会話分岐」のみ残。MASTER_PLAN 本体は 17 行と軽量で再構成不要。次メジャー 17.0 で PHASE3 完了、その後の新フェーズは 17.0 着手後に検討。

### CLAUDE.md

約 100 行、現状維持で問題なし。ver16.1 では `ThreadSettings` に 2 フィールド追加のみでアーキテクチャ変更なし、開発者向け新規注意点は発生せず。

### ISSUES

| カテゴリ | 優先度 | 件数 | 備考 |
|---|---|---|---|
| app | high | 0 | — |
| app | medium | 2 | `getState-timing`, `additional-kwargs-sqlite`（ver16.0 追加、未検証のまま継続） |
| app | low | 2 | `syntax-highlight`, `vitest-nuxt-test-utils` |

ver16.0 の medium 3 件から「動作確認便利化」を本バージョンで解消し 2 件に減少。残 2 件はデプロイ実機検証待ち。

---

## 2. バージョン作成フローの振り返り

### 各ステップの評価

| ステップ | 評価 | コメント |
|---|---|---|
| split_plan | ◎ | ROUGH_PLAN で 2 機能を同一バージョンに束ねる判断を明文化、IMPLEMENT.md 368 行で環境判定の使い分け（サーバー `NODE_ENV` / フロント `import.meta.dev`）を決定。マイナーで REFACTOR.md 不要判定もルール通り |
| imple_plan | ◎ | 計画との乖離ゼロ。リスク 5 件を「検証済み／検証不要／検証先送り」で全件分類（ver16.0 のパターン踏襲、スキル明文化の効果） |
| wrap_up | ○ | MEMO に未解決項目がほぼなく、typecheck と ISSUES 削除確認のみの軽量対応。「コード変更なしのためコミットスキップ」の判断も正しく機能 |
| write_current | ○ | マイナーのため `CURRENT.md` スキップ、`CHANGES.md` 100 行で ver16.0 からの差分を網羅 |
| retrospective | — | 本ステップ |

### 良かった点

1. **ver16.0 スキル改善の効果が即時確認できた**: ver16.0 retrospective で imple_plan SKILL に「検証先送りリスクは ISSUES 化する」明文化を即時適用。ver16.1 では R1 を「検証先送り → デプロイ後手動確認」として MEMO に記録、ただし既存 ISSUES（`getState-timing` / `additional-kwargs-sqlite`）が同じ検証パスでカバーされるため新規 ISSUES は起票せず、MEMO から既存 ISSUES を明示参照。スキル規定を機械的に適用せず「既存 ISSUES で補足可能」を判断できた

2. **2 機能バンドルの判断が正当化された**: エコーモード + システムプロンプト上書きの 2 機能を同一マイナーに束ねた。両者とも `ThreadSettings` への追加・dev/prod ガード・UI 追加という同構造で、テストフィクスチャ更新のコストを一度で済ませられた（既存テスト 5 ケースのアサーション更新）。別バージョンに分割すると `DEFAULT_SETTINGS` 参照を 2 回更新する冗長作業になっていた

3. **環境判定の二本立て決定がスムーズ**: サーバー側 `process.env.NODE_ENV` / フロント側 `import.meta.dev` の使い分けを IMPLEMENT.md §3.2 で事前決定し、Vitest での `vi.stubEnv` 制御可能性を理由に採用。実装・テスト段階で判断の揺り戻しなし

### 改善すべき点

1. **実機確認 7 バージョン連続先送り**

   ver14.3 以降、dev サーバー起動・ブラウザ動作確認なしで進行中。ver16.1 は特にリスク R1（`agent.updateState()` の SQLite 往復）がユニットテストで原理的に検証不能で、デプロイ後の手動確認に依存する構造。エコーモードは「動作確認便利化」という UI 確認目的なのに、その機能自体が未確認という皮肉な状況。

   **影響**: 中（ver16.0 までの「視覚面のみ」から、ver16.1 では「機能の動作そのもの」が未確認領域に入った）。
   **対応**: スキル変更は引き続き提案しない（非対話セッションでの制約であり SKILL の問題ではない）。次バージョン着手前にユーザー側でデプロイ 1 往復確認を推奨 → ISSUES 2 件と R1 を同時に解消できる。

2. **`ThreadSettings` フィールド増加による既存テスト更新コスト**

   `thread-settings.test.ts` / `settings-api.test.ts` で完全一致アサーション 5 件を新フィールド込みに更新。ver15.1（`search` 追加）、ver16.1（`responseMode` + `systemPromptOverride` 追加）の 2 回連続で同種の更新が発生。今後 `ThreadSettings` が拡張されるたびに同じコストが生じる。

   **影響**: 低（機械的な更新作業で実装リスクは低い）。
   **対応提案**: **提案のみで即時適用せず**。テスト側で `{ ...DEFAULT_SETTINGS, ...override }` パターンを使うヘルパを導入すれば既存テスト更新コストが削減できるが、リファクタ自体が複数テスト横断で 200 行規模になる見込み。次メジャー ver17.0 の REFACTOR フェーズで検討。

### 前回（ver16.0）改善提案の効果検証

| ver16.0 RETROSPECTIVE での改善提案 | ver16.1 での実績 |
|---|---|
| imple_plan SKILL に「検証先送り→ISSUES 化」を明文化（即時適用済） | **◎**: ver16.1 MEMO.md R1 で本パターンを適用、ただし既存 ISSUES で代替可能と判断して新規起票を回避。スキル規定を機械的でなく文脈に即して運用できた |
| 実機確認の継続（スキル変更しない方針） | **△ 継続先送り 7 回目**: 方針は維持。ver16.1 でリスクレベルは上昇（機能そのものが未確認領域） |

---

## 3. 次バージョンの種別推奨

### 推奨: マイナーバージョン 16.2（デプロイ検証 + 軽量整理）を先に挟み、その後メジャー 17.0

**理由**:

ver16.0 retrospective では 17.0（会話分岐）を推奨したが、ver16.1 で実機未検証リスクがさらに上積みされた（エコーモードの永続化パスが未確認）。会話分岐はデータモデル拡張と UI 構造変化を伴う大物で、未検証のまま積み上げると顕在化時の切り分けが難しくなる。1 度デプロイ実機検証を挟むのが望ましい。

### 推奨する 16.2 の内容（軽量マイナー）

- `ISSUES/app/medium/getState-timing.md` 手動確認 → close
- `ISSUES/app/medium/additional-kwargs-sqlite.md` 手動確認 → close
- ver16.1 エコーモード R1 の実機確認（`updateState → getState` 往復）
- 必要に応じて小規模な型整理（`ThreadSettings` / `SearchResult` の型重複定義、ver15.1 MEMO / ver16.0 IMPLEMENT で言及）

### 他の候補

| 候補 | バージョン | 優先度 | コメント |
|---|---|---|---|
| デプロイ検証 + 軽量整理 | 16.2 | **推奨** | 7 バージョン積んだ実機未検証を 1 度解消、ISSUES 2 件 close 見込み |
| PHASE3 項目 3: 会話分岐 | 17.0 | 高 | 16.2 後の本命。データモデル + UI 拡張、メジャー相当 |
| 型重複定義解消 (`shared/types/`) | 16.2 と同梱可 | 低 | 独立で切るほどではない |

**ユーザー判断が必要な分岐**: 16.2 を挟むか直接 17.0 に進むか。ただし 16.2 はスキーマ変更不要で実機確認 + 軽量整理のみのため、1〜2 コミット規模で済む見込み。

---

## 4. スキル改善（本ステップで即時適用）

### 改善提案なし

ver16.1 のフローは split_plan〜write_current まで既存スキルで円滑に流れた。特に以下は前回の即時適用が機能している:

- imple_plan SKILL の「検証先送り → ISSUES 化」規定（ver16.0 追加）→ ver16.1 で自然に運用、かつ「既存 ISSUES で代替可能」な場合の回避判断も機能
- split_plan SKILL の前提条件分類ガイド（ver15.1 追加）→ ver16.1 ROUGH_PLAN でも継続適用

改善すべき点 2「`ThreadSettings` 拡張時の既存テスト更新コスト」はスキル変更ではなくコード側のテストヘルパ導入で対処すべき性質のため、スキル編集はしない。

---

## 5. 対応済み ISSUES

| ISSUES | 状態 |
|---|---|
| `ISSUES/app/medium/動作確認便利化.md` | ver16.1 で完了・削除済み（本バージョン内で実施） |
| `ISSUES/app/medium/getState-timing.md` | 未対応（デプロイ実機確認待ち、16.2 で close 見込み） |
| `ISSUES/app/medium/additional-kwargs-sqlite.md` | 未対応（同上） |
| `ISSUES/app/low/syntax-highlight.md` | 未対応（優先度 low、着手時期未定） |
| `ISSUES/app/low/vitest-nuxt-test-utils.md` | 未対応（同上） |

本ステップでの追加削除はなし。
