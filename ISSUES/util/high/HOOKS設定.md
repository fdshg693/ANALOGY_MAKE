# Hooks 設定

`.claude\settings.local.json` の `hooks` セクションで、Hooksの設定を行います。

##　問題
現状、PermissionRequestを全許可している。
本来は、スクリプト自動化モードで、Editを利用して`.claude`配下のファイルなどを編集する際に許可する意図があった。

現状、手動実行などのときに、askUserQuestionをAIが使う場合もすぐ許可して、回答ができない
-> askUserQuestionは除外するようにしたい

手動Claude実行の際は、`.claude`配下のファイルへの書き込みは意図通り成功するが、スクリプト自動化モードの時は失敗しているよう。

また、Hooks内のコマンドは別ファイルのスクリプトを呼び出すような形にすることで、Hooksをシンプルに保ち、管理しやすくしたい。

## 参考文献
https://code.claude.com/docs/en/hooks-guide#hook-input

## ステータス
実装完了（ver1.0）。`_staged_hooks/` にファイルをステージング済み。ユーザーによる `bash _staged_hooks/install.sh` の実行待ち。詳細は `REQUESTS/AI/hooks_install_request.md` を参照。