#!/usr/bin/env python3
"""Lint the agent knowledge base. Stdlib only.

Checks: per-file line caps, broken relative links, and the shape of docs/STATE.md.
Exit code 1 if anything fails, so it can run as a pre-commit hook.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIMITS = {"CONTINUE.md": 60, "docs/STATE.md": 40, "docs/wiki/gotchas.md": 60}  # per-file caps (lines)
DEFAULT_LIMIT = 150  # every other docs/**/*.md
STATE_HEADINGS = ["## Current milestone", "## Done", "## Next", "## Open questions"]

FENCE = re.compile(r"```.*?```", re.S)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
DATE = re.compile(r"^Last updated: \d{4}-\d{2}-\d{2}$", re.M)


def kb_files() -> list[Path]:
    files = sorted((ROOT / "docs").rglob("*.md"))
    top = ROOT / "CONTINUE.md"
    if top.exists():
        files.insert(0, top)
    return files


def check_file(path: Path) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    errors = []

    limit = LIMITS.get(rel, DEFAULT_LIMIT)
    n = len(text.splitlines())
    if n > limit:
        errors.append(f"{rel}: {n} lines, cap is {limit}. Split or prune it.")

    for target in LINK.findall(FENCE.sub("", text)):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        dest = (path.parent / target.split("#")[0]).resolve()
        if not dest.exists():
            errors.append(f"{rel}: broken link -> {target}")
    return errors


def check_state() -> list[str]:
    state = ROOT / "docs" / "STATE.md"
    if not state.exists():
        return ["docs/STATE.md is missing"]
    text = state.read_text(encoding="utf-8")
    errors = [f"docs/STATE.md: missing heading '{h}'" for h in STATE_HEADINGS if h not in text]
    if not DATE.search(text):
        errors.append("docs/STATE.md: needs a line 'Last updated: YYYY-MM-DD'")
    return errors


def main() -> int:
    errors = check_state()
    for f in kb_files():
        errors += check_file(f)
    for e in errors:
        print(e, file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} knowledge-base problem(s).", file=sys.stderr)
        return 1
    print("knowledge base OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
