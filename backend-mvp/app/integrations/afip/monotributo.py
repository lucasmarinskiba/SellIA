"""ARCA (ex-AFIP) · Monotributo helpers.

Categorías 2025 (anualizado · ARS · escala vigente al 2026):
  A · hasta $7.813.063
  B · hasta $11.447.046
  C · hasta $16.050.091
  D · hasta $19.926.340
  E · hasta $23.439.190
  F · hasta $29.374.695
  G · hasta $35.128.502
  H · hasta $53.298.417
  I · hasta $59.657.887
  J · hasta $68.318.880
  K · hasta $82.370.281

Used to:
  - Recommend recategorization based on facturación últimos 12 meses
  - Compute monthly cuota (impuesto integrado + aportes + obra social)
  - Generate VEP (Volante Electrónico de Pago) link

VEP issuance via ARCA portal (no public WS for VEP gen as of 2026 · Computer Use fallback).
"""
from dataclasses import dataclass
from datetime import date


# Cap anual por categoría (ARS) · servicios. Bienes muebles tiene caps mayores en H-K.
CATEGORIAS_SERVICIOS = [
    ("A", 7_813_063),
    ("B", 11_447_046),
    ("C", 16_050_091),
    ("D", 19_926_340),
    ("E", 23_439_190),
    ("F", 29_374_695),
    ("G", 35_128_502),
    ("H", 53_298_417),
]

CATEGORIAS_BIENES = CATEGORIAS_SERVICIOS + [
    ("I", 59_657_887),
    ("J", 68_318_880),
    ("K", 82_370_281),
]

# Cuota mensual aprox (impuesto + jubilación + obra social) · ARS
CUOTA_MENSUAL = {
    "A": 26_000, "B": 32_500, "C": 39_500, "D": 50_000, "E": 70_000,
    "F": 90_000, "G": 115_000, "H": 200_000, "I": 320_000, "J": 400_000, "K": 530_000,
}


@dataclass
class RecategorizacionResult:
    categoria_actual: str | None
    categoria_sugerida: str
    facturacion_12m: float
    excede_tope: bool
    cuota_estimada_ars: int
    requiere_pasaje_ri: bool  # Pasa a Responsable Inscripto si supera cap K


def sugerir_categoria(facturacion_12m: float, *, vende_bienes: bool = True, categoria_actual: str | None = None) -> RecategorizacionResult:
    """Recomienda categoría según facturación últimos 12 meses.

    Llama a esta función al cierre de cada semestre (enero · julio) o al pasar 80% del tope actual.
    """
    escala = CATEGORIAS_BIENES if vende_bienes else CATEGORIAS_SERVICIOS

    sugerida = "A"
    excede = True
    for letra, cap in escala:
        if facturacion_12m <= cap:
            sugerida = letra
            excede = False
            break

    cuota = CUOTA_MENSUAL.get(sugerida, 0)

    return RecategorizacionResult(
        categoria_actual=categoria_actual,
        categoria_sugerida=sugerida,
        facturacion_12m=facturacion_12m,
        excede_tope=excede,
        cuota_estimada_ars=cuota,
        requiere_pasaje_ri=excede,
    )


def proxima_recategorizacion(today: date | None = None) -> date:
    """Devuelve fecha próxima recategorización obligatoria (ene 20 / jul 20)."""
    today = today or date.today()
    candidates = [date(today.year, 1, 20), date(today.year, 7, 20), date(today.year + 1, 1, 20)]
    for d in candidates:
        if d >= today:
            return d
    return candidates[-1]
