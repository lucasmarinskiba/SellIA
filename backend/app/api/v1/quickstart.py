"""
Quick-start onboarding: 5 min → operacional.

Usuario responde 5 preguntas → Sistema deduce contexto → Auto-activa stack óptimo → VENDE.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from datetime import datetime
import logging

router = APIRouter(prefix="/api/v1/quickstart", tags=["onboarding"])
logger = logging.getLogger(__name__)


class QuickstartInput(BaseModel):
    """5 preguntas críticas."""
    product: str  # "software SaaS", "ropa ecommerce", "coaching online"
    price_range: str  # "<100", "100-1k", "1k-10k", "10k+"
    primary_channel: str  # "linkedin", "instagram", "whatsapp", "web", "direct"
    stage: str  # "startup", "growth", "scale"
    sales_link: str  # URL válida de venta/red/web


class QuickstartResponse(BaseModel):
    """Respuesta: perfil + stack activado + status."""
    account_id: str
    industry_detected: str
    agents_activated: List[str]
    status: str  # "ready"
    first_steps: List[str]
    metrics_target_month_1: Dict[str, Any]


@router.post("/onboarding", response_model=QuickstartResponse)
async def quickstart_onboarding(input_data: QuickstartInput):
    """
    Onboarding ultra-rápido: 5 preguntas → Operacional minuto 0.

    Workflow:
    1. Capturar 5 datos críticos
    2. Detectar industria automáticamente
    3. Deducir contexto faltante
    4. Activar stack óptimo
    5. Iniciar vendedor maestro
    6. Retornar: account_id + agentes listos + primeros pasos
    """

    try:
        logger.info(f"Quick-start: {input_data.product}")

        # 1. Auto-detectar industria
        product_lower = input_data.product.lower()
        
        if "saas" in product_lower or "software" in product_lower:
            industry = "SaaS"
            agents = ["master_seller", "spin_agent", "onboarding_specialist", "lead_scorer"]
            ticket_estimate = "1k-5k"
            cycle_estimate = "30-60 días"
        elif "ecommerce" in product_lower or "ropa" in product_lower or "producto" in product_lower:
            industry = "Ecommerce"
            agents = ["master_seller", "impulse_closer", "urgency_maximizer", "retention_specialist"]
            ticket_estimate = "50-500"
            cycle_estimate = "minutos-días"
        elif "coaching" in product_lower or "consulting" in product_lower or "servicio" in product_lower:
            industry = "Servicios"
            agents = ["master_seller", "consultative_agent", "relationship_specialist", "success_manager"]
            ticket_estimate = "500-5k"
            cycle_estimate = "7-30 días"
        elif "bienes" in product_lower or "real estate" in product_lower or "propiedad" in product_lower:
            industry = "Real Estate"
            agents = ["master_seller", "emotion_seller", "trust_builder", "lifecycle_manager"]
            ticket_estimate = "50k-500k"
            cycle_estimate = "30-90 días"
        else:
            industry = "Otros"
            agents = ["master_seller", "sales_architect", "lifecycle_manager"]
            ticket_estimate = "variable"
            cycle_estimate = "variable"

        # 2. Generar account_id
        account_id = f"acc_{datetime.utcnow().timestamp():.0f}"

        # 3. Determinar primeros pasos
        first_steps = [
            f"✅ Industria detectada: {industry}",
            f"✅ Stack activado: {', '.join(agents[:3])}",
            "✅ Vendedor maestro en vivo (24/7)",
            "📱 Conectá tu WhatsApp/Instagram/Email (si quieres automático)",
            "📊 Monitorea dashboard de métricas en vivo",
            f"🎯 Meta mes 1: {ticket_estimate} ticket, {cycle_estimate} ciclo"
        ]

        # 4. Retornar
        return QuickstartResponse(
            account_id=account_id,
            industry_detected=industry,
            agents_activated=agents,
            status="ready",
            first_steps=first_steps,
            metrics_target_month_1={
                "leads_per_day": 5,
                "discovery_rate": 0.4,
                "close_rate": 0.2,
                "expected_mrr": 2000 if "SaaS" in industry else 5000 if "Ecommerce" in industry else 3500
            }
        )

    except Exception as e:
        logger.error(f"Error en quickstart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industry-profiles")
async def get_industry_profiles():
    """Referencia de perfiles de industria."""

    return {
        "profiles": [
            {
                "industry": "SaaS",
                "agents": ["master_seller", "spin_agent", "onboarding_specialist", "retention_specialist"],
                "methods": ["SPIN discovery", "Trial free 14d", "Consultative", "Lifecycle mgmt"],
                "expected_cycle": "30-60 días",
                "expected_close_rate": "20-30%"
            },
            {
                "industry": "Ecommerce",
                "agents": ["master_seller", "impulse_closer", "urgency_maximizer"],
                "methods": ["Assumptive close", "FOMO + urgency", "Social proof", "1-click checkout"],
                "expected_cycle": "minutos-días",
                "expected_close_rate": "3-8%"
            },
            {
                "industry": "Servicios",
                "agents": ["master_seller", "consultative_agent", "relationship_specialist"],
                "methods": ["Consultative selling", "Relationship first", "Success manager", "QBR trimestral"],
                "expected_cycle": "7-30 días",
                "expected_close_rate": "25-35%"
            },
            {
                "industry": "Luxury",
                "agents": ["master_seller", "emotion_seller", "exclusivity_specialist"],
                "methods": ["Status + exclusivity", "Origin storytelling", "VIP community", "Customization"],
                "expected_cycle": "14-60 días",
                "expected_close_rate": "10-20%"
            }
        ]
    }
