"""Harvey threads in the unified inbox: mirrored without a channel, so nothing generic can send through them."""

# The db fixture comes from test_harvey, so every test argument "redefines" it.
# ruff: noqa: F811

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select
from test_harvey import _Biz, _fake_model, _setup, db  # noqa: F401 - db is a pytest fixture

from app.api.v1 import conversations as conversations_api
from app.domains.channels import followup_service
from app.domains.channels.models import Conversation, ConversationStatus, Message, MessageDirection
from app.domains.channels.schemas import MessageCreate
from app.domains.harvey import inbox_sync
from app.domains.harvey.models import HarveyOutboxItem


@pytest_asyncio.fixture
async def inbox(db):
    async with db.bind.begin() as conn:
        for m in (Conversation, Message):
            await conn.run_sync(lambda c, m=m: m.__table__.create(bind=c, checkfirst=True))
    return db


async def _convs(db, biz):
    return list((await db.execute(select(Conversation).where(Conversation.business_id == biz.id))).scalars())


async def _msgs(db, conv):
    rows = await db.execute(select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at))
    return list(rows.scalars())


def _sent_item(biz, prospect, step, when, kind="sequence", body="cuerpo"):
    return HarveyOutboxItem(
        business_id=biz.id, prospect_id=prospect.id, step=step, kind=kind, to_email=prospect.email, subject="hola",
        body=body, status="sent", sent_at=when, message_id=f"<m{step}{kind}@x>",
    )


@pytest.mark.asyncio
async def test_a_reply_opens_a_channelless_thread_with_the_emails_sent_before(inbox, monkeypatch):
    svc, biz, profile, prospect = await _setup(inbox)
    t0 = datetime.now(timezone.utc) - timedelta(days=3)
    inbox.add_all([_sent_item(biz, prospect, 1, t0), _sent_item(biz, prospect, 2, t0 + timedelta(days=1))])
    await inbox.commit()

    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    await svc.record_reply(biz, profile, prospect, "Me interesa, ¿cuánto sale?")

    (conv,) = await _convs(inbox, biz)
    assert conv.channel_connection_id is None and conv.lead_source == "harvey"
    assert conv.lead_email == "ana@cliente.com" and conv.external_id == f"harvey:{prospect.id}"
    msgs = await _msgs(inbox, conv)
    assert [m.direction for m in msgs] == [MessageDirection.OUTBOUND, MessageDirection.OUTBOUND, MessageDirection.INBOUND]
    assert "¿cuánto sale?" in msgs[-1].content and msgs[0].content.startswith("hola")


@pytest.mark.asyncio
async def test_cold_emails_alone_do_not_fill_the_inbox(inbox):
    svc, biz, profile, prospect = await _setup(inbox)
    item = _sent_item(biz, prospect, 1, datetime.now(timezone.utc))
    inbox.add(item)
    await inbox.commit()
    await inbox_sync.on_sent(inbox, biz.id, prospect, item)
    assert await _convs(inbox, biz) == []


@pytest.mark.asyncio
async def test_a_reply_needing_a_person_flags_the_thread_and_answering_clears_it(inbox, monkeypatch):
    svc, biz, profile, prospect = await _setup(inbox)
    _fake_model(monkeypatch, None)  # no model: the reply goes to a human
    await svc.record_reply(biz, profile, prospect, "¿Podemos hablar del precio?")
    (conv,) = await _convs(inbox, biz)
    assert conv.extra_data["awaiting_human"] is True and "decide una persona" in conv.extra_data["handoff_reason"]

    answer = _sent_item(biz, prospect, 1, datetime.now(timezone.utc), kind="reply", body="Claro, te cuento.")
    inbox.add(answer)
    await inbox.commit()
    await inbox_sync.on_sent(inbox, biz.id, prospect, answer)
    await inbox.refresh(conv)
    assert conv.extra_data["awaiting_human"] is False
    assert (await _msgs(inbox, conv))[-1].content == "Claro, te cuento."


@pytest.mark.asyncio
async def test_the_same_reply_or_email_is_never_mirrored_twice(inbox, monkeypatch):
    svc, biz, profile, prospect = await _setup(inbox)
    _fake_model(monkeypatch, {"classification": "question", "answer": "x"})
    reply = await svc.record_reply(biz, profile, prospect, "¿Envían?")
    await inbox_sync.on_reply(inbox, biz.id, prospect, reply)
    (conv,) = await _convs(inbox, biz)
    assert len(await _msgs(inbox, conv)) == 1
    _fake_model(monkeypatch, {"classification": "interested", "answer": "x"})
    await svc.record_reply(biz, profile, prospect, "Dale")
    assert len(await _convs(inbox, biz)) == 1 and len(await _msgs(inbox, conv)) == 2


