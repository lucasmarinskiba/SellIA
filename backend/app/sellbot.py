"""
SellIA Sellbot - Email Delivery + PostgreSQL Persistence
Endpoints:
- POST /api/v1/webhooks/whatsapp (Meta webhook)
- POST /api/v1/webhooks/sendgrid (Email tracking)
- POST /api/v1/sequences/cold-email (Email generation)
- POST /api/v1/knowledge/ingest (PDF knowledge)
- GET /api/ping (Health check)
- /api/v1/leads/* (Lead management + scoring)
- /api/v1/workflows/* (Email automation)
- /api/v1/lead-sources/* (Prospecting)
"""
import os
import logging
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from collections import defaultdict
from datetime import datetime, timedelta

# Import routers
from app.api.v1 import leads as leads_module
from app.api.v1 import workflows as workflows_module
from app.api.v1 import lead_sources as lead_sources_module
from app.api.v1 import email_webhooks as email_webhooks_module
from app.api.v1 import progression as progression_module
from app.api.v1 import analytics as analytics_module
from app.api.v1 import attribution as attribution_module
from app.api.v1 import journeys as journeys_module
from app.api.v1 import compliance as compliance_module
from app.api.v1 import integrations as integrations_module
from app.api.v1 import sales_agents as sales_agents_module
from app.api.v1 import neural_networks as neural_networks_module
from app.api.v1 import sales_automation as sales_automation_module
from app.api.v1 import deal_intelligence as deal_intelligence_module
from app.api.v1 import sales_coaching as sales_coaching_module
from app.api.v1 import crm_collaboration as crm_collaboration_module
from app.api.v1 import sales_funnel_orchestration as sales_funnel_orchestration_module
from app.api.v1 import marketing_intelligence as marketing_intelligence_module
from app.api.v1 import accounting_intelligence as accounting_intelligence_module
from app.api.v1 import sales_operations as sales_operations_module

# Phase X6: FOMO Dynamics (Ultra-Potent Psychology Engine)
from app.domains.fomo_dynamics import router as fomo_dynamics_router

# Phase X7: Perception Engineering (Psychology-Driven Sales Agent)
from app.domains.perception_engineering import router as perception_engineering_router

# Phase X8: Auto-Marketing & Growth (SellIA Self-Promotion)
from app.domains.auto_marketing import router as auto_marketing_router

# Phase X9: AI User Intelligence (Deep Profiling)
from app.domains.user_intelligence import router as user_intelligence_router

# Phase X10: FOMO Generation (Personalized Scarcity)
from app.domains.fomo_generation import router as fomo_generation_router

# Phase X11: Loyalty & Retention (VIP Program)
from app.domains.loyalty_engine import router as loyalty_engine_router

# Phase X12: Conversion & Attraction (Multi-touch Closing)
from app.domains.conversion_engine import router as conversion_engine_router

# Acquisition Orchestrator (X9→X10→X12→X11 Integration)
from app.domains.acquisition_orchestrator import router as acquisition_orchestrator_router

# Instagram Automation (@sell_.ia + FeedIA synergy)
from app.domains.instagram_automation import router as instagram_automation_router

# Feedback Loop (Conversion data → X9 improvements)
from app.domains.feedback_loop import router as feedback_loop_router

# FOMO Intelligence (Escasez real / Prueba social / Exclusividad / Transparencia)
from app.domains.fomo_intelligence import router as fomo_intelligence_router

# ARCA Compliance (CUIT, Monotributo, INCOTERMS, NCM — datos reales)
from app.domains.arca_compliance import router as arca_compliance_router

# Business model: se importa explícito porque ChannelConnection.business usa
# relationship("Business") (string) - SQLAlchemy necesita la clase ya cargada
# en el registry antes de configurar mappers, y ningún import previo la traía.
from app.domains.businesses.models import Business

# Location model: Phase 5A location profiles — must be imported before SQLAlchemy mapper config
from app.domains.businesses.location_models import Location

# Nota: api.v1.channels ya se registra en app.main (_try_include, prefix
# /api/v1/businesses) — no duplicar acá.

# Platforms Integration (TikTok Shop real; resto queda como TODO histórico)
from app.api.v1.platforms_integration import router as platforms_integration_router

from app.domains.performance_optimization.models import PerformanceMetrics, SlowQuery, IndexRecommendation, CacheStrategy, QueryOptimization
from app.domains.channel_integration.models import GoogleBusinessProfileConnection, GoogleMapsLocation, LocationMessage, LocationMessageExecution, LocationReview
from app.domains.ai_content_generation.models import ContentTemplate, GeneratedContent, ContentPerformance, BulkContentGeneration, ContentVariant

# Database
from app.db import init_db, close_db, get_db

# Scheduler
from app.core.scheduler import get_scheduler
from app.core.task_processor import init_processor, start_processor, stop_processor, get_processor_stats

# Progression
from app.services.progression_service import init_progression_service

# Cold-lead follow-up loop (Task 5)
from app.core.followup_scheduler import run_followup_loop, stop_followup_loop

