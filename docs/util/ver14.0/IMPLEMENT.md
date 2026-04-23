# ver14.0 IMPLEMENT — PHASE7.0 §6+§7+§8 一括着手

`ROUGH_PLAN.md` に基づき、§7（rules/scripts.md 新設と規約集約）を先行し、その上に §6（retrospective からの FEEDBACK handoff）と §8（workflow prompt / model 評価）の SKILL 拡張を積む順序で実装する。Python コード側の構造変更は発生しない。

## 1. 実装順序

1. **§7 rules 整備（先行）** — `.claude/rules/scripts.md` を新規作成し、既存 docs / SKILL / CLAUDE.md に散在する stable 規約の一次資料を rules 側に確立する。これを最初に済ませることで、後続の §6 / §8 で SKILL 本文を書く際に「規約の根拠は rules を見よ」のポインタ記法で済む
2. **§6 retrospective handoff** — `/retrospective` SKILL に「次ループ向け FEEDBACK 書き出し」節を追加。`/issue_plan` 側にも受信指示を追記
3. **§8 prompt / model 評価** — `/retrospective` SKILL に「workflow step 別 prompt / model 評価」節を追加。評価結果の §6 FEEDBACK 連携を明文化
4. **docs 整合** — `scripts/README.md` / `scripts/USAGE.md` / `CLAUDE.md` / `.claude/SKILLS/meta_judge/WORKFLOW.md` から rules へ移した stable 規約の重複を削除。`meta_judge/WORKFLOW.md` 既存の誤記（`command / mode / defaults`。ver13.0 で `mode` 撤去済）も併せて整合させる

## 2. `.claude/` 配下の編集手順

`.claude/rules/scripts.md` 新規作成 / `.claude/skills/retrospective/SKILL.md` 編集 / `.claude/skills/issue_plan/SKILL.md` 編集 / `.claude/SKILLS/meta_judge/WORKFLOW.md` 編集 はすべて CLI `-p` モードの security 制約により直接編集不可。ver13.0 で確立済の手順を本実装でも踏襲する:

1. `python scripts/claude_sync.py export` で `.claude/` → `.claude_sync/` をコピー
2. `.claude_sync/` 側で編集
3. `python scripts/claude_sync.py import` で書き戻す
4. `git status` / `git diff` で想定ファイルに差分が入っていることを確認してからコミット

**要点**: `/split_plan` 本ステップでは `.claude/` に触らない（IMPLEMENT.md 策定のみ）。実ファイル編集は `/imple_plan` で上記手順に従って行う。

## 3. §7 `.claude/rules/scripts.md` 新規作成

### 3-1. frontmatter と適用範囲

`.claude/rules/` の新しい慣例として `paths:` frontmatter を導入する（既存 `.claude/rules/claude_edit.md` は現状 `paths:` を持たないグローバル rule のため、本 rule が `paths:` 付き rule の最初の実例となる）:

```markdown
---
paths:
  - "scripts/**/*"
---
```

本文は stable（毎回守るべき作法）に限定し、volatile（PHASE ごとの進行状況・一時的注意点）は docs 側に残す。

**運用上の注意**: `paths:` frontmatter を agents がどう解釈するかは本バージョンでは未検証（§6 リスク参照）。rule として書いておけば参照されうる状態を整えるに留め、実動作検証は次ループ以降の retrospective に委ねる。

### 3-2. 収録する stable 規約（骨子）

以下 5 系統を `.claude/rules/scripts.md` に収める。各項目は 2〜4 行程度の簡潔な記述とし、詳細は `scripts/README.md` / `scripts/USAGE.md` へのリンクで委譲する:

