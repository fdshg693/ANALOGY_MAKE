# ver11.1 CHANGES — `scripts/README.md` 分割・ログ読解観点追記

前バージョン ver11.0 からの変更差分。

## 変更ファイル一覧

| 変更種別 | ファイル | 概要 |
|---|---|---|
| 更新 | `scripts/README.md` | 353行 → 149行に縮小。ファイル一覧を論理グループ分け。詳細仕様を USAGE.md へ移管 |
| 新規 | `scripts/USAGE.md` | CLI オプション一覧・YAML 仕様詳細・ログトラブルシュート・拡張ガイドを収録した詳細リファレンス（243行） |

## 変更内容の詳細

### S1. `scripts/` 配下のワークフロー関連コード分離（論理分離）

物理的なファイル移動は行わず、`scripts/README.md` のファイル一覧を 3 グループに再編して境界を明示した:

- **ワークフロー実行（`claude_loop` 系）**: `claude_loop.py` / `claude_loop_lib/` / `claude_loop*.yaml`
- **ISSUES 管理ツール**: `issue_status.py` / `issue_worklist.py`
- **補助ツール**: `claude_sync.py`

物理移動を採用しなかった理由: `.claude/rules/claude_edit.md` が `scripts/claude_sync.py` を、CLAUDE.md / CURRENT_scripts.md 等が各スクリプトのパスをハードコードしており、移動するとパス参照の更新コストが高い。振る舞い不変の優先度を重視し論理分離で対応した。

### S2. `scripts/README.md` の分割（`scripts/USAGE.md` 新設）

`scripts/README.md`（353行）を以下の方針で分割した:

**`scripts/README.md`（149行 → 目標200行以下クリア）**:
- 概要把握（これは何か / 前提条件）
- ファイル一覧（3グループ）
- クイックスタート（コマンド例）
- フル/quick の使い分け
- ログの見方（要点のみ）
- フィードバック注入機能（要点のみ）
- `claude_sync.py` の使い方
- テスト実行コマンド
- 関連ドキュメント（USAGE.md リンク追加）

**`scripts/USAGE.md`（243行、新規）**:
- `issue_worklist.py` 使い方詳細
- CLI オプション一覧（全オプション一覧テーブル）
- YAML ワークフロー仕様（セクション定義 / override キー / 継承ルール / `append_system_prompt` 合成順序 / `continue` 使い分けとエッジケース / `--workflow auto` 分岐仕様 / サンプル YAML）
- フィードバック注入機能（詳細：`step` フィールドの書き方 / 消費後の挙動）
- ログフォーマット（詳細）+ ログ読解のトラブルシュート観点（S3）
- 拡張ガイド

### S3. ログ読解の勘所追記

`scripts/USAGE.md` の「### ログの読み方（トラブルシュート）」節に以下の観点を追記:

- **失敗ステップの特定**: `--- end (exit: {code}, ...)` 行で非ゼロの箇所を探す手順
- **セッション汚染の切り分け**: `continue: true` ステップでのエラー連鎖と `--start N` による単独再実行
- **手動再開**: ワークフローフッターの `Last session (full):` UUID を使った `claude -r <uuid>` および `--start N` の使い方
- **ログファイルの管理**: `.gitignore` 済みのため手動削除可、ローテーション未実装の明記

## 技術的判断

### 物理移動 vs 論理分離

ROUGH_PLAN で「決め手に欠ける場合は移動しない」を明示していたとおり、論理分離を採用した。今後 `scripts/` が更に肥大化する場合（例: `claude_loop_lib/` 外への新規モジュール追加が 3 件超える等）はサブディレクトリ化を再検討する。
