---
status: ready
assigned: ai
priority: low
reviewed_at: 2026-04-24
---

# Windows toast 永続表示挙動の実機目視検証

## 概要

ver15.4 で `scripts/claude_loop_lib/notify.py::_notify_toast` を `scenario='reminder' duration='long'` + dismiss アクション構成の XML に移行した。狙いは Windows Action Center に「人が閉じるまで残る」こと。コード側では `reminder` が拒否された場合に `duration='long'` 単独へフォールバック、それも失敗したら beep + console 出力へ降格する 3 段構造を入れてある。

実機での目視検証（30 秒・5 分・10 分後の Action Center 残留）は ver15.4 の `/imple_plan` がヘッドレスだったため未実施。OS 実環境での挙動確認が follow-up として残っている。

## 本番発生時の兆候

- `notify_completion` 呼び出し後、Action Center に何も追加されない
- コンソールに beep fallback 装飾（`========` の枠線）も出ない
- → reminder XML も long XML も OS には「成功」扱いだが実際は silently 無表示のケースが疑われる

別パターン:
- reminder XML が OS に拒否される（XML パースエラー / スキーマ違反）ビルドに遭遇すると、毎回 2 回 PowerShell を起動する無駄が生じる。そのビルドでは `duration='long'` のみを直接使う分岐が望ましい

## 対応方針

1. 開発者の Windows 11 実機で `notify_completion` を手動トリガし、Action Center での残留時間を目視確認
2. reminder 構成が動作しない場合は `_build_toast_xml(persistent=True)` の XML 構造を実環境で通る形に調整
3. 動作したが残留時間が短すぎる場合は、`<actions>` に dismiss 以外のアクションも追加して優先度を上げる運用を検討
4. Windows バージョン毎の差異が大きい場合は `platform.win32_ver()` で分岐する

## 影響範囲

- `scripts/claude_loop_lib/notify.py::_notify_toast` の実装
- 複数ループ実行の完了把握体験（本 ISSUE が未解決でも beep fallback で最低限の通知は成立）
- PHASE7.1 §4 の完了条件「Windows Action Center で通知が auto-dismiss されにくい挙動が PoC で確認できる」

## 関連

- `docs/util/ver15.4/IMPLEMENT.md` §リスク・不確実性 R1
- `docs/util/ver15.4/MEMO.md` § R1 の検証先送り記録
- `scripts/claude_loop_lib/notify.py::_build_toast_xml`
