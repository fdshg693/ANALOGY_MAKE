# ver11.0 RETROSPECTIVE — `tests/test_claude_loop.py` 分割 / `scripts/tests/` 新設

## 1. ドキュメント構成整理

### 1-1. `docs/util/MASTER_PLAN.md`

- 1 行サマリ形式を維持。肥大化の兆候なし。本バージョンは既存 ISSUE 消化（`pythonテスト肥大化`）で MASTER_PLAN の項目ステータスには変化なし
- **再構成提案: なし**

### 1-2. `MASTER_PLAN/PHASE7.0.md`

- §1 = 部分完了（ver10.0）、§2〜§8 未着手の状態が継続。現行 PHASE は未完走
- **新 PHASE（PHASE8.0）の骨子作成は不要**（PHASE7.0 §2〜§8 が明確に控えている）

### 1-3. `CLAUDE.md` の肥大化チェック

- ルート `CLAUDE.md` 60 行台、`.claude/CLAUDE.md` は ROLE.md 参照のみで健全
- ver11.0 のテスト配置変更に伴い「`scripts/tests/` 配下に Python テストを配置する」記述が将来的に必要になるが、これは `docs/util/ver11.0/CURRENT_tests.md` および `scripts/README.md` に記述済。CLAUDE.md への反映は不要
- **分割提案: なし**

### 1-4. ISSUES ディレクトリ健全性

- util カテゴリ 5 件（medium 4 / low 1）。ver11.0 wrap_up で `pythonテスト肥大化.md` 削除、`scripts構成改善.md` を新規追加という扱いはなかった（既存のまま）
- 件数閾値（10 件超）には未到達。**構成変更提案: なし**

## 2. バージョン作成の流れの検討

### 2-1. 各ステップの効果

| ステップ | 評価 | コメント |
|---|---|---|
| `/issue_plan` | ◎ | `workflow: full` / `source: issues` を frontmatter に正しく記録。high 1 件を優先選定し、medium 2 件（`issue-review-rewrite-verification` / `scripts構成改善`）を次バージョン送りとする判断を ROUGH_PLAN §「なぜ他 ISSUE を含めないか」に明文化 |
| `/split_plan` | ◎ | IMPLEMENT.md 352 行に展開。7 件の判断事項（配置先 / `__init__.py` / 粒度 / ヘルパ / コマンド集約 / CI / 移行手順）を確定、リスク R1〜R6 を事前列挙。plan_review_agent で review 実施 |
| `/imple_plan` | ○ | IMPLEMENT.md §1-7 の Phase B per-step commit（11 コミット）を**サブエージェントで 1 コミットに集約**。CLAUDE.md「段階的アプローチのスキップ」条件に合致（機械的分割 + 件数保全検証済）と判断し適用。乖離は MEMO に記載済 |
| `/wrap_up` | ◎ | `pythonテスト肥大化.md` を削除、`test-issue-worklist-limit-omitted-returns-all.md` 本文中の参照先（`tests/test_claude_loop.py` → `scripts/tests/test_issue_worklist.py`）を更新。MEMO 乖離 3 件は記録のみで対応不要と判定 |
| `/write_current` | ◎ | 4 分割構成（`CURRENT.md` + `_scripts/_skills/_tests`）を維持。`CURRENT_tests.md` を `scripts/tests/` 11 ファイル体系に書き換え |
| `/retrospective` | — | 本ステップ |

### 2-2. 流れに対する改善提案

ver11.0 は **サブエージェント活用による 1 コミット集約** という積極的な乖離判断が含まれたが、MEMO に (a)(b)(c) の根拠と git bisect 上のトレードオフが明記されており、事後に振り返り可能な形が保てている。SKILL 改修につながる構造的問題は観察されなかった。

検討した観点（いずれも改修不要と判断）:

- **a. Phase B の per-step commit スキップの正当化**: CLAUDE.md「段階的アプローチのスキップ条件」の現文言は ver11.0 のケース（機械的分割 + 件数保全）に十分適用可能で、MEMO 乖離節で逐条的に確認されている。SKILL 側の明文化追記は不要
- **b. pre-existing テスト失敗の継続発覚**: `test_limit_omitted_returns_all` は ver10.0 RETROSPECTIVE で「ver10.1 で quick 消化」を推奨したが、その後 `pythonテスト肥大化` (high) が追加されたため優先度で上書きされ ver11.0 では保全に留まった。ver11.0 で再構成に伴い参照先（`scripts/tests/test_issue_worklist.py`）への更新も完了しており、**baseline 確認を SKILL で強制する必要性は依然なし**（高優先度 ISSUE の割り込みを SKILL が機械的に却下できないほうが運用上健全）
- **c. リスク事前列挙の効果**: IMPLEMENT.md §3 の R1〜R6 に対して wrap_up で逐条検証（4 件検証済 / 2 件「検証不要」と判定しその根拠を記述）。ver8.0 から続く「リスク列挙 → wrap_up 検証マトリクス」運用が安定

