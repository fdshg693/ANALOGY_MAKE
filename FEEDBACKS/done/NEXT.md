`feedback-abnormal-exit-integration-test.md` 消化して

注意点:
1. **スコープ**: ISSUE 本文の「対応方針 1〜3」に従い、step 失敗時に FEEDBACK が `FEEDBACKS/` 直下に残ることを検証する integration テストを追加。プロダクションコードには手を入れない
2. **変更対象想定**: `scripts/tests/test_claude_loop_integration.py` に新規テストクラス追加 + 必要なら軽量テスト YAML fixture 1 本。2 ファイル / 50 行前後で完結見込み
3. **quick 適合性**: ver12.0 RETROSPECTIVE §2-2-b で既に指摘された cwd 依存を避けるため、既存 `TestRunMainAuto` 等のテンポラリ cwd パターンを流用。subprocess 起動 + `sh -c "exit 1"` 相当の擬似 step で再現する想定
4. **ver13.0 実装との相互作用**: ver13.0 で `--append-system-prompt` が常時注入される仕様に変わったため、テスト内の assertion は「unattended prompt が含まれる」前提で書く。`build_command()` の挙動変更（MEMO §「計画からの乖離」参照）を取り込み済
5. **raw → ready 昇格**: ver13.1 の `/issue_plan` 冒頭で `status: raw → ready` / `reviewed_at` 更新を行うこと