# ver5.0 MEMO: ステップ間セッション継続

## 計画との乖離

### `previous_session_id` の更新位置

IMPLEMENT.md L173-180 では「成功確定後（`completed_count += 1` と同じ位置）に状態更新」と明記していたが、実装では **`if dry_run: continue` の直前** にも更新を追加した（成功確定後の更新はそのまま残す形ではなく、dry-run 経路にも追加）。

**理由**: dry-run 時に `previous_session_id = session_id` の更新がスキップされ、`continue: true` ステップが「前セッションが存在しない」警告を毎ステップ出力してしまい、コマンド事前確認という dry-run 本来の目的（実本番と等価なコマンド列を見たい）と乖離する。失敗時は `_run_steps` が即 `return` するので、失敗ハンドリング前に更新しても害がない（IMPLEMENT.md R5 で整理済み）。実コードでは:

```python
if dry_run:
    previous_session_id = session_id
    continue
# ...（実行・失敗ハンドリング）...
previous_session_id = session_id
completed_count += 1
```

両方の経路で更新する形にした。dry-run 経路と本番経路で `previous_session_id` の更新タイミングが異なるが、実害はない。

## リスク・不確実性の検証結果

### R1. `--session-id <uuid>` の動作仕様 → **検証済み**

- **CLI が `--session-id` をサポートする**: `claude --help` で確認済み（IMPLEMENT.md 時点と同じ）
- **同一 UUID を 2 回使った場合**: **エラー** `Error: Session ID <uuid> is already in use.`
- **本実装の流れでは衝突しない**: `continue: true` 以外の各ステップで `uuid.uuid4()` を毎回生成するため。`continue: true` のステップは `-r` 経由なので `--session-id` の重複指定にはならない
- **`--session-id` と `-r` の同時指定**: 検証していない（本実装では片方しか出力しないため呼ばない）

### R2. `-r` 時のモデル切替 → **検証済み**

- 既存セッションを `-r <uuid> --model sonnet` で再開し「What model are you?」と質問 → 正常応答（`Claude Sonnet 4.6`）が返却された
- 元のセッションは `--model haiku` で作成していたため、**resume 時に `--model` を指定するとモデルが切り替わる挙動が確認**された（エラーにも警告にもならず、新指定値が反映される）
- 本実装では現状 YAML がモデル切替を発生させない設計（`split_plan` / `imple_plan` どちらも opus）だが、将来的に `wrap_up`（sonnet）が `imple_plan`（opus）を継続するケースで切替が発生する。**問題なく動作することを確認**した。`scripts/README.md` への追記は不要と判断（ユーザーが意図して切り替えるケースが想定通り動くため）

### R3. Session ID の stdout 出力形式 → **検証済み**

- 2 ステップ連続実行で動作確認: ステップ 1 で `--session-id <uuid>` 指定 + 「Say PING only.」 → ステップ 2 で `-r <uuid>` + 「Repeat the word you said before.」 → **「PING」が返却**された
- Python 側で発行した UUID で `-r` 接続が成功し、前ステップのコンテキストが保持されていることを確認

### R4. TeeWriter との両立 → **検証不要**

UUID は Python 側で生成する文字列であり、subprocess 出力に依存しない。検証不要のまま。

### R5. `continue: true` で前ステップが失敗した場合 → **整理済み**

IMPLEMENT.md L361 の通り、前ステップが exit_code ≠ 0 なら `_run_steps` が即 `return` するため、`continue: true` の後続ステップは実行されない。検証不要。

## 動作確認サマリ

- `python -m unittest tests.test_claude_loop`: **103件 グリーン**（既存 89 件 + 新規 14 件）
- `pnpm test`: **145件 グリーン**（影響なし）
- `npx nuxi typecheck`: 既知の vue-router/volar 警告のみ（CLAUDE.md 記載通り、ビルド・実行に影響なし）
- `python scripts/claude_loop.py -w scripts/claude_loop.yaml --dry-run --no-log`:
  - 全 5 ステップで `--session-id` または `-r` 付きコマンドを生成
  - `imple_plan` / `wrap_up` が前ステップと同じ session ID で `-r` を出力
  - `write_current` / `retrospective` は新規 UUID で `--session-id` を出力
- `python scripts/claude_loop.py -w scripts/claude_loop.yaml --start 3 --dry-run --no-log`:
  - `WARNING: --start > 1 detected; disabling 'continue: true' for all steps in this run.` を 1 度だけ出力
  - `wrap_up` を含む全ステップが `--session-id`（`-r` ではなく）でコマンド生成
- 実機 (`claude -p --session-id <uuid>` → `claude -p -r <uuid>`) で前セッションの会話継続を確認

## 残課題・次バージョンへの提案

### 既存テストへの影響なし

`build_command` の新引数はデフォルト `None` / `False` のため、既存 89 テストはそのままグリーン。`tests/test_claude_loop.py` に追加した 14 テストはすべて新機能に対するもの。

### `MASTER_PLAN.md` PHASE4.0 ステータス更新（次ステップ `write_current` で対応）

`docs/util/MASTER_PLAN.md` の PHASE4.0「セッション継続」を「部分実装」→「実装済み」に更新する作業は `write_current` ステップで実施する。

### ドキュメント更新の必要性

- `scripts/README.md`: ver5.0 で `continue` セクションを追加済み
- `docs/util/ver5.0/CURRENT.md`: `write_current` ステップで作成
- `.claude/SKILLS/meta_judge/WORKFLOW.md` への `continue` 指定ガイド: ver5.0 スコープ外（ROUGH_PLAN.md L52 の方針通り）

### 古いテキストの提案

- `docs/util/ver4.0/CURRENT.md` L94-96 の「未実装（ver4.1 以降の予定）」セクションは ver5.0 で「セッション継続機能」を実装済みのため、`write_current` ステップで該当行を ver5.0 の CURRENT.md に引き継ぐ際に削除すること

### リファクタリングの必要性を感じた点

なし。`_run_steps` のセッション管理ロジックは局所的に追加可能で、既存責務との混在も最小限。

---

## wrap_up 対応結果

| 項目 | 対応 | 内容 |
|---|---|---|
| MASTER_PLAN.md PHASE4.0 更新 | ✅ 対応完了 | 「部分実装」→「実装済み（ver5.0 でセッション継続を実装し全項目完了）」に更新 |
| `docs/util/ver5.0/CURRENT.md` 作成 | 📋 次バージョン先送り | write_current 本来の責務。`ISSUES/util/medium/ver5.0-CURRENT.md未作成.md` として記録 |
| `docs/util/ver4.0/CURRENT.md` L92-96 削除 | ✅ 対応完了 | 「未実装（ver4.1 以降の予定）」セクション（セッション継続機能の記述）を削除 |
| WORKFLOW.md への `continue` ガイド追記 | ⏭️ 対応不要 | MEMO に「ver5.0 スコープ外」と明記済みのため |
