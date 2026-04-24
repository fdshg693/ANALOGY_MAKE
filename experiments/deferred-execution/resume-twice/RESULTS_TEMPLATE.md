# resume-twice 実測結果テンプレート

> **記入方法**: `./run_experiment.sh --both` を実行後、生成ログ（`logs/` 配下）を参照しながら
> 各欄を埋めてください。AI による自動記入は禁止（nested CLI 観測バイアス回避）。
>
> 記入完了後、ver16.8 以降の `/issue_plan` で判定に使用します。

---

## 実測日時・環境

| 項目 | 値 |
|---|---|
| 実測日時 | YYYY-MM-DD HH:MM（JST） |
| 実行環境 | WSL / Git Bash（どちらか記載） |
| claude CLI バージョン | `claude --version` の出力 |
| OS | |
| ログファイル名 | `logs/YYYYMMDD_HHMMSS_with_bare.log` / `without_bare.log` |

---

## §U3 — 同一 session id への 2 回目 `-r` による履歴継承確認

> EXPERIMENT.md §U3「2 回目の resume が前回セッション終了後に安全か」の実測値

### with_bare（`--bare` あり）

| 観測項目 | 値 |
|---|---|
| 発話1 終了コード | |
| 発話2 終了コード | |
| 発話3 終了コード | |
| 発話3 stdout に `kiwi42` が含まれたか | Yes / No |
| session_id（3 発話で一致したか） | 一致 / 不一致（不一致なら詳細記載） |

**§U3 判定（with_bare）**: PASS / FAIL / 要追加確認

### without_bare（`--bare` なし）

| 観測項目 | 値 |
|---|---|
| 発話1 終了コード | |
| 発話2 終了コード | |
| 発話3 終了コード | |
| 発話3 stdout に `kiwi42` が含まれたか | Yes / No |
| session_id（3 発話で一致したか） | 一致 / 不一致（不一致なら詳細記載） |

**§U3 判定（without_bare）**: PASS / FAIL / 要追加確認

---

## §U2 — `--bare` 採否判定

> EXPERIMENT.md §U2「`_execute_resume()` で `--bare` を採用すべきか」の実測値

### (1) 応答成功可否

| モード | 発話1成功 | 発話2成功 | 発話3成功 | 備考 |
|---|---|---|---|---|
| with_bare | Yes / No | Yes / No | Yes / No | |
| without_bare | Yes / No | Yes / No | Yes / No | |

### (2) 実行時間（ms）

| モード | 発話1 | 発話2 | 発話3 | 合計 |
|---|---|---|---|---|
| with_bare | | | | |
| without_bare | | | | |

時間差（without - with）: \_\_\_\_ ms（正 = `--bare` なしが遅い）

### (3) Token 流入量（`--output-format json` の `.usage` から）

> ログの `発話X usage:` 行を参照。`N/A` の場合は手動で jq 抽出してください。

| モード | 発話1 input_tokens | 発話2 input_tokens | 発話3 input_tokens | 合計 |
|---|---|---|---|---|
| with_bare | | | | |
| without_bare | | | | |

Token 差（without - with）: \_\_\_\_（正 = `--bare` なしがトークン多）

### (4) CLAUDE.md 参照の痕跡（主観判定）

> `--bare` なしの応答に CLAUDE.md 由来と思われる挙動（コードブロック強制・日本語返答ルール等）が
> 見られたか。ログの発話1〜3 出力を確認してください。

| モード | CLAUDE.md 参照の痕跡 | 根拠（該当行・フレーズ） |
|---|---|---|
| with_bare | あり / なし / 不明 | |
| without_bare | あり / なし / 不明 | |

### §U2 総合判定

> 上記 (1)〜(4) を踏まえた判断。ver16.8 以降の `/issue_plan` でコード変更要否を決定する。

```
判定: --bare を採用する / 採用しない / 追加実測が必要

根拠:
(1) 応答成功可否: ...
(2) 実行時間差: ...
(3) Token 差: ...
(4) CLAUDE.md 参照痕跡: ...
```

---

## 自由記述・補足

（予期しない動作・エラー・気づき等を記載）

---

> **次のステップ**: 結果記入後、`ISSUES/util/medium/deferred-resume-twice-verification.md` の
> コメントとして要約を追記し、ver16.8 以降の `/issue_plan` で判定→コード変更または現状維持を決定します。
> 実測が ver16.8 より前に完了した場合でも、コード変更は ver16.8 以降の版で行います。
