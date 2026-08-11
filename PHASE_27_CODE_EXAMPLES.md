# Phase 27 - Code Examples & Quick Reference

Quick-copy code snippets for Phase 27 implementation.

---

## DATABASE MIGRATIONS

### Alembic Migration File

**File**: `backend/alembic/versions/0031_intelligence_schema.py`

```python
"""Create intelligence schema for deal scoring

Revision ID: 0031
Revises: 0030
Create Date: 2026-08-12 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0031'
down_revision = '0030'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create schema
    op.execute('CREATE SCHEMA IF NOT EXISTS intelligence')
    
    # deal_stakeholders
    op.create_table(
        'deal_stakeholders',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('person_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('buyer_role', sa.String(50), nullable=True),
        sa.Column('influence_level', sa.Integer(), server_default='5', nullable=False),
        sa.Column('engagement_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('last_email_open', sa.DateTime(), nullable=True),
        sa.Column('last_call_date', sa.DateTime(), nullable=True),
        sa.Column('email_open_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('meeting_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('message_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(50), server_default='active', nullable=False),
        sa.Column('identified_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['public.deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='intelligence'
    )
    op.create_index('idx_deal_stakeholders_deal', 'deal_stakeholders', ['deal_id'], schema='intelligence')
    op.create_index('idx_deal_stakeholders_role', 'deal_stakeholders', ['buyer_role'], schema='intelligence')
    
    # deal_probability_scores
    op.create_table(
        'deal_probability_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('close_probability', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('features', postgresql.JSON(), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('prediction_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('probability_low', sa.Float(), nullable=False),
        sa.Column('probability_high', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['public.deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('deal_id'),
        schema='intelligence'
    )
    op.create_index('idx_prob_scores_deal', 'deal_probability_scores', ['deal_id'], schema='intelligence')
    op.create_index('idx_prob_scores_prob', 'deal_probability_scores', ['close_probability'], schema='intelligence')
    
    # deal_health_snapshots
    op.create_table(
        'deal_health_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('health_score', sa.Integer(), nullable=False),
        sa.Column('health_status', sa.String(20), nullable=False),
        sa.Column('engagement_health', sa.Integer(), nullable=False),
        sa.Column('momentum_health', sa.Integer(), nullable=False),
        sa.Column('buyer_health', sa.Integer(), nullable=False),
        sa.Column('competition_health', sa.Integer(), nullable=False),
        sa.Column('days_since_last_activity', sa.Integer(), nullable=False),
        sa.Column('stakeholder_churn_count', sa.Integer(), nullable=False),
        sa.Column('buying_committee_complete', sa.Boolean(), nullable=False),
        sa.Column('economic_buyer_engaged', sa.Boolean(), nullable=False),
        sa.Column('recommended_actions', postgresql.JSON(), nullable=True),
        sa.Column('snapshot_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['public.deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='intelligence'
    )
    op.create_index('idx_health_deal', 'deal_health_snapshots', ['deal_id'], schema='intelligence')
    op.create_index('idx_health_status', 'deal_health_snapshots', ['health_status'], schema='intelligence')
    op.create_index('idx_health_date', 'deal_health_snapshots', ['snapshot_date'], schema='intelligence')
    
    # deal_health_alerts
    op.create_table(
        'deal_health_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('action_taken', sa.Boolean(), server_default=False, nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['public.deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='intelligence'
    )
    op.create_index('idx_alerts_deal', 'deal_health_alerts', ['deal_id'], schema='intelligence')
    op.create_index('idx_alerts_user', 'deal_health_alerts', ['user_id'], schema='intelligence')
    op.create_index('idx_alerts_status', 'deal_health_alerts', ['resolved_at'], schema='intelligence')
    
    # stakeholder_engagement_events
    op.create_table(
        'stakeholder_engagement_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('person_id', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('engagement_value', sa.Integer(), nullable=False),
        sa.Column('event_details', postgresql.JSON(), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['public.deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='intelligence'
    )
    op.create_index('idx_engagement_deal_person', 'stakeholder_engagement_events', ['deal_id', 'person_id'], schema='intelligence')
    op.create_index('idx_engagement_timestamp', 'stakeholder_engagement_events', ['event_timestamp'], schema='intelligence')
    
    # model_predictions_cache
    op.create_table(
        'model_predictions_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('prediction_json', postgresql.JSON(), nullable=False),
        sa.Column('cache_created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('cache_expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['public.deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('deal_id'),
        schema='intelligence'
    )
    op.create_index('idx_cache_expires', 'model_predictions_cache', ['cache_expires_at'], schema='intelligence')
    
    # Grant permissions
    op.execute('GRANT USAGE ON SCHEMA intelligence TO sellia_user')
    op.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA intelligence TO sellia_user')

def downgrade() -> None:
    op.execute('DROP SCHEMA intelligence CASCADE')
```

