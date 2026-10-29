"""A business with no postal address can neither draft, answer nor send: it goes in every email's footer."""

# The db/smtp fixtures come from test_harvey, so every test argument "redefines" them.
# ruff: noqa: F811

import uuid

import pytest
from test_harvey import _approved, _connect_mailbox, _fake_model, _setup, db, smtp  # noqa: F401 - pytest fixtures

from app.domains.harvey.service import HarveyError


@pytest.mark.asyncio
async def test_drafting_is_refused_with_a_clear_message_when_there_is_no_postal_address(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db, postal_address="")
    _fake_model(monkeypatch, {"subject": "hola", "body": "¿Cómo reciben pedidos?"})
    with pytest.raises(HarveyError) as e:
        await svc.draft_first_email(biz, profile, prospect)
    assert e.value.status_code == 409 and "dirección postal" in str(e.value)


@pytest.mark.asyncio
async def test_a_blank_address_counts_as_no_address(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db, postal_address="   ")
    _fake_model(monkeypatch, {"subject": "hola", "body": "x"})
    with pytest.raises(HarveyError):
        await svc.draft_first_email(biz, profile, prospect)


@pytest.mark.asyncio
async def test_an_approved_email_is_blocked_at_send_time_if_the_address_was_removed(db, monkeypatch, smtp):
    svc, biz, profile, prospect = await _setup(db)
    await _connect_mailbox(db, biz)
    item = await _approved(monkeypatch, svc, biz, profile, prospect)
    profile = await svc.update_profile(biz, {"postal_address": ""})  # removed after approval, before the send
    sent = await svc.send_item(biz, profile, item, await svc.require_account(biz.id))
    assert sent.status == "blocked" and any("dirección postal" in r for r in sent.gate_reasons)
    assert smtp == []  # nothing left the building


@pytest.mark.asyncio
async def test_editing_a_draft_without_an_address_keeps_it_blocked(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db)
    _fake_model(monkeypatch, {"subject": "hola", "body": "¿Cómo reciben pedidos?"})
    item = await svc.draft_first_email(biz, profile, prospect)
    profile = await svc.update_profile(biz, {"postal_address": ""})
    edited = await svc.edit_item(biz.id, profile, item.id, "hola", "Hola Ana, ¿pedidos?")
    assert edited.status == "blocked" and any("dirección postal" in r for r in edited.gate_reasons)


@pytest.mark.asyncio
async def test_with_an_address_everything_still_works_and_the_footer_carries_it(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db)
    _fake_model(monkeypatch, {"subject": "hola", "body": "¿Cómo reciben pedidos?"})
    item = await svc.draft_first_email(biz, profile, prospect)
    assert item.status == "pending_review" and "Calle Falsa 123" in item.body


@pytest.mark.asyncio
async def test_answering_a_reply_is_also_refused_without_an_address(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db)
    _fake_model(monkeypatch, {"classification": "interested", "answer": "¡Genial!"})
    reply = await svc.record_reply(biz, profile, prospect, "Me interesa")
    profile = await svc.update_profile(biz, {"postal_address": ""})
    with pytest.raises(HarveyError) as e:
        await svc.answer_reply(biz, profile, reply.id)
    assert e.value.status_code == 409 and "dirección postal" in str(e.value)
    assert uuid.UUID(str(reply.id))
