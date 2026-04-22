# PHASE4.0: ワークフロー柔軟化（ステップごとのモデル/effort 指定とセッション継続）

## 概要

`scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` の各ステップで、Claude Code CLI に渡すモデル (`--model`)・推論エフォート (`--effort`)・前ステップからのセッション継続 (`-r` / `-c`) を指定可能にする。YAML top-level に `defaults:` セクションを設けて共通値を定義し、各ステップで必要に応じて上書きする。

## 動機

- 現状は全ステップが同じモデル・同じエフォートで実行されるため、タスクの重さに対して不釣り合いなコストが発生する
  - 例: `write_current` / `retrospective` はドキュメント整形が主体のため軽量モデルで十分
  - 例: `imple_plan` はリスク洗い出しを含むため高エフォートが望ましい
- 現状はステップごとに独立したセッションが立ち上がるため、前ステップの会話履歴が失われる
  - 例: `wrap_up` は `imple_plan` / 実装ステップの判断経緯を参照できればより的確な整理が可能
- フルワークフロー・軽量ワークフロー双方で同じ柔軟性が欲しい

## 前提条件

- PHASE3.0 が実装済み（`claude_loop_quick.yaml` が存在すること）
- Claude Code CLI が以下のフラグをサポートしていること（2026-04 時点で確認済み）
  - `--model <alias|fullname>`: セッションのモデル指定（例: `sonnet`, `opus`, `claude-sonnet-4-6`）
  - `--effort <low|medium|high|xhigh|max>`: 推論エフォート（モデルによって利用可能な値は異なる）
  - `-r <session-id-or-name>` / `--resume`: 指定セッションを再開
  - `-c` / `--continue`: 直近のセッションを継続

## やること

### 1. YAML スキーマ拡張

#### 1-1. top-level `defaults:` セクションの追加

全ステップ共通のデフォルト値を定義する。各ステップの設定はこの値を上書きする形。

```yaml
defaults:
  model: sonnet          # 省略時は CLI のデフォルト（= 未指定）
  effort: medium         # 省略時は CLI のデフォルト（= 未指定）
```

- `defaults:` 自体を省略した場合も、これまで通り動作する（後方互換）
- `defaults.model` / `defaults.effort` 個別の省略も可

#### 1-2. `steps[]` の項目拡張

```yaml
steps:
  - name: imple_plan
    prompt: /imple_plan
    model: opus          # defaults.model を上書き
    effort: high         # defaults.effort を上書き
    continue: false      # 新規セッションで開始（デフォルト）

  - name: wrap_up
    prompt: /wrap_up
    continue: true       # 直前ステップのセッションを引き継ぐ
```

- `model`: 省略時は `defaults.model`、それも省略なら CLI デフォルト
- `effort`: 省略時は `defaults.effort`、それも省略なら CLI デフォルト
- `continue`: boolean（デフォルト `false`）
  - `true` の場合、直前ステップのセッションを引き継いで実行する
  - **ループの初回ステップで `continue: true` が指定された場合**: 前ループの最終ステップが存在すればそれを継続、存在しなければ警告を出力して新規セッションで実行（エラーにはしない）

#### 1-3. セッション継続の実現方式

実装方式は **セッションID 明示指定方式** を採用する（`-c` の「直近セッション」方式は、並行実行やユーザーの手動 claude 実行で壊れるため）。

1. `claude -p` 実行時に `--output-format stream-json` 等でセッションIDを取得する
   - または `--session-id <uuid>` フラグで ID を事前指定する（CLI が対応している場合）
2. 次ステップで `continue: true` なら `-r <前ステップのsession-id>` を付与する
3. セッションIDは `claude_loop.py` のメモリ内変数として保持する（ディスクには書かない）

**実装上の検証タスク**:
- `--session-id` フラグの有無を確認し、対応していれば事前指定方式を優先する（決定論的で扱いが楽）
- 未対応なら `--output-format stream-json` の先頭行 `system` イベントから `session_id` を抽出する実装にする
- どちらも機能しない場合は `-c` 方式にフォールバックする（動作を YAML コメントに明記）

### 2. `scripts/claude_loop.py` の改修

#### 2-1. `resolve_command_config` / `get_steps` の拡張

- `defaults` セクションをロードする関数 `resolve_defaults(config)` を追加
- `get_steps` で各ステップの `model` / `effort` / `continue` を読み取り、dict に格納
- ステップレベルの値がなければ `defaults` の値を採用

