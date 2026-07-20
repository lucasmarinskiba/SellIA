"""Tests para Lookalike Audience Engine."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from app.domains.social_sellers.lookalike_scorer import (
    calculate_similarity_score,
    extract_behavioral_features,
    match_platform_preference,
)
from app.domains.social_sellers.lookalike import LookalikeEngine


# ─── Pure Scorer Tests ───────────────────────────────────────────────────────

class TestCalculateSimilarityScore:
    def test_perfect_match(self):
        lead_data = {
            'platform': 'instagram',
            'engagement': {'total_messages': 15, 'inbound_ratio': 0.9},
            'intent': {'buying_keywords': 5, 'price_mentioned': True},
            'behavior': {
                'response_time_avg_seconds': 120,
                'question_count': 4,
                'emoji_usage_rate': 0.15,
                'message_length_avg': 25,
            },
            'demographic': {'email': 'a@b.com', 'phone': '+123', 'name': 'Juan'},
        }
        ideal_profile = {'preferred_platforms': ['instagram']}
        score = calculate_similarity_score(lead_data, ideal_profile)
        assert 80 <= score <= 100

    def test_no_match(self):
        lead_data = {
            'platform': 'linkedin',
            'engagement': {'total_messages': 0, 'inbound_ratio': 0.0},
            'intent': {'buying_keywords': 0, 'price_mentioned': False},
            'behavior': {
                'response_time_avg_seconds': None,
                'question_count': 0,
                'emoji_usage_rate': 0.0,
                'message_length_avg': 0,
            },
            'demographic': {'email': None, 'phone': None, 'name': None},
        }
        ideal_profile = {'preferred_platforms': ['instagram']}
        score = calculate_similarity_score(lead_data, ideal_profile)
        assert 0 <= score <= 20

    def test_deterministic(self):
        lead_data = {
            'platform': 'tiktok',
            'engagement': {'total_messages': 8, 'inbound_ratio': 0.6},
            'intent': {'buying_keywords': 2, 'price_mentioned': False},
            'behavior': {
                'response_time_avg_seconds': 600,
                'question_count': 1,
                'emoji_usage_rate': 0.05,
                'message_length_avg': 15,
            },
            'demographic': {'email': 'x@y.com', 'phone': None, 'name': 'Ana'},
        }
        ideal_profile = {'preferred_platforms': ['tiktok', 'instagram']}
        s1 = calculate_similarity_score(lead_data, ideal_profile)
        s2 = calculate_similarity_score(lead_data, ideal_profile)
        assert s1 == s2

    def test_platform_similarity_boost(self):
        lead_data = {
            'platform': 'messenger',
            'engagement': {'total_messages': 0, 'inbound_ratio': 0.0},
            'intent': {'buying_keywords': 0, 'price_mentioned': False},
            'behavior': {},
            'demographic': {},
        }
        ideal_profile = {'preferred_platforms': ['facebook']}
        score = calculate_similarity_score(lead_data, ideal_profile)
        # messenger es similar a facebook => 0.5 * 10 = 5 pts mínimo
        assert score >= 5


class TestExtractBehavioralFeatures:
    def test_empty_messages(self):
        features = extract_behavioral_features([])
        assert features['response_time_avg_seconds'] is None
        assert features['question_count'] == 0
        assert features['price_mention_count'] == 0
        assert features['emoji_usage_rate'] == 0.0
        assert features['message_length_avg'] == 0.0

    def test_response_time_calculation(self):
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        messages = [
            {
                'content': 'Hola!',
                'direction': 'outbound',
                'created_at': now,
            },
            {
                'content': 'Buenas',
                'direction': 'inbound',
                'created_at': now + timedelta(seconds=120),
            },
        ]
        features = extract_behavioral_features(messages)
        assert features['response_time_avg_seconds'] == 120.0

    def test_question_count(self):
        messages = [
            {'content': 'Cuánto cuesta?', 'direction': 'inbound', 'created_at': datetime.now(timezone.utc)},
            {'content': 'Hay stock?', 'direction': 'inbound', 'created_at': datetime.now(timezone.utc)},
            {'content': 'Dale', 'direction': 'inbound', 'created_at': datetime.now(timezone.utc)},
        ]
        features = extract_behavioral_features(messages)
        assert features['question_count'] == 2

    def test_price_mentions(self):
        messages = [
            {'content': 'precio?', 'direction': 'inbound', 'created_at': datetime.now(timezone.utc)},
            {'content': 'cuesta mucho', 'direction': 'inbound', 'created_at': datetime.now(timezone.utc)},
            {'content': 'ok', 'direction': 'inbound', 'created_at': datetime.now(timezone.utc)},
        ]
        features = extract_behavioral_features(messages)
        assert features['price_mention_count'] == 2

    def test_emoji_usage(self):
        messages = [
            {'content': 'Hola 😊', 'direction': 'inbound', 'created_at': datetime.now(timezone.utc)},
            {'content': 'Gracias 🙏', 'direction': 'inbound', 'created_at': datetime.now(timezone.utc)},
        ]
        features = extract_behavioral_features(messages)
        assert features['emoji_usage_rate'] > 0.0
        assert features['message_length_avg'] > 0.0


class TestMatchPlatformPreference:
    def test_exact_match(self):
        assert match_platform_preference('instagram', ['instagram']) == 1.0

    def test_similar_match(self):
        assert match_platform_preference('messenger', ['facebook']) == 0.5
        assert match_platform_preference('tiktok', ['instagram']) == 0.5

    def test_no_match(self):
        assert match_platform_preference('linkedin', ['instagram']) == 0.0

    def test_case_insensitive(self):
        assert match_platform_preference('Instagram', ['INSTAGRAM']) == 1.0


# ─── Engine Tests (con MagicMock) ────────────────────────────────────────────

@pytest.mark.asyncio
class TestLookalikeEngine:
    async def test_build_ideal_customer_profile_empty(self):
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        engine = LookalikeEngine(db)
        profile = await engine.build_ideal_customer_profile('biz-123')
        assert profile['avg_lifetime_value'] == 0.0
        assert profile['preferred_platforms'] == []

    async def test_prioritize_leads_empty(self):
        db = MagicMock()
        # First call: no customers -> empty profile
        db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        engine = LookalikeEngine(db)
        leads = await engine.prioritize_leads('biz-123')
        assert leads == []

    async def test_get_lookalike_report_empty(self):
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        engine = LookalikeEngine(db)
        report = await engine.get_lookalike_report('biz-123')
        assert 'summary' in report
        assert report['total_leads_scored'] == 0