scheduler = None
processor = None
progression_service = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# STARTUP/SHUTDOWN
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global scheduler, processor, progression_service
    logger.info("🚀 SellIA Sellbot starting...")

    await init_db()
    logger.info("✅ Database initialized")

    # Migrate schema for 2FA columns
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                existing = await db.execute(text("PRAGMA table_info(users)"))
                cols = {row[1] for row in existing.all()}
                if "totp_secret" not in cols:
                    await db.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR(32)"))
                if "is_2fa_enabled" not in cols:
                    await db.execute(text("ALTER TABLE users ADD COLUMN is_2fa_enabled BOOLEAN DEFAULT 0"))
            else:
                await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(32)"))
                await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_2fa_enabled BOOLEAN DEFAULT false"))
            await db.commit()
        logger.info("✅ 2FA schema migrated")
    except Exception as e:
        logger.warning(f"2FA schema migration: {str(e)[:80]}")

    # Create computer_use_audit_logs table (real agent activity trail used by
    # the Brain dashboard's Agent Audit Log / Approvals Center / Handoff Log).
    # Its ORM model's FK previously pointed at a nonexistent "user" (singular)
    # table so this never got created by the disabled auto-create_all path.
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS computer_use_audit_logs (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36),
                        session_id VARCHAR(36),
                        created_at DATETIME,
                        executed_at DATETIME,
                        duration_ms INTEGER DEFAULT 0,
                        platform VARCHAR(50),
                        action_type VARCHAR(50),
                        agent_name VARCHAR(100),
                        strategy_name VARCHAR(100),
                        tactics TEXT,
                        confidence_score FLOAT DEFAULT 0.0,
                        requires_approval BOOLEAN DEFAULT 0,
                        input_data TEXT,
                        output_data TEXT,
                        status VARCHAR(50),
                        error_message TEXT,
                        metadata TEXT,
                        user_approved BOOLEAN,
                        approval_at DATETIME,
                        approved_by_user_id VARCHAR(36)
                    )
                """))
            else:
                # No FK constraints on user_id/approved_by_user_id here: the
                # users table's id column type has varied across migration
                # attempts in this codebase's history, and a type mismatch
                # would abort this CREATE TABLE and leave the whole audit
                # trail feature broken. Values are still real UUID strings.
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS computer_use_audit_logs (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36),
                        session_id VARCHAR(36),
                        created_at TIMESTAMP,
                        executed_at TIMESTAMP,
                        duration_ms INTEGER DEFAULT 0,
                        platform VARCHAR(50),
                        action_type VARCHAR(50),
                        agent_name VARCHAR(100),
                        strategy_name VARCHAR(100),
                        tactics JSONB,
                        confidence_score FLOAT DEFAULT 0.0,
                        requires_approval BOOLEAN DEFAULT false,
                        input_data TEXT,
                        output_data TEXT,
                        status VARCHAR(50),
                        error_message TEXT,
                        metadata JSONB,
                        user_approved BOOLEAN,
                        approval_at TIMESTAMP,
                        approved_by_user_id VARCHAR(36)
                    )
                """))
                await db.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_cu_audit_created_at ON computer_use_audit_logs (created_at)"
                ))
                await db.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_cu_audit_platform ON computer_use_audit_logs (platform)"
                ))
                await db.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_cu_audit_status ON computer_use_audit_logs (status)"
                ))
            await db.commit()
        logger.info("✅ computer_use_audit_logs table ensured")
    except Exception as e:
        logger.warning(f"computer_use_audit_logs migration: {str(e)[:120]}")

    # Restore businesses.is_active (referenced by 15+ call sites across the
    # codebase for soft-delete filtering; a prior session's schema-drift fix
    # dropped it from the ORM model instead of restoring the column, which
    # broke every one of those call sites with AttributeError).
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                existing = await db.execute(text("PRAGMA table_info(businesses)"))
                cols = {row[1] for row in existing.all()}
                if "is_active" not in cols:
                    await db.execute(text("ALTER TABLE businesses ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            else:
                await db.execute(text(
                    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true NOT NULL"
                ))
            await db.commit()
        logger.info("✅ businesses.is_active restored")
    except Exception as e:
        logger.warning(f"businesses.is_active migration: {str(e)[:120]}")

    # Restore businesses.type (Business.type is read by context_builder.py,
    # ai_reply.py, crm/scoring.py, and 5 other files for AI prompt context —
    # same class of drift-caused AttributeError as is_active above).
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                existing = await db.execute(text("PRAGMA table_info(businesses)"))
                cols = {row[1] for row in existing.all()}
                if "type" not in cols:
                    await db.execute(text("ALTER TABLE businesses ADD COLUMN type VARCHAR(20) DEFAULT 'services'"))
            else:
                # "business_kind", not "businesstype": that name collides
                # with app.domains.business_context.models.BusinessType,
                # which already owns a Postgres enum called "businesstype"
                # with a completely different (uppercase) value set.
                # SQLAlchemy's Enum type stores the Python member NAME by
                # default (SERVICES), not .value ("services") — matching how
                # business_context's BusinessType enum is already stored.
                await db.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE business_kind AS ENUM ('SERVICES', 'GOODS', 'DIGITAL', 'MIXED');
                    EXCEPTION WHEN duplicate_object THEN null;
                    END $$;
                """))
                await db.execute(text(
                    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS type business_kind NOT NULL DEFAULT 'SERVICES'"
                ))
            await db.commit()
        logger.info("✅ businesses.type restored")
    except Exception as e:
        logger.warning(f"businesses.type migration: {str(e)[:120]}")

    # Restore businesses.config (read by context_builder.py, localization.py,
    # investor_pitch/service.py, agents.py — same drift-caused AttributeError).
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                existing = await db.execute(text("PRAGMA table_info(businesses)"))
                cols = {row[1] for row in existing.all()}
                if "config" not in cols:
                    await db.execute(text("ALTER TABLE businesses ADD COLUMN config TEXT DEFAULT '{}'"))
            else:
                await db.execute(text(
                    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}'::jsonb NOT NULL"
                ))
            await db.commit()
        logger.info("✅ businesses.config restored")
    except Exception as e:
        logger.warning(f"businesses.config migration: {str(e)[:120]}")

    # Create business_contexts table if missing (was skipped when CoreBase FK
    # validation blocked auto table creation in init_db). Minimal schema with
    # just the essential columns — full model definition in
    # app.domains.business_context.models.BusinessContext.
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS business_contexts (
                        id VARCHAR(36) PRIMARY KEY,
                        business_id VARCHAR(36) NOT NULL,
                        industry VARCHAR(255),
                        target_audience TEXT,
                        value_proposition TEXT,
                        price_range VARCHAR(100),
                        average_ticket VARCHAR(100),
                        sales_model VARCHAR(50),
                        communication_angles TEXT,
                        winning_offer_summary TEXT,
                        scheduling_link VARCHAR(512),
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
            else:
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS business_contexts (
                        id UUID PRIMARY KEY,
                        business_id UUID NOT NULL,
                        industry VARCHAR(255),
                        target_audience TEXT,
                        value_proposition TEXT,
                        price_range VARCHAR(100),
                        average_ticket VARCHAR(100),
                        sales_model VARCHAR(50),
                        communication_angles JSONB DEFAULT '[]'::jsonb,
                        winning_offer_summary TEXT,
                        scheduling_link VARCHAR(512),
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
            await db.commit()
        logger.info("✅ business_contexts table ensured")
    except Exception as e:
        logger.warning(f"business_contexts table creation: {str(e)[:120]}")

    # Migrate schema for ManyChat + Nicho/Oferta/Ángulos + Booking-rate feature.
    # create_all() never alters existing tables, so business_contexts' new
    # columns need this same idempotent-patch idiom used above for 2FA.
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                existing = await db.execute(text("PRAGMA table_info(business_contexts)"))
                cols = {row[1] for row in existing.all()}
                if "communication_angles" not in cols:
                    await db.execute(text("ALTER TABLE business_contexts ADD COLUMN communication_angles TEXT"))
                if "winning_offer_summary" not in cols:
                    await db.execute(text("ALTER TABLE business_contexts ADD COLUMN winning_offer_summary TEXT"))
                if "scheduling_link" not in cols:
                    await db.execute(text("ALTER TABLE business_contexts ADD COLUMN scheduling_link VARCHAR(512)"))
            else:
                await db.execute(text(
                    "ALTER TABLE business_contexts ADD COLUMN IF NOT EXISTS communication_angles JSONB DEFAULT '[]'::jsonb"
                ))
                await db.execute(text(
                    "ALTER TABLE business_contexts ADD COLUMN IF NOT EXISTS winning_offer_summary TEXT"
                ))
                await db.execute(text(
                    "ALTER TABLE business_contexts ADD COLUMN IF NOT EXISTS scheduling_link VARCHAR(512)"
                ))
            await db.commit()
        logger.info("✅ business_contexts angles/scheduling schema migrated")
    except Exception as e:
        logger.warning(f"business_contexts schema migration: {str(e)[:120]}")

    # ManyChat enum value — must commit alone, isolated from any statement
    # that might use the new value in the same transaction (Postgres rule).
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        if not is_sqlite:
            async with AsyncSessionLocal() as db:
                await db.execute(text(
                    "ALTER TYPE channelplatform ADD VALUE IF NOT EXISTS 'manychat'"
                ))
                await db.commit()
            logger.info("✅ channelplatform enum: manychat ensured")
    except Exception as e:
        logger.warning(f"channelplatform enum migration: {str(e)[:120]}")

    # Create transactions/refunds tables if missing. These live on
    # app.core.database.Base (CoreBase) which init_db() explicitly skips
    # (see app/db/database.py:111 — FK conflicts across ~100 domain models),
    # so — same as business_contexts above — they need an explicit
    # CREATE TABLE IF NOT EXISTS here or PaymentService's queries 500 with
    # "relation does not exist". Minimal schema; full definition lives in
    # app.domains.payments.payment_models.
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id VARCHAR(36) PRIMARY KEY,
                        business_id VARCHAR(36) NOT NULL,
                        customer_id VARCHAR(36),
                        order_id VARCHAR(36),
                        location_id VARCHAR(36),
                        conversation_id VARCHAR(36),
                        amount NUMERIC(12,2) NOT NULL,
                        currency VARCHAR(3) DEFAULT 'USD',
                        method VARCHAR(50) NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        mercadopago_payment_id VARCHAR(255) UNIQUE,
                        mercadopago_preference_id VARCHAR(255),
                        mercadopago_merchant_order_id VARCHAR(255),
                        mercadopago_status VARCHAR(50),
                        installments INTEGER DEFAULT 1,
                        installment_amount NUMERIC(12,2),
                        description VARCHAR(500),
                        reference_id VARCHAR(255),
                        transaction_metadata TEXT,
                        gateway_fee NUMERIC(12,2) DEFAULT 0,
                        net_amount NUMERIC(12,2),
                        settlement_date DATETIME,
                        settled BOOLEAN DEFAULT 0,
                        webhook_notification_received BOOLEAN DEFAULT 0,
                        webhook_notification_date DATETIME,
                        created_at DATETIME,
                        approved_at DATETIME,
                        updated_at DATETIME
                    )
                """))
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS refunds (
                        id VARCHAR(36) PRIMARY KEY,
                        transaction_id VARCHAR(36) NOT NULL,
                        business_id VARCHAR(36) NOT NULL,
                        amount NUMERIC(12,2) NOT NULL,
                        status VARCHAR(20) DEFAULT 'requested',
                        reason VARCHAR(500),
                        mercadopago_refund_id VARCHAR(255) UNIQUE,
                        requested_by VARCHAR(36),
                        approved_by VARCHAR(36),
                        processed_at DATETIME,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
            else:
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id UUID PRIMARY KEY,
                        business_id UUID NOT NULL,
                        customer_id UUID,
                        order_id UUID,
                        location_id UUID,
                        conversation_id UUID,
                        amount NUMERIC(12,2) NOT NULL,
                        currency VARCHAR(3) DEFAULT 'USD',
                        method VARCHAR(50) NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        mercadopago_payment_id VARCHAR(255) UNIQUE,
                        mercadopago_preference_id VARCHAR(255),
                        mercadopago_merchant_order_id VARCHAR(255),
                        mercadopago_status VARCHAR(50),
                        installments INTEGER DEFAULT 1,
                        installment_amount NUMERIC(12,2),
                        description VARCHAR(500),
                        reference_id VARCHAR(255),
                        transaction_metadata JSONB,
                        gateway_fee NUMERIC(12,2) DEFAULT 0,
                        net_amount NUMERIC(12,2),
                        settlement_date TIMESTAMP,
                        settled BOOLEAN DEFAULT FALSE,
                        webhook_notification_received BOOLEAN DEFAULT FALSE,
                        webhook_notification_date TIMESTAMP,
                        created_at TIMESTAMP,
                        approved_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS refunds (
                        id UUID PRIMARY KEY,
                        transaction_id UUID NOT NULL,
                        business_id UUID NOT NULL,
                        amount NUMERIC(12,2) NOT NULL,
                        status VARCHAR(20) DEFAULT 'requested',
                        reason VARCHAR(500),
                        mercadopago_refund_id VARCHAR(255) UNIQUE,
                        requested_by UUID,
                        approved_by UUID,
                        processed_at TIMESTAMP,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                await db.execute(text(
                    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS conversation_id UUID"
                ))
            await db.commit()
        logger.info("✅ transactions/refunds tables ensured")
    except Exception as e:
        logger.warning(f"transactions/refunds table creation: {str(e)[:120]}")

    # Same story as transactions/refunds above — payment_metrics is another
    # CoreBase table init_db() skips. PaymentService._update_payment_metrics
    # (Task 4: webhook → mark sale won + refresh metrics) upserts into this
    # on every approved payment; without the table it 500s silently inside
    # the webhook's own try/except and the payments dashboard stays empty.
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS payment_metrics (
                        id VARCHAR(36) PRIMARY KEY,
                        business_id VARCHAR(36) NOT NULL UNIQUE,
                        total_transactions INTEGER DEFAULT 0,
                        total_revenue NUMERIC(15,2) DEFAULT 0,
                        avg_transaction_value NUMERIC(12,2) DEFAULT 0,
                        success_rate INTEGER DEFAULT 0,
                        failed_transactions INTEGER DEFAULT 0,
                        refund_rate INTEGER DEFAULT 0,
                        method_breakdown TEXT,
                        total_settled NUMERIC(15,2) DEFAULT 0,
                        pending_settlement NUMERIC(15,2) DEFAULT 0,
                        total_fees NUMERIC(12,2) DEFAULT 0,
                        transactions_7d INTEGER DEFAULT 0,
                        revenue_7d NUMERIC(15,2) DEFAULT 0,
                        updated_at DATETIME
                    )
                """))
            else:
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS payment_metrics (
                        id UUID PRIMARY KEY,
                        business_id UUID NOT NULL UNIQUE,
                        total_transactions INTEGER DEFAULT 0,
                        total_revenue NUMERIC(15,2) DEFAULT 0,
                        avg_transaction_value NUMERIC(12,2) DEFAULT 0,
                        success_rate INTEGER DEFAULT 0,
                        failed_transactions INTEGER DEFAULT 0,
                        refund_rate INTEGER DEFAULT 0,
                        method_breakdown JSONB,
                        total_settled NUMERIC(15,2) DEFAULT 0,
                        pending_settlement NUMERIC(15,2) DEFAULT 0,
                        total_fees NUMERIC(12,2) DEFAULT 0,
                        transactions_7d INTEGER DEFAULT 0,
                        revenue_7d NUMERIC(15,2) DEFAULT 0,
                        updated_at TIMESTAMP
                    )
                """))
            await db.commit()
        logger.info("✅ payment_metrics table ensured")
    except Exception as e:
        logger.warning(f"payment_metrics table creation: {str(e)[:120]}")

    # Task 5: cold-lead follow-up tracking columns on conversations. The
    # table itself already exists in production (created earlier via the
    # per-table debug endpoint) — just needs these 2 new columns so
    # followup_service.py can dedupe ("already nudged this silence window")
    # and cap ("max N nudges per conversation") without re-scanning history.
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                existing = await db.execute(text("PRAGMA table_info(conversations)"))
                cols = {row[1] for row in existing.all()}
                if "last_followup_sent_at" not in cols:
                    await db.execute(text("ALTER TABLE conversations ADD COLUMN last_followup_sent_at DATETIME"))
                if "followup_count" not in cols:
                    await db.execute(text("ALTER TABLE conversations ADD COLUMN followup_count INTEGER DEFAULT 0"))
            else:
                await db.execute(text(
                    "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS last_followup_sent_at TIMESTAMP"
                ))
                await db.execute(text(
                    "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS followup_count INTEGER DEFAULT 0"
                ))
            await db.commit()
        logger.info("✅ conversations follow-up columns ensured")
    except Exception as e:
        logger.warning(f"conversations follow-up columns migration: {str(e)[:120]}")

    # Task 6: LLM daily call cap — business_contexts.llm_daily_call_limit
    # (NULL = unlimited, existing behavior) + the llm_daily_usage counter
    # table llm_provider.py checks/increments on every LLM call.
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal, is_sqlite
        async with AsyncSessionLocal() as db:
            if is_sqlite:
                existing = await db.execute(text("PRAGMA table_info(business_contexts)"))
                cols = {row[1] for row in existing.all()}
                if "llm_daily_call_limit" not in cols:
                    await db.execute(text("ALTER TABLE business_contexts ADD COLUMN llm_daily_call_limit INTEGER"))
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS llm_daily_usage (
                        id VARCHAR(36) PRIMARY KEY,
                        business_id VARCHAR(36) NOT NULL,
                        usage_date DATE NOT NULL,
                        call_count INTEGER DEFAULT 0,
                        updated_at DATETIME,
                        UNIQUE(business_id, usage_date)
                    )
                """))
            else:
                await db.execute(text(
                    "ALTER TABLE business_contexts ADD COLUMN IF NOT EXISTS llm_daily_call_limit INTEGER"
                ))
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS llm_daily_usage (
                        id UUID PRIMARY KEY,
                        business_id UUID NOT NULL,
                        usage_date DATE NOT NULL,
                        call_count INTEGER DEFAULT 0,
                        updated_at TIMESTAMP,
                        UNIQUE(business_id, usage_date)
                    )
                """))
            await db.commit()
        logger.info("✅ LLM daily usage cap schema ensured")
    except Exception as e:
        logger.warning(f"LLM daily usage cap schema migration: {str(e)[:120]}")

    # Ensure the double-entry ledger tables exist (CoreBase domain that
    # init_db() skips; migrations are disabled — see entrypoint.sh).
    try:
        from app.domains.ledger.bootstrap import ensure_ledger_tables
        await ensure_ledger_tables()
        from app.domains.ad_budget.bootstrap import ensure_ad_budget_tables
        await ensure_ad_budget_tables()
        from app.domains.forecasting.bootstrap import ensure_forecasting_tables
        await ensure_forecasting_tables()
        from app.domains.brand_transformation.bootstrap import ensure_brand_transformation_tables
        await ensure_brand_transformation_tables()
        from app.domains.hr.models import HR_TABLES
        from app.domains.legal.models import LEGAL_TABLES
        from app.domains.procurement.models import PROCUREMENT_TABLES
        from app.core.database import engine
        async with engine.begin() as conn:
            for t in HR_TABLES + LEGAL_TABLES + PROCUREMENT_TABLES:
                await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    except Exception as e:
        logger.warning(f"domain tables bootstrap: {str(e)[:160]}")

    # Load Phase 33 seed data if needed (async-compatible)
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import os
        from app.db.seed_phase_33 import seed_phase_33

        # Get sync engine from DATABASE_URL
        db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://").replace("postgresql://", "postgresql+psycopg2://")
        if db_url:
            sync_engine = create_engine(db_url, connect_args={"connect_timeout": 5})
            SessionLocal = sessionmaker(bind=sync_engine)
            db = SessionLocal()
            try:
                result = seed_phase_33(db)
                if result["status"] == "success":
                    logger.info(f"✅ Phase 33 seed loaded: {result['products_created']} products, {result['listings_created']} listings, ${result['total_gmv_monthly']:,}/mo GMV")
                elif result["status"] == "skipped":
                    logger.debug(f"Phase 33 seed: {result['reason']}")
                else:
                    logger.warning(f"Phase 33 seed error: {result.get('error', 'unknown')}")
            finally:
                db.close()
    except Exception as e:
        logger.debug(f"Phase 33 seed unavailable: {e}")

    scheduler = await get_scheduler()
    logger.info("✅ Redis scheduler connected")

    if scheduler and scheduler.redis:
        try:
            from fastapi_limiter import FastAPILimiter
            await FastAPILimiter.init(scheduler.redis)
            logger.info("✅ FastAPILimiter initialized")
        except Exception as e:
            logger.warning(f"FastAPILimiter init skipped: {e}")
    else:
        logger.warning("⚠️ Redis unavailable — rate-limited endpoints (auth) will fail")

    processor = await init_processor(scheduler)
    logger.info("✅ Task processor initialized")

    progression_service = await init_progression_service(scheduler)
    logger.info("✅ Progression service initialized")

    # Start processor in background
    try:
        asyncio.create_task(start_processor())
        logger.info("✅ Task processor started")
    except Exception as e:
        logger.warning(f"Processor background start warning: {e}")

    # Start cold-lead follow-up loop in background (Task 5)
    try:
        asyncio.create_task(run_followup_loop())
        logger.info("✅ Follow-up scheduler started")
    except Exception as e:
        logger.warning(f"Follow-up scheduler background start warning: {e}")

    yield

    # Shutdown
    logger.info("🛑 SellIA Sellbot shutting down...")
    await stop_processor()
    stop_followup_loop()
    await close_db()
    if scheduler:
        await scheduler.close()
    logger.info("✅ All services closed")

