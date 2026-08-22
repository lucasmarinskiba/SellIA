"""Unit tests for FOMO Intelligence's integrity gate.

Pure logic, no DB/Redis needed - runs standalone:
    pytest backend/tests/test_fomo_intelligence.py -v

The core rule under test: FOMOIntelligenceService must never register a
strategy application with fabricated/incomplete data. This is what stops
the platform from shipping fake urgency copy ("Only 47 seats left") the
way the old Instagram automation code used to.
"""
import pytest

from app.domains.fomo_intelligence.service import FOMOIntelligenceService
from app.domains.fomo_intelligence.models import FOMOStrategyType


class TestIntegrityGate:
    def test_complete_escasez_real_data_renders_message(self):
        msg = FOMOIntelligenceService._validate_and_render(
            FOMOStrategyType.ESCASEZ_REAL,
            {"slots_remaining": 3, "total_slots": 50},
        )
        assert "3" in msg and "50" in msg

    def test_incomplete_escasez_real_raises(self):
        with pytest.raises(ValueError, match="faltan"):
            FOMOIntelligenceService._validate_and_render(
                FOMOStrategyType.ESCASEZ_REAL,
                {"slots_remaining": 3},  # missing total_slots
            )

    def test_complete_prueba_social_renders_message(self):
        msg = FOMOIntelligenceService._validate_and_render(
            FOMOStrategyType.PRUEBA_SOCIAL,
            {"buyer_name_or_alias": "María G.", "result_or_quote": "Cerré 3 deals en una semana"},
        )
        assert "María G." in msg
        assert "Cerré 3 deals en una semana" in msg

    def test_incomplete_prueba_social_raises(self):
        with pytest.raises(ValueError, match="faltan"):
            FOMOIntelligenceService._validate_and_render(
                FOMOStrategyType.PRUEBA_SOCIAL,
                {"buyer_name_or_alias": "María G."},  # missing result_or_quote
            )

    def test_complete_exclusividad_renders_message(self):
        msg = FOMOIntelligenceService._validate_and_render(
            FOMOStrategyType.EXCLUSIVIDAD,
            {"group_size_or_criteria": "primeros 20 clientes", "access_window": "hasta el viernes"},
        )
        assert "primeros 20 clientes" in msg

    def test_complete_transparencia_renders_message(self):
        msg = FOMOIntelligenceService._validate_and_render(
            FOMOStrategyType.TRANSPARENCIA,
            {"metric_name": "deals cerrados", "metric_value": "45", "verification_source": "funnel_health"},
        )
        assert "45" in msg and "funnel_health" in msg

    def test_incomplete_transparencia_raises(self):
        with pytest.raises(ValueError, match="faltan"):
            FOMOIntelligenceService._validate_and_render(
                FOMOStrategyType.TRANSPARENCIA,
                {"metric_name": "deals cerrados", "metric_value": "45"},  # missing verification_source
            )

    def test_empty_snapshot_always_raises_for_every_strategy(self):
        """No strategy should ever accept a completely empty data_snapshot -
        this is the last line of defense against a caller skipping real data."""
        for strategy in FOMOStrategyType:
            with pytest.raises(ValueError):
                FOMOIntelligenceService._validate_and_render(strategy, {})

    def test_error_message_names_missing_fields(self):
        """The rejection message should be actionable, not just 'invalid'."""
        with pytest.raises(ValueError) as exc_info:
            FOMOIntelligenceService._validate_and_render(
                FOMOStrategyType.ESCASEZ_REAL, {}
            )
        assert "slots_remaining" in str(exc_info.value)
        assert "total_slots" in str(exc_info.value)
