"""seo_config.router: business-ownership gate on the authenticated router, and
the generic /webhooks/conversion endpoint (link resolution, no fabricated
signature, correct FOMAConversionService method).

Real SQLite tables (users, businesses, publication_links, conversion_events,
seo_conversion_webhook_events); no Mercado Libre/network calls involved.
"""

import json
import os
import uuid
from uuid import uuid4

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool


@compiles(PGUUID, "sqlite")
def _uuid_sqlite(el, comp, **kw):  # noqa: ANN001
    return "CHAR(36)"


@compiles(PGJSONB, "sqlite")
def _jsonb_sqlite(el, comp, **kw):  # noqa: ANN001
    return "TEXT"


def _try_uuid(v):
    try:
        return uuid.UUID(v)
    except (ValueError, TypeError, AttributeError):
        return v


PGUUID.bind_processor = lambda self, d: (lambda v: None if v is None else str(v))
PGUUID.result_processor = lambda self, d, c: (lambda v: None if v is None else _try_uuid(v))
PGJSONB.bind_processor = lambda self, d: (lambda v: None if v is None else json.dumps(v))
PGJSONB.result_processor = lambda self, d, c: (
    lambda v: None if v in (None, "") else (v if isinstance(v, (dict, list)) else json.loads(v))
)

from app.core.database import Base, get_db  # noqa: E402
from app.core.deps import get_current_user  # noqa: E402
from app.domains.businesses.models import Business  # noqa: E402
from app.domains.seo_config.fomo_models import ConversionEvent  # noqa: E402
from app.domains.seo_config.models import PublicationLink  # noqa: E402
from app.domains.seo_config.fomo_service import FOMAConversionService  # noqa: E402
from app.domains.seo_config.router import router  # noqa: E402
from app.domains.seo_config.webhook_models import ConversionWebhookPayload, WebhookEvent  # noqa: E402
from app.domains.seo_config.webhook_service import WebhookService  # noqa: E402
from app.domains.users.models import User  # noqa: E402


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        for t in (
            User.__table__, Business.__table__, PublicationLink.__table__,
            ConversionEvent.__table__, WebhookEvent.__table__,
        ):
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        yield type("Env", (), {"db": db, "Session": Session})()
    await engine.dispose()


async def make_user(db):
    user = User(email=f"{uuid4()}@example.com", hashed_password="x", full_name="Test User")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def make_business(db, owner):
    business = Business(user_id=owner.id, name="Negocio de prueba")
    db.add(business)
    await db.commit()
    await db.refresh(business)
    return business


async def make_link(db, business_id, url="https://example.com/producto"):
    link = PublicationLink(business_id=business_id, url=url, title="Producto", platform_source="custom")
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


def build_client(env, current_user):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/businesses")

    async def override_db():
        yield env.db

    async def override_user():
        return current_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    return TestClient(app)


# ── Ownership gate ──

async def test_owner_can_read_their_own_business(env):
    owner = await make_user(env.db)
    business = await make_business(env.db, owner)
    client = build_client(env, owner)

    resp = client.get(f"/api/v1/businesses/{business.id}/seo-config/publication-links")
    assert resp.status_code == 200


async def test_a_different_user_is_forbidden_from_another_businesss_data(env):
    owner = await make_user(env.db)
    business = await make_business(env.db, owner)
    intruder = await make_user(env.db)
    client = build_client(env, intruder)

    resp = client.get(f"/api/v1/businesses/{business.id}/seo-config/publication-links")
    assert resp.status_code == 403


async def test_a_different_user_cannot_write_to_another_businesss_data(env):
    owner = await make_user(env.db)
    business = await make_business(env.db, owner)
    intruder = await make_user(env.db)
    client = build_client(env, intruder)

    resp = client.patch(f"/api/v1/businesses/{business.id}/seo-config/global-toggle?enabled=false")
    assert resp.status_code == 403


async def test_nonexistent_business_is_404_not_403(env):
    user = await make_user(env.db)
    client = build_client(env, user)

    resp = client.get(f"/api/v1/businesses/{uuid4()}/seo-config/publication-links")
    assert resp.status_code == 404


# ── Generic conversion webhook ──

async def test_conversion_with_a_link_owned_by_the_business_is_tracked(env):
    owner = await make_user(env.db)
    business = await make_business(env.db, owner)
    link = await make_link(env.db, business.id)

    service = WebhookService(env.db)
    result = await service.ingest_conversion(
        business_id=business.id,
        platform="custom",
        payload=ConversionWebhookPayload(platform="custom", link_id=str(link.id), amount=42.5),
    )
    assert result["message"] == "Conversion tracked"

    events = (await env.db.execute(select(ConversionEvent))).scalars().all()
    assert len(events) == 1
    assert events[0].link_id == link.id
    assert events[0].conversion_value == 42.5

    logs = (await env.db.execute(select(WebhookEvent))).scalars().all()
    assert logs[0].event_type == "conversion"
    assert logs[0].signature_valid == "unverified"  # never fabricated as 'valid'