app = FastAPI(
    title="SellIA Sellbot",
    version="1.0.0",
    lifespan=lifespan
)

allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://sellia-brain.vercel.app").split(",")]

# Rate limiter (simple in-memory)
class RateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.rpm = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, ip: str) -> bool:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        # Clean old requests
        self.requests[ip] = [t for t in self.requests[ip] if t > minute_ago]
        if len(self.requests[ip]) >= self.rpm:
            return False
        self.requests[ip].append(now)
        return True

rate_limiter = RateLimiter(requests_per_minute=100)

# Logging middleware (structured)
@app.middleware("http")
async def log_request(request: Request, call_next):
    import time
    from app.middleware.threat_intel import get_client_ip
    start_time = time.time()
    client_ip = get_client_ip(request)
    request.state.client_ip = client_ip

    # Rate limit check
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded: {client_ip} {request.method} {request.url.path}")
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

    response = await call_next(request)
    process_time = time.time() - start_time

    # Structured log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "client_ip": client_ip,
        "process_time_ms": round(process_time * 1000, 2)
    }
    logger.info(f"API | {log_entry}")

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Registrar routers
# v1 routes (current stable) — each wrapped so a single broken router
# (missing dependency, bad import) can never take the whole app down.
def _register(router_module, name: str) -> None:
    try:
        app.include_router(router_module.router)
        logger.info(f"✅ {name} router registered")
    except Exception as e:
        logger.error(f"❌ Failed to register {name} router: {e}", exc_info=True)

