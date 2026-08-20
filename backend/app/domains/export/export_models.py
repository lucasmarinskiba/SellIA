"""Export & BI models — data export, reports, warehouse sync."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExportFormat(str, Enum):
    """Export file format."""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PARQUET = "parquet"


class ExportType(str, Enum):
    """Export data type."""
    CUSTOMERS = "customers"
    ORDERS = "orders"
    TRANSACTIONS = "transactions"
    JOURNEYS = "journeys"
    SEGMENTS = "segments"
    LOCATIONS = "locations"
    FEEDBACK = "feedback"
    INVENTORY = "inventory"
    STAFF_TASKS = "staff_tasks"
    PREDICTIONS = "predictions"


class ReportFrequency(str, Enum):
    """Report schedule frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class DataExport(Base):
    """Track data exports."""
    __tablename__ = "data_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Export config
    export_name = Column(String(255), nullable=False)
    export_type = Column(String(50), nullable=False)  # customers, orders, etc
    export_format = Column(String(20), default=ExportFormat.CSV)

    # Scope
    date_start = Column(String(10), nullable=True)  # YYYY-MM-DD
    date_end = Column(String(10), nullable=True)
    filters = Column(JSONB, default=dict)  # {"status": "active", "segment": "high_value"}
    columns_included = Column(JSONB, default=list)  # ["id", "email", "revenue"]

    # Output
    file_url = Column(String(500), nullable=True)  # S3 or storage URL
    file_size_bytes = Column(Integer, default=0)
    row_count = Column(Integer, default=0)

    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    requested_by = Column(String(255), nullable=True)  # Email of user
    requested_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone.utc), nullable=True)
    expires_at = Column(DateTime(timezone.utc), nullable=True)  # When file is purged

    __table_args__ = (
        Index("idx_business_status", "business_id", "status"),
        Index("idx_requested_at", "business_id", "requested_at"),
    )


class ScheduledReport(Base):
    """Configure recurring reports."""
    __tablename__ = "scheduled_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Report config
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(100), nullable=False)  # "daily_sales", "weekly_customer_summary", etc
    description = Column(Text, nullable=True)

    # Scheduling
    frequency = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly
    schedule_time = Column(String(5), default="06:00")  # 24h format HH:MM
    day_of_week = Column(Integer, nullable=True)  # 0-6 (Mon-Sun) for weekly
    day_of_month = Column(Integer, nullable=True)  # 1-31 for monthly

    # Content
    export_format = Column(String(20), default=ExportFormat.CSV)
    metrics_included = Column(JSONB, default=list)  # Metrics to include in report
    segments_to_report = Column(JSONB, default=list)  # Segment IDs to break down by

    # Recipients
    recipients = Column(JSONB, default=list)  # Email addresses
    include_charts = Column(Boolean, default=False)
    include_summary = Column(Boolean, default=True)

    # Status
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime(timezone.utc), nullable=True)
    next_send_at = Column(DateTime(timezone.utc), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_active", "business_id", "is_active"),
        Index("idx_next_send", "business_id", "next_send_at"),
    )


class DataWarehouseSync(Base):
    """Track data warehouse integrations."""
    __tablename__ = "data_warehouse_sync"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Integration
    warehouse_type = Column(String(50), nullable=False)  # bigquery, snowflake, redshift, databricks
    warehouse_name = Column(String(255), nullable=False)
    connection_status = Column(String(20), default="disconnected")  # connected, disconnected, error

    # Config
    dataset_prefix = Column(String(100), default="sellias_")  # Table prefix
    sync_interval_hours = Column(Integer, default=24)  # Sync frequency
    tables_synced = Column(JSONB, default=list)  # ["customers", "orders", "transactions"]

    # Credentials (encrypted)
    connection_string_encrypted = Column(String(500), nullable=True)  # Encrypted connection string
    api_key_encrypted = Column(String(500), nullable=True)  # Encrypted API key

    # Sync tracking
    last_sync_at = Column(DateTime(timezone.utc), nullable=True)
    next_sync_at = Column(DateTime(timezone.utc), nullable=True)
    rows_synced_total = Column(Integer, default=0)
    sync_errors = Column(Integer, default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_status", "business_id", "connection_status"),
    )


class BIDashboardConfig(Base):
    """BI dashboard configuration."""
    __tablename__ = "bi_dashboard_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Dashboard
    dashboard_name = Column(String(255), nullable=False)
    dashboard_type = Column(String(100), nullable=False)  # "executive_summary", "sales_dashboard", "customer_analytics"
    description = Column(Text, nullable=True)

    # Configuration
    layout = Column(JSONB, default=list)  # Chart positions, sizes
    charts = Column(JSONB, default=list)  # Chart types, data sources, filters
    refresh_rate_minutes = Column(Integer, default=60)

    # Access
    shared_with = Column(JSONB, default=list)  # User emails
    is_public = Column(Boolean, default=False)

    # Usage
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime(timezone.utc), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_type", "business_id", "dashboard_type"),
    )


class ExportMetrics(Base):
    """Track export usage metrics."""
    __tablename__ = "export_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Export activity
    total_exports_requested = Column(Integer, default=0)
    successful_exports = Column(Integer, default=0)
    failed_exports = Column(Integer, default=0)
    avg_export_time_seconds = Column(Integer, default=0)

    # Data volume
    total_rows_exported = Column(Integer, default=0)
    total_bytes_exported = Column(Integer, default=0)

    # Format breakdown
    csv_exports = Column(Integer, default=0)
    excel_exports = Column(Integer, default=0)
    json_exports = Column(Integer, default=0)
    parquet_exports = Column(Integer, default=0)

    # Reports
    scheduled_reports_sent = Column(Integer, default=0)
    report_delivery_failures = Column(Integer, default=0)

    # BI
    dashboard_views = Column(Integer, default=0)
    avg_dashboard_load_time_ms = Column(Integer, default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "date"),
    )