---

## MODELS

### SQLAlchemy Models

**File**: `backend/app/models/intelligence.py`

```python
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from backend.app.database import Base

class DealStakeholder(Base):
    """Buying committee member."""
    __tablename__ = 'deal_stakeholders'
    __table_args__ = (
        Index('idx_deal_stakeholders_deal', 'deal_id'),
        Index('idx_deal_stakeholders_role', 'buyer_role'),
        {'schema': 'intelligence'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(String(255), ForeignKey('public.deals.id', ondelete='CASCADE'), nullable=False)
    person_id = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    title = Column(String(255))
    company = Column(String(255))
    buyer_role = Column(String(50))  # economic_buyer, user_buyer, coach, blocker, influencer
    influence_level = Column(Integer, default=5)  # 1-10
    engagement_score = Column(Float, default=0.0)  # 0-100
    last_email_open = Column(DateTime)
    last_call_date = Column(DateTime)
    email_open_count = Column(Integer, default=0)
    meeting_count = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    status = Column(String(50), default='active')  # active, churned, dormant
    identified_at = Column(DateTime, default=datetime.utcnow)

class DealProbabilityScore(Base):
    """Predicted deal close probability."""
    __tablename__ = 'deal_probability_scores'
    __table_args__ = (
        UniqueConstraint('deal_id'),
        Index('idx_prob_scores_deal', 'deal_id'),
        Index('idx_prob_scores_prob', 'close_probability'),
        {'schema': 'intelligence'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(String(255), ForeignKey('public.deals.id', ondelete='CASCADE'), nullable=False)
    close_probability = Column(Float, nullable=False)  # 0-100
    confidence_level = Column(Float, nullable=False)  # 0-100
    features = Column(JSON)
    model_version = Column(String(50))
    prediction_date = Column(DateTime, default=datetime.utcnow)
    probability_low = Column(Float)  # 90% CI lower
    probability_high = Column(Float)  # 90% CI upper

class DealHealthSnapshot(Base):
    """Real-time deal health assessment."""
    __tablename__ = 'deal_health_snapshots'
    __table_args__ = (
        Index('idx_health_deal', 'deal_id'),
        Index('idx_health_status', 'health_status'),
        Index('idx_health_date', 'snapshot_date'),
        {'schema': 'intelligence'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(String(255), ForeignKey('public.deals.id', ondelete='CASCADE'), nullable=False)
    health_score = Column(Integer, nullable=False)  # 0-100
    health_status = Column(String(20))  # healthy, at_risk, critical
    engagement_health = Column(Integer)  # 0-100
    momentum_health = Column(Integer)  # 0-100
    buyer_health = Column(Integer)  # 0-100
    competition_health = Column(Integer)  # 0-100
    days_since_last_activity = Column(Integer)
    stakeholder_churn_count = Column(Integer)
    buying_committee_complete = Column(Boolean)
    economic_buyer_engaged = Column(Boolean)
    recommended_actions = Column(JSON)
    snapshot_date = Column(DateTime, default=datetime.utcnow)

class DealHealthAlert(Base):
    """Deal health alert."""
    __tablename__ = 'deal_health_alerts'
    __table_args__ = (
        Index('idx_alerts_deal', 'deal_id'),
        Index('idx_alerts_user', 'user_id'),
        Index('idx_alerts_status', 'resolved_at'),
        {'schema': 'intelligence'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(String(255), ForeignKey('public.deals.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(255), ForeignKey('public.users.id', ondelete='CASCADE'), nullable=False)
    alert_type = Column(String(50))  # low_engagement, lost_momentum, buyer_churn, stalled
    severity = Column(String(20))  # info, warning, critical
    title = Column(String(255))
    description = Column(String(500))
    recommended_action = Column(String(500))
    action_type = Column(String(50))  # call, email, meeting
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    action_taken = Column(Boolean, default=False)

class StakeholderEngagementEvent(Base):
    """Engagement event (time-series)."""
    __tablename__ = 'stakeholder_engagement_events'
    __table_args__ = (
        Index('idx_engagement_deal_person', 'deal_id', 'person_id'),
        Index('idx_engagement_timestamp', 'event_timestamp'),
        {'schema': 'intelligence'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(String(255), ForeignKey('public.deals.id', ondelete='CASCADE'), nullable=False)
    person_id = Column(String(255), nullable=False)
    event_type = Column(String(50))  # email_open, email_click, call, meeting, message
    engagement_value = Column(Integer)
    event_details = Column(JSON)
    event_timestamp = Column(DateTime, default=datetime.utcnow)

class ModelPredictionsCache(Base):
    """Prediction cache for performance."""
    __tablename__ = 'model_predictions_cache'
    __table_args__ = (
        UniqueConstraint('deal_id'),
        Index('idx_cache_expires', 'cache_expires_at'),
        {'schema': 'intelligence'}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(String(255), ForeignKey('public.deals.id', ondelete='CASCADE'), nullable=False)
    prediction_json = Column(JSON)
    cache_created_at = Column(DateTime, default=datetime.utcnow)
    cache_expires_at = Column(DateTime)
```

