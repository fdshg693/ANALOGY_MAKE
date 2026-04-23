---
status: ready
assigned: ai
priority: medium
reviewed_at: "2026-04-23"
---
`scripts`に以下の改善を行いたい

- ワークフロー関連のコードと、そのほかのコード（現状だとscripts\claude_sync.pyのみ）を適切に分離する
- `scripts\README.md`が肥大化してきているため、使い方を専門に解説したファイルを切り出す
    - CLIの引数の渡し方、YAMLファイルの設定の仕方
- そのほかの内容として、ログの見方、注意点などをREADMEに残す、あるいは追記する
    - READMEは人間用ファイルであり、現状のコード内容・実装にあたっての注意点などClaude Code向けの内容は`docs\util`フォルダにて書かれているため、不要