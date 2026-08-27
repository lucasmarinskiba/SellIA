"""Purchase-intent detection → checkout generation.

Closes the loop between "lead calificado por el bot" and "venta cobrada":
when an inbound message signals the customer wants to buy, resolve which
catalog item they mean, generate a MercadoPago checkout link tied to the
conversation, and send it back through whatever channel the conversation
came from (WhatsApp, ManyChat, etc).

Deliberately conservative: only auto-generates a checkout when the catalog
item can be resolved unambiguously (single-item catalog, or the item name
is clearly mentioned in the message). When it can't tell which product the
customer means, it does nothing rather than risk sending the wrong link —
the qualification pitch from process_incoming_message still goes out.
"""

import re
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.catalogs.models import CatalogItem
from app.domains.channels.models import Conversation

logger = get_logger(__name__)

# Spanish + English buy-intent signals. Kept as plain substring checks — no
# LLM dependency, so this still works even when a business hasn't configured
# an LLM key (Groq/OpenAI/Anthropic) for their conversations.
_BUY_INTENT_PATTERNS = [
    r"\bquiero comprar", r"\bcomo pago", r"\bcómo pago", r"\bdonde pago", r"\bdónde pago",
    r"\blink de pago", r"\bmandame el link", r"\bmándame el link", r"\bme lo llevo",
    r"\bquiero reservar", r"\bconfirmo la compra", r"\bdale.{0,10}va\b", r"\bquiero pagar",
    r"\bcuanto sale\b.{0,20}(lo compro|me lo llevo)", r"\bwant to buy", r"\bhow do i pay",
    r"\bpayment link", r"\bi'?ll take it", r"\bcheckout\b",
]
_BUY_INTENT_RE = re.compile("|".join(_BUY_INTENT_PATTERNS), re.IGNORECASE)


def has_buy_intent(message_text: str) -> bool:
    """Cheap keyword heuristic — deliberately not an LLM call so it never
    blocks on missing/failed LLM providers."""
    if not message_text:
        return False
    return bool(_BUY_INTENT_RE.search(message_text))


async def _resolve_catalog_item(
    db: AsyncSession, business_id: UUID, message_text: str
) -> Optional[CatalogItem]:
    """Pick the catalog item the customer means, or None if ambiguous."""
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.business_id == business_id,
            CatalogItem.is_available == True,
            CatalogItem.is_active == True,
        )
    )
    items = result.scalars().all()

    if not items:
        return None
    if len(items) == 1:
        return items[0]

    # Multiple products — only proceed if the message clearly names one.
    text_lower = message_text.lower()
    matches = [item for item in items if item.name and item.name.lower() in text_lower]
    if len(matches) == 1:
        return matches[0]

    logger.info(
        f"Buy intent detected but catalog item ambiguous for business {business_id} "
        f"({len(items)} items, {len(matches)} name matches) — skipping auto-checkout"
    )
    return None


async def _has_pending_or_paid_checkout(db: AsyncSession, conversation_id: UUID) -> bool:
    """Avoid spamming a new payment link on every message once one is out."""
    from app.domains.payments.payment_models import Transaction, TransactionStatus

    result = await db.execute(
        select(Transaction.id).where(
            Transaction.conversation_id == conversation_id,
            Transaction.status.in_([TransactionStatus.PROCESSING, TransactionStatus.APPROVED]),
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def maybe_trigger_checkout(
    db: AsyncSession,
    business_id: UUID,
    conversation: Conversation,
    message_text: str,
) -> Optional[dict[str, Any]]:
    """Entry point called from the inbound-message pipeline.

    Returns the checkout dict ({checkout_url, transaction_id, ...}) if one
    was created and should be sent to the customer, else None. Never raises —
    all failure paths return None so a payments hiccup can't break message
    ingestion (mirrors every other best-effort block in process_incoming_message).
    """
    try:
        if not has_buy_intent(message_text):
            return None

        if await _has_pending_or_paid_checkout(db, conversation.id):
            logger.debug(f"Conversation {conversation.id} already has a pending/paid checkout — skipping")
            return None

        item = await _resolve_catalog_item(db, business_id, message_text)
        if not item:
            return None

        from app.domains.payments.payment_service import PaymentService

        checkout = await PaymentService.create_mercadopago_checkout(
            business_id=business_id,
            customer_email=conversation.lead_email or "cliente@example.com",
            customer_name=conversation.lead_name or "Cliente",
            items=[{
                "name": item.name,
                "quantity": 1,
                "unit_price": float(item.price),
            }],
            amount=item.price,
            currency=item.currency or "ARS",
            conversation_id=conversation.id,
            db=db,
        )

        if checkout.get("status") == "error":
            logger.warning(f"Checkout creation failed for conversation {conversation.id}: {checkout.get('error')}")
            return None

        if not checkout.get("checkout_url"):
            logger.warning(f"Checkout created without a URL for conversation {conversation.id}: {checkout}")
            return None

        logger.info(
            f"Checkout generated for conversation {conversation.id}: "
            f"item={item.name} amount={item.price}{item.currency} url={checkout['checkout_url']}"
        )
        checkout["item_name"] = item.name
        checkout["amount"] = float(item.price)
        checkout["currency"] = item.currency or "ARS"
        return checkout

    except Exception as e:
        logger.error(f"maybe_trigger_checkout error for conversation {conversation.id}: {e}")
        return None
