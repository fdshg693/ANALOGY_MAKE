"""
何を確かめるためか: RESEARCH.md §U1 の仮説「session JSONL は ~/.claude/projects/<slug>/<uuid>.jsonl
  に保存され、既定で 30 日程度保持される」を、本機の実データで裏付ける。
  deferred 完了から resume までが分単位のため、retention 既定が 1 日以上あれば設計不変。

いつ削除してよいか: ver16.1 で deferred_commands.py が統合され、retrospective が閉じた時点。
  以降は同じ確認を `scripts/USAGE.md` に 1 行書いて運用に引き継ぐ。
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    home = Path.home()
    projects = home / ".claude" / "projects"
    settings = home / ".claude" / "settings.json"

    if not projects.exists():
        print(f"NOT FOUND: {projects}")
        return 1

    # 1. `--no-session-persistence` フラグ存在 = 既定は永続化
    # (claude --help から確認済、RESEARCH §A5 に記録)

    # 2. ~/.claude/settings.json に cleanupPeriodDays 指定があるか
    cleanup_days: object = None
    if settings.exists():
        try:
            cleanup_days = json.loads(settings.read_text(encoding="utf-8")).get(
                "cleanupPeriodDays"
            )
        except json.JSONDecodeError as err:
            print(f"settings.json parse error: {err}")
    print(f"settings.cleanupPeriodDays = {cleanup_days!r} (None = default applied)")

    # 3. 本機の実データで「現存する JSONL の最古 mtime」を測る
    project_dirs = [d for d in projects.iterdir() if d.is_dir()]
    print(f"project_dirs count = {len(project_dirs)}")

    all_jsonls: list[tuple[float, Path]] = []
    for d in project_dirs:
        for p in d.glob("*.jsonl"):
            try:
                all_jsonls.append((p.stat().st_mtime, p))
            except OSError:
                continue

    if not all_jsonls:
        print("no jsonl files found")
        return 1

    all_jsonls.sort()
    oldest_mtime, oldest_path = all_jsonls[0]
    newest_mtime, newest_path = all_jsonls[-1]
    now = time.time()

    def fmt_age(ts: float) -> str:
        age_days = (now - ts) / 86400.0
        return f"{age_days:.1f} days ago"

    print(f"jsonl total    = {len(all_jsonls)}")
    print(f"oldest jsonl   = {oldest_path.name} ({fmt_age(oldest_mtime)})")
    print(f"newest jsonl   = {newest_path.name} ({fmt_age(newest_mtime)})")

    # 4. 判定
    oldest_age_days = (now - oldest_mtime) / 86400.0
    verdict = "PASS" if oldest_age_days >= 1.0 else "INSUFFICIENT DATA"
    print(f"verdict        = {verdict} (deferred→resume は分単位、1 日以上なら実害なし)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
