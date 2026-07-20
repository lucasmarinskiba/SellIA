"""
Sales Cycle Trigger — Usuario sube producto → Sistema actúa.

Endpoint: POST /api/v1/sales-cycle/start
Requiere: auth + producto + buyer
Retorna: cycle_id + status
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import logging
import uuid

from backend.app.core.orchestration.loop_engineering import LoopEngineering
from backend.app.core.orchestration.brain_computer_use import BrainComputerUseCoordinator
from backend.app.core.database.models import get_db

router = APIRouter(prefix="/api/v1/sales-cycle", tags=["sales"])
logger = logging.getLogger(__name__)


class ProductInput(BaseModel):
    name: str
    description: str
    price: float
    stock: int = 1
    images: list = []
    category: str = "general"


class BuyerInput(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    company: Optional[str] = None


class StartSalesCycleRequest(BaseModel):
    product: ProductInput
    buyer: BuyerInput


# Mock auth (reemplazar con JWT real)
def verify_auth(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    # TODO: Verificar JWT token real
    return {"user_id": "user_123", "token": token}


@router.post("/start")
async def start_sales_cycle(
    request: StartSalesCycleRequest,
    auth: dict = Depends(verify_auth),
    db = Depends(get_db),
):
    """
    Inicia ciclo venta completo.

    Flow:
    1. Valida producto + buyer
    2. Inicia Brain analysis
    3. Lanza Computer Use automation
    4. Ejecuta loops (capture → negotiate → close → pay → deliver → retain)
    5. Retorna cycle_id para tracking
    """

    cycle_id = str(uuid.uuid4())

    try:
        logger.info(f"Starting sales cycle {cycle_id} for {request.product.name}")

        # Inicializar engines
        loop_engine = LoopEngineering()
        # brain_computer_use = BrainComputerUseCoordinator(brain_engine, computer_use_agent)

        # Convertir input a dict
        product = request.product.dict()
        buyer = request.buyer.dict()

        # Lanzar ciclo completo (async background)
        # En producción: queue job (Celery, n8n, etc)
        # Por ahora: simular
        cycle_result = await loop_engine.run_sales_cycle_with_loops(product, buyer)

        logger.info(f"Sales cycle {cycle_id} initialized: {cycle_result['overall_status']}")

        return {
            "status": "initiated",
            "cycle_id": cycle_id,
            "product": product["name"],
            "buyer_email": buyer["email"],
            "phases": list(cycle_result["phases"].keys()),
            "overall_status": cycle_result["overall_status"],
        }

    except Exception as e:
        logger.error(f"Error starting sales cycle {cycle_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cycle_id}/status")
async def get_cycle_status(
    cycle_id: str,
    auth: dict = Depends(verify_auth),
):
    """Obtiene status actual del ciclo."""

    # TODO: Query DB por cycle_id
    return {
        "cycle_id": cycle_id,
        "status": "in_progress",
        "current_phase": "negotiation",
        "progress": 60,
    }


@router.get("/{cycle_id}/results")
async def get_cycle_results(
    cycle_id: str,
    auth: dict = Depends(verify_auth),
):
    """Obtiene resultados finales del ciclo."""

    # TODO: Query DB
    return {
        "cycle_id": cycle_id,
        "overall_status": "success",
        "revenue": 5000,
        "phases": {
            "capture": "success",
            "qualification": "success",
            "negotiation": "success",
            "closing": "success",
            "payment": "success",
            "delivery": "success",
            "retention": "in_progress",
        },
    }
