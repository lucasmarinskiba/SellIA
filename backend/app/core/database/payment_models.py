"""
Payment Models — SQLAlchemy ORM para órdenes, pagos y catálogo.
"""

from sqlalchemy import Column, String, Float, DateTime, JSON, Enum, Integer, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class Product(Base):
    """Modelo para productos en catálogo."""

    __tablename__ = "products"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text)
    price_usd = Column(Float, nullable=False)
    stock_qty = Column(Integer, default=0)
    sku = Column(String(100), unique=True, index=True)
    category = Column(String(100), index=True)
    images = Column(JSON, default=[])  # URLs de imágenes
    tags = Column(JSON, default=[])

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    """Modelo para órdenes."""

    __tablename__ = "orders"

    id = Column(String(50), primary_key=True)  # Stripe session ID
    customer_email = Column(String(255), index=True)
    customer_name = Column(String(255))
    customer_phone = Column(String(20), nullable=True)

    product_id = Column(String(50), index=True)
    product_name = Column(String(255))
    product_price = Column(Float)

    amount = Column(Float)  # Total paid
    currency = Column(String(3), default="USD")

    status = Column(String(50), default="pending")  # pending, payment_received, shipped, delivered, refunded
    payment_status = Column(String(50), default="pending")  # pending, succeeded, failed

    stripe_session_id = Column(String(255), unique=True, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True)

    # Shipping info
    shipping_address = Column(JSON, nullable=True)
    shipping_label_url = Column(String(500), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(50), nullable=True)  # DHL, FedEx, UPS, etc

    # Fulfillment
    fulfilled = Column(Boolean, default=False)
    fulfilled_at = Column(DateTime, nullable=True)
    delivery_type = Column(String(50))  # digital (email), physical (shipping), service

    # Refund
    refunded = Column(Boolean, default=False)
    refund_id = Column(String(255), nullable=True)
    refund_amount = Column(Float, nullable=True)
    refund_reason = Column(String(255), nullable=True)

    # Metadata
    source = Column(String(50))  # sellias_automation, manual, api
    campaign = Column(String(255), nullable=True)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(Base):
    """Modelo para transacciones de pago."""

    __tablename__ = "payments"

    id = Column(String(50), primary_key=True)  # Stripe payment intent ID
    order_id = Column(String(50), ForeignKey("orders.id"), index=True)

    customer_email = Column(String(255), index=True)
    amount = Column(Float)
    currency = Column(String(3), default="USD")

    status = Column(String(50))  # succeeded, failed, processing, cancelled
    failure_reason = Column(String(255), nullable=True)

    payment_method = Column(String(50))  # card, ach_transfer, etc
    card_last_four = Column(String(4), nullable=True)
    card_brand = Column(String(50), nullable=True)  # visa, mastercard, amex

    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    stripe_charge_id = Column(String(255), nullable=True)

    receipt_url = Column(String(500), nullable=True)
    invoice_url = Column(String(500), nullable=True)

    # Encryption for sensitive payment details (encrypted in DB, decrypted in app)
    billing_details_encrypted = Column(String(500), nullable=True)  # Encrypted JSON
    payment_metadata_encrypted = Column(String(500), nullable=True)  # Encrypted JSON

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)


class Refund(Base):
    """Modelo para refunds."""

    __tablename__ = "refunds"

    id = Column(String(50), primary_key=True)  # Stripe refund ID
    order_id = Column(String(50), ForeignKey("orders.id"), index=True)
    payment_id = Column(String(50), ForeignKey("payments.id"))

    customer_email = Column(String(255), index=True)
    amount = Column(Float)
    currency = Column(String(3), default="USD")

    status = Column(String(50))  # succeeded, failed, processing
    reason = Column(String(50))  # requested_by_customer, duplicate, fraudulent, etc

    stripe_refund_id = Column(String(255), unique=True, index=True)
    stripe_charge_id = Column(String(255), index=True)

    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)


class Invoice(Base):
    """Modelo para invoices."""

    __tablename__ = "invoices"

    id = Column(String(50), primary_key=True)  # Stripe invoice ID
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=True, index=True)

    customer_email = Column(String(255), index=True)
    customer_name = Column(String(255))

    amount = Column(Float)
    currency = Column(String(3), default="USD")

    status = Column(String(50))  # draft, open, paid, void, uncollectible
    due_date = Column(DateTime, nullable=True)

    description = Column(String(500))
    items = Column(JSON)  # Line items

    stripe_invoice_id = Column(String(255), unique=True, index=True)
    stripe_customer_id = Column(String(255), index=True)

    payment_url = Column(String(500), nullable=True)
    pdf_url = Column(String(500), nullable=True)

    paid_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Subscription(Base):
    """Modelo para subscripciones recurrentes."""

    __tablename__ = "subscriptions"

    id = Column(String(50), primary_key=True)  # Stripe subscription ID
    customer_email = Column(String(255), index=True)
    customer_name = Column(String(255))

    plan_name = Column(String(255))
    plan_price = Column(Float)
    interval = Column(String(50))  # month, year

    status = Column(String(50))  # active, past_due, canceled, unpaid

    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)

    stripe_subscription_id = Column(String(255), unique=True, index=True)
    stripe_customer_id = Column(String(255), index=True)

    auto_renew = Column(Boolean, default=True)
    cancel_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaymentWebhookLog(Base):
    """Log de webhooks procesados."""

    __tablename__ = "payment_webhook_logs"

    id = Column(String(50), primary_key=True)
    event_id = Column(String(255), unique=True, index=True)  # Stripe event ID
    event_type = Column(String(100), index=True)  # checkout.session.completed, etc

    status = Column(String(50))  # processed, failed, pending
    error = Column(String(500), nullable=True)

    payload = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TravelMode(Base):
    """Modelo para travel mode — Usuario avisa que se va de viaje."""

    __tablename__ = "travel_modes"

    id = Column(String(50), primary_key=True)
    seller_id = Column(String(255), index=True, nullable=False, unique=True)
    is_active = Column(Boolean, default=False, index=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    calendar_blocked = Column(Boolean, default=False)
    auto_response_active = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
