"""Post-deploy check: did every group of routes survive the start-up of the deployed API?

Why it exists: ``app/main.py`` mounts routers with ``_try_include``, which logs and SKIPS a router that fails to import.
On 2026-10-28 a Python 3.12-only f-string took every Harvey route out of production for ~3 hours while ``/api/health``
kept answering "ok". This script reads the deployed ``/openapi.json`` and compares it with a snapshot of what a healthy
deployment exposed (``routes_snapshot.json``).

A *group* is the first four static path segments (path parameters dropped), e.g.
``/api/v1/businesses/{business_id}/harvey/profile`` -> ``api/v1/businesses/harvey``. The check fails when

* a whole group in the snapshot has no route at all in the deployment (a router was skipped), or
* the deployment exposes fewer than ``MIN_RATIO`` of the snapshot's routes.

New routes never fail it. When routes are removed on purpose, refresh the snapshot against a healthy deployment:
``python scripts/check_prod_routes.py --update``.

Usage:  python scripts/check_prod_routes.py [--url URL] [--wait SECONDS] [--update]
Only the standard library is used, so CI runs it without installing anything.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parent.parent / "routes_snapshot.json"
DEFAULT_URL = "https://sellia-production.up.railway.app"
MIN_RATIO = 0.95
GROUP_DEPTH = 4


def group_of(path: str) -> str:
    segments = [s for s in path.split("/") if s and not (s.startswith("{") and s.endswith("}"))]
    return "/".join(segments[:GROUP_DEPTH])


def groups_of(paths: list[str]) -> Counter[str]:
    return Counter(group_of(p) for p in paths)


def compare(snapshot: dict[str, int], deployed: Counter[str]) -> list[str]:
    """Human-readable problems; empty when the deployment is complete."""
    problems = [
        f"grupo sin rutas: /{group} (había {count} en la foto sana)"
        for group, count in sorted(snapshot.items())
        if deployed.get(group, 0) == 0
    ]
    expected, found = sum(snapshot.values()), sum(min(deployed.get(g, 0), c) for g, c in snapshot.items())
    if expected and found / expected < MIN_RATIO:
        problems.append(f"faltan rutas: {found} de {expected} esperadas ({found / expected:.0%})")
    return problems


def fetch_paths(url: str, timeout: int = 40) -> list[str]:
    req = urllib.request.Request(url.rstrip("/") + "/openapi.json", headers={"User-Agent": "sellia-route-check"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https URL from our own config
        return list(json.load(resp).get("paths", {}))


def fetch_with_wait(url: str, wait: int) -> list[str]:
    """A fresh deployment may still be swapping instances (502/503): retry until ``wait`` seconds have passed."""
    deadline = time.monotonic() + wait
    while True:
        try:
            return fetch_paths(url)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
            if time.monotonic() >= deadline:
                raise SystemExit(f"::error::no se pudo leer {url}/openapi.json: {e}") from e
            time.sleep(15)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--wait", type=int, default=0, help="seconds to keep retrying while the deployment swaps")
    parser.add_argument("--update", action="store_true", help="rewrite the snapshot from a healthy deployment")
    args = parser.parse_args(argv)

    paths = fetch_with_wait(args.url, args.wait)
    deployed = groups_of(paths)
    if args.update:
        SNAPSHOT.write_text(json.dumps(dict(sorted(deployed.items())), indent=1) + "\n", encoding="utf-8")
        print(f"foto actualizada: {len(deployed)} grupos, {len(paths)} rutas -> {SNAPSHOT.name}")
        return 0

    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    problems = compare(snapshot, deployed)
    if problems:
        for p in problems:
            print(f"::error::{p}")
        print("Un router no arrancó en producción (mirá el log: 'Skipped extra router').")
        return 1
    print(f"OK: {sum(deployed.values())} rutas en {len(deployed)} grupos; la foto tiene {sum(snapshot.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
