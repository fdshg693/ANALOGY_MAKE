# ver17.0 RETROSPECTIVE

## 実装サマリー

| 項目 | 内容 |
|---|---|
| カテゴリ | app |
| バージョン | 17.0（メジャー） |
| 対象 | PHASE3 項目3: 会話分岐（メッセージ編集 → 分岐生成 → 分岐切替） |
| コミット範囲 | `af8a970`（split_plan）→ `862164f`（write_current） |
| 変更規模 | 29 ファイル、+1406 行 / -129 行（新規 12 ファイル、変更 10 ファイル、テスト 15 ファイル） |
| テスト | 10 ファイル 112 ケース → 15 ファイル 145 ケース（+33、目標 137 を上回る） |

### 実装内容

- 新規テーブル `thread_branches`（`branch_id` PK、`parent_branch_id` + `fork_message_index`、`ON DELETE CASCADE`）と `branch-store.ts`
- LangGraph `thread_id` 合成ヘルパ `toLangGraphThreadId(threadId, branchId)`（main は raw、非 main は `${threadId}::${branchId}`）で既存スレッド互換
- API 3 本: `POST /api/chat/fork`（チェックポイントコピー + settings 更新、応答生成は `/api/chat` 再利用）、`GET /api/chat/branches`、`GET /api/chat/history?branchId=...`
- `ThreadSettings.activeBranchId` 追加 + PUT バリデーション（不正値は `main` フォールバック）
- `useBranches` composable 新規 + `useChat` の `switchThread(threadId, branchId)` 拡張
- `ChatMessage.vue` のホバー編集ボタン、`ChatInput.vue` の編集モード、`BranchNavigator.vue`（◀ N/M ▶）、`index.vue` 配線
- `deriveCurrentStep(messages)` を `analogy-agent.ts` に export（末尾メッセージヒューリスティクス）
- `tests/fixtures/settings.ts` の `makeThreadSettings()` 導入（ver16.1 retrospective 提案を本バージョンで実現）

---

## 1. ドキュメント構成整理

### MASTER_PLAN

PHASE3 状況:

- ✅ 1.1 AI 回答粒度設定 — ver15.0
- ✅ 1.2 検索設定 — ver15.1
- ✅ 2. 検索結果の可視化 — ver16.0
- ✅ 3. 会話分岐 — ver17.0（本バージョン）
- ✅ 4. 動作確認便利化 — ver16.1

**判断**: **PHASE3 は全項目完了**。次バージョンでの新機能着手には **新 PHASE（PHASE4）の MASTER_PLAN 作成が必要**。ただし現状 PHASE4 のネタは明確に用意されておらず、当面は以下で対応可:

- 次は ISSUES 起点のマイナーバージョン（17.1: デプロイ検証 + 軽量整理）が自然
- 本格的な PHASE4 起草はユーザーからの方向性提示（新機能の指示）を待つのが望ましい

→ **スキル変更不要**、`PHASE3.md` の完了マークで MASTER_PLAN 更新は完了している

### CLAUDE.md

約 100 行、現状維持。ver17.0 で新規ライブラリ追加なし、アーキテクチャ拡張は `thread_branches` テーブルと `::` 合成キー程度で、開発者視点の新規注意点は MEMO に記載済み（`better-sqlite3` の 2 接続経路は `ISSUES/app/low/db-connection-refactor.md` で追跡）。

### ISSUES

| カテゴリ | 優先度 | 件数 | 備考 |
|---|---|---|---|
| app | high | 0 | — |
| app | medium | 3 | `getState-timing`, `additional-kwargs-sqlite`, `fork-checkpoint-verification`（ver17.0 追加） |
| app | low | 3 | `syntax-highlight`, `vitest-nuxt-test-utils`, `db-connection-refactor`（ver17.0 追加） |

medium は全て**デプロイ実機確認待ち**で積み上がり続けている（3 件、うち 2 件は ver16.0 から継続）。次バージョンで一括解消が望ましい。

---

## 2. バージョン作成フローの振り返り

### 各ステップの評価

