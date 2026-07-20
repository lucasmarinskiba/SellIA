"""Computer Use — Brain Integration Router

Endpoints para que Computer Use consulte SellIA Brain:
- GET /strategy — obtener estrategia óptima por contexto
- POST /response-prompt — generar prompt para responder mensaje
- POST /score-lead — scoring automático de lead
- POST /detect-signals — detectar señales de compra
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.computer_use.services.sellia_brain_service import (
    get_brain_service,
    ActionContext,
    SalesStage,
    Platform,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== Request/Response Models ==========


class StrategyRequest(BaseModel):
    """Solicitud de estrategia al Brain."""

    platform: str = Field(..., description="Plataforma: whatsapp, email, instagram, etc")
    stage: str = Field(..., description="Etapa de venta: awareness, consideration, decision, closure, etc")
    customer_profile: Optional[dict] = Field(default=None, description="Perfil del cliente")
    product_info: Optional[dict] = Field(default=None, description="Información del producto")
    objections: Optional[list] = Field(default=[], description="Objeciones del cliente")


class StrategyResponse(BaseModel):
    """Respuesta con estrategia recomendada."""

    strategy_id: str
    strategy_name: str
    stage: str
    confidence: float
    tactics: list
    prompt_template: str
    reasoning: str
    metadata: dict


class ResponsePromptRequest(BaseModel):
    """Solicitud de prompt para responder mensaje."""

    instruction: str = Field(..., description="Qué debe lograr la respuesta")
    platform: str = Field(..., description="Plataforma")
    stage: str = Field(..., description="Etapa de venta")
    customer_profile: Optional[dict] = Field(default=None)
    message_history: Optional[list] = Field(default=None)
    objections: Optional[list] = Field(default=[])


class ResponsePromptResponse(BaseModel):
    """Respuesta con prompt listo para usar."""

    prompt: str
    strategy_name: str
    confidence: float


class LeadScoringRequest(BaseModel):
    """Solicitud de scoring de lead."""

    conversation: list = Field(..., description="Historial de conversación")
    customer_profile: dict = Field(..., description="Perfil del cliente")


class LeadScoringResponse(BaseModel):
    """Resultado de scoring."""

    score: int  # 0-100
    temperature: str  # hot, warm, cold
    signals: list
    recommended_action: str


class SalesSignalRequest(BaseModel):
    """Solicitud de detección de señales de compra."""

    message: str = Field(..., description="Mensaje del cliente")
    platform: str = Field(..., description="Plataforma")
    stage: str = Field(..., description="Etapa de venta")


class SalesSignalResponse(BaseModel):
    """Resultado de detección de señales."""

    signal_found: bool
    signal_type: Optional[str]
    recommended_action: str
    confidence: float


# ========== Endpoints ==========


@router.post("/brain/strategy", response_model=StrategyResponse)
async def get_strategy(
    request: StrategyRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Consulta SellIA Brain por estrategia óptima.

    Retorna: estrategia recomendada + tactics + confidence score.
    """
    try:
        # Validar plataforma
        try:
            platform = Platform(request.platform)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform. Valid: {', '.join([p.value for p in Platform])}",
            )

        # Validar etapa
        try:
            stage = SalesStage(request.stage)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage. Valid: {', '.join([s.value for s in SalesStage])}",
            )

        # Crear contexto
        context = ActionContext(
            platform=platform,
            stage=stage,
            customer_profile=request.customer_profile,
            product_info=request.product_info,
            objections=request.objections,
        )

        # Consultar Brain
        brain_service = get_brain_service()
        recommendation = await brain_service.get_strategy(context)

        if not recommendation:
            raise HTTPException(
                status_code=404,
                detail="No strategy found for this context",
            )

        return StrategyResponse(**recommendation.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brain/response-prompt", response_model=ResponsePromptResponse)
async def get_response_prompt(
    request: ResponsePromptRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Genera prompt completo para responder mensaje.

    Combina: estrategia + contexto + instrucción específica.
    """
    try:
        # Validar
        try:
            platform = Platform(request.platform)
            stage = SalesStage(request.stage)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Crear contexto
        context = ActionContext(
            platform=platform,
            stage=stage,
            customer_profile=request.customer_profile,
            conversation_history=request.message_history,
            objections=request.objections,
        )

        # Generar prompt
        brain_service = get_brain_service()
        prompt = await brain_service.get_response_prompt(context, request.instruction)

        # Obtener estrategia para incluir en respuesta
        strategy = await brain_service.get_strategy(context)
        strategy_name = strategy.strategy_name if strategy else "default"
        confidence = strategy.confidence if strategy else 0.5

        return ResponsePromptResponse(
            prompt=prompt,
            strategy_name=strategy_name,
            confidence=confidence,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating response prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brain/score-lead", response_model=LeadScoringResponse)
async def score_lead(
    request: LeadScoringRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Scoring automático de lead (hot/warm/cold).

    Analiza conversación + perfil → score + temperatura + acción recomendada.
    """
    try:
        brain_service = get_brain_service()
        result = await brain_service.score_lead(
            request.conversation,
            request.customer_profile,
        )

        return LeadScoringResponse(**result)

    except Exception as e:
        logger.error(f"Error scoring lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brain/detect-signals", response_model=SalesSignalResponse)
async def detect_sales_signals(
    request: SalesSignalRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Detecta señales de compra en mensaje.

    Identifica palabras clave → recomienda próxima acción (cerrar, seguir, escalar).
    """
    try:
        try:
            platform = Platform(request.platform)
            stage = SalesStage(request.stage)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        context = ActionContext(
            platform=platform,
            stage=stage,
        )

        brain_service = get_brain_service()
        result = await brain_service.detect_sales_signals(request.message, context)

        return SalesSignalResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
