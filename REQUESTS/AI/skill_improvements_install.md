# スキル改善のインストール依頼

## 背景

ver1.0 の retrospective で `imple_plan/SKILL.md` に2つの改善を特定しました。
`.claude/` 保護ディレクトリ制限により AI から直接編集できないため、ステージング方式で準備しています。

## 変更内容

### `.claude/skills/imple_plan/SKILL.md`
1. **カテゴリ対応の動作確認**: `npx nuxi typecheck` / `pnpm test` を app カテゴリ限定に変更。util/infra/cicd カテゴリ向けに構文チェック・バリデーション・ドライランの確認手順を追加
2. **`.claude/` 保護制限の注意事項追加**: 保護ディレクトリへの書き込み制限と、ステージング方式の推奨を実装品質ガイドラインに追加

## インストール方法

```bash
bash _staged_skills/install.sh
```

## インストール後

```bash
rm -rf _staged_skills/
```
