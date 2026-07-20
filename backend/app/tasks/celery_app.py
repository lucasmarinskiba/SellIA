"""Celery App Configuration

Configura Celery con Redis como broker y backend.
"""

import os
from celery import Celery
from app.core.config import get_settings

# Import all models so SQLAlchemy mappers are configured in Celery workers
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.catalogs.models import CatalogItem
from app.domains.channels.models import ChannelConnection, Conversation, Message
from app.domains.subscriptions.models import SubscriptionPlan, Subscription, UserAPIKey, UsageTracking, PaymentTransaction, Invoice, UsageAlert
from app.domains.agents.models import AgentPersonality, AgentConfig, AgentConversation, AgentMessage
from app.domains.automations.models import Workflow, WorkflowExecution, EmailTemplate, EmailSequence, SequenceStep, ChatbotRule, SequenceSubscription, SequenceEmailLog, GeneratedContent, ContentCalendar
from app.domains.crm.models import Pipeline, Deal, LeadScore, LeadActivity
from app.domains.orders.models import Order, RevenueEvent, PaymentIntegration
from app.domains.alerts.models import AlertRule, Alert, Recommendation
from app.domains.objectives.models import Department, BusinessObjective, KPI, KeyResult
from app.domains.retention.models import LoyaltyProgram, ReferralProgram, ReferralCode, ReferralUse, NpsCampaign, NpsResponse, CustomerSegment
from app.domains.bi.models import FunnelMetrics, CohortMetrics, ChurnPrediction, LtvPrediction, InsightAlert
from app.domains.finance.models import SalesInvoice, PaymentReminder, AccountsReceivableSnapshot, TaxConfig
from app.domains.autopilot.models import AutopilotConfig, AutopilotActionLog, AutopilotDailyReport
from app.domains.outreach.models import ContactFatigueScore, OutreachCadenceRule, OutreachLog
from app.domains.proactive.models import OutreachOpportunity, OutreachRule
from app.domains.retention.models import HealthScoreRecord, HealthScoreHistory
from app.domains.intelligence.models import MessageAnalysis, ConversationIntelligence
from app.domains.notifications.models import NotificationDelivery
from app.domains.optimization.models import OptimizationExperiment, OptimizationResult
from app.domains.provisioning.models import ResourceRequest, ResourceJob, ResourceEvent
from app.domains.growth.models import GrowthCampaign, LeadMagnet, InboundLead, SocialProofItem, UgcRequest, ValueSequence, ValueSequenceEnrollment
from app.domains.consumo.models import AICallLog, OnboardingProgress, ChurnRiskSignal, QualityGateConfig
from app.domains.marketplace.models import MarketplaceItem, MarketplacePurchase
from app.domains.fomo.models import FOMOCampaign, SocialProofEvent
from app.domains.social_growth.models import SocialProfileAudit, ContentCalendarSlot, CompetitorTracking
from app.domains.gamification.ambassador_models import CertificationProgram, UserCertification, PublicExpertProfile
from app.domains.referrals.models import ReferralCode, ReferralTracking
from app.domains.coupons.models import Coupon, CouponUsage
from app.domains.nps.models import FeedbackNPSResponse, FeedbackItem
from app.domains.product_tours.models import TourStep, UserTourProgress
from app.domains.training.models import TrainingScenario, TrainingRun

settings = get_settings()

_modules = [
    "app.tasks.workflow_tasks",
    "app.domains.documents.tasks",
    "app.tasks.content_tasks",
    "app.tasks.subscription_tasks",
    "app.tasks.selia_tasks",
    "app.tasks.autopilot_tasks",
    "app.tasks.autonomous_tasks",
    "app.tasks.provisioning_tasks",
    "app.tasks.growth_tasks",
    "app.tasks.support_tasks",
    "app.tasks.batch_ai_tasks",
    "app.tasks.synthetic_tasks",
    "app.tasks.consumo_tasks",
    "app.tasks.competitive_tasks",
    "app.tasks.sales_funnel_tasks",
    "app.domains.memory.tasks",
    "app.domains.proactive.tasks",
    "app.domains.agents.tasks_scoring",
    "app.domains.agents.auto_responder.tasks",
    "app.domains.training.tasks",
]
_includes = []
for mod in _modules:
    try:
        __import__(mod)
        _includes.append(mod)
    except Exception:
        pass

