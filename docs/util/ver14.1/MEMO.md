# ver14.1 MEMO

## 実装サマリ

ROUGH_PLAN の方針通り、raw/ai ISSUE 2 件を再評価し、いずれも `done/` へ移動した。

### ISSUE A: cli-flag-compatibility-system-prompt.md → done/

**再評価結果**: 吸収済と判定

根拠:
1. `--append-system-prompt` は `commands.py:50` でログパス・unattended 注入・FEEDBACKS 注入のために**全 step で必ず発行されている** → 実運用検証済
2. `--system-prompt` は YAML 3 本すべてコメントのみ（実値投入ゼロ）。ver10.0 から ver14.0 までの 4 バージョン・全ワークフロー実行で一度も `unknown option` エラーが発生していない
3. `.claude/rules/scripts.md` §3 が新規フラグ追加時の構造整合性（`parse_args()` ↔ `build_command()` 同期 / YAML 3 本同一化 / `validation.py` 明示拒否）をカバー

残論点（「Claude CLI バイナリが --system-prompt を受理するか起動時チェック」）は非現実的（実値ゼロ）かつ v10.0 以降発生実績なしのため、現時点での新規実装は不要と判断。

### ISSUE B: system-prompt-replacement-behavior-risk.md → done/

**再評価結果**: 吸収済と判定

根拠:
1. `scripts/USAGE.md:94` に明示警告「`system_prompt` はデフォルト system prompt を完全置換するため…通常は `append_system_prompt` を使うこと」が存在（ver10.0 wrap_up 対応済）
2. `/retrospective` SKILL §3.5 評価観点 1「`system_prompt` / `append_system_prompt` が step 役割に合っているか」で不適切な置換型利用を評価時に検出可能
3. 既存 YAML 3 本に `system_prompt` の実値投入はゼロ

§3.5 の評価観点が若干暗黙的だが、評価者が見るテンプレに `system_prompt`/`append_system_prompt` の適切性が明示されており、リスク顕在化前に検出できる体制は整っている。

## 運用観察記録（handoff §4 観察ポイント）

1. **handoff 1 回消費挙動**: `FEEDBACKS/handoff_ver14.0_to_next.md` が本ループ処理後に `FEEDBACKS/done/` へ移動していることを `git status` で確認 ✅ → §4.5 消費機構は正常に機能している
2. **`.claude/rules/scripts.md` の `paths: scripts/**/*` frontmatter**: 本ループは scripts/ への実装変更ゼロのため直接観測機会なし。ver14.0 MEMO §リスク 6 の先送り事項を引き続き保留
3. **§3.5 評価の形骸化**: 本ループは quick のため §3.5 自体は実行されない。次回 full ループで差分評価基準が機能するかを観察予定（ver14.1 では介入しない）

## 乖離なし

ROUGH_PLAN の計画通り。新規実装（`validation.py` CLI フラグ実在チェック）は不要と判定し、両 ISSUE とも `done/` 移動で完了した。

## 残 ISSUE 状況（util / ver14.1 完了時点）

| ファイル | priority | status | assigned | 備考 |
|---|---|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai | app/infra カテゴリ実行まで継続持ち越し |
| `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` | low | raw | ai | ver14.0 記録系 ISSUE、観察保持 |
| `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` | low | raw | ai | ver14.0 記録系 ISSUE、観察保持 |
| `ISSUES/util/done/cli-flag-compatibility-system-prompt.md` | medium | — | — | **本ループで done 化** |
| `ISSUES/util/done/system-prompt-replacement-behavior-risk.md` | low | — | — | **本ループで done 化** |
