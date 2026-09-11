"""Find functions that use a module-level name BEFORE re-importing it locally.

That pattern makes the name local for the whole function body, so every earlier
use raises UnboundLocalError at runtime — exactly the bug that broke
POST /chatbots/{platform}/test. Static linters miss it (ruff F821 does not
model this), so walk the AST ourselves.
"""
import ast
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
findings = []

for path in root.rglob("*.py"):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        continue

    module_names = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                module_names.add(alias.asname or alias.name.split(".")[0])

    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # names imported locally inside this function (not nested functions)
        local_imports = {}
        for node in ast.walk(func):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    local_imports.setdefault(name, node.lineno)
        shadowed = {n: ln for n, ln in local_imports.items() if n in module_names}
        if not shadowed:
            continue
        for node in ast.walk(func):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                ln = shadowed.get(node.id)
                if ln is not None and node.lineno < ln:
                    findings.append((path, node.id, node.lineno, ln, func.name))

for path, name, use_line, import_line, func_name in sorted(set(findings)):
    rel = path.relative_to(root)
    print(f"{rel}:{use_line}: '{name}' used in {func_name}() before local re-import at line {import_line}")

print(f"\n{len(set(findings))} risky uses")
