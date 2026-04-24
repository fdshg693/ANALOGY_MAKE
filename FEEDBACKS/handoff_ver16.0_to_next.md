---
step: issue_plan
---

## 背景

ver16.0 で PHASE8.0 §1（`research` workflow 新設）を完走。8 step 構成・2 新 SKILL・新 YAML を実装し、テスト 276→280 全 green。`RESEARCH.md` / `EXPERIMENT.md` artifact と `--workflow research` auto 選定条件（4 条件いずれか 1 つ）が定義済。

## 次ループで試すこと

- **PHASE8.0 §2（deferred execution）に着手し、ver16.1 メジャー扱いで進める**。`scripts/claude_loop_lib/deferred_commands.py` 新規・`claude_loop.py` の実行ライフサイクル変更を伴うため `quick` 条件を超える
- **§2 の workflow は ver16.0 で新設した `research` を自己適用する候補**。PHASE8.0 §2 本文で「事前調査・試行を挟む価値が高い」と明言されている。`auto` 選定条件のうち「実装方式を実験で絞り込む必要がある」「軽い隔離環境（`experiments/` 配下）での試行が前提」の 2 条件に明確に該当する
- **`/write_current` の effort を medium → high で試す**（model は sonnet 維持）。PHASE8.0 §2 以降で `CURRENT.md` の複雑度が上がる見込みのため

## 保留事項

- `ready/ai` プール 2 件（`issue-review-rewrite-verification.md` / `toast-persistence-verification.md`）は util 単独消化不能の構造的カリオーバー。ver16.1 でも据え置き判断で問題ない。ただし 4 バージョン連続持ち越しになるため、ver16.2 以降で「`status: need_human_action` に振り直して queue を一度クリアする」選択肢を検討
- raw/ai 2 件（`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）は triage 未実施。ver16.1 着手前にユーザー triage を促すか、そのまま据え置くかは次 `/issue_plan` で判断
- YAML sync 契約が 6 ファイルに拡大した件は ver16.0 スコープ外として未対応。§2 で YAML が更に増えたら生成元 1 箇所化 or 起動時 validation 強化を検討
