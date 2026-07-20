import os
import re
import sys

categories_dir = "backend/app/domains/agents/prompts/categories"
all_slugs = {}
duplicates = {}

for fname in sorted(os.listdir(categories_dir)):
    if not fname.endswith('.py'):
        continue
    path = os.path.join(categories_dir, fname)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    slugs = re.findall(r'^\s+"([a-z0-9-]+)":\s*"""', content, re.MULTILINE)
    for s in slugs:
        if s in all_slugs:
            duplicates[s] = (all_slugs[s], fname)
        else:
            all_slugs[s] = fname

if duplicates:
    print("DUPLICATES FOUND:")
    for slug, (first, second) in duplicates.items():
        print(f"  {slug}: {first}  +  {second}")
    sys.exit(1)
else:
    print("No duplicates found.")
