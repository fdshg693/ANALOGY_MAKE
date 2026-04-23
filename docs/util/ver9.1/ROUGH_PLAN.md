---
workflow: quick
source: issues
---

# ROUGH_PLAN: util ver9.1 — `--workflow auto` の ROUGH_PLAN.md 同定ロジック強化

## ISSUE レビュー結果

今回 `review / ai` の ISSUE は 0 件のため、状態遷移は発生しなかった（レビューフェーズはスキップ）。

## ISSUE 状態サマリ（util、本 plan 開始時点）

| assigned × status | high | medium | low | 計 |
|---|---:|---:|---:|---:|
| `ready / ai` | 0 | 2 | 2 | 4 |
| `review / ai` | 0 | 0 | 0 | 0 |
| `need_human_action / human` | 0 | 0 | 0 | 0 |
| `raw / human` | 0 | 0 | 0 | 0 |
| `raw / ai` | 0 | 0 | 0 | 0 |

（`python scripts/issue_status.py util` 実行結果に基づく）

対象 ISSUE 一覧:

| path | priority | status | assigned | 本 plan での扱い |
|---|---|---|---|---|
| `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` | medium | ready | ai | **クローズ**（人間コメントにより検証済。ver9.1 で `done/` へ移動） |
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai | 持ち越し（util 単体では消化不能、app/infra ワークフロー起動待ち） |
| `ISSUES/util/low/auto-mtime-robustness.md` | low | ready | ai | **今回の主対象**（下記参照） |
| `ISSUES/util/low/issue-worklist-json-context-bloat.md` | low | ready | ai | 持ち越し（件数閾値未到達、YAGNI 継続） |

## バージョン種別の判定

**マイナーバージョンアップ (ver9.1)** として進める。

判定根拠:

- 既存 ISSUE の解消（ver9.0 で導入した `--workflow auto` の堅牢性向上）であり、バグ修正・既存機能改善に該当
- アーキテクチャ変更なし、新規ライブラリ導入なし、破壊的変更なし
- MASTER_PLAN の新項目着手ではない（PHASE6.0 は ver9.0 で全完了済、PHASE7.0 骨子作成は ver10.0 以降に先送りする方針が `docs/util/ver9.0/RETROSPECTIVE.md` §3-3 で確定済）
- 変更見込みファイルは `scripts/claude_loop.py` + `tests/test_claude_loop.py` + ISSUE 移動の計 3 本のみ
- CLAUDE.md バージョン管理規則「マイナー = バグ修正・既存機能改善・ISSUES対応」に合致

## ワークフロー種別の選択

**`workflow: quick`** を採用する。

判定根拠:

- 選定 ISSUE は `status: ready / ai` のみ（`review` なし）→ `quick` 許容条件を満たす
- 変更ファイルは 3 本以下（`scripts/claude_loop.py` / `tests/test_claude_loop.py` / 移動対象 ISSUE）
- 100 行以下の変更見込み（主要ロジック変更は `_find_latest_rough_plan` と `_run_auto` の局所改修）
- アーキテクチャ変更・新規ライブラリ導入なし

`source: issues`（既存 ISSUE 起点、MASTER_PLAN 新項目ではない）。

## 今回取り組む内容

`ISSUES/util/low/auto-mtime-robustness.md` の解消を主眼とし、副次的に人間コメントで検証済と判定された `issue-plan-split-plan-handoff-verification.md` を `done/` へクローズする。

### 主対象: `--workflow auto` の ROUGH_PLAN.md 同定ロジック強化

#### 現状（ver9.0 時点の挙動）

`python scripts/claude_loop.py`（= `--workflow auto` 新デフォルト）のフェーズ 2 は、`scripts/claude_loop.py::_find_latest_rough_plan` で `docs/{CURRENT_CATEGORY}/ver*/ROUGH_PLAN.md` を走査し、**`st_mtime` が最大のファイル**を「今回フェーズ 1 で書かれたもの」として同定している。

#### 問題点

以下の状況で誤同定が発生し得る:

1. 人間が過去バージョンの `ROUGH_PLAN.md` を `touch` / 再保存した直後に `--workflow auto` を起動した場合
2. フェーズ 1 が極めて短時間で終わり、mtime の秒解像度以下で既存ファイルと衝突した場合
3. mtime 解像度が粗いファイルシステム（FAT32 等）で実行した場合

誤同定が起きると:

