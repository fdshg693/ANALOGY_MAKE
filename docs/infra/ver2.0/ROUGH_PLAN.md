# ver2.0 タスク概要: Bicep による Azure インフラの IaC 管理

## 対応方針

MASTER_PLAN の PHASE1.5 に着手する。ISSUES 対応ではない。
（`ISSUES/infra/high/` が空のため、MASTER_PLAN の次項目を進める）

## 背景

ver1.0 で Azure App Service へのデプロイに必要なコード変更（CI/CD ワークフロー、DB パス管理、Justfile、Nitro preset）は完了した。しかし、Azure リソース自体の作成は手動操作（`az` CLI コマンド）に依存しており、構成の再現性がない。

PHASE1.5 では、Azure リソースを Bicep テンプレートで宣言的に管理し、`just deploy-infra` 一発でインフラを構築できるようにする。

## 提供する機能

### Bicep テンプレートによるインフラ定義

Azure リソース（Resource Group、App Service Plan、Web App）を Bicep ファイルで宣言的に定義する。環境変数（API キー等）もテンプレート内で管理し、デプロイ時にプロンプトで安全に入力する。

### Justfile によるインフラ操作コマンド

以下の操作を Justfile コマンドとして提供する:
- インフラのデプロイ（作成・更新）
- 変更のプレビュー（what-if）
- インフラの削除
- Publish Profile の取得

### 初回セットアップの簡素化

`az login` → `just deploy-infra` → `just get-publish-profile` → GitHub Secrets 登録 → push、という明確な手順でゼロからデプロイ可能な状態にする。

## スコープ

### 含むもの

- `infra/` ディレクトリに Bicep テンプレートを作成（main.bicep、パラメータファイル、モジュール分割）
- Justfile にインフラ管理コマンドを追加（deploy-infra, preview-infra, destroy-infra, get-publish-profile）

### 含まないもの

- Key Vault によるシークレット管理
- 複数環境（staging / production）の管理
- 監視・アラート・バックアップの設定
- GitHub Actions でのインフラ CI/CD（手動実行のみ）
- ISSUES/infra/ の既存課題への対応（ver1.1 以降で対応）

## 事前リファクタリング

不要。変更は新規ファイル作成（infra/ ディレクトリ）と既存 Justfile への追記のみで、既存コードの構造変更を伴わない。

## ISSUES との関係

- `ISSUES/infra/low/azure-resource-docs.md` — Bicep テンプレートがリソース作成手順の代替となるため、この ISSUE は本バージョン完了後にクローズ可能
- `ISSUES/infra/medium/verify-output-dir-azure.md` — 本バージョンのスコープ外。初回デプロイ後に検証
