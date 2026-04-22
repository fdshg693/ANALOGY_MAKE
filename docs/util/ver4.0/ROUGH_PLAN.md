# ver4.0 ROUGH_PLAN

## 位置づけ

- カテゴリ: util
- バージョン種別: **メジャー（4.0）**
- 対応内容: `docs/util/MASTER_PLAN/PHASE4.0.md`（ワークフロー柔軟化）の **一部スコープ** を切り出して実装
- 判断根拠:
  - `ISSUES/util/high/` に課題なし → MASTER_PLAN の次項目（PHASE4.0）を進める
  - YAML スキーマ拡張 + `claude_loop.py` の引数ビルド機構を拡張するアーキテクチャ変更のため、メジャー扱い

## スコープ切り出しの考え方

PHASE4.0 には以下 3 系統の機能が含まれる:

1. ステップごとの **`--model` 指定**
2. ステップごとの **`--effort` 指定**
3. ステップ間の **セッション継続（`-r` / `--session-id`）**

このうち **ver4.0 では 1 と 2 のみを対象** とする。理由:

- セッション継続は CLI フラグ（`--session-id` / `stream-json` 経由の抽出）の対応状況が未検証で、リスク・不確実性が大きい（PHASE4.0 のリスク欄にも明記）
- モデル/effort 指定だけでも、「重いステップに `opus`・軽いステップに `sonnet`」等のコスト・品質最適化という主要メリットの大半が得られる
- セッション継続は後続バージョン（ver4.1 予定）で CLI 検証と合わせて独立して追加できる

したがって **ver4.0 のテーマは「ステップごとのモデル/effort 指定によるコスト・品質バランス最適化」**。

## 今回のバージョンで提供するユーザー体験

### Before（ver3.x）

- `claude_loop.yaml` / `claude_loop_quick.yaml` の全ステップが Claude CLI デフォルトの同一モデル・同一エフォートで実行される
- 軽量な整形ステップ（`write_current` / `retrospective` / `quick_doc`）も、重い計画ステップ（`imple_plan` / `quick_plan`）も同条件のため、コスト効率が悪い、または逆に軽量モデルで計画ステップが情報不足になる
- 個別に変えるには YAML 内で強引に `args` を書き換えるしかなく、ワークフロー全体の見通しが悪い

### After（ver4.0）

- YAML に top-level `defaults:` セクションが追加され、全ステップ共通のモデル/effort を 1 箇所で指定できる
- 各 `steps[]` 項目でも個別に `model` / `effort` を上書きできる
- `defaults` も step 単位も省略可で、省略時は CLI デフォルト（現状の挙動）にフォールバック → **完全後方互換**
- `claude_loop.yaml`（フル）と `claude_loop_quick.yaml`（quick）それぞれに、ステップの性質に応じた推奨値が設定された状態で出荷される
- ワークフロー実行ログに「Model: {値}, Effort: {値}」が出力され、どのステップがどの設定で動いたかが追跡可能になる

### 影響範囲

- `scripts/` 配下（Python スクリプト + YAML）の変更と、`meta_judge/WORKFLOW.md` のドキュメント反映
- SKILL ファイル自体の挙動は変わらない（モデル/effort は CLI 引数経由で外側から注入されるため）
- `scripts/` の README はまだ存在しないが、`ISSUES/util/medium/スクリプト改善.md`（README 追加・ファイル分割）は **ver4.0 の対象外**（独立したリファクタリング性質のため別バージョンで扱う）

## 想定される変更規模

- 主対象: `scripts/claude_loop.py`、`scripts/claude_loop.yaml`、`scripts/claude_loop_quick.yaml`、`tests/test_claude_loop.py`、`.claude/SKILLS/meta_judge/WORKFLOW.md`
- 小規模タスクの判定基準（変更 3 ファイル以下 / 100 行以下）を超えるため、**通常タスクとしてフルワークフローで進める**
- 事前リファクタリング不要（既存の `build_command` / `get_steps` / `resolve_command_config` はステップ設定の受け取り方を拡張するだけで対応可能）
  → `REFACTOR.md` は作成しない

## 非対象（ver4.1 以降に先送り）

- `continue: true` / `-r` / `--session-id` によるセッション継続機能
- `--output-format stream-json` パーサの導入
- `scripts/README.md` の新規作成（`ISSUES/util/medium/スクリプト改善.md` に紐づく）
- `.claude/SKILLS/meta_judge/WORKFLOW.md` のワークフロー選択ガイドライン改訂（モデル設定の使い分け方針の明文化）は、実運用で挙動を確認してから別バージョンで扱う
- ステップ側で `defaults` を明示的にリセット（無効化）する機能（例: `defaults.model: sonnet` が設定されているが特定ステップだけ CLI デフォルトに戻したい、というニーズ）。ver4.0 ではステップの `model` / `effort` は「キー自体が存在するかどうか」のみで上書き判定し、`null` / 空文字列などによる無効化はサポートしない

## 成功条件

- `claude_loop.yaml` / `claude_loop_quick.yaml` が `defaults` / `model` / `effort` を含んだ状態になっていて、`python scripts/claude_loop.py --dry-run` で各ステップに期待通り `--model` / `--effort` が付与されたコマンドが出力される
- `defaults` / `model` / `effort` を完全に取り除いた YAML でも従来通り動作する（後方互換確認）
- `tests/test_claude_loop.py` のユニットテストがグリーン（`defaults` 解決・ステップレベル上書き・未指定時の CLI 引数省略のテストを追加）