- `auto: phase2 = <kind> (<yaml>)` の `<kind>` が想定と食い違う
- フェーズ 2 で想定外ワークフロー（full のはずが quick、または逆）が起動する
- `/issue_plan` が作成した新バージョンフォルダではなく、別の古いファイルが読まれる

ver9.0 RETROSPECTIVE §2-4 で「実走検証の観察対象」として残されていた項目であり、実走での事故が起これば `--workflow auto` 自体のブロッカーになり得るため、ver9.1 で先に閉じる。

#### ver9.1 で提供する振る舞い

ユーザー体験の変化（= 機能面での効果）:

- **フェーズ 1 開始前に存在した `ROUGH_PLAN.md` 群は、フェーズ 2 の候補から必ず除外される**
- **フェーズ 1 が新規生成したファイルだけがフェーズ 2 の対象になる**
- フェーズ 1 後に複数の新規ファイルが検出された場合は、バージョン番号が最大のものを選ぶ（安全側の明示判定）
- 新規ファイルが 0 件だった場合は `SystemExit` で即失敗し、「フェーズ 1 が実質的に ROUGH_PLAN.md を書かなかった」ことをユーザーに通知する
- 直接関連しない既存ファイルの `touch` / 再保存によるフェーズ 2 の挙動乱れは発生しなくなる

mtime 依存自体は残すが、「**フェーズ 1 開始時点の mtime 上限**」を明示的な閾値として記録することで、`touch` 耐性・秒解像度衝突耐性・FAT32 耐性を得る。実装方式（具体的な API 設計・閾値の受け渡し方法・代替案の比較）は `IMPLEMENT.md` に委ねる。

### 副次対象: `issue-plan-split-plan-handoff-verification.md` のクローズ

`ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` の本文末尾に、人間コメントとして以下の記述がある:

> **人間コメント:上記のver9.0 実走のログの`logs\workflow\20260423_135034_claude_loop.log`にて、`/issue_plan` ・ `/split_plan`の対応するsessionを確認すると異なっている。そのため、上記は検証済でCloseして問題ないと考えます。**

ver9.0 RETROSPECTIVE §2-2 時点では「完全独立セッション未検証」と判定されていたが、人間側で実ログから session ID の独立性が確認された。したがって ver9.1 スコープ内で `ISSUES/util/done/issue-plan-split-plan-handoff-verification.md` へ移動し、クローズする。

### 除外対象と除外理由

- `ISSUES/util/medium/issue-review-rewrite-verification.md`: 書き換えロジックの実動作確認には `ISSUES/app/medium/*.md` の `review / ai` ISSUE もしくは `ISSUES/infra/high/Windowsデプロイ.md` が必要。util カテゴリのワークフローでは消化不能なため持ち越し
- `ISSUES/util/low/issue-worklist-json-context-bloat.md`: util の ISSUE 数は 4 件にとどまり、JSON 肥大化の閾値に達していない。YAGNI により持ち越し
- PHASE7.0 骨子作成: `docs/util/ver9.0/RETROSPECTIVE.md` §3-3 で ver10.0 以降に先送りする方針が確定済

### MASTER_PLAN 状況（参考）

- `docs/util/MASTER_PLAN/PHASE1.0.md`〜`PHASE6.0.md` はすべて実装済
- `PHASE7.0.md` は未作成。`--workflow auto` を数回実走してから新フェーズの課題を具体化する方針
- 本 ver9.1 は既存 ISSUES 消化を優先し、MASTER_PLAN 新項目には着手しない（`source: issues`）

## 関連ファイル

### 主対象（コード）

- `scripts/claude_loop.py`
  - `_find_latest_rough_plan(cwd: Path) -> Path`（行 129〜141、`st_mtime` 最大値を返す現行実装）
  - `_run_auto(args, cwd, yaml_dir, tee, log_path, uncommitted_status) -> int`（行 241〜299、フェーズ 1 → `_find_latest_rough_plan` → フェーズ 2 の遷移ロジック）

### 主対象（テスト）

- `tests/test_claude_loop.py`
  - `TestFindLatestRoughPlan` クラス
  - `TestAutoWorkflowIntegration` クラス

### 副次対象（ISSUE 管理）

- `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` → `ISSUES/util/done/` へ git mv

### 参照ドキュメント

