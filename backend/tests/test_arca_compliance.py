"""Unit tests for ARCA compliance: CUIT checksum, Monotributo, NCM.

Pure logic, no DB/Redis needed - runs standalone:
    pytest backend/tests/test_arca_compliance.py -v
"""
import pytest

from app.domains.arca_compliance.service import (
    validate_cuit_checksum, CUITValidationError, ARCAComplianceService,
)


class TestCUITChecksum:
    def test_valid_cuit_accepted(self):
        # 20-12345678-6: hand-verified mod-11 (sum=148, 148%11=5, 11-5=6)
        result = validate_cuit_checksum("20123456786")
        assert result["checksum_valid"] is True
        assert result["cuit"] == "20123456786"

    def test_invalid_checksum_rejected(self):
        result = validate_cuit_checksum("20123456780")
        assert result["checksum_valid"] is False

    def test_accepts_dashes_and_spaces(self):
        result = validate_cuit_checksum("20-12345678-6")
        assert result["checksum_valid"] is True
        assert result["cuit"] == "20123456786"

    def test_wrong_length_raises(self):
        with pytest.raises(CUITValidationError):
            validate_cuit_checksum("123")

    def test_tipo_probable_persona_juridica(self):
        # prefix 30 = persona jurídica; digits chosen so checksum is valid
        # 30-71234567-X: compute check digit
        nums = [3, 0, 7, 1, 2, 3, 4, 5, 6, 7]
        mult = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(n * m for n, m in zip(nums, mult))
        rem = total % 11
        check = 0 if rem == 0 else (9 if rem == 1 else 11 - rem)
        cuit = "3071234567" + str(check)
        result = validate_cuit_checksum(cuit)
        assert result["checksum_valid"] is True
        assert result["tipo_probable"] == "Persona jurídica"

    def test_unknown_prefix(self):
        # prefix 99 doesn't map to any known type
        nums = [9, 9, 1, 2, 3, 4, 5, 6, 7, 8]
        mult = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(n * m for n, m in zip(nums, mult))
        rem = total % 11
        check = 0 if rem == 0 else (9 if rem == 1 else 11 - rem)
        cuit = "9912345678" + str(check)
        result = validate_cuit_checksum(cuit)
        assert result["tipo_probable"] == "Desconocido (prefijo no estándar)"


class TestMonotributoSugerencia:
    def test_low_facturacion_gets_category_a(self):
        result = ARCAComplianceService.sugerir_categoria_monotributo(1_000_000, True)
        assert result["categoria_sugerida"] == "A"
        assert result["excede_tope"] is False

    def test_mid_range_picks_correct_bracket(self):
        result = ARCAComplianceService.sugerir_categoria_monotributo(10_000_000, True)
        assert result["categoria_sugerida"] == "C"
        assert result["tope_categoria"] == 13_250_000

    def test_services_only_caps_at_h(self):
        # categoria I/J/K only exist for vende_bienes=True; servicios-only
        # facturación beyond H's cap must skip straight to excede_tope
        result = ARCAComplianceService.sugerir_categoria_monotributo(50_000_000, False)
        assert result["excede_tope"] is True

    def test_bienes_can_reach_higher_categories(self):
        result = ARCAComplianceService.sugerir_categoria_monotributo(50_000_000, True)
        assert result["categoria_sugerida"] == "I"

    def test_over_absolute_limit(self):
        result = ARCAComplianceService.sugerir_categoria_monotributo(999_999_999, True)
        assert result["excede_tope"] is True
        assert result["categoria_sugerida"] is None

    def test_negative_facturacion_raises(self):
        with pytest.raises(ValueError):
            ARCAComplianceService.sugerir_categoria_monotributo(-100, True)

    def test_alerta_proximidad_tope_when_near_ceiling(self):
        # Categoria A tops out at 6,450,000; 95% of that should trigger the alert
        result = ARCAComplianceService.sugerir_categoria_monotributo(6_200_000, True)
        assert result["categoria_sugerida"] == "A"
        assert result["alerta_proximidad_tope"] is True


class TestNCMLookup:
    def test_valid_8_digit_resolves_chapter(self):
        result = ARCAComplianceService.lookup_ncm("84713012")
        assert result["valid_format"] is True
        assert result["capitulo_sa"] == "84"
        assert "máquinas" in result["capitulo_descripcion"].lower() or "aparatos" in result["capitulo_descripcion"].lower()

    def test_strips_dots_and_dashes(self):
        result = ARCAComplianceService.lookup_ncm("8471.30.12")
        assert result["valid_format"] is True
        assert result["formatted"] == "8471.30.12"

    def test_wrong_length_rejected_but_no_exception(self):
        result = ARCAComplianceService.lookup_ncm("847")
        assert result["valid_format"] is False

    def test_never_fabricates_full_description(self):
        """Integrity check: 8-digit description must stay None (no full NCM
        DB embedded) - this must never silently start returning fake data."""
        result = ARCAComplianceService.lookup_ncm("84713012")
        assert result["descripcion_completa_8_digitos"] is None


class TestIncoterms:
    def test_returns_all_11_official_rules(self):
        rows = ARCAComplianceService.get_incoterms()
        assert len(rows) == 11
        codes = {r["code"] for r in rows}
        assert codes == {"EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"}
