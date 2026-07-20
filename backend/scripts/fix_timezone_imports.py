import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
files = list((root / "app").rglob("*.py")) + list((root / "tests").rglob("*.py"))

for f in files:
    content = f.read_text(encoding="utf-8")
    if "datetime.now(timezone.utc)" not in content:
        continue
    if re.search(r"from datetime import .*\btimezone\b", content):
        continue
    new_content = re.sub(
        r"^from datetime import datetime\s*$",
        "from datetime import datetime, timezone",
        content,
        flags=re.MULTILINE,
    )
    if new_content != content:
        f.write_text(new_content, encoding="utf-8")
        print(f"Fixed import in {f.relative_to(root)}")
    else:
        print(f"NEEDS MANUAL FIX: {f.relative_to(root)}")
