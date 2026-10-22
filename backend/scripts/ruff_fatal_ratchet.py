"""Ratchet for the ruff rules that flag code which crashes at runtime.

`ruff check app/` reports ~24k style findings that nobody can gate on, but a small
subset is different in kind: names that are used and never defined (F821/F822/F823),
invalid comparisons, misplaced statements and syntax errors. Each one is a
NameError/SyntaxError waiting for the line to run, and they are exactly the bugs that
slip through here because `_try_include` in app/main.py swallows an import-time
NameError and silently drops the whole router (production returns 404 for
/api/v1/automations/* because of one).

The existing findings are recorded in `.ruff-fatal-baseline.json`. CI fails only when a
finding appears that the baseline does not allow, so the count can go down but never
up. The key is (file, rule, offending name) -- no line numbers, so moving code around
does not trip it.

    python scripts/ruff_fatal_ratchet.py            # CI: compare against the baseline
    python scripts/ruff_fatal_ratchet.py --update   # rewrite the baseline (after fixing)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

BACKEND = Path(__file__).resolve().parent.parent
BASELINE = BACKEND / ".ruff-fatal-baseline.json"

# E9 syntax/IO errors, F63 invalid comparisons, F7 misplaced statements, F82 undefined
# names, PLE0704 bare `raise` outside an except block.
RULES = "E9,F63,F7,F82,PLE0704"

Key = tuple[str, str, str]


def _key(finding: dict) -> Key:
    path = finding["filename"].replace("\\", "/")
    rel = path.split("/app/", 1)[-1] if "/app/" in path else path
    quoted = re.search(r"`([^`]+)`", finding["message"])
    return (rel, finding["code"], quoted.group(1) if quoted else finding["message"])


def count(findings: Iterable[dict]) -> Counter[Key]:
    return Counter(_key(f) for f in findings)


def compare(current: Counter[Key], baseline: Counter[Key]) -> tuple[list[Key], list[Key]]:
    """(keys that exceed the baseline, keys that improved on it)."""
    worse = [k for k, n in current.items() if n > baseline.get(k, 0)]
    better = [k for k, n in baseline.items() if current.get(k, 0) < n]
    return sorted(worse), sorted(better)


def run_ruff() -> list[dict]:
    proc = subprocess.run(
        ["ruff", "check", "app", "--isolated", "--select", RULES, "--output-format", "json"],
        cwd=BACKEND, capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode not in (0, 1):  # 1 = findings; anything else = ruff itself broke
        sys.exit(f"ruff failed to run (exit {proc.returncode}):\n{proc.stderr[:800]}")
    return json.loads(proc.stdout or "[]")


def load_baseline() -> Counter[Key]:
    if not BASELINE.exists():
        return Counter()
    rows = json.loads(BASELINE.read_text(encoding="utf-8"))
    return Counter({(r["file"], r["rule"], r["name"]): r["count"] for r in rows})


def write_baseline(current: Counter[Key]) -> None:
    rows = [{"file": f, "rule": c, "name": n, "count": k} for (f, c, n), k in sorted(current.items())]
    BASELINE.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--update", action="store_true", help="rewrite the baseline from the current tree")
    args = parser.parse_args()

    findings = run_ruff()
    current = count(findings)

    if args.update:
        write_baseline(current)
        print(f"baseline written: {sum(current.values())} findings in {len({k[0] for k in current})} files")
        return 0

    worse, better = compare(current, load_baseline())
    if worse:
        print(f"{len(worse)} new runtime-error finding(s) not allowed by the baseline:\n")
        for file, code, name in worse:
            for f in findings:
                if _key(f) == (file, code, name):
                    line = f["location"]["row"]
                    print(f"::error file=backend/app/{file},line={line},title=ruff {code}::{f['message']}")
        print(
            "\nThese are names that are used but never defined (or similar): the line raises "
            "NameError when it runs, and if it is at import time the whole router is silently "
            "dropped. Define/import the name; do not add it to the baseline."
        )
        return 1

    if better:
        print(f"OK, and {len(better)} baselined finding(s) were fixed: run "
              "`python scripts/ruff_fatal_ratchet.py --update` to lock the improvement in.")
    else:
        print(f"OK: {sum(current.values())} known findings, none new.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