@pytest.mark.asyncio
async def test_a_refusal_archives_the_thread(inbox, monkeypatch):
    svc, biz, profile, prospect = await _setup(inbox)
    _fake_model(monkeypatch, {"classification": "opt_out", "answer": ""})
    await svc.record_reply(biz, profile, prospect, "No me escriban más")
    (conv,) = await _convs(inbox, biz)
    assert conv.status is ConversationStatus.ARCHIVED


@pytest.mark.asyncio
async def test_a_mirrored_thread_can_never_receive_a_generic_follow_up(inbox, monkeypatch):
    svc, biz, profile, prospect = await _setup(inbox)
    _fake_model(monkeypatch, {"classification": "question", "answer": "x"})
    await svc.record_reply(biz, profile, prospect, "¿Envían?")
    (conv,) = await _convs(inbox, biz)
    conv.last_message_at = datetime.now(timezone.utc) - timedelta(days=5)  # cold: the scan would pick a chat thread
    await inbox.commit()
    assert (conv.id, biz.id) not in await followup_service._find_cold_conversations(inbox)


@pytest.mark.asyncio
async def test_a_mirror_failure_never_loses_the_reply(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db)  # no conversations/messages tables here
    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    reply = await svc.record_reply(biz, profile, prospect, "Me interesa")
    assert reply.classification == "interested" and (await svc.list_replies(biz.id))[0].id == reply.id


@pytest.mark.asyncio
async def test_other_business_sees_nothing(inbox, monkeypatch):
    svc, biz, profile, prospect = await _setup(inbox)
    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    await svc.record_reply(biz, profile, prospect, "Me interesa")
    assert await _convs(inbox, _Biz()) == []


# ── the inbox API ─────────────────────────────────────────────────────────
@pytest.fixture
def api(monkeypatch):
    async def ok(business_id, user, db):
        return None

    monkeypatch.setattr(conversations_api, "_get_business_for_user", ok)


@pytest.mark.asyncio
async def test_the_inbox_lists_harvey_threads_with_source_and_attention(inbox, api, monkeypatch):
    svc, biz, profile, prospect = await _setup(inbox)
    _fake_model(monkeypatch, None)
    await svc.record_reply(biz, profile, prospect, "¿Podemos hablar del precio?")
    inbox.add(Conversation(business_id=biz.id, lead_name="Chat", lead_source="whatsapp", extra_data={}))
    await inbox.commit()

    rows = await conversations_api.list_conversations(biz.id, None, None, False, None, inbox, None)
    by_source = {r.source: r for r in rows}
    assert set(by_source) == {"harvey", "chat"}
    assert by_source["harvey"].platform == "email" and by_source["harvey"].awaiting_human
    assert not by_source["chat"].awaiting_human

    attention = await conversations_api.list_conversations(biz.id, None, None, True, None, inbox, None)
    assert [r.source for r in attention] == ["harvey"]
    only_chat = await conversations_api.list_conversations(biz.id, None, None, False, "chat", inbox, None)
    assert [r.source for r in only_chat] == ["chat"]
    only_harvey = await conversations_api.list_conversations(biz.id, None, None, False, "harvey", inbox, None)
    assert [r.source for r in only_harvey] == ["harvey"]


@pytest.mark.asyncio
async def test_replying_to_a_harvey_thread_from_the_inbox_is_refused(inbox, api, monkeypatch):
    svc, biz, profile, prospect = await _setup(inbox)
    _fake_model(monkeypatch, {"classification": "question", "answer": "x"})
    await svc.record_reply(biz, profile, prospect, "¿Envían?")
    (conv,) = await _convs(inbox, biz)
    body = MessageCreate(content="hola", direction=MessageDirection.OUTBOUND)
    with pytest.raises(HTTPException) as e:
        await conversations_api.send_message(biz.id, conv.id, body, inbox, None)
    assert e.value.status_code == 409 and "Prospección" in e.value.detail
    assert len(await _msgs(inbox, conv)) == 1  # nothing was written
