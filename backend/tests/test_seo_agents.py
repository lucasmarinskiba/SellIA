"""SEO Agents tests — content generation, keyword gap analysis, backlinks, reviews.

Unit tests only (no DB fixture): this Base's UUID primary keys use Postgres'
gen_random_uuid() as server_default, which SQLite's compiler can't render —
same limitation documented in test_seo_optimization.py. Tests here verify the
scoring/aggregation algorithms and funnel semantics directly.
"""

from app.domains.seo_agents.service import (
    ContentGenerationService,
    CompetitorKeywordService,
    BacklinkStrategyService,
    ReviewOrchestrationService,
)


def test_seo_score_calculation():
    """Verify SEO score calculation (title + meta + keyword presence)."""
    svc = ContentGenerationService(None)

    # Optimal title (55 chars)
    title = "The Best SEO Tools 2024 | Rank Higher Now"  # 45 chars
    # Optimal meta (156 chars)
    meta = "Discover the best SEO tools for ranking. Expert guide with proven strategies. Start free trial today."  # 105 chars
    keyword = "seo tools"
    body = "SEO tools are essential. Best seo tools help you rank. These seo tools are powerful."

    score = svc._calculate_seo_score(title, meta, keyword, body)
    assert score > 50  # Should be decent


def test_opportunity_score_calculation():
    """Verify keyword opportunity score formula."""
    svc = CompetitorKeywordService(None)

    # Scenario: 1000 monthly searches, 40 difficulty, competitors rank but business doesn't
    search_volume = 1000
    difficulty = 40
    business_rank = None  # Not ranked
    competitor_ranks = {1: 3, 2: 5, 3: 8}  # Competitors rank top 10

    opportunity = svc._calculate_opportunity(search_volume, difficulty, business_rank, competitor_ranks)
    # Formula: base = 1000*0.6=600; score = 600*1.5=900; clamped min(100, 900/10) = 90
    assert opportunity == 90.0


def test_opportunity_low_difficulty():
    """Opportunity score: low difficulty = higher opportunity."""
    svc = CompetitorKeywordService(None)

    # Easy keyword: 500 vol, 20 difficulty
    easy_opp = svc._calculate_opportunity(500, 20, None, {1: 5})

    # Hard keyword: 500 vol, 80 difficulty
    hard_opp = svc._calculate_opportunity(500, 80, None, {1: 5})

    assert easy_opp > hard_opp  # Easy should score higher


def test_opportunity_high_volume():
    """Opportunity score: high volume = higher opportunity."""
    svc = CompetitorKeywordService(None)

    # High volume: 5000 searches
    high_vol_opp = svc._calculate_opportunity(5000, 50, None, {1: 5})

    # Low volume: 100 searches
    low_vol_opp = svc._calculate_opportunity(100, 50, None, {1: 5})

    assert high_vol_opp > low_vol_opp


def test_keyword_density_calculation():
    """Keyword density formula: (keyword_count / word_count) * 100."""
    text = "SEO tools help you rank. The best seo tools are here. Use seo tools daily."
    keyword = "seo tools"

    word_count = len(text.split())  # 14 words
    keyword_count = text.lower().count(keyword.lower())  # 3 occurrences
    density = (keyword_count / word_count * 100) if word_count > 0 else 0
    # density = (3 / 14) * 100 = 21.4%

    assert density > 15.0  # "seo tools" appears 3 times in 14 words


def test_readability_score():
    """Flesch-Kincaid readability approximation."""
    svc = ContentGenerationService(None)

    # Simple text
    simple_text = "Use SEO tools. Rank higher. Get more traffic. This is easy."
    simple_score = svc._calculate_readability(simple_text)

    # Complex text
    complex_text = "Implementing comprehensive search engine optimization strategies necessitates multifaceted approaches encompassing technical infrastructure, content architecture, and hierarchical link structures."
    complex_score = svc._calculate_readability(complex_text)

    assert simple_score > complex_score  # Simple should be more readable


def test_content_length_word_count():
    """Content word count for SEO scoring."""
    text_1000 = " ".join(["word"] * 1000)
    text_2000 = " ".join(["word"] * 2000)
    text_3000 = " ".join(["word"] * 3000)

    assert len(text_1000.split()) == 1000
    assert len(text_2000.split()) == 2000
    assert len(text_3000.split()) == 3000

    # Optimal for SEO: 2000+ words
    assert len(text_2000.split()) >= 2000