_register(leads_module, "leads")
_register(workflows_module, "workflows")
_register(lead_sources_module, "lead_sources")
_register(email_webhooks_module, "email_webhooks")
_register(progression_module, "progression")
_register(analytics_module, "analytics")
_register(attribution_module, "attribution")
_register(journeys_module, "journeys")
_register(compliance_module, "compliance")
_register(integrations_module, "integrations")
_register(sales_agents_module, "sales_agents")
_register(neural_networks_module, "neural_networks")
_register(sales_automation_module, "sales_automation")
_register(deal_intelligence_module, "deal_intelligence")
_register(sales_coaching_module, "sales_coaching")
_register(crm_collaboration_module, "crm_collaboration")
_register(sales_funnel_orchestration_module, "sales_funnel_orchestration")
_register(marketing_intelligence_module, "marketing_intelligence")
_register(accounting_intelligence_module, "accounting_intelligence")
_register(sales_operations_module, "sales_operations")

# Domain routers (Phase 2-5: Backend Intelligence)
def _register_domain_router(router_obj, name: str) -> None:
    try:
        app.include_router(router_obj)
        logger.info(f"✅ {name} router registered")
    except Exception as e:
        logger.error(f"❌ Failed to register {name} router: {e}", exc_info=True)

# Phase X6: FOMO Dynamics (Ultra-Potent Psychology Engine)
_register_domain_router(fomo_dynamics_router, "fomo_dynamics")