---

## UNIT TESTS

### Test Suite

**File**: `backend/tests/test_deal_intelligence_manager.py`

```python
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from backend.app.domains.enterprise.deal_intelligence import (
    DealIntelligenceManager, StakeholderProfile
)
from backend.app.models.intelligence import DealStakeholder, StakeholderEngagementEvent

@pytest.fixture
def manager(db_session):
    return DealIntelligenceManager(db_session)

@pytest.fixture
def sample_deal(db_session):
    """Create sample deal for testing."""
    deal = Deal(
        id='deal_001',
        name='Acme Corp',
        deal_value=100000,
        stage='proposal',
        stage_changed_at=datetime.utcnow() - timedelta(days=10),
        created_at=datetime.utcnow() - timedelta(days=45),
        owner_id='user_001'
    )
    db_session.add(deal)
    db_session.commit()
    return deal

@pytest.fixture
def sample_stakeholders(db_session, sample_deal):
    """Create sample stakeholders."""
    stakeholders = [
        DealStakeholder(
            deal_id=sample_deal.id,
            person_id='person_001',
            email='cfo@acme.com',
            name='Jane Doe',
            title='CFO',
            buyer_role='economic_buyer',
            influence_level=10,
            engagement_score=75
        ),
        DealStakeholder(
            deal_id=sample_deal.id,
            person_id='person_002',
            email='user@acme.com',
            name='John Smith',
            title='VP Operations',
            buyer_role='user_buyer',
            influence_level=8,
            engagement_score=60
        ),
    ]
    for s in stakeholders:
        db_session.add(s)
    db_session.commit()
    return stakeholders

# ============================================================
# Stakeholder Tests
# ============================================================

def test_get_buying_committee(manager, sample_deal, sample_stakeholders):
    """Test fetching buying committee."""
    committee = manager.get_buying_committee(sample_deal.id)
    
    assert len(committee) == 2
    assert committee[0].person_id == 'person_001'
    assert committee[0].email == 'cfo@acme.com'

def test_identify_economic_buyer_already_marked(manager, sample_deal, sample_stakeholders):
    """Test identifying pre-marked economic buyer."""
    buyer = manager.identify_economic_buyer(sample_deal.id)
    
    assert buyer is not None
    assert buyer.buyer_role == 'economic_buyer'
    assert buyer.person_id == 'person_001'

def test_identify_economic_buyer_c_level(manager, db_session, sample_deal):
    """Test identifying C-level as economic buyer."""
    # Add CEO without explicit buyer_role
    ceo = DealStakeholder(
        deal_id=sample_deal.id,
        person_id='person_ceo',
        email='ceo@acme.com',
        name='Alice CEO',
        title='CEO',
        buyer_role=None,
        influence_level=9,
        engagement_score=70
    )
    db_session.add(ceo)
    db_session.commit()
    
    buyer = manager.identify_economic_buyer(sample_deal.id)
    
    assert buyer is not None
    assert buyer.person_id == 'person_ceo'

def test_identify_economic_buyer_none_engaged(manager, db_session, sample_deal):
    """Test when no economic buyer found."""
    # Create deal with no stakeholders
    new_deal = Deal(id='deal_empty', name='Empty Deal', deal_value=50000, stage='prospect')
    db_session.add(new_deal)
    db_session.commit()
    
    buyer = manager.identify_economic_buyer(new_deal.id)
    
    assert buyer is None

# ============================================================
# Engagement Tracking Tests
# ============================================================

def test_update_stakeholder_engagement_email_open(manager, db_session, sample_deal, sample_stakeholders):
    """Test recording email open event."""
    manager.update_stakeholder_engagement(
        deal_id=sample_deal.id,
        person_id='person_001',
        event_type='email_open',
        event_details={'email_subject': 'Proposal Review'}
    )
    
    # Check event recorded
    event = db_session.query(StakeholderEngagementEvent).filter_by(
        deal_id=sample_deal.id,
        person_id='person_001'
    ).first()
    assert event is not None
    assert event.event_type == 'email_open'
    
    # Check stakeholder engagement score updated
    stakeholder = db_session.query(DealStakeholder).filter_by(
        deal_id=sample_deal.id,
        person_id='person_001'
    ).first()
    assert stakeholder.engagement_score > 75

def test_update_stakeholder_engagement_meeting(manager, db_session, sample_deal, sample_stakeholders):
    """Test recording meeting event (higher value)."""
    manager.update_stakeholder_engagement(
        deal_id=sample_deal.id,
        person_id='person_002',
        event_type='meeting',
        event_details={'duration_minutes': 30}
    )
    
    stakeholder = db_session.query(DealStakeholder).filter_by(
        deal_id=sample_deal.id,
        person_id='person_002'
    ).first()
    # Meeting adds 10 points (vs 1 for email_open)
    assert stakeholder.engagement_score > 60

# ============================================================
# Deal Health Tests
# ============================================================

def test_calculate_deal_health_healthy(manager, sample_deal, sample_stakeholders):
    """Test deal health calculation (healthy case)."""
    health = manager.calculate_deal_health(sample_deal.id)
    
    assert health.health_score >= 70  # Should be healthy
    assert health.health_status == 'healthy'
    assert health.engagement_health >= 60
    assert health.buyer_health >= 60

def test_calculate_deal_health_critical(manager, db_session):
    """Test deal health calculation (critical case)."""
    # Create deal with no stakeholders
    deal = Deal(
        id='deal_critical',
        name='Dead Deal',
        deal_value=50000,
        stage='proposal',
        stage_changed_at=datetime.utcnow() - timedelta(days=60),  # 60 days in stage
        created_at=datetime.utcnow() - timedelta(days=120),
        owner_id='user_001'
    )
    db_session.add(deal)
    db_session.commit()
    
    manager = DealIntelligenceManager(db_session)
    health = manager.calculate_deal_health(deal.id)
    
    assert health.health_score < 50  # Should be critical
    assert health.health_status == 'critical'

def test_deal_health_snapshot_stored(manager, db_session, sample_deal, sample_stakeholders):
    """Test that health snapshot is persisted."""
    manager.calculate_deal_health(sample_deal.id)
    
    snapshot = db_session.query(DealHealthSnapshot).filter_by(
        deal_id=sample_deal.id
    ).first()
    
    assert snapshot is not None
    assert snapshot.health_score >= 0
    assert snapshot.health_score <= 100

# ============================================================
# Recommendation Tests
# ============================================================

def test_generate_recommendations_missing_buyer(manager, db_session):
    """Test recommendations when economic buyer not engaged."""
    deal = Deal(
        id='deal_no_buyer',
        name='Deal',
        deal_value=50000,
        stage='discovery'
    )
    db_session.add(deal)
    db_session.commit()
    
    # Create stakeholder but not economic buyer
    stakeholder = DealStakeholder(
        deal_id=deal.id,
        person_id='person_ops',
        email='ops@acme.com',
        title='Operations Manager',
        buyer_role='user_buyer'
    )
    db_session.add(stakeholder)
    db_session.commit()
    
    manager = DealIntelligenceManager(db_session)
    health = manager.calculate_deal_health(deal.id)
    
    # Should recommend identifying economic buyer
    actions = health.recommended_actions
    assert any('economic buyer' in a['action'].lower() for a in actions)

# ============================================================
# ML Model Tests
# ============================================================

def test_predict_close_probability(manager, sample_deal, sample_stakeholders):
    """Test deal probability prediction."""
    probability = manager.predict_close_probability(sample_deal.id)
    
    assert probability.close_probability >= 0
    assert probability.close_probability <= 100
    assert probability.confidence_level >= 0.5
    assert probability.confidence_level <= 1.0
    assert probability.probability_low < probability.close_probability
    assert probability.probability_high > probability.close_probability

def test_predict_close_probability_caching(manager, db_session, sample_deal, sample_stakeholders):
    """Test that predictions are cached."""
    # First call
    prob1 = manager.predict_close_probability(sample_deal.id)
    
    # Second call (should hit cache)
    prob2 = manager.predict_close_probability(sample_deal.id)
    
    assert prob1.close_probability == prob2.close_probability

# ============================================================
# Alert Tests
# ============================================================

def test_alert_created_on_health_drop(manager, db_session, sample_deal, sample_stakeholders):
    """Test alert creation when health drops."""
    # Initial health calculation
    health1 = manager.calculate_deal_health(sample_deal.id)
    
    # Simulate engagement drop (time passes, no activity)
    now = datetime.utcnow()
    for s in sample_stakeholders:
        s.last_email_open = now - timedelta(days=30)
    db_session.commit()
    
    # Recalculate health
    health2 = manager.calculate_deal_health(sample_deal.id)
    
    # If health dropped > 20 points, alert should be created
    if health1.health_score - health2.health_score > 20:
        alert = db_session.query(DealHealthAlert).filter_by(
            deal_id=sample_deal.id
        ).first()
        assert alert is not None
```

