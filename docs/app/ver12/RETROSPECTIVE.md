# ver12 振り返り

## 概要

- **対象**: Web検索連携（Tavily Search）
- **変更規模**: 17ファイル, +233行 / -5行（ドキュメント・インフラ含む）
- **コード変更**: 6ファイル（analogy-agent.ts, analogy-prompt.ts, nuxt.config.ts, package.json, .env.example, chat.test.ts）

---

## 1. ドキュメント構成整理

### MASTER_PLAN の状態

- PHASE1.0: 完了
- PHASE1.5: 完了（ストリーミング改善のみ ISSUES/low に残存）
- PHASE2: **4項目中3項目が完了**（残り: LangGraphステートマシンによるフロー制御）

**評価**: PHASE2 は次バージョン（ver13）で最終項目を完了する見込み。PHASE2 完了後は PHASE3 の策定が必要。現時点では MASTER_PLAN の再構成は不要。

### ISSUES の状態

| 優先度 | 件数 | 内容 |
|--------|------|------|
| high | 0 | — |
| medium | 0 | — |
| low | 6 | streaming, syntax-highlight, vitest-nuxt-test-utils, react-agent-getstate-type-safety, analogy-prompt-categories, streaming-tool-call-compatibility（new） |

**評価**: ISSUES は肥大化しておらず、全件 low。high/medium が存在しないため、次バージョンは MASTER_PLAN の残タスク（LangGraph）に集中可能。

### CLAUDE.md の状態

- ルート `CLAUDE.md`: 67行 — 適正サイズ、分割不要
- `.claude/CLAUDE.md`: 3行（ROLE.md への参照のみ）— 最小構成で適切

**提案**: 現時点で分割は不要。server/ や app/ 配下に固有の `CLAUDE.md` が必要になるのは、サブディレクトリ固有のルールが増えた場合（例: LangGraph導入で server/ の構成が複雑化した時点）。

---

## 2. バージョン作成の流れの検討

### 良かった点

1. **スコープが明確だった**: ROUGH_PLAN の「スコープ外」セクションにより、LangGraph 移行などを明確に除外し、フォーカスが保たれた
2. **リスク分析が機能した**: IMPLEMENT.md の「リスク・不確実性」セクションが `tavilyApiKey` パラメータ名の乖離を事前に認識させ、MEMO.md での記録に繋がった
3. **wrap_up のトリアージが適切**: MEMO の2項目に対し、「対応不要」と「ISSUES へ先送り」の判断が妥当だった
4. **CURRENT.md の品質が高い**: API契約、DB スキーマ、技術的決定事項まで網羅的に記載されている

### 改善点

#### A. ROUGH_PLAN に REFACTOR 判断の明記がない

`split_plan` スキルでは、小規模タスクの場合「小規模タスクのため REFACTOR 省略」と ROUGH_PLAN に記載するルールがある。ver12 の ROUGH_PLAN にはこの記載がなかった。

**対策**: `split_plan/SKILL.md` の小規模タスク判定セクションに、省略理由の記載を強調する一文を追加する。

#### B. 非機能変更がバージョンサイクルに混在

ver12 サイクル中に以下のインフラ改善がコミットされた:
- `REQUESTS/` の `HUMAN/` `AI/` への再編成
- `claude_loop.yaml` への `--disallowedTools` 追加
- `claude_loop.py` の `normalize_cli_args` 追加

これらは ver12 の機能（Tavily Search）とは無関係だが、同じサイクル内でコミットされた。

**評価**: 現時点では小規模な改善であり、分離コストのほうが高い。ただし、インフラ変更が大規模になる場合は `infra` カテゴリでの独立バージョン管理を検討すべき。

#### C. 実環境テストの仕組みがない

Tavily API キーを使った実環境テストが未実施のまま ISSUES に先送りされた。これは `imple_plan` スキルの「動作確認」セクションが typecheck と pnpm test に限定されているため。

**提案**: `imple_plan/SKILL.md` の動作確認セクションに、外部 API 連携がある場合の手動テスト確認項目をオプションとして追加する。

### スキルへの具体的な変更提案

#### 1. `split_plan/SKILL.md` — REFACTOR 省略の明記強化

現在の記述:
> 小規模タスクの場合:
> - `REFACTOR.md` の作成は省略してよい（ステップ1の `ROUGH_PLAN.md` に「小規模タスクのため REFACTOR 省略」と記載）

追加提案: ステップ1の指示に「**REFACTOR の要否判断を ROUGH_PLAN に必ず明記すること**（省略する場合は理由も記載）」を追加する。

#### 2. `imple_plan/SKILL.md` — 外部 API 連携時のテスト指針

動作確認セクションに以下を追加:
> 3. 外部 API 連携がある場合: API キーが利用可能であれば、手動での動作確認をユーザーに提案する。API キーが未設定の場合は、その旨を `MEMO.md` に記載する。

#### 3. `retrospective/SKILL.md` — RETROSPECTIVE.md の出力先を明記

現在のスキルでは振り返り結果の記録先が明示されていない。

追加提案: 「振り返り結果を `docs/{カテゴリ}/ver{最新バージョン番号}/RETROSPECTIVE.md` に記録する」を明記する。

---

## 3. 次バージョン（ver13）に向けて

### 優先タスク

- **PHASE2.4: LangGraphステートマシンによるフロー制御** — MASTER_PLAN の PHASE2 最終項目

### 注意事項

- LangGraph 導入は構成の大幅変更を伴う（単一プロンプト → ノード分離）。REFACTOR.md の作成が必須になる可能性が高い
- server/ 配下の構成が複雑化するため、`server/CLAUDE.md` の作成を検討する時期
- PHASE2 完了後は PHASE3（次のマイルストーン）の策定が必要