# Phase X7: Perception Engineering (Psychology-Driven Sales Agent)
_register_domain_router(perception_engineering_router, "perception_engineering")

# Phase X8: Auto-Marketing & Growth (SellIA Self-Promotion)
_register_domain_router(auto_marketing_router, "auto_marketing")

# Phase X9: AI User Intelligence (Deep Profiling)
_register_domain_router(user_intelligence_router, "user_intelligence")

# Phase X10: FOMO Generation (Personalized Scarcity)
_register_domain_router(fomo_generation_router, "fomo_generation")

# Phase X11: Loyalty & Retention (VIP Program)
_register_domain_router(loyalty_engine_router, "loyalty_engine")

# Phase X12: Conversion & Attraction (Multi-touch Closing)
_register_domain_router(conversion_engine_router, "conversion_engine")

# Acquisition Orchestrator (X9→X10→X12→X11 Integration)
_register_domain_router(acquisition_orchestrator_router, "acquisition_orchestrator")

# Instagram Automation (@sell_.ia + FeedIA synergy)
_register_domain_router(instagram_automation_router, "instagram_automation")

# Feedback Loop (Conversion data → X9 improvements)
_register_domain_router(feedback_loop_router, "feedback_loop")

# FOMO Intelligence (Escasez real / Prueba social / Exclusividad / Transparencia)
_register_domain_router(fomo_intelligence_router, "fomo_intelligence")