- `ISSUES/util/low/auto-mtime-robustness.md`（本 ISSUE 本文・対応方針 1・2 の記述あり）
- `docs/util/ver9.0/RETROSPECTIVE.md` §2-4 / §3-3 / §4-4
- `docs/util/ver9.0/IMPLEMENT.md` §10 R1（mtime 依存検証先送り）
- `docs/util/ver9.0/MEMO.md` §D3（ver9.0 で実走検証を見送った背景）
- `docs/util/ver9.0/CURRENT.md`（`--workflow auto` 仕様・CLI 例）
- `docs/util/MASTER_PLAN/PHASE6.0.md` §3（`--workflow auto` 元設計）

## 判断経緯の補足（`/split_plan` への引き継ぎ用）

### なぜ `auto-mtime-robustness.md`（low）を medium より優先するか

- 優先度順（high → medium → low）の原則に反するが、残 medium 2 件は以下の通り util 単独消化が不能/不要:
  - `issue-plan-split-plan-handoff-verification.md` は人間コメントで検証済判定済み → ver9.1 スコープ内で `done/` に移動するだけでクローズ可能（実装作業ではなくクリーンアップ）
  - `issue-review-rewrite-verification.md` は util カテゴリの ISSUE 書き換え対象が 0 件のため、app/infra カテゴリの `/split_plan` 起動時にしか検証機会が発生しない
- 一方 `auto-mtime-robustness.md` は ver9.0 で導入した `--workflow auto`（本リポジトリのデフォルトワークフロー）の堅牢性に直結し、実走で事故が起きれば即ブロッカーとなるため先行消化の価値が高い
- `docs/util/ver9.0/RETROSPECTIVE.md` §3-3 での推奨（「ver9.1 で `auto-mtime-robustness.md` を閉じる」）と一致する

### なぜ `quick` ワークフローを選んだか

- 変更対象は `scripts/claude_loop.py` 内の局所関数 2 つ（`_find_latest_rough_plan` / `_run_auto`）と対応テストのみ
- 選定 ISSUE に `review / ai` は含まれない（現時点で util カテゴリの `review / ai` は 0 件）
- アーキテクチャ変更なし、新規ライブラリなし、MASTER_PLAN 新項目着手なし
- ver9.0 RETROSPECTIVE §3-3 の推奨も `quick` 指定

### `/split_plan` で詰めるべき事前リスク（先行列挙）

`IMPLEMENT.md` 作成時に扱うべき論点:

1. **閾値記録方式 vs サイドチャネル方式の最終決定**: ISSUE 本文は両案併記。`docs/util/ver9.0/RETROSPECTIVE.md` §4-4-1 は方針 1（閾値記録方式）を推奨するが、`/split_plan` で再確認する
2. **閾値が候補全体に対してどこでサンプリングされるか**: フェーズ 1 実行直前のワンショットで十分か、並行書き込みがあり得るかの検証
3. **`SystemExit` 時のメッセージ設計**: 「フェーズ 1 が ROUGH_PLAN.md を書かなかった」「既存閾値超過ファイルが 0 件」の 2 ケースを区別してユーザーが原因特定できる文言にする
4. **`ver` 番号最大の解決規則**: `ver9.1` / `ver10.0` 比較で正しく `ver10.0` を勝たせる自然順ソート。`docs/util/CURRENT.md` 既存慣行（`ver4.0`〜`ver9.0`）に照らして数値ソートが安全
5. **既存テストケース `TestFindLatestRoughPlan` / `TestAutoWorkflowIntegration` との互換**: 既存テストで閾値未記録の呼び出し経路が残るかを確認し、API シグネチャ変更の影響を評価
6. **副次対象（ISSUE 移動）のコミット分離**: ロジック修正と ISSUE 移動を単一コミットにするか分離するかを `/wrap_up` で整理
7. **`--dry-run` との相性**: 現行コードはフェーズ 2 を `--dry-run` 時にスキップするため、`_find_latest_rough_plan` 呼び出し自体が発生しない。閾値記録の有無が `--dry-run` 経路に影響しないことを確認
8. **`IMPLEMENT.md` 作成後の `plan_review_agent` 観点**: 閾値サンプリング箇所とフェーズ 2 側の読み出しが関数境界を跨ぐ設計になるため、呼び出し側テストも含めるべき旨を指摘されうる

上記は `IMPLEMENT.md` で詳細化・棄却判断を行う前提の論点リストであり、本 ROUGH_PLAN 時点では実装方式に踏み込まない。
