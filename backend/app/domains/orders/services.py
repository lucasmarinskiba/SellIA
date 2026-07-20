"""Orders Services — E-commerce Webhook Processing.

Handles conversion of e-commerce webhooks (Shopify, MercadoLibre, Amazon)
into unified Order records with revenue attribution.
"""

import uuid
from typing import Any, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.channels.models import ChannelConnection, Conversation
from app.domains.channels.schemas import WebhookPayload
from app.domains.orders.models import Order, OrderStatus, PaymentStatus
from app.domains.catalogs.models import CatalogItem
from app.core.logger import get_logger

logger = get_logger(__name__)


class EcommerceWebhookProcessor:
    """Process e-commerce webhooks into Order records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_order_webhook(
        self,
        channel: ChannelConnection,
        conversation: Conversation,
        payload: WebhookPayload,
    ) -> Optional[Order]:
        """Process an order-related webhook and create/update an Order."""
        platform = channel.platform.value
        extra = payload.extra_data or {}

        if platform == "shopify":
            return await self._process_shopify(channel, conversation, extra)
        elif platform == "mercadolibre":
            return await self._process_mercadolibre(channel, conversation, extra)
        elif platform == "amazon":
            return await self._process_amazon(channel, conversation, extra)

        return None

    async def _process_shopify(
        self,
        channel: ChannelConnection,
        conversation: Conversation,
        extra: dict[str, Any],
    ) -> Optional[Order]:
        order_id = str(extra.get("id", ""))
        if not order_id:
            return None

        total_price = Decimal(str(extra.get("total_price", "0")))
        currency = extra.get("currency", "USD")
        financial_status = extra.get("financial_status", "pending")
        fulfillment_status = extra.get("fulfillment_status")
        name = extra.get("name", f"#{order_id}")

        customer = extra.get("customer", {})
        line_items = extra.get("line_items", [])

        order = await self._upsert_order(
            business_id=channel.business_id,
            conversation_id=conversation.id,
            external_id=order_id,
            external_platform="shopify",
            order_number=name,
            total_amount=total_price,
            currency=currency,
            status=self._map_shopify_status(financial_status, fulfillment_status),
            payment_status=self._map_payment_status(financial_status),
            customer_name=customer.get("first_name", "") + " " + customer.get("last_name", ""),
            customer_email=customer.get("email"),
            customer_phone=customer.get("phone"),
            items=[{"name": li.get("title", ""), "qty": li.get("quantity", 1), "price": str(li.get("price", "0")), "sku": li.get("sku", "")} for li in line_items],
            source_channel="shopify",
        )
        return order

    async def _process_mercadolibre(
        self,
        channel: ChannelConnection,
        conversation: Conversation,
        extra: dict[str, Any],
    ) -> Optional[Order]:
        order_data = extra.get("data", {}).get("order", {})
        order_id = str(order_data.get("id", ""))
        if not order_id:
            return None

        total = Decimal(str(order_data.get("total_amount", "0")))
        currency = order_data.get("currency_id", "ARS")
        status = order_data.get("status", "pending")
        buyer = order_data.get("buyer", {})
        items = order_data.get("order_items", [])

        order = await self._upsert_order(
            business_id=channel.business_id,
            conversation_id=conversation.id,
            external_id=order_id,
            external_platform="mercadolibre",
            order_number=order_id,
            total_amount=total,
            currency=currency,
            status=self._map_ml_status(status),
            payment_status=PaymentStatus.PENDING,
            customer_name=buyer.get("nickname", ""),
            customer_email=buyer.get("email"),
            items=[{"name": i.get("item", {}).get("title", ""), "qty": i.get("quantity", 1), "price": str(i.get("unit_price", "0")), "sku": i.get("item", {}).get("seller_sku", "")} for i in items],
            source_channel="mercadolibre",
        )
        return order

    async def _process_amazon(
        self,
        channel: ChannelConnection,
        conversation: Conversation,
        extra: dict[str, Any],
    ) -> Optional[Order]:
        payload_data = extra.get("Payload", {})
        order_change = payload_data.get("OrderChangeNotification", {}).get("OrderChange", {})
        order_id = str(order_change.get("OrderId", ""))
        if not order_id:
            return None

        order_items = order_change.get("OrderItems", [])
        total = Decimal("0")
        items = []
        for item in order_items:
            price = Decimal(str(item.get("ItemPrice", {}).get("Amount", "0")))
            qty = item.get("QuantityOrdered", 1)
            total += price * qty
            items.append({
                "name": item.get("Title", ""),
                "qty": qty,
                "price": str(price),
                "sku": item.get("SellerSKU", ""),
            })

        order = await self._upsert_order(
            business_id=channel.business_id,
            conversation_id=conversation.id,
            external_id=order_id,
            external_platform="amazon",
            order_number=order_id,
            total_amount=total,
            currency=order_change.get("OrderTotal", {}).get("CurrencyCode", "USD"),
            status=self._map_amazon_status(order_change.get("OrderStatus", "")),
            payment_status=PaymentStatus.PENDING,
            customer_name="Comprador Amazon",
            customer_email=order_change.get("BuyerEmail"),
            items=items,
            source_channel="amazon",
        )
        return order

    async def _upsert_order(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        external_id: str,
        external_platform: str,
        order_number: str,
        total_amount: Decimal,
        currency: str,
        status: OrderStatus,
        payment_status: PaymentStatus,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        items: Optional[list] = None,
        source_channel: Optional[str] = None,
    ) -> Order:
        """Upsert an Order by external_id + external_platform."""
        result = await self.db.execute(
            select(Order).where(
                Order.business_id == business_id,
                Order.external_id == external_id,
                Order.external_platform == external_platform,
            )
        )
        order = result.scalar_one_or_none()

        if not order:
            order = Order(
                business_id=business_id,
                conversation_id=conversation_id,
                external_id=external_id,
                external_platform=external_platform,
                order_number=order_number,
                total_amount=total_amount,
                currency=currency,
                status=status,
                payment_status=payment_status,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                items=items or [],
                source_channel=source_channel,
                first_touch_channel=source_channel,
                last_touch_channel=source_channel,
            )
            self.db.add(order)
        else:
            order.status = status
            order.payment_status = payment_status
            order.total_amount = total_amount
            order.customer_name = customer_name or order.customer_name
            order.customer_email = customer_email or order.customer_email
            if items:
                order.items = items
            order.last_touch_channel = source_channel

        await self.db.commit()
        await self.db.refresh(order)
        logger.info(f"Order upserted: {order.id} ({external_platform}:{external_id})")
        return order

    @staticmethod
    def _map_shopify_status(financial: str, fulfillment: Optional[str]) -> OrderStatus:
        if financial == "paid":
            return OrderStatus.PAID
        if financial == "refunded":
            return OrderStatus.REFUNDED
        if fulfillment == "shipped":
            return OrderStatus.SHIPPED
        if fulfillment == "delivered":
            return OrderStatus.DELIVERED
        if financial == "voided":
            return OrderStatus.CANCELLED
        return OrderStatus.PENDING

    @staticmethod
    def _map_payment_status(financial: str) -> PaymentStatus:
        if financial == "paid":
            return PaymentStatus.COMPLETED
        if financial == "refunded":
            return PaymentStatus.REFUNDED
        if financial == "partially_paid":
            return PaymentStatus.PROCESSING
        return PaymentStatus.PENDING

    @staticmethod
    def _map_ml_status(status: str) -> OrderStatus:
        status_map = {
            "paid": OrderStatus.PAID,
            "cancelled": OrderStatus.CANCELLED,
            "confirmed": OrderStatus.PENDING,
            "payment_required": OrderStatus.PENDING,
        }
        return status_map.get(status, OrderStatus.PENDING)

    @staticmethod
    def _map_amazon_status(status: str) -> OrderStatus:
        status_map = {
            "Shipped": OrderStatus.SHIPPED,
            "Delivered": OrderStatus.DELIVERED,
            "Cancelled": OrderStatus.CANCELLED,
            "Pending": OrderStatus.PENDING,
        }
        return status_map.get(status, OrderStatus.PENDING)
