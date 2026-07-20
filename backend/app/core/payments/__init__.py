"""
Payment Processing System — Production-grade payments module.

Core Components:
1. stripe_processor.py (700L): Stripe payment sessions, intents, refunds, webhooks
2. mercadopago_processor.py (600L): MercadoPago Checkout Pro, payment links, webhooks
3. crypto_processor.py (400L): USDT TRC20/BEP20, blockchain verification, exchange rates
4. payment_reconciliation.py (300L): Match payments with orders, trigger fulfillment
5. billing_history.py (250L): Transaction history, monthly summaries, CSV export
6. invoice_generator.py (250L): HTML/PDF invoices, email delivery
7. payout_manager.py (300L): Seller payouts, fee calculations, batch processing
8. compliance.py (200L): PCI-DSS, AML/KYC, transaction screening, audit logging
9. tests.py (400L): Comprehensive unit and integration tests

Features:
- Multi-payment provider support (Stripe, MercadoPago, Crypto)
- Webhook handling with signature verification
- PCI-DSS compliant (no card storage)
- Automatic payment reconciliation
- Seller payout management
- Compliance monitoring
- Comprehensive logging and audit trails

Usage:

    from backend.app.core.payments import (
        StripeProcessor,
        MercadoPagoProcessor,
        CryptoProcessor,
        PaymentReconciler,
        InvoiceGenerator,
        PayoutManager,
        ComplianceChecker,
    )

    # Create Stripe checkout
    checkout = StripeProcessor.create_checkout_session(
        customer_email="buyer@example.com",
        customer_name="John Doe",
        product_name="Product",
        amount_usd=99.99,
        order_id="order_123",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )

    # Handle Stripe webhook
    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    result = StripeWebhookHandler.handle_event(event)

    # Reconcile payment with order
    reconciliation = PaymentReconciler.reconcile_payment(
        db=db,
        payment_id=payment_intent_id,
        payment_provider="stripe",
        customer_email="buyer@example.com",
        amount_usd=99.99,
    )

    # Generate invoice
    invoice = InvoiceGenerator.generate_invoice(
        order_id="order_123",
        customer_name="John Doe",
        customer_email="john@example.com",
        items=[{"name": "Product", "qty": 1, "unit_price": 99.99}],
        amount_total=99.99,
    )

    # Calculate seller payout
    payout = PayoutManager.calculate_payout(gross_revenue=1000.0)

    # Validate customer and screen transaction
    validation = ComplianceChecker.validate_customer_data(
        customer_name="John Doe",
        customer_email="john@example.com",
    )
    screening = ComplianceChecker.screen_transaction(
        transaction_id="tx_123",
        customer_email="john@example.com",
        amount_usd=99.99,
    )

Environment Variables:

    # Stripe
    STRIPE_SECRET_KEY=sk_live_***
    STRIPE_PUBLISHABLE_KEY=pk_live_***
    STRIPE_WEBHOOK_SECRET=whsec_***

    # MercadoPago
    MERCADOPAGO_ACCESS_TOKEN=***
    MERCADOPAGO_PUBLIC_KEY=***
    MERCADOPAGO_WEBHOOK_SECRET=***

    # Crypto
    TRON_RPC_URL=https://api.trongrid.io
    BSC_RPC_URL=https://bsc-dataseed.binance.org
    DEPOSIT_WALLET_ADDRESS=TAbCd...

    # Compliance
    HIGH_VALUE_THRESHOLD=5000
    SUSPICIOUS_ACTIVITY_THRESHOLD=10000

Dependencies:

    stripe==7.4.0
    requests==2.31.0
    sqlalchemy==2.0.23
    reportlab>=3.6.0 (optional, for PDF generation)

Testing:

    pytest app/core/payments/tests.py -v
    pytest app/core/payments/tests.py -v --cov=app/core/payments
"""

from .stripe_processor import (
    StripeProcessor,
    StripeWebhookHandler,
    PaymentMethodType,
    WebhookEventType,
)
from .mercadopago_processor import (
    MercadoPagoProcessor,
    MercadoPagoWebhookHandler,
    CurrencyCode,
    PaymentStatus as MPPaymentStatus,
)
from .crypto_processor import (
    CryptoProcessor,
    CryptoDepositMonitor,
    Blockchain,
    TransactionStatus,
)
from .payment_reconciliation import (
    PaymentReconciler,
    FulfillmentOrchestrator,
    ReconciliationStatus,
    FulfillmentType,
)
from .billing_history import (
    BillingHistoryManager,
    TransactionType,
)
from .invoice_generator import (
    InvoiceGenerator,
    InvoiceStatus,
)
from .payout_manager import (
    PayoutManager,
    PayoutStatus,
    PayoutFrequency,
)
from .compliance import (
    ComplianceChecker,
    PciDssCompliance,
    ComplianceRisk,
)

__all__ = [
    # Stripe
    "StripeProcessor",
    "StripeWebhookHandler",
    "PaymentMethodType",
    "WebhookEventType",
    # MercadoPago
    "MercadoPagoProcessor",
    "MercadoPagoWebhookHandler",
    "CurrencyCode",
    "MPPaymentStatus",
    # Crypto
    "CryptoProcessor",
    "CryptoDepositMonitor",
    "Blockchain",
    "TransactionStatus",
    # Reconciliation
    "PaymentReconciler",
    "FulfillmentOrchestrator",
    "ReconciliationStatus",
    "FulfillmentType",
    # Billing
    "BillingHistoryManager",
    "TransactionType",
    # Invoices
    "InvoiceGenerator",
    "InvoiceStatus",
    # Payouts
    "PayoutManager",
    "PayoutStatus",
    "PayoutFrequency",
    # Compliance
    "ComplianceChecker",
    "PciDssCompliance",
    "ComplianceRisk",
]
