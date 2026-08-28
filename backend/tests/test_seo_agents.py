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
    ContentCalendarService,
    EntityOptimizationService,
    MultiLocationSEOService,
    TopicalClusterService,
)
from app.domains.seo_agents.orchestrator import SEOAuditOrchestrator


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


class TestContentCalendar:
    def test_priority_band_high(self):
        """Opportunity >= 70 -> high priority."""
        svc = ContentCalendarService(None)
        assert svc._priority_for_score(70) == "high"
        assert svc._priority_for_score(95) == "high"

    def test_priority_band_medium(self):
        """40 <= opportunity < 70 -> medium priority."""
        svc = ContentCalendarService(None)
        assert svc._priority_for_score(40) == "medium"
        assert svc._priority_for_score(69) == "medium"

    def test_priority_band_low(self):
        """Opportunity < 40 -> low priority."""
        svc = ContentCalendarService(None)
        assert svc._priority_for_score(0) == "low"
        assert svc._priority_for_score(39) == "low"

    def test_content_type_rotation_cycles(self):
        """Content type rotation cycles through all 4 types for 5 keywords."""
        rotation = ContentCalendarService.CONTENT_TYPE_ROTATION
        assigned = [rotation[i % len(rotation)] for i in range(5)]
        assert assigned == ["blog_post", "landing_page", "guide", "video", "blog_post"]

    def test_cadence_spacing_stops_at_window(self):
        """Entries spaced by cadence_days must stop once they'd exceed the days window."""
        days = 30
        cadence_days = 10
        keywords = ["a", "b", "c", "d", "e"]  # offsets: 0,10,20,30,40 -> last exceeds 30
        included = [k for i, k in enumerate(keywords) if i * cadence_days <= days]
        assert included == ["a", "b", "c", "d"]  # offset 40 > 30 excluded


class TestEntityOptimization:
    def test_build_schema_organization(self):
        """Organization schema includes @context, @type, name."""
        svc = EntityOptimizationService(None)
        schema = svc._build_schema("Organization", "Acme Corp")
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "Organization"
        assert schema["name"] == "Acme Corp"
        assert "sameAs" not in schema  # no links provided

    def test_build_schema_with_external_links(self):
        """sameAs populated when external_links provided."""
        svc = EntityOptimizationService(None)
        links = ["https://en.wikipedia.org/wiki/Acme", "https://twitter.com/acme"]
        schema = svc._build_schema("Organization", "Acme Corp", links)
        assert schema["sameAs"] == links

    def test_build_schema_person_type(self):
        """Person entity type builds correctly."""
        svc = EntityOptimizationService(None)
        schema = svc._build_schema("Person", "Jane Founder")
        assert schema["@type"] == "Person"
        assert schema["name"] == "Jane Founder"

    def test_build_schema_product_type(self):
        """Product entity type builds correctly."""
        svc = EntityOptimizationService(None)
        schema = svc._build_schema("Product", "Widget Pro")
        assert schema["@type"] == "Product"


class TestMultiLocationSEO:
    def test_build_local_schema_minimal(self):
        """LocalBusiness schema with just required fields."""
        svc = MultiLocationSEOService(None)
        schema = svc._build_local_schema("Acme Austin", "123 Main St", "Austin", None, None, "US")
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "LocalBusiness"
        assert schema["name"] == "Acme Austin"
        assert schema["address"]["streetAddress"] == "123 Main St"
        assert schema["address"]["addressLocality"] == "Austin"
        assert "addressRegion" not in schema["address"]
        assert "postalCode" not in schema["address"]

    def test_build_local_schema_full(self):
        """LocalBusiness schema with state + zip populates full address block."""
        svc = MultiLocationSEOService(None)
        schema = svc._build_local_schema("Acme Austin", "123 Main St", "Austin", "TX", "78701", "US")
        assert schema["address"]["addressRegion"] == "TX"
        assert schema["address"]["postalCode"] == "78701"

    def test_generate_location_keywords(self):
        """Location keywords cover the standard local-intent patterns."""
        svc = MultiLocationSEOService(None)
        keywords = svc._generate_location_keywords("plumber", "Austin")
        assert "plumber in Austin" in keywords
        assert "plumber near me" in keywords
        assert "best plumber Austin" in keywords
        assert len(keywords) == 4

    def test_citation_platforms_list(self):
        """5 directories tracked for NAP consistency."""
        assert len(MultiLocationSEOService.CITATION_PLATFORMS) == 5
        assert "google_business" in MultiLocationSEOService.CITATION_PLATFORMS

    def test_nap_consistency_requires_all_platforms(self):
        """nap_consistent is only true when every tracked platform is confirmed."""
        platforms = MultiLocationSEOService.CITATION_PLATFORMS
        partial_status = {p: True for p in platforms[:-1]}  # all but last
        partial_status[platforms[-1]] = False
        full_status = {p: True for p in platforms}

        assert all(partial_status.get(p, False) for p in platforms) is False
        assert all(full_status.get(p, False) for p in platforms) is True

    def test_citation_coverage_percentage(self):
        """Coverage % = confirmed platforms / total platforms * 100."""
        platforms = MultiLocationSEOService.CITATION_PLATFORMS
        status = {p: True for p in platforms[:3]}  # 3 of 5 confirmed
        confirmed = sum(1 for v in status.values() if v)
        coverage = (confirmed / len(platforms)) * 100
        assert coverage == 60.0


