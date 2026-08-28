"""Financial Dashboard schemas — response shape for the unified dashboard."""

from pydantic import BaseModel


class DataAvailabilityOut(BaseModel):
    ledger: bool
    invoicing: bool
    ad_budget: bool
    cashflow: bool


class RevenueSectionOut(BaseModel):
    total_revenue: float
    gross_profit: float
    net_income: float
    gross_margin_pct: float
    net_margin_pct: float


class AdvertisingSectionOut(BaseModel):
    total_spend: float
    blended_roas: float
    marketing_efficiency_ratio: float | None
    active_channels: int


class InvoicingSectionOut(BaseModel):
    accounts_receivable: float
    overdue_invoices: int
    avg_payment_days: float
    total_invoices: int


class CashSectionOut(BaseModel):
    cash_balance: float
    runway_days: int | None
    health: str  # unknown, critical, at_risk, stable, healthy


class FinancialDashboardOut(BaseModel):
    business_id: str
    period_days: int
    data_availability: DataAvailabilityOut
    revenue: RevenueSectionOut
    advertising: AdvertisingSectionOut
    invoicing: InvoicingSectionOut
    cash: CashSectionOut
