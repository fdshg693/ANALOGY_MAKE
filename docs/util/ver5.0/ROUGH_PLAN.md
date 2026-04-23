# ver5.0 ROUGH_PLAN: ワークフローのステップ間セッション継続

## バージョン種別

**メジャー (5.0)**

理由:
- `claude_loop.py` に「ステップ間でセッション状態を引き継ぐ」という新しいアーキテクチャ概念（inter-step session state）を導入する
- ver4.1 の RETROSPECTIVE で次バージョンの推奨として明示されていた
- PHASE4.0 の残項目（セッション継続）を閉じることで MASTER_PLAN の「部分実装」ステータスを解消する

## 対応方針

`docs/util/MASTER_PLAN.md` の PHASE4.0 残項目 **「セッション継続」** に対応する。ISSUES/util の `high` / `medium` / `low` はいずれも空（`.gitkeep` のみ）のため、MASTER_PLAN に沿った機能追加を優先する。

## スコープ

YAML ワークフロー定義の各ステップで、直前ステップのセッションを継続するかどうかを宣言できるようにする。継続が有効なステップでは、前ステップの会話履歴（ツール使用結果・判断の経緯）を引き継いだ状態で Claude Code CLI が起動する。

### ユーザー体験の変化

**Before (ver4.x)**:
- 各ステップは完全に独立したセッションで実行される。`wrap_up` ステップは `imple_plan` で行った判断・トレードオフの検討経緯を参照できないため、MEMO.md / ROUGH_PLAN.md に書かれた「結果」のみを起点に動く。
- 結果として、後続ステップは毎回ドキュメントを読み直し、文脈を再構築する必要がある。

**After (ver5.0)**:
- YAML で `continue: true` を指定したステップは、直前ステップの会話を引き継いで起動する。`wrap_up` / `retrospective` など「前のステップの判断を踏まえて整理する」種類のタスクで、ドキュメントに書き漏らされた暗黙の判断経緯も参照できる。
- `continue: false`（デフォルト）のステップは従来通り新規セッションで開始する。`write_current`（現況を新規視点で整理）などには適切。

### 提供する機能

1. YAML ステップ項目に `continue: bool` を追加（省略時 `false`）
2. `claude_loop.py` が `continue: true` のステップに対し、直前ステップの session ID を `-r` で渡す
3. ステップヘッダのログに `Continue: true/false` と `Session: <uuid>` を表示
4. `claude_loop.yaml`（full）の `imple_plan` / `wrap_up` に `continue: true` を設定（PHASE4.0 推奨テーブル L127-133 に準拠）。`split_plan` / `write_current` / `retrospective` は `continue: false`。`claude_loop_quick.yaml`（quick）は `quick_impl` / `quick_doc` を `continue: true` に設定（同 L137-141）。
5. ワークフロー完了時・中断時の session ID をログ末尾に記録（トラブルシュート時に `claude -r <id>` で手動再開できるように）

### セッション ID の取得方式

PHASE4.0 L64-75 で挙げられている 3 候補（(a) `--session-id <uuid>` による事前発行、(b) `--output-format stream-json` の `system` イベントからの抽出、(c) `-c` による「直近セッション」フォールバック）のうち、**どれを採用するかは IMPLEMENT.md で確定する**（CLI の対応状況・TeeWriter との両立可否を検証した上で決定）。PHASE4.0 のリスク項目（`--session-id` の存在、stream-json と `-p` の併用）は IMPLEMENT.md の「リスク・不確実性」セクションで改めて洗い出す。

### エッジケースの扱い

- **`--start` で途中ステップから開始**: 当該実行の**全ステップ**で `continue` 指定を無効化し、すべて新規セッションで実行する（起点ステップの `continue` だけを無効化するのではなく、以降のステップも含めて無効化する）。理由: 起点ステップの前段セッションが存在しないため、2 番目以降の `continue: true` も「起点から引き継いだ文脈」を再現できないため。無効化時は警告ログのみ出力し、エラーにはしない。
- **`--max-loops` / `--max-step-runs` 複数ループ**: ループ**内**のステップ継続は通常どおり動作する（前ステップの session ID を `-r` で渡す）。**ループの初回ステップで `continue: true` が指定された場合**（PHASE4.0 L61 の仕様そのまま）: 前ループの最終ステップが存在すればその session ID を継続、存在しなければ警告を出力して新規セッションで実行（エラーにはしない）。
- **`--dry-run`**: 実行しないため session ID を発行せず、コマンドラインには `-r DRY_RUN_PLACEHOLDER` 相当の識別子（実装詳細は IMPLEMENT で確定）を表示
- **`continue: true` のステップでモデル/effort 切替**: 現状 Claude CLI が resume 時のモデル切替を正式サポートするかは未検証。互換性が崩れる場合は IMPLEMENT で挙動確認の上、制限または警告を入れる

### ドキュメント更新

- `scripts/README.md` に `continue` オプションのセクションを追加
- `.claude/SKILLS/meta_judge/WORKFLOW.md` への `continue` 指定ガイドは ver5.0 スコープ**外**（実運用で挙動確認後、別バージョンで対応。ver4.1 retrospective の持ち越し事項に同方針を既に記録済み）
- CLAUDE.md の更新: `write_current` で該当する場合のみ（新規フォルダ追加はなく、既存ファイルの機能強化のため原則不要）

## スコープ外

- `.claude/SKILLS/meta_judge/WORKFLOW.md` のモデル/effort 使い分け方針の明文化（ver4.1 retrospective の持ち越し事項）
- `write_current/SKILL.md` の CLAUDE.md チェック強化（同持ち越し事項、ユーザー確認後に別タスクとして適用）
- ISSUE ステータス管理（PHASE5.0 の範囲）
- セッションID のディスク永続化・ワークフロー途中再開（PHASE4.0「やらないこと」で明示）

## 影響範囲の見積もり

変更対象ファイル:

| ファイル | 変更種別 |
|---|---|
| `scripts/claude_loop.py` | 変更（`_run_steps` にセッション状態保持を追加） |
| `scripts/claude_loop_lib/workflow.py` | 変更（`get_steps` で `continue` キーを取り込む） |
| `scripts/claude_loop_lib/commands.py` | 変更（`build_command` に session ID 引数・`--session-id` / `-r` 付与ロジックを追加） |
| `scripts/claude_loop_lib/logging_utils.py` | 変更（ステップヘッダの拡張、もしくは呼び出し側に引数追加） |
| `scripts/claude_loop.yaml` | 変更（`imple_plan` / `wrap_up` に `continue: true`。`split_plan` / `write_current` / `retrospective` は既定の `false`） |
| `scripts/claude_loop_quick.yaml` | 変更（`quick_impl` / `quick_doc` に `continue: true`） |
| `scripts/README.md` | 変更（セクション追加） |
| `tests/test_claude_loop.py` | 変更（`build_command` / `get_steps` / `_run_steps` のテスト拡張） |

新規ファイル作成は見込みなし。変更対象は 8 ファイル / 追加行数は 150〜250 行程度の見込みで、小規模タスクの閾値（3 ファイル / 100 行）を超えるため **通常タスク**として扱う（REFACTOR.md 作成の要否は次ステップで判断）。

## 事前リファクタリング

事前リファクタリング不要の見込み。ver4.1 で `claude_loop_lib/` にモジュール分割済みで、セッション状態は `commands.py` と `_run_steps`（`claude_loop.py`）に局所化して追加可能。必要があれば IMPLEMENT.md で改めて検討する。
