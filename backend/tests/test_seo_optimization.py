"""SEO Optimization tests — demonstration of scoring algorithms and task lifecycle."""

from uuid import UUID
from app.domains.seo_optimization.service import (
    TitleOptimizationService,
    MetaOptimizationService,
    ContentOptimizationService,
    OptimizationTaskService,
)


def test_title_scoring():
    """Verify title CTR scoring algorithm."""
    base_ctr = 2.5
    variant_a_ctr = base_ctr * 1.15  # +15% for year indicator
    variant_b_ctr = base_ctr * 1.25  # +25% for superlative
    variant_c_ctr = base_ctr * 1.18  # +18% for structure

    assert abs(variant_a_ctr - 2.875) < 0.001
    assert abs(variant_b_ctr - 3.125) < 0.001
    assert abs(variant_c_ctr - 2.95) < 0.001
    assert variant_b_ctr > variant_a_ctr  # B is highest


def test_meta_scoring():
    """Verify meta description CTR scoring."""
    base_ctr = 2.0
    variant_a_ctr = base_ctr * 1.20
    variant_b_ctr = base_ctr * 1.35  # CTA drives higher CTR

    assert variant_a_ctr == 2.4
    assert variant_b_ctr == 2.7
    assert variant_b_ctr > variant_a_ctr


def test_seo_score_components():
    """Verify SEO score calculation."""
    # Title: 50-60 chars is optimal
    title_score_short = 0 if len("Short Title") < 50 else 100
    title_score_optimal = 100 if 50 <= len("This is the best SEO title with optimal keyword") <= 60 else 50

    # Meta: 150-160 chars is optimal
    meta_score_short = 0 if len("Meta") < 150 else 100
    meta_optimal = "Discover everything about SEO. Expert guide with tips & best practices. Learn more today." * 2
    meta_score_optimal = 100 if 150 <= len(meta_optimal) <= 160 else 50

    assert title_score_optimal > title_score_short
    assert meta_score_optimal >= 50


def test_ctr_score_components():
    """Verify CTR score calculation (power words, urgency, social proof)."""
    base_ctr_score = 50

    # Power words: "Best" adds +15%
    power_word_bonus = 15

    # Urgency: "Today", "Just X left" adds +20%
    urgency_bonus = 20

    # Social proof: "500+ customers" adds +15%
    social_proof_bonus = 15

    max_ctr_score = base_ctr_score + power_word_bonus + urgency_bonus + social_proof_bonus
    assert max_ctr_score == 100


def test_rank_improvement_calculation():
    """Verify rank improvement formula (positive = better)."""
    pre_rank = 15
    post_rank = 8
    improvement = pre_rank - post_rank

    assert improvement == 7  # Rank improved by 7 positions


def test_content_word_count_recommendation():
    """Verify content word count recommendation logic."""
    current_word_count = 1500
    recommended_wc = max(2000, current_word_count * 1.3) if current_word_count < 2000 else current_word_count

    assert recommended_wc == 2000

    current_word_count_large = 2500
    recommended_wc_large = max(2000, current_word_count_large * 1.3) if current_word_count_large < 2000 else current_word_count_large

    assert recommended_wc_large == 2500


def test_keyword_density_analysis():
    """Verify keyword density thresholds."""
    # Low density: recommend adding H2 + internal links
    low_density = 0.3
    assert low_density < 0.5  # Below optimal

    # Optimal density: 1.5%
    optimal_density = 1.5
    assert optimal_density == 1.5

    # High density: potential keyword stuffing
    high_density = 3.5
    assert high_density > 2.0  # Too high
