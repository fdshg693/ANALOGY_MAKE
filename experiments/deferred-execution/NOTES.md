# experiments/deferred-execution/

ver16.1 PHASE8.0 §2 の deferred execution 方式比較。IMPLEMENT.md §0 / §5 の未解決論点を
`docs/util/ver16.1/RESEARCH.md` の調査結果と突き合わせて、ここで実測する。

## variant / hypothesis 対応表

| directory | 対応仮説 (RESEARCH §未解決点) | 扱い |
|---|---|---|
| `retention-check/` | §U1 session JSONL retention | 実測済 (本版) |
| `large-stdout/` | §U4 巨大 stdout の excerpt 行数 | 実測済 (本版) |
| `orphan-recovery/` | §U5 `.started` marker による orphan 検知 | 実測済 (本版) |
| `resume-twice/` | §U2 `--bare` 採用判定 / §U3 同一 session 2 回 resume | **未検証** (nested claude 起動が `RESEARCH §5-5` で禁止。deferred execution 機構が実装された ver16.2 以降の外部経路で検証) |

## 有望な方式

- **request file = frontmatter + body markdown、result = meta.json + sidecar stdout/stderr log**（§0-2 確定、Q7 結論）
- **`data/deferred/` に隔離**（§0-5 推奨、Q9）
- **`subprocess.run(..., stdout=open(...,"wb"), stderr=open(...,"wb"), check=False)`**（D1/D2/D3 に準拠、deadlock 回避 + 明示的 exit code 記録）
- **`head 20 + tail 20 + sizes` excerpt 案 (C 案)**（large-stdout 実験で確定）
- **`.started` marker file による orphan 検知**（orphan-recovery 実験で成立）

## 避けるべき方式

- **`stdout=subprocess.PIPE`**（D2: PIPE buffer deadlock）
- **head 200 + tail 200 excerpt (B 案)**（10MB stdout で resume prompt が数 KB に肥大、token cost が予測不能）
- **`DEFERRED/` repo ルート直下**（`.gitignore` 追加が必要 + root 肥大、Q9 評価で△）
- **新 claude session ID を都度発行して履歴を prompt に貼り直す**（Q1 の確定結果により不要、A2/A3 の公式 pattern から外れる）

## 削除条件

本ディレクトリ全体の削除条件:
- **§2-3 完了条件 5 項目を満たす方式が `scripts/claude_loop_lib/deferred_commands.py` に統合され、ver16.1 の wrap_up で retrospective まで閉じた時点**

`resume-twice/` は ver16.2 以降で実検証される想定のため、それまで保持。
