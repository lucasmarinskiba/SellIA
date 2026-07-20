"""
Payment Processing Tests — Unit and integration tests for all payment modules.

Run:
    pytest app/core/payments/tests.py -v
    pytest app/core/payments/tests.py -v --cov=app/core/payments
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Import all payment modules
from stripe_processor import (
    StripeProcessor,
    StripeWebhookHandler,
    WebhookEventType,
)
from mercadopago_processor import (
    MercadoPagoProcessor,
    MercadoPagoWebhookHandler,
    CurrencyCode,
)
from crypto_processor import (
    CryptoProcessor,
    Blockchain,
)
from payment_reconciliation import (
    PaymentReconciler,
    FulfillmentOrchestrator,
)
from billing_history import BillingHistoryManager
from invoice_generator import InvoiceGenerator
from payout_manager import PayoutManager
from compliance import ComplianceChecker, PciDssCompliance


# ============= STRIPE TESTS =============

class TestStripeProcessor:
    """Stripe payment processor tests."""

    def test_create_checkout_session_valid(self):
        """Test creating a valid checkout session."""
        with patch("stripe.checkout.Session.create") as mock_create:
            mock_create.return_value = {
                "id": "cs_test_123",
                "url": "https://checkout.stripe.com/pay/cs_test_123",
                "expires_at": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
            }

            result = StripeProcessor.create_checkout_session(
                customer_email="test@example.com",
                customer_name="Test Customer",
                product_name="Test Product",
                amount_usd=99.99,
                order_id="order_123",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
            )

            assert result["status"] == "session_created"
            assert result["session_id"] == "cs_test_123"
            assert "checkout_url" in result

    def test_create_checkout_session_invalid_amount(self):
        """Test checkout with invalid amount."""
        result = StripeProcessor.create_checkout_session(
            customer_email="test@example.com",
            customer_name="Test Customer",
            product_name="Test Product",
            amount_usd=-10.0,  # Invalid
            order_id="order_123",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

        assert result["status"] == "error"

    def test_refund_payment(self):
        """Test payment refund."""
        with patch("stripe.Refund.create") as mock_refund:
            mock_refund.return_value = {
                "id": "re_test_123",
                "amount": 9999,
                "status": "succeeded",
                "charge": "ch_test_123",
            }

            result = StripeProcessor.refund_payment(
                payment_intent_id="pi_test_123",
                amount_usd=99.99,
            )

            assert result["status"] == "refunded"
            assert result["refund_id"] == "re_test_123"
            assert result["amount_refunded"] == 99.99

    def test_webhook_payment_succeeded(self):
        """Test payment succeeded webhook handler."""
        event = {
            "type": WebhookEventType.PAYMENT_INTENT_SUCCEEDED,
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "amount": 9999,
                    "currency": "usd",
                    "receipt_email": "test@example.com",
                    "metadata": {"order_id": "order_123"},
                }
            },
        }

        result = StripeWebhookHandler.handle_event(event)

        assert result["status"] == "processed"
        assert result["event_type"] == WebhookEventType.PAYMENT_INTENT_SUCCEEDED
        assert result["order_id"] == "order_123"

    def test_webhook_signature_verification(self):
        """Test webhook signature verification."""
        with patch("stripe.Webhook.construct_event") as mock_verify:
            mock_verify.return_value = {"id": "evt_test"}

            is_valid = StripeWebhookHandler.verify_signature(
                payload=b"test_payload",
                signature="test_signature",
            )

            assert is_valid == True


# ============= MERCADOPAGO TESTS =============

class TestMercadoPagoProcessor:
    """MercadoPago payment processor tests."""

    def test_create_checkout_preference(self):
        """Test MercadoPago preference creation."""
        with patch("requests.post") as mock_post:
            mock_post.return_value = Mock(
                status_code=201,
                json=lambda: {
                    "id": "pref_123",
                    "init_point": "https://www.mercadopago.com.ar/checkout/pay/pref_123",
                }
            )

            result = MercadoPagoProcessor.create_checkout_preference(
                external_reference="order_123",
                customer_email="test@example.com",
                customer_name="Test Customer",
                items=[
                    {"name": "Product", "qty": 1, "unit_price": 99.99}
                ],
            )

            assert result["status"] == "preference_created"
            assert result["preference_id"] == "pref_123"

    def test_get_payment_info(self):
        """Test getting payment info."""
        with patch("requests.get") as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "id": "pay_123",
                    "status": "approved",
                    "transaction_amount": 99.99,
                    "currency_id": "USD",
                    "payer": {"email": "test@example.com"},
                    "installments": 1,
                    "date_created": datetime.utcnow().isoformat(),
                }
            )

            result = MercadoPagoProcessor.get_payment_info("pay_123")

            assert result["status"] == "retrieved"
            assert result["payment_id"] == "pay_123"

    def test_refund_mercadopago_payment(self):
        """Test MercadoPago refund."""
        with patch("requests.post") as mock_post:
            mock_post.return_value = Mock(
                status_code=201,
                json=lambda: {
                    "id": "ref_123",
                    "amount": 99.99,
                    "status": "approved",
                }
            )

            result = MercadoPagoProcessor.refund_payment(
                payment_id="pay_123",
                amount=99.99,
            )

            assert result["status"] == "refunded"


# ============= CRYPTO TESTS =============

class TestCryptoProcessor:
    """Crypto payment processor tests."""

    def test_generate_payment_address(self):
        """Test generating crypto payment address."""
        with patch.dict("os.environ", {"DEPOSIT_WALLET_ADDRESS": "TAbCd123"}):
            result = CryptoProcessor.generate_payment_address(
                customer_id="cust_123",
                blockchain="tron",
            )

            assert result["status"] == "address_generated"
            assert "address" in result
            assert "invoice_id" in result

    def test_get_exchange_rate(self):
        """Test getting exchange rate."""
        with patch("requests.get") as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {"usdt": {"usd": 1.00}}
            )

            result = CryptoProcessor.get_exchange_rate()

            assert result["status"] == "retrieved"
            assert result["rate"] == 1.00


# ============= RECONCILIATION TESTS =============

class TestPaymentReconciler:
    """Payment reconciliation tests."""

    def test_reconcile_unmatched_payment(self):
        """Test reconciling payment with no matching order."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = PaymentReconciler.reconcile_payment(
            db=mock_db,
            payment_id="pay_123",
            payment_provider="stripe",
            customer_email="test@example.com",
            amount_usd=99.99,
        )

        assert result["status"] == "unmatched"
        assert result["reconciliation_status"] == "unmatched"


