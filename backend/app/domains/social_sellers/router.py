"""Social Seller API Router"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from app.domains.social_sellers.models import SocialSeller, SellerCustomerRelationship, SellerPerformance, UnifiedCustomer
from app.domains.social_sellers.schemas import (
    SocialSellerCreate, SocialSellerUpdate, SocialSellerResponse,
    SellerCustomerCreate, SellerCustomerResponse, CustomerInsightResponse,
    SellerPerformanceResponse, SellerPipelineResponse, TeamReportResponse,
    RecordSaleRequest, RecordSaleResponse, ExecuteActionRequest, ExecuteActionResponse,
    WallOfFameCustomer, CustomerBadgeResponse, LoyaltySegmentsResponse,
    LoyaltyActionRequest, LoyaltyActionResponse,
    UnifiedCustomerResponse, UnifiedCustomerProfileResponse, MergeRequest, MergeResponse,
    MergeSuggestionResponse,
    RadarDataResponse, OpportunityScoreResponse, RadarActRequest, RadarActResponse,
    IdealCustomerProfile, LookalikeLead, LookalikeReportResponse,
)
from app.domains.social_sellers.engine import SocialSellerEngine
from app.domains.social_sellers.loyalty_engine import LoyaltyEngine
from app.domains.social_sellers.lifetime_engine import CustomerLifetimeEngine
from app.domains.social_sellers.customer_unification import CustomerIdentityMatcher

router = APIRouter(prefix="/social-sellers", tags=["social-sellers"])


# ========== Helpers ==========

async def _get_seller_or_404(db: AsyncSession, seller_id: uuid.UUID) -> SocialSeller:
    engine = SocialSellerEngine(db)
    seller = await engine.get_seller(seller_id)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Seller no encontrado.',
        )
    return seller


async def _require_business_access(db: AsyncSession, business_id: uuid.UUID, user: User) -> None:
    engine = SocialSellerEngine(db)
    has_access = await engine._check_business_access(business_id, user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='No tenés acceso a este negocio.',
        )


async def _require_seller_access(db: AsyncSession, seller_id: uuid.UUID, user: User) -> SocialSeller:
    seller = await _get_seller_or_404(db, seller_id)
    await _require_business_access(db, seller.business_id, user)
    return seller


# ========== CRUD ==========

@router.post("", response_model=SocialSellerResponse, status_code=status.HTTP_201_CREATED)
async def create_seller(
    data: SocialSellerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea un nuevo social seller."""
    await _require_business_access(db, data.business_id, current_user)
    engine = SocialSellerEngine(db)
    seller = await engine.create_seller(
        business_id=data.business_id,
        platform=data.platform,
        name=data.name,
        personality_slug=data.personality_slug,
        voice_config=data.voice_config,
        greeting_message=data.greeting_message,
        closing_message=data.closing_message,
        ai_auto_reply=data.ai_auto_reply,
    )
    return seller


