# .output/ ディレクトリ構造の Azure App Service 互換性検証

## 概要

Nuxt ビルド成果物（`.output/`）が Azure App Service のデプロイ方式と合致するか、実デプロイ時に検証する。

## 背景

- 現在の deploy.yml は `.output/` をそのまま Azure にデプロイする想定
- Azure App Service の期待するディレクトリ構造と合致しない場合、zip デプロイへの切り替えが必要
- 実際にデプロイを試行しないと判断できないため、ver1.0 wrap_up では対応不可

## 対応方針

1. 初回デプロイ時に動作確認
2. 問題があれば zip デプロイ方式に切り替え（deploy.yml の修正）
3. 必要に応じて `web.config` や `startup-file` の調整
