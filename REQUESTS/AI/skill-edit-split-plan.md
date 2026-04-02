# split_plan スキルへの改善提案

## 背景

ver14.0 の振り返りで、ROUGH_PLAN が実装詳細（`interrupt` 機構）に踏み込みすぎた結果、IMPLEMENT.md で Router パターンに設計変更が発生し、ROUGH_PLAN と IMPLEMENT.md の間に矛盾が生じた。

## 提案内容

`.claude/SKILLS/split_plan/SKILL.md` のステップ1に以下の注意書きを追加したい:

```
  - **ROUGH_PLAN の粒度に注意**: 「何をするか」（機能・スコープ・ユーザー体験の変化）を記述し、「どうやるか」（具体的なAPI・実装方式）は IMPLEMENT.md に委ねること。ROUGH_PLAN で実装方式を詳述すると、IMPLEMENT.md で設計変更が生じた際に矛盾が残る（ver14.0 での教訓: ROUGH_PLAN で `interrupt` 機構を詳述 → IMPLEMENT.md で Router パターンに変更）
```

追加場所: `実装には踏み込まず、提供される機能の全体像を説明すること` の次の行

## ユーザーへのお願い

`.claude/SKILLS/` 配下のファイルへの書き込み権限が必要です。上記の変更を承認いただけますか？
