# Windows: PowerShell をシェルとして使用
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Azure App Service 操作コマンド
# 前提: az login 済み

app_name := "analogy-make"
resource_group := "rg-analogy-make"

# アプリ情報表示（URL・状態・デプロイ情報）
info:
	az webapp show --name {{app_name}} --resource-group {{resource_group}} --query "{Name:name, ResourceGroup:resourceGroup, DefaultHostName:defaultHostName, State:state, Runtime:siteConfig.linuxFxVersion, Location:location}" --output table
	Write-Host ""
	Write-Host "App URL: https://{{app_name}}.azurewebsites.net"

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
	pnpm build
	node .output/server/index.mjs

# --- インフラ管理 (Bicep) ---

# インフラのデプロイ（初回作成 / 更新、アプリ本体は配備しない）
deploy-infra:
	az deployment sub create --location japaneast --template-file infra/main.bicep --parameters infra/main.bicepparam

# アプリ本体のデプロイ（既存 App Service に ZIP 配備）
# 既にビルド済みなら `just deploy-app true` で build をスキップ可能
deploy-app skip_build="false":
	pnpm install
	if ("{{skip_build}}" -ne "true") { pnpm build } else { Write-Host "Skipping build because skip_build=true" }
	if (-not (Test-Path .output)) { throw "Build output '.output' not found. Run 'just deploy-app' or pass skip_build=true only after a successful build." }
	if (Test-Path deploy.zip) { Remove-Item deploy.zip -Force }
	Compress-Archive -Path .output\* -DestinationPath deploy.zip -Force
	az webapp deploy --resource-group {{resource_group}} --name {{app_name}} --src-path deploy.zip --type zip

# インフラの変更プレビュー（what-if）
preview-infra:
	az deployment sub what-if --location japaneast --template-file infra/main.bicep --parameters infra/main.bicepparam

# インフラの削除（Resource Group ごと）
destroy-infra:
	az group delete --name {{resource_group}} --yes

# Publish Profile の取得（GitHub Actions 用）
get-publish-profile:
	az webapp deployment list-publishing-profiles --name {{app_name}} --resource-group {{resource_group}} --xml