async def test_conversion_for_a_link_from_another_business_is_not_counted(env):
    owner_a = await make_user(env.db)
    business_a = await make_business(env.db, owner_a)
    owner_b = await make_user(env.db)
    business_b = await make_business(env.db, owner_b)
    other_link = await make_link(env.db, business_b.id)

    service = WebhookService(env.db)
    result = await service.ingest_conversion(
        business_id=business_a.id,
        platform="custom",
        payload=ConversionWebhookPayload(platform="custom", link_id=str(other_link.id), amount=999),
    )
    assert "no pertenece" in result["message"]
    assert (await env.db.execute(select(ConversionEvent))).scalars().all() == []

    logs = (await env.db.execute(select(WebhookEvent))).scalars().all()
    assert logs[0].event_type == "conversion_unmatched"


async def test_conversion_without_a_link_id_is_logged_but_not_counted(env):
    owner = await make_user(env.db)
    business = await make_business(env.db, owner)

    service = WebhookService(env.db)
    result = await service.ingest_conversion(
        business_id=business.id,
        platform="custom",
        payload=ConversionWebhookPayload(platform="custom", amount=10),
    )
    assert result["received"] is True
    assert (await env.db.execute(select(ConversionEvent))).scalars().all() == []


# ── Duplicate-webhook dedupe (DB constraint, not check-then-insert) ──

async def test_same_external_event_id_is_rejected_by_the_db_not_double_counted(env):
    """The check-then-insert race this replaces: two notifications for the same
    order committing close together could both pass a SELECT-based "does this
    exist?" check before either commits. Calling log_conversion twice with no
    SELECT in between proves the unique index (not a pre-check) is what
    actually stops the duplicate."""
    owner = await make_user(env.db)
    business = await make_business(env.db, owner)
    link = await make_link(env.db, business.id)
    # log_conversion's rollback (see below) expires every object the session
    # has loaded, `business`/`link` included — snapshot the plain ids first
    # rather than touching the ORM instances again afterwards.
    # (app/db/leads_bootstrap.py and the rollback_expires_orm_instances lesson
    # cover the same gotcha.)
    business_id, link_id = business.id, link.id

    service = FOMAConversionService(env.db)
    first = await service.log_conversion(
        business_id=business_id, link_id=link_id, platform_name="mercado-libre",
        conversion_value=100.0, external_listing_id="MLA111", external_event_id="9001",
    )
    assert first is not None

    second = await service.log_conversion(
        business_id=business_id, link_id=link_id, platform_name="mercado-libre",
        conversion_value=100.0, external_listing_id="MLA111", external_event_id="9001",
    )
    assert second is None  # rejected, not raised — caller decides what that means

    events = (await env.db.execute(select(ConversionEvent))).scalars().all()
    assert len(events) == 1

    # The session must still be usable after the rollback inside log_conversion.
    third = await service.log_conversion(
        business_id=business_id, link_id=link_id, platform_name="mercado-libre",
        conversion_value=50.0, external_listing_id="MLA111", external_event_id="9002",
    )
    assert third is not None
    assert len((await env.db.execute(select(ConversionEvent))).scalars().all()) == 2


async def test_conversions_without_an_external_event_id_are_never_deduped(env):
    """Most conversion sources have no stable per-event id — external_event_id
    stays NULL, and NULLs must not collide in the unique index."""
    owner = await make_user(env.db)
    business = await make_business(env.db, owner)
    link = await make_link(env.db, business.id)

    service = FOMAConversionService(env.db)
    for _ in range(3):
        event = await service.log_conversion(
            business_id=business.id, link_id=link.id, platform_name="custom", conversion_value=10.0,
        )
        assert event is not None

    assert len((await env.db.execute(select(ConversionEvent))).scalars().all()) == 3


async def test_conversion_payload_with_a_timestamp_does_not_crash_json_serialization(env):
    """payload.model_dump() (without mode="json") leaves a datetime object in the
    dict, which json.dumps() can't serialize — this used to blow up on any
    webhook that actually sent a timestamp."""
    from datetime import datetime

    owner = await make_user(env.db)
    business = await make_business(env.db, owner)
    link = await make_link(env.db, business.id)

    service = WebhookService(env.db)
    result = await service.ingest_conversion(
        business_id=business.id,
        platform="custom",
        payload=ConversionWebhookPayload(
            platform="custom", link_id=str(link.id), amount=1, timestamp=datetime.utcnow()
        ),
    )
    assert result["received"] is True
