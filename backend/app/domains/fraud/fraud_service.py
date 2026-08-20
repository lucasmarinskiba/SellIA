"""Fraud detection service — order + account fraud scoring."""

import logging
import hashlib
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional
from decimal import Decimal
from statistics import stdev, mean

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.fraud.fraud_models import (
    OrderFraudScore, AccountFraudScore, FraudBlacklist, FraudMetrics,
    FraudRiskLevel, FraudReason
)

logger = logging.getLogger(__name__)


class FraudDetectionService:
    """Detect order and account fraud."""

    @staticmethod
    def score_order_fraud(
        business_id: UUID,
        order_id: str,
        customer_id: UUID,
        order_value: Decimal,
        ip_address: str = None,
        device_fingerprint: str = None,
        billing_address: str = None,
        shipping_address: str = None,
        db: Session = None
    ) -> dict:
        """Score fraud risk for order."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.customers.models import Customer
        from app.domains.orders.models import Order

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        fraud_score = Decimal("0")
        signals = {}

        # Signal 1: Velocity (orders in last 24h)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_orders = db.query(Order).filter(
            Order.customer_id == customer_id,
            Order.created_at >= cutoff
        ).count()
        if recent_orders > 3:
            velocity_score = min(40, recent_orders * 10)
            signals["velocity_score"] = Decimal(str(velocity_score))
            fraud_score += Decimal(str(velocity_score))

        # Signal 2: New account
        account_age = (datetime.now(timezone.utc) - customer.created_at).days
        if account_age < 7:
            new_account_score = 35
            signals["new_account_score"] = Decimal(str(new_account_score))
            fraud_score += Decimal(str(new_account_score))

        # Signal 3: High first order
        customer_order_count = db.query(Order).filter(
            Order.customer_id == customer_id
        ).count()
        if customer_order_count == 1 and float(order_value) > 500:
            high_first_score = 25
            signals["high_first_score"] = Decimal(str(high_first_score))
            fraud_score += Decimal(str(high_first_score))

        # Signal 4: Address mismatch
        if billing_address and shipping_address and billing_address != shipping_address:
            mismatch_score = 20
            signals["address_mismatch_score"] = Decimal(str(mismatch_score))
            fraud_score += Decimal(str(mismatch_score))

        # Signal 5: Blacklist check
        blacklist_hit = False
        if ip_address:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
            blacklist = db.query(FraudBlacklist).filter(
                FraudBlacklist.business_id == business_id,
                FraudBlacklist.entity_type == "ip",
                FraudBlacklist.entity_hash == ip_hash,
                FraudBlacklist.is_active == True
            ).first()
            if blacklist:
                blacklist_hit = True
                signals["blacklist_match_score"] = Decimal("30")
                fraud_score += Decimal("30")

        # Calculate risk level
        fraud_score = min(100, fraud_score)
        if fraud_score >= 81:
            risk_level = FraudRiskLevel.CRITICAL
        elif fraud_score >= 51:
            risk_level = FraudRiskLevel.HIGH
        elif fraud_score >= 16:
            risk_level = FraudRiskLevel.MEDIUM
        else:
            risk_level = FraudRiskLevel.LOW

        # Primary reason
        if fraud_score >= 50:
            if signals.get("velocity_score"):
                primary_reason = FraudReason.VELOCITY_ABUSE
            elif signals.get("new_account_score"):
                primary_reason = FraudReason.NEW_ACCOUNT
            elif blacklist_hit:
                primary_reason = FraudReason.BLACKLIST_HIT
            else:
                primary_reason = FraudReason.HIGH_VALUE_FIRST
        else:
            primary_reason = FraudReason.NONE

        # Create or update score
        score_record = db.query(OrderFraudScore).filter(
            OrderFraudScore.order_id == order_id
        ).first()

        if score_record:
            score_record.fraud_risk_score = fraud_score
            score_record.fraud_risk_level = risk_level
            score_record.primary_fraud_reason = primary_reason
        else:
            score_record = OrderFraudScore(
                business_id=business_id,
                order_id=order_id,
                customer_id=customer_id,
                fraud_risk_score=fraud_score,
                fraud_risk_level=risk_level,
                primary_fraud_reason=primary_reason,
                customer_order_count=customer_order_count,
                **{k: v for k, v in signals.items()}
            )
            db.add(score_record)

        # Auto-block if critical
        if risk_level == FraudRiskLevel.CRITICAL:
            score_record.order_blocked = True
            score_record.reason_for_action = f"Auto-blocked: {primary_reason.value}"

        db.commit()

        logger.info(f"Order fraud scored: {order_id} - risk={risk_level.value}")

        return {
            "order_id": order_id,
            "fraud_risk_score": float(fraud_score),
            "fraud_risk_level": risk_level.value,
            "primary_reason": primary_reason.value,
            "blocked": score_record.order_blocked,
            "manual_review_requested": score_record.manual_review_requested
        }

    @staticmethod
    def score_account_fraud(
        business_id: UUID,
        customer_id: UUID,
        db: Session = None
    ) -> dict:
        """Score fraud risk for customer account."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.customers.models import Customer
        from app.domains.orders.models import Order

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        fraud_score = Decimal("0")

        # Signal 1: New account
        account_age = (datetime.now(timezone.utc) - customer.created_at).days
        if account_age < 7:
            fraud_score += 40
        elif account_age < 30:
            fraud_score += 20

        # Signal 2: Profile completeness
        fields_filled = sum([
            bool(customer.email),
            bool(customer.phone),
            bool(customer.address),
        ])
        if fields_filled < 2:
            fraud_score += 25

        # Signal 3: Order history
        orders = db.query(Order).filter(Order.customer_id == customer_id).all()
        if not orders and account_age < 30:
            fraud_score += 15

        # Signal 4: High-value pattern
        if orders:
            amounts = [float(o.total_value) for o in orders if o.total_value]
            if amounts and max(amounts) > 1000 and len(orders) <= 2:
                fraud_score += 20

        # Calculate risk level
        fraud_score = min(100, fraud_score)
        if fraud_score >= 81:
            risk_level = FraudRiskLevel.CRITICAL
        elif fraud_score >= 51:
            risk_level = FraudRiskLevel.HIGH
        elif fraud_score >= 16:
            risk_level = FraudRiskLevel.MEDIUM
        else:
            risk_level = FraudRiskLevel.LOW

        # Create or update account score
        account_score = db.query(AccountFraudScore).filter(
            AccountFraudScore.customer_id == customer_id
        ).first()

        if account_score:
            account_score.account_fraud_score = fraud_score
            account_score.account_risk_level = risk_level
            account_score.days_since_signup = account_age
            account_score.total_orders = len(orders)
        else:
            account_score = AccountFraudScore(
                business_id=business_id,
                customer_id=customer_id,
                account_fraud_score=fraud_score,
                account_risk_level=risk_level,
                days_since_signup=account_age,
                total_orders=len(orders),
                email_verified=customer.email_verified if hasattr(customer, "email_verified") else False
            )
            db.add(account_score)

        db.commit()

        logger.info(f"Account fraud scored: {customer_id} - risk={risk_level.value}")

        return {
            "customer_id": str(customer_id),
            "account_fraud_score": float(fraud_score),
            "account_risk_level": risk_level.value,
            "account_age_days": account_age,
            "total_orders": len(orders)
        }

    @staticmethod
    def add_to_blacklist(
        business_id: UUID,
        entity_type: str,
        entity_value: str,
        fraud_reason: str = None,
        expires_at: datetime = None,
        db: Session = None
    ) -> dict:
        """Add email/IP/card to fraud blacklist."""
        if not db:
            raise ValueError("Database session required")

        entity_hash = hashlib.sha256(entity_value.encode()).hexdigest()

        # Check if already blacklisted
        existing = db.query(FraudBlacklist).filter(
            FraudBlacklist.business_id == business_id,
            FraudBlacklist.entity_type == entity_type,
            FraudBlacklist.entity_hash == entity_hash
        ).first()

        if existing:
            existing.fraud_count += 1
            db.commit()
            return {
                "blacklist_action": "updated",
                "entity_type": entity_type,
                "fraud_count": existing.fraud_count
            }

        # Add to blacklist
        blacklist = FraudBlacklist(
            business_id=business_id,
            entity_type=entity_type,
            entity_value=entity_value,
            entity_hash=entity_hash,
            fraud_reason=fraud_reason,
            expires_at=expires_at
        )

        db.add(blacklist)
        db.commit()

        logger.info(f"Blacklisted: {entity_type} - {fraud_reason}")

        return {
            "blacklist_action": "added",
            "entity_type": entity_type,
            "reason": fraud_reason
        }

    @staticmethod
    def get_fraud_summary(
        business_id: UUID,
        date: str = None,
        db: Session = None
    ) -> dict:
        """Get fraud detection summary."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Count by risk level
        order_scores = db.query(OrderFraudScore).filter(
            OrderFraudScore.business_id == business_id
        ).all()

        if not order_scores:
            return {"summary_available": False}

        high_risk = len([s for s in order_scores if s.fraud_risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]])
        blocked = len([s for s in order_scores if s.order_blocked])
        confirmed_fraud = len([s for s in order_scores if s.is_confirmed_fraud])

        # Account fraud
        account_scores = db.query(AccountFraudScore).filter(
            AccountFraudScore.business_id == business_id
        ).all()

        accounts_flagged = len([a for a in account_scores if a.is_flagged])
        accounts_suspended = len([a for a in account_scores if a.account_suspended])

        # Blacklist
        blacklist_count = db.query(FraudBlacklist).filter(
            FraudBlacklist.business_id == business_id,
            FraudBlacklist.is_active == True
        ).count()

        # Create metrics
        metrics = FraudMetrics(
            business_id=business_id,
            date=date,
            total_orders_reviewed=len(order_scores),
            orders_flagged_high_risk=high_risk,
            orders_blocked=blocked,
            confirmed_fraud_orders=confirmed_fraud,
            fraud_order_rate=Decimal(str(round((confirmed_fraud / max(len(order_scores), 1)) * 100, 2))),
            accounts_flagged=accounts_flagged,
            accounts_suspended=accounts_suspended,
            total_blacklisted=blacklist_count
        )

        db.add(metrics)
        db.commit()

        logger.info(f"Fraud summary generated: {business_id} - {date}")

        return {
            "summary_generated": True,
            "date": date,
            "order_fraud": {
                "total_reviewed": len(order_scores),
                "high_risk": high_risk,
                "blocked": blocked,
                "confirmed_fraud": confirmed_fraud
            },
            "account_fraud": {
                "flagged": accounts_flagged,
                "suspended": accounts_suspended
            },
            "blacklist": {
                "total_entries": blacklist_count
            }
        }
