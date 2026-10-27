"""WhatsApp bot hardening: firma, dedupe, memoria, opt-out, límites y fail-open.

Sin red y sin Redis real: _store() se reemplaza por FakeRedis y las llamadas a
Meta y Anthropic por mocks. Solo se monta el router, no toda la app.
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import RedisError

from app.api.v1 import whatsapp_webhook as wh

APP_SECRET = "app-secret-test"
SENDER = "5491112345678"


class FakeRedis:
    """Subconjunto de redis.asyncio usado por el webhook. fail=True simula Redis caído."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.kv: dict[str, str] = {}
        self.lists: dict[str, list[str]] = {}

    def _check(self) -> None:
        if self.fail:
            raise RedisError("redis caído (simulado)")

    async def set(self, key, value, nx=False, ex=None):
        self._check()
        if nx and key in self.kv:
            return None
        self.kv[key] = str(value)
        return True

    async def incr(self, key):
        self._check()
        self.kv[key] = str(int(self.kv.get(key, "0")) + 1)
        return int(self.kv[key])

    async def expire(self, key, seconds):
        self._check()
        return True

    async def exists(self, key):
        self._check()
        return int(key in self.kv or key in self.lists)

    async def rpush(self, key, *values):
        self._check()
        self.lists.setdefault(key, []).extend(values)
        return len(self.lists[key])

    async def ltrim(self, key, start, stop):
        self._check()
        end = None if stop == -1 else stop + 1
        self.lists[key] = self.lists.get(key, [])[start:end]
        return True

    async def lrange(self, key, start, stop):
        self._check()
        end = None if stop == -1 else stop + 1
        return self.lists.get(key, [])[start:end]


def _event(
    msg_id: str = "wamid.1",
    sender: str = SENDER,
    text: str = "Hola",
    phone_number_id: str = "111",
    kind: str = "text",
) -> bytes:
    message = {"id": msg_id, "from": sender, "type": kind, "text": {"body": text}}
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "entry-1",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {"phone_number_id": phone_number_id},
                            "messages": [message],
                        },
                    }
                ],
            }
        ],
    }
    return json.dumps(payload).encode()


def _sign(raw: bytes, secret: str = APP_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def _post(
    client: TestClient, raw: bytes, signed: bool = True, secret: str = APP_SECRET
):
    headers = {"Content-Type": "application/json"}
    if signed:
        headers["X-Hub-Signature-256"] = _sign(raw, secret)
    return client.post("/api/v1/webhooks/whatsapp", content=raw, headers=headers)


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", APP_SECRET)
    monkeypatch.setenv("META_PHONE_NUMBER_ID", "111")
    monkeypatch.setenv("META_WHATSAPP_TOKEN", "wa-token")
    monkeypatch.setenv("META_WEBHOOK_VERIFY_TOKEN", "verify-me")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.delenv("WHATSAPP_BUSINESS_CONTEXT", raising=False)


@pytest.fixture
def store(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(wh, "_store", lambda: fake)
    return fake


@pytest.fixture
def sent(monkeypatch):
    mock = AsyncMock(return_value=True)
    monkeypatch.setattr(wh, "_send_whatsapp_message", mock)
    return mock


@pytest.fixture
def ai(monkeypatch):
    mock = AsyncMock(return_value="Hola, ¿qué necesitás?")
    monkeypatch.setattr(wh, "_call_anthropic", mock)
    return mock


@pytest.fixture
def client(env):
    app = FastAPI()
    app.include_router(wh.router, prefix="/api/v1")
    return TestClient(app)


# ---------- Verificación GET ----------


def test_verify_with_right_token_returns_challenge(client):
    response = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "abc123",
        },
    )

    assert response.status_code == 200
    assert response.text == "abc123"


def test_verify_with_wrong_token_is_forbidden(client):
    response = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "nope",
            "hub.challenge": "abc123",
        },
    )

    assert response.status_code == 403


def test_verify_without_configured_token_is_forbidden(client, monkeypatch):
    monkeypatch.delenv("META_WEBHOOK_VERIFY_TOKEN")
    response = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "",
            "hub.challenge": "abc123",
        },
    )

    assert response.status_code == 403


# ---------- Firma en POST ----------


def test_unsigned_post_is_rejected_and_does_nothing(client, store, sent, ai):
    response = _post(client, _event(), signed=False)

    assert response.status_code == 403
    ai.assert_not_called()
    sent.assert_not_called()


def test_wrong_signature_is_rejected(client, store, sent, ai):
    response = _post(client, _event(), secret="otro-secret")

    assert response.status_code == 403
    ai.assert_not_called()
    sent.assert_not_called()


def test_missing_app_secret_rejects_everything(client, store, sent, ai, monkeypatch):
    monkeypatch.delenv("META_APP_SECRET")

    response = _post(client, _event())

    assert response.status_code == 403
    ai.assert_not_called()


# ---------- Flujo feliz, memoria y dedupe ----------