| ステップ | 評価 | コメント |
|---|---|---|
| split_plan | ◎ | ROUGH_PLAN で ver16.2（デプロイ検証）スキップ判断を「リスク承知」節で明示的に残し、会話分岐が既存検索系と独立した新規 API/テーブル追加であることで影響分離の方針を明文化。REFACTOR.md で `toLangGraphThreadId` / `makeThreadSettings` の事前リファクタを切り出し、機能追加コミットを純粋化 |
| imple_plan | ◎ | 計画との乖離は **Phase I.0（`experiments/fork-checkpoint.ts`）のスキップ 1 件のみ**。IMPLEMENT.md の「段階的アプローチのスキップ条項」に照らした 3 条件（安全性・対話性・仮説蓋然性）を MEMO で明示的に検証して判断。R1/R2 は ISSUES 化して先送り |
| wrap_up | ○ | MEMO の更新必要ドキュメント 3 項目に対し、PHASE3.md 実装済みマーク・CURRENT.md 新規作成を実施、CLAUDE.md はユーザー管理ファイルのためスキップし内容を ISSUES に統合 |
| write_current | ◎ | メジャーバージョンのため `CURRENT.md` を作成、**150 行超を見越して `CURRENT_backend.md` / `CURRENT_frontend.md` / `CURRENT_tests.md` に 3 分割**（write_current SKILL §CURRENT.md のファイル分割に準拠）。初の分割適用だが想定通り機能した |
| retrospective | — | 本ステップ |

### 良かった点

1. **事前リファクタ先出しが機能追加コミットを純粋化した**

   REFACTOR.md で `toLangGraphThreadId` ヘルパ骨組み作成と `makeThreadSettings` ヘルパ導入を機能追加前に切り出す方針を確定。実際には本バージョンは 1 コミットに束ねられたが、計画段階で「事前リファクタ → 機能追加」の段階分けを明確化したことで、IMPLEMENT.md §実装順序が素直になり、既存テスト更新と新規機能追加の衝突を避けられた。ver16.1 retrospective で提案した `makeThreadSettings` テストヘルパを本バージョンで実装 → `ThreadSettings.activeBranchId` 追加時の更新コストが 1 箇所（`DEFAULT_SETTINGS`）に集約された。**複数バージョンに渡る提案→実現のトラッキングが機能している**

2. **`CURRENT.md` 3 分割が初適用で成功**

   ver14.0 以降メジャーごとに CURRENT.md が段階的に肥大化していたが、ver17.0 で初めて 150 行基準の 3 分割（backend / frontend / tests）を適用。インデックスの CURRENT.md が 57 行で全体像を掴みやすく、詳細は各ファイル 50〜200 行のレンジに収まった。write_current SKILL の分割ルールが実運用で妥当であることを確認

3. **リスク分類「検証済み／検証不要／検証先送り」の定着**

   ver16.0 で imple_plan SKILL に明文化された「検証先送りリスクは ISSUES 化する」規定を 3 バージョン連続で適用。ver17.0 では R1/R2 を新規 `fork-checkpoint-verification.md` に統合、R6 は既存 ISSUES に包含と判断。ver16.1 と同様、スキル規定を機械的でなく文脈判断で運用できた

4. **IMPLEMENT.md「段階的アプローチのスキップ条項」が `experiments/` スキップ判断で機能した**

   Phase I.0（検証スクリプト）は AUTO モードの非対話性により実質効果が薄いと判断。スキップ条件 (a)(b)(c) を MEMO で明示的に点検し、仮説蓋然性（`messagesStateReducer` の設計・better-sqlite3 のパラメータバインディング挙動）を根拠として記録。検証先送り分は ISSUES に落とすワンセット運用が完成している

### 改善すべき点

