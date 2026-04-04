# MEMO: util ver3.1

## 実装メモ

- ROUGH_PLAN.md 通りに `" ".join(command)` → `shlex.join(command)` へ変更（489行目）
- `shlex` は既にインポート済みだったため、追加のインポートは不要
- テストファイル内の `" ".join` はトースト通知テスト（`test_toast_escapes_single_quotes`）のもので、今回の修正対象外。変更不要

## 残課題

なし
