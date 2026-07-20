"""NCM (Nomenclatura Común del Mercosur) · 8-digit derived from HS 6-digit.

Estructura:
  XX       Capítulo (2d)
  XX.XX    Partida (4d)
  XX.XX.XX Subpartida (6d · HS)
  XX.XX.XX.XX NCM (8d · Mercosur)

Validación básica: longitud, dígitos, separadores opcionales.
Para tarifa completa (DIE, DTE, reintegro, retención) integrar con base de TARIFAR/SIM.
"""
import re
from dataclasses import dataclass


NCM_PATTERN = re.compile(r"^(\d{2})\.?(\d{2})\.?(\d{2})\.?(\d{2})$")


@dataclass
class NCM:
    code: str           # canonical "XXXX.XX.XX"
    capitulo: str
    partida: str
    subpartida_hs: str  # 6-digit HS code (works universally)
    ncm_full: str       # 8-digit


def validate_ncm(raw: str) -> NCM:
    """Validate + canonicalize NCM code (accepts with/without dots)."""
    clean = (raw or "").strip().replace(" ", "")
    m = NCM_PATTERN.match(clean)
    if not m:
        raise ValueError(f"Invalid NCM format '{raw}'. Expected 8 digits (XXXX.XX.XX or XXXXXXXX)")
    a, b, c, d = m.groups()
    return NCM(
        code=f"{a}{b}.{c}.{d}",
        capitulo=a,
        partida=f"{a}{b}",
        subpartida_hs=f"{a}{b}{c}{d}"[:6],
        ncm_full=f"{a}{b}{c}{d}",
    )


# Stub catálogo. Producción debe consumir base TARIFAR o https://servicios.afip.gob.ar/clavefiscal/...
COMMON_NCM_CATALOG: dict[str, str] = {
    "0203.12.00": "Carne porcina · jamones, paletas",
    "0901.21.00": "Café tostado, sin descafeinar",
    "1701.14.00": "Azúcar de caña refinada",
    "2204.21.00": "Vino de uvas en envases ≤ 2 L",
    "4202.11.00": "Baúles, maletas con superficie exterior de cuero",
    "6109.10.00": "Camisetas de algodón (T-shirts)",
    "8471.30.12": "Notebooks/laptops ≤ 10 kg con disco rígido",
    "8517.13.00": "Smartphones",
    "9504.50.00": "Consolas de videojuegos",
}


def ncm_lookup(code: str) -> str | None:
    """Returns description if known. Production stub."""
    try:
        ncm = validate_ncm(code)
    except ValueError:
        return None
    return COMMON_NCM_CATALOG.get(ncm.code)