# ARCA Compliance (CUIT, Monotributo, INCOTERMS, NCM — datos reales)
_register_domain_router(arca_compliance_router, "arca_compliance")

# Platforms Integration (TikTok Shop real; resto queda como TODO histórico)
_register_domain_router(platforms_integration_router, "platforms_integration")

# Legacy redirect (v1 is default)
@app.get("/api/version", tags=["system"])
async def get_version():
    return {
        "version": "1.0.0",
        "status": "stable",
        "deprecation": None,
        "next_version": "2.0.0 (planned Q3 2024)"
    }

# ============================================================
# SALES SYSTEM PROMPT - 34 libros integrados
# ============================================================
SALES_SYSTEM_PROMPT = """Eres SellIA, un agente de ventas de IA con maestría en 34 libros de psicología de ventas, negocios y marketing.

### MARCOS DE REFERENCIA INTEGRADOS:

**PROSPECTING & COLD OUTREACH:**
- Efti (Cold Email): subject lines con curiosidad, personalización profunda, valor primero, social proof, CTA simple
- LinkedIn B2B (Konrath): decision makers, pain points, multi-threading, account-based selling

**SALES METHODOLOGY:**
- SPIN Selling (Rackham): Situation, Problem, Implication, Need-Payoff questions
- 10X Mindset (Cardone): Audacia, volumen, presión positiva, cierre agresivo pero ético
- Closing (Ziglar): 7 técnicas de cierre, manejar objeciones con empatía

**PSYCHOLOGY & INFLUENCE:**
- 7 Principios Cialdini: Reciprocidad, Compromiso, Prueba Social, Autoridad, Simpatía, Escasez, Urgencia
- Pre-suasión (Cialdini): Framing antes de pitch
- Irracionalidad (Ariely): Anclaje, relatividad, costo hundido
- Empatía (Carnegie): Escuchar, validar, conexión humana

**POSITIONING & DIFERENCIACIÓN:**
- Purple Cow (Godin): Ser notable, diferente, memorable
- Monopoly (Thiel): Crear categoría única, defensible
- Expert Secrets (Brunson): Posicionarse como authority, storytelling

**OFFER DESIGN & PRICING:**
- Offer Design (Hormozi): Value equation, stack, bonuses, urgency real
- Pricing Psychology (Poundstone): Anclajes, decoys, paquetes
- Direct Response (Kennedy): ROI focus, 80/20 rule, metricas

**FUNNELS & CONVERSION:**
- Funnel Hacking (Brunson): Squeeze page, sales page, order form, thank you page
- A/B Testing: Headlines, copy, calls to action
- Conversion Optimization (Saleh): Scarcity, social proof, testimonials

**RETENTION & EXPANSION:**
- NPS & Retention (Reichheld): Proactive engagement, loyalty loops
- Tiny Habits (Fogg): Behavior change, sticky features
- Customer Success (Mehta): Health scores, proactive outreach, upsell sequences

**NEGOTIATION:**
- Getting to Yes (Fisher): Win-win, BATNA, options generation
- Never Split the Difference (Voss): Mirroring, labels, tactical empathy

### TU COMPORTAMIENTO:

1. **Prospecting**: Busca pain points, propón soluciones claras, crea urgencia real
2. **Sales**: SPIN questions → descubre need → presenta offer con ROI visible
3. **Objeciones**: Reframe, social proof, alternative close, urgencia limitada
4. **Retention**: Onboarding rápido, health score check-in, cross-sell/upsell
5. **Analytics**: Pensa en métricas (conversion, CAC, LTV, churn), 80/20

### TONO:
- Audaz pero profesional
- Directo sin ser grosero
- ROI-focused
- Data-driven cuando sea posible
- Empatico pero orientado a resultados
"""

