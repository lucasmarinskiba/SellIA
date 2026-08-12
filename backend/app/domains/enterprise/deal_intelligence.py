"""Deal Intelligence Manager - Core service for stakeholder mapping, probability prediction, deal health scoring."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.app.models.deal import Deal
from backend.app.models.deal_intelligence import (
    DealStakeholder,
    DealProbabilityScore,
    DealHealthSnapshot,
    DealHealthAlert,
    StakeholderEngagementEvent,
    ModelPredictionsCache,
)
from backend.app.domains.ml.deal_probability_model import DealProbabilityModel
from backend.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


class BuyerRole(str, Enum):
    """Role in buying process."""

    ECONOMIC_BUYER = "economic_buyer"
    USER_BUYER = "user_buyer"
    COACH = "coach"
    BLOCKER = "blocker"
    INFLUENCER = "influencer"


class HealthStatus(str, Enum):
    """Deal health status."""

    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    WON = "won"
    LOST = "lost"


@dataclass
class StakeholderProfile:
    """Buying committee member profile."""

    person_id: str
    email: str
    name: str
    title: str
    buyer_role: str
    influence_level: int
    engagement_score: float
    email_open_count: int
    meeting_count: int
    call_count: int
    last_activity: Optional[datetime]


@dataclass
class DealProbabilityResult:
    """Deal close probability prediction."""

    close_probability: float
    confidence_level: float
    probability_low: float
    probability_high: float
    features: Dict[str, Any]
    model_version: str


@dataclass
class DealHealthResult:
    """Real-time deal health assessment."""

    health_score: int
    health_status: str
    engagement_health: int
    momentum_health: int
    buyer_health: int
    competition_health: int
    risk_indicators: Dict[str, Any]
    recommended_actions: List[Dict[str, str]]


class DealIntelligenceManager:
    """Unified deal intelligence engine."""

    def __init__(self, db: Session):
        self.db = db
        self.ml_model = DealProbabilityModel()

    # ============================================================
    # STAKEHOLDER INTELLIGENCE
    # ============================================================

    def identify_stakeholders(self, deal_id: str) -> List[StakeholderProfile]:
        """Fetch stakeholders for a deal."""
        query = select(DealStakeholder).where(
            DealStakeholder.deal_id == deal_id
        ).order_by(DealStakeholder.influence_level.desc())

        stakeholders = self.db.execute(query).scalars().all()

        return [self._to_stakeholder_profile(s) for s in stakeholders]

    def find_economic_buyer(self, deal_id: str) -> Optional[StakeholderProfile]:
        """Identify economic buyer from buying committee."""
        # Priority: economic_buyer role > C-level + engagement > recent activity
        query = select(DealStakeholder).where(
            (DealStakeholder.deal_id == deal_id) &
            (DealStakeholder.status == "active")
        ).order_by(
            DealStakeholder.buyer_role.desc(),
            DealStakeholder.influence_level.desc(),
            DealStakeholder.engagement_score.desc()
        ).limit(1)

        stakeholder = self.db.execute(query).scalar()
        return self._to_stakeholder_profile(stakeholder) if stakeholder else None

    def add_stakeholder(
        self,
        deal_id: str,
        person_id: str,
        email: str,
        name: str,
        title: str,
        buyer_role: str = BuyerRole.INFLUENCER,
        influence_level: int = 5,
    ) -> StakeholderProfile:
        """Add stakeholder to buying committee."""
        stakeholder = DealStakeholder(
            deal_id=deal_id,
            person_id=person_id,
            email=email,
            name=name,
            title=title,
            buyer_role=buyer_role,
            influence_level=influence_level,
            engagement_score=0.0,
            status="active",
        )
        self.db.add(stakeholder)
        self.db.commit()

        logger.info(f"Added stakeholder {email} to deal {deal_id}")
        return self._to_stakeholder_profile(stakeholder)

    def update_stakeholder_engagement(
        self,
        deal_id: str,
        person_id: str,
        event_type: str,
        event_details: Dict[str, Any] = None,
    ):
        """Record engagement event and update stakeholder score."""
        # 1. Log engagement event
        engagement_value = self._get_engagement_points(event_type)
        event = StakeholderEngagementEvent(
            deal_id=deal_id,
            person_id=person_id,
            event_type=event_type,
            engagement_value=engagement_value,
            event_details=event_details or {},
        )
        self.db.add(event)

        # 2. Update stakeholder
        query = select(DealStakeholder).where(
            (DealStakeholder.deal_id == deal_id) &
            (DealStakeholder.person_id == person_id)
        )
        stakeholder = self.db.execute(query).scalar()

        if stakeholder:
            stakeholder.engagement_score = self._calculate_engagement_score(deal_id, person_id)

            if event_type == "email_open":
                stakeholder.last_email_open = datetime.utcnow()
                stakeholder.email_open_count = (stakeholder.email_open_count or 0) + 1
            elif event_type == "call":
                stakeholder.last_call_date = datetime.utcnow()
                stakeholder.meeting_count = (stakeholder.meeting_count or 0) + 1
            elif event_type == "meeting":
                stakeholder.meeting_count = (stakeholder.meeting_count or 0) + 1

            self.db.add(stakeholder)

        self.db.commit()

        # 3. Trigger deal health recalculation
        calculate_deal_health.delay(deal_id)

    def _get_engagement_points(self, event_type: str) -> int:
        """Points assigned per engagement event type."""
        points = {
            "email_send": 1,
            "email_open": 3,
            "email_click": 5,
            "call": 10,
            "meeting": 25,
            "proposal_view": 15,
            "demo_attended": 20,
            "contract_download": 30,
        }
        return points.get(event_type, 1)

    def _calculate_engagement_score(self, deal_id: str, person_id: str) -> float:
        """Calculate engagement score for stakeholder (0-100)."""
        # Recent activity (last 30 days) weighted more heavily
        recent_events = self.db.query(StakeholderEngagementEvent).filter(
            (StakeholderEngagementEvent.deal_id == deal_id) &
            (StakeholderEngagementEvent.person_id == person_id) &
            (StakeholderEngagementEvent.event_timestamp >= datetime.utcnow() - timedelta(days=30))
        ).all()

        recent_score = sum(e.engagement_value for e in recent_events) * 2

        # Historical activity (30-90 days)
        historical_events = self.db.query(StakeholderEngagementEvent).filter(
            (StakeholderEngagementEvent.deal_id == deal_id) &
            (StakeholderEngagementEvent.person_id == person_id) &
            (StakeholderEngagementEvent.event_timestamp >= datetime.utcnow() - timedelta(days=90)) &
            (StakeholderEngagementEvent.event_timestamp < datetime.utcnow() - timedelta(days=30))
        ).all()

        historical_score = sum(e.engagement_value for e in historical_events)

        # Normalize to 0-100 scale
        total_score = recent_score + historical_score
        engagement_score = min(total_score / 2, 100)

        return engagement_score

    def _to_stakeholder_profile(self, stakeholder: DealStakeholder) -> Optional[StakeholderProfile]:
        """Convert database model to profile dataclass."""
        if not stakeholder:
            return None

        return StakeholderProfile(
            person_id=stakeholder.person_id,
            email=stakeholder.email,
            name=stakeholder.name,
            title=stakeholder.title,
            buyer_role=stakeholder.buyer_role,
            influence_level=stakeholder.influence_level,
            engagement_score=stakeholder.engagement_score or 0.0,
            email_open_count=stakeholder.email_open_count or 0,
            meeting_count=stakeholder.meeting_count or 0,
            call_count=0,
            last_activity=stakeholder.last_email_open or stakeholder.last_call_date,
        )

    # ============================================================
    # DEAL PROBABILITY PREDICTION
    # ============================================================

    def predict_close_probability(self, deal_id: str) -> DealProbabilityResult:
        """Predict deal close probability using ML model."""
        # 1. Check cache
        cache = self.db.query(ModelPredictionsCache).filter(
            ModelPredictionsCache.deal_id == deal_id
        ).first()

        if cache and cache.cache_expires_at > datetime.utcnow():
            logger.info(f"Using cached prediction for deal {deal_id}")
            import json

            cached_data = json.loads(cache.prediction_json)
            return DealProbabilityResult(**cached_data)

        # 2. Fetch deal data
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")

        # 3. Extract features
        deal_data = self._prepare_deal_data(deal_id)

        # 4. Predict
        prob, confidence, prob_low, prob_high = self.ml_model.predict(deal_data)

        # 5. Store prediction
        result = DealProbabilityResult(
            close_probability=prob,
            confidence_level=confidence,
            probability_low=prob_low,
            probability_high=prob_high,
            features=deal_data,
            model_version=self.ml_model.model_version,
        )

        # 6. Save to database
        probability_score = DealProbabilityScore(
            deal_id=deal_id,
            close_probability=prob,
            confidence_level=confidence,
            probability_low=prob_low,
            probability_high=prob_high,
            features=deal_data,
            model_version=self.ml_model.model_version,
        )
        self.db.add(probability_score)

        # 7. Cache result
        import json

        cache = ModelPredictionsCache(
            deal_id=deal_id,
            prediction_json=json.dumps(
                {
                    "close_probability": prob,
                    "confidence_level": confidence,
                    "probability_low": prob_low,
                    "probability_high": prob_high,
                    "features": deal_data,
                    "model_version": self.ml_model.model_version,
                }
            ),
            cache_expires_at=datetime.utcnow() + timedelta(hours=6),
        )
        self.db.merge(cache)
        self.db.commit()

        logger.info(f"Predicted close probability for deal {deal_id}: {prob:.1f}%")
        return result

    def _prepare_deal_data(self, deal_id: str) -> Dict[str, Any]:
        """Prepare deal data for ML model."""
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        stakeholders = self.identify_stakeholders(deal_id)
        engagement_events = self.db.query(StakeholderEngagementEvent).filter(
            StakeholderEngagementEvent.deal_id == deal_id
        ).all()

        return {
            "created_at": deal.created_at if deal else datetime.utcnow(),
            "stage_entered_at": deal.stage_entered_at if deal else datetime.utcnow(),
            "value": deal.amount if deal else 50000,
            "stakeholders": [
                {
                    "buyer_role": s.buyer_role,
                    "engagement_score": s.engagement_score,
                }
                for s in stakeholders
            ],
            "engagement_events": [
                {
                    "event_type": e.event_type,
                    "timestamp": e.event_timestamp.isoformat(),
                }
                for e in engagement_events
            ],
            "proposal_sent_at": deal.proposal_sent_at.isoformat() if deal and deal.proposal_sent_at else None,
            "budget_confirmed": getattr(deal, "budget_confirmed", False) if deal else False,
            "timeline_confirmed": getattr(deal, "timeline_confirmed", False) if deal else False,
            "competitor_mentions": [],
            "avg_buyer_response_time_hours": 48,
        }

    # ============================================================
    # DEAL HEALTH SCORING
    # ============================================================

    def calculate_deal_health(self, deal_id: str) -> DealHealthResult:
        """Calculate real-time deal health score."""
        stakeholders = self.identify_stakeholders(deal_id)
        engagement_events = self.db.query(StakeholderEngagementEvent).filter(
            StakeholderEngagementEvent.deal_id == deal_id
        ).all()

        # Calculate component scores
        engagement_health = self._calculate_engagement_health(stakeholders, engagement_events)
        momentum_health = self._calculate_momentum_health(engagement_events)
        buyer_health = self._calculate_buyer_health(stakeholders)
        competition_health = self._calculate_competition_health(deal_id)

        # Weighted average
        health_score = int(
            (engagement_health * 0.3) +
            (momentum_health * 0.3) +
            (buyer_health * 0.25) +
            (competition_health * 0.15)
        )

        # Determine status
        if health_score >= 70:
            health_status = HealthStatus.HEALTHY
        elif health_score >= 50:
            health_status = HealthStatus.AT_RISK
        else:
            health_status = HealthStatus.CRITICAL

        # Recommended actions
        recommended_actions = self._generate_recommendations(
            health_score, engagement_health, momentum_health, buyer_health, competition_health
        )

        result = DealHealthResult(
            health_score=health_score,
            health_status=health_status.value,
            engagement_health=engagement_health,
            momentum_health=momentum_health,
            buyer_health=buyer_health,
            competition_health=competition_health,
            risk_indicators={
                "days_since_activity": self._days_since_last_activity(engagement_events),
                "stakeholder_churn": len([s for s in stakeholders if s.engagement_score < 20]),
                "economic_buyer_engaged": buyer_health >= 70,
            },
            recommended_actions=recommended_actions,
        )

        # Save to database
        health_snapshot = DealHealthSnapshot(
            deal_id=deal_id,
            health_score=health_score,
            health_status=health_status.value,
            engagement_health=engagement_health,
            momentum_health=momentum_health,
            buyer_health=buyer_health,
            competition_health=competition_health,
            recommended_actions=recommended_actions,
        )
        self.db.add(health_snapshot)

        # Create alerts if status changed
        self._create_health_alerts(deal_id, health_status, recommended_actions)

        self.db.commit()

        logger.info(f"Calculated health for deal {deal_id}: {health_score}/100 ({health_status.value})")
        return result

    def _calculate_engagement_health(
        self, stakeholders: List[StakeholderProfile], events: List[StakeholderEngagementEvent]
    ) -> int:
        """Engagement health score (0-100)."""
        if not stakeholders:
            return 0

        avg_engagement = sum(s.engagement_score for s in stakeholders) / len(stakeholders)
        recent_events = len([e for e in events if (datetime.utcnow() - e.event_timestamp).days <= 7])

        engagement_score = (avg_engagement * 0.6) + (min(recent_events * 10, 40) * 0.4)
        return int(min(engagement_score, 100))

    def _calculate_momentum_health(self, events: List[StakeholderEngagementEvent]) -> int:
        """Momentum health score (0-100)."""
        now = datetime.utcnow()

        events_7d = len([e for e in events if (now - e.event_timestamp).days <= 7])
        events_14d = len([e for e in events if (now - e.event_timestamp).days <= 14])
        events_30d = len([e for e in events if (now - e.event_timestamp).days <= 30])

        # Positive momentum if increasing activity
        momentum = 0
        if events_7d > 0:
            momentum += 30
        if events_7d > events_14d * 0.4:
            momentum += 40
        if events_30d > events_14d * 1.5:
            momentum += 30

        return min(momentum, 100)

    def _calculate_buyer_health(self, stakeholders: List[StakeholderProfile]) -> int:
        """Buyer involvement health score (0-100)."""
        economic_buyer = next((s for s in stakeholders if s.buyer_role == BuyerRole.ECONOMIC_BUYER), None)

        if not economic_buyer:
            return 30  # No economic buyer identified

        if economic_buyer.engagement_score >= 70:
            return 100
        elif economic_buyer.engagement_score >= 50:
            return 75
        elif economic_buyer.engagement_score >= 30:
            return 50
        else:
            return 25

    def _calculate_competition_health(self, deal_id: str) -> int:
        """Competition threat health score (0-100)."""
        # TODO: Integrate with competitor detection
        return 75  # Placeholder

    def _days_since_last_activity(self, events: List[StakeholderEngagementEvent]) -> int:
        """Days since last engagement event."""
        if not events:
            return 999

        last_event = max(events, key=lambda e: e.event_timestamp)
        return (datetime.utcnow() - last_event.event_timestamp).days

    def _generate_recommendations(
        self,
        health_score: int,
        engagement_health: int,
        momentum_health: int,
        buyer_health: int,
        competition_health: int,
    ) -> List[Dict[str, str]]:
        """Generate recommended actions based on health components."""
        actions = []

        if buyer_health < 50:
            actions.append({
                "action": "Call economic buyer",
                "priority": "high",
                "description": "Economic buyer engagement is low. Schedule call to understand concerns.",
            })

        if momentum_health < 40:
            actions.append({
                "action": "Increase touchpoints",
                "priority": "high",
                "description": "Deal momentum declining. Schedule meeting or send proposal update.",
            })

        if engagement_health < 30:
            actions.append({
                "action": "Stakeholder mapping",
                "priority": "medium",
                "description": "Add more stakeholders to buying committee.",
            })

        if competition_health < 50:
            actions.append({
                "action": "Competitive response",
                "priority": "high",
                "description": "Competition detected. Prepare differentiation messaging.",
            })

        return actions[:3]  # Top 3 recommendations

    def _create_health_alerts(
        self, deal_id: str, health_status: HealthStatus, recommended_actions: List[Dict[str, str]]
    ):
        """Create deal health alerts if status is concerning."""
        if health_status in [HealthStatus.CRITICAL, HealthStatus.AT_RISK]:
            alert = DealHealthAlert(
                deal_id=deal_id,
                user_id=None,  # TODO: Get deal owner
                alert_type="health_status_change",
                severity="critical" if health_status == HealthStatus.CRITICAL else "warning",
                title=f"Deal health: {health_status.value}",
                description=f"Deal health has changed to {health_status.value}",
                recommended_action=recommended_actions[0]["action"] if recommended_actions else None,
                action_type="meeting" if "Call" in str(recommended_actions) else "email",
            )
            self.db.add(alert)


# ============================================================
# CELERY BACKGROUND TASKS
# ============================================================


@celery_app.task(bind=True, max_retries=3)
def calculate_deal_health(self, deal_id: str):
    """Background task to calculate deal health."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        manager = DealIntelligenceManager(db)
        manager.calculate_deal_health(deal_id)
        db.close()

        logger.info(f"Health calculation complete for deal {deal_id}")
        return {"status": "complete", "deal_id": deal_id}

    except Exception as exc:
        logger.error(f"Error calculating health for deal {deal_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def predict_deal_probability(self, deal_id: str):
    """Background task to predict deal close probability."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        manager = DealIntelligenceManager(db)
        result = manager.predict_close_probability(deal_id)
        db.close()

        logger.info(f"Probability prediction complete for deal {deal_id}: {result.close_probability:.1f}%")
        return {
            "status": "complete",
            "deal_id": deal_id,
            "probability": result.close_probability,
        }

    except Exception as exc:
        logger.error(f"Error predicting probability for deal {deal_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def train_probability_model(self, training_data_ids: List[str]):
    """Background task to retrain ML model on historical deals."""
    try:
        from backend.app.database import SessionLocal

        logger.info(f"Starting model training on {len(training_data_ids)} deals...")

        db = SessionLocal()
        manager = DealIntelligenceManager(db)

        # TODO: Fetch deal data from database, extract features, train
        # model_metrics = manager.ml_model.train(training_data, training_labels)

        db.close()

        logger.info("Model training complete")
        return {"status": "complete", "deals_trained": len(training_data_ids)}

    except Exception as exc:
        logger.error(f"Error training model: {exc}")
        raise self.retry(exc=exc, countdown=300)