1. **Python 前提**: Python 3.10+、標準ライブラリ + PyYAML のみ。dataclass や 3rd-party 依存を増やさない。PEP 604 型ヒント（`str | None`）を使う
2. **パス操作**: `pathlib.Path` を使う。文字列連結 / `os.path.join` は使わない。相対パスは `Path(__file__).resolve().parent` を起点にする
3. **CLI 引数処理**: `argparse` を使う。新規オプションは `claude_loop.py` の `parse_args()` と、値を渡す先（多くは `claude_loop_lib/commands.py` の `build_command`）の両方を更新する。廃止オプションは黙って無視せず、argparse のエラーで即座に落とすか validation で拒否する
4. **frontmatter / YAML 更新時の作法**: `claude_loop_lib/frontmatter.py` の `parse_frontmatter` を共通基盤として使う（独自再定義しない）。ISSUE frontmatter は `claude_loop_lib/issues.py` の共通定数を参照する。YAML override キーを独自に増やす場合は、必ず `claude_loop_lib/workflow.py` の定数定義と `validation.py` を通す経路を使う（具体的な定数名・拡張手順は `scripts/README.md` / `scripts/USAGE.md` を一次資料とする）
5. **ログ出力**: `print()` ではなく `claude_loop_lib/logging_utils.py` の `TeeWriter` / `print_step_header` / `format_duration` を使う。ログファイル名規約は `{YYYYMMDD_HHMMSS}_{workflow_stem}.log`

### 3-3. 書かないこと

以下は docs 側に残す（rules には書かない）:

- PHASE 固有の進捗メモ（例: 「ver13.0 で `--auto` 撤去」）
- validation 検査項目一覧の詳細表（`scripts/README.md` 「起動前 validation」節に存在）
- CLI オプション一覧の網羅表（`scripts/USAGE.md` に存在）
- ワークフロー YAML の継承ルール詳細（`scripts/USAGE.md` に存在）
- テスト実行コマンド例

ポイントは「何をどこで守るか」の根拠を示すことであり、仕様の丸写しはしない。

### 3-4. 既存 docs / CLAUDE.md からの重複整理

`.claude/rules/scripts.md` に移した stable 規約のうち、既存 docs に重複がある箇所は以下のように整理する:

- `scripts/README.md`「前提条件」節（L8-11）: Python 前提はそのまま残す（docs も見る人がいるため）が、rules に「毎回守る」観点が入ったことを前書きで示す（1 行追記）
- `scripts/README.md`「拡張ガイド」節（validation.py の override キー記述、L147-149）: rules に要点を集約したので、docs 側は手順詳細だけ残す（重複削除は 1〜2 行程度）
- `scripts/USAGE.md`「拡張ガイド」節（L235-240）: rules の項目番号と整合するよう見出しを統一するのみ（内容は残す）
- `CLAUDE.md` L31（scripts ディレクトリの説明）: 現状 1 行で詳細は `scripts/README.md` に委譲済のため変更不要。rules への pointer 追記も不要（`.claude/rules` は agents が自動読込する想定で、CLAUDE.md へのアンカーは重複になる）

**整理の原則**: volatile は docs、stable は rules、と境界が曖昧な項目は rules に書かない。迷ったら rules 外に置く。

## 4. §6 `/retrospective` からの FEEDBACK handoff

### 4-1. `.claude/skills/retrospective/SKILL.md` への追記

既存 §4「振り返り結果の記録」の直後（`## 5. Git にコミットする` の前）に新しい節 `## 4.5 次ループへの FEEDBACK handoff` を挿入する。主な内容:

1. **目的**: retrospective の成果のうち「次ループで 1 回だけ読ませたい補助線」を `FEEDBACKS/<filename>.md` に書き出す
2. **対象**:
   - 次に着手すべき ISSUE の候補（優先選定の根拠つき）
   - 直前バージョンで保留した判断の継続確認事項
   - workflow 設定（prompt / model / temperature）見直しメモ（§8 の評価結果との接続点）
   - 次 `/issue_plan` に渡したい注意点
3. **書かないケース**: 「次ループで特に引き継ぐべき内容がない」なら書き出しを省略する。空の handoff / 感想のみの FEEDBACK は禁止（次ループの FEEDBACK 消費枠を無駄にしない）
4. **ファイル書式**:
   - ファイル名: `handoff_ver{現行バージョン}_to_next.md`（ver14.0 からの handoff なら `handoff_ver14.0_to_next.md`）
   - frontmatter: `step: issue_plan`（次ループの `/issue_plan` にのみ注入する。retrospective 由来の handoff はほぼ全て issue_plan 向けのため、catch-all ではなく step 限定で書く）
   - 本文: 「## 背景」「## 次ループで試すこと」「## 保留事項」の 3 節を推奨