@router.get("", response_model=List[SocialSellerResponse])
async def list_sellers(
    business_id: uuid.UUID,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista los sellers de un negocio."""
    await _require_business_access(db, business_id, current_user)
    engine = SocialSellerEngine(db)
    return await engine.get_sellers(business_id, status=status)


@router.get("/{seller_id}", response_model=SocialSellerResponse)
async def get_seller(
    seller_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene el detalle de un seller."""
    seller = await _require_seller_access(db, seller_id, current_user)
    return seller


@router.put("/{seller_id}", response_model=SocialSellerResponse)
async def update_seller(
    seller_id: uuid.UUID,
    data: SocialSellerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualiza un seller existente."""
    await _require_seller_access(db, seller_id, current_user)
    engine = SocialSellerEngine(db)
    updates = data.model_dump(exclude_unset=True)
    seller = await engine.update_seller(seller_id, **updates)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Seller no encontrado.',
        )
    return seller


@router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(
    seller_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Elimina un seller."""
    await _require_seller_access(db, seller_id, current_user)
    engine = SocialSellerEngine(db)
    deleted = await engine.delete_seller(seller_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Seller no encontrado.',
        )
    return None


# ========== Customers ==========

@router.post("/{seller_id}/customers", response_model=SellerCustomerResponse, status_code=status.HTTP_201_CREATED)
async def assign_customer(
    seller_id: uuid.UUID,
    data: SellerCustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Asigna un cliente (conversación) a un seller."""
    await _require_seller_access(db, seller_id, current_user)
    engine = SocialSellerEngine(db)
    try:
        rel = await engine.assign_customer(seller_id, data.customer_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return rel


@router.get("/{seller_id}/customers", response_model=List[SellerCustomerResponse])
async def list_customers(
    seller_id: uuid.UUID,
    stage: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista los clientes asignados a un seller."""
    await _require_seller_access(db, seller_id, current_user)
    engine = SocialSellerEngine(db)
    return await engine.get_seller_customers(seller_id, stage=stage, limit=limit)


# ========== Unified Customers ==========

@router.get("/customers/unified", response_model=List[UnifiedCustomerResponse])
async def list_unified_customers(
    business_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista los clientes unificados de un negocio."""
    await _require_business_access(db, business_id, current_user)
    matcher = CustomerIdentityMatcher(db)
    customers = await matcher.list_unified_customers(business_id, limit=limit, offset=offset)
    return customers


@router.get("/customers/unified/{unified_customer_id}", response_model=UnifiedCustomerProfileResponse)
async def get_unified_customer(
    unified_customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene el perfil unificado completo de un cliente."""
    matcher = CustomerIdentityMatcher(db)
    profile = await matcher.get_unified_profile(unified_customer_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Cliente unificado no encontrado.',
        )
    return profile


@router.post("/customers/merge", response_model=MergeResponse)
async def merge_customers(
    data: MergeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fusiona dos clientes unificados."""
    matcher = CustomerIdentityMatcher(db)
    result = await matcher.merge_customers(
        business_id=current_user.business_id if hasattr(current_user, 'business_id') else None,
        target_id=data.target_id,
        source_id=data.source_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No se pudo fusionar: verificá que ambos clientes existan.',
        )
    return {
        'status': 'merged',
        'target_id': data.target_id,
        'merged_source_id': data.source_id,
    }


@router.get("/customers/suggest-merge", response_model=List[MergeSuggestionResponse])
async def suggest_merge(
    business_id: uuid.UUID,
    customer_a_id: uuid.UUID,
    customer_b_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sugiere la fusión de dos clientes con puntaje de confianza."""
    await _require_business_access(db, business_id, current_user)
    matcher = CustomerIdentityMatcher(db)
    suggestion = await matcher.suggest_merge(business_id, customer_a_id, customer_b_id)
    return [{
        'customer_a_id': customer_a_id,
        'customer_b_id': customer_b_id,
        'score': suggestion['score'],
        'reasons': suggestion['reasons'],
    }]


# ========== Pipeline & Performance ==========

@router.get("/{seller_id}/pipeline", response_model=SellerPipelineResponse)
async def get_pipeline(
    seller_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene el pipeline desglosado por etapa de relación."""
    await _require_seller_access(db, seller_id, current_user)
    engine = SocialSellerEngine(db)
    return await engine.get_seller_pipeline(seller_id)


@router.get("/{seller_id}/performance", response_model=List[SellerPerformanceResponse])
async def get_performance(
    seller_id: uuid.UUID,
    period: str = Query("week"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene métricas de rendimiento del seller."""
    await _require_seller_access(db, seller_id, current_user)
    engine = SocialSellerEngine(db)
    return await engine.get_seller_performance(seller_id, period=period)


# ========== Sales & Actions ==========

@router.post("/{seller_id}/record-sale", response_model=RecordSaleResponse)
async def record_sale(
    seller_id: uuid.UUID,
    data: RecordSaleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registra una venta cerrada por el seller."""
    await _require_seller_access(db, seller_id, current_user)
    engine = SocialSellerEngine(db)
    result = await engine.record_sale(seller_id, data.conversation_id, data.amount)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No se pudo registrar la venta.',
        )
    return result


# ========== Lookalike Audience Engine ==========

@router.get('/lookalike/profile', response_model=IdealCustomerProfile)
async def get_lookalike_profile(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perfil del cliente ideal basado en el top 20% por LTV."""
    await _require_business_access(db, business_id, current_user)
    engine = LookalikeEngine(db)
    return await engine.build_ideal_customer_profile(business_id)


@router.get('/lookalike/leads', response_model=List[LookalikeLead])
async def get_lookalike_leads(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Leads priorizados por similitud al cliente ideal."""
    await _require_business_access(db, business_id, current_user)
    engine = LookalikeEngine(db)
    return await engine.prioritize_leads(business_id)


@router.get('/lookalike/similar-to/{customer_id}', response_model=List[LookalikeLead])
async def get_similar_to_customer(
    customer_id: uuid.UUID,
    business_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Leads más similares a un cliente específico."""
    await _require_business_access(db, business_id, current_user)
    engine = LookalikeEngine(db)
    return await engine.find_similar_to_customer(business_id, customer_id, limit=limit)


@router.get('/lookalike/report', response_model=LookalikeReportResponse)
async def get_lookalike_report(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reporte completo de lookalike audience."""
    await _require_business_access(db, business_id, current_user)
    engine = LookalikeEngine(db)
    return await engine.get_lookalike_report(business_id)


@router.get("/team-report", response_model=TeamReportResponse)
async def get_team_report(
    business_id: uuid.UUID,
    period: str = Query("week"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reporte agregado de todo el equipo de sellers."""
    await _require_business_access(db, business_id, current_user)
    engine = SocialSellerEngine(db)
    return await engine.get_team_report(business_id, period=period)


@router.post("/{seller_id}/actions", response_model=ExecuteActionResponse)
async def execute_action(
    seller_id: uuid.UUID,
    data: ExecuteActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ejecuta una acción del seller (enviar mensaje, esperar, ofrecer descuento)."""
    await _require_seller_access(db, seller_id, current_user)
    engine = SocialSellerEngine(db)

    if data.action == "decide":
        conversation_id = (data.payload or {}).get("conversation_id")
        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Se requiere conversation_id en payload.',
            )
        decision = await engine.decide_next_action(seller_id, uuid.UUID(conversation_id))
        if not decision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='No se encontró la relación con el cliente.',
            )
        return {
            "status": "success",
            "action": decision["action"],
            "result": decision,
        }

    # Acciones directas
    return {
        "status": "success",
        "action": data.action,
        "result": data.payload or {},
    }


# ========== Radar de Oportunidades ==========

@router.get("/radar", response_model=RadarDataResponse)
async def get_radar(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Datos principales para el Radar de Oportunidades."""
    await _require_business_access(db, business_id, current_user)
    engine = CustomerLifetimeEngine(db)
    return await engine.get_radar_data(business_id)


@router.get("/radar/opportunities", response_model=List[dict])
async def list_opportunities(
    business_id: uuid.UUID,
    heat_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista oportunidades filtradas por nivel de calor."""
    await _require_business_access(db, business_id, current_user)
    engine = CustomerLifetimeEngine(db)
    opps = await engine.detect_buying_moments(business_id, lookback_hours=168)
    if heat_level:
        opps = [o for o in opps if o['heat_level'] == heat_level.lower()]
    return opps


@router.get("/radar/{conversation_id}/score", response_model=OpportunityScoreResponse)
async def get_opportunity_score(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Score detallado de una oportunidad específica."""
    engine = CustomerLifetimeEngine(db)
    score_data = await engine.score_opportunity(conversation_id)
    return {
        "conversation_id": str(conversation_id),
        **score_data,
    }


@router.post("/radar/{conversation_id}/act", response_model=RadarActResponse)
async def execute_radar_action(
    conversation_id: uuid.UUID,
    data: RadarActRequest,
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ejecuta una acción recomendada desde el radar."""
    await _require_business_access(db, business_id, current_user)
    engine = CustomerLifetimeEngine(db)
    result = await engine.execute_radar_action(business_id, conversation_id, data.action, data.payload)
    return {
        "status": result.get("status", "success"),
        "action": result.get("action", data.action),
        "message": result.get("message"),
        "discount_pct": result.get("discount_pct"),
        "redirect_url": result.get("redirect_url"),
        "conversation_id": str(conversation_id),
        "detail": result.get("detail"),
    }


# ========== Wall of Fame & Loyalty ==========

@router.get("/wall-of-fame", response_model=List[WallOfFameCustomer])
async def get_wall_of_fame(
    business_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Devuelve el Wall of Fame: mejores clientes ordenados por LTV."""
    await _require_business_access(db, business_id, current_user)
    engine = LoyaltyEngine(db)
    return await engine.get_wall_of_fame(business_id, limit=limit)


@router.get("/customers/{customer_id}/badges", response_model=List[CustomerBadgeResponse])
async def get_customer_badges(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Devuelve todos los badges de un cliente."""
    engine = LoyaltyEngine(db)
    return await engine.get_customer_badges(customer_id)


@router.post("/customers/{customer_id}/badges/check", response_model=List[dict])
async def check_and_assign_badges(
    customer_id: uuid.UUID,
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evalúa criterios y asigna badges ganados a un cliente."""
    await _require_business_access(db, business_id, current_user)
    engine = LoyaltyEngine(db)
    return await engine.assign_badges(business_id, customer_id)


@router.get("/loyalty/segments", response_model=LoyaltySegmentsResponse)
async def get_loyalty_segments(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Devuelve segmentación RFM de clientes."""
    await _require_business_access(db, business_id, current_user)
    engine = LoyaltyEngine(db)
    return await engine.get_loyalty_segments(business_id)


@router.post("/customers/{customer_id}/actions", response_model=LoyaltyActionResponse)
async def create_loyalty_action(
    customer_id: uuid.UUID,
    data: LoyaltyActionRequest,
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ejecuta una acción de fidelización (regalo, VIP, testimonio, referido)."""
    await _require_business_access(db, business_id, current_user)
    engine = LoyaltyEngine(db)
    try:
        result = await engine.create_loyalty_action(business_id, customer_id, data.action_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result