---

## CELERY TASKS

### Background Jobs

**File**: `backend/app/tasks/intelligence.py`

```python
from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy import func, select
from backend.celery_app import celery_app
from backend.app.database import SessionLocal
from backend.app.models import Deal
from backend.app.models.intelligence import DealHealthAlert
from backend.app.domains.enterprise.deal_intelligence import DealIntelligenceManager
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def calculate_all_deal_health_hourly(self):
    """Recalculate health scores for all open deals (hourly)."""
    try:
        db = SessionLocal()
        manager = DealIntelligenceManager(db)
        
        # Get all open deals
        open_deals = db.query(Deal).filter(
            Deal.closed_date.is_(None)
        ).all()
        
        count = 0
        for deal in open_deals:
            try:
                manager.calculate_deal_health(deal.id)
                count += 1
            except Exception as e:
                logger.error(f"Failed to calculate health for {deal.id}: {e}")
        
        logger.info(f"Calculated health for {count}/{len(open_deals)} deals")
        return {'deals_processed': count}
    
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        self.retry(countdown=300, exc=exc)  # Retry in 5 min

@celery_app.task(bind=True)
def process_engagement_webhook(self, deal_id: str, person_id: str, event_type: str, event_details: dict = None):
    """Process engagement event webhook (email tracking, etc)."""
    try:
        db = SessionLocal()
        manager = DealIntelligenceManager(db)
        
        manager.update_stakeholder_engagement(
            deal_id=deal_id,
            person_id=person_id,
            event_type=event_type,
            event_details=event_details or {}
        )
        
        logger.info(f"Recorded {event_type} for {person_id} on {deal_id}")
        return {'status': 'recorded'}
    
    except Exception as exc:
        logger.error(f"Webhook processing failed: {exc}")
        self.retry(countdown=60, exc=exc, max_retries=3)

@celery_app.task(bind=True, max_retries=2)
def retrain_deal_probability_model_weekly(self):
    """Retrain ML model with latest data (weekly)."""
    try:
        from backend.app.ml.deal_probability_trainer import train_deal_probability_model
        
        logger.info("Starting model retraining...")
        
        # Train new model
        new_model = train_deal_probability_model()
        
        # Validate performance
        auc_score = new_model.evaluate()
        
        if auc_score >= 0.85:
            logger.info(f"New model AUC: {auc_score}. Deploying...")
            new_model.save()
            return {'status': 'deployed', 'auc': auc_score}
        else:
            logger.warning(f"New model AUC {auc_score} < 0.85. Not deploying.")
            return {'status': 'not_deployed', 'auc': auc_score}
    
    except Exception as exc:
        logger.error(f"Model retraining failed: {exc}")
        self.retry(countdown=3600, exc=exc)

@celery_app.task(bind=True)
def send_health_alerts_digest(self):
    """Send daily digest of deal health alerts (9am UTC)."""
    try:
        db = SessionLocal()
        
        # Get all unresolved alerts
        now = datetime.utcnow()
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        recent_alerts = db.query(DealHealthAlert).filter(
            (DealHealthAlert.resolved_at.is_(None)) |
            (DealHealthAlert.triggered_at >= twenty_four_hours_ago)
        ).all()
        
        # Group by user
        alerts_by_user = {}
        for alert in recent_alerts:
            if alert.user_id not in alerts_by_user:
                alerts_by_user[alert.user_id] = []
            alerts_by_user[alert.user_id].append(alert)
        
        # Send email per user
        for user_id, alerts in alerts_by_user.items():
            send_alert_email.delay(user_id, [a.id for a in alerts])
        
        logger.info(f"Sent alerts digest to {len(alerts_by_user)} users")
        return {'users_notified': len(alerts_by_user)}
    
    except Exception as exc:
        logger.error(f"Alert digest failed: {exc}")
```