5. **§4 運用ルールとの整合**: 書き出した FEEDBACK は次ループで 1 回だけ消費され、その後 `FEEDBACKS/done/` に退避される（ver13.0 の `consume_feedbacks` 挙動に従う）。恒久メモリではないことを SKILL 本文に 1 行で明記する
6. **即時適用対象**: 本 §6 の追記自体が `/retrospective` SKILL 編集であり、既存 §4 の「即時適用してよい変更」範囲に含まれる。`scripts/claude_sync.py` 手順で反映する

### 4-2. `.claude/skills/issue_plan/SKILL.md` への追記

「## 準備」節の「直前バージョンの `RETROSPECTIVE.md` が存在する場合は確認し…」の直後に、FEEDBACK handoff の受信指示を追加する:

> `FEEDBACKS/handoff_ver*_to_next.md` が存在する場合、`--append-system-prompt` 経由で自動注入される。ROUGH_PLAN の判断材料として優先度高で参照する（retrospective が次ループ向けに意図的に書き出した補助線であり、感想ではなく次ステップに効く入力として扱う）。

**挿入位置の意図**: 「ISSUE レビューフェーズ」より前に読ませる（ROUGH_PLAN 判断材料として活用するため）。レビュー結果に handoff の観点を反映できる順序で SKILL を構成する。

FEEDBACK 自動注入は既存の `load_feedbacks()` 経路で成立するため、コード変更は不要。SKILL 側は「どう読むか」の指示だけを追加する。

### 4-3. `.claude/SKILLS/meta_judge/WORKFLOW.md` への整合反映

既存 L45 の「`command / mode / defaults` セクションは同一内容で維持する」を ver13.0 時点の事実（`mode` 撤去済）に合わせて `command / defaults` に訂正する。また「各 step のモデル・エフォート」の節末に「§6 で retrospective が書き出した FEEDBACK は次ループの `/issue_plan` で消費される」を 1 行追記する。

## 5. §8 workflow prompt / model 評価の追加

### 5-1. `.claude/skills/retrospective/SKILL.md` への追記

§4.5 の前、`## 3 次バージョンの種別推奨` の直後に新節 `## 3.5 workflow prompt / model 評価` を挿入する。主な内容:

1. **評価対象**: 直前バージョンで実行された workflow YAML（`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml`）の各 step について、以下を評価する
   - `system_prompt` / `append_system_prompt` が step 役割に合っていたか、長すぎないか、他 step と指示重複していないか
   - `model` 選択（`opus` / `sonnet` / `haiku`）と `effort`（`low` / `medium` / `high` / `xhigh` / `max`）が品質・速度・コストに見合っていたか
   - step 間の `continue: true` / 新規セッション選択が適切だったか
2. **評価粒度**: 各 step を「維持 / 調整 / 削除候補」の 3 分類で記録する。分類理由（1〜2 行）と、調整・削除候補には「次ループでの具体的な修正案」を添える
3. **評価結果の出力先**: `RETROSPECTIVE.md` §8 評価節に本文（全評価）を残し、「調整 / 削除候補」のうち次ループで試す価値があるものを §4.5 handoff FEEDBACK に転記する。**転記基準**: 「次 1 ループ以内に試す具体的な調整」のみ handoff に転記する。複数バージョンにまたがる検討や、すぐには試さない観察メモは RETROSPECTIVE.md に留める（handoff の消費枠を無駄にしないため）
4. **省略条件**: 評価材料がない（例: 直前バージョンでモデル変更を試していない / step 実装差分が皆無）場合は本節を省略してよい。形骸的な評価を毎ループで要求しない
5. **既存の「即時適用」との関係**: 本節は評価記録であり、SKILL / YAML の実編集は §4.5 handoff → 次ループの `/issue_plan` → ユーザー判断 or AI 編集という経路で行う。評価時点では YAML を直接編集しない（評価と適用の分離）

### 5-2. 評価記録の最小テンプレ（SKILL 本文内で示す例）

