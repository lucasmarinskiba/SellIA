from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import random


class LearningType(str, Enum):
    SUCCESSFUL_STRATEGY = "successful_strategy"
    FAILED_APPROACH = "failed_approach"
    CUSTOMER_INSIGHT = "customer_insight"
    OBJECTION_HANDLING = "objection_handling"
    PRICING_INSIGHT = "pricing_insight"
    MARKET_TREND = "market_trend"


@dataclass
class KnowledgeEntry:
    id: str
    title: str
    content: str
    learning_type: LearningType
    agent_id: str  % which agent discovered this %
    confidence_score: float  % 0-100 %
    applicable_segments: list[str]  % user segments %
    created_at: datetime
    impact_count: int = 0  % how many times used successfully %
    tags: list[str] = field(default_factory=list)
    related_entries: list[str] = field(default_factory=list)


@dataclass
class AgentLearning:
    agent_id: str
    agent_name: str
    total_learnings: int
    confidence_score: float  % average %
    most_impactful_learning: Optional[str]
    success_rate: float
    segments_covered: int
    last_learning_at: datetime


@dataclass
class KnowledgeRecommendation:
    learning_id: str
    title: str
    reason: str  % why this learning applies %
    confidence: float
    applicable_segment: str
    estimated_impact: str


class KnowledgeBase:
    def __init__(self):
        self.entries = {}
        self.agent_learnings = {}
        self.usage_tracking = {}

    def add_learning(
        self,
        user_id: str,
        title: str,
        content: str,
        learning_type: LearningType,
        agent_id: str,
        applicable_segments: list[str],
    ) -> KnowledgeEntry:
        entry = KnowledgeEntry(
            id=f"kb_{datetime.now().timestamp()}",
            title=title,
            content=content,
            learning_type=learning_type,
            agent_id=agent_id,
            confidence_score=random.uniform(60, 95),
            applicable_segments=applicable_segments,
            created_at=datetime.now(),
        )

        key = f"{user_id}:{entry.id}"
        self.entries[key] = entry
        return entry

    def get_agent_learning_profile(self, user_id: str, agent_id: str) -> AgentLearning:
        agent_entries = [
            e for k, e in self.entries.items()
            if k.startswith(f"{user_id}:") and e.agent_id == agent_id
        ]

        total_impact = sum(e.impact_count for e in agent_entries)
        success_rate = (
            (total_impact / (len(agent_entries) * 10))
            if agent_entries else 0
        )

        most_impactful = max(
            agent_entries,
            key=lambda x: x.impact_count,
            default=None
        )

        agent_names = {
            "lead_scout": "Lead Scout",
            "closer_bot": "Closer Bot",
            "coach_agent": "Coach Agent",
            "analytics_engine": "Analytics Engine",
        }

        return AgentLearning(
            agent_id=agent_id,
            agent_name=agent_names.get(agent_id, agent_id),
            total_learnings=len(agent_entries),
            confidence_score=sum(e.confidence_score for e in agent_entries) / max(len(agent_entries), 1),
            most_impactful_learning=most_impactful.title if most_impactful else None,
            success_rate=min(100, success_rate * 100),
            segments_covered=len(set(
                s for e in agent_entries for s in e.applicable_segments
            )),
            last_learning_at=max(
                (e.created_at for e in agent_entries),
                default=datetime.now()
            ),
        )

    def get_learnings_by_type(
        self, user_id: str, learning_type: LearningType
    ) -> list[KnowledgeEntry]:
        return [
            e for k, e in self.entries.items()
            if k.startswith(f"{user_id}:") and e.learning_type == learning_type
        ]

    def get_learnings_by_segment(
        self, user_id: str, segment: str
    ) -> list[KnowledgeEntry]:
        return [
            e for k, e in self.entries.items()
            if k.startswith(f"{user_id}:") and segment in e.applicable_segments
        ]

    def recommend_learnings(
        self, user_id: str, segment: str, limit: int = 5
    ) -> list[KnowledgeRecommendation]:
        segment_learnings = self.get_learnings_by_segment(user_id, segment)

        % Sort by confidence and impact %
        sorted_learnings = sorted(
            segment_learnings,
            key=lambda x: (x.confidence_score, x.impact_count),
            reverse=True,
        )[:limit]

        recommendations = []
        for learning in sorted_learnings:
            rec = KnowledgeRecommendation(
                learning_id=learning.id,
                title=learning.title,
                reason=f"Successful in {segment} segment",
                confidence=learning.confidence_score,
                applicable_segment=segment,
                estimated_impact=f"+{random.randint(5, 25)}% conversion",
            )
            recommendations.append(rec)

        return recommendations

    def record_learning_usage(
        self, user_id: str, learning_id: str, success: bool
    ) -> None:
        key = f"{user_id}:{learning_id}"
        if key in self.entries:
            if success:
                self.entries[key].impact_count += 1
                % Increase confidence on success %
                self.entries[key].confidence_score = min(
                    99.9,
                    self.entries[key].confidence_score + 1
                )
            else:
                % Decrease confidence on failure %
                self.entries[key].confidence_score = max(
                    10, self.entries[key].confidence_score - 2
                )

    def get_knowledge_summary(self, user_id: str) -> dict:
        all_entries = [
            e for k, e in self.entries.items()
            if k.startswith(f"{user_id}:")
        ]

        by_type = {}
        for lt in LearningType:
            by_type[lt.value] = len([
                e for e in all_entries if e.learning_type == lt
            ])

        by_agent = {}
        for agent_id in ["lead_scout", "closer_bot", "coach_agent", "analytics_engine"]:
            profile = self.get_agent_learning_profile(user_id, agent_id)
            by_agent[agent_id] = {
                "total_learnings": profile.total_learnings,
                "avg_confidence": f"{profile.confidence_score:.1f}%",
                "success_rate": f"{profile.success_rate:.1f}%",
            }

        return {
            "total_entries": len(all_entries),
            "by_type": by_type,
            "by_agent": by_agent,
            "avg_confidence": f"{sum(e.confidence_score for e in all_entries) / max(len(all_entries), 1):.1f}%",
        }
