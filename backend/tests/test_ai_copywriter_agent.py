"""Fase A: AI FOMO Copywriter Agent Tests"""

import json
import uuid
import pytest
from unittest.mock import AsyncMock, patch

from app.domains.fomo.ai_copywriter_agent import (
    AICopywriterAgent,
    AICopywriterPromptBuilder,
    LLMResponseParser,
    VariantScorer,
    CopyTone,
    SupportedLanguage,
)


class FakeLLMResponse:
    def __init__(self, content, provider="anthropic", model="claude-3-5-sonnet-20241022"):
        self.content = content
        self.provider = provider
        self.model = model


VALID_SCHEMA_JSON = {
    "subject_lines": [
        "Últimas horas: 30% OFF en tu producto favorito",
        "No te pierdas esto - solo hoy",
        "Solo quedan 3 unidades disponibles",
    ],
    "preview_texts": ["Aprovecha antes que termine", "Oferta exclusiva", "Stock limitado"],
    "urgency_messages": ["Termina en 2 horas", "Solo 3 quedan", "Oferta de hoy"],
    "cta_texts": ["Comprar ahora", "Ver oferta", "Reservar ya"],
    "sms_variants": ["Oferta especial hoy, no te la pierdas. Compra ya."],
}


class TestPromptBuilder:
    def test_build_campaign_copy_prompt_structure(self):
        messages = AICopywriterPromptBuilder.build_campaign_copy_prompt(
            campaign_type="flash_sale",
            product_name="Zapatillas Pro",
            product_description="Zapatillas deportivas premium",
            audience="deportistas",
            tone=CopyTone.URGENT,
            language=SupportedLanguage.ES,
            variant_count=3,
        )
        assert len(messages) == 2
        assert "Zapatillas Pro" in messages[1].content
        assert "flash_sale" in messages[1].content

    def test_build_prompt_respects_language(self):
        messages_en = AICopywriterPromptBuilder.build_campaign_copy_prompt(
            campaign_type="cart_abandonment",
            product_name="Widget",
            product_description="A widget",
            audience="general",
            tone=CopyTone.FRIENDLY,
            language=SupportedLanguage.EN,
            variant_count=2,
        )
        assert "English" in messages_en[1].content

    def test_build_translation_prompt(self):
        messages = AICopywriterPromptBuilder.build_translation_prompt(
            VALID_SCHEMA_JSON, SupportedLanguage.EN
        )
        assert len(messages) == 2
        assert "subject_lines" in messages[1].content


class TestLLMResponseParser:
    def test_parse_clean_json(self):
        raw = json.dumps(VALID_SCHEMA_JSON)
        parsed = LLMResponseParser.parse_json_response(raw)
        assert parsed == VALID_SCHEMA_JSON

    def test_parse_json_with_markdown_fences(self):
        raw = f"```json\n{json.dumps(VALID_SCHEMA_JSON)}\n```"
        parsed = LLMResponseParser.parse_json_response(raw)
        assert parsed == VALID_SCHEMA_JSON

    def test_parse_json_embedded_in_text(self):
        raw = f"Here is the result:\n{json.dumps(VALID_SCHEMA_JSON)}\nHope this helps!"
        parsed = LLMResponseParser.parse_json_response(raw)
        assert parsed == VALID_SCHEMA_JSON

    def test_parse_invalid_json_returns_none(self):
        parsed = LLMResponseParser.parse_json_response("not json at all {{{")
        assert parsed is None

    def test_parse_empty_string_returns_none(self):
        assert LLMResponseParser.parse_json_response("") is None
        assert LLMResponseParser.parse_json_response(None) is None

    def test_validate_schema_valid(self):
        assert LLMResponseParser.validate_campaign_copy_schema(VALID_SCHEMA_JSON) is True

    def test_validate_schema_missing_key(self):
        bad = {k: v for k, v in VALID_SCHEMA_JSON.items() if k != "cta_texts"}
        assert LLMResponseParser.validate_campaign_copy_schema(bad) is False

    def test_validate_schema_empty_list(self):
        bad = dict(VALID_SCHEMA_JSON)
        bad["subject_lines"] = []
        assert LLMResponseParser.validate_campaign_copy_schema(bad) is False