```markdown
## §8 workflow prompt / model 評価

### 評価対象バージョン: ver{X.Y}

| step | model | effort | 分類 | 理由・次ループ案 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | ROUGH_PLAN.md の判断精度良好 |
| split_plan | sonnet | medium | 調整 | IMPLEMENT.md の実装詳細が浅い。effort → high で試す |
| imple_plan | opus | max | 維持 | 実装品質問題なし |
| ... | | | | |
```

## 6. リスク・不確実性

新規ライブラリや未使用 API は導入しないため主なリスクは運用設計面に集中する:

1. **rules と docs の責務分離が曖昧化するリスク**（PHASE7.0 §6-リスクに明記済）
   - rules 側に「毎回守る規約」以外（進捗メモ・運用ログ・詳細仕様）が流入すると、stable convention が二重管理になり将来の更新で片方が取り残される
   - **軽減策**: §3-3「書かないこと」の明確化に加え、rules 末尾に「詳細仕様は `scripts/README.md` / `scripts/USAGE.md` を一次資料とする」を 1 行明記する
2. **FEEDBACK handoff が感想メモ化するリスク**
   - retrospective が「何か書かねば」と感じて空気感だけの FEEDBACK を出すと、次ループの消費枠を無駄にする（§4 は 1 ループ限定運用なので重い）
   - **軽減策**: SKILL 本文で「書くべき内容がない場合は出さない」を明示。handoff ファイル名を `handoff_*` プレフィックス固定にし、retrospective 以外が書き出さない慣習を作る
3. **prompt / model 評価の過剰化リスク**
   - step 全数を毎バージョン評価すると retrospective が重くなり、形骸的記述が増える
   - **軽減策**: §5-1(4)「省略条件」を SKILL 本文に明記。差分評価（直前バージョンから変えた step のみ再評価）を推奨する 1 行を添える
4. **`.claude/` 編集手順のミスで反映漏れが起きるリスク**
   - `claude_sync.py export → edit → import` の 3 段階のうち import を忘れると `.claude/` に差分が入らず commit 時に気付きにくい
   - **軽減策**: `/imple_plan` 実装時に `git diff --name-only .claude/` で想定ファイルが含まれているかを必ず確認する手順を IMPLEMENT.md §2 に明記済
5. **`meta_judge/WORKFLOW.md` L45 の `mode` 誤記がさらに古い参照を連鎖させる可能性**
   - 他所（docs 配下）にも同系の誤記がないかは未確認。修正は meta_judge のみに限定し、検出漏れがあれば retrospective / 次バージョンで拾う
   - **軽減策**: `/imple_plan` 実装中に `grep -rn "mode:" docs/ scripts/ .claude/` で念のため確認する
6. **rules の自動読込範囲に対する agents の挙動が明文化されていない**
   - `.claude/rules/*.md` の `paths:` frontmatter が agents にどう解釈されるかは現状 `claude_edit.md` の 1 例しかない。追加した `scripts.md` が期待どおり読まれる保証は実行して初めて分かる
   - **軽減策**: 本バージョンでは「ルールとして書いておけば agents が参照しうる状態」を整えるに留め、自動読込挙動の検証は PHASE7.0 §6 後の retrospective で評価対象にする（§8 評価と同じ手法で扱う）

## 7. テスト戦略

SKILL / rules 中心の変更で Python コード変更は発生しないため、新規テストは追加しない。既存回帰の維持のみを担保する:

