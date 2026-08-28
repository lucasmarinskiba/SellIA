"""SEO Audit Orchestrator — ties every SEO domain together into one
'run full audit + action plan' call per business.

Reads (read-only, no writes) across:
  - seo_intelligence  (page health, keyword tracking)
  - fomo_seo          (psychological copy + A/B tests)
  - seo_optimization  (title/meta/content optimization tasks)
  - seo_agents        (content gen, keyword gaps, backlinks, reviews,
                        calendar, entities, locations, topical clusters)

Produces a single dashboard payload plus a prioritized action_plan the
business owner (or an automation) can act on directly.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_intelligence.service import PageOptimizationService, KeywordService
from app.domains.fomo_seo.service import FOMOSEOCopyService, A_B_TestService
from app.domains.seo_optimization.service import OptimizationTaskService
from app.domains.seo_agents.service import (
    ContentGenerationService,
    CompetitorKeywordService,
    BacklinkStrategyService,
    ReviewOrchestrationService,
    ContentCalendarService,
    MultiLocationSEOService,
    TopicalClusterService,
)

logger = get_logger(__name__)

# Priority ranks for sorting the action plan (lower = more urgent)
_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class SEOAuditOrchestrator:
    """Aggregates every SEO domain's state for a business and derives a
    prioritized, thresholds-based action plan. Read-only — never mutates state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_audit(self, business_id: uuid.UUID) -> dict:
        """Run the full cross-domain audit and return dashboard + action plan."""

        # seo_intelligence
        seo_health = await PageOptimizationService(self.db).seo_health(business_id)
        keywords = await KeywordService(self.db).list_keywords(business_id)

        # fomo_seo
        fomo_copy = await FOMOSEOCopyService(self.db).list_copy(business_id)
        ab_tests = await A_B_TestService(self.db).list_tests(business_id)

        # seo_optimization
        optimization_dashboard = await OptimizationTaskService(self.db).impact_dashboard(business_id)
        pending_optimization_tasks = await OptimizationTaskService(self.db).list_pending_tasks(business_id)

        # seo_agents: content + keyword gaps
        generated_content = await ContentGenerationService(self.db).list_content(business_id)
        keyword_gaps = await CompetitorKeywordService(self.db).list_gaps(business_id, min_opportunity=60.0)

        # seo_agents: backlinks + reviews
        backlink_opportunities = await BacklinkStrategyService(self.db).list_opportunities(
            business_id, min_priority=60.0
        )
        review_aggregate = await ReviewOrchestrationService(self.db).get_aggregate(business_id)

        # seo_agents: calendar + locations + clusters
        upcoming_calendar = await ContentCalendarService(self.db).upcoming_entries(business_id, within_days=14)
        citation_report = await MultiLocationSEOService(self.db).citation_consistency_report(business_id)
        topical_clusters = await TopicalClusterService(self.db).list_clusters(business_id)

        avg_content_seo_score = (
            sum(c.seo_score for c in generated_content) / len(generated_content)
            if generated_content
            else 0.0
        )

        metrics = {
            "seo_health": seo_health,
            "keywords_tracked": len(keywords),
            "fomo_copy_count": len(fomo_copy),
            "active_ab_tests": len(ab_tests),
            "optimization_completed_tasks": optimization_dashboard.get("completed_tasks", 0),
            "optimization_pending_tasks": len(pending_optimization_tasks),
            "avg_traffic_lift_pct": optimization_dashboard.get("avg_traffic_lift_pct", 0.0),
            "content_generated_count": len(generated_content),
            "avg_content_seo_score": round(avg_content_seo_score, 1),
            "keyword_gap_count": len(keyword_gaps),
            "backlink_opportunity_count": len(backlink_opportunities),
            "review_total": review_aggregate.total_reviews if review_aggregate else 0,
            "review_avg_rating": review_aggregate.average_rating if review_aggregate else 0.0,
            "calendar_upcoming_count": len(upcoming_calendar),
            "location_total": citation_report.get("total_locations", 0),
            "location_fully_consistent": citation_report.get("fully_consistent", 0),
            "topical_cluster_count": len(topical_clusters),
        }

        action_plan = self._build_action_plan(metrics, keyword_gaps, backlink_opportunities)

        logger.info(f"SEO audit run for business {business_id}: {len(action_plan)} actions identified")

        return {
            "business_id": str(business_id),
            "metrics": metrics,
            "action_plan": action_plan,
        }

    def _build_action_plan(
        self,
        metrics: dict,
        keyword_gaps: list,
        backlink_opportunities: list,
    ) -> list[dict]:
        """Derive a prioritized action plan from threshold checks against the
        aggregated metrics. Pure function of its inputs — no DB access — so it
        can be unit-tested directly with hand-built metrics dicts.
        """
        actions: list[dict] = []

        overall_score = metrics["seo_health"].get("overall_score", 0)
        critical_issues = metrics["seo_health"].get("critical_issues", 0)

        if critical_issues > 0:
            actions.append({
                "category": "page_health",
                "priority": "critical",
                "action": f"Fix {critical_issues} page(s) with critical SEO issues (optimization_score < 30)",
                "impact_estimate": "high",
            })

        if overall_score < 70:
            actions.append({
                "category": "page_health",
                "priority": "high",
                "action": f"Overall SEO health score is {overall_score}/100 — run content generation on underperforming pages",
                "impact_estimate": "high",
            })

        if metrics["keyword_gap_count"] > 0:
            top_gap = max(keyword_gaps, key=lambda g: g.opportunity_score) if keyword_gaps else None
            action_text = f"Generate content for {metrics['keyword_gap_count']} high-opportunity keyword gap(s)"
            if top_gap:
                action_text += f" — top target: '{top_gap.keyword}' (opportunity {top_gap.opportunity_score:.0f})"
            actions.append({
                "category": "keyword_gaps",
                "priority": "high",
                "action": action_text,
                "impact_estimate": "high",
            })

        if metrics["backlink_opportunity_count"] > 0:
            top_backlink = (
                max(backlink_opportunities, key=lambda b: b.priority_score) if backlink_opportunities else None
            )
            action_text = f"Begin outreach on {metrics['backlink_opportunity_count']} high-priority backlink opportunit(y/ies)"
            if top_backlink:
                action_text += f" — top target: {top_backlink.domain} (priority {top_backlink.priority_score:.0f})"
            actions.append({
                "category": "backlinks",
                "priority": "medium",
                "action": action_text,
                "impact_estimate": "medium",
            })

        if metrics["review_total"] < 10:
            actions.append({
                "category": "reviews",
                "priority": "medium",
                "action": f"Only {metrics['review_total']} reviews collected — launch review solicitation campaigns to reach 10+ for AggregateRating eligibility",
                "impact_estimate": "medium",
            })

        if metrics["location_total"] > 0 and metrics["location_fully_consistent"] < metrics["location_total"]:
            inconsistent = metrics["location_total"] - metrics["location_fully_consistent"]
            actions.append({
                "category": "local_seo",
                "priority": "medium",
                "action": f"{inconsistent} location(s) have inconsistent NAP citations — confirm remaining directory listings",
                "impact_estimate": "medium",
            })

        if metrics["optimization_pending_tasks"] > 0:
            actions.append({
                "category": "optimization",
                "priority": "medium",
                "action": f"Execute {metrics['optimization_pending_tasks']} pending title/meta/content optimization task(s)",
                "impact_estimate": "medium",
            })

        if metrics["topical_cluster_count"] == 0 and metrics["content_generated_count"] > 0:
            actions.append({
                "category": "content_structure",
                "priority": "low",
                "action": "No topical clusters defined yet — group existing content into pillar/cluster structure for internal linking",
                "impact_estimate": "low",
            })

        if metrics["calendar_upcoming_count"] == 0:
            actions.append({
                "category": "content_calendar",
                "priority": "low",
                "action": "No content scheduled in the next 14 days — generate a content calendar",
                "impact_estimate": "low",
            })

        actions.sort(key=lambda a: _PRIORITY_RANK.get(a["priority"], 99))
        return actions
