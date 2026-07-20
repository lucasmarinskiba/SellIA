"""INCOTERMS 2020 · 11 reglas vigentes.

Las INCOTERMS definen quién paga flete, seguro, despacho aduanero, dónde se transfiere
el riesgo. Obligatorio declararlas en Factura E y permiso de embarque.

Grupos:
  E · Salida (EXW)
  F · Sin pago transporte principal (FCA, FAS, FOB)
  C · Con pago transporte principal (CFR, CIF, CPT, CIP)
  D · Llegada (DAP, DPU, DDP)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Incoterm:
    code: str
    name: str
    group: str
    modo: str  # "any" | "sea" (only sea/inland waterway)
    paga_flete: str
    paga_seguro: str
    paga_despacho_export: str
    paga_despacho_import: str
    transferencia_riesgo: str


INCOTERMS_2020: dict[str, Incoterm] = {
    "EXW": Incoterm("EXW", "Ex Works",                 "E", "any", "Comprador", "Comprador", "Comprador", "Comprador", "En fábrica del vendedor"),
    "FCA": Incoterm("FCA", "Free Carrier",             "F", "any", "Comprador", "Comprador", "Vendedor", "Comprador", "Al entregar al transportista"),
    "FAS": Incoterm("FAS", "Free Alongside Ship",      "F", "sea", "Comprador", "Comprador", "Vendedor", "Comprador", "Al costado del buque puerto origen"),
    "FOB": Incoterm("FOB", "Free On Board",            "F", "sea", "Comprador", "Comprador", "Vendedor", "Comprador", "A bordo del buque puerto origen"),
    "CFR": Incoterm("CFR", "Cost and Freight",         "C", "sea", "Vendedor", "Comprador", "Vendedor", "Comprador", "A bordo del buque puerto origen"),
    "CIF": Incoterm("CIF", "Cost Insurance Freight",   "C", "sea", "Vendedor", "Vendedor", "Vendedor", "Comprador", "A bordo del buque puerto origen"),
    "CPT": Incoterm("CPT", "Carriage Paid To",         "C", "any", "Vendedor", "Comprador", "Vendedor", "Comprador", "Al entregar al primer transportista"),
    "CIP": Incoterm("CIP", "Carriage and Insurance Paid To", "C", "any", "Vendedor", "Vendedor", "Vendedor", "Comprador", "Al entregar al primer transportista"),
    "DAP": Incoterm("DAP", "Delivered at Place",       "D", "any", "Vendedor", "Vendedor", "Vendedor", "Comprador", "En lugar de destino · sin descargar"),
    "DPU": Incoterm("DPU", "Delivered at Place Unloaded","D", "any","Vendedor", "Vendedor", "Vendedor", "Comprador", "En lugar de destino · descargado"),
    "DDP": Incoterm("DDP", "Delivered Duty Paid",      "D", "any", "Vendedor", "Vendedor", "Vendedor", "Vendedor", "En destino · todo pagado"),
}


def resolve_incoterm(code: str) -> Incoterm:
    code = (code or "").upper().strip()
    if code not in INCOTERMS_2020:
        raise ValueError(f"Unknown INCOTERM '{code}'. Valid: {list(INCOTERMS_2020.keys())}")
    return INCOTERMS_2020[code]