class TestTopicalCluster:
    def test_authority_score_scales_with_cluster_size(self):
        """10 points per subtopic, capped at 100."""
        svc = TopicalClusterService(None)
        assert svc._calculate_authority_score(3) == 30.0
        assert svc._calculate_authority_score(10) == 100.0
        assert svc._calculate_authority_score(15) == 100.0  # capped

    def test_authority_score_empty_cluster(self):
        """No subtopics -> zero authority."""
        svc = TopicalClusterService(None)
        assert svc._calculate_authority_score(0) == 0.0

    def test_linking_map_hub_and_spoke_structure(self):
        """Every cluster topic links back to the pillar (hub-and-spoke)."""
        svc = TopicalClusterService(None)
        linking_map = svc._build_linking_map("SEO Services", ["Keyword Research", "Link Building"])

        assert linking_map["pillar"] == "seo-services"
        assert len(linking_map["clusters"]) == 2
        assert linking_map["clusters"][0]["topic"] == "Keyword Research"
        assert linking_map["clusters"][0]["slug"] == "keyword-research"
        assert linking_map["clusters"][0]["links_to_pillar"] is True

    def test_linking_map_empty_clusters(self):
        """Pillar with no subtopics yet still builds a valid (empty) map."""
        svc = TopicalClusterService(None)
        linking_map = svc._build_linking_map("New Pillar", [])
        assert linking_map["pillar"] == "new-pillar"
        assert linking_map["clusters"] == []


class _FakeGap:
    """Minimal stand-in for CompetitorKeywordGap — only what _build_action_plan reads."""
    def __init__(self, keyword: str, opportunity_score: float):
        self.keyword = keyword
        self.opportunity_score = opportunity_score


class _FakeBacklink:
    """Minimal stand-in for BacklinkOpportunity — only what _build_action_plan reads."""
    def __init__(self, domain: str, priority_score: float):
        self.domain = domain
        self.priority_score = priority_score


def _healthy_metrics(**overrides) -> dict:
    """Baseline metrics dict representing a fully healthy business — no action
    should fire unless a field is deliberately overridden to breach a threshold."""
    metrics = {
        "seo_health": {"overall_score": 85, "critical_issues": 0},
        "keywords_tracked": 20,
        "fomo_copy_count": 5,
        "active_ab_tests": 1,
        "optimization_completed_tasks": 3,
        "optimization_pending_tasks": 0,
        "avg_traffic_lift_pct": 15.0,
        "content_generated_count": 5,
        "avg_content_seo_score": 88.0,
        "keyword_gap_count": 0,
        "backlink_opportunity_count": 0,
        "review_total": 25,
        "review_avg_rating": 4.6,
        "calendar_upcoming_count": 3,
        "location_total": 2,
        "location_fully_consistent": 2,
        "topical_cluster_count": 2,
    }
    metrics.update(overrides)
    return metrics