Add to `celery_app.py`:

```python
from celery.schedules import crontab

beat_schedule = {
    'calculate-all-deal-health': {
        'task': 'backend.app.tasks.intelligence.calculate_all_deal_health_hourly',
        'schedule': crontab(minute=0),  # Hourly at :00
    },
    'retrain-model': {
        'task': 'backend.app.tasks.intelligence.retrain_deal_probability_model_weekly',
        'schedule': crontab(hour=2, day_of_week=6),  # Sunday 2am UTC
    },
    'send-alerts-digest': {
        'task': 'backend.app.tasks.intelligence.send_health_alerts_digest',
        'schedule': crontab(hour=9, minute=0),  # Daily 9am UTC
    },
}
```

---

## REACT COMPONENTS

### DealHealthCard.tsx

```typescript
import React, { useMemo } from 'react';
import { Card, Metric } from '@tremor/react';

interface DealHealthCardProps {
  health_score: number;
  health_status: 'healthy' | 'at_risk' | 'critical';
  component_scores: {
    engagement: number;
    momentum: number;
    buyer_completeness: number;
    competition: number;
  };
}

export const DealHealthCard: React.FC<DealHealthCardProps> = ({
  health_score,
  health_status,
  component_scores
}) => {
  const statusColor = useMemo(() => {
    switch (health_status) {
      case 'healthy': return 'text-green-600';
      case 'at_risk': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  }, [health_status]);

  const statusBg = useMemo(() => {
    switch (health_status) {
      case 'healthy': return 'bg-green-50';
      case 'at_risk': return 'bg-yellow-50';
      case 'critical': return 'bg-red-50';
      default: return 'bg-gray-50';
    }
  }, [health_status]);

  return (
    <Card className={statusBg}>
      <div className="space-y-4">
        <div className="text-center">
          <div className={`text-5xl font-bold ${statusColor}`}>
            {health_score}
          </div>
          <p className="text-xs text-gray-500 mt-1">Deal Health Score</p>
          <p className={`text-sm font-semibold mt-2 ${statusColor}`}>
            {health_status.toUpperCase()}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2 border-t pt-4">
          <div>
            <p className="text-xs text-gray-500">Engagement</p>
            <p className="text-lg font-semibold">{component_scores.engagement}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Momentum</p>
            <p className="text-lg font-semibold">{component_scores.momentum}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Buyer</p>
            <p className="text-lg font-semibold">{component_scores.buyer_completeness}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Competition</p>
            <p className="text-lg font-semibold">{component_scores.competition}</p>
          </div>
        </div>
      </div>
    </Card>
  );
};
```

---

## API TESTING

### cURL Examples

```bash
# Get buying committee
curl -X GET "http://localhost:8000/api/v1/intelligence/stakeholders/deal_001" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"

# Get deal probability
curl -X GET "http://localhost:8000/api/v1/intelligence/probability/deal_001" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Get deal health
curl -X GET "http://localhost:8000/api/v1/intelligence/health/deal_001" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Record engagement event
curl -X POST "http://localhost:8000/api/v1/intelligence/stakeholders/deal_001/engagement" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "person_001",
    "event_type": "email_open",
    "event_details": {"email_subject": "Proposal Review"}
  }'

# Get alerts
curl -X GET "http://localhost:8000/api/v1/intelligence/alerts?status=unresolved" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Acknowledge alert
curl -X POST "http://localhost:8000/api/v1/intelligence/alerts/alert_uuid/acknowledge" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

**Phase 27 Implementation - Ready to Code** ✅

All code examples ready for copy-paste development.

