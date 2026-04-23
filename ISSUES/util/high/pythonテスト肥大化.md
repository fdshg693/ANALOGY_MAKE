---
status: ready
assigned: ai
priority: high
reviewed_at: "2026-04-23"
---
`tests\test_claude_loop.py`が肥大化していて、メンテ困難に近づいている。
適切な拡張性をもったファイル構成にする必要がある。
また、`tests`フォルダに置いている現状は、本体アプリのテストと混じって分かりづらいため、`scripts`フォルダに`tests`フォルダを新設するなどして、対応したい。