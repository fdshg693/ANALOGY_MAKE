# ROUGH_PLAN: Hooks 設定の修正

## バージョン

ver1.0（util カテゴリ初バージョン）

## 対応する課題

`ISSUES/util/high/HOOKS設定.md`

## 背景

現在の `.claude/settings.local.json` の `PermissionRequest` フックは、空の matcher で全ての PermissionRequest を無条件に自動許可している。これにより以下の 3 つの問題が発生している。

## 解決すべき問題

### 1. 手動モードで AskUserQuestion が自動許可される

手動で Claude Code を実行した際、AI がユーザーに質問するために AskUserQuestion ツールを使用すると、フックが自動的に許可してしまい、ユーザーが質問に回答する機会が得られない。

**期待する動作**: AskUserQuestion はフックで自動許可せず、通常のパーミッションダイアログを表示する。それ以外のツール（Edit, Write, Bash 等）は引き続き自動許可される。

### 2. スクリプト自動化モードで `.claude` 配下のファイル書き込みが失敗する

`claude_loop.py` を使ったスクリプト自動化モード（`-p` フラグ使用）では、`.claude` 配下のファイル（SKILL ファイルなど）の編集が失敗する。手動モードでは成功する。

Hooks のドキュメントによると、**`PermissionRequest` フックは非対話モード（`-p`）では発火しない**。これが原因の可能性が高い。

**期待する動作**: 自動化モードでも `.claude` 配下のファイル編集が正常に行える。

**解決手段の仮説**: `PermissionRequest` フックが非対話モードで発火しないことが原因であれば、`PreToolUse` フックの利用や `permissions.allow` への明示的なエントリ追加で回避できる可能性がある。IMPLEMENT.md 作成時に原因を特定し、適切な解決策を選定する。

### 3. フックコマンドの外部スクリプト化

現在のフック設定はインラインの echo コマンドで記述されている。今後フックが複雑化する可能性を考慮し、別ファイルのスクリプトとして管理したい。

**期待する動作**: フックの判断ロジックは外部スクリプトファイルに分離され、`settings.local.json` にはスクリプトの呼び出しのみが記述される。

## スコープ

- `.claude/settings.local.json` のフック設定の修正
- フック用スクリプトファイルの新規作成（`.claude/hooks/` 配下）
- 既存の `scripts/claude_loop.py` や `scripts/claude_loop.yaml` は変更しない（PHASE2.0 のスコープ）

## 事前リファクタリング不要

現在のフック設定はインラインコマンド 1 行のみであり、リファクタリングの対象となる既存コードはない。
