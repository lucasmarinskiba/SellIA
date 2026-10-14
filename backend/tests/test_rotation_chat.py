"""The business owner answers webhook-token rotation proposals in the SellIA assistant chat.

Rotating a token breaks the webhook URL on the external platform, so the chat reads the owner's
message by plain rules (never the language model) and only a clear yes, after the proposal was
shown, rotates anything.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from app.domains.channels.token_rotation_chat import Intent, interpret

NOW = datetime.now(timezone.utc)

# ── the interpreter, as a table ──────────────────────────────────────────────

@pytest.mark.parametrize(
    ("message", "just_listed", "expected"),
    [
        # not about rotation: the normal assistant answers
        ("¿cuántos leads tuve hoy?", False, Intent.NONE),
        ("quiero renovar mi suscripción", False, Intent.NONE),
        ("sí", False, Intent.NONE),                       # a bare yes out of the blue does nothing
        ("dale", False, Intent.NONE),
        ("no", False, Intent.NONE),
        # asking about it only lists
        ("quiero rotar el token del webhook", False, Intent.LIST),
        ("ver rotaciones pendientes", False, Intent.LIST),
        ("hay que renovar el token de whatsapp?", False, Intent.LIST),
        ("sí, rotá el token del webhook", False, Intent.LIST),     # short "sí" without the proposal shown
        # an explicit yes naming the topic accepts even without the listing
        ("acepto la rotación del token", False, Intent.ACCEPT),
        ("confirmo, renovar el token del webhook", False, Intent.ACCEPT),
        # after the listing a short answer is enough
        ("sí", True, Intent.ACCEPT),
        ("Sí, dale", True, Intent.ACCEPT),
        ("aceptar", True, Intent.ACCEPT),
        ("ok adelante", True, Intent.ACCEPT),
        ("no", True, Intent.REJECT),
        ("No, dejalo como está", True, Intent.REJECT),
        ("rechazar", True, Intent.REJECT),
        ("más adelante", True, Intent.REJECT),
        ("ahora no", True, Intent.REJECT),
        # contradictory answers are not guessed
        ("sí pero no", True, Intent.UNCLEAR),
        ("acepto pero cancelá", True, Intent.UNCLEAR),
        # after the listing, unrelated talk is left to the assistant (it must not hijack the chat)
        ("¿cuántos canales tengo conectados en total en mi cuenta?", True, Intent.NONE),
        ("no sé qué canal es ese, podés explicarme mejor cómo funciona todo esto de la plataforma?", True, Intent.NONE),
        ("sí me gustaría saber cuántas ventas hicimos el mes pasado en el canal de instagram", True, Intent.NONE),
    ],
)
def test_interpreter(message: str, just_listed: bool, expected: Intent) -> None:
    assert interpret(message, just_listed=just_listed) is expected


# ── the chat endpoint ────────────────────────────────────────────────────────

@pytest.fixture
def orchestrator_calls(monkeypatch):
    """Replace the language-model orchestrator: records calls, never reaches an LLM."""
    from app.api.v1 import assistant

    calls: list[str] = []

    async def process_intent(self, *, user_input, user_id, business_id, conversation_history):
        calls.append(user_input)
        return {"action": "ASK_CLARIFICATION", "response": "respuesta del modelo"}

    async def process_intent_stream(self, *, user_input, user_id, business_id, conversation_history):
        calls.append(user_input)
        yield json.dumps({"type": "token", "content": "respuesta del modelo"})

    monkeypatch.setattr(assistant.SellIAOrchestrator, "process_intent", process_intent)
    monkeypatch.setattr(assistant.SellIAOrchestrator, "process_intent_stream", process_intent_stream)
    return calls


@pytest.fixture
async def owner_business(db_session, test_user):
    from app.domains.alerts.models import Alert, Recommendation
    from app.domains.businesses.models import Business
    from app.domains.channels.models import ChannelConnection, ChannelPlatform
    from app.domains.channels.token_rotation import propose_rotation
    from app.domains.security.models import SecretRotationLog

    business = Business(user_id=test_user.id, name=f"Chat {uuid.uuid4().hex[:6]}")
    db_session.add(business)
    await db_session.commit()
    business_id = business.id

    async def make_channel(name: str, *, proposal: bool = True) -> uuid.UUID:
        ch = ChannelConnection(business_id=business_id, platform=ChannelPlatform.EMAIL, name=name)
        db_session.add(ch)
        await db_session.commit()
        channel_id = ch.id
        await db_session.execute(
            update(ChannelConnection).where(ChannelConnection.id == channel_id).values(created_at=NOW - timedelta(days=200))
        )
        await db_session.commit()
        if proposal:
            channel = (await db_session.execute(select(ChannelConnection).where(ChannelConnection.id == channel_id))).scalar_one()
            await propose_rotation(db_session, channel, NOW)
            await db_session.commit()
        return channel_id

    yield business_id, make_channel
    for table, column in (
        (Alert, Alert.business_id),
        (Recommendation, Recommendation.business_id),
        (SecretRotationLog, SecretRotationLog.business_id),
        (ChannelConnection, ChannelConnection.business_id),
    ):
        await db_session.execute(table.__table__.delete().where(column == business_id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


async def _token(db, channel_id) -> str:
    from app.domains.channels.models import ChannelConnection

    db.expire_all()
    return (await db.execute(select(ChannelConnection.webhook_token).where(ChannelConnection.id == channel_id))).scalar_one()


@pytest.fixture
def chat(auth_client, db_session, test_user):
    """Post a message to the assistant as the owner. Refreshes the user first: the test's own
    commits expire the fixture object, while a real request loads a fresh one."""

    async def _chat(message: str, business_id, conversation_id=None) -> dict:
        await db_session.refresh(test_user)
        params = {"message": message, "business_id": str(business_id)}
        if conversation_id:
            params["conversation_id"] = str(conversation_id)
        response = await auth_client.post("/api/v1/assistant/chat", params=params)
        assert response.status_code == 200, response.text
        return response.json()

    return _chat


@pytest.fixture
def new_conversation(auth_client, db_session, test_user):
    async def _new() -> str:
        await db_session.refresh(test_user)
        created = await auth_client.post("/api/v1/assistant/conversations")
        assert created.status_code == 201, created.text
        return created.json()["id"]

    return _new


async def test_asking_lists_the_proposal_and_changes_nothing(db_session, auth_client, owner_business, orchestrator_calls, chat) -> None:
    business_id, make_channel = owner_business
    channel_id = await make_channel("WhatsApp ventas")
    before = await _token(db_session, channel_id)

    result = await chat("quiero rotar el token del webhook", business_id)

    assert result["action"] == "ROTATION_PROPOSAL" and result["pending_rotations"] == 1
    assert "WhatsApp ventas" in result["response"] and "aceptar" in result["response"].lower()
    assert orchestrator_calls == []                      # the model was not involved
    assert await _token(db_session, channel_id) == before


async def test_listing_then_yes_rotates_once_and_never_prints_the_token(
    db_session, auth_client, owner_business, orchestrator_calls, chat, new_conversation) -> None:
    business_id, make_channel = owner_business
    channel_id = await make_channel("WhatsApp ventas")
    before = await _token(db_session, channel_id)
    conversation = await new_conversation()

    await chat("ver rotaciones pendientes", business_id, conversation)
    answer = await chat("sí", business_id, conversation)

    after = await _token(db_session, channel_id)
    assert answer["action"] == "ROTATION_APPLIED" and after != before
    assert after not in answer["response"] and before not in answer["response"]
    assert "Canales" in answer["response"]               # where to find the new URL
    assert orchestrator_calls == []

    again = await chat("sí", business_id, conversation)   # a second "sí" must not rotate again
    assert await _token(db_session, channel_id) == after
    assert again["action"] != "ROTATION_APPLIED"


async def test_a_bare_yes_without_the_proposal_goes_to_the_normal_assistant(
    db_session, auth_client, owner_business, orchestrator_calls, chat, new_conversation) -> None:
    business_id, make_channel = owner_business
    channel_id = await make_channel("WhatsApp ventas")
    before = await _token(db_session, channel_id)
    conversation = await new_conversation()

    result = await chat("sí", business_id, conversation)

    assert orchestrator_calls == ["sí"] and result["response"] == "respuesta del modelo"
    assert await _token(db_session, channel_id) == before
    assert result["pending_rotations"] == 1              # the normal answer still tells there is one pending


async def test_rejecting_keeps_the_token(db_session, auth_client, owner_business, orchestrator_calls, chat, new_conversation) -> None:
    business_id, make_channel = owner_business
    channel_id = await make_channel("WhatsApp ventas")
    before = await _token(db_session, channel_id)
    conversation = await new_conversation()

    await chat("ver rotaciones pendientes", business_id, conversation)
    answer = await chat("no, dejalo como está", business_id, conversation)

    assert answer["action"] == "ROTATION_DISMISSED" and answer["pending_rotations"] == 0
    assert await _token(db_session, channel_id) == before
    nothing = await chat("ver rotaciones pendientes", business_id)
    assert nothing["action"] == "ROTATION_NONE"


async def test_with_two_proposals_the_owner_names_the_channel(
    db_session, auth_client, owner_business, orchestrator_calls, chat, new_conversation) -> None:
    business_id, make_channel = owner_business
    ventas = await make_channel("WhatsApp ventas")
    soporte = await make_channel("Email soporte")
    before = {ventas: await _token(db_session, ventas), soporte: await _token(db_session, soporte)}
    conversation = await new_conversation()

    await chat("ver rotaciones pendientes", business_id, conversation)
    ambiguous = await chat("aceptar", business_id, conversation)
    assert ambiguous["action"] == "ROTATION_PROPOSAL"    # which one? it asks again
    assert {c: await _token(db_session, c) for c in before} == before

    named = await chat("aceptar el de Email soporte", business_id, conversation)
    assert named["action"] == "ROTATION_APPLIED" and named["pending_rotations"] == 1
    assert await _token(db_session, soporte) != before[soporte]
    assert await _token(db_session, ventas) == before[ventas]


async def test_someone_elses_business_is_not_touched(
    db_session, auth_client, owner_business, orchestrator_calls, chat) -> None:
    from app.core.deps import get_current_active_user
    from app.domains.users.models import User
    from app.main import app

    business_id, make_channel = owner_business
    channel_id = await make_channel("WhatsApp ventas")
    before = await _token(db_session, channel_id)

    stranger = User(id=uuid.uuid4(), email=f"s-{uuid.uuid4()}@example.com", hashed_password="x", full_name="S", is_active=True)
    db_session.add(stranger)
    await db_session.commit()
    stranger_id = stranger.id
    try:
        await db_session.refresh(stranger)
        app.dependency_overrides[get_current_active_user] = lambda: stranger
        result = await chat("acepto la rotación del token del webhook", business_id)
        assert result["response"] == "respuesta del modelo"     # handled as ordinary chat, no rotation
        assert "pending_rotations" not in result              # and it does not leak that there is one
        assert await _token(db_session, channel_id) == before
    finally:
        await db_session.execute(User.__table__.delete().where(User.id == stranger_id))
        await db_session.commit()


async def test_the_stream_endpoint_is_answered_by_the_rules_too(
    db_session, auth_client, owner_business, orchestrator_calls, test_user
) -> None:
    business_id, make_channel = owner_business
    await make_channel("WhatsApp ventas")
    await db_session.refresh(test_user)

    response = await auth_client.post(
        "/api/v1/assistant/chat/stream",
        params={"message": "quiero rotar el token del webhook", "business_id": str(business_id)},
    )

    assert response.status_code == 200
    body = response.text
    assert "event: token" in body and "event: action" in body and "ROTATION_PROPOSAL" in body
    assert orchestrator_calls == []
