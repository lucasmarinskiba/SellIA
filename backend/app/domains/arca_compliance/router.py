"""ARCA Compliance router — sirve exactamente los paths que el frontend ya llama
(ARCAComplianceHub.tsx, CustomsExportHub.tsx): sin prefijo /api/v1, porque esos
componentes usan el cliente axios con baseURL = NEXT_PUBLIC_API_URL directo.
"""
from fastapi import APIRouter, HTTPException, Query
from app.domains.arca_compliance.service import ARCAComplianceService, CUITValidationError


router = APIRouter(prefix="/arca", tags=["arca-compliance"])


@router.get("/padron/{cuit}")
async def consultar_padron(cuit: str) -> dict:
    """Padrón A13. Valida CUIT real; datos AFIP requieren certificado (ver /arca/status)."""
    try:
        return ARCAComplianceService.consultar_padron(cuit)
    except CUITValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/monotributo/sugerir")
async def sugerir_monotributo(
    facturacion_12m: float = Query(...),
    vende_bienes: bool = Query(True),
) -> dict:
    """Sugiere categoría Monotributo real contra la escala vigente de ARCA."""
    try:
        return ARCAComplianceService.sugerir_categoria_monotributo(facturacion_12m, vende_bienes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/aduana/incoterms")
async def get_incoterms() -> list[dict]:
    """Las 11 reglas INCOTERMS 2020 (ICC), dato de referencia estable."""
    return ARCAComplianceService.get_incoterms()


@router.get("/aduana/ncm/{code}")
async def lookup_ncm(code: str) -> dict:
    """Valida formato NCM (8 dígitos) + resuelve capítulo real del Sistema Armonizado."""
    return ARCAComplianceService.lookup_ncm(code)


@router.get("/status")
async def get_arca_status() -> dict:
    """Estado real de configuración: qué trámites tienen certificado AFIP y cuáles no."""
    configured = ARCAComplianceService.is_afip_configured()
    return {
        "afip_certificate_configured": configured,
        "live_without_certificate": ["padron (validación de CUIT)", "monotributo/sugerir", "aduana/incoterms", "aduana/ncm"],
        "requires_certificate": ["padron (datos reales AFIP)", "factura/emit (WSFE)", "factura/export (WSFEX)"],
        "not_implemented_yet": ["libro_iva", "mis_comprobantes", "constancia", "f931", "aduana/cove", "aduana/origen", "aduana/djve", "aduana/permiso-embarque", "aduana/manifiesto"],
    }
