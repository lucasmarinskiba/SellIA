"""Phase 49: Multi-Vendor Management & Orchestration."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class VendorPartner(Base):
    __tablename__ = "vendor_partners"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False)
    vendor_email = Column(String(255), nullable=False)
    vendor_phone = Column(String(20), nullable=True)
    vendor_rating = Column(Float, default=0)
    vendor_status = Column(String(50), default="active")
    payment_terms = Column(String(100), nullable=True)
    commission_rate = Column(Float, default=0)
    total_products = Column(Integer, default=0)
    total_sales = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class VendorProduct(Base):
    __tablename__ = "vendor_products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendor_partners.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(500), nullable=False)
    vendor_sku = Column(String(255), nullable=False)
    cost_price = Column(Float, default=0)
    wholesale_price = Column(Float, default=0)
    suggested_retail_price = Column(Float, default=0)
    commission_per_unit = Column(Float, default=0)
    stock_available = Column(Integer, default=0)
    lead_time_days = Column(Integer, default=0)
    quality_score = Column(Float, default=0)
    approval_status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class CommissionTracking(Base):
    __tablename__ = "commission_tracking"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendor_partners.id", ondelete="CASCADE"), nullable=False)
    period = Column(String(50), nullable=False)
    total_sales = Column(Float, default=0)
    commission_rate = Column(Float, default=0)
    total_commission = Column(Float, default=0)
    payments_made = Column(Float, default=0)
    balance_due = Column(Float, default=0)
    payment_date = Column(DateTime(timezone.utc), nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class VendorPerformance(Base):
    __tablename__ = "vendor_performance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendor_partners.id", ondelete="CASCADE"), nullable=False)
    total_orders = Column(Integer, default=0)
    on_time_delivery_rate = Column(Float, default=0)
    quality_rating = Column(Float, default=0)
    defect_rate = Column(Float, default=0)
    customer_satisfaction = Column(Float, default=0)
    return_rate = Column(Float, default=0)
    communication_score = Column(Float, default=0)
    overall_score = Column(Float, default=0)
    performance_status = Column(String(50), default="good")
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class VendorSettlement(Base):
    __tablename__ = "vendor_settlements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendor_partners.id", ondelete="CASCADE"), nullable=False)
    settlement_period = Column(String(50), nullable=False)
    total_sales_value = Column(Float, default=0)
    commission_amount = Column(Float, default=0)
    returns_amount = Column(Float, default=0)
    chargebacks_amount = Column(Float, default=0)
    net_payment = Column(Float, default=0)
    settlement_status = Column(String(50), default="pending")  # pending, scheduled, paid
    payment_method = Column(String(50), nullable=True)
    payment_date = Column(DateTime(timezone.utc), nullable=True)
    settled_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
