"""ARCA (ex-AFIP) · Padrón A13 · consulta de contribuyentes.

Service: ws_sr_padron_a13 (WSAA service id) · returns inscription status, IVA condition,
domiciles, activities (CAE codes), monotributo category, etc.

WSDL: https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA13?wsdl
"""
import logging
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

import httpx

from app.integrations.afip.wsaa import AFIPClient


logger = logging.getLogger(__name__)


PADRON_URL_HOMO = "https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA13"
PADRON_URL_PROD = "https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA13"


@dataclass
class PadronPersona:
    cuit: str
    tipo_persona: str  # FISICA | JURIDICA
    estado: str  # ACTIVO | INACTIVO
    nombre: str
    apellido: str | None = None
    razon_social: str | None = None
    fecha_nacimiento: str | None = None
    fecha_inscripcion: str | None = None
    domicilios: list[dict] = field(default_factory=list)
    actividades: list[dict] = field(default_factory=list)  # [{periodo, idActividad, descripcion, orden}]
    impuestos: list[dict] = field(default_factory=list)
    categorias_monotributo: list[dict] = field(default_factory=list)
    iva_condicion: str | None = None  # RI · MONOTRIBUTO · EXENTO · CONSUMIDOR_FINAL
    raw_xml: str | None = None


async def consultar_padron(client: AFIPClient, cuit_target: str, *, production: bool = False) -> PadronPersona:
    """Query contribuyente data by CUIT via Padrón A13.

    Requires the AFIPClient to be initialized w/ service='ws_sr_padron_a13'.
    """
    if client.service != "ws_sr_padron_a13":
        raise ValueError("AFIPClient.service must be 'ws_sr_padron_a13' for padron queries")

    ta = await client.get_auth()
    url = PADRON_URL_PROD if production else PADRON_URL_HOMO

    envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:a13="http://a13.soap.ws.server.puc.sr/">
  <soapenv:Header/>
  <soapenv:Body>
    <a13:getPersona>
      <token>{ta.token}</token>
      <sign>{ta.sign}</sign>
      <cuitRepresentada>{client.cuit}</cuitRepresentada>
      <idPersona>{cuit_target}</idPersona>
    </a13:getPersona>
  </soapenv:Body>
</soapenv:Envelope>"""

    async with httpx.AsyncClient(timeout=30.0) as c:
        resp = await c.post(
            url,
            content=envelope,
            headers={"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": ""},
        )
        resp.raise_for_status()

    return _parse_padron(resp.text, cuit_target)


def _parse_padron(soap_xml: str, cuit: str) -> PadronPersona:
    """Extract personaReturn fields from SOAP response."""
    try:
        root = ET.fromstring(soap_xml)
    except ET.ParseError as e:
        raise RuntimeError(f"Padrón response XML invalid: {e}") from e

    persona_node = root.find(".//persona") or root.find(".//{*}persona")
    if persona_node is None:
        # Maybe fault
        fault = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Fault")
        msg = fault.findtext(".//faultstring") if fault is not None else "Padron: persona node missing"
        raise RuntimeError(f"Padron lookup failed: {msg}")

    def t(path: str) -> str | None:
        n = persona_node.find(path)
        return n.text if n is not None and n.text else None

    domicilios = []
    for d in persona_node.findall(".//domicilio"):
        domicilios.append({
            "tipo": d.findtext("tipoDomicilio") or "",
            "direccion": d.findtext("direccion") or "",
            "localidad": d.findtext("localidad") or "",
            "provincia": d.findtext("descripcionProvincia") or "",
            "codigo_postal": d.findtext("codPostal") or "",
        })

    actividades = []
    for a in persona_node.findall(".//actividad"):
        actividades.append({
            "id": a.findtext("idActividad") or "",
            "descripcion": a.findtext("descripcionActividad") or "",
            "orden": int(a.findtext("orden") or 0),
            "periodo": a.findtext("periodo") or "",
        })

    impuestos = []
    for i in persona_node.findall(".//impuesto"):
        impuestos.append({
            "id": i.findtext("idImpuesto") or "",
            "descripcion": i.findtext("descripcionImpuesto") or "",
            "estado": i.findtext("estadoImpuesto") or "",
        })

    cats = []
    for c in persona_node.findall(".//categoriaMonotributo"):
        cats.append({
            "id": c.findtext("idCategoria") or "",
            "descripcion": c.findtext("descripcionCategoria") or "",
            "periodo": c.findtext("periodo") or "",
        })

    # Derive IVA condition heuristically
    iva_cond = None
    for imp in impuestos:
        if "IVA" in imp["descripcion"].upper():
            iva_cond = "RESPONSABLE_INSCRIPTO" if imp["estado"] == "ACTIVO" else None
        if "MONOTRIBUTO" in imp["descripcion"].upper() and imp["estado"] == "ACTIVO":
            iva_cond = "MONOTRIBUTO"

    return PadronPersona(
        cuit=cuit,
        tipo_persona=t("tipoPersona") or "",
        estado=t("estadoClave") or "",
        nombre=t("nombre") or "",
        apellido=t("apellido"),
        razon_social=t("razonSocial"),
        fecha_nacimiento=t("fechaNacimiento"),
        fecha_inscripcion=t("fechaInscripcion"),
        domicilios=domicilios,
        actividades=actividades,
        impuestos=impuestos,
        categorias_monotributo=cats,
        iva_condicion=iva_cond,
        raw_xml=soap_xml[:5000],
    )