def test_signed_message_gets_ai_reply_and_is_stored(client, store, sent, ai):
    response = _post(client, _event(text="¿Cuánto cuesta el corte?"))

    assert response.status_code == 200
    ai.assert_awaited_once()
    assert ai.call_args.args[0] == [
        {"role": "user", "content": "¿Cuánto cuesta el corte?"}
    ]
    sent.assert_awaited_once()
    assert sent.call_args.args[0] == SENDER
    assert sent.call_args.args[1] == "Hola, ¿qué necesitás?"
    assert len(store.lists[f"wa:hist:{wh._sender_key(SENDER)}"]) == 2


def test_second_message_carries_previous_turns(client, store, sent, ai):
    _post(client, _event(msg_id="wamid.1", text="Hola"))
    _post(client, _event(msg_id="wamid.2", text="¿Y los horarios?"))

    second_call_messages = ai.call_args_list[1].args[0]
    assert second_call_messages == [
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "Hola, ¿qué necesitás?"},
        {"role": "user", "content": "¿Y los horarios?"},
    ]


def test_redelivered_message_is_processed_once(client, store, sent, ai):
    _post(client, _event(msg_id="wamid.same"))
    _post(client, _event(msg_id="wamid.same"))

    ai.assert_awaited_once()
    sent.assert_awaited_once()


def test_wrong_phone_number_id_is_ignored(client, store, sent, ai):
    _post(client, _event(phone_number_id="999"))

    ai.assert_not_called()
    sent.assert_not_called()


def test_non_text_messages_are_ignored(client, store, sent, ai):
    _post(client, _event(kind="image"))

    ai.assert_not_called()


# ---------- Sin respuesta enlatada ----------


async def test_without_api_key_nothing_is_sent(store, sent, monkeypatch, env):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    await wh._handle_message(
        {"id": "wamid.9", "from": SENDER, "text": "Hola", "phone_number_id": "111"},
        "111",
        "wa-token",
    )

    sent.assert_not_called()


# ---------- Opt-out ----------


def test_opt_out_stops_all_future_replies(client, store, sent, ai):
    _post(client, _event(msg_id="wamid.1", text="BAJA"))
    _post(client, _event(msg_id="wamid.2", text="Hola, sigo?"))

    ai.assert_not_called()
    sent.assert_awaited_once()
    assert sent.call_args.args[1] == wh.OPT_OUT_REPLY


def test_opt_out_only_matches_whole_message(client, store, sent, ai):
    _post(client, _event(text="quiero dar de baja mi pedido"))

    ai.assert_awaited_once()


# ---------- Límites ----------


def test_rate_limit_stops_replies_for_a_sender(client, store, sent, ai, monkeypatch):
    monkeypatch.setattr(wh, "MAX_MESSAGES_PER_WINDOW", 2)
    for index in range(3):
        _post(client, _event(msg_id=f"wamid.{index}", text=f"msg {index}"))

    assert ai.await_count == 2


def test_long_inbound_text_is_clipped(client, store, sent, ai):
    _post(client, _event(text="x" * 5000))

    sent_text = ai.call_args.args[0][-1]["content"]
    assert len(sent_text) <= wh.MAX_INBOUND_CHARS


def test_long_outbound_reply_is_clipped(client, store, sent, ai):
    ai.return_value = "y" * 3000

    _post(client, _event())

    assert len(sent.call_args.args[1]) <= wh.MAX_OUTBOUND_CHARS


# ---------- Redis caído: fail-open ----------


def test_redis_down_still_answers(client, sent, ai, monkeypatch):
    monkeypatch.setattr(wh, "_store", lambda: FakeRedis(fail=True))

    _post(client, _event())

    ai.assert_awaited_once()
    sent.assert_awaited_once()


# ---------- Historial y contrato con Anthropic ----------


async def test_misaligned_history_is_discarded(store):
    key = f"wa:hist:{wh._sender_key(SENDER)}"
    store.lists[key] = [
        json.dumps({"role": "assistant", "content": "huérfano"}),
        json.dumps({"role": "user", "content": "x"}),
    ]

    assert await wh._load_history(SENDER) == []


async def test_call_anthropic_caches_system_and_adds_business_context(monkeypatch, env):
    captured: list[dict] = []

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"content": [{"type": "text", "text": "ok"}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, headers=None, json=None):
            captured.append(json)
            return FakeResponse()

    monkeypatch.setenv("WHATSAPP_BUSINESS_CONTEXT", "Corte $5000. Horario 9-18.")
    monkeypatch.setattr(wh.httpx, "AsyncClient", FakeClient)

    reply = await wh._call_anthropic([{"role": "user", "content": "precio?"}])

    payload = captured[0]
    assert reply == "ok"
    assert payload["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Corte $5000" in payload["system"][1]["text"]
    assert payload["messages"] == [{"role": "user", "content": "precio?"}]


# ---------- Regresión: la app de producción sirve el webhook endurecido ----------


def test_production_app_rejects_unsigned_webhook(env):
    """app.sellbot (la app de producción) antes tenía su propio handler sin firma.

    Este test falla si vuelve a haber una copia no endurecida en la ruta.
    """
    from app.sellbot import app as production_app

    client = TestClient(production_app)
    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=_event(),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 403
