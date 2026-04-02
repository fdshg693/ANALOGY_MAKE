# Azure App Service 操作コマンド
# 前提: az login 済み

app_name := "analogy-make"
resource_group := "rg-analogy-make"

# ログ確認（リアルタイム）
logs:
	az webapp log tail --name {{app_name}} --resource-group {{resource_group}}

# 再起動
restart:
	az webapp restart --name {{app_name}} --resource-group {{resource_group}}

# 環境変数一覧
env-list:
	az webapp config appsettings list --name {{app_name}} --resource-group {{resource_group}} --output table

# SSH接続
ssh:
	az webapp ssh --name {{app_name}} --resource-group {{resource_group}}

# ローカルビルド + プレビュー
preview:
	pnpm build && node .output/server/index.mjs
