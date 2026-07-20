#!/usr/bin/env python3
"""
Auto-fix script for common Python deprecations in the SellIA backend.

Fixes applied:
  1. datetime.utcnow()  -> datetime.now(timezone.utc)
  2. class Config:       -> model_config = ConfigDict(...)

Usage:
    python scripts/fix_deprecations.py [--check]
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
TESTS_DIR = PROJECT_ROOT / "tests"

UTCNOW_RE = re.compile(r"datetime\.utcnow\(\)")
CLASS_CONFIG_RE = re.compile(
    r"^(\s+)class Config:\s*$"
    r"(?P<body>(?:\n(?:\1\s+.+|\s*))+)",
    re.MULTILINE,
)


def fix_utcnow(content: str) -> str:
    """Replace datetime.utcnow() with timezone-aware equivalent."""
    # Ensure we have 'timezone' imported from datetime
    if UTCNOW_RE.search(content):
        if "from datetime import" in content and "timezone" not in content:
            # naive attempt to add timezone to existing datetime import
            content = re.sub(
                r"(from datetime import .*)(\))",
                lambda m: f"{m.group(1)}, timezone{'' if 'datetime' in m.group(1) else ''})",
                content,
            )
        elif "import datetime" in content and "from datetime import timezone" not in content:
            content = content.replace(
                "import datetime",
                "import datetime\nfrom datetime import timezone",
            )
        content = UTCNOW_RE.sub("datetime.now(timezone.utc)", content)
    return content


def fix_pydantic_config(content: str) -> str:
    """Replace class Config: with model_config = ConfigDict(...)."""
    if "class Config:" not in content:
        return content

    # Ensure ConfigDict is imported
    if "ConfigDict" not in content:
        if "from pydantic import" in content:
            content = re.sub(
                r"(from pydantic import .*)(\n)",
                lambda m: f"{m.group(1).rstrip()}, ConfigDict\n",
                content,
            )
        else:
            content = "from pydantic import ConfigDict\n" + content

    def replacer(match):
        indent = match.group(1)
        body = match.group("body")
        lines = [ln.rstrip() for ln in body.splitlines() if ln.strip()]
        if not lines:
            return f'{indent}model_config = ConfigDict()'

        # Parse simple key = value assignments
        items = []
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith("#"):
                continue
            if "=" in line_stripped:
                items.append(line_stripped)
        inner = ", ".join(items)
        return f"{indent}model_config = ConfigDict({inner})"

    content = CLASS_CONFIG_RE.sub(replacer, content)
    return content


def process_file(path: Path, check: bool = False) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = fix_utcnow(original)
    updated = fix_pydantic_config(updated)

    if original == updated:
        return False

    if check:
        print(f"Would modify: {path.relative_to(PROJECT_ROOT)}")
        return True

    path.write_text(updated, encoding="utf-8")
    print(f"Fixed: {path.relative_to(PROJECT_ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-fix deprecations in SellIA backend")
    parser.add_argument("--check", action="store_true", help="Dry-run, only list files that would change")
    args = parser.parse_args()

    changed = 0
    for directory in (APP_DIR, TESTS_DIR):
        for path in directory.rglob("*.py"):
            if path.name.startswith("."):
                continue
            if process_file(path, check=args.check):
                changed += 1

    print(f"\n{'Would change' if args.check else 'Changed'} {changed} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