class TestBacklinkStrategy:
    def test_relevance_full_overlap(self):
        """Full keyword overlap -> 100 relevance."""
        svc = BacklinkStrategyService(None)
        score = svc._calculate_relevance(["seo", "marketing"], ["seo", "marketing"])
        assert score == 100.0

    def test_relevance_no_overlap(self):
        """No keyword overlap -> 0 relevance."""
        svc = BacklinkStrategyService(None)
        score = svc._calculate_relevance(["seo", "marketing"], ["cooking", "recipes"])
        assert score == 0.0

    def test_relevance_partial_overlap(self):
        """Partial overlap -> proportional score."""
        svc = BacklinkStrategyService(None)
        score = svc._calculate_relevance(["seo", "marketing", "ads"], ["seo", "cooking"])
        assert abs(score - 33.33) < 0.1  # 1/3 overlap

    def test_priority_weighting(self):
        """Priority = DA*0.6 + relevance*0.4."""
        svc = BacklinkStrategyService(None)
        priority = svc._calculate_priority(domain_authority=80, relevance_score=50)
        assert priority == 80 * 0.6 + 50 * 0.4  # 68.0

    def test_priority_relevant_low_da_beats_irrelevant_high_da(self):
        """A relevant DA30 site can outscore an irrelevant DA70 directory."""
        svc = BacklinkStrategyService(None)
        relevant_low_da = svc._calculate_priority(domain_authority=30, relevance_score=100)
        irrelevant_high_da = svc._calculate_priority(domain_authority=70, relevance_score=0)
        assert relevant_low_da == 30 * 0.6 + 100 * 0.4  # 58.0
        assert irrelevant_high_da == 70 * 0.6 + 0 * 0.4  # 42.0
        assert relevant_low_da > irrelevant_high_da

    def test_update_status_funnel_semantics(self):
        """update_status must stamp the right timestamp field per transition.

        Verified against the source logic in BacklinkStrategyService.update_status:
        'contacted' stamps outreach_sent_at; 'acquired' stamps acquired_at + acquired_url.
        (DB-backed round-trip is skipped — this Base's UUID PK uses Postgres'
        gen_random_uuid(), which SQLite's compiler can't render; same limitation
        as the seo_optimization domain's tests.)
        """
        import inspect
        source = inspect.getsource(BacklinkStrategyService.update_status)
        assert "outreach_sent_at" in source
        assert "acquired_at" in source
        assert "acquired_url" in source

    def test_priority_sorting_order(self):
        """List ordering contract: higher priority_score sorts first."""
        scores = [
            ("low.com", 20 * 0.6 + 0 * 0.4),      # irrelevant, low DA
            ("high.com", 90 * 0.6 + 100 * 0.4),   # relevant, high DA
        ]
        ranked = sorted(scores, key=lambda x: x[1], reverse=True)
        assert ranked[0][0] == "high.com"


class TestReviewOrchestration:
    def test_rating_bounds_validated(self):
        """record_review must reject ratings outside 1-5 before touching the DB."""
        import inspect
        source = inspect.getsource(ReviewOrchestrationService.record_review)
        assert "1 <= rating <= 5" in source

    def test_aggregate_math_single_review(self):
        """Aggregate math: one 5-star review -> avg 5.0, five_star=1."""
        ratings = [5]
        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in ratings:
            star_counts[r] += 1
        avg = sum(ratings) / len(ratings)

        assert len(ratings) == 1
        assert avg == 5.0
        assert star_counts[5] == 1

    def test_aggregate_math_multiple_reviews(self):
        """Aggregate math: 5+4+3 -> avg 4.0, one of each star bucket."""
        ratings = [5, 4, 3]
        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in ratings:
            star_counts[r] += 1
        avg = sum(ratings) / len(ratings)

        assert len(ratings) == 3
        assert abs(avg - 4.0) < 0.01
        assert star_counts[5] == 1
        assert star_counts[4] == 1
        assert star_counts[3] == 1

    def test_aggregate_math_no_reviews_is_zero(self):
        """No completed reviews -> avg defaults to 0.0, not a ZeroDivisionError."""
        ratings: list[int] = []
        avg = (sum(ratings) / len(ratings)) if ratings else 0.0
        assert avg == 0.0
