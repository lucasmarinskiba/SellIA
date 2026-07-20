"""ARCA (ex-AFIP) · endpoints REST para trámites impositivos y aduaneros.

Endpoints:
  GET  /padron/{cuit}                · consulta contribuyente
  POST /factura/emit                 · factura A/B/C (WSFE)
  POST /factura/export               · factura E (WSFEX)
  GET  /monotributo/sugerir          · recategorización
  POST /aduana/cove                  · COVE
  POST /aduana/origen                · certificado de origen
  POST /aduana/djve                  · DJVE
  POST /aduana/permiso-embarque      · permiso embarque
  POST /aduana/manifiesto            · manifiesto WSCOEM
  GET  /aduana/incoterms             · listado INCOTERMS 2020
  GET  /aduana/ncm/{code}            · validar NCM + descripción
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, get_current_user
from app.integrations.afip import (
    AFIPClient, FacturaRequest, FacturaExportRequest, ItemExport,
    consultar_padron, emit_factura, emit_factura_export,
    sugerir_categoria, proxima_recategorizacion,
)
from app.integrations.afip.aduana import (
    COVERequest, COVEItem, emit_cove,
    generate_origin_certificate,
    DJVERequest, DJVELinea, emit_djve,
    request_permiso_embarque,
    ManifiestoRequest, CargaManifiesto, ContenedorManifiesto, submit_manifiesto,
    INCOTERMS_2020, resolve_incoterm,
    validate_ncm, ncm_lookup,
)


logger = logging.getLogger(__name__)
router = APIRouter()


# ─── helpers ────────────────────────────────────────────────────────────────


async def _load_client(user: CurrentUser, service: str) -> AFIPClient:
    """Build AFIPClient from tenant settings (cert + key + cuit + prod flag)."""
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.db.models import Tenant

    async with AsyncSessionLocal() as db:
        t = (await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))).scalar_one_or_none()
        if not t:
            raise HTTPException(status_code=404, detail="Tenant no existe")
        sett = t.settings or {}
        cuit = sett.get("arca_cuit") or sett.get("afip_cuit")
        cert = sett.get("arca_cert_pem") or sett.get("afip_cert_pem")
        key = sett.get("arca_key_pem") or sett.get("afip_key_pem")
        prod = bool(sett.get("arca_production", False))
        if not cuit or not cert or not key:
            raise HTTPException(status_code=412, detail="Tenant sin cert/key/CUIT ARCA configurado")

    return AFIPClient(cuit=cuit, cert_pem=cert, key_pem=key, service=service, production=prod)


# ─── padrón ─────────────────────────────────────────────────────────────────


@router.get("/padron/{cuit}")
async def get_padron(cuit: str, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """Consulta contribuyente por CUIT."""
    client = await _load_client(user, service="ws_sr_padron_a13")
    persona = await consultar_padron(client, cuit)
    return {
        "cuit": persona.cuit,
        "tipo": persona.tipo_persona,
        "estado": persona.estado,
        "nombre": persona.nombre,
        "apellido": persona.apellido,
        "razon_social": persona.razon_social,
        "iva_condicion": persona.iva_condicion,
        "domicilios": persona.domicilios,
        "actividades": persona.actividades,
        "impuestos": persona.impuestos,
        "monotributo_categorias": persona.categorias_monotributo,
    }


# ─── factura doméstica ──────────────────────────────────────────────────────


class FacturaEmitBody(BaseModel):
    pto_vta: int
    cbte_tipo: int = Field(default=11, description="1=A · 6=B · 11=C")
    concepto: int = 1
    doc_tipo: int = 80
    doc_nro: int = 0
    imp_neto: Decimal
    imp_iva: Decimal = Decimal(0)
    imp_total: Decimal


@router.post("/factura/emit")
async def factura_emit(body: FacturaEmitBody, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    client = await _load_client(user, service="wsfe")
    fch = datetime.utcnow().strftime("%Y%m%d")
    req = FacturaRequest(
        pto_vta=body.pto_vta,
        cbte_tipo=body.cbte_tipo,
        concepto=body.concepto,
        doc_tipo=body.doc_tipo,
        doc_nro=body.doc_nro,
        cbte_fch=fch,
        imp_neto=body.imp_neto,
        imp_iva=body.imp_iva,
        imp_total=body.imp_total,
    )
    resp = await emit_factura(client, req)
    if resp.resultado != "A":
        raise HTTPException(status_code=422, detail={"observaciones": resp.observaciones})
    return {
        "cae": resp.cae,
        "vencimiento": resp.cae_fch_vto,
        "cbte_nro": resp.cbte_nro,
        "resultado": resp.resultado,
    }


# ─── factura exportación ────────────────────────────────────────────────────


class ItemExportBody(BaseModel):
    codigo: str
    descripcion: str
    cantidad: Decimal
    umed: int = 7
    precio_unit: Decimal


class FacturaExportBody(BaseModel):
    pto_vta: int
    cbte_tipo: int = 19
    dst_cmp: int                    # Código país destino ARCA (200=USA, 203=BR, 212=CL)
    cliente_razon_social: str
    cliente_domicilio: str
    cliente_id_impositivo: str
    moneda_id: str = "DOL"
    moneda_cotiz: Decimal
    incoterms: str
    items: list[ItemExportBody]
    permisos: list[str] = Field(default_factory=list)
    obs_comerciales: str = ""


@router.post("/factura/export")
async def factura_export(body: FacturaExportBody, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    try:
        resolve_incoterm(body.incoterms)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    client = await _load_client(user, service="wsfex")
    items = [
        ItemExport(
            codigo=i.codigo, descripcion=i.descripcion, cantidad=i.cantidad,
            umed=i.umed, precio_unit=i.precio_unit,
        )
        for i in body.items
    ]
    total = sum((i.cantidad * i.precio_unit for i in body.items), Decimal(0))
    req = FacturaExportRequest(
        pto_vta=body.pto_vta,
        cbte_tipo=body.cbte_tipo,
        fecha=datetime.utcnow().strftime("%Y%m%d"),
        dst_cmp=body.dst_cmp,
        cliente_razon_social=body.cliente_razon_social,
        cliente_domicilio=body.cliente_domicilio,
        cliente_id_impositivo=body.cliente_id_impositivo,
        moneda_id=body.moneda_id,
        moneda_cotiz=body.moneda_cotiz,
        incoterms=body.incoterms,
        imp_total=total,
        permisos=body.permisos,
        items=items,
        obs_comerciales=body.obs_comerciales,
    )
    resp = await emit_factura_export(client, req)
    if resp.resultado != "A":
        raise HTTPException(status_code=422, detail={"observaciones": resp.observaciones})
    return {
        "cae": resp.cae,
        "vencimiento": resp.cae_fch_vto,
        "cbte_nro": resp.cbte_nro,
        "imp_total": str(total),
    }


# ─── monotributo ────────────────────────────────────────────────────────────


@router.get("/monotributo/sugerir")
async def monotributo_sugerir(
    facturacion_12m: float = Query(..., gt=0),
    vende_bienes: bool = Query(True),
    categoria_actual: str | None = Query(None),
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    r = sugerir_categoria(facturacion_12m, vende_bienes=vende_bienes, categoria_actual=categoria_actual)
    return {
        **r.__dict__,
        "proxima_recategorizacion": proxima_recategorizacion().isoformat(),
    }


# ─── aduana · COVE ──────────────────────────────────────────────────────────


class COVEItemBody(BaseModel):
    ncm: str
    descripcion: str
    cantidad: Decimal
    unidad: str
    valor_unitario_fob_usd: Decimal
    pais_origen: str = "AR"


class COVEBody(BaseModel):
    pto_vta: int
    factura_e_nro: str
    pais_destino: str
    cliente_razon_social: str
    cliente_tax_id: str
    cliente_domicilio: str
    incoterm: str
    moneda: str = "USD"
    flete_usd: Decimal = Decimal(0)
    seguro_usd: Decimal = Decimal(0)
    items: list[COVEItemBody]
    submit_to_sim: bool = False


@router.post("/aduana/cove")
async def aduana_cove(body: COVEBody, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    items = [
        COVEItem(
            ncm=i.ncm, descripcion=i.descripcion, cantidad=i.cantidad, unidad=i.unidad,
            valor_unitario_fob_usd=i.valor_unitario_fob_usd, pais_origen=i.pais_origen,
        )
        for i in body.items
    ]
    valor_fob = sum((i.cantidad * i.valor_unitario_fob_usd for i in body.items), Decimal(0))
    req = COVERequest(
        cuit_exportador=user.tenant_id,  # backed by tenant setting in real impl
        pto_vta=body.pto_vta,
        factura_e_nro=body.factura_e_nro,
        fecha_emision=datetime.utcnow().date().isoformat(),
        pais_destino=body.pais_destino,
        cliente_razon_social=body.cliente_razon_social,
        cliente_tax_id=body.cliente_tax_id,
        cliente_domicilio=body.cliente_domicilio,
        incoterm=body.incoterm,
        moneda=body.moneda,
        valor_fob_total=valor_fob,
        flete_usd=body.flete_usd,
        seguro_usd=body.seguro_usd,
        items=items,
    )
    resp = await emit_cove(req, submit_to_sim=body.submit_to_sim)
    return {
        "cove_id": resp.cove_id,
        "estado": resp.estado,
        "qr_url": resp.qr_url,
        "payload": resp.payload,
    }


# ─── aduana · certificado origen ───────────────────────────────────────────


class CertOrigenBody(BaseModel):
    regimen: str = "MERCOSUR"
    pais_destino: str
    exportador: dict
    importador: dict
    items: list[dict]
    factura_e_nro: str
    consignatario: dict | None = None
    productor: dict | None = None
    medios_transporte: str = "Marítimo"


@router.post("/aduana/origen")
async def aduana_origen(body: CertOrigenBody, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    try:
        cert = generate_origin_certificate(
            regimen=body.regimen,
            pais_destino=body.pais_destino,
            exportador=body.exportador,
            importador=body.importador,
            items=body.items,
            factura_e_nro=body.factura_e_nro,
            consignatario=body.consignatario,
            productor=body.productor,
            medios_transporte=body.medios_transporte,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return cert.__dict__


# ─── aduana · DJVE ──────────────────────────────────────────────────────────


class DJVELineaBody(BaseModel):
    ncm: str
    descripcion: str
    cantidad: Decimal
    unidad: str = "TONELADAS"
    precio_fob_usd: Decimal


class DJVEBody(BaseModel):
    cuit_comprador_exterior: str
    tipo: str = "30"
    pais_destino: str
    puerto_embarque: str
    fecha_embarque_estimada: str
    lineas: list[DJVELineaBody]
    submit: bool = False


@router.post("/aduana/djve")
async def aduana_djve(body: DJVEBody, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    lineas = [DJVELinea(**l.dict()) for l in body.lineas]
    total = sum((l.cantidad * l.precio_fob_usd for l in body.lineas), Decimal(0))
    req = DJVERequest(
        cuit_exportador=user.tenant_id,
        cuit_comprador_exterior=body.cuit_comprador_exterior,
        tipo=body.tipo,
        pais_destino=body.pais_destino,
        puerto_embarque=body.puerto_embarque,
        fecha_embarque_estimada=body.fecha_embarque_estimada,
        valor_total_fob=total,
        lineas=lineas,
    )
    resp = await emit_djve(req, submit=body.submit)
    return {
        "djve_id": resp.djve_id,
        "estado": resp.estado,
        "vencimiento": resp.fecha_vencimiento,
        "aliquota_pct": resp.aliquota_retencion_pct,
        "payload": resp.payload,
    }


# ─── aduana · permiso de embarque ──────────────────────────────────────────


class PEBody(BaseModel):
    pais_destino: str
    aduana_registro: str = "001"
    aduana_salida: str = "001"
    medio_transporte: str = "Aéreo"
    documento_transporte: str = ""
    valor_fob_total_usd: Decimal
    items: list[dict]
    factura_e: str
    cove_id: str | None = None
    djve_id: str | None = None
    derechos_export_pct: float = 0.0
    reintegros_pct: float = 0.0
    submit_to_sim: bool = False


@router.post("/aduana/permiso-embarque")
async def aduana_permiso_embarque(body: PEBody, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    pe = await request_permiso_embarque(
        cuit_exportador=user.tenant_id,
        pais_destino=body.pais_destino,
        aduana_registro=body.aduana_registro,
        aduana_salida=body.aduana_salida,
        medio_transporte=body.medio_transporte,
        documento_transporte=body.documento_transporte,
        valor_fob_total_usd=body.valor_fob_total_usd,
        items=body.items,
        factura_e=body.factura_e,
        cove_id=body.cove_id,
        djve_id=body.djve_id,
        submit_to_sim=body.submit_to_sim,
        derechos_export_pct=body.derechos_export_pct,
        reintegros_pct=body.reintegros_pct,
    )
    return {
        "pe_numero": pe.pe_numero,
        "estado": pe.estado,
        "canal": pe.canal,
        "derechos_usd": str(pe.derechos_export_usd),
        "reintegros_usd": str(pe.reintegros_usd),
        "valor_fob_usd": str(pe.valor_fob_total_usd),
    }


# ─── aduana · manifiesto ───────────────────────────────────────────────────


class CargaBody(BaseModel):
    documento_transporte: str
    tipo_doc: str = "BL"
    consignatario: str
    pais_destino: str
    puerto_descarga: str
    valor_fob_usd: Decimal
    peso_bruto_kg: Decimal
    cantidad_bultos: int
    descripcion_mercaderia: str
    ncm: str


class ManifiestoBody(BaseModel):
    numero_viaje: str
    medio_transporte_id: str
    bandera_id: str = "AR"
    fecha_arribo_partida: str
    puerto_origen: str
    puerto_destino: str
    tipo_operacion: str = "EXPO"
    cargas: list[CargaBody]


@router.post("/aduana/manifiesto")
async def aduana_manifiesto(body: ManifiestoBody, user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    cargas = [
        CargaManifiesto(
            documento_transporte=c.documento_transporte, tipo_doc=c.tipo_doc,
            consignatario=c.consignatario, pais_destino=c.pais_destino,
            puerto_descarga=c.puerto_descarga, valor_fob_usd=c.valor_fob_usd,
            peso_bruto_kg=c.peso_bruto_kg, cantidad_bultos=c.cantidad_bultos,
            descripcion_mercaderia=c.descripcion_mercaderia, ncm=c.ncm,
        )
        for c in body.cargas
    ]
    req = ManifiestoRequest(
        cuit_ata=user.tenant_id,
        numero_viaje=body.numero_viaje,
        medio_transporte_id=body.medio_transporte_id,
        bandera_id=body.bandera_id,
        fecha_arribo_partida=body.fecha_arribo_partida,
        puerto_origen=body.puerto_origen,
        puerto_destino=body.puerto_destino,
        tipo_operacion=body.tipo_operacion,
        cargas=cargas,
    )
    resp = await submit_manifiesto(req)
    return resp.__dict__


# ─── aduana · tablas auxiliares ────────────────────────────────────────────


@router.get("/aduana/incoterms")
async def aduana_incoterms() -> list[dict]:
    return [
        {
            "code": i.code, "name": i.name, "group": i.group, "modo": i.modo,
            "paga_flete": i.paga_flete, "paga_seguro": i.paga_seguro,
            "transferencia_riesgo": i.transferencia_riesgo,
        }
        for i in INCOTERMS_2020.values()
    ]


@router.get("/aduana/ncm/{code}")
async def aduana_ncm(code: str) -> dict:
    try:
        ncm = validate_ncm(code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": ncm.code,
        "ncm_full": ncm.ncm_full,
        "capitulo": ncm.capitulo,
        "partida": ncm.partida,
        "subpartida_hs": ncm.subpartida_hs,
        "descripcion": ncm_lookup(ncm.code),
    }
