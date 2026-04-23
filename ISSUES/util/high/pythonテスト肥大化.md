---
status: review
assigned: ai
priority: high
---
`tests\test_claude_loop.py`が肥大化していて、メンテ困難に近づいている。
適切な拡張性をもったファイル構成にする必要がある。
また、`tests`フォルダに置いている現状は、本体アプリのテストと混じって分かりづらいため、`scripts`フォルダに`tests`フォルダを新設するなどして、対応したい。