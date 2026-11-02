"""Who a post-visit message is sent from, decided per business.

Production sends only from the business's own verified domain. A shared sending domain carries every business's
reputation: one business's spam would reach all the others, so it is not used there.

A test environment may set ALLOW_GLOBAL_SENDER_FOR_TESTING and a GLOBAL_SENDER_EMAIL. Only then, and only for a
business with no verified domain yet, the global address is used.

Replies go to the business's contact email from its profile. Without one the message is not sent: the text says
"respondé este mensaje", so an unanswerable address would break the promise.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.business_context.models import BusinessContext
from app.domains.businesses.models import Business
from app.domains.sequences.sending_domain_models import BusinessSendingDomain


@dataclass(frozen=True)
class SenderIdentity:
    from_name: str
    from_email: str
    reply_to: str


async def resolve_identity(
    db: AsyncSession,
    business: Business,
    *,
    allow_global_sender: bool,
    global_sender_email: str | None,
) -> SenderIdentity | str:
    """The identity to send from, or the reason it cannot be resolved yet (the message then stays pending)."""
    contact = (
        await db.execute(
            select(BusinessContext.contact_email).where(BusinessContext.business_id == business.id)
        )
    ).scalars().first()
    if not contact:
        return "el negocio no tiene email de contacto en su perfil"

    domain = (
        await db.execute(select(BusinessSendingDomain).where(BusinessSendingDomain.business_id == business.id))
    ).scalars().first()
    if domain is not None and domain.status == "verified":
        return SenderIdentity(
            from_name=business.name,
            from_email=f"{domain.local_part}@{domain.domain}",
            reply_to=contact,
        )

    if allow_global_sender and global_sender_email:
        return SenderIdentity(from_name=business.name, from_email=global_sender_email, reply_to=contact)
    return "falta verificar el dominio de envío del negocio"
