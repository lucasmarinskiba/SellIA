"""Phase 29: Marketplace Expansion - Cross-platform inventory, analytics, strategy."""

from fastapi import APIRouter, HTTPException, Query

_NOT_IMPLEMENTED = (
    "Métricas de marketplace no disponibles: el cálculo real no está implementado. "
    "Las cifras que devolvía este endpoint eran de muestra."
)


router = APIRouter(prefix="/marketplace-expansion", tags=["marketplace-expansion"])


@router.get("/platforms/performance")
async def platform_performance(seller_id: str = Query(...)):
    """Compare performance across all platforms."""
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/opportunities/analyze")
async def marketplace_opportunities(seller_id: str = Query(...)):
    """Identify expansion opportunities across platforms."""
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/inventory/sync-strategy")
async def sync_strategy(seller_id: str = Query(...)):
    """Get inventory synchronization strategy."""
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