### 2-3. 即時適用したスキル変更

**なし**。ver11.0 は事前計画どおり（乖離は MEMO で justification 済み）進行したため、`.claude/skills/` 配下への即時適用は行わない。

## 3. 次バージョンの種別推奨

### 3-1. 判定材料 3 点の突合

1. **ISSUE 状況**（`issue_worklist.py` 結果 ready/ai 2 件）:
   - `ISSUES/util/medium/issue-review-rewrite-verification.md` — util 単体消化不能（app / infra ワークフロー起動待ち）、ver6.0 からの持ち越し継続
   - `ISSUES/util/medium/scripts構成改善.md` — `scripts/` 配下のワークフロー関連コード分離 / `scripts/README.md` 分割 / 運用注記追加
   - 加えて raw/ai 相当: `test-issue-worklist-limit-omitted-returns-all.md` / `cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md`
2. **MASTER_PLAN の次項目**: PHASE7.0 §2「起動前 validation」が未着手。§1 完了条件③はここで吸収される設計
3. **現行 PHASE 完走状態**: PHASE7.0 §1 部分完了 / §2〜§8 未着手で未完走。新 PHASE 骨子は不要

### 3-2. 推奨

**推奨: ver11.1（マイナー、quick）で `ISSUES/util/medium/scripts構成改善.md` を消化 → ver12.0（メジャー、full）で PHASE7.0 §2 起動前 validation に着手**

推奨根拠:

- `scripts構成改善.md` は ver11.0 の `scripts/tests/` 新設と**テーマが連続**（どちらも `scripts/` 配下の構造整理）しており、ver11.0 の記憶が新しいうちに続けて手を入れるほうが効率的。変更範囲も「ワークフロー関連コード分離」「`scripts/README.md` 分割」「運用注記追加」で、1〜2 ファイル程度の追加 / 既存 README のリファクタに収まり **quick ワークフロー適合**
- ver10.0 RETROSPECTIVE §3-2 で推奨した `test-issue-worklist-limit-omitted-returns-all.md` は依然 pre-existing 失敗として残るが、ver11.0 でこのテストの参照先（新配置）は既に整備済み。**ver11.1 で `scripts構成改善` を先に処理**しても PHASE7.0 §2 着手前の baseline 安定化（ver12.0 前の消化）には支障しない。`test_limit_omitted_returns_all` は `scripts構成改善` と並行して拾うか、ver11.2 で単独処理するかは `/issue_plan` に委ねる
- PHASE7.0 §2「起動前 validation」は MASTER_PLAN の新項目着手 + アーキテクチャ変更（全 step 走査 + schema 検証 + エラー集約報告）であり、CLAUDE.md 版管理規則「メジャー = MASTER_PLAN 新項目 / アーキテクチャ変更」に合致 → `ver12.0` メジャー + `workflow: full` が妥当
- `cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md` は引き続き PHASE7.0 §2 で吸収予定
- `issue-review-rewrite-verification.md` は util 単体消化不能のまま持ち越し継続

**代替案 A（採用しない）**: ver11.1 で `test-issue-worklist-limit-omitted-returns-all.md` を先に消化。利点は ver10.0 RETROSPECTIVE の推奨を遵守する点。欠点は ver11.0 の記憶が新しいうちに `scripts構成改善` を拾う機会を逃し、後でコンテキストを再構築するコストが発生する点。どちらを先にしても ver12.0 着手前までに両方消化される前提なら、近接テーマを優先する

**代替案 B（採用しない）**: ver11.1 で PHASE7.0 §2 へ直接着手。欠点は `scripts構成改善` / `test_limit_omitted_returns_all` / `cli-flag-compatibility` 等を §2 と同コミット化すると review 負荷が跳ねる点

→ **最終推奨: ver11.1（マイナー、quick）で `scripts構成改善.md` を消化。PHASE7.0 §2 着手は ver12.0 以降**

## 4. 振り返り結果の記録