# ============================================================
# MODELOS
# ============================================================
class LeadProfile(BaseModel):
    name: str
    email: str
    company: str
    title: str
    pain_point: str
    industry: str

class EmailSequenceRequest(BaseModel):
    lead: LeadProfile
    offer: str
    sender_name: str = "SellIA"
    sender_email: str

class KnowledgeIngestRequest(BaseModel):
    content: str
    source: str

# ============================================================
# FUNCIONES CORE
# ============================================================
async def call_anthropic_api(system_prompt: str, user_message: str, retries: int = 3) -> str:
    """Llama a Claude API con retry logic."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    last_error = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 2048,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_message}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                if not data.get("content") or not isinstance(data["content"], list) or len(data["content"]) == 0:
                    raise ValueError(f"Invalid Anthropic response structure: {data}")
                return data["content"][0]["text"]
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = e
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:  # Retry only 5xx errors
                last_error = e
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            raise HTTPException(status_code=e.response.status_code, detail=str(e))

    raise HTTPException(status_code=503, detail=f"Anthropic API unavailable after {retries} attempts: {last_error}")

async def send_whatsapp_message(to: str, text: str, phone_number_id: str, token: str) -> dict:
    """Envía mensaje vía WhatsApp Graph API."""
    url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                params={"access_token": token},
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"body": text},
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error(f"WhatsApp API timeout for {to}")
        raise
    except httpx.HTTPError as e:
        logger.error(f"WhatsApp API error for {to}: {e}")
        raise

# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/")
async def root():
    return RedirectResponse(url="/api/ping")

@app.get("/api/ping")
async def ping():
    """Simple health check."""
    return {"status": "ok", "service": "SellIA Sellbot", "timestamp": datetime.now().isoformat()}

@app.get("/api/health", tags=["system"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependency status."""
    try:
        # Check database
        await db.execute(select(1))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "failed"

    # Check Redis
    try:
        if processor and processor.scheduler and processor.scheduler.redis:
            await processor.scheduler.redis.ping()
            redis_status = "ok"
        else:
            redis_status = "fallback"  # In-memory mode
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "failed"

    # Check processor
    try:
        processor_running = processor and processor.running
        processor_status = "ok" if processor_running else "stopped"
    except Exception as e:
        logger.error(f"Processor health check failed: {e}")
        processor_status = "failed"

    overall = "ok" if db_status == "ok" and processor_status == "ok" else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_status,
            "redis": redis_status,
            "processor": processor_status,
            "scheduler": "ok" if scheduler else "not_initialized"
        },
        "uptime_seconds": 0  # TODO: track from startup
    }

