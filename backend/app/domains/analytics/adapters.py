"""Business-type-aware adapters for Analytics & BI.

Maps each of the 11 business types to:
- Custom funnel stages and conversion metrics
- Churn risk factors and thresholds
- LTV prediction factors
- Insight alert thresholds and recommendations
- Dashboard KPI priorities
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal

from app.domains.business_context.models import BusinessType


class FunnelAdapter:
    """Returns business-type-specific funnel definitions."""

    STAGES: Dict[BusinessType, List[Dict[str, Any]]] = {
        BusinessType.SOFTWARE: [
            {"key": "trial_signup", "label": "Trial Signup", "order": 1},
            {"key": "activation", "label": "Activation", "order": 2},
            {"key": "paid_conversion", "label": "Paid Conversion", "order": 3},
            {"key": "expansion", "label": "Expansion / Upsell", "order": 4},
            {"key": "retention", "label": "Retention", "order": 5},
        ],
        BusinessType.CONSULTING: [
            {"key": "inquiry", "label": "Inquiry", "order": 1},
            {"key": "consultation", "label": "Consultation", "order": 2},
            {"key": "proposal", "label": "Proposal Sent", "order": 3},
            {"key": "contract", "label": "Contract Signed", "order": 4},
            {"key": "referral", "label": "Referral", "order": 5},
        ],
        BusinessType.SERVICES: [
            {"key": "inquiry", "label": "Inquiry", "order": 1},
            {"key": "quote", "label": "Quote Request", "order": 2},
            {"key": "booking", "label": "Booking Confirmed", "order": 3},
            {"key": "service_delivery", "label": "Service Delivered", "order": 4},
            {"key": "repeat", "label": "Repeat Service", "order": 5},
        ],
        BusinessType.FOOD_BEVERAGE: [
            {"key": "visit", "label": "Store Visit / App Open", "order": 1},
            {"key": "order", "label": "Order Placed", "order": 2},
            {"key": "delivery", "label": "Delivered / Served", "order": 3},
            {"key": "repeat", "label": "Repeat Order", "order": 4},
            {"key": "review", "label": "Positive Review", "order": 5},
        ],
        BusinessType.FASHION_BEAUTY: [
            {"key": "browse", "label": "Product Browse", "order": 1},
            {"key": "cart", "label": "Add to Cart", "order": 2},
            {"key": "checkout", "label": "Checkout", "order": 3},
            {"key": "delivery", "label": "Delivery Completed", "order": 4},
            {"key": "repeat", "label": "Repeat Purchase", "order": 5},
        ],
        BusinessType.PHYSICAL_PRODUCTS: [
            {"key": "browse", "label": "Product Browse", "order": 1},
            {"key": "cart", "label": "Add to Cart", "order": 2},
            {"key": "checkout", "label": "Checkout", "order": 3},
            {"key": "delivery", "label": "Delivery Completed", "order": 4},
            {"key": "repeat", "label": "Repeat Purchase", "order": 5},
        ],
        BusinessType.DIGITAL_PRODUCTS: [
            {"key": "landing_visit", "label": "Landing Visit", "order": 1},
            {"key": "lead_capture", "label": "Lead Capture", "order": 2},
            {"key": "purchase", "label": "Purchase", "order": 3},
            {"key": "consume", "label": "Content Consumed", "order": 4},
            {"key": "upsell", "label": "Upsell Accepted", "order": 5},
        ],
        BusinessType.HEALTH_WELLNESS: [
            {"key": "inquiry", "label": "Inquiry", "order": 1},
            {"key": "assessment", "label": "Assessment / Trial", "order": 2},
            {"key": "subscription", "label": "Subscription", "order": 3},
            {"key": "engagement", "label": "Active Engagement", "order": 4},
            {"key": "referral", "label": "Referral", "order": 5},
        ],
        BusinessType.HOME_DECOR: [
            {"key": "browse", "label": "Product Browse", "order": 1},
            {"key": "wishlist", "label": "Wishlist / Save", "order": 2},
            {"key": "purchase", "label": "Purchase", "order": 3},
            {"key": "delivery", "label": "Delivery / Install", "order": 4},
            {"key": "repeat", "label": "Repeat Purchase", "order": 5},
        ],
        BusinessType.HANDCRAFT: [
            {"key": "browse", "label": "Product Browse", "order": 1},
            {"key": "inquiry", "label": "Custom Inquiry", "order": 2},
            {"key": "order", "label": "Order Confirmed", "order": 3},
            {"key": "delivery", "label": "Delivery", "order": 4},
            {"key": "review", "label": "Review / Repeat", "order": 5},
        ],
        BusinessType.OTHER: [
            {"key": "lead", "label": "Lead", "order": 1},
            {"key": "qualified", "label": "Qualified", "order": 2},
            {"key": "deal", "label": "Deal", "order": 3},
            {"key": "order", "label": "Order", "order": 4},
            {"key": "repeat", "label": "Repeat", "order": 5},
        ],
    }

    @classmethod
    def get_stages(cls, business_type: Optional[BusinessType]) -> List[Dict[str, Any]]:
        return cls.STAGES.get(business_type, cls.STAGES[BusinessType.OTHER])


class ChurnAdapter:
    """Returns business-type-specific churn risk logic."""

    THRESHOLDS: Dict[BusinessType, Dict[str, int]] = {
        BusinessType.SOFTWARE: {
            "inactive_days_critical": 14,
            "inactive_days_warning": 7,
            "no_order_days": 30,
            "support_ticket_weight": 20,
        },
        BusinessType.CONSULTING: {
            "inactive_days_critical": 60,
            "inactive_days_warning": 30,
            "no_order_days": 90,
            "support_ticket_weight": 10,
        },
        BusinessType.SERVICES: {
            "inactive_days_critical": 45,
            "inactive_days_warning": 21,
            "no_order_days": 60,
            "support_ticket_weight": 15,
        },
        BusinessType.FOOD_BEVERAGE: {
            "inactive_days_critical": 14,
            "inactive_days_warning": 7,
            "no_order_days": 14,
            "support_ticket_weight": 5,
        },
        BusinessType.FASHION_BEAUTY: {
            "inactive_days_critical": 60,
            "inactive_days_warning": 30,
            "no_order_days": 90,
            "support_ticket_weight": 10,
        },
        BusinessType.PHYSICAL_PRODUCTS: {
            "inactive_days_critical": 60,
            "inactive_days_warning": 30,
            "no_order_days": 90,
            "support_ticket_weight": 10,
        },
        BusinessType.DIGITAL_PRODUCTS: {
            "inactive_days_critical": 45,
            "inactive_days_warning": 21,
            "no_order_days": 60,
            "support_ticket_weight": 10,
        },
        BusinessType.HEALTH_WELLNESS: {
            "inactive_days_critical": 30,
            "inactive_days_warning": 14,
            "no_order_days": 45,
            "support_ticket_weight": 10,
        },
        BusinessType.HOME_DECOR: {
            "inactive_days_critical": 90,
            "inactive_days_warning": 45,
            "no_order_days": 120,
            "support_ticket_weight": 10,
        },
        BusinessType.HANDCRAFT: {
            "inactive_days_critical": 90,
            "inactive_days_warning": 45,
            "no_order_days": 120,
            "support_ticket_weight": 10,
        },
        BusinessType.OTHER: {
            "inactive_days_critical": 30,
            "inactive_days_warning": 14,
            "no_order_days": 60,
            "support_ticket_weight": 10,
        },
    }

    ACTIONS: Dict[BusinessType, str] = {
        BusinessType.SOFTWARE: "Ofrecer onboarding personalizado o descuento en renovación anual",
        BusinessType.CONSULTING: "Enviar case study o invitar a webinar exclusivo",
        BusinessType.SERVICES: "Ofrecer descuento en próximo servicio o paquete",
        BusinessType.FOOD_BEVERAGE: "Enviar cupón de descuento o promoción de combo",
        BusinessType.FASHION_BEAUTY: "Enviar lookbook nuevo o descuento temporada",
        BusinessType.PHYSICAL_PRODUCTS: "Enviar oferta de envío gratis o bundle",
        BusinessType.DIGITAL_PRODUCTS: "Ofrecer contenido gratuito de valor o descuento en próxima compra",
        BusinessType.HEALTH_WELLNESS: "Enviar plan de bienestar personalizado o descuento en suscripción",
        BusinessType.HOME_DECOR: "Enviar catálogo de novedades o consultoría de diseño gratis",
        BusinessType.HANDCRAFT: "Ofrecer personalización exclusiva o descuento por recomendación",
        BusinessType.OTHER: "Enviar oferta de re-engagement",
    }

    @classmethod
    def get_thresholds(cls, business_type: Optional[BusinessType]) -> Dict[str, int]:
        return cls.THRESHOLDS.get(business_type, cls.THRESHOLDS[BusinessType.OTHER])

    @classmethod
    def get_recommended_action(cls, business_type: Optional[BusinessType]) -> str:
        return cls.ACTIONS.get(business_type, cls.ACTIONS[BusinessType.OTHER])


class LtvAdapter:
    """Returns business-type-specific LTV prediction adjustments."""

    MULTIPLIERS: Dict[BusinessType, Dict[str, float]] = {
        BusinessType.SOFTWARE: {"predicted_orders_multiplier": 1.5, "confidence_boost": 0.1},
        BusinessType.CONSULTING: {"predicted_orders_multiplier": 0.8, "confidence_boost": 0.05},
        BusinessType.SERVICES: {"predicted_orders_multiplier": 1.0, "confidence_boost": 0.0},
        BusinessType.FOOD_BEVERAGE: {"predicted_orders_multiplier": 2.5, "confidence_boost": 0.15},
        BusinessType.FASHION_BEAUTY: {"predicted_orders_multiplier": 2.0, "confidence_boost": 0.1},
        BusinessType.PHYSICAL_PRODUCTS: {"predicted_orders_multiplier": 1.8, "confidence_boost": 0.1},
        BusinessType.DIGITAL_PRODUCTS: {"predicted_orders_multiplier": 1.2, "confidence_boost": 0.05},
        BusinessType.HEALTH_WELLNESS: {"predicted_orders_multiplier": 1.8, "confidence_boost": 0.1},
        BusinessType.HOME_DECOR: {"predicted_orders_multiplier": 0.6, "confidence_boost": 0.05},
        BusinessType.HANDCRAFT: {"predicted_orders_multiplier": 1.0, "confidence_boost": 0.05},
        BusinessType.OTHER: {"predicted_orders_multiplier": 1.0, "confidence_boost": 0.0},
    }

    @classmethod
    def get_multipliers(cls, business_type: Optional[BusinessType]) -> Dict[str, float]:
        return cls.MULTIPLIERS.get(business_type, cls.MULTIPLIERS[BusinessType.OTHER])


class AlertAdapter:
    """Returns business-type-specific anomaly detection thresholds."""

    REVENUE_THRESHOLDS: Dict[BusinessType, Dict[str, float]] = {
        BusinessType.SOFTWARE: {"drop_critical": -15.0, "growth_opportunity": 30.0},
        BusinessType.CONSULTING: {"drop_critical": -25.0, "growth_opportunity": 40.0},
        BusinessType.SERVICES: {"drop_critical": -20.0, "growth_opportunity": 35.0},
        BusinessType.FOOD_BEVERAGE: {"drop_critical": -10.0, "growth_opportunity": 25.0},
        BusinessType.FASHION_BEAUTY: {"drop_critical": -20.0, "growth_opportunity": 35.0},
        BusinessType.PHYSICAL_PRODUCTS: {"drop_critical": -20.0, "growth_opportunity": 35.0},
        BusinessType.DIGITAL_PRODUCTS: {"drop_critical": -25.0, "growth_opportunity": 40.0},
        BusinessType.HEALTH_WELLNESS: {"drop_critical": -15.0, "growth_opportunity": 30.0},
        BusinessType.HOME_DECOR: {"drop_critical": -25.0, "growth_opportunity": 40.0},
        BusinessType.HANDCRAFT: {"drop_critical": -25.0, "growth_opportunity": 40.0},
        BusinessType.OTHER: {"drop_critical": -20.0, "growth_opportunity": 50.0},
    }

    RECOMMENDATIONS: Dict[BusinessType, Dict[str, str]] = {
        BusinessType.SOFTWARE: {
            "drop": "Revisar churn de usuarios activos y ofrecer descuento en renovación anual",
            "growth": "Aumentar presupuesto de ads y lanzar programa de referrals",
        },
        BusinessType.CONSULTING: {
            "drop": "Revisar pipeline de propuestas y hacer follow-up con leads calificados",
            "growth": "Aumentar tarifas y filtrar clientes de mayor valor",
        },
        BusinessType.SERVICES: {
            "drop": "Activar campaña de re-engagement con descuento en próximo servicio",
            "growth": "Aumentar presupuesto de ads y lanzar upsell de paquetes",
        },
        BusinessType.FOOD_BEVERAGE: {
            "drop": "Revisar calidad de últimas reseñas y activar promoción de combos",
            "growth": "Ampliar horarios o zonas de delivery, lanzar menú nuevo",
        },
        BusinessType.FASHION_BEAUTY: {
            "drop": "Enviar lookbook de nueva temporada con descuento early access",
            "growth": "Lanzar colección limitada o colaboración con influencers",
        },
        BusinessType.PHYSICAL_PRODUCTS: {
            "drop": "Activar oferta de envío gratis o bundle por compra mínima",
            "growth": "Ampliar stock de productos más vendidos y lanzar cross-sell",
        },
        BusinessType.DIGITAL_PRODUCTS: {
            "drop": "Revisar funnel de ventas y ofrecer lead magnet actualizado",
            "growth": "Lanzar curso nuevo o membership con precio de lanzamiento",
        },
        BusinessType.HEALTH_WELLNESS: {
            "drop": "Enviar contenido de valor y ofrecer consulta gratuita de retorno",
            "growth": "Lanzar programa de transformación de 90 días o retiro",
        },
        BusinessType.HOME_DECOR: {
            "drop": "Ofrecer consultoría de diseño gratuita o envío gratis",
            "growth": "Lanzar colección de temporada o partnership con arquitectos",
        },
        BusinessType.HANDCRAFT: {
            "drop": "Destacar proceso artesanal y ofrecer personalización exclusiva",
            "growth": "Lanzar edición limitada o workshop de creación",
        },
        BusinessType.OTHER: {
            "drop": "Activar workflow de re-engagement y revisar ads",
            "growth": "Aumentar presupuesto de ads y lanzar upsell",
        },
    }

    @classmethod
    def get_revenue_thresholds(cls, business_type: Optional[BusinessType]) -> Dict[str, float]:
        return cls.REVENUE_THRESHOLDS.get(business_type, cls.REVENUE_THRESHOLDS[BusinessType.OTHER])

    @classmethod
    def get_recommendations(cls, business_type: Optional[BusinessType]) -> Dict[str, str]:
        return cls.RECOMMENDATIONS.get(business_type, cls.RECOMMENDATIONS[BusinessType.OTHER])


class DashboardKPIAdapter:
    """Returns prioritized KPIs for the dashboard summary."""

    KPIs: Dict[BusinessType, List[Dict[str, Any]]] = {
        BusinessType.SOFTWARE: [
            {"key": "mrr", "label": "MRR", "priority": 1},
            {"key": "active_users", "label": "Usuarios Activos", "priority": 2},
            {"key": "churn_rate", "label": "Churn Rate", "priority": 3},
            {"key": "trial_to_paid", "label": "Trial → Paid", "priority": 4},
            {"key": "nps", "label": "NPS", "priority": 5},
        ],
        BusinessType.CONSULTING: [
            {"key": "pipeline_value", "label": "Pipeline", "priority": 1},
            {"key": "proposal_win_rate", "label": "Win Rate", "priority": 2},
            {"key": "avg_project_value", "label": "Ticket Promedio", "priority": 3},
            {"key": "client_retention", "label": "Retención", "priority": 4},
            {"key": "referrals", "label": "Referidos", "priority": 5},
        ],
        BusinessType.SERVICES: [
            {"key": "bookings", "label": "Reservas", "priority": 1},
            {"key": "revenue", "label": "Ingresos", "priority": 2},
            {"key": "utilization_rate", "label": "Ocupación", "priority": 3},
            {"key": "repeat_rate", "label": "Tasa de Repetición", "priority": 4},
            {"key": "nps", "label": "NPS", "priority": 5},
        ],
        BusinessType.FOOD_BEVERAGE: [
            {"key": "orders", "label": "Pedidos", "priority": 1},
            {"key": "revenue", "label": "Ingresos", "priority": 2},
            {"key": "avg_ticket", "label": "Ticket Promedio", "priority": 3},
            {"key": "delivery_time", "label": "Tiempo de Entrega", "priority": 4},
            {"key": "repeat_rate", "label": "Tasa de Repetición", "priority": 5},
        ],
        BusinessType.FASHION_BEAUTY: [
            {"key": "revenue", "label": "Ingresos", "priority": 1},
            {"key": "conversion_rate", "label": "Conversión", "priority": 2},
            {"key": "return_rate", "label": "Tasa de Devolución", "priority": 3},
            {"key": "avg_ticket", "label": "Ticket Promedio", "priority": 4},
            {"key": "new_vs_returning", "label": "Nuevos vs Recurrentes", "priority": 5},
        ],
        BusinessType.PHYSICAL_PRODUCTS: [
            {"key": "revenue", "label": "Ingresos", "priority": 1},
            {"key": "orders", "label": "Pedidos", "priority": 2},
            {"key": "conversion_rate", "label": "Conversión", "priority": 3},
            {"key": "avg_ticket", "label": "Ticket Promedio", "priority": 4},
            {"key": "inventory_turnover", "label": "Rotación de Stock", "priority": 5},
        ],
        BusinessType.DIGITAL_PRODUCTS: [
            {"key": "revenue", "label": "Ingresos", "priority": 1},
            {"key": "leads", "label": "Leads", "priority": 2},
            {"key": "conversion_rate", "label": "Conversión", "priority": 3},
            {"key": "content_engagement", "label": "Engagement", "priority": 4},
            {"key": "upsell_rate", "label": "Upsell", "priority": 5},
        ],
        BusinessType.HEALTH_WELLNESS: [
            {"key": "subscribers", "label": "Suscriptores", "priority": 1},
            {"key": "retention_rate", "label": "Retención", "priority": 2},
            {"key": "avg_ticket", "label": "Ticket Promedio", "priority": 3},
            {"key": "engagement", "label": "Engagement", "priority": 4},
            {"key": "referrals", "label": "Referidos", "priority": 5},
        ],
        BusinessType.HOME_DECOR: [
            {"key": "revenue", "label": "Ingresos", "priority": 1},
            {"key": "avg_ticket", "label": "Ticket Promedio", "priority": 2},
            {"key": "consultation_to_sale", "label": "Consulta → Venta", "priority": 3},
            {"key": "project_value", "label": "Valor Proyecto", "priority": 4},
            {"key": "repeat_rate", "label": "Recompra", "priority": 5},
        ],
        BusinessType.HANDCRAFT: [
            {"key": "orders", "label": "Pedidos", "priority": 1},
            {"key": "revenue", "label": "Ingresos", "priority": 2},
            {"key": "custom_orders", "label": "Pedidos Personalizados", "priority": 3},
            {"key": "avg_ticket", "label": "Ticket Promedio", "priority": 4},
            {"key": "review_score", "label": "Reviews", "priority": 5},
        ],
        BusinessType.OTHER: [
            {"key": "revenue", "label": "Ingresos", "priority": 1},
            {"key": "orders", "label": "Pedidos", "priority": 2},
            {"key": "leads", "label": "Leads", "priority": 3},
            {"key": "conversion_rate", "label": "Conversión", "priority": 4},
            {"key": "nps", "label": "NPS", "priority": 5},
        ],
    }

    @classmethod
    def get_kpis(cls, business_type: Optional[BusinessType]) -> List[Dict[str, Any]]:
        return cls.KPIs.get(business_type, cls.KPIs[BusinessType.OTHER])
