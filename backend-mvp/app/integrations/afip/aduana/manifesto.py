"""WSCOEM · Manifiesto Electrónico de Carga.

Permite registrar el manifiesto de exportación (lo que sale del país) e importación.
Datos: medio de transporte, viaje, lista de cargas, consignatarios, puerto origen/destino,
contenedores. Obligatorio para agentes de transporte aduanero (ATA).

Endpoint homo: https://wsaduhomoext.afip.gov.ar/DIAV2/wgescargav2/wgescargav2.asmx
Endpoint prod: https://servicios1.afip.gov.ar/wgescargav2/wgescargav2.asmx

Esta capa expone un modelo + builder de manifiesto que envía al WS via SOAP cuando
el tenant tiene rol ATA habilitado.
"""
import logging
from dataclasses import dataclass, field
from decimal import Decimal


logger = logging.getLogger(__name__)


@dataclass
class ContenedorManifiesto:
    numero: str            # Container ID (ej ABCU1234567)
    tipo: str              # 20DV, 40HC, 40FR, RF
    precintos: list[str] = field(default_factory=list)
    peso_kg: Decimal = Decimal(0)


@dataclass
class CargaManifiesto:
    documento_transporte: str         # BL / AWB / CRT
    tipo_doc: str                     # BL · MASTER · HOUSE
    consignatario: str
    pais_destino: str
    puerto_descarga: str
    valor_fob_usd: Decimal
    peso_bruto_kg: Decimal
    cantidad_bultos: int
    descripcion_mercaderia: str
    ncm: str
    contenedores: list[ContenedorManifiesto] = field(default_factory=list)


@dataclass
class ManifiestoRequest:
    cuit_ata: str
    numero_viaje: str
    medio_transporte_id: str
    bandera_id: str
    fecha_arribo_partida: str
    puerto_origen: str
    puerto_destino: str
    tipo_operacion: str               # EXPO · IMPO
    cargas: list[CargaManifiesto] = field(default_factory=list)


@dataclass
class ManifiestoResponse:
    manifiesto_id: str
    estado: str
    fecha_oficializacion: str | None
    observaciones: list[str] = field(default_factory=list)


async def submit_manifiesto(req: ManifiestoRequest, *, production: bool = False) -> ManifiestoResponse:
    """Stub builder · in production wires to WSCOEM SOAP."""
    # Real impl: build envelope w/ wgescargav2:RegistrarTitMicDtaParam, sign w/ TA from wsaa svc=wgescarga
    manifiesto_id = f"MFTO-{req.tipo_operacion}-{req.numero_viaje}-{req.fecha_arribo_partida.replace('-','')}"
    logger.info("manifiesto_built", extra={"id": manifiesto_id, "cargas": len(req.cargas)})
    return ManifiestoResponse(
        manifiesto_id=manifiesto_id,
        estado="PENDIENTE_OFICIALIZACION",
        fecha_oficializacion=None,
        observaciones=["Stub local · requiere submit a WSCOEM"],
    )
