"""
何を確かめるためか: RESEARCH.md §U5 の仮説「`DEFERRED/<id>.started` marker を
  execute 直前に作り、正常終了で削除、異常終了で残す方式なら、次回起動時に
  marker 残存を検知できる」を、SIGKILL 相当 (os._exit) でも marker が
  残ることを含めて実測する。

  シナリオ:
    1. execute_with_marker(A) を try/finally + 正常終了 → marker 削除 → 残らない
    2. execute_with_marker(B) を途中で os._exit(137) (= SIGKILL 相当) →
       marker 残る
    3. scan_orphans() が B の marker のみを検知する

いつ削除してよいか: ver16.1 で deferred_commands.py に orphan 検知が統合され、
  test_deferred_commands.py::test_orphan_detection が pass した時点。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = r"""
import os, sys
from pathlib import Path

deferred = Path(sys.argv[1])
req_id = sys.argv[2]
mode = sys.argv[3]  # "clean" | "kill"

marker = deferred / f"{req_id}.started"
marker.write_text("running\n", encoding="utf-8")

if mode == "kill":
    os._exit(137)  # mimic SIGKILL: no finally, no atexit

try:
    (deferred / f"{req_id}.result").write_text("ok\n", encoding="utf-8")
finally:
    marker.unlink(missing_ok=True)
"""


def scan_orphans(deferred_dir: Path) -> list[Path]:
    return sorted(deferred_dir.glob("*.started"))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        deferred = Path(tmp) / "deferred"
        deferred.mkdir()
        helper_path = deferred / "_helper.py"
        helper_path.write_text(HELPER, encoding="utf-8")

        # 1. 正常経路
        rc_a = subprocess.run(
            [sys.executable, str(helper_path), str(deferred), "req-A", "clean"],
            check=False,
        ).returncode
        # 2. SIGKILL 相当
        rc_b = subprocess.run(
            [sys.executable, str(helper_path), str(deferred), "req-B", "kill"],
            check=False,
        ).returncode

        print(f"clean exit code = {rc_a}  (expected 0)")
        print(f"kill  exit code = {rc_b}  (expected 137 on posix / 137 on Windows via os._exit)")

        orphans = scan_orphans(deferred)
        print(f"orphan markers  = {[p.name for p in orphans]}")

        all_files = sorted(p.name for p in deferred.iterdir() if p.is_file())
        print(f"deferred_dir    = {all_files}")

        ok = (
            rc_a == 0
            and rc_b != 0
            and [p.name for p in orphans] == ["req-B.started"]
            and "req-A.result" in all_files
            and "req-A.started" not in all_files
        )
        print(f"verdict         = {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
