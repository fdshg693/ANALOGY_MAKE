"""
何を確かめるためか: RESEARCH.md §U4 の 3 案比較。10MB 相当の fixture stdout に対して、
  A案 (head 50 + tail 50) / B案 (head 200 + tail 200) / C案 (head 20 + tail 20 + sizes のみ)
  の 3 方式で resume prompt を組み立て、prompt 長と「成功/失敗の判別に必要な情報が
  残っているか」を実測する。

いつ削除してよいか: deferred_commands.py::build_resume_prompt の excerpt 行数が確定し、
  unit test が書かれた時点。IMPLEMENT.md §2-3 / §2-4 の暫定仕様確定後に削除可。
"""

from __future__ import annotations

from pathlib import Path


def generate_fixture(path: Path, target_bytes: int = 10 * 1024 * 1024) -> int:
    """
    典型的な長時間 task 出力を模したテキストを生成:
      - 大半は進捗ログ (均一な行)
      - 末尾近くに失敗マーカーや warning が現れる
    """
    lines: list[str] = []
    size = 0
    i = 0
    while size < target_bytes - 2048:
        line = f"[{i:08d}] INFO processing record batch step={i // 1000}\n"
        lines.append(line)
        size += len(line)
        i += 1
    # 末尾に「後段で判断材料になる情報」を置く
    lines.append(
        "[99999998] WARNING last chunk had 3 records below threshold\n"
    )
    lines.append("[99999999] ERROR finalize: non-zero checksum, aborting\n")
    lines.append("exit status: 1\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path.stat().st_size


def build_excerpt(text: str, *, head_n: int, tail_n: int) -> str:
    lines = text.splitlines()
    if len(lines) <= head_n + tail_n:
        return text
    head = "\n".join(lines[:head_n])
    tail = "\n".join(lines[-tail_n:])
    return f"{head}\n... ({len(lines) - head_n - tail_n} lines omitted) ...\n{tail}"


def build_resume_prompt(
    stdout_bytes: int,
    excerpt: str | None,
    *,
    case_label: str,
) -> str:
    parts = [
        "DEFERRED EXECUTION COMPLETED:",
        "- request: DEFERRED/done/<request_id>.md",
        "- result meta: DEFERRED/results/<request_id>.meta.json",
        "- overall_exit_code: 1",
        f"- stdout_bytes: {stdout_bytes}, stderr_bytes: 0",
    ]
    if excerpt is not None:
        parts.append("")
        parts.append("## stdout excerpt")
        parts.append(excerpt)
    parts.append("")
    parts.append(
        "必要に応じて meta と stdout/stderr path を Read して判断してください。"
    )
    parts.append(f"(case: {case_label})")
    return "\n".join(parts)


def contains_failure_signal(prompt: str) -> bool:
    return "ERROR" in prompt or "exit status: 1" in prompt or "aborting" in prompt


def main() -> int:
    here = Path(__file__).resolve().parent
    fixture = here / "fixture_stdout.log"
    size_bytes = generate_fixture(fixture)
    text = fixture.read_text(encoding="utf-8")
    total_lines = text.count("\n")
    print(f"fixture size   = {size_bytes:,} bytes ({size_bytes / 1024 / 1024:.2f} MB)")
    print(f"fixture lines  = {total_lines:,}")
    print()

    # 3 案比較
    cases = [
        ("A (head 50 + tail 50)", 50, 50),
        ("B (head 200 + tail 200)", 200, 200),
        ("C (head 20 + tail 20)", 20, 20),
    ]
    # 参考: excerpt なし案 (sizes のみ)
    prompt_sizes_only = build_resume_prompt(size_bytes, None, case_label="sizes only")
    print(
        f"{'sizes only':<28}"
        f"prompt={len(prompt_sizes_only):>6}B  "
        f"failure_signal={contains_failure_signal(prompt_sizes_only)}"
    )

    for label, head_n, tail_n in cases:
        excerpt = build_excerpt(text, head_n=head_n, tail_n=tail_n)
        prompt = build_resume_prompt(size_bytes, excerpt, case_label=label)
        ok = contains_failure_signal(prompt)
        print(
            f"{label:<28}"
            f"prompt={len(prompt):>6}B  "
            f"excerpt={len(excerpt):>6}B  "
            f"failure_signal={ok}"
        )

    # 判定補助: prompt 長 2KB 以下が望ましい (既存 step の追加 prompt と同規模)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
