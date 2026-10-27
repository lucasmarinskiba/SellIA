"""POST /api/v1/webhooks/whatsapp is answered by whatsapp_receive, and only by it.

The Meta webhook used to be registered twice: sellbot.py had its own POST handler, mounted first, so it
answered and whatsapp_receive never ran. That copy sent replies through graph.instagram.com, returned 500 on
errors (which makes Meta redeliver the message) and, in its later form, only delegated. These tests pin that a
single handler remains and that it is the one that checks the signature.
(What that handler does with a valid message is covered in test_whatsapp_bot_hardening.py.)
"""

from fastapi.testclient import TestClient

import app.api.v1.whatsapp_webhook as whatsapp_webhook
from app.main import app

PATH = "/api/v1/webhooks/whatsapp"


def _post_handlers() -> list:
    return [
        route.endpoint
        for route in app.routes
        if getattr(route, "path", None) == PATH and "POST" in (getattr(route, "methods", None) or set())
    ]


def test_exactly_one_post_handler_and_it_is_whatsapp_receive() -> None:
    assert _post_handlers() == [whatsapp_webhook.whatsapp_receive]


def test_an_unsigned_post_is_rejected_by_that_handler(monkeypatch) -> None:
    monkeypatch.setenv("META_APP_SECRET", "test-app-secret")

    response = TestClient(app).post(PATH, json={"entry": []})

    # The removed sellbot copy answered 200 to anyone; the remaining handler requires X-Hub-Signature-256.
    assert response.status_code == 403
