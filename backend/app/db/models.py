"""
SQLAlchemy ORM Models
- Leads
- Workflows
- Workflow Executions (email tracking)
- Lead Sources
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

Base = declarative_base()

# ============================================================
# LEADS
# ============================================================
class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    company = Column(String(255))
    job_title = Column(String(255))
    industry = Column(String(100))
    phone = Column(String(20))
    pain_points = Column(Text)
    budget = Column(Float)
    timeline = Column(String(50))
    source = Column(String(50))  # "linkedin", "website", "manual", "referral"
    status = Column(String(50), default="new")  # new, contacted, engaged, qualified, won, lost
    score = Column(Float, default=0)
    score_breakdown = Column(JSON)  # {completeness: 10, engagement: 30, fit: 60}
    last_contacted = Column(DateTime)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relationships
    workflow_executions = relationship("WorkflowExecution", back_populates="lead", cascade="all, delete-orphan")

# ============================================================
# WORKFLOWS
# ============================================================
class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    industry_filter = Column(String(100))
    min_score_filter = Column(Float, default=0)
    status = Column(String(50), default="draft")  # draft, active, paused, completed
    active_leads_count = Column(Integer, default=0)
    steps = Column(JSON)  # Array of steps with templates

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

# ============================================================
# WORKFLOW EXECUTIONS - Email Tracking
# ============================================================
class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    lead_email = Column(String(255))  # Denormalized for quick lookup
    step_number = Column(Integer)
    email_status = Column(String(50), default="scheduled")  # scheduled, sent, delivered, opened, clicked, bounced, unsubscribed
    tracking_id = Column(String(100), unique=True)  # For webhook tracking

    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    opened_count = Column(Integer, default=0)
    clicked_at = Column(DateTime)
    clicked_count = Column(Integer, default=0)
    bounce_reason = Column(String(255))
    bounced_at = Column(DateTime)

    email_subject = Column(String(255))
    email_body = Column(Text)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    lead = relationship("Lead", back_populates="workflow_executions")

# ============================================================
# LEAD SOURCES
# ============================================================
class LeadSource(Base):
    __tablename__ = "lead_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_type = Column(String(50), nullable=False)  # linkedin, website, manual, referral, email, cold_outreach
    status = Column(String(50), default="active")  # active, paused, inactive
    auto_workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=True)
    industry_filter = Column(String(100))
    config = Column(JSON)  # LinkedInConfig, WebsiteFormConfig, etc.

    leads_generated = Column(Integer, default=0)
    last_fetch = Column(DateTime)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

# ============================================================
# EMAIL LOGS (for audit trail)
# ============================================================
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True)
    tracking_id = Column(String(100), unique=True, nullable=False)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"))
    lead_email = Column(String(255), nullable=False)
    subject = Column(String(255))
    provider = Column(String(50))  # sendgrid, smtp, mock
    status = Column(String(50))  # sent, delivered, opened, clicked, bounced
    error_message = Column(Text)

    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

# ============================================================
# WEBHOOK EVENTS (for tracking opens/clicks)
# ============================================================
class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True)
    provider = Column(String(50))  # sendgrid, etc.
    event_type = Column(String(50))  # open, click, bounce, unsubscribe
    tracking_id = Column(String(100))
    email = Column(String(255))
    payload = Column(JSON)  # Raw webhook payload
    processed = Column(Boolean, default=False)

    received_at = Column(DateTime, default=datetime.now, nullable=False)
    processed_at = Column(DateTime)
