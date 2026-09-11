"""Default Toggles Seed Data"""

import uuid
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.automations.models import AutomationToggle


DEFAULT_TOGGLES = [
    # AGENTS (4)
    {
        "toggle_key": "agent:lead_scorer",
        "category": "agent",
        "display_name": "Lead Scorer IA",
        "description": "Califica automáticamente leads por probabilidad de conversión",
        "icon": "🎯",
        "monthly_limit": 1000,
    },
    {
        "toggle_key": "agent:cold_email",
        "category": "agent",
        "display_name": "Agente Cold Email",
        "description": "Redacta y envía emails de prospección",
        "icon": "📧",
        "monthly_limit": 500,
    },
    {
        "toggle_key": "agent:negotiation",
        "category": "agent",
        "display_name": "Agente de Negociación",
        "description": "Estrategia de cierre y manejo de objeciones",
        "icon": "🤝",
        "monthly_limit": 200,
    },
    {
        "toggle_key": "agent:competitor_intel",
        "category": "agent",
        "display_name": "Inteligencia Competitiva",
        "description": "Monitoreo y análisis de competidores",
        "icon": "🔍",
        "monthly_limit": None,
    },
    # AUTOMATIONS (3)
    {
        "toggle_key": "automation:email_sequences",
        "category": "automation",
        "display_name": "Secuencias de Email",
        "description": "Workflows automáticos de email nurturing",
        "icon": "📨",
        "monthly_limit": None,
    },
    {
        "toggle_key": "automation:fomo_campaigns",
        "category": "automation",
        "display_name": "Campañas FOMO",
        "description": "Urgencia + escasez + social proof",
        "icon": "⏰",
        "monthly_limit": None,
    },
    {
        "toggle_key": "automation:sms_marketing",
        "category": "automation",
        "display_name": "Marketing por SMS",
        "description": "Mensajes automáticos vía WhatsApp/SMS",
        "icon": "💬",
        "monthly_limit": 5000,
    },
    # FEATURES (3)
    {
        "toggle_key": "feature:dynamic_pricing",
        "category": "feature",
        "display_name": "Precios Dinámicos",
        "description": "Ajusta precios en tiempo real según demanda",
        "icon": "💰",
        "monthly_limit": None,
    },
    {
        "toggle_key": "feature:predictive_analytics",
        "category": "feature",
        "display_name": "Análisis Predictivo",
        "description": "Forecasting de demanda y churn",
        "icon": "🔮",
        "monthly_limit": None,
    },
    {
        "toggle_key": "feature:computer_use",
        "category": "feature",
        "display_name": "Computer Use (Browser Automation)",
        "description": "Automatización de tareas web (alto costo)",
        "icon": "🖥️",
        "monthly_limit": 100,
    },
    # INTEGRATIONS (2)
    {
        "toggle_key": "integration:stripe",
        "category": "integration",
        "display_name": "Stripe Payments",
        "description": "Procesamiento de pagos Stripe",
        "icon": "💳",
        "monthly_limit": None,
    },
    {
        "toggle_key": "integration:meta_ads",
        "category": "integration",
        "display_name": "Meta Ads Automation",
        "description": "Creación + gestión de campañas Meta",
        "icon": "📱",
        "monthly_limit": None,
    },
]


async def seed_toggles_for_business(business_id: UUID, db: AsyncSession):
    """Crea los toggles por defecto para un negocio nuevo."""
    for toggle_data in DEFAULT_TOGGLES:
        # Verificar si ya existe
        existing = await db.execute(
            select(AutomationToggle).where(
                AutomationToggle.business_id == business_id,
                AutomationToggle.toggle_key == toggle_data["toggle_key"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Crear nuevo toggle
        toggle = AutomationToggle(
            id=uuid.uuid4(),
            business_id=business_id,
            toggle_key=toggle_data["toggle_key"],
            category=toggle_data["category"],
            display_name=toggle_data["display_name"],
            description=toggle_data.get("description"),
            icon=toggle_data.get("icon"),
            monthly_limit=toggle_data.get("monthly_limit"),
            is_enabled=True,
        )
        db.add(toggle)

    await db.commit()