1. **実機確認 8 バージョン連続先送り（ver14.3 以降継続）**

   ver14.3 以降、dev サーバー起動・ブラウザ動作確認なしで進行。ver17.0 ではさらにリスク R1（`updateState` 複数メッセージ初期化）・R2（`::` 含む `thread_id`）という**分岐機能の core path** が未検証領域に入った。medium ISSUES は 3 件に増加し、全てデプロイ実機確認で一括解消可能な性質。

   **影響**: 高（会話分岐の core path が未検証、ver16.1 のエコーモード永続化も未検証、検索結果の永続化も未検証 — 3 大機能の永続化層が全て未検証）
   **対応**: スキル変更は引き続き提案しない（非対話セッションでの制約）。ただし**次バージョン（17.1）でデプロイ検証を最優先に位置付ける**ことを強く推奨。PHASE3 の機能追加が完了した今、デプロイ検証を挟まないと PHASE4 起草時に信頼できる土台が得られない

2. **PHASE3 完了後の次フェーズ起草タイミング**

   PHASE3 全 4 項目が完了した現時点で、次バージョン（メジャー）の方向性を決める根拠が MASTER_PLAN 上にない。通常、MASTER_PLAN は次フェーズを先に起草しておくものだが、これまでのフローでは「PHASE N 完了 → retrospective で PHASE (N+1) を提案」の流れは明確化されていなかった。

   **影響**: 中（17.1 などマイナー作業は ISSUES 起点で継続可能、メジャー起草時にユーザーからの方向性提示待ちになる）
   **対応提案**: **スキル変更は不要**。MASTER_PLAN は本質的にユーザーの意思決定領域であり、retrospective 側で prompt する以上のことはできない。本 RETROSPECTIVE §1 で「PHASE4 起草はユーザー指示待ち」を明記することで対応済み

3. **`experiments/` スクリプトの AUTO モード親和性**

   ver17.0 で Phase I.0 をスキップした経緯から、AUTO モード下では `experiments/` スクリプトの実効性が限定的であることが明確になった。IMPLEMENT.md で検証スクリプトを計画しても実施されない傾向がある。

   **影響**: 低（スキップ条項で MEMO 記録すれば許容されるルールになっている）
   **対応提案**: **スキル変更は不要**。imple_plan SKILL は既に「スキップ条件 + ISSUES 化」を明記済み。ver17.0 の運用で妥当性が確認できており、ルール自体は維持して良い。ただし split_plan/imple_plan 段階で `experiments/` スクリプトを計画する際は、AUTO モードで実施不可である可能性を前提に「スキップ時の代替検証（静的解析・ユニットテスト）で R1/R2/R4 がどこまでカバーできるか」を事前に記述する運用にシフトするのが自然（ver17.0 の MEMO は結果的にそうなっている）

### 前回（ver16.1）改善提案の効果検証

| ver16.1 RETROSPECTIVE での改善提案 | ver17.0 での実績 |
|---|---|
| `ThreadSettings` 拡張コスト削減のテストヘルパ導入は次メジャーの REFACTOR で検討（提案のみ） | **◎**: ver17.0 REFACTOR.md §5 で本案を正式採用、`tests/fixtures/settings.ts` として実装。`activeBranchId` 追加時のテスト更新コストを 1 箇所に集約。**複数バージョン跨ぎの提案→実現のトラッキングが機能** |
| ver16.2（デプロイ検証）を先に挟むことを推奨 | **△ 実施されず**: AUTO モードの制約上実機デプロイ検証は実施不可、ROUGH_PLAN §選定外で明示的にスキップ判断を残して 17.0 着手。代わりに「既存検索系と独立した新規 API/テーブル追加」で影響分離。結果として未検証の積み上げは 3 つ目（会話分岐 core path）に増加 |
| 実機確認の継続（スキル変更しない方針） | **△ 継続先送り 8 回目**: 方針は維持。ver17.0 でリスクレベルはさらに上昇 |

---

## 3. 次バージョンの種別推奨

### 推奨: マイナーバージョン 17.1（デプロイ検証 + 軽量整理）

**理由**:

PHASE3 全項目完了により「機能追加の押し出し」の必然性が消えた。一方、medium ISSUES 3 件（全てデプロイ実機確認待ち）が積み上がり、会話分岐の core path まで未検証領域に入った。次メジャー（PHASE4）を起草する前に、土台の健全性を確認する絶好のタイミング。