celery_app = Celery(
    "sellia",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=_includes,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutos max por tarea
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

# Beat schedule para tareas periódicas
celery_app.conf.beat_schedule = {
    "check-pending-workflows": {
        "task": "app.tasks.workflow_tasks.check_pending_workflows",
        "schedule": 30.0,  # cada 30 segundos
    },
    "check-email-sequences": {
        "task": "app.tasks.workflow_tasks.check_email_sequences",
        "schedule": 60.0,  # cada 60 segundos
    },
    "check-human-handoffs": {
        "task": "app.tasks.workflow_tasks.check_human_handoffs",
        "schedule": 15.0,  # cada 15 segundos
    },
    "check-deals-stalled": {
        "task": "app.tasks.workflow_tasks.check_deals_stalled",
        "schedule": 3600.0,  # cada 1 hora
    },
    "check-hot-leads-no-deal": {
        "task": "app.tasks.workflow_tasks.check_hot_leads_no_deal",
        "schedule": 21600.0,  # cada 6 horas
    },
    "check-abandoned-carts": {
        "task": "app.tasks.workflow_tasks.check_abandoned_carts",
        "schedule": 86400.0,  # cada 1 día
    },
    "check-no-reply": {
        "task": "app.tasks.workflow_tasks.check_no_reply_conversations",
        "schedule": 3600.0,  # cada 1 hora
    },
    "check-upcoming-appointments": {
        "task": "app.tasks.workflow_tasks.check_upcoming_appointments",
        "schedule": 900.0,  # cada 15 minutos
    },
    "process-no-shows": {
        "task": "app.tasks.workflow_tasks.process_no_show_appointments",
        "schedule": 1800.0,  # cada 30 minutos
    },
    "request-pending-confirmations": {
        "task": "app.tasks.workflow_tasks.request_pending_confirmations",
        "schedule": 3600.0,  # cada 1 hora
    },
    # === AI Content Generation Tasks ===
    "auto-generate-catalog-content": {
        "task": "app.tasks.content_tasks.auto_generate_catalog_content_task",
        "schedule": 86400.0,  # cada 24 horas
    },
    "schedule-content-posts": {
        "task": "app.tasks.content_tasks.schedule_content_posts_task",
        "schedule": 300.0,  # cada 5 minutos
    },
    "analyze-content-performance": {
        "task": "app.tasks.content_tasks.analyze_content_performance_task",
        "schedule": 604800.0,  # cada 7 días
    },
    "cleanup-old-generated-content": {
        "task": "app.tasks.content_tasks.cleanup_old_generated_content_task",
        "schedule": 86400.0,  # cada 24 horas
    },
    # === Subscription Management Tasks ===
    "check-expiring-subscriptions": {
        "task": "app.tasks.subscription_tasks.check_expiring_subscriptions",
        "schedule": 21600.0,  # cada 6 horas
    },
    "process-crypto-pending-payments": {
        "task": "app.tasks.subscription_tasks.process_crypto_pending_payments",
        "schedule": 120.0,  # cada 2 minutos
    },
    "cleanup-expired-crypto-payments": {
        "task": "app.tasks.subscription_tasks.cleanup_expired_crypto_payments",
        "schedule": 600.0,  # cada 10 minutos
    },
    "check-usage-alerts": {
        "task": "app.tasks.subscription_tasks.check_usage_alerts",
        "schedule": 300.0,  # cada 5 minutos
    },
    "generate-recurring-invoices": {
        "task": "app.tasks.subscription_tasks.generate_recurring_invoices",
        "schedule": 86400.0,  # cada 24 horas
    },
    "send-transfer-reminders": {
        "task": "app.tasks.subscription_tasks.send_transfer_reminders",
        "schedule": 21600.0,  # cada 6 horas
    },
    "expire-pending-transfers": {
        "task": "app.tasks.subscription_tasks.expire_pending_transfers",
        "schedule": 21600.0,  # cada 6 horas
    },
    "sync-mercadopago-preapprovals": {
        "task": "app.tasks.subscription_tasks.sync_mercadopago_preapprovals",
        "schedule": 21600.0,  # cada 6 horas
    },
    # === SellIA Virtual Company Tasks ===
    "selia-director-daily": {
        "task": "app.tasks.selia_tasks.selia_director_daily",
        "schedule": 86400.0,  # cada 24 horas
    },
    "rfm-segmentation": {
        "task": "app.tasks.selia_tasks.rfm_segmentation",
        "schedule": 86400.0,  # cada 24 horas
    },
    "payment-reminder-check": {
        "task": "app.tasks.selia_tasks.payment_reminder_check",
        "schedule": 3600.0,  # cada 1 hora
    },
    "bi-analytics-daily": {
        "task": "app.tasks.selia_tasks.bi_analytics_daily",
        "schedule": 86400.0,  # cada 24 horas
    },
    # === Security & Compliance Tasks ===
    "data-retention-cleanup": {
        "task": "app.tasks.security_tasks.data_retention_cleanup",
        "schedule": 604800.0,  # cada 7 días
    },
    "rotate-webhook-tokens": {
        "task": "app.tasks.security_tasks.rotate_webhook_tokens",
        "schedule": 7776000.0,  # cada 90 días
    },
    "security-audit-report": {
        "task": "app.tasks.security_tasks.security_audit_report",
        "schedule": 604800.0,  # cada 7 días
    },
    "cleanup-expired-ip-blocks": {
        "task": "app.tasks.security_tasks.cleanup_expired_ip_blocks",
        "schedule": 3600.0,  # cada 1 hora
    },
    "auto-block-high-risk-ips": {
        "task": "app.tasks.security_tasks.auto_block_high_risk_ips",
        "schedule": 300.0,  # cada 5 minutos
    },
    # === Autopilot 24/7 Tasks ===
    "autopilot-recommendation-executor": {
        "task": "app.tasks.autopilot_tasks.autopilot_recommendation_executor",
        "schedule": 900.0,  # cada 15 minutos
    },
    "autopilot-daily-report-generator": {
        "task": "app.tasks.autopilot_tasks.autopilot_daily_report_generator",
        "schedule": 86400.0,  # cada 24 horas
    },
    "fatigue-score-recalculation": {
        "task": "app.tasks.autopilot_tasks.fatigue_score_recalculation",
        "schedule": 3600.0,  # cada 1 hora
    },
    "auto-close-evaluator": {
        "task": "app.tasks.autopilot_tasks.auto_close_evaluator",
        "schedule": 3600.0,  # cada 1 hora
    },
    "health-score-recalculation": {
        "task": "app.tasks.autopilot_tasks.health_score_recalculation",
        "schedule": 86400.0,  # cada 24 horas
    },
    "churn-prevention-activator": {
        "task": "app.tasks.autopilot_tasks.churn_prevention_activator",
        "schedule": 86400.0,  # cada 24 horas
    },
    "cadence-engine-scheduler": {
        "task": "app.tasks.autopilot_tasks.cadence_engine_scheduler",
        "schedule": 1800.0,  # cada 30 minutos
    },
    "director-executive-loop": {
        "task": "app.tasks.autopilot_tasks.director_executive_loop",
        "schedule": 21600.0,  # cada 6 horas
    },
    # === Autonomous Sales Loop Tasks ===
    "message-intelligence-analyzer": {
        "task": "app.tasks.autonomous_tasks.message_intelligence_analyzer",
        "schedule": 300.0,  # cada 5 minutos
    },
    "smart-action-router-evaluator": {
        "task": "app.tasks.autonomous_tasks.smart_action_router_evaluator",
        "schedule": 900.0,  # cada 15 minutos
    },
    "proactive-outreach-scheduler": {
        "task": "app.tasks.autonomous_tasks.proactive_outreach_scheduler",
        "schedule": 86400.0,  # cada 24 horas
    },
    "briefing-delivery": {
        "task": "app.tasks.autonomous_tasks.briefing_delivery",
        "schedule": 86400.0,  # cada 24 horas
    },
    "handoff-alert-sender": {
        "task": "app.tasks.autonomous_tasks.handoff_alert_sender",
        "schedule": 300.0,  # cada 5 minutos
    },
    "experiment-evaluator": {
        "task": "app.tasks.autonomous_tasks.experiment_evaluator",
        "schedule": 604800.0,  # cada 7 días
    },
    "auto-optimizer-runner": {
        "task": "app.tasks.autonomous_tasks.auto_optimizer_runner",
        "schedule": 604800.0,  # cada 7 días
    },
    "ab-test-winner-applier": {
        "task": "app.tasks.autonomous_tasks.ab_test_winner_applier",
        "schedule": 604800.0,  # cada 7 días
    },
    "pipeline-automation-trigger-scanner": {
        "task": "app.tasks.autonomous_tasks.pipeline_automation_trigger_scanner",
        "schedule": 3600.0,  # cada 1 hora
    },
    # === Synthetic Monitoring Tasks ===
    "synthetic-checks": {
        "task": "app.tasks.synthetic_tasks.run_synthetic_checks_task",
        "schedule": 300.0,  # cada 5 minutos
    },
    # === Churn Shield Tasks ===
    "churn-shield-analysis": {
        "task": "app.tasks.consumo_tasks.churn_shield_analysis_task",
        "schedule": 86400.0,  # cada 24 horas
    },
    # === Support Auto-Resolution Tasks ===
    "auto-resolve-tickets": {
        "task": "app.tasks.support_tasks.auto_resolve_tickets_task",
        "schedule": 21600.0,  # cada 6 horas
    },
    "generate-support-stats": {
        "task": "app.tasks.support_tasks.generate_support_stats_task",
        "schedule": 86400.0,  # cada 24 horas
    },
    # === Finance Autopilot Tasks ===
    "finance-auto-deliver": {
        "task": "app.tasks.finance_tasks.auto_deliver_invoices",
        "schedule": 86400.0,  # cada 24 horas (8 AM)
    },
    "finance-dunning": {
        "task": "app.tasks.finance_tasks.dunning_sequence",
        "schedule": 86400.0,  # cada 24 horas (9 AM)
    },
    "finance-cash-flow": {
        "task": "app.tasks.finance_tasks.cash_flow_forecast",
        "schedule": 86400.0,  # cada 24 horas (6 AM)
    },
    "finance-reconcile": {
        "task": "app.tasks.finance_tasks.auto_reconcile_payments",
        "schedule": 7200.0,  # cada 2 horas
    },
    # === Memory & Summarization ===
    "summarize-conversations-hourly": {
        "task": "app.domains.memory.tasks.summarize_conversation_task",
        "schedule": 3600.0,  # cada 1 hora
    },
    # === Proactive Outreach Engine ===
    "detect-opportunities": {
        "task": "app.domains.proactive.tasks.detect_opportunities_task",
        "schedule": 1800.0,  # cada 30 minutos
    },
    # === Deal Scoring ===
    "update-deal-scores": {
        "task": "app.domains.agents.tasks_scoring.update_deal_scores_task",
        "schedule": 3600.0,  # cada 1 hora
    },
    # ═══════════════════════════════════════════════
    # === 4-Pillar Autonomous Computing System ===
    # ═══════════════════════════════════════════════
    # Ciclo maestro: config + repair + protection + optimization
    "autonomous-operations-cycle": {
        "task": "app.tasks.autonomous_tasks.autonomous_operations_cycle",
        "schedule": 300.0,   # cada 5 minutos — pilares internos con sus propios intervalos
    },
    # Health check rápido (sin acciones)
    "system-health-check": {
        "task": "app.tasks.autonomous_tasks.system_health_check",
        "schedule": 120.0,   # cada 2 minutos
    },
    # Optimización profunda + A/B tests
    "deep-system-optimization": {
        "task": "app.tasks.autonomous_tasks.deep_system_optimization",
        "schedule": 86400.0,  # cada 24 horas
    },
    # Reporte ejecutivo semanal al dueño
    "weekly-executive-report": {
        "task": "app.tasks.autonomous_tasks.weekly_executive_report",
        "schedule": 604800.0,  # cada 7 días (lunes 8 AM)
    },
    # === Auto-Responder Pilot Agent ===
    "auto-responder-check": {
        "task": "app.domains.agents.auto_responder.tasks.auto_responder_check_task",
        "schedule": 300.0,  # cada 5 minutos
    },
    # === Sales Funnel Automation (Fases 11-12) ===
    "send-follow-ups": {
        "task": "app.tasks.sales_funnel_tasks.send_follow_ups",
        "schedule": 259200.0,  # cada 3 días
    },
    "send-upsell-campaigns": {
        "task": "app.tasks.sales_funnel_tasks.send_upsell_campaigns",
        "schedule": 604800.0,  # cada 7 días
    },
    "send-winback-campaigns": {
        "task": "app.tasks.sales_funnel_tasks.send_winback_campaigns",
        "schedule": 1209600.0,  # cada 14 días
    },
    "daily-growth-cycle": {
        "task": "app.tasks.sales_funnel_tasks.daily_growth_cycle",
        "schedule": 86400.0,  # cada 24 horas (6 AM UTC)
        "args": ({"name": "SellIA Pro", "price": 499, "niche": "sales"},),
    },
}


def get_celery_app():
    return celery_app
