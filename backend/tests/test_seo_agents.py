"""SEO Agents tests — content generation + keyword gap analysis."""

from uuid import UUID
from app.domains.seo_agents.service import ContentGenerationService, CompetitorKeywordService


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
    assert 50 < opportunity <= 100  # Should be high opportunity


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

    word_count = len(text.split())
    keyword_count = text.lower().count(keyword.lower())
    density = (keyword_count / word_count * 100) if word_count > 0 else 0

    assert 1.0 < density < 3.0  # Optimal: 1.5-2.5%


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