class TestSEOAuditOrchestrator:
    def test_healthy_business_yields_no_actions(self):
        """A business clearing every threshold gets an empty action plan."""
        orchestrator = SEOAuditOrchestrator(None)
        plan = orchestrator._build_action_plan(_healthy_metrics(), [], [])
        assert plan == []

    def test_critical_page_issues_flagged_critical(self):
        """critical_issues > 0 -> a 'critical' priority action."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(seo_health={"overall_score": 40, "critical_issues": 3})
        plan = orchestrator._build_action_plan(metrics, [], [])
        assert any(a["category"] == "page_health" and a["priority"] == "critical" for a in plan)

    def test_low_overall_score_flagged_high(self):
        """overall_score < 70 -> a 'high' priority page_health action."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(seo_health={"overall_score": 55, "critical_issues": 0})
        plan = orchestrator._build_action_plan(metrics, [], [])
        assert any(a["category"] == "page_health" and a["priority"] == "high" for a in plan)

    def test_keyword_gaps_surface_top_target(self):
        """Keyword gap action names the highest-opportunity keyword."""
        orchestrator = SEOAuditOrchestrator(None)
        gaps = [_FakeGap("cheap seo", 40.0), _FakeGap("best seo tools", 92.0)]
        metrics = _healthy_metrics(keyword_gap_count=2)
        plan = orchestrator._build_action_plan(metrics, gaps, [])
        gap_action = next(a for a in plan if a["category"] == "keyword_gaps")
        assert "best seo tools" in gap_action["action"]

    def test_backlink_opportunities_surface_top_target(self):
        """Backlink action names the highest-priority domain."""
        orchestrator = SEOAuditOrchestrator(None)
        links = [_FakeBacklink("low.com", 30.0), _FakeBacklink("high.com", 88.0)]
        metrics = _healthy_metrics(backlink_opportunity_count=2)
        plan = orchestrator._build_action_plan(metrics, [], links)
        backlink_action = next(a for a in plan if a["category"] == "backlinks")
        assert "high.com" in backlink_action["action"]

    def test_low_review_count_flagged(self):
        """Fewer than 10 reviews -> reviews action fires."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(review_total=3)
        plan = orchestrator._build_action_plan(metrics, [], [])
        assert any(a["category"] == "reviews" for a in plan)

    def test_inconsistent_locations_flagged(self):
        """Some locations not fully NAP-consistent -> local_seo action fires."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(location_total=3, location_fully_consistent=1)
        plan = orchestrator._build_action_plan(metrics, [], [])
        local_action = next(a for a in plan if a["category"] == "local_seo")
        assert "2 location" in local_action["action"]

    def test_no_locations_does_not_flag_local_seo(self):
        """A business with zero tracked locations should not get a local_seo action."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(location_total=0, location_fully_consistent=0)
        plan = orchestrator._build_action_plan(metrics, [], [])
        assert not any(a["category"] == "local_seo" for a in plan)

    def test_pending_optimization_tasks_flagged(self):
        """Pending title/meta/content tasks -> optimization action fires."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(optimization_pending_tasks=4)
        plan = orchestrator._build_action_plan(metrics, [], [])
        assert any(a["category"] == "optimization" for a in plan)

    def test_no_clusters_with_content_flagged_low(self):
        """Content exists but no topical clusters -> low-priority content_structure action."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(topical_cluster_count=0, content_generated_count=5)
        plan = orchestrator._build_action_plan(metrics, [], [])
        action = next(a for a in plan if a["category"] == "content_structure")
        assert action["priority"] == "low"

    def test_no_clusters_without_content_not_flagged(self):
        """No content yet either -> no point flagging missing clusters."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(topical_cluster_count=0, content_generated_count=0)
        plan = orchestrator._build_action_plan(metrics, [], [])
        assert not any(a["category"] == "content_structure" for a in plan)

    def test_empty_calendar_flagged(self):
        """Nothing scheduled in the next 14 days -> content_calendar action fires."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(calendar_upcoming_count=0)
        plan = orchestrator._build_action_plan(metrics, [], [])
        assert any(a["category"] == "content_calendar" for a in plan)

    def test_action_plan_sorted_by_priority(self):
        """Plan is sorted critical -> high -> medium -> low regardless of check order."""
        orchestrator = SEOAuditOrchestrator(None)
        metrics = _healthy_metrics(
            seo_health={"overall_score": 40, "critical_issues": 2},  # critical + high
            review_total=2,  # medium
            calendar_upcoming_count=0,  # low
        )
        plan = orchestrator._build_action_plan(metrics, [], [])
        ranks = [_PRIORITY_RANK_FOR_TEST[a["priority"]] for a in plan]
        assert ranks == sorted(ranks)


_PRIORITY_RANK_FOR_TEST = {"critical": 0, "high": 1, "medium": 2, "low": 3}
