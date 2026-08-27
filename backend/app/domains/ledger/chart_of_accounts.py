"""Default chart of accounts.

A compact, opinionated COA that covers what an SME running on this
platform actually needs: cash, receivables, payables, tax control
accounts, revenue by channel, COGS, and the operating-expense buckets
the inter-department orchestrator reasons about (marketing / ads / sales
/ ops / payroll).

`subtype` values are the stable keys the posting engine looks accounts up
by — never match on `name` or `code`, which the user may rename.
"""

from app.domains.ledger.models import AccountType, NORMAL_BALANCE_BY_TYPE

# (code, name, type, subtype, is_system)
DEFAULT_ACCOUNTS: list[tuple[str, str, str, str, bool]] = [
    # ---- Assets ----
    ("1000", "Caja y bancos", AccountType.ASSET.value, "cash", True),
    ("1010", "MercadoPago", AccountType.ASSET.value, "cash_mercadopago", True),
    ("1020", "Stripe", AccountType.ASSET.value, "cash_stripe", True),
    ("1100", "Cuentas por cobrar", AccountType.ASSET.value, "accounts_receivable", True),
    ("1200", "Pagos en tránsito (procesador)", AccountType.ASSET.value, "payment_clearing", True),
    ("1300", "Inventario", AccountType.ASSET.value, "inventory", True),
    ("1400", "IVA crédito fiscal", AccountType.ASSET.value, "vat_input", True),
    ("1500", "Anticipos a proveedores", AccountType.ASSET.value, "prepaid_expenses", True),

    # ---- Liabilities ----
    ("2000", "Cuentas por pagar", AccountType.LIABILITY.value, "accounts_payable", True),
    ("2100", "IVA débito fiscal", AccountType.LIABILITY.value, "vat_output", True),
    ("2110", "Retenciones e impuestos a pagar", AccountType.LIABILITY.value, "taxes_payable", True),
    ("2200", "Ingresos diferidos (suscripciones)", AccountType.LIABILITY.value, "deferred_revenue", True),
    ("2300", "Reembolsos a pagar", AccountType.LIABILITY.value, "refunds_payable", True),
    ("2400", "Comisiones de plataforma a pagar", AccountType.LIABILITY.value, "platform_fees_payable", True),

    # ---- Equity ----
    ("3000", "Capital", AccountType.EQUITY.value, "owner_capital", True),
    ("3100", "Resultados acumulados", AccountType.EQUITY.value, "retained_earnings", True),
    ("3900", "Resultado del ejercicio", AccountType.EQUITY.value, "current_year_earnings", True),

    # ---- Revenue ----
    ("4000", "Ventas de productos", AccountType.REVENUE.value, "product_sales", True),
    ("4010", "Ventas de servicios", AccountType.REVENUE.value, "service_sales", True),
    ("4020", "Ingresos por suscripción", AccountType.REVENUE.value, "subscription_revenue", True),
    ("4100", "Descuentos y bonificaciones", AccountType.REVENUE.value, "sales_discounts", True),
    ("4900", "Otros ingresos", AccountType.REVENUE.value, "other_income", True),

    # ---- COGS ----
    ("5000", "Costo de mercadería vendida", AccountType.EXPENSE.value, "cogs", True),
    ("5100", "Comisiones de pasarela de pago", AccountType.EXPENSE.value, "payment_processing_fees", True),
    ("5200", "Comisiones de marketplace", AccountType.EXPENSE.value, "marketplace_fees", True),
    ("5300", "Envíos y logística", AccountType.EXPENSE.value, "shipping_costs", True),

    # ---- Operating expenses (department-tagged) ----
    ("6000", "Publicidad — Meta Ads", AccountType.EXPENSE.value, "ad_spend_meta", True),
    ("6010", "Publicidad — Google Ads", AccountType.EXPENSE.value, "ad_spend_google", True),
    ("6020", "Publicidad — TikTok Ads", AccountType.EXPENSE.value, "ad_spend_tiktok", True),
    ("6030", "Publicidad — otros canales", AccountType.EXPENSE.value, "ad_spend_other", True),
    ("6100", "Marketing — contenido y herramientas", AccountType.EXPENSE.value, "marketing_tools", True),
    ("6200", "Ventas — comisiones y viáticos", AccountType.EXPENSE.value, "sales_expenses", True),
    ("6300", "Sueldos y cargas sociales", AccountType.EXPENSE.value, "payroll", True),
    ("6400", "Software y suscripciones (SaaS)", AccountType.EXPENSE.value, "software_subscriptions", True),
    ("6500", "Servicios profesionales (legal / contable)", AccountType.EXPENSE.value, "professional_services", True),
    ("6600", "Alquiler y servicios", AccountType.EXPENSE.value, "rent_utilities", True),
    ("6900", "Gastos varios", AccountType.EXPENSE.value, "misc_expenses", True),
    ("7000", "Impuestos y tasas (no IVA)", AccountType.EXPENSE.value, "tax_expense", True),
    ("7100", "Diferencias de cambio", AccountType.EXPENSE.value, "fx_gain_loss", True),
]


def build_default_accounts(currency: str = "ARS") -> list[dict]:
    """Return the default COA as a list of dicts ready for ORM insert."""
    rows: list[dict] = []
    for code, name, acc_type, subtype, is_system in DEFAULT_ACCOUNTS:
        rows.append(
            {
                "code": code,
                "name": name,
                "type": acc_type,
                "subtype": subtype,
                "normal_balance": NORMAL_BALANCE_BY_TYPE[acc_type],
                "currency": currency,
                "is_system": is_system,
                "is_active": True,
            }
        )
    return rows


# Subtypes the posting engine needs to always resolve. Bootstrap verifies these.
REQUIRED_SUBTYPES = {
    "cash",
    "accounts_receivable",
    "payment_clearing",
    "vat_output",
    "vat_input",
    "product_sales",
    "service_sales",
    "subscription_revenue",
    "deferred_revenue",
    "sales_discounts",
    "cogs",
    "payment_processing_fees",
    "refunds_payable",
    "retained_earnings",
    "current_year_earnings",
    "ad_spend_meta",
    "ad_spend_google",
    "ad_spend_tiktok",
    "ad_spend_other",
    "accounts_payable",
}
