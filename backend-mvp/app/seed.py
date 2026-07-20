"""Seed demo data · run via `python -m app.seed`."""
import asyncio
import logging
import uuid

from sqlalchemy import select

from app.core.logging import setup_logging
from app.core.security import hash_password
from app.db.models import (
    Channel,
    ChannelKind,
    Contact,
    Conversation,
    Deal,
    DealStage,
    Message,
    MessageRole,
    Tenant,
    User,
    UserRole,
)
from app.db.session import AsyncSessionLocal


logger = logging.getLogger(__name__)


DEMO_EMAIL = "demo@sellia.app"
DEMO_PASSWORD = "demo-pw-change-me"


async def seed() -> None:
    setup_logging()
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        if existing.scalar_one_or_none():
            logger.warning("seed_already_exists · skipping")
            return

        # Tenant
        tenant = Tenant(name="Demo Boutique", plan="pro")
        db.add(tenant)
        await db.flush()

        # Owner
        owner = User(
            tenant_id=tenant.id,
            email=DEMO_EMAIL,
            name="Demo Owner",
            password_hash=hash_password(DEMO_PASSWORD),
            role=UserRole.OWNER,
        )
        # Team member
        admin = User(
            tenant_id=tenant.id,
            email="admin@sellia.app",
            name="Demo Admin",
            password_hash=hash_password(DEMO_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add_all([owner, admin])
        await db.flush()

        # Channel
        wa = Channel(
            tenant_id=tenant.id,
            kind=ChannelKind.WHATSAPP,
            external_id="demo-phone-id",
            config={},
        )
        db.add(wa)
        await db.flush()

        # Contacts + deals
        contacts_data = [
            ("Ana Suárez", "+5491155551234", "ana@example.com"),
            ("Tomás N.", "+5491155555678", "tomas@example.com"),
            ("María L.", "+5491155559876", "maria@example.com"),
            ("Pedro K.", "+5491155553333", "pedro@example.com"),
            ("Lucía F.", "+5491155557777", "lucia@example.com"),
        ]

        contacts = []
        for name, phone, email in contacts_data:
            c = Contact(tenant_id=tenant.id, name=name, phone=phone, email=email)
            contacts.append(c)
            db.add(c)
        await db.flush()

        deals_data = [
            (contacts[0].id, "Pack Premium", 98000, DealStage.WON,         95),
            (contacts[1].id, "Plan anual",   240000, DealStage.NEGOTIATION, 78),
            (contacts[2].id, "Carrito x3",   124000, DealStage.QUALIFIED,   55),
            (contacts[3].id, "Demo agendada", 32000, DealStage.PROSPECT,    25),
            (contacts[4].id, "Cierre B2B",  184700, DealStage.WON,         100),
        ]
        for cid, title, val, stage, prob in deals_data:
            db.add(Deal(
                tenant_id=tenant.id,
                contact_id=cid,
                title=title,
                value_cents=val,
                currency="ARS",
                stage=stage,
                probability=prob,
            ))

        # Sample conversation
        conv = Conversation(tenant_id=tenant.id, channel_id=wa.id, contact_id=contacts[0].id)
        db.add(conv)
        await db.flush()

        db.add_all([
            Message(tenant_id=tenant.id, conversation_id=conv.id, role=MessageRole.INBOUND,
                    body="Hola! Estoy interesada en el pack premium"),
            Message(tenant_id=tenant.id, conversation_id=conv.id, role=MessageRole.OUTBOUND_AI,
                    body="Hola Ana! Gracias por escribir. El Pack Premium incluye..."),
        ])

        await db.commit()
        logger.info("seed_done", extra={"tenant_id": str(tenant.id), "email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        print(f"\n✓ Demo tenant created · login: {DEMO_EMAIL} / {DEMO_PASSWORD}\n")


if __name__ == "__main__":
    asyncio.run(seed())
