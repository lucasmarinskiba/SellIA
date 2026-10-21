"""Finance Schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from app.core.pii_masking import mask_email, mask_name, mask_phone, mask_tax_id


class SalesInvoiceCreate(BaseModel):
    order_id: UUID | None = None
    conversation_id: UUID | None = None
    invoice_number: str
    amount: Decimal
    tax_amount: Decimal = Decimal(0)
    total_amount: Decimal
    currency: str = "ARS"
    due_date: datetime
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    items: list = []


class SalesInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    order_id: UUID | None
    conversation_id: UUID | None
    invoice_number: str
    status: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    due_date: datetime
    paid_at: datetime | None
    paid_amount: Decimal
    customer_name: str | None
    customer_email: str | None
    customer_phone: str | None
    items: list
    created_at: datetime

    @field_serializer("customer_name")
    def mask_customer_name(self, value: str | None) -> str | None:
        return mask_name(value)

    @field_serializer("customer_email")
    def mask_customer_email(self, value: str | None) -> str | None:
        return mask_email(value)

    @field_serializer("customer_phone")
    def mask_customer_phone(self, value: str | None) -> str | None:
        return mask_phone(value)


class PaymentReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    order_id: UUID
    invoice_id: UUID | None
    conversation_id: UUID | None
    reminder_level: int
    status: str
    scheduled_at: datetime
    sent_at: datetime | None
    message_content: str | None
    channel_platform: str
    response_received: bool
    created_at: datetime


class AccountsReceivableSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    snapshot_date: datetime
    total_outstanding: Decimal
    total_overdue: Decimal
    invoice_count: int
    overdue_count: int
    customer_breakdown: list
    created_at: datetime


class TaxConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    country_code: str
    tax_name: str
    tax_rate: Decimal
    tax_id_number: str | None
    is_tax_exempt: bool
    extra_data: dict
    created_at: datetime

    @field_serializer("tax_id_number")
    def mask_tax_id(self, value: str | None) -> str | None:
        return mask_tax_id(value)


class FinanceAutopilotStatusResponse(BaseModel):
    business_id: UUID
    is_active: bool
    is_paused: bool
    paused_reason: str | None = None
    auto_deliver_invoices: bool
    auto_run_dunning: bool
    auto_reconcile_payments: bool
    auto_generate_tax_reports: bool
    dunning_channel: str
    max_dunning_level: int


class TaxReportResponse(BaseModel):
    period: str
    total_invoiced: Decimal
    total_net: Decimal
    iva_debito: Decimal
    iva_credito: Decimal
    saldo: Decimal
    tax_rate: Decimal
    invoice_count: int
    currency: str


class CashFlowForecastResponse(BaseModel):
    days: int
    total_receivables: Decimal
    pipeline_weighted: Decimal
    daily_projection: list[dict]
    currency: str


class DunningPipelineResponse(BaseModel):
    level_1: dict
    level_2: dict
    level_3: dict
    level_4: dict


class FinanceDashboardResponse(BaseModel):
    business_id: str
    total_receivables: Decimal
    overdue_amount: Decimal
    invoice_count: int
    overdue_count: int
    dunning_active: int
    forecast_summary: dict | None = None
    tax_status: dict
    collection_rate: Decimal
    autopilot_active: bool
    currency: str