class TestVariantScorer:
    def test_heuristic_score_urgency_boost(self):
        urgent = VariantScorer.score_by_heuristics("Última oportunidad, solo hoy termina")
        neutral = VariantScorer.score_by_heuristics("Este es un producto muy bueno de calidad")
        assert urgent > neutral

    def test_heuristic_score_excessive_caps_penalty(self):
        base = "Compra ahora antes que se acabe todo"
        shouty = VariantScorer.score_by_heuristics(base.upper())
        normal = VariantScorer.score_by_heuristics(base)
        assert shouty < normal

    def test_heuristic_score_optimal_length_bonus(self):
        optimal = VariantScorer.score_by_heuristics("x" * 45)
        too_long = VariantScorer.score_by_heuristics("x" * 120)
        assert optimal > too_long

    def test_score_range_bounded(self):
        score = VariantScorer.score_by_heuristics("hoy ahora último solo quedan termina expira")
        assert 0.0 <= score <= 100.0

    def test_historical_scoring_uses_matches(self):
        historical = [
            {"text": "Solo hoy: última oportunidad", "open_rate": 0.5, "click_rate": 0.3},
            {"text": "Termina pronto, no esperes", "open_rate": 0.4, "click_rate": 0.2},
        ]
        score = VariantScorer.score_by_historical_performance(
            "Última oportunidad, solo hoy", historical
        )
        assert score > 0

    def test_historical_scoring_falls_back_when_no_match(self):
        score = VariantScorer.score_by_historical_performance("Producto genérico sin nada especial", [])
        heuristic = VariantScorer.score_by_heuristics("Producto genérico sin nada especial")
        assert score == heuristic

    def test_rank_variants_sorted_descending(self):
        variants = [
            "Producto disponible",
            "ÚLTIMA OPORTUNIDAD HOY MISMO ACTUA YA",
            "Solo hoy: última oportunidad, quedan pocas",
        ]
        ranked = VariantScorer.rank_variants(variants)
        scores = [r["score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_variants_returns_text_and_score(self):
        ranked = VariantScorer.rank_variants(["Test variant"])
        assert ranked[0]["text"] == "Test variant"
        assert "score" in ranked[0]


class TestAICopywriterAgentGeneration:
    @pytest.mark.asyncio
    async def test_generate_campaign_copy_success(self):
        fake_response = FakeLLMResponse(json.dumps(VALID_SCHEMA_JSON))
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=fake_response),
        ):
            result = await AICopywriterAgent.generate_campaign_copy(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                campaign_type="flash_sale",
                product_name="Producto X",
                product_description="Descripción",
            )
        assert result["campaign_type"] == "flash_sale"
        assert result["generated_by"] == "anthropic"
        assert result["content"] == VALID_SCHEMA_JSON

    @pytest.mark.asyncio
    async def test_generate_campaign_copy_llm_none_uses_fallback(self):
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=None),
        ):
            result = await AICopywriterAgent.generate_campaign_copy(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                campaign_type="cart_abandonment",
                product_name="Producto Y",
                product_description="Desc",
                variant_count=3,
            )
        assert result["generated_by"] == "fallback_template"
        assert len(result["content"]["subject_lines"]) == 3

    @pytest.mark.asyncio
    async def test_generate_campaign_copy_bad_json_uses_fallback(self):
        fake_response = FakeLLMResponse("this is not valid json output")
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=fake_response),
        ):
            result = await AICopywriterAgent.generate_campaign_copy(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                campaign_type="countdown",
                product_name="Producto Z",
                product_description="Desc",
            )
        assert result["generated_by"] == "fallback_template"

    @pytest.mark.asyncio
    async def test_generate_campaign_copy_incomplete_schema_uses_fallback(self):
        incomplete = {"subject_lines": ["only this key"]}
        fake_response = FakeLLMResponse(json.dumps(incomplete))
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=fake_response),
        ):
            result = await AICopywriterAgent.generate_campaign_copy(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                campaign_type="flash_sale",
                product_name="P",
                product_description="D",
            )
        assert result["generated_by"] == "fallback_template"

    @pytest.mark.asyncio
    async def test_fallback_copy_variant_count_respected(self):
        result = AICopywriterAgent._fallback_copy("flash_sale", "Producto", 5)
        assert len(result["content"]["subject_lines"]) == 5
        assert len(result["content"]["cta_texts"]) == 5


class TestAICopywriterAgentRanking:
    @pytest.mark.asyncio
    async def test_generate_and_rank_produces_recommended(self):
        fake_response = FakeLLMResponse(json.dumps(VALID_SCHEMA_JSON))
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=fake_response),
        ):
            result = await AICopywriterAgent.generate_and_rank(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                campaign_type="flash_sale",
                product_name="Producto X",
                product_description="Descripción",
            )
        assert "ranked_content" in result
        assert "recommended" in result
        assert result["recommended"]["subject_lines"] in VALID_SCHEMA_JSON["subject_lines"]

    @pytest.mark.asyncio
    async def test_generate_and_rank_with_historical_data(self):
        fake_response = FakeLLMResponse(json.dumps(VALID_SCHEMA_JSON))
        historical = {
            "subject_lines": [
                {"text": "Últimas horas: 30% OFF en tu producto favorito", "open_rate": 0.6, "click_rate": 0.4}
            ]
        }
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=fake_response),
        ):
            result = await AICopywriterAgent.generate_and_rank(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                campaign_type="flash_sale",
                product_name="Producto X",
                product_description="Descripción",
                historical_data=historical,
            )
        # The variant with historical data should rank first
        assert result["ranked_content"]["subject_lines"][0]["text"] == (
            "Últimas horas: 30% OFF en tu producto favorito"
        )


class TestAICopywriterAgentTranslation:
    @pytest.mark.asyncio
    async def test_translate_copy_success(self):
        translated_json = {
            "subject_lines": ["Last hours: 30% OFF"],
            "preview_texts": ["Grab it now"],
            "urgency_messages": ["Ends in 2 hours"],
            "cta_texts": ["Buy now"],
            "sms_variants": ["Special offer today"],
        }
        fake_response = FakeLLMResponse(json.dumps(translated_json))
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=fake_response),
        ):
            result = await AICopywriterAgent.translate_copy(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                content=VALID_SCHEMA_JSON,
                target_language=SupportedLanguage.EN,
            )
        assert result["language"] == "en"
        assert result["content"] == translated_json

    @pytest.mark.asyncio
    async def test_translate_copy_llm_failure(self):
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=None),
        ):
            result = await AICopywriterAgent.translate_copy(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                content=VALID_SCHEMA_JSON,
                target_language=SupportedLanguage.PT,
            )
        assert result["error"] == "translation_failed"

    @pytest.mark.asyncio
    async def test_translate_copy_bad_json(self):
        fake_response = FakeLLMResponse("not valid json")
        with patch(
            "app.domains.fomo.ai_copywriter_agent.generate_with_fallback",
            new=AsyncMock(return_value=fake_response),
        ):
            result = await AICopywriterAgent.translate_copy(
                db=AsyncMock(),
                business_id=uuid.uuid4(),
                content=VALID_SCHEMA_JSON,
                target_language=SupportedLanguage.EN,
            )
        assert result["error"] == "translation_parse_failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
