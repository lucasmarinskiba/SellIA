"""Celery's broker layer (kombu) must be able to start with the redis-py this project pins.

celery==5.3.6 allows any kombu <6, so a fresh build picks up the newest one. kombu 5.7.0 refuses to start with
redis-py < 6.1 (``VersionMismatch``), which crashed the celery beat and worker services on boot right after a rebuild
while the web service, which does not use kombu, kept working. Nothing in the web app's tests touches this path.
"""

import re
from pathlib import Path

import pytest

kombu = pytest.importorskip("kombu")
redis = pytest.importorskip("redis")


def test_kombu_is_pinned_explicitly():
    text = (Path(__file__).resolve().parents[1] / "requirements.txt").read_text(encoding="utf-8")
    pins = [line.split("#")[0].strip() for line in text.splitlines()]
    assert any(re.fullmatch(r"kombu==\d+\.\d+\.\d+", p) for p in pins), "pin kombu: celery lets it float"


def test_redis_transport_accepts_the_installed_redis_py():
    from kombu import Connection
    from kombu.exceptions import VersionMismatch

    try:
        Connection("redis://127.0.0.1:1/0", connect_timeout=1).channel()
    except VersionMismatch as exc:  # the failure mode this test exists for
        pytest.fail(f"kombu {kombu.__version__} cannot use redis-py {redis.__version__}: {exc}")
    except Exception:
        pass  # no broker listening on port 1: the transport itself initialised fine
