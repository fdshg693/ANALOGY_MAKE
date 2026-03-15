# ver2 リファクタリング計画

## 概要

ver2は `experiments/` ディレクトリでの実験フェーズのため、既存コードの変更は最小限。
実験環境のセットアップに必要な構成変更のみ行う。

## 変更点

### 1. パッケージ追加

**新規依存パッケージ（dependencies）:**

| パッケージ | 用途 |
|---|---|
| `@langchain/core` | プロンプトテンプレート、メッセージ型、LCEL基盤 |
| `@langchain/openai` | ChatOpenAI（OpenAI API連携） |
| `@langchain/langgraph` | MemorySaver（会話メモリのチェックポイント管理） |
| `langchain` | createAgent、メッセージ型の再エクスポート |

**新規依存パッケージ（devDependencies）:**

| パッケージ | 用途 |
|---|---|
| `tsx` | TypeScriptスクリプトの直接実行（`npx tsx experiments/xxx.ts`） |
| `dotenv` | `.env` ファイルからの環境変数読み込み |

### 2. 環境変数ファイル

- `.env.example` を作成（APIキーのテンプレート）
- `.env` は `.gitignore` に既に含まれているため変更不要

### 3. npm scripts 追加

`package.json` に実験スクリプト実行用のショートカットを追加：

```json
{
  "scripts": {
    "exp:basic": "tsx experiments/01-basic-connection.ts",
    "exp:memory": "tsx experiments/02-memory-management.ts",
    "exp:analogy": "tsx experiments/03-analogy-prompt.ts"
  }
}
```