#### 2-2. `build_command` の拡張

```python
def build_command(..., step, defaults, previous_session_id):
    cmd = [executable, prompt_flag, step["prompt"], *common_args, *step["args"]]
    model = step.get("model") or defaults.get("model")
    effort = step.get("effort") or defaults.get("effort")
    if model:
        cmd.extend(["--model", model])
    if effort:
        cmd.extend(["--effort", effort])
    if step.get("continue") and previous_session_id:
        cmd.extend(["-r", previous_session_id])
    ...
```

#### 2-3. セッションID の取得と受け渡し

- `_run_steps` ループ内で `previous_session_id: str | None = None` を保持
- 各ステップ実行時に stdout をパースしてセッションIDを抽出する `extract_session_id(line)` を追加
  - `--output-format stream-json` の `system` イベントから抽出
  - あるいは `--session-id <uuid>` を毎回事前生成する方式なら `uuid.uuid4()` で事前発行
- ステップ完了後、次ステップが `continue: true` なら取得した ID を `-r` で渡す

#### 2-4. ログ出力の拡張

ステップヘッダにモデル・エフォート・継続状態を出力する:

```
[2/5] imple_plan
Started: 2026-04-22 10:15:00
Model: opus, Effort: high, Continue: false
Session: abc12345
$ claude -p /imple_plan --model opus --effort high ...
```

### 3. 既存 YAML への適用

#### 3-1. `scripts/claude_loop.yaml`（full）

推奨値の提案（実装時に plan_review_agent で確定）:

| ステップ | model | effort | continue |
|---|---|---|---|
| split_plan | opus | high | false |
| imple_plan | opus | high | true（split_plan の判断を引き継ぐ） |
| wrap_up | sonnet | medium | true（実装経緯を引き継ぐ） |
| write_current | sonnet | low | false（現況を新規視点で整理） |
| retrospective | sonnet | medium | false |

#### 3-2. `scripts/claude_loop_quick.yaml`（quick）

| ステップ | model | effort | continue |
|---|---|---|---|
| quick_plan | sonnet | medium | false |
| quick_impl | sonnet | high | true（計画を引き継ぐ） |
| quick_doc | sonnet | low | true（実装経緯を引き継ぐ） |

### 4. ドキュメント整備

- `scripts/` 配下に `README.md` を新規作成（ISSUES/util/medium/スクリプト改善.md の要件を一部兼ねる）
  - 起動方法・主要オプション・YAML フォーマットの説明
  - `defaults` / `model` / `effort` / `continue` の意味と例
  - デフォルト値変更時の影響範囲（コスト・所要時間）
- `.claude/SKILLS/meta_judge/WORKFLOW.md` に「ステップごとのモデル/エフォート指定が可能」であることを追記

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | `defaults` ロード・ステップ設定拡張・セッションID 継承・ログ出力拡張 |
| `scripts/claude_loop.yaml` | 変更 | `defaults` 追加・各ステップに `model`/`effort`/`continue` を設定 |
| `scripts/claude_loop_quick.yaml` | 変更 | 同上（quick 版） |
| `scripts/README.md` | 新規作成 | YAML フォーマット・CLI オプション説明 |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | 変更 | モデル/エフォート指定機能の追記 |
| `docs/util/ver4.0/` | 新規作成 | ROUGH_PLAN / IMPLEMENT / CURRENT / MEMO |

## リスク・不確実性

- **`--session-id` フラグの存在**: CLI リファレンスに明記されていない可能性があり、実装時に要検証
- **`--output-format stream-json` と `-p` の併用**: stdout パースが複雑化する。ログ出力（TeeWriter）との両立が必要
- **セッション継続時のモデル切替**: `-r` でセッションを再開した際に `--model` が有効かは未確認。モデル切替とセッション継続が両立しない場合は、`continue: true` のステップは前ステップと同じモデルを強制する仕様に制限する必要あり

## やらないこと

- `thinking` パラメータの指定（CLI 未対応、かつ `--effort` で代替可能）
- ステップ単位の `--append-system-prompt` カスタマイズ（現状の共通 `auto_args` で十分）
- コスト見積もり機能（モデル別のトークン単価計算などは対象外）
- セッションIDの永続化（ワークフロー再開時の session 復元は対象外。`--start` で途中ステップから開始する場合は `continue` 指定を無効化する）
