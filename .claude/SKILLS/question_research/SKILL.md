---
name: question_research
description: QUESTIONS/ から 1 件選び調査専用で報告書を出力する opt-in workflow（--workflow question で起動）
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 今日の日付: !`date +%Y-%m-%d`
- AI 向け ready Question: !`python scripts/question_worklist.py --category $(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app) --format json`

## 役割

調査専用 SKILL。`QUESTIONS/{カテゴリ}/{priority}/` から `ready / ai` の Question を 1 件選び、コードベース・ドキュメント・既存 ISSUE を読み解いて結論をまとめ、`docs/{カテゴリ}/questions/{slug}.md` に報告書を出力する。

**やらないこと**:

- コード修正・テスト修正・実装・デプロイ
- `docs/{カテゴリ}/ver*/` バージョンディレクトリの作成・更新
- `QUESTIONS/` 以外のファイルの再配置
- `.claude/` 配下の編集
- 既存 ISSUE の status 変更（新規 ISSUE 起票は許可、後述）

## 調査手順（3 段階）

### 1. Question 1 件選定

`python scripts/question_worklist.py --category $(cat .claude/CURRENT_CATEGORY) --format json` の結果から **最上位優先度（high → medium → low）の `ready / ai`** を 1 件選ぶ。`ready / ai` が 0 件なら **そのまま終了**（報告書も起票もしない）。

### 2. 証拠収集

選定 Question の本文を Read し、関連ファイル・docs・既存 ISSUE / RETROSPECTIVE / MEMO を探索して根拠を集める。

- 関連コード（grep / Read）
- 直近メジャーバージョンの `CURRENT.md` / `MASTER_PLAN.md`
- 関連する `ISSUES/` 配下（done/ 含む）
- 必要に応じてサブエージェントを並列で起動（コンテキスト肥大化防止）

証拠は **ファイルパス + 行番号** の形で記録する（曖昧な「どこかにある」表現は避ける）。

### 3. 結論・不確実性整理

集めた証拠から以下を整理する:

- **結論** — 問いに対する答え（断定 / 部分的 / 未確定 のどれか）
- **不確実性** — 結論を弱める要因 / 検証できなかった点
- **次アクション候補** — 実装に進むなら新規 ISSUE 起票、人間判断が必要なら Question を `need_human_action` に戻す等

## 報告書の出力

出力先: `docs/{カテゴリ}/questions/{slug}.md`（`{slug}` は Question ファイル名の拡張子なし部分と一致させる）

ディレクトリが存在しない場合は作成する（`mkdir -p`）。

報告書は次の固定 5 セクションで構成する:

```markdown
# {Question タイトル}

調査日: YYYY-MM-DD
対象 Question: QUESTIONS/{カテゴリ}/{priority}/{slug}.md

## 問い

（Question 本文の要約。原文を逸脱しないこと）

## 確認した証拠

- ファイル `xxx.py:NN-MM` で〜という実装
- ドキュメント `docs/.../yyy.md` の §X に〜と記載
- 過去 ISSUE `ISSUES/.../zzz.md`（done/）で〜と判断

## 結論

（断定 / 部分的 / 未確定 を明示。1〜3 段落程度）

## 不確実性

- 検証できなかった範囲 / 仮定置きした前提 / 反証可能性
- 「未確定」結論の場合は **理由を必ず詳述**

## 次アクション候補

- 実装に進める場合 → 新規 ISSUE `ISSUES/{cat}/{priority}/xxx.md` を起票（本セクションにパス記載）
- 人間判断が必要 → Question を `need_human_action / human` に戻し、本文末尾に確認事項を追記
- 追加調査が必要 → 必要なツール / 権限 / 情報を列挙
```

## 後処理ルール

調査結果に応じて以下のいずれかを実施する:

1. **結論確定 + 実装課題が明確化** — 新規 ISSUE を `ISSUES/{カテゴリ}/{priority}/` に起票（`raw / ai` または `ready / ai`、`issue_scout` の昇格条件を準用）。Question 本文末尾に新規 ISSUE へのリンクを追記。Question を `QUESTIONS/{カテゴリ}/done/` へ移動
2. **結論確定 + 実装不要** — Question 本文末尾に報告書へのリンクを追記。Question を `QUESTIONS/{カテゴリ}/done/` へ移動
3. **結論未確定 + 人間の追加情報が必要** — 報告書の「結論」を「未確定」、「不確実性」に理由を詳述。Question を `need_human_action / human` に書き換え、本文末尾に「追加調査に必要な情報 / ツール / 権限」を列挙。**`done/` 移動は行わない**（結論確定まで queue に残す）

## やらないこと（再掲）

- コード修正 / テスト修正 / デプロイ
- `QUESTIONS/` 以外のファイルの再配置（既存 ISSUE の移動含む）
- `docs/{cat}/ver*/` バージョンフォルダ作成・既存 `CURRENT.md` / `RETROSPECTIVE.md` 更新
- `.claude/` 配下の編集

## Git コミット

報告書 + Question の `done/` 移動（または `need_human_action` 書き換え）+ 新規 ISSUE 起票を **1 コミット** にまとめる:

```
git add docs/{cat}/questions/ QUESTIONS/{cat}/ ISSUES/{cat}/
git commit -m "docs(ver{X.Y}): question_research による調査 ({slug})"
```

**プッシュはしない**（後続 flow が push 責任を持つ）。
