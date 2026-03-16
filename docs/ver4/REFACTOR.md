# ver4 リファクタリング計画

## 概要

ストリーミング実装の前提として必要な軽微なリファクタリング。変更は1箇所のみ。

## R1: 自動スクロールのトリガー変更

### 現状

`app/pages/index.vue` の自動スクロールは `messages.value.length` の変化のみを監視している。

```typescript
watch(
  () => messages.value.length,
  async () => { ... }
)
```

### 問題

ストリーミングでは、先に空の assistant メッセージを追加し（length +1）、その後はメッセージの `content` を逐次更新する。
length は変わらないため、ストリーミング中にスクロールが追従しない。

### 変更

`messages.value.length` の監視を、最後のメッセージの `content` も含む監視に変更する。

```typescript
watch(
  () => {
    const len = messages.value.length
    const last = messages.value[len - 1]
    return `${len}:${last?.content.length ?? 0}`
  },
  async () => { ... }
)
```

これにより、メッセージ追加時とストリーミング中のコンテンツ更新時の両方でスクロールが発火する。