1. **既存テスト**: `python -m unittest discover -s scripts/tests -t .` で 233 件（ver13.1 時点）が全通過することを確認
2. **§4 FEEDBACKS 異常終了 invariant**: ver13.1 で追加された `TestFeedbackInvariant` が、§6 の handoff ファイルも正常に `FEEDBACKS/done/` へ退避される挙動を暗黙的にカバーすることを確認（handoff ファイルは通常 FEEDBACK と同じパスで書かれるため、既存テスト範囲内）。新規テスト追加の要否は `/imple_plan` 実装時に handoff ファイルの書式が確定した段階で最終判断する
3. **validation**: `.claude/rules/scripts.md` 新規作成は validation 対象外（YAML でもステップ定義でもない）だが、念のため `python scripts/claude_loop.py --dry-run` で全 YAML の validation が通ることを `/imple_plan` 完了時に確認
4. **手動確認**:
   - `cat .claude/rules/scripts.md` で paths frontmatter + 本文が期待どおりか確認
   - `grep -n "next ループ\|handoff" .claude/skills/retrospective/SKILL.md` で §4.5 / §3.5 節の挿入位置が想定どおりか確認
   - `grep -n "handoff" .claude/skills/issue_plan/SKILL.md` で受信指示が追加されているか確認
   - `grep -rn "mode:" scripts/ .claude/ docs/util/ 2>/dev/null` で ver13.0 で撤去済の `mode:` セクションへの古い参照が残っていないか確認（`meta_judge/WORKFLOW.md` L45 以外にヒットした場合は追加修正対象）

## 8. 関連 ISSUE の扱い方針

ROUGH_PLAN.md §「関連 ISSUE」に記載の 3 件について、本バージョン完了後の retrospective で以下の判断を行うよう MEMO に記載する:

- `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`（`raw / ai`）: §7 で scripts 系 CLI 規約を rules 化した結果、本 ISSUE の論点（CLI フラグ互換性の明文化）が rules 側に吸収できたかを確認。吸収済なら `done` 化、残っていれば `ready` 昇格判断
- `ISSUES/util/low/system-prompt-replacement-behavior-risk.md`（`raw / ai`）: §8 で prompt 評価基準を明文化した結果、本 ISSUE の論点（`system_prompt` 完全置換の副作用）が評価観点に織り込めたかを確認。織り込み済なら `done` 化、さらに踏み込む必要があれば `ready` 昇格
- `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready / ai`）: 引き続き util 単体消化不能のため持ち越し継続。ver14.0 本バージョンでは触らない

## 9. ファイル変更見積

| ファイル | 操作 | 見積行数 |
|---|---|---|
| `.claude/rules/scripts.md` | 新規作成 | 40〜60 行 |
| `.claude/skills/retrospective/SKILL.md` | 変更（§3.5 / §4.5 追記） | +50〜70 行 |
| `.claude/skills/issue_plan/SKILL.md` | 変更（FEEDBACK 受信指示追記） | +3〜5 行 |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | 変更（`mode` 誤記訂正・§6 handoff 1 行追記） | ±5 行 |
| `scripts/README.md` | 変更（rules 存在の前書き 1 行・重複整理 1〜2 行） | ±3 行 |
| `scripts/USAGE.md` | 変更（「拡張ガイド」見出し統一のみ） | ±2 行 |
| `docs/util/ver14.0/MEMO.md` | 新規作成（`/imple_plan` / `/wrap_up` で蓄積） | — |

合計編集規模は 100〜150 行程度。quick 閾値（3 ファイル以下かつ 100 行以下）を超えるため full で進める判断（ROUGH_PLAN.md §「ワークフロー選定根拠」）と整合する。

## 10. `/imple_plan` への引き継ぎ要点

1. `.claude/` 編集は必ず `claude_sync.py export → edit → import` 手順。`git status` で `.claude/` 側に差分が入っていることを確認してからコミット
2. 実装順序は本 IMPLEMENT §3（rules = PHASE7.0 §7）→ §4（handoff = PHASE7.0 §6）→ §5（prompt/model 評価 = PHASE7.0 §8）→ §3-4（docs 整合）の順で、後段は前段に依存する
3. SKILL 本文の節番号（§3.5 / §4.5）は既存節との衝突を避けるための暫定番号。**既存 SKILL の番号書式は混在（例: `## 1.` と `## 3` が共存）しているが、本バージョンでは番号書式の統一は行わない**（意図しない diff を増やさない）。新節は既存節の直後に違和感ない番号で挿入するに留める
4. リスク §6（rules 自動読込挙動）は実装中に検証できないため、動作確認は次ループ以降の retrospective に委ねる旨を MEMO.md に記載
5. 既存テスト 233 件の全通過を確認し、`MEMO.md` に「既存回帰維持確認済」を記録