### 4-1. ISSUES ファイルの整理

- **削除**: なし（`pythonテスト肥大化.md` は wrap_up 段階で既に削除済み）
- **持ち越し**（削除しない、理由記載済）:
  - `ISSUES/util/medium/issue-review-rewrite-verification.md` — ver6.0 からの持ち越し継続。util 単体消化不能
  - `ISSUES/util/medium/scripts構成改善.md` — ver11.1 で消化予定（§3-2）
  - `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` — 参照先を ver11.0 新配置に更新済。ver11.1〜ver11.2 で quick 消化予定（`/issue_plan` に判定委任）
  - `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` — PHASE7.0 §2（ver12.0）で吸収予定
  - `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` — 同上
- **frontmatter 無しファイル**: なし

### 4-2. `REQUESTS/AI/` の整理

- `REQUESTS/AI/` 配下に実ファイルなし（ディレクトリ空）。**変更なし**

### 4-3. 即時適用したスキル変更

**なし**（§2-3 のとおり）。

### 4-4. 次バージョン ver11.1 への引き継ぎ

`scripts構成改善.md` 消化時の注意点:

1. **対応方針**: ISSUE 本文の 3 項目（ワークフロー関連コードと他コードの分離 / `scripts/README.md` 分割 / 運用注記追記）に従う
2. **テーマ連続性**: ver11.0 で `scripts/tests/` を新設したので、テスト側の分離パターン（`scripts/tests/_bootstrap.py` / `__init__.py` / `python -m unittest discover -s scripts/tests -t .` 集約）を参考にしつつ、プロダクションコード側の分離方針を決める。ただし ver11.0 IMPLEMENT §1-2 で決めた「`scripts/__init__.py` は**作らない**（`claude_loop.py` の絶対 import を守る）」方針は維持する — パッケージ化が必要なら別バージョンで慎重に扱う
3. **scripts/README.md 分割**: 現状は単一の README。「ワークフロー運用」「テスト」「個別ツール（issue_worklist / issue_status / claude_sync）」で分割するか、セクション整理に留めるかを ROUGH_PLAN で決定
4. **quick ワークフロー適合性**: 変更対象は `scripts/` 配下のファイル移動・README 編集・必要に応じた `scripts/claude_loop_lib/` 内の import パス調整。プロダクションコードの振る舞いは不変を目標とする
5. **ver12.0（PHASE7.0 §2）への引き継ぎ**: `scripts構成改善` 完了後の新構成が §2 で追加される起動前 validation の配置方針（`claude_loop_lib/validators/` など）と整合するよう、ver11.1 の最終状態を ver12.0 ROUGH_PLAN の前提として確認する

### 4-5. 今バージョンからの学び（手法面）

- **サブエージェント経由での 1 コミット集約**: 1881 行 / 41 クラスという機械的分割に対して、per-step commit より一括集約のほうが対話コスト・レビューコストともに低い。条件は「分割結果が前段階に依存しない」「件数保全が定量的に検証できる（192 件 / 1 fail の一致）」「import / パス調整が網羅的にテスト実行で検出される」の 3 点。次回同等の機械的再構成時は同パターンを初手から適用してよい
- **IMPLEMENT.md 内の「機械的 VERBATIM コピー」指示とパス依存テストの干渉**: `TestYamlSyncOverrideKeys._yaml_path` のように、テスト本体が `Path(__file__).parent.parent / "scripts"` で物理位置から逆算するヘルパを持つ場合、移動に伴う不可避の適応が発生する。ver11.0 ではコピー後に検出し `parent.parent.parent` に修正したが、次回類似作業では IMPLEMENT.md の段階で「`__file__` 依存のパス計算は grep で事前抽出し、移動後の階層差分を明示する」チェックを含めると事前見積もりが精緻化する。ただしこれは SKILL 強制化までは不要で、個別 IMPLEMENT.md でのチェックリスト項目として運用者判断に委ねる
- **pre-existing テスト失敗の継続観察**: ver10.0 → ver11.0 と 2 バージョン連続で `test_limit_omitted_returns_all` が pre-existing 失敗として未処理のまま持ち越されたが、ver11.0 の再構成で参照先は整備済みで、baseline 健全性は ver12.0 着手前までに消化すれば PHASE7.0 §2 への悪影響は回避できる。**高優先度 ISSUE（今回の `pythonテスト肥大化`）が発生した場合、pre-existing fail の保全優先度は一段下げられる**という運用判断が機能した
