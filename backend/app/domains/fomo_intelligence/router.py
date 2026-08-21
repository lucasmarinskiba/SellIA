"""FOMO Intelligence API: registro + inteligencia de las 4 estrategias FOMO."""
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domains.fomo_intelligence.service import FOMOIntelligenceService


router = APIRouter(prefix="/api/v1/fomo-intelligence", tags=["fomo-intelligence"])


@router.post("/register-strategy")
async def register_strategy_application(
    business_id: str = Body(...),
    strategy_type: str = Body(..., description="escasez_real | prueba_social | exclusividad | transparencia"),
    target_type: str = Body(...),
    target_id: str = Body(...),
    real_data_source: str = Body(..., description="De dónde sale el dato real, ej: inventory_count"),
    data_snapshot: dict = Body(..., description="El dato real capturado en este momento"),
    channel: str | None = Body(None),
    personality_target: str | None = Body(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Registra un uso real de una de las 4 estrategias FOMO. Rechaza datos incompletos."""
    try:
        application = await FOMOIntelligenceService.register_strategy_application(
            db, business_id, strategy_type, target_type, target_id,
            real_data_source, data_snapshot, channel, personality_target,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "application_id": application.id,
        "strategy_type": application.strategy_type.value,
        "generated_message": application.generated_message,
        "real_data_source": application.real_data_source,
        "applied_at": application.applied_at.isoformat(),
    }


@router.post("/record-outcome")
async def record_outcome(
    application_id: str = Body(...),
    impressions: int = Body(...),
    clicks: int = Body(...),
    conversions: int = Body(...),
    revenue: float = Body(0.0),
    perceived_as_genuine: bool | None = Body(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Registra el resultado medido de una aplicación de estrategia."""
    outcome = await FOMOIntelligenceService.record_outcome(
        db, application_id, impressions, clicks, conversions, revenue, perceived_as_genuine
    )
    return {
        "outcome_id": outcome.id,
        "application_id": outcome.application_id,
        "conversion_rate": outcome.conversions / max(outcome.impressions, 1),
        "measured_at": outcome.measured_at.isoformat(),
    }


@router.get("/intelligence-report")
async def get_intelligence_report(db: AsyncSession = Depends(get_db)) -> dict:
    """Agrega todas las applications/outcomes y devuelve inteligencia por estrategia+personalidad."""
    return await FOMOIntelligenceService.generate_intelligence_report(db)


@router.get("/recommend-strategy/{personality_type}")
async def recommend_strategy(
    personality_type: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Recomienda cuál de las 4 estrategias usar para una personalidad dada."""
    return await FOMOIntelligenceService.recommend_strategy(db, personality_type)


@router.get("/transparency-dashboard")
async def get_transparency_dashboard(db: AsyncSession = Depends(get_db)) -> dict:
    """Métricas reales del sistema, listas para usarse como contenido de la estrategia Transparencia."""
    return await FOMOIntelligenceService.get_transparency_dashboard(db)


@router.get("/strategies")
async def list_strategies() -> dict:
    """Lista las 4 estrategias FOMO con su descripción + campos de dato real requeridos."""
    return {
        "strategies": [
            {
                "id": "escasez_real",
                "name": "Escasez real",
                "description": "Muestra que los cupos, lugares o productos son muy pocos.",
                "requires_fields": ["slots_remaining", "total_slots"],
            },
            {
                "id": "prueba_social",
                "name": "Prueba social",
                "description": "Comparte fotos, mensajes o testimonios de personas que ya participan o compraron.",
                "requires_fields": ["buyer_name_or_alias", "result_or_quote"],
            },
            {
                "id": "exclusividad",
                "name": "Exclusividad",
                "description": "Da acceso solo a un grupo reducido o por tiempo limitado.",
                "requires_fields": ["group_size_or_criteria", "access_window"],
            },
            {
                "id": "transparencia",
                "name": "Transparencia",
                "description": "Muestra resultados y logros reales de tu comunidad para despertar interés genuino.",
                "requires_fields": ["metric_name", "metric_value", "verification_source"],
            },
        ]
    }
