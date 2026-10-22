"""POST /api/v1/webhooks/whatsapp is answered by whatsapp_receive, and only by it.

The Meta webhook used to be registered twice: sellbot.py had its own POST handler,
mounted first, so it answered and whatsapp_receive never ran. That copy sent replies
through graph.instagram.com and returned 500 on errors, which makes Meta redeliver
the message. These tests pin the handler that remains: it always answers 200.
"""

import pytest
from fastapi.testclient import TestClient

import app.api.v1.whatsapp_webhook as whatsapp_webhook
from app.main import app

PATH = "/api/v1/webhooks/whatsapp"
SENDER = "5491100000000"


def _text_payload(body: str = "hola") -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": SENDER, "type": "text", "text": {"body": body}}
                            ]
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> dict[str, list]:
    recorded: dict[str, list] = {"ai": [], "send": []}

    async def fake_ai(message: str) -> str:
        recorded["ai"].append(message)
        return "respuesta"

    async def fake_send(to: str, text: str, phone_number_id: str, token: str) -> bool:
        recorded["send"].append((to, text))
        return True

    monkeypatch.setattr(whatsapp_webhook, "_call_anthropic", fake_ai)
    monkeypatch.setattr(whatsapp_webhook, "_send_whatsapp_message", fake_send)
    monkeypatch.setenv("META_PHONE_NUMBER_ID", "123")
    monkeypatch.setenv("META_WHATSAPP_TOKEN", "token")
    return recorded


def test_text_message_gets_ai_reply(calls: dict[str, list]) -> None:
    response = TestClient(app).post(PATH, json=_text_payload("quiero comprar"))

    assert response.status_code == 200
    assert calls["ai"] == ["quiero comprar"]
    assert calls["send"] == [(SENDER, "respuesta")]


def test_non_text_message_is_ignored(calls: dict[str, list]) -> None:
    payload = _text_payload()
    payload["entry"][0]["changes"][0]["value"]["messages"][0]["type"] = "image"

    response = TestClient(app).post(PATH, json=payload)

    assert response.status_code == 200
    assert calls["ai"] == []
    assert calls["send"] == []


def test_ai_failure_still_answers_200(calls: dict[str, list], monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_ai(message: str) -> str:
        raise RuntimeError("anthropic down")

    monkeypatch.setattr(whatsapp_webhook, "_call_anthropic", failing_ai)

    response = TestClient(app).post(PATH, json=_text_payload())

    # 200, not 500: Meta redelivers any non-2xx webhook, which would repeat the reply.
    assert response.status_code == 200
    assert calls["send"] == []


def test_malformed_body_answers_200(calls: dict[str, list]) -> None:
    response = TestClient(app).post(
        PATH, content=b"not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200
    assert calls["ai"] == []
