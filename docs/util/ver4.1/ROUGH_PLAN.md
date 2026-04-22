# ver4.1 ROUGH_PLAN

## 対応内容

`ISSUES/util/medium/スクリプト改善.md` の対応。

**判断基準**: `ISSUES/util/high/` は空。前バージョン（ver4.0）の `RETROSPECTIVE.md` が「次は ver4.1 マイナーで本 ISSUE を先に消化する」を第一推奨としており、その方針に従う。PHASE4.0 残タスク（セッション継続）や PHASE5.0（ISSUE ステータス管理）は ver5.0 以降に回す。

## バージョン種別

**マイナーバージョン (4.1)**。

理由:
- 新機能追加はなし（CLI インターフェース・YAML スキーマ・ワークフロー挙動は不変）
- 既存の `scripts/claude_loop.py`（698 行）の内部構造整理と人間向けドキュメントの追加
- 破壊的変更なし（ただしテスト内のモックターゲットは内部構造の変化に合わせて更新する必要あり）

## スコープ

以下の 2 点を今回のバージョンでカバーする。

### 1. `scripts/README.md` の新規作成

現状 `scripts/` 配下には Python スクリプトと YAML だけが置かれ、以下の情報が散在している:

- CLI オプションの意味・使い方 → `docs/util/ver4.0/CURRENT_scripts.md` とコード
- YAML ワークフローの書き方 → `docs/util/ver4.0/CURRENT_scripts.md` とサンプル YAML
- フル/クイックワークフローの使い分け → `docs/util/ver4.0/CURRENT.md` のワークフロー選択ガイドライン
- ステップごとの `model` / `effort` 指定 → ver4.0 CURRENT_scripts.md
- フィードバック注入の仕組み → CURRENT.md
- `claude_sync.py` の役割 → CURRENT_scripts.md

これらを `scripts/README.md` として集約し、**人間（＝本プロジェクトの開発者）が `scripts/` を開いたときに自己完結した使用方法・拡張方法がわかる状態**にする。`docs/util/` のドキュメントは内部状態の完全版として残し、README はユーザー視点での入口に徹する。

### 2. `scripts/claude_loop.py` の分割

現在 698 行の単一ファイルに以下の責務が混在している:

- CLI 引数パース
- YAML ロード・バリデーション
- ステップ抽出 / defaults 解決 / command 設定 / mode 判定
- フィードバック（frontmatter 解析・ロード・消費）
- コマンド構築（`build_command`）
- ステップイテレータ
- ログ（`TeeWriter`・ログパス生成・ヘッダ・duration フォーマット）
- Git ヘルパ（HEAD commit・未コミット検出・自動コミット）
- 通知（toast / beep）
- エントリポイント（`main` / `_run_steps`）

将来拡張（PHASE4.0 残のセッション継続、PHASE5.0 の ISSUE ステータス管理 SKILL が触る箇所）を見据え、責務単位でモジュール分割を行う。**機能は一切変更せず**、関数のインポート元だけが変わる純粋なリファクタリングとする。

### 3. 既存テスト（89 件）のアップデート

`tests/test_claude_loop.py` は `from claude_loop import X` で関数を取り込み、`@patch("claude_loop.Y")` で内部依存（`datetime` / `subprocess.run` / `_notify_toast` 等）をモックしている。モジュール分割後はパッチ対象のパスが変わるため、テスト側のインポートとパッチターゲットを新モジュール構成に追従させる。**テストの意図・カバレッジは維持**する（89 件を減らさない・新規の追加も今回は最小限）。

## 非対象スコープ（明示的に扱わない）

- PHASE4.0 残タスク（`continue: true` / `-r` / `--session-id` / `--output-format stream-json`）→ ver5.0 以降
- PHASE5.0（ISSUE ステータス管理 frontmatter）→ ver5.0 以降
- `defaults` の明示リセット機能（`model: null` による無効化）→ 需要発生時に別バージョンで扱う
- `claude_sync.py` の分割・整理 → 58 行と小さく、現状で支障がないため据え置き
- YAML スキーマの拡張 → 今回は README 化のみで仕様変更は行わない
- `.claude/SKILLS/meta_judge/WORKFLOW.md` のモデル/effort ガイドライン改訂 → 実運用で挙動が固まってから別バージョンで扱う

## 規模見積もり

| 項目 | 見積 |
|---|---|
| 変更対象ファイル | `scripts/claude_loop.py`（分割元）、`scripts/README.md`（新規）、`tests/test_claude_loop.py`、新規モジュールファイル数個、`scripts/claude_loop.yaml` / `_quick.yaml` のコメント補助（必要に応じ） |
| 新規ファイル作成 | 必要（README + 分割後の各モジュールファイル） |
| 追加行数 | README 単体で 150〜250 行程度、テスト更新は主にパッチターゲット書き換えで行数は小変動 |

小規模タスクの条件（変更ファイル 3 つ以下・追加 100 行以下・新規ファイル不要）の **すべてに該当しない** ため、フルワークフロー（現在実行中）で進行する。REFACTOR.md の要否は「このタスク自体がリファクタリング本体」であるため事前リファクタリングは不要。REFACTOR.md は作成せず、IMPLEMENT.md に分割計画を含める。

## 事前リファクタリング

**不要**。本タスク自体が `claude_loop.py` の責務整理・分割というリファクタリングを主眼とするため、さらなる事前リファクタを重ねる意味はない。分割方針の詳細は IMPLEMENT.md で定める。

## 成功条件

- `scripts/README.md` が新規作成され、CLI オプション・YAML ワークフロー仕様・フル/クイックの使い分け・ステップ別 model/effort・フィードバック機構・`claude_sync.py` の役割 が網羅されている
- `scripts/claude_loop.py` の責務が複数モジュールに分割され、単一ファイルの肥大化が解消されている
- `python -m unittest tests.test_claude_loop` が 89 件すべてグリーン
- `python scripts/claude_loop.py --dry-run --no-log` および `-w scripts/claude_loop_quick.yaml --dry-run --no-log` がリファクタ前と同じコマンド出力を生成する（機能不変の確認）
- PHASE4.0 残タスク / PHASE5.0 を次バージョンで扱いやすい形になっている（モジュール境界が責務で切れており、変更箇所が局所化される）

## ユーザー視点の変化

- `scripts/` ディレクトリを開いたときに `README.md` があり、CLI と YAML の使い方がそこで完結する
- 既存の `python scripts/claude_loop.py ...` 実行方法は**変わらない**（CLI インターフェース保持）
- YAML ワークフローの書き方も**変わらない**（フォーマット保持）
