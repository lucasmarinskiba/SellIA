"""The ruff ratchet must fail on NEW runtime-error findings and only on those.

Pure-logic checks of scripts/ruff_fatal_ratchet.py (no ruff run), plus a consistency
check of the committed baseline. The gate is only useful if it keeps three promises:
a new finding fails, code that merely moves does not, and fixing one never fails.
"""

import importlib.util
import json
from collections import Counter
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "ruff_fatal_ratchet.py"

_spec = importlib.util.spec_from_file_location("ruff_fatal_ratchet", SCRIPT)
ratchet = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ratchet)


def finding(path: str, name: str, row: int = 1, code: str = "F821") -> dict:
    return {
        "filename": path,
        "code": code,
        "message": f"Undefined name `{name}`",
        "location": {"row": row, "column": 1},
    }


def test_the_key_ignores_line_numbers_and_path_separators() -> None:
    posix = finding("C:/work/backend/app/api/v1/x.py", "foo", row=10)
    windows = finding("C:\\work\\backend\\app\\api\\v1\\x.py", "foo", row=250)
    assert ratchet._key(posix) == ratchet._key(windows) == ("api/v1/x.py", "F821", "foo")


def test_a_new_finding_is_worse_than_the_baseline() -> None:
    baseline = ratchet.count([finding("/b/app/a.py", "known")])
    current = ratchet.count([finding("/b/app/a.py", "known"), finding("/b/app/a.py", "brand_new")])
    worse, better = ratchet.compare(current, baseline)
    assert worse == [("a.py", "F821", "brand_new")]
    assert better == []


def test_one_more_use_of_an_already_baselined_name_is_worse() -> None:
    baseline = ratchet.count([finding("/b/app/a.py", "select")])
    current = ratchet.count([finding("/b/app/a.py", "select", row=1), finding("/b/app/a.py", "select", row=2)])
    worse, _ = ratchet.compare(current, baseline)
    assert worse == [("a.py", "F821", "select")]


def test_the_same_tree_and_a_shifted_tree_are_not_worse() -> None:
    baseline = ratchet.count([finding("/b/app/a.py", "select", row=5)])
    shifted = ratchet.count([finding("/b/app/a.py", "select", row=95)])
    assert ratchet.compare(shifted, baseline) == ([], [])


def test_fixing_a_finding_is_an_improvement_never_a_failure() -> None:
    baseline = ratchet.count([finding("/b/app/a.py", "x"), finding("/b/app/b.py", "y")])
    current = ratchet.count([finding("/b/app/a.py", "x")])
    worse, better = ratchet.compare(current, baseline)
    assert worse == []
    assert better == [("b.py", "F821", "y")]


def test_the_committed_baseline_is_well_formed() -> None:
    rows = json.loads(ratchet.BASELINE.read_text(encoding="utf-8"))
    # An empty baseline is the goal: zero known findings, so ANY new one fails the gate. (It used to be rejected as a
    # sign of a broken baseline; the "ruff did not run" case is covered by test_a_failed_ruff_run_is_not_a_clean_pass.)
    assert isinstance(rows, list)
    assert all(isinstance(r["count"], int) and r["count"] > 0 for r in rows)
    keys = [(r["file"], r["rule"], r["name"]) for r in rows]
    assert keys == sorted(keys), "keep the baseline sorted so diffs stay reviewable"
    assert len(set(keys)) == len(keys)
    assert isinstance(ratchet.load_baseline(), Counter)


def test_a_failed_ruff_run_is_not_a_clean_pass(monkeypatch) -> None:
    # With an empty baseline, "ruff crashed" must never read as "zero findings".
    import types

    monkeypatch.setattr(
        ratchet.subprocess, "run", lambda *a, **k: types.SimpleNamespace(returncode=2, stdout="", stderr="boom")
    )
    try:
        ratchet.run_ruff()
    except SystemExit as e:
        assert "ruff failed to run" in str(e)
    else:
        raise AssertionError("a crashed ruff must stop the gate, not return no findings")


def test_with_an_empty_baseline_any_new_finding_fails() -> None:
    worse, _ = ratchet.compare(ratchet.count([finding("a.py", "x")]), Counter())
    assert worse == [("a.py", "F821", "x")]