### 推奨する 17.1 の内容（軽量マイナー）

- `ISSUES/app/medium/getState-timing.md` 手動確認 → close
- `ISSUES/app/medium/additional-kwargs-sqlite.md` 手動確認 → close
- `ISSUES/app/medium/fork-checkpoint-verification.md` 手動確認（R1: `updateState` 複数メッセージ初期化 / R2: `::` 含む thread_id ラウンドトリップ） → close
- ver16.1 エコーモード R1（`updateState → getState` 往復）の実機確認
- 必要に応じて `ISSUES/app/low/db-connection-refactor.md` の小規模対応（`db-config.ts` 一元化）

### 他の候補

| 候補 | バージョン | 優先度 | コメント |
|---|---|---|---|
| デプロイ検証 + ISSUES 一括 close | 17.1 | **推奨** | 8 バージョン積んだ実機未検証を 1 度解消、medium 3 件 close 見込み |
| PHASE4 起草 + 新機能 | 18.0 | 保留 | PHASE3 完了で新フェーズが必要だが、**ユーザーからの方向性提示待ち**（PHASE4 のネタは現時点で明確に用意されていない） |
| `shared/` 型統合 + `MAIN_BRANCH_ID` 重複解消 | 17.1 と同梱可 | 低 | `db-connection-refactor.md` に 3 点まとまっている。17.1 に含められる範囲で対応 |

**ユーザー判断が必要な分岐**: 17.1 を挟むのは非対話 AUTO モードでは半端（デプロイ実機確認はユーザー操作必須）。**AUTO モードでは 17.1 着手はユーザーのデプロイ検証完了を待ってから**が望ましい。それまでは PHASE4 方向性の指示待ち状態を明示的に保持する。

---

## 4. スキル改善（本ステップで即時適用）

### 改善提案なし

ver17.0 のフローは split_plan〜write_current まで既存スキルで円滑に流れた。特に以下は前回までの即時適用・継続運用が機能している:

- imple_plan SKILL の「検証先送り → ISSUES 化」規定（ver16.0 追加）→ ver17.0 R1/R2 で適用、既存 ISSUES との統合判断も機能
- imple_plan SKILL の「段階的アプローチのスキップ条項」→ Phase I.0 スキップで初適用、条件 (a)(b)(c) の点検運用が確立
- write_current SKILL の CURRENT.md 150 行分割ルール → ver17.0 で初適用、想定通り機能
- split_plan SKILL の REFACTOR.md 要否判定 → ver17.0 メジャーで REFACTOR.md 作成、機能追加コミットの純粋化に寄与

改善すべき点 1（実機確認 8 連続先送り）はスキルではなく **AUTO モードの制約そのもの**、改善すべき点 2（PHASE 完了後の次フェーズ起草）は**ユーザーの意思決定領域**、改善すべき点 3（`experiments/` の AUTO モード親和性）は**既存スキルで十分カバー**のため、いずれもスキル編集は行わない。

---

## 5. 対応済み ISSUES

| ISSUES | 状態 |
|---|---|
| （なし） | ver17.0 では既存 ISSUES の close なし。PHASE3 最終項目「会話分岐」を実装したが、これは MASTER_PLAN 直接対応で ISSUES は介在せず |
| `ISSUES/app/medium/getState-timing.md` | 未対応（デプロイ実機確認待ち、17.1 で close 見込み） |
| `ISSUES/app/medium/additional-kwargs-sqlite.md` | 未対応（同上） |
| `ISSUES/app/medium/fork-checkpoint-verification.md` | **ver17.0 追加**（R1 / R2 を統合） |
| `ISSUES/app/low/syntax-highlight.md` | 未対応（優先度 low） |
| `ISSUES/app/low/vitest-nuxt-test-utils.md` | 未対応（優先度 low） |
| `ISSUES/app/low/db-connection-refactor.md` | **ver17.0 追加**（`getDb()` / `MAIN_BRANCH_ID` / `ThreadSettings` の型重複 3 点を統合） |

本ステップでの追加削除はなし。
