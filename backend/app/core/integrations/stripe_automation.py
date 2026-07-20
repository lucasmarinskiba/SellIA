"""
Stripe Payment Automation — Checkout automático, webhooks, refunds.

Flujo:
1. SellIA identifica buyer hot
2. Genera checkout link via Stripe
3. Buyer clickea, paga
4. Webhook confirma payment
5. Auto-trigger fulfillment (deliver product)
"""

import logging
import stripe
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class StripeAutomation:
    """Automatización completa Stripe checkout + webhooks."""

    def __init__(self, stripe_api_key: str, webhook_secret: str):
        stripe.api_key = stripe_api_key
        self.webhook_secret = webhook_secret

    # ========== CHECKOUT CREATION ==========

    async def create_checkout_session(
        self,
        product: Dict[str, Any],
        buyer: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Crea Stripe checkout session automáticamente.

        product: {id, name, price, description}
        buyer: {email, name, phone}
        metadata: {order_id, campaign, source, ...}
        """

        logger.info(f"Creating checkout for {buyer.get('email')}")

        try:
            # Validar que price > 0
            price = product.get("price", 0)
            if price <= 0:
                raise ValueError("Product price must be greater than 0")

            # Crear line item
            line_items = [
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": product.get("name"),
                            "description": product.get("description", ""),
                            "images": product.get("images", []),
                        },
                        "unit_amount": int(price * 100),
                    },
                    "quantity": 1,
                }
            ]

            # Metadata para tracking
            session_metadata = metadata or {}
            session_metadata.update({
                "product_id": product.get("id"),
                "buyer_email": buyer.get("email"),
                "buyer_phone": buyer.get("phone", ""),
                "source": "sellias_automation",
            })

            # Crear session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                customer_email=buyer.get("email"),
                client_reference_id=product.get("id"),  # Link to order
                success_url="https://sellia.com/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="https://sellia.com/cancel",
                metadata=session_metadata,
                billing_address_collection="required",
            )

            logger.info(f"Checkout created: {session.id}")

            return {
                "status": "success",
                "checkout_url": session.url,
                "session_id": session.id,
                "expires_at": datetime.fromtimestamp(session.expires_at).isoformat(),
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def create_subscription_checkout(
        self,
        plan: Dict[str, Any],
        buyer: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Crea checkout para suscripción recurrente.

        plan: {name, price, interval (month/year), description}
        """

        logger.info(f"Creating subscription checkout for {buyer.get('email')}")

        try:
            # Crear product si no existe
            product = stripe.Product.create(
                name=plan.get("name"),
                description=plan.get("description", ""),
            )

            # Crear price con recurrencia
            price = stripe.Price.create(
                product=product.id,
                currency="usd",
                unit_amount=int(plan.get("price", 0) * 100),
                recurring={"interval": plan.get("interval", "month")},
            )

            # Crear subscription session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": price.id, "quantity": 1}],
                mode="subscription",
                customer_email=buyer.get("email"),
                success_url="https://sellia.com/subscription/success",
                cancel_url="https://sellia.com/subscription/cancel",
                metadata={
                    "buyer_email": buyer.get("email"),
                    "plan_name": plan.get("name"),
                },
            )

            logger.info(f"Subscription checkout created: {session.id}")

            return {
                "status": "success",
                "checkout_url": session.url,
                "session_id": session.id,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription error: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ========== WEBHOOK HANDLING ==========

    async def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Maneja webhooks de Stripe con verificación de firma obligatoria.

        SECURITY: Siempre verifica firma del webhook. Sin firma válida, rechaza.
        """

        logger.info("Processing Stripe webhook")

        # P0: Sin firma verificada, rechazar webhook inmediatamente
        if not sig_header:
            logger.warning("Webhook rejected: missing signature header")
            return {
                "status": "error",
                "error": "Invalid signature",
                "code": "missing_signature"
            }

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return {"status": "error", "error": "Invalid payload", "code": "invalid_payload"}
        except stripe.error.SignatureError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return {"status": "error", "error": "Invalid signature", "code": "invalid_signature"}

        # Handle event
        if event["type"] == "checkout.session.completed":
            return await self._handle_checkout_complete(event["data"]["object"])

        elif event["type"] == "payment_intent.succeeded":
            return await self._handle_payment_success(event["data"]["object"])

        elif event["type"] == "payment_intent.payment_failed":
            return await self._handle_payment_failed(event["data"]["object"])

        elif event["type"] == "charge.refunded":
            return await self._handle_refund(event["data"]["object"])

        elif event["type"] == "customer.subscription.updated":
            return await self._handle_subscription_update(event["data"]["object"])

        else:
            logger.info(f"Unhandled event type: {event['type']}")
            return {"status": "ignored", "event_type": event["type"]}

    async def _handle_checkout_complete(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja checkout completado."""

        logger.info(f"Checkout completed: {session['id']}")

        metadata = session.get("metadata", {})
        customer_email = session.get("customer_details", {}).get("email", "")

        # TODO: Trigger fulfillment (entrega producto)
        fulfillment_result = await self._trigger_fulfillment(
            order_id=session["id"],
            product_id=metadata.get("product_id"),
            customer_email=customer_email,
            amount_paid=session["amount_total"] / 100,
        )

        return {
            "status": "success",
            "event": "checkout_complete",
            "session_id": session["id"],
            "fulfillment": fulfillment_result,
        }

    async def _handle_payment_success(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja payment exitoso. Persiste en DB."""

        logger.info(f"Payment succeeded: {payment_intent['id']}")

        metadata = payment_intent.get("metadata", {})

        # P1: Guardar payment en DB real
        try:
            from app.core.database import AsyncSessionLocal
            from app.core.database.payment_models import Payment
            from datetime import datetime

            async with AsyncSessionLocal() as db:
                payment = Payment(
                    id=payment_intent["id"],
                    order_id=metadata.get("order_id"),
                    customer_email=payment_intent.get("receipt_email", ""),
                    amount=payment_intent["amount"] / 100,
                    currency=payment_intent["currency"].upper(),
                    status="succeeded",
                    payment_method=payment_intent.get("payment_method", "unknown"),
                    stripe_payment_intent_id=payment_intent["id"],
                    stripe_charge_id=payment_intent.get("charges", {}).get("data", [{}])[0].get("id"),
                    receipt_url=payment_intent.get("receipt_email"),
                    completed_at=datetime.utcnow(),
                )
                db.add(payment)
                await db.commit()
                logger.info(f"Payment {payment_intent['id']} saved to database")
        except Exception as e:
            logger.error(f"Failed to save payment to DB: {str(e)}")
            # No fallar el webhook, pero loguear el error

        return {
            "status": "success",
            "event": "payment_success",
            "amount": payment_intent["amount"] / 100,
            "currency": payment_intent["currency"],
            "payment_id": payment_intent["id"],
        }

    async def _handle_payment_failed(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja payment fallido."""

        logger.warning(f"Payment failed: {payment_intent['id']}")

        # TODO: Notify buyer, retry logic
        return {
            "status": "failed",
            "event": "payment_failed",
            "reason": payment_intent.get("last_payment_error", {}).get("message", "Unknown"),
        }

    async def _handle_refund(self, charge: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja refund."""

        logger.info(f"Refund processed: {charge['id']}")

        # TODO: Update order status, notify buyer

        return {
            "status": "success",
            "event": "refund",
            "amount_refunded": charge.get("amount_refunded", 0) / 100,
        }

    async def _handle_subscription_update(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja subscription update."""

        logger.info(f"Subscription updated: {subscription['id']}")

        # TODO: Update customer subscription status

        return {
            "status": "success",
            "event": "subscription_update",
            "status_value": subscription["status"],
        }

    # ========== FULFILLMENT TRIGGER ==========

    async def _trigger_fulfillment(
        self,
        order_id: str,
        product_id: str,
        customer_email: str,
        amount_paid: float,
    ) -> Dict[str, Any]:
        """
        Dispara fulfillment (entrega) automáticamente post-pago.

        Para productos digitales: envía link
        Para físicos: genera shipping label
        """

        logger.info(f"Triggering fulfillment for order {order_id}")

        # TODO: Determinar tipo producto (digital vs físico)
        # TODO: Si digital → email link
        # TODO: Si físico → generar shipping label

        return {
            "status": "triggered",
            "order_id": order_id,
            "customer_email": customer_email,
            "amount_paid": amount_paid,
        }

    # ========== REFUND AUTOMATION ==========

    async def process_refund(
        self,
        payment_intent_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Procesa refund automáticamente.
        """

        logger.info(f"Processing refund for {payment_intent_id}")

        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                reason=reason or "requested_by_customer",
            )

            logger.info(f"Refund created: {refund.id}")

            return {
                "status": "success",
                "refund_id": refund.id,
                "amount": refund.amount / 100,
                "status_value": refund.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Refund error: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ========== INVOICE AUTOMATION ==========

    async def create_invoice(
        self,
        customer_email: str,
        amount: float,
        description: str,
        due_date_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Crea invoice automáticamente (para pagos diferidos).
        """

        logger.info(f"Creating invoice for {customer_email}")

        try:
            # Obtener o crear customer
            customers = stripe.Customer.list(email=customer_email, limit=1)

            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(email=customer_email)

            # Crear invoice item
            stripe.InvoiceItem.create(
                customer=customer.id,
                amount=int(amount * 100),
                currency="usd",
                description=description,
            )

            # Crear invoice
            invoice = stripe.Invoice.create(
                customer=customer.id,
                due_date=int((datetime.now() + timedelta(days=due_date_days)).timestamp()),
                auto_advance=True,
            )

            logger.info(f"Invoice created: {invoice.id}")

            return {
                "status": "success",
                "invoice_id": invoice.id,
                "payment_url": invoice.hosted_invoice_url,
                "due_date": datetime.fromtimestamp(invoice.due_date).isoformat() if invoice.due_date else None,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Invoice error: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ========== CUSTOMER MANAGEMENT ==========

    async def create_customer(
        self,
        email: str,
        name: str,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Crea customer en Stripe.
        """

        logger.info(f"Creating customer: {email}")

        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                phone=phone,
                metadata=metadata or {},
            )

            return {
                "status": "success",
                "customer_id": customer.id,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Customer creation error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def get_customer_balance(self, customer_id: str) -> Dict[str, Any]:
        """
        Obtiene balance/history de customer.
        """

        try:
            customer = stripe.Customer.retrieve(customer_id)

            invoices = stripe.Invoice.list(customer=customer_id, limit=10)
            charges = stripe.Charge.list(customer=customer_id, limit=10)

            return {
                "status": "success",
                "customer_id": customer_id,
                "email": customer.email,
                "total_charges": sum(c.amount for c in charges.data) / 100,
                "invoices_count": len(invoices.data),
                "recent_invoices": [
                    {
                        "id": inv.id,
                        "amount": inv.amount_paid / 100,
                        "date": datetime.fromtimestamp(inv.created).isoformat(),
                    }
                    for inv in invoices.data[:5]
                ],
            }

        except stripe.error.StripeError as e:
            logger.error(f"Get balance error: {str(e)}")
            return {"status": "error"}