# ============= BILLING HISTORY TESTS =============

class TestBillingHistoryManager:
    """Billing history manager tests."""

    def test_get_account_balance(self):
        """Test calculating account balance."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = [
            Mock(status="succeeded", amount=100.0),
            Mock(status="succeeded", amount=50.0),
            Mock(status="refunded", amount=10.0),
        ]

        result = BillingHistoryManager.get_account_balance(mock_db, "acc_123")

        assert result["status"] == "calculated"
        assert result["total_revenue"] == 150.0
        assert result["total_refunds"] == 10.0
        assert result["net_balance"] == 140.0


# ============= INVOICE TESTS =============

class TestInvoiceGenerator:
    """Invoice generator tests."""

    def test_generate_invoice_html(self):
        """Test generating HTML invoice."""
        result = InvoiceGenerator.generate_invoice(
            order_id="order_123",
            customer_name="Test Customer",
            customer_email="test@example.com",
            items=[
                {"name": "Product", "qty": 1, "unit_price": 99.99}
            ],
            amount_total=99.99,
            tax_rate=0.10,
        )

        assert result["status"] == "generated"
        assert "invoice_id" in result
        assert "invoice_number" in result
        assert result["amount_tax"] == 10.0
        assert result["amount_total"] == 110.0  # 99.99 + tax


# ============= PAYOUT TESTS =============

class TestPayoutManager:
    """Payout manager tests."""

    def test_calculate_payout(self):
        """Test payout calculation."""
        result = PayoutManager.calculate_payout(
            gross_revenue=1000.0,
            refunds=50.0,
            chargebacks=0.0,
            platform_fees=True,
            stripe_fees=True,
        )

        assert result["status"] == "calculated"
        assert result["gross_revenue"] == 1000.0
        assert result["refunds"] == 50.0
        assert result["stripe_fees"] > 0
        assert result["platform_fees"] > 0
        assert result["net_payout"] < 950.0  # After deductions


# ============= COMPLIANCE TESTS =============

class TestComplianceChecker:
    """Compliance checker tests."""

    def test_validate_customer_data_valid(self):
        """Test validating valid customer data."""
        result = ComplianceChecker.validate_customer_data(
            customer_name="John Doe",
            customer_email="john@example.com",
        )

        assert result["status"] == "valid"
        assert result["risk_level"] == "low"

    def test_validate_customer_data_invalid_email(self):
        """Test validating invalid email."""
        result = ComplianceChecker.validate_customer_data(
            customer_name="John Doe",
            customer_email="invalid-email",
        )

        assert result["status"] == "invalid"
        assert len(result["issues"]) > 0

    def test_screen_transaction_high_value(self):
        """Test transaction screening for high value."""
        result = ComplianceChecker.screen_transaction(
            transaction_id="tx_123",
            customer_email="test@example.com",
            amount_usd=10000.0,  # High value
        )

        assert "High-value transaction" in result["flags"]
        assert result["risk_score"] > 0

    def test_mask_payment_data(self):
        """Test payment data masking."""
        result = ComplianceChecker.mask_payment_data(
            card_number="4111111111111111",
        )

        assert "card" in result
        assert result["card"].endswith("1111")
        assert result["card"].startswith("*")


# ============= FIXTURES =============

@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with patch("stripe.api_key"):
        yield


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
