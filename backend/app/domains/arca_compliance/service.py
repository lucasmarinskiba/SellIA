"""ARCA Compliance service: lógica real, sin datos inventados.

Todo lo que no requiere el certificado digital de ARCA/AFIP (validación de
CUIT, cálculo de categoría Monotributo, INCOTERMS, capítulos NCM) está
implementado con el algoritmo/dato público real. Lo que sí requiere el
certificado (razón social real del padrón, CAE de facturación) devuelve un
estado `requires_certificate` explícito — nunca un dato inventado.
"""
import os
from app.domains.arca_compliance.reference_data import (
    INCOTERMS_2020, HS_CHAPTERS, MONOTRIBUTO_CATEGORIAS,
)


class CUITValidationError(ValueError):
    pass


def validate_cuit_checksum(cuit: str) -> dict:
    """Valida el dígito verificador de un CUIT con el algoritmo mod-11 real de AFIP."""
    digits = [c for c in cuit if c.isdigit()]
    if len(digits) != 11:
        raise CUITValidationError(f"CUIT debe tener 11 dígitos, recibido {len(digits)}")

    nums = [int(d) for d in digits]
    multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(n * m for n, m in zip(nums[:10], multipliers))
    remainder = total % 11
    if remainder == 0:
        check_digit = 0
    elif remainder == 1:
        check_digit = 9
    else:
        check_digit = 11 - remainder

    is_valid = check_digit == nums[10]
    tipo_map = {20: "Persona física - masculino", 23: "Persona física", 24: "Persona física",
                27: "Persona física - femenino", 30: "Persona jurídica", 33: "Persona jurídica",
                34: "Persona jurídica"}
    prefix = int("".join(digits[0:2]))

    return {
        "cuit": "".join(digits),
        "checksum_valid": is_valid,
        "tipo_probable": tipo_map.get(prefix, "Desconocido (prefijo no estándar)"),
    }


class ARCAComplianceService:
    """Servicio de compliance impositivo/aduanero — datos reales o estado explícito de config faltante."""

    @staticmethod
    def is_afip_configured() -> bool:
        """AFIP/ARCA requiere certificado digital (.crt/.key) registrado sobre el CUIT del emisor."""
        return bool(os.getenv("AFIP_CERT_PATH") and os.getenv("AFIP_KEY_PATH") and os.getenv("AFIP_CUIT"))

    @classmethod
    def consultar_padron(cls, cuit: str) -> dict:
        """Padrón A13: valida el CUIT en el momento (real). Datos de AFIP (razón social,
        condición IVA, domicilio) requieren certificado — sin él, no se inventan."""
        validation = validate_cuit_checksum(cuit)

        if not cls.is_afip_configured():
            return {
                **validation,
                "status": "requires_certificate",
                "message": (
                    "El dígito verificador del CUIT es válido, pero la consulta al Padrón A13 "
                    "de ARCA requiere certificado digital (AFIP_CERT_PATH, AFIP_KEY_PATH, AFIP_CUIT) "
                    "que todavía no está configurado. Sin esto no se puede traer razón social, "
                    "condición de IVA ni domicilio fiscal reales."
                ),
                "razon_social": None,
                "condicion_iva": None,
                "domicilio_fiscal": None,
            }

        # TODO: cuando AFIP_CERT_PATH/AFIP_KEY_PATH estén configurados, implementar
        # llamada real a ws_sr_padron_a13 (SOAP, requiere WSAA para token+sign previo).
        return {
            **validation,
            "status": "certificate_configured_but_call_not_implemented",
            "message": "Certificado detectado pero la llamada SOAP a ws_sr_padron_a13 aún no está implementada.",
        }

    @staticmethod
    def sugerir_categoria_monotributo(facturacion_12m: float, vende_bienes: bool) -> dict:
        """Cálculo real contra la escala vigente de categorías Monotributo."""
        if facturacion_12m < 0:
            raise ValueError("facturacion_12m no puede ser negativa")

        categorias = MONOTRIBUTO_CATEGORIAS["categorias"]
        sugerida = None
        for cat in categorias:
            if facturacion_12m <= cat["facturacion_max_anual"]:
                # Categorías I/J/K solo aplican si vende bienes (servicios tope en H)
                if not vende_bienes and cat["cuota_servicios"] is None:
                    continue
                sugerida = cat
                break

        if sugerida is None:
            return {
                "facturacion_12m": facturacion_12m,
                "vende_bienes": vende_bienes,
                "categoria_sugerida": None,
                "excede_tope": True,
                "message": "Facturación excede el tope máximo de Monotributo. Debe evaluar Responsable Inscripto.",
                "vigencia_escala": MONOTRIBUTO_CATEGORIAS["vigencia"],
            }

        cuota = sugerida["cuota_bienes"] if vende_bienes else sugerida["cuota_servicios"]
        margen_para_recategorizar = sugerida["facturacion_max_anual"] - facturacion_12m
        alerta_tope = margen_para_recategorizar < (sugerida["facturacion_max_anual"] * 0.1)

        return {
            "facturacion_12m": facturacion_12m,
            "vende_bienes": vende_bienes,
            "categoria_sugerida": sugerida["categoria"],
            "cuota_mensual_estimada": cuota,
            "tope_categoria": sugerida["facturacion_max_anual"],
            "margen_restante": round(margen_para_recategorizar, 2),
            "alerta_proximidad_tope": alerta_tope,
            "excede_tope": False,
            "vigencia_escala": MONOTRIBUTO_CATEGORIAS["vigencia"],
        }

    @staticmethod
    def get_incoterms() -> list[dict]:
        return INCOTERMS_2020

    @staticmethod
    def lookup_ncm(code: str) -> dict:
        """Valida estructura NCM (8 dígitos) + resuelve el capítulo SA real (primeros 2 dígitos).

        La descripción completa a 8 dígitos requiere la base de datos completa de
        Nomenclatura Común Mercosur (miles de posiciones, mantenida por Aduana) que
        no está embebida acá — se informa el capítulo real, no se inventa la posición.
        """
        digits = "".join(c for c in code if c.isdigit())
        if len(digits) != 8:
            return {
                "code": code,
                "valid_format": False,
                "message": f"NCM debe tener 8 dígitos, recibido {len(digits)}",
            }

        chapter = digits[0:2]
        chapter_desc = HS_CHAPTERS.get(chapter)

        return {
            "code": digits,
            "formatted": f"{digits[0:4]}.{digits[4:6]}.{digits[6:8]}",
            "valid_format": True,
            "capitulo_sa": chapter,
            "capitulo_descripcion": chapter_desc or "Capítulo no reconocido en el Sistema Armonizado",
            "descripcion_completa_8_digitos": None,
            "message": (
                "Formato válido y capítulo SA resuelto. La descripción completa a 8 dígitos "
                "requiere la base NCM completa de Aduana, no incluida en esta consulta."
            ),
        }
