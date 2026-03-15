# Task 1: リファクタリング（事前準備）

## 概要

プロジェクトは Nuxt 4 のスキャフォールディング状態であり、実装コードはほぼ存在しない。
機能追加に入る前に、最小限のディレクトリ構造とエントリポイントの整備を行う。

## 変更一覧

### 1. `app/app.vue` の書き換え

**現状**: `<NuxtWelcome />` を表示するだけのテンプレート。

**変更**: `<NuxtPage />` によるページルーティングに切り替える。

```vue
<template>
  <div>
    <NuxtRouteAnnouncer />
    <NuxtPage />
  </div>
</template>
```

**理由**: ページコンポーネント (`app/pages/`) を使うために必要。

### 2. ディレクトリの作成

以下のディレクトリを新規作成する（Nuxt の規約に沿った配置）。

| ディレクトリ | 用途 |
|---|---|
| `app/pages/` | ページコンポーネント |
| `app/components/` | 再利用可能なUIコンポーネント |
| `server/api/` | APIルート |

**理由**: Nuxt 4 の auto-import / auto-routing に乗るための最小構成。
