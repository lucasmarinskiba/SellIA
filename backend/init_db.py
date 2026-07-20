import asyncio

# Import all models first so they register with Base.metadata
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.catalogs.models import CatalogItem
from app.domains.channels.models import ChannelConnection, Conversation, Message
from app.domains.subscriptions.models import SubscriptionPlan, Subscription, UserAPIKey, UsageTracking, PaymentTransaction, Invoice, UsageAlert
from app.domains.agents.models import AgentPersonality, AgentConfig, AgentConversation, AgentMessage
from app.domains.automations.models import Workflow, WorkflowExecution, EmailTemplate, EmailSequence, SequenceStep, ChatbotRule, GeneratedContent, ContentCalendar
from app.domains.crm.models import Pipeline, Deal, LeadScore, LeadActivity
from app.domains.orders.models import Order, RevenueEvent, PaymentIntegration
from app.domains.alerts.models import AlertRule, Alert, Recommendation
from app.domains.objectives.models import Department, BusinessObjective, KPI, KeyResult
from app.domains.retention.models import LoyaltyProgram, ReferralProgram, ReferralCode, ReferralUse, NpsCampaign, NpsResponse, CustomerSegment
from app.domains.bi.models import FunnelMetrics, CohortMetrics, ChurnPrediction, LtvPrediction, InsightAlert
from app.domains.finance.models import SalesInvoice, PaymentReminder, AccountsReceivableSnapshot, TaxConfig
from app.domains.computer_use.models import ComputerUseSession, ComputerUseStep, ComputerUseMessage
from app.domains.security.models import DataAccessLog, RolePermission, BusinessUserRole
try:
    from app.domains.security.models import UserLoginLog, SecurityWebhook, SecurityConfig, PushSubscription, UserSession, TwoFABackupCode, BreachCheckLog
except ImportError:
    pass

from app.core.database import engine, Base, AsyncSessionLocal
from sqlalchemy import text
from app.domains.subscriptions.services import create_default_plans
from app.domains.agents.services import AgentService
from app.domains.alerts.models import AlertRule, AlertRuleType, AlertSeverity
from app.core.rbac import seed_default_permissions