@app.get("/api/queue/dlq", tags=["monitoring"])
async def get_dead_letter_queue():
    """Get tasks that failed permanently (DLQ)."""
    try:
        if not scheduler or not scheduler.redis:
            return {"status": "not_available", "dlq_size": 0}

        dlq_size = await scheduler.redis.llen("sellia:dead-letter")
        dlq_tasks = await scheduler.redis.lrange("sellia:dead-letter", 0, 10)  # Last 10

        return {
            "status": "ok",
            "dlq_size": dlq_size,
            "recent_tasks": [json.loads(t) if isinstance(t, str) else t for t in dlq_tasks],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"DLQ query failed: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/api/v1/queue/stats")
async def queue_stats():
    """Get email queue statistics."""
    try:
        stats = await get_processor_stats()
        return {
            "status": "ok",
            "queue": stats
        }
    except Exception as e:
        logger.error(f"Queue stats error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/api/v1/queue/peek")
async def queue_peek(count: int = 5):
    """Peek at queue (non-destructive)."""
    global scheduler
    if not scheduler:
        return {"status": "error", "detail": "Scheduler not initialized"}

    try:
        tasks = await scheduler.peek_queue(count)
        return {
            "status": "ok",
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        logger.error(f"Queue peek error: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/api/v1/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    """Meta WhatsApp webhook - recibe y responde mensajes."""
    try:
        body = await request.json()

        # Meta verifica webhook con GET
        if request.method == "GET":
            token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
            verify_token = request.query_params.get("hub.verify_token", "")
            if verify_token == token:
                return int(request.query_params.get("hub.challenge", 0))
            return JSONResponse({"error": "Invalid token"}, status_code=403)

        # Procesa mensaje entrante
        messages = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
        if not messages:
            return JSONResponse({"status": "ok"})

        message = messages[0]
        from_number = message.get("from")
        message_text = message.get("text", {}).get("body", "")

        if not message_text:
            return JSONResponse({"status": "ok"})

        # Genera respuesta con IA
        response_text = await call_anthropic_api(
            system_prompt=SALES_SYSTEM_PROMPT,
            user_message=f"Cliente: {message_text}\n\nResponde como agente de ventas SellIA.",
        )

        # Envía respuesta
        phone_number_id = os.getenv("META_PHONE_NUMBER_ID", "")
        token = os.getenv("META_WHATSAPP_TOKEN", "")
        if phone_number_id and token:
            await send_whatsapp_message(from_number, response_text, phone_number_id, token)

        return JSONResponse({"status": "ok", "response_sent": True})
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

@app.post("/api/v1/sequences/cold-email")
async def generate_cold_email_sequence(req: EmailSequenceRequest):
    """Genera secuencia de 5 emails (Efti + Kennedy frameworks)."""
    try:
        prompt = f"""Genera una secuencia de 5 emails de prospecting para:

LEAD:
- Nombre: {req.lead.name}
- Email: {req.lead.email}
- Empresa: {req.lead.company}
- Título: {req.lead.title}
- Pain point: {req.lead.pain_point}
- Industria: {req.lead.industry}

OFFER: {req.offer}

Usa Efti (cold email) + Kennedy (80/20 ROI).
Retorna JSON array: [{"day": 1, "subject": "...", "body": "..."}, ...]
SOLO JSON, sin markdown."""

        response_json = await call_anthropic_api(
            system_prompt="Eres un copywriter experto. Devuelve SOLO JSON válido.",
            user_message=prompt,
        )

        emails = json.loads(response_json)
        return {
            "sequence_id": f"seq_{req.lead.email}",
            "lead": req.lead,
            "emails": emails,
            "status": "generated",
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse email sequence JSON")
    except Exception as e:
        logger.error(f"Email sequence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/knowledge/ingest")
async def ingest_knowledge(req: KnowledgeIngestRequest):
    """Ingesta PDFs/conocimientos para mejorar system prompt (v1: solo logging)."""
    try:
        # v1: Solo registra. v2: Mejorar system prompt dinámicamente
        logger.info(f"Knowledge ingested from {req.source}: {len(req.content)} chars")
        return {
            "status": "ingested",
            "source": req.source,
            "size": len(req.content),
            "message": "Knowledge received. System will be enhanced in v2.",
        }
    except Exception as e:
        logger.error(f"Knowledge ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