async def run_migration(label: str, sql: str):
    """Run a single migration in its own transaction so failures are isolated."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text(sql))
        print(f"Migración: {label} verificada.")
    except Exception as e:
        print(f"Nota: migración '{label}' skipped ({type(e).__name__}: {e})")


async def init_models():
    # Primero crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tablas creadas correctamente.")

    # Luego aplicar migraciones ad-hoc en transacciones separadas
    await run_migration(
        "api_key_fernet",
        "ALTER TABLE user_api_keys ADD COLUMN IF NOT EXISTS api_key_fernet TEXT"
    )
    await run_migration(
        "visual_data",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS visual_data JSONB"
    )
    await run_migration(
        "failed_login_attempts",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0"
    )
    await run_migration(
        "locked_until",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE"
    )
    await run_migration(
        "last_failed_login",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMP WITH TIME ZONE"
    )
    await run_migration(
        "is_superuser",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE"
    )
    await run_migration(
        "totp_secret",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(255)"
    )
    await run_migration(
        "is_2fa_enabled",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_2fa_enabled BOOLEAN DEFAULT FALSE"
    )
    await run_migration(
        "last_login_at",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE"
    )
    await run_migration(
        "last_device_fingerprint",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_device_fingerprint VARCHAR(64)"
    )
    await run_migration(
        "login_logs_geo",
        "ALTER TABLE user_login_logs ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION, ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION, ADD COLUMN IF NOT EXISTS city VARCHAR(100)"
    )
    await run_migration(
        "webhook_token",
        "ALTER TABLE channel_connections ADD COLUMN IF NOT EXISTS webhook_token VARCHAR(64) UNIQUE"
    )
    await run_migration(
        "webhook_token_not_null",
        "UPDATE channel_connections SET webhook_token = md5(random()::text || clock_timestamp()::text) WHERE webhook_token IS NULL"
    )
    await run_migration(
        "drop_channel_crm_fields",
        "ALTER TABLE channel_connections DROP COLUMN IF EXISTS lead_score, DROP COLUMN IF EXISTS stage, DROP COLUMN IF EXISTS deal_value, DROP COLUMN IF EXISTS estimated_close_date"
    )
    await run_migration(
        "messages_conversation_created_idx",
        "CREATE INDEX IF NOT EXISTS ix_messages_conversation_created ON messages (conversation_id, created_at)"
    )
    await run_migration(
        "security_config_geofencing",
        "ALTER TABLE security_config ADD COLUMN IF NOT EXISTS max_distance_km DOUBLE PRECISION, ADD COLUMN IF NOT EXISTS alert_on_geofence BOOLEAN DEFAULT TRUE, ADD COLUMN IF NOT EXISTS hibp_api_key VARCHAR(255), ADD COLUMN IF NOT EXISTS alert_on_breach BOOLEAN DEFAULT TRUE"
    )
    await run_migration(
        "two_fa_backup_codes",
        "CREATE TABLE IF NOT EXISTS two_fa_backup_codes (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, code_hash VARCHAR(255) NOT NULL, is_used BOOLEAN DEFAULT FALSE, used_at TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "breach_check_logs",
        "CREATE TABLE IF NOT EXISTS breach_check_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, email VARCHAR(255) NOT NULL, breaches_found INTEGER DEFAULT 0, breach_names TEXT, checked_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "idx_backup_codes_user",
        "CREATE INDEX IF NOT EXISTS idx_two_fa_backup_codes_user ON two_fa_backup_codes(user_id)"
    )
    await run_migration(
        "idx_breach_logs_user",
        "CREATE INDEX IF NOT EXISTS idx_breach_check_logs_user ON breach_check_logs(user_id)"
    )
    await run_migration(
        "alerts_metadata_rename",
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='alerts' AND column_name='metadata') THEN ALTER TABLE alerts RENAME COLUMN metadata TO alert_metadata; END IF; END $$"
    )
    await run_migration(
        "workflow_conversion_count",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS conversion_count INTEGER DEFAULT 0"
    )
    await run_migration(
        "email_sequence_counts",
        "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS sent_count INTEGER DEFAULT 0, ADD COLUMN IF NOT EXISTS opens_count INTEGER DEFAULT 0, ADD COLUMN IF NOT EXISTS clicks_count INTEGER DEFAULT 0"
    )
    await run_migration(
        "sequence_step_extra_data",
        "ALTER TABLE sequence_steps ADD COLUMN IF NOT EXISTS extra_data JSONB DEFAULT '{}'"
    )
    await run_migration(
        "sequence_subscriptions_table",
        "CREATE TABLE IF NOT EXISTS sequence_subscriptions (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), sequence_id UUID NOT NULL REFERENCES email_sequences(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, current_step_index INTEGER DEFAULT 0, started_at TIMESTAMP WITH TIME ZONE DEFAULT now(), last_sent_at TIMESTAMP WITH TIME ZONE, status VARCHAR(20) DEFAULT 'active', extra_data JSONB DEFAULT '{}', created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "sequence_subscriptions_idx_seq",
        "CREATE INDEX IF NOT EXISTS idx_sequence_subscriptions_seq ON sequence_subscriptions(sequence_id)"
    )
    await run_migration(
        "sequence_subscriptions_idx_conv",
        "CREATE INDEX IF NOT EXISTS idx_sequence_subscriptions_conv ON sequence_subscriptions(conversation_id)"
    )
    await run_migration(
        "sequence_email_logs_table",
        "CREATE TABLE IF NOT EXISTS sequence_email_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), subscription_id UUID NOT NULL REFERENCES sequence_subscriptions(id) ON DELETE CASCADE, sequence_id UUID NOT NULL REFERENCES email_sequences(id) ON DELETE CASCADE, step_id UUID NOT NULL REFERENCES sequence_steps(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, recipient_email VARCHAR(255) NOT NULL, subject VARCHAR(500), tracking_token VARCHAR(64) UNIQUE NOT NULL, sent_at TIMESTAMP WITH TIME ZONE, opened_at TIMESTAMP WITH TIME ZONE, clicked_at TIMESTAMP WITH TIME ZONE, status VARCHAR(20) DEFAULT 'pending', extra_data JSONB DEFAULT '{}', created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "sequence_email_logs_idx_token",
        "CREATE INDEX IF NOT EXISTS idx_sequence_email_logs_token ON sequence_email_logs(tracking_token)"
    )
    await run_migration(
        "sequence_email_logs_idx_sub",
        "CREATE INDEX IF NOT EXISTS idx_sequence_email_logs_sub ON sequence_email_logs(subscription_id)"
    )
    await run_migration(
        "subscription_mercadopago_payment_id",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS mercadopago_payment_id VARCHAR(100)"
    )
    await run_migration(
        "subscription_mercadopago_preapproval_id",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS mercadopago_preapproval_id VARCHAR(100)"
    )
    await run_migration(
        "workflow_variants_table",
        "CREATE TABLE IF NOT EXISTS workflow_variants (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE, business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, variant_name VARCHAR(100) NOT NULL, traffic_split INTEGER DEFAULT 50, actions JSONB DEFAULT '[]', execution_count INTEGER DEFAULT 0, conversion_count INTEGER DEFAULT 0, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "workflow_variants_idx",
        "CREATE INDEX IF NOT EXISTS idx_workflow_variants_workflow ON workflow_variants(workflow_id)"
    )
    await run_migration(
        "workflow_execution_variant_id",
        "ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS variant_id UUID REFERENCES workflow_variants(id) ON DELETE SET NULL"
    )
    await run_migration(
        "workflow_variants_is_control",
        "ALTER TABLE workflow_variants ADD COLUMN IF NOT EXISTS is_control BOOLEAN DEFAULT FALSE"
    )
    await run_migration(
        "agent_config_ai_auto_reply_enabled",
        "ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS ai_auto_reply_enabled BOOLEAN DEFAULT FALSE"
    )
    await run_migration(
        "agent_config_ai_auto_reply_personality_id",
        "ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS ai_auto_reply_personality_id UUID REFERENCES agent_personalities(id) ON DELETE SET NULL"
    )

    # Subscription multi-region & payment expansion
    await run_migration(
        "users_country_code",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS country_code VARCHAR(2) DEFAULT 'AR'"
    )
    await run_migration(
        "users_detected_country",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS detected_country VARCHAR(2)"
    )
    await run_migration(
        "users_preferred_currency",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_currency VARCHAR(3) DEFAULT 'ARS'"
    )
    await run_migration(
        "users_timezone",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'America/Argentina/Buenos_Aires'"
    )
    await run_migration(
        "users_tax_id",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS tax_id VARCHAR(20)"
    )
    await run_migration(
        "users_billing_address",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_address JSONB DEFAULT '{}'"
    )
    await run_migration(
        "users_payment_methods",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_methods JSONB DEFAULT '[]'"
    )
    await run_migration(
        "subscription_plans_latam_price",
        "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS price_monthly_latam_usd NUMERIC(10,2), ADD COLUMN IF NOT EXISTS price_yearly_latam_usd NUMERIC(10,2)"
    )
    await run_migration(
        "subscription_plans_cycle_options",
        "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS billing_cycle_options JSONB DEFAULT '[\"monthly\", \"yearly\"]', ADD COLUMN IF NOT EXISTS target_regions JSONB DEFAULT '[\"AR\", \"LATAM\", \"INTL\"]', ADD COLUMN IF NOT EXISTS trial_days INTEGER DEFAULT 14"
    )
    await run_migration(
        "subscriptions_billing_cycle",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR(10) DEFAULT 'monthly', ADD COLUMN IF NOT EXISTS payment_provider VARCHAR(20), ADD COLUMN IF NOT EXISTS payment_method_id VARCHAR(100), ADD COLUMN IF NOT EXISTS crypto_network VARCHAR(20), ADD COLUMN IF NOT EXISTS crypto_wallet_address VARCHAR(100)"
    )
    await run_migration(
        "subscriptions_stripe_ids",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100), ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(100)"
    )
    await run_migration(
        "subscriptions_billing_dates",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS next_billing_date TIMESTAMP WITH TIME ZONE, ADD COLUMN IF NOT EXISTS grace_period_end TIMESTAMP WITH TIME ZONE, ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN DEFAULT TRUE, ADD COLUMN IF NOT EXISTS invoice_data JSONB DEFAULT '{}', ADD COLUMN IF NOT EXISTS downgrade_to_plan_id UUID REFERENCES subscription_plans(id) ON DELETE SET NULL"
    )
    await run_migration(
        "payment_transactions_table",
        "CREATE TABLE IF NOT EXISTS payment_transactions (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL, plan_id UUID REFERENCES subscription_plans(id), amount NUMERIC(14,2) NOT NULL, currency VARCHAR(3) NOT NULL, provider VARCHAR(20) NOT NULL, provider_transaction_id VARCHAR(100), status VARCHAR(20) DEFAULT 'pending', crypto_network VARCHAR(20), crypto_from_address VARCHAR(100), crypto_tx_hash VARCHAR(100), crypto_confirmations INTEGER DEFAULT 0, billing_cycle VARCHAR(10), metadata JSONB DEFAULT '{}', error_message TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), completed_at TIMESTAMP WITH TIME ZONE)"
    )
    await run_migration(
        "payment_transactions_idx_user",
        "CREATE INDEX IF NOT EXISTS idx_payment_transactions_user ON payment_transactions(user_id)"
    )
    await run_migration(
        "payment_transactions_idx_status",
        "CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(status)"
    )
    await run_migration(
        "payment_transactions_idx_provider_tx",
        "CREATE INDEX IF NOT EXISTS idx_payment_transactions_provider_tx ON payment_transactions(provider_transaction_id)"
    )
    await run_migration(
        "invoices_table",
        "CREATE TABLE IF NOT EXISTS invoices (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, transaction_id UUID REFERENCES payment_transactions(id), invoice_number VARCHAR(50) UNIQUE NOT NULL, invoice_type VARCHAR(10) DEFAULT 'C', amount NUMERIC(14,2) NOT NULL, currency VARCHAR(3) NOT NULL, tax_amount NUMERIC(14,2) DEFAULT 0, total_amount NUMERIC(14,2) NOT NULL, plan_name VARCHAR(100), billing_period_start TIMESTAMP WITH TIME ZONE, billing_period_end TIMESTAMP WITH TIME ZONE, status VARCHAR(20) DEFAULT 'pending', afip_cae VARCHAR(20), afip_barcode TEXT, pdf_url TEXT, metadata JSONB DEFAULT '{}', created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), emitted_at TIMESTAMP WITH TIME ZONE)"
    )
    await run_migration(
        "invoices_idx_user",
        "CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices(user_id)"
    )
    await run_migration(
        "invoices_idx_number",
        "CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)"
    )
    await run_migration(
        "usage_alerts_table",
        "CREATE TABLE IF NOT EXISTS usage_alerts (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, metric_type VARCHAR(50) NOT NULL, threshold_percent INTEGER NOT NULL, sent_at TIMESTAMP WITH TIME ZONE DEFAULT now(), acknowledged BOOLEAN DEFAULT FALSE)"
    )
    await run_migration(
        "usage_alerts_idx",
        "CREATE INDEX IF NOT EXISTS idx_usage_alerts_user ON usage_alerts(user_id)"
    )
    await run_migration(
        "bank_transfer_payments_table",
        "CREATE TABLE IF NOT EXISTS bank_transfer_payments (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL, plan_id UUID REFERENCES subscription_plans(id), amount NUMERIC(14,2) NOT NULL, currency VARCHAR(3) NOT NULL, order_number VARCHAR(50) UNIQUE NOT NULL, alias VARCHAR(100), cbu VARCHAR(50), account_holder VARCHAR(255), instructions TEXT, status VARCHAR(20) DEFAULT 'pending', proof_image_url TEXT, paid_at TIMESTAMP WITH TIME ZONE, confirmed_by_admin_at TIMESTAMP WITH TIME ZONE, confirmed_by_admin_id UUID REFERENCES users(id) ON DELETE SET NULL, expires_at TIMESTAMP WITH TIME ZONE NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "bank_transfer_payments_idx",
        "CREATE INDEX IF NOT EXISTS idx_bank_transfer_user ON bank_transfer_payments(user_id)"
    )
    await run_migration(
        "cancellation_feedbacks_table",
        "CREATE TABLE IF NOT EXISTS cancellation_feedbacks (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL, reason_category VARCHAR(50) NOT NULL, reason_text TEXT, competitor_name TEXT, improvement_suggestion TEXT, rating_nps INTEGER, cancelled_at TIMESTAMP WITH TIME ZONE DEFAULT now(), created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "cancellation_feedbacks_idx",
        "CREATE INDEX IF NOT EXISTS idx_cancellation_user ON cancellation_feedbacks(user_id)"
    )

    # Shipments tables
    await run_migration(
        "shipment_configs_table",
        "CREATE TABLE IF NOT EXISTS shipment_configs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, carrier VARCHAR(50) NOT NULL, label VARCHAR(100), credentials JSONB DEFAULT '{}', is_test_mode BOOLEAN DEFAULT FALSE, is_active BOOLEAN DEFAULT TRUE, default_service_type VARCHAR(50), default_from_address JSONB DEFAULT '{}', created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "shipment_configs_idx",
        "CREATE INDEX IF NOT EXISTS idx_shipment_configs_business ON shipment_configs(business_id)"
    )
    await run_migration(
        "shipments_table",
        "CREATE TABLE IF NOT EXISTS shipments (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE, config_id UUID REFERENCES shipment_configs(id) ON DELETE SET NULL, carrier VARCHAR(50) NOT NULL, service_type VARCHAR(50) DEFAULT 'standard', status VARCHAR(50) DEFAULT 'pending', tracking_number VARCHAR(100), tracking_url TEXT, label_url TEXT, label_data TEXT, from_address JSONB DEFAULT '{}', to_address JSONB DEFAULT '{}', package JSONB DEFAULT '{}', shipping_cost NUMERIC(14,2), insurance_amount NUMERIC(14,2), declared_value NUMERIC(14,2), estimated_delivery_date TIMESTAMP WITH TIME ZONE, actual_delivery_date TIMESTAMP WITH TIME ZONE, picked_up_at TIMESTAMP WITH TIME ZONE, customer_notified_at TIMESTAMP WITH TIME ZONE, notification_channel VARCHAR(50), carrier_response JSONB DEFAULT '{}', last_tracking_check_at TIMESTAMP WITH TIME ZONE, notes TEXT, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "shipments_idx_business",
        "CREATE INDEX IF NOT EXISTS idx_shipments_business ON shipments(business_id)"
    )
    await run_migration(
        "shipments_idx_order",
        "CREATE INDEX IF NOT EXISTS idx_shipments_order ON shipments(order_id)"
    )
    await run_migration(
        "shipments_idx_tracking",
        "CREATE INDEX IF NOT EXISTS idx_shipments_tracking ON shipments(tracking_number)"
    )
    await run_migration(
        "shipment_tracking_events_table",
        "CREATE TABLE IF NOT EXISTS shipment_tracking_events (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), shipment_id UUID NOT NULL REFERENCES shipments(id) ON DELETE CASCADE, event_code VARCHAR(50), event_description VARCHAR(255) NOT NULL, location VARCHAR(255), carrier_status VARCHAR(100), event_at TIMESTAMP WITH TIME ZONE NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "shipment_tracking_events_idx",
        "CREATE INDEX IF NOT EXISTS idx_tracking_events_shipment ON shipment_tracking_events(shipment_id)"
    )

    # Service deliveries & appointments
    await run_migration(
        "service_deliveries_table",
        "CREATE TABLE IF NOT EXISTS service_deliveries (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE, catalog_item_id UUID REFERENCES catalog_items(id) ON DELETE SET NULL, conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL, scheduled_at TIMESTAMP WITH TIME ZONE, started_at TIMESTAMP WITH TIME ZONE, completed_at TIMESTAMP WITH TIME ZONE, cancelled_at TIMESTAMP WITH TIME ZONE, modality VARCHAR(50), solution_type VARCHAR(50), status VARCHAR(50) DEFAULT 'scheduled', location_address JSONB DEFAULT '{}', meeting_url TEXT, provider_notes TEXT, client_feedback TEXT, client_rating INTEGER, materials_used JSONB DEFAULT '[]', diagnosis JSONB DEFAULT '{}', follow_up_required BOOLEAN DEFAULT FALSE, follow_up_notes TEXT, reminders_sent JSONB DEFAULT '[]', estimated_duration_minutes INTEGER, actual_duration_minutes INTEGER, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "service_deliveries_idx_business",
        "CREATE INDEX IF NOT EXISTS idx_service_deliveries_business ON service_deliveries(business_id)"
    )
    await run_migration(
        "service_deliveries_idx_order",
        "CREATE INDEX IF NOT EXISTS idx_service_deliveries_order ON service_deliveries(order_id)"
    )
    await run_migration(
        "service_deliveries_idx_status",
        "CREATE INDEX IF NOT EXISTS idx_service_deliveries_status ON service_deliveries(status)"
    )
    await run_migration(
        "appointments_table",
        "CREATE TABLE IF NOT EXISTS appointments (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, service_delivery_id UUID REFERENCES service_deliveries(id) ON DELETE CASCADE, order_id UUID REFERENCES orders(id) ON DELETE SET NULL, conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL, client_name VARCHAR(255), client_email VARCHAR(255), client_phone VARCHAR(50), start_time TIMESTAMP WITH TIME ZONE NOT NULL, end_time TIMESTAMP WITH TIME ZONE NOT NULL, timezone VARCHAR(50) DEFAULT 'America/Argentina/Buenos_Aires', modality VARCHAR(50), solution_type VARCHAR(50), service_name VARCHAR(255), location_address JSONB DEFAULT '{}', meeting_url TEXT, status VARCHAR(50) DEFAULT 'pending', reminder_sent_at TIMESTAMP WITH TIME ZONE, confirmation_sent_at TIMESTAMP WITH TIME ZONE, confirmation_received_at TIMESTAMP WITH TIME ZONE, feedback_sent_at TIMESTAMP WITH TIME ZONE, feedback_received_at TIMESTAMP WITH TIME ZONE, provider_notes TEXT, preparation_notes TEXT, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "appointments_idx_business",
        "CREATE INDEX IF NOT EXISTS idx_appointments_business ON appointments(business_id)"
    )
    await run_migration(
        "appointments_idx_delivery",
        "CREATE INDEX IF NOT EXISTS idx_appointments_delivery ON appointments(service_delivery_id)"
    )
    await run_migration(
        "appointments_idx_start",
        "CREATE INDEX IF NOT EXISTS idx_appointments_start ON appointments(start_time)"
    )
    await run_migration(
        "appointments_idx_status",
        "CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)"
    )

    # Virtual Company tables — Objectives & KPIs
    await run_migration(
        "departments_table",
        "CREATE TABLE IF NOT EXISTS departments (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, name VARCHAR(100) NOT NULL, slug VARCHAR(50) NOT NULL, description TEXT, head_agent_personality_id UUID REFERENCES agent_personalities(id) ON DELETE SET NULL, color VARCHAR(20) DEFAULT '#3B82F6', icon VARCHAR(50) DEFAULT 'briefcase', config JSONB DEFAULT '{}', is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "departments_idx",
        "CREATE INDEX IF NOT EXISTS idx_departments_business ON departments(business_id)"
    )
    await run_migration(
        "business_objectives_table",
        "CREATE TABLE IF NOT EXISTS business_objectives (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, department_id UUID REFERENCES departments(id) ON DELETE SET NULL, name VARCHAR(200) NOT NULL, description TEXT, period VARCHAR(20) DEFAULT 'monthly', status VARCHAR(20) DEFAULT 'active', target_value NUMERIC(14,2) NOT NULL, current_value NUMERIC(14,2) DEFAULT 0, unit VARCHAR(50) DEFAULT 'ARS', start_date TIMESTAMP WITH TIME ZONE NOT NULL, end_date TIMESTAMP WITH TIME ZONE NOT NULL, linked_workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL, linked_channel_platform VARCHAR(50), alert_threshold_percent NUMERIC(5,2) DEFAULT 80, alert_channels JSONB DEFAULT '[]', extra_data JSONB DEFAULT '{}', is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "business_objectives_idx",
        "CREATE INDEX IF NOT EXISTS ix_objectives_business_status ON business_objectives(business_id, status)"
    )
    await run_migration(
        "kpis_table",
        "CREATE TABLE IF NOT EXISTS kpis (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, department_id UUID REFERENCES departments(id) ON DELETE SET NULL, objective_id UUID REFERENCES business_objectives(id) ON DELETE SET NULL, name VARCHAR(200) NOT NULL, slug VARCHAR(50) NOT NULL, description TEXT, metric_type VARCHAR(50) NOT NULL, aggregation VARCHAR(20) DEFAULT 'sum', target_value NUMERIC(14,2), current_value NUMERIC(14,2) DEFAULT 0, unit VARCHAR(50) DEFAULT 'count', period VARCHAR(20) DEFAULT 'monthly', period_start TIMESTAMP WITH TIME ZONE, period_end TIMESTAMP WITH TIME ZONE, data_source VARCHAR(100) NOT NULL, data_source_filter JSONB DEFAULT '{}', is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "kpis_idx",
        "CREATE INDEX IF NOT EXISTS ix_kpis_business_slug_period ON kpis(business_id, slug, period)"
    )
    await run_migration(
        "key_results_table",
        "CREATE TABLE IF NOT EXISTS key_results (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), objective_id UUID NOT NULL REFERENCES business_objectives(id) ON DELETE CASCADE, name VARCHAR(200) NOT NULL, description TEXT, target_value NUMERIC(14,2) NOT NULL, current_value NUMERIC(14,2) DEFAULT 0, unit VARCHAR(50) DEFAULT 'count', weight NUMERIC(3,2) DEFAULT 1.0, due_date TIMESTAMP WITH TIME ZONE, status VARCHAR(20) DEFAULT 'active', is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )

    # Virtual Company tables — Retention & Loyalty
    await run_migration(
        "loyalty_programs_table",
        "CREATE TABLE IF NOT EXISTS loyalty_programs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, name VARCHAR(200) NOT NULL, description TEXT, points_per_currency NUMERIC(10,2) DEFAULT 1, min_redeem_points INTEGER DEFAULT 100, welcome_bonus INTEGER DEFAULT 0, referral_bonus INTEGER DEFAULT 50, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "referral_programs_table",
        "CREATE TABLE IF NOT EXISTS referral_programs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, name VARCHAR(200) NOT NULL, description TEXT, reward_type VARCHAR(50) DEFAULT 'discount_percent', reward_value NUMERIC(10,2) DEFAULT 10, max_referrals_per_user INTEGER DEFAULT 10, expiry_days INTEGER DEFAULT 30, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "referral_codes_table",
        "CREATE TABLE IF NOT EXISTS referral_codes (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, program_id UUID NOT NULL REFERENCES referral_programs(id) ON DELETE CASCADE, conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL, code VARCHAR(50) NOT NULL UNIQUE, referrer_name VARCHAR(255), referrer_email VARCHAR(255), total_uses INTEGER DEFAULT 0, total_conversions INTEGER DEFAULT 0, total_revenue NUMERIC(14,2) DEFAULT 0, expires_at TIMESTAMP WITH TIME ZONE, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "referral_codes_idx",
        "CREATE INDEX IF NOT EXISTS idx_referral_codes_business ON referral_codes(business_id, code)"
    )
    await run_migration(
        "referral_uses_table",
        "CREATE TABLE IF NOT EXISTS referral_uses (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), code_id UUID NOT NULL REFERENCES referral_codes(id) ON DELETE CASCADE, business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, referred_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL, referred_email VARCHAR(255), status VARCHAR(20) DEFAULT 'pending', converted_order_id UUID REFERENCES orders(id) ON DELETE SET NULL, reward_given BOOLEAN DEFAULT FALSE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), converted_at TIMESTAMP WITH TIME ZONE)"
    )
    await run_migration(
        "nps_campaigns_table",
        "CREATE TABLE IF NOT EXISTS nps_campaigns (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, name VARCHAR(200) NOT NULL, trigger_type VARCHAR(50) DEFAULT 'post_purchase', trigger_days INTEGER DEFAULT 14, status VARCHAR(20) DEFAULT 'draft', question_text VARCHAR(500) DEFAULT '¿Qué tan probable es que recomiendes nuestro producto/servicio?', thank_you_message VARCHAR(500) DEFAULT '¡Gracias por tu feedback!', is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "nps_responses_table",
        "CREATE TABLE IF NOT EXISTS nps_responses (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), campaign_id UUID NOT NULL REFERENCES nps_campaigns(id) ON DELETE CASCADE, business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL, order_id UUID REFERENCES orders(id) ON DELETE SET NULL, score INTEGER NOT NULL, feedback_text TEXT, category VARCHAR(20), created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "nps_responses_idx",
        "CREATE INDEX IF NOT EXISTS ix_nps_responses_business_score ON nps_responses(business_id, score)"
    )
    await run_migration(
        "customer_segments_table",
        "CREATE TABLE IF NOT EXISTS customer_segments (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, segment VARCHAR(20) NOT NULL, r_score INTEGER DEFAULT 1, f_score INTEGER DEFAULT 1, m_score INTEGER DEFAULT 1, rfm_score INTEGER DEFAULT 111, last_order_at TIMESTAMP WITH TIME ZONE, total_orders INTEGER DEFAULT 0, total_revenue NUMERIC(14,2) DEFAULT 0, avg_order_value NUMERIC(14,2) DEFAULT 0, calculated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), is_active BOOLEAN DEFAULT TRUE)"
    )
    await run_migration(
        "customer_segments_idx",
        "CREATE INDEX IF NOT EXISTS ix_customer_segments_business_segment ON customer_segments(business_id, segment)"
    )

    # Virtual Company tables — Analytics & BI
    await run_migration(
        "funnel_metrics_table",
        "CREATE TABLE IF NOT EXISTS funnel_metrics (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, period VARCHAR(20) NOT NULL, period_type VARCHAR(10) NOT NULL, leads_count INTEGER DEFAULT 0, qualified_count INTEGER DEFAULT 0, deals_count INTEGER DEFAULT 0, orders_count INTEGER DEFAULT 0, repeat_orders_count INTEGER DEFAULT 0, conversion_lead_to_qualified NUMERIC(5,2) DEFAULT 0, conversion_qualified_to_deal NUMERIC(5,2) DEFAULT 0, conversion_deal_to_order NUMERIC(5,2) DEFAULT 0, conversion_order_to_repeat NUMERIC(5,2) DEFAULT 0, revenue_total NUMERIC(14,2) DEFAULT 0, avg_order_value NUMERIC(14,2) DEFAULT 0, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "funnel_metrics_idx",
        "CREATE INDEX IF NOT EXISTS ix_funnel_metrics_business_period ON funnel_metrics(business_id, period)"
    )
    await run_migration(
        "cohort_metrics_table",
        "CREATE TABLE IF NOT EXISTS cohort_metrics (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, cohort_month VARCHAR(7) NOT NULL, cohort_size INTEGER DEFAULT 0, period_months INTEGER DEFAULT 0, active_customers INTEGER DEFAULT 0, revenue NUMERIC(14,2) DEFAULT 0, retention_rate NUMERIC(5,2) DEFAULT 0, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "cohort_metrics_idx",
        "CREATE INDEX IF NOT EXISTS ix_cohort_metrics_business_cohort ON cohort_metrics(business_id, cohort_month, period_months)"
    )
    await run_migration(
        "churn_predictions_table",
        "CREATE TABLE IF NOT EXISTS churn_predictions (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, risk_level VARCHAR(20) NOT NULL, churn_probability NUMERIC(5,2) NOT NULL, predicted_churn_date TIMESTAMP WITH TIME ZONE, factors JSONB DEFAULT '[]', recommended_action VARCHAR(255), model_version VARCHAR(20) DEFAULT 'v1', is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "churn_predictions_idx",
        "CREATE INDEX IF NOT EXISTS ix_churn_predictions_business_risk ON churn_predictions(business_id, risk_level)"
    )
    await run_migration(
        "ltv_predictions_table",
        "CREATE TABLE IF NOT EXISTS ltv_predictions (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, predicted_ltv NUMERIC(14,2) NOT NULL, predicted_orders INTEGER DEFAULT 1, prediction_horizon_months INTEGER DEFAULT 12, confidence_score NUMERIC(5,2) DEFAULT 0.5, factors JSONB DEFAULT '[]', model_version VARCHAR(20) DEFAULT 'v1', is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "ltv_predictions_idx",
        "CREATE INDEX IF NOT EXISTS ix_ltv_predictions_business_ltv ON ltv_predictions(business_id, predicted_ltv)"
    )
    await run_migration(
        "insight_alerts_table",
        "CREATE TABLE IF NOT EXISTS insight_alerts (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, insight_type VARCHAR(50) NOT NULL, severity VARCHAR(20) DEFAULT 'info', title VARCHAR(255) NOT NULL, description TEXT, metric_name VARCHAR(100), metric_change_percent NUMERIC(7,2), recommended_action TEXT, action_taken BOOLEAN DEFAULT FALSE, action_result TEXT, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "insight_alerts_idx",
        "CREATE INDEX IF NOT EXISTS ix_insight_alerts_business_type ON insight_alerts(business_id, insight_type)"
    )

    # PII Column Encryption — alter sensitive columns to TEXT for encrypted storage
    await run_migration(
        "users_tax_id_to_text",
        "ALTER TABLE users ALTER COLUMN tax_id TYPE TEXT"
    )
    await run_migration(
        "users_billing_address_to_text",
        "ALTER TABLE users ALTER COLUMN billing_address TYPE TEXT"
    )
    await run_migration(
        "users_payment_methods_to_text",
        "ALTER TABLE users ALTER COLUMN payment_methods TYPE TEXT"
    )
    await run_migration(
        "sales_invoices_customer_pii_to_text",
        "ALTER TABLE sales_invoices ALTER COLUMN customer_name TYPE TEXT, ALTER COLUMN customer_email TYPE TEXT, ALTER COLUMN customer_phone TYPE TEXT"
    )
    await run_migration(
        "orders_customer_pii_to_text",
        "ALTER TABLE orders ALTER COLUMN customer_name TYPE TEXT, ALTER COLUMN customer_email TYPE TEXT, ALTER COLUMN customer_phone TYPE TEXT"
    )
    await run_migration(
        "tax_configs_tax_id_to_text",
        "ALTER TABLE tax_configs ALTER COLUMN tax_id_number TYPE TEXT"
    )

    # Security — Data Access Audit Log & RBAC
    await run_migration(
        "data_access_logs_table",
        "CREATE TABLE IF NOT EXISTS data_access_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID REFERENCES users(id) ON DELETE SET NULL, business_id UUID REFERENCES businesses(id) ON DELETE SET NULL, action VARCHAR(20) NOT NULL, table_name VARCHAR(100) NOT NULL, record_id VARCHAR(36), field_name VARCHAR(100), ip_address VARCHAR(45), user_agent TEXT, request_path VARCHAR(255), created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "data_access_logs_idx_user_business",
        "CREATE INDEX IF NOT EXISTS ix_data_access_logs_user_business ON data_access_logs(user_id, business_id)"
    )
    await run_migration(
        "data_access_logs_idx_table_action",
        "CREATE INDEX IF NOT EXISTS ix_data_access_logs_table_action ON data_access_logs(table_name, action)"
    )
    await run_migration(
        "role_permissions_table",
        "CREATE TABLE IF NOT EXISTS role_permissions (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), role VARCHAR(50) NOT NULL, resource VARCHAR(100) NOT NULL, action VARCHAR(20) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "role_permissions_idx_role_resource",
        "CREATE INDEX IF NOT EXISTS ix_role_permissions_role_resource ON role_permissions(role, resource)"
    )
    await run_migration(
        "business_user_roles_table",
        "CREATE TABLE IF NOT EXISTS business_user_roles (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, role VARCHAR(50) DEFAULT 'viewer', invited_by UUID REFERENCES users(id) ON DELETE SET NULL, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "business_user_roles_idx_user_business",
        "CREATE INDEX IF NOT EXISTS ix_business_user_roles_user_business ON business_user_roles(user_id, business_id)"
    )

    # Data Retention Policies & Logs
    await run_migration(
        "data_retention_policies_table",
        "CREATE TABLE IF NOT EXISTS data_retention_policies (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID REFERENCES businesses(id) ON DELETE CASCADE, table_name VARCHAR(100) NOT NULL, retention_days INTEGER NOT NULL DEFAULT 365, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "data_retention_policies_idx_business_table",
        "CREATE INDEX IF NOT EXISTS ix_data_retention_policies_business_table ON data_retention_policies(business_id, table_name)"
    )
    await run_migration(
        "data_retention_logs_table",
        "CREATE TABLE IF NOT EXISTS data_retention_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), policy_id UUID REFERENCES data_retention_policies(id) ON DELETE SET NULL, table_name VARCHAR(100) NOT NULL, records_deleted INTEGER DEFAULT 0, started_at TIMESTAMP WITH TIME ZONE DEFAULT now(), completed_at TIMESTAMP WITH TIME ZONE, status VARCHAR(20) DEFAULT 'success', error_message TEXT)"
    )

    # Secret Rotation Logs
    await run_migration(
        "secret_rotation_logs_table",
        "CREATE TABLE IF NOT EXISTS secret_rotation_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID REFERENCES businesses(id) ON DELETE SET NULL, secret_type VARCHAR(50) NOT NULL, target_id VARCHAR(36), old_value_hash VARCHAR(255), new_value_hash VARCHAR(255), rotated_by UUID REFERENCES users(id) ON DELETE SET NULL, status VARCHAR(20) DEFAULT 'success', error_message TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "secret_rotation_logs_idx_business",
        "CREATE INDEX IF NOT EXISTS ix_secret_rotation_logs_business ON secret_rotation_logs(business_id, secret_type)"
    )

    # Auto IP Blocklist
    await run_migration(
        "blocked_ips_table",
        "CREATE TABLE IF NOT EXISTS blocked_ips (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), ip_address VARCHAR(45) NOT NULL UNIQUE, reason VARCHAR(100) NOT NULL, blocked_until TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "blocked_ips_idx_ip",
        "CREATE INDEX IF NOT EXISTS ix_blocked_ips_ip ON blocked_ips(ip_address)"
    )

    # Computer Use Agents
    await run_migration(
        "computer_use_sessions_table",
        "CREATE TABLE IF NOT EXISTS computer_use_sessions (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, business_id UUID REFERENCES businesses(id) ON DELETE CASCADE, task_description TEXT NOT NULL, status VARCHAR(20) DEFAULT 'pending', current_url VARCHAR(2048), result_data JSONB DEFAULT '{}', error_message TEXT, total_steps INTEGER DEFAULT 0, started_at TIMESTAMP WITH TIME ZONE, completed_at TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "computer_use_sessions_idx_user",
        "CREATE INDEX IF NOT EXISTS idx_computer_use_sessions_user ON computer_use_sessions(user_id)"
    )
    await run_migration(
        "computer_use_steps_table",
        "CREATE TABLE IF NOT EXISTS computer_use_steps (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), session_id UUID NOT NULL REFERENCES computer_use_sessions(id) ON DELETE CASCADE, step_number INTEGER NOT NULL, screenshot_path VARCHAR(512), llm_prompt TEXT, llm_response TEXT, action_type VARCHAR(30) NOT NULL, action_params JSONB DEFAULT '{}', executed_at TIMESTAMP WITH TIME ZONE, execution_result TEXT, execution_ms INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "computer_use_steps_idx_session",
        "CREATE INDEX IF NOT EXISTS idx_computer_use_steps_session ON computer_use_steps(session_id, step_number)"
    )
    await run_migration(
        "computer_use_messages_table",
        "CREATE TABLE IF NOT EXISTS computer_use_messages (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), session_id UUID NOT NULL REFERENCES computer_use_sessions(id) ON DELETE CASCADE, role VARCHAR(10) NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "computer_use_messages_idx_session",
        "CREATE INDEX IF NOT EXISTS idx_computer_use_messages_session ON computer_use_messages(session_id, created_at)"
    )

    # Idempotency Keys
    await run_migration(
        "idempotency_keys_table",
        "CREATE TABLE IF NOT EXISTS idempotency_keys (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), key VARCHAR(64) NOT NULL UNIQUE, resource VARCHAR(50) NOT NULL, response_body TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "idempotency_keys_idx_resource_created",
        "CREATE INDEX IF NOT EXISTS ix_idempotency_keys_resource_created ON idempotency_keys(resource, created_at)"
    )

    # Webhook Event Deduplication
    await run_migration(
        "webhook_event_logs_table",
        "CREATE TABLE IF NOT EXISTS webhook_event_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), provider VARCHAR(20) NOT NULL, event_id VARCHAR(100) NOT NULL, event_type VARCHAR(50) NOT NULL, processed_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "webhook_event_logs_idx_provider_event",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_webhook_event_logs_provider_event ON webhook_event_logs(provider, event_id)"
    )

    # === Autopilot 24/7 Engine ===
    await run_migration(
        "autopilot_configs_table",
        "CREATE TABLE IF NOT EXISTS autopilot_configs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE UNIQUE, auto_qualify_leads BOOLEAN DEFAULT FALSE, auto_move_deals BOOLEAN DEFAULT FALSE, auto_send_followups BOOLEAN DEFAULT FALSE, auto_close_deals BOOLEAN DEFAULT FALSE, auto_create_orders BOOLEAN DEFAULT FALSE, auto_request_reviews BOOLEAN DEFAULT FALSE, auto_activate_recovery_workflows BOOLEAN DEFAULT FALSE, auto_escalate_to_human BOOLEAN DEFAULT TRUE, approval_threshold_amount NUMERIC(14,2) DEFAULT 5000, max_daily_auto_messages INTEGER DEFAULT 50, max_daily_auto_closes INTEGER DEFAULT 10, max_daily_auto_orders INTEGER DEFAULT 10, human_escalation_channels JSONB DEFAULT '[]', escalation_email VARCHAR(255), escalation_whatsapp VARCHAR(100), is_active BOOLEAN DEFAULT FALSE, is_paused BOOLEAN DEFAULT FALSE, paused_reason TEXT, paused_at TIMESTAMP WITH TIME ZONE, require_ai_explanation BOOLEAN DEFAULT TRUE, explanation_language VARCHAR(10) DEFAULT 'es', created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "autopilot_configs_idx",
        "CREATE INDEX IF NOT EXISTS ix_autopilot_configs_business_active ON autopilot_configs(business_id, is_active)"
    )
    await run_migration(
        "autopilot_action_logs_table",
        "CREATE TABLE IF NOT EXISTS autopilot_action_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, action_type VARCHAR(50) NOT NULL, entity_type VARCHAR(50) NOT NULL, entity_id UUID NOT NULL, reason TEXT NOT NULL, ai_explanation TEXT, confidence_score INTEGER DEFAULT 0, context_data JSONB DEFAULT '{}', status VARCHAR(20) DEFAULT 'executed', error_message TEXT, requires_approval BOOLEAN DEFAULT FALSE, approved_at TIMESTAMP WITH TIME ZONE, approved_by_user_id UUID, rejected_at TIMESTAMP WITH TIME ZONE, rejected_reason TEXT, revenue_impact NUMERIC(14,2), created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), executed_at TIMESTAMP WITH TIME ZONE)"
    )
    await run_migration(
        "autopilot_logs_idx",
        "CREATE INDEX IF NOT EXISTS ix_autopilot_logs_business_status ON autopilot_action_logs(business_id, status)"
    )
    await run_migration(
        "autopilot_logs_idx_created",
        "CREATE INDEX IF NOT EXISTS ix_autopilot_logs_business_created ON autopilot_action_logs(business_id, created_at)"
    )
    await run_migration(
        "autopilot_logs_idx_entity",
        "CREATE INDEX IF NOT EXISTS ix_autopilot_logs_entity ON autopilot_action_logs(entity_type, entity_id)"
    )
    await run_migration(
        "autopilot_daily_reports_table",
        "CREATE TABLE IF NOT EXISTS autopilot_daily_reports (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, report_date TIMESTAMP WITH TIME ZONE NOT NULL, leads_contacted INTEGER DEFAULT 0, deals_moved INTEGER DEFAULT 0, deals_closed INTEGER DEFAULT 0, orders_created INTEGER DEFAULT 0, messages_sent INTEGER DEFAULT 0, sequences_started INTEGER DEFAULT 0, workflows_activated INTEGER DEFAULT 0, revenue_generated NUMERIC(14,2) DEFAULT 0, deals_value_closed NUMERIC(14,2) DEFAULT 0, actions_escalated INTEGER DEFAULT 0, actions_pending_approval INTEGER DEFAULT 0, actions_rejected INTEGER DEFAULT 0, ai_summary TEXT, highlights JSONB DEFAULT '[]', created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "autopilot_reports_idx",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_autopilot_reports_business_date ON autopilot_daily_reports(business_id, report_date)"
    )

    # === Smart Outreach Cadence ===
    await run_migration(
        "contact_fatigue_scores_table",
        "CREATE TABLE IF NOT EXISTS contact_fatigue_scores (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE UNIQUE, total_contacts_last_7d INTEGER DEFAULT 0, total_contacts_last_30d INTEGER DEFAULT 0, contacts_by_channel JSONB DEFAULT '{}', last_contact_at TIMESTAMP WITH TIME ZONE, last_response_at TIMESTAMP WITH TIME ZONE, consecutive_no_replies INTEGER DEFAULT 0, fatigue_level VARCHAR(20) DEFAULT 'relaxed', recommended_cooldown_until TIMESTAMP WITH TIME ZONE, ai_recommendation TEXT, recommended_channel VARCHAR(50), recommended_message_type VARCHAR(50), created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "fatigue_scores_idx",
        "CREATE INDEX IF NOT EXISTS ix_fatigue_business_level ON contact_fatigue_scores(business_id, fatigue_level)"
    )
    await run_migration(
        "fatigue_scores_idx_cooldown",
        "CREATE INDEX IF NOT EXISTS ix_fatigue_cooldown ON contact_fatigue_scores(recommended_cooldown_until)"
    )
    await run_migration(
        "outreach_cadence_rules_table",
        "CREATE TABLE IF NOT EXISTS outreach_cadence_rules (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE UNIQUE, max_messages_per_week INTEGER DEFAULT 3, max_messages_per_channel_per_week INTEGER DEFAULT 2, min_hours_between_contacts INTEGER DEFAULT 24, cooldown_after_no_reply_days INTEGER DEFAULT 3, cooldown_after_no_reply_count INTEGER DEFAULT 3, long_cooldown_days INTEGER DEFAULT 14, channel_priority JSONB DEFAULT '[]', respect_local_hours BOOLEAN DEFAULT TRUE, allowed_hours_start INTEGER DEFAULT 9, allowed_hours_end INTEGER DEFAULT 20, avoid_weekends BOOLEAN DEFAULT FALSE, hot_lead_override BOOLEAN DEFAULT TRUE, hot_lead_max_per_week INTEGER DEFAULT 5, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "outreach_logs_table",
        "CREATE TABLE IF NOT EXISTS outreach_logs (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, channel VARCHAR(50) NOT NULL, message_type VARCHAR(50) NOT NULL, cadence_step INTEGER DEFAULT 1, message_content TEXT, workflow_execution_id UUID, sequence_step_id UUID, status VARCHAR(20) DEFAULT 'sent', sent_at TIMESTAMP WITH TIME ZONE DEFAULT now(), delivered_at TIMESTAMP WITH TIME ZONE, read_at TIMESTAMP WITH TIME ZONE, responded_at TIMESTAMP WITH TIME ZONE, response_type VARCHAR(50), response_content TEXT, ai_generated BOOLEAN DEFAULT FALSE, ai_prompt_summary TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "outreach_logs_idx_conv",
        "CREATE INDEX IF NOT EXISTS ix_outreach_logs_conv_sent ON outreach_logs(conversation_id, sent_at)"
    )
    await run_migration(
        "outreach_logs_idx_business_channel",
        "CREATE INDEX IF NOT EXISTS ix_outreach_logs_business_channel ON outreach_logs(business_id, channel)"
    )

    # === Customer Health Score (Churn Prevention) ===
    await run_migration(
        "health_score_records_table",
        "CREATE TABLE IF NOT EXISTS health_score_records (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE UNIQUE, health_score INTEGER DEFAULT 100, trend VARCHAR(20) DEFAULT 'stable', churn_risk_level VARCHAR(20) DEFAULT 'none', recommended_action TEXT, last_order_days INTEGER DEFAULT 0, engagement_score INTEGER DEFAULT 0, nps_score INTEGER, support_ticket_count INTEGER DEFAULT 0, calculated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "health_scores_idx",
        "CREATE INDEX IF NOT EXISTS ix_health_scores_business_risk ON health_score_records(business_id, churn_risk_level)"
    )
    await run_migration(
        "health_score_histories_table",
        "CREATE TABLE IF NOT EXISTS health_score_histories (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, health_score INTEGER DEFAULT 100, trend VARCHAR(20) DEFAULT 'stable', churn_risk_level VARCHAR(20) DEFAULT 'none', calculated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "health_histories_idx",
        "CREATE INDEX IF NOT EXISTS ix_health_histories_conv_date ON health_score_histories(conversation_id, calculated_at)"
    )

    # === Message Intelligence & Intent Detection ===
    await run_migration(
        "message_analyses_table",
        "CREATE TABLE IF NOT EXISTS message_analyses (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE UNIQUE, sentiment_score NUMERIC(4,3) DEFAULT 0, sentiment_label VARCHAR(20) DEFAULT 'neutral', intent_type VARCHAR(50) DEFAULT 'neutral', intent_confidence NUMERIC(4,3) DEFAULT 0, objections_detected JSONB DEFAULT '[]', pain_points_detected JSONB DEFAULT '[]', buying_signals_detected JSONB DEFAULT '[]', urgency_level VARCHAR(20) DEFAULT 'low', language_detected VARCHAR(10) DEFAULT 'es', key_entities JSONB DEFAULT '{}', recommended_action VARCHAR(50), recommended_personality VARCHAR(50), raw_analysis JSONB DEFAULT '{}', created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "message_analyses_idx",
        "CREATE INDEX IF NOT EXISTS ix_message_analyses_business_intent ON message_analyses(business_id, intent_type)"
    )
    await run_migration(
        "message_analyses_idx_conv",
        "CREATE INDEX IF NOT EXISTS ix_message_analyses_conversation ON message_analyses(conversation_id, created_at)"
    )
    await run_migration(
        "conversation_intelligences_table",
        "CREATE TABLE IF NOT EXISTS conversation_intelligences (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE UNIQUE, overall_sentiment_trend VARCHAR(20) DEFAULT 'stable', average_sentiment_score NUMERIC(4,3) DEFAULT 0, dominant_intent VARCHAR(50) DEFAULT 'neutral', buying_readiness_score INTEGER DEFAULT 0, objection_history JSONB DEFAULT '[]', churn_risk_signals_count INTEGER DEFAULT 0, next_best_action VARCHAR(50), next_best_action_reason TEXT, total_messages_analyzed INTEGER DEFAULT 0, positive_messages_count INTEGER DEFAULT 0, negative_messages_count INTEGER DEFAULT 0, buying_signals_count INTEGER DEFAULT 0, updated_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "conv_intel_idx",
        "CREATE INDEX IF NOT EXISTS ix_conv_intel_business_readiness ON conversation_intelligences(business_id, buying_readiness_score)"
    )

    # === Notification Delivery ===
    await run_migration(
        "notification_deliveries_table",
        "CREATE TABLE IF NOT EXISTS notification_deliveries (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, channel VARCHAR(20) NOT NULL, priority VARCHAR(20) NOT NULL, notification_type VARCHAR(50) NOT NULL, subject VARCHAR(255), message TEXT NOT NULL, message_short VARCHAR(500), status VARCHAR(20) DEFAULT 'pending', sent_at TIMESTAMP WITH TIME ZONE, delivered_at TIMESTAMP WITH TIME ZONE, read_at TIMESTAMP WITH TIME ZONE, error_message TEXT, context_data JSONB DEFAULT '{}', created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "notifications_idx",
        "CREATE INDEX IF NOT EXISTS ix_notifications_user_status ON notification_deliveries(user_id, status)"
    )

    # === Optimization Experiments ===
    await run_migration(
        "optimization_experiments_table",
        "CREATE TABLE IF NOT EXISTS optimization_experiments (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, name VARCHAR(200) NOT NULL, hypothesis TEXT NOT NULL, target_metric VARCHAR(50) NOT NULL, variant_a_name VARCHAR(100) DEFAULT 'Control', variant_a_config JSONB DEFAULT '{}', variant_b_name VARCHAR(100) DEFAULT 'Treatment', variant_b_config JSONB DEFAULT '{}', status VARCHAR(20) DEFAULT 'running', sample_size_target INTEGER DEFAULT 100, confidence_threshold NUMERIC(4,3) DEFAULT 0.95, started_at TIMESTAMP WITH TIME ZONE DEFAULT now(), completed_at TIMESTAMP WITH TIME ZONE, winner_variant VARCHAR(10), created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )
    await run_migration(
        "optimization_results_table",
        "CREATE TABLE IF NOT EXISTS optimization_results (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), experiment_id UUID NOT NULL REFERENCES optimization_experiments(id) ON DELETE CASCADE, business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, variant_a_conversions INTEGER DEFAULT 0, variant_a_total INTEGER DEFAULT 0, variant_a_rate NUMERIC(5,4) DEFAULT 0, variant_b_conversions INTEGER DEFAULT 0, variant_b_total INTEGER DEFAULT 0, variant_b_rate NUMERIC(5,4) DEFAULT 0, improvement_percent NUMERIC(7,2) DEFAULT 0, is_statistically_significant BOOLEAN DEFAULT FALSE, p_value NUMERIC(6,5), applied_at TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now())"
    )

    # PostgreSQL Row-Level Security (RLS) — deny-by-default on critical tables
    rls_tables = [
        "conversations", "orders", "sales_invoices", "payment_reminders",
        "departments", "business_objectives", "kpis",
        "funnel_metrics", "cohort_metrics", "churn_predictions", "ltv_predictions",
        "insight_alerts", "customer_segments", "referral_codes", "referral_uses",
        "nps_campaigns", "nps_responses", "service_deliveries", "appointments",
        "shipments", "sequence_subscriptions", "sequence_email_logs",
    ]
    for tbl in rls_tables:
        await run_migration(f"rls_enable_{tbl}", f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")
        await run_migration(
            f"rls_policy_drop_{tbl}",
            f"DROP POLICY IF EXISTS business_isolation ON {tbl}"
        )
        # RLS policy: if app.current_business_id is set, enforce it; otherwise permissive (migration/admin)
        await run_migration(
            f"rls_policy_{tbl}",
            f"""CREATE POLICY business_isolation ON {tbl} FOR ALL TO PUBLIC USING (
                COALESCE(current_setting('app.current_business_id', true), '') = ''
                OR business_id = current_setting('app.current_business_id', true)::uuid
            )"""
        )

    # Create default subscription plans
    async with AsyncSessionLocal() as session:
        try:
            await create_default_plans(session)
            print("Planes de suscripción por defecto creados.")
        except Exception:
            await session.rollback()
            print("Planes de suscripción ya existen. Skipping.")

        # Seed agent personalities
        try:
            agent_service = AgentService(session)
            await agent_service.seed_personalities()
            print("Personalidades de agentes sembradas.")
        except Exception as e:
            await session.rollback()
            print(f"Agent personalities seed error (may already exist): {e}")

        # Seed default alert rules for each business
        try:
            await seed_default_alert_rules(session)
        except Exception as e:
            await session.rollback()
            print(f"Alert rules seed error: {e}")


async def seed_default_alert_rules(session):
    """Create default alert rules for every active business."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await session.execute(select(Business).where(Business.is_active == True))
    businesses = result.scalars().all()

    default_rules = [
        {
            "name": "Lead caliente sin deal",
            "rule_type": AlertRuleType.HOT_LEAD_NO_DEAL,
            "severity": AlertSeverity.WARNING,
            "config": {},
            "channels": ["in_app"],
            "cooldown_minutes": 360,
            "max_alerts_per_day": 5,
        },
        {
            "name": "Deal estancado",
            "rule_type": AlertRuleType.DEAL_STALLED,
            "severity": AlertSeverity.WARNING,
            "config": {"days": 3},
            "channels": ["in_app"],
            "cooldown_minutes": 1440,
            "max_alerts_per_day": 3,
        },
        {
            "name": "Carrito abandonado",
            "rule_type": AlertRuleType.CART_ABANDONED,
            "severity": AlertSeverity.INFO,
            "config": {"days": 2},
            "channels": ["in_app"],
            "cooldown_minutes": 1440,
            "max_alerts_per_day": 5,
        },
    ]

    created_count = 0
    for business in businesses:
        for rule_data in default_rules:
            # Check if rule already exists for this business
            existing = await session.execute(
                select(AlertRule).where(
                    AlertRule.business_id == business.id,
                    AlertRule.rule_type == rule_data["rule_type"],
                    AlertRule.is_active == True,
                )
            )
            if existing.scalar_one_or_none():
                continue
            rule = AlertRule(
                business_id=business.id,
                name=rule_data["name"],
                rule_type=rule_data["rule_type"],
                severity=rule_data["severity"],
                config=rule_data["config"],
                channels=rule_data["channels"],
                cooldown_minutes=rule_data["cooldown_minutes"],
                max_alerts_per_day=rule_data["max_alerts_per_day"],
            )
            session.add(rule)
            created_count += 1

    if created_count > 0:
        await session.commit()
        print(f"Reglas de alerta por defecto creadas: {created_count}")
    else:
        print("Reglas de alerta ya existen. Skipping.")

    # Seed default RBAC permissions
    try:
        await seed_default_permissions(session)
        print("Permisos RBAC por defecto creados.")
    except Exception as e:
        await session.rollback()
        print(f"RBAC seed error: {e}")


if __name__ == "__main__":
    asyncio.run(init_models())
