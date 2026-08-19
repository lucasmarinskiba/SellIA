import sys
import os

# Add backend to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# Import app database and models
from app.core.database import Base
from app.core.config import get_settings

# Import ALL model modules so they register with Base.metadata.
# This is critical for autogenerate to work.
#
# Each import is isolated: a broken/incomplete domain module must never
# block `alembic upgrade` for every other domain. Failures are logged to
# stderr (visible in Render job logs) so they stay discoverable without
# taking down migrations for the rest of the app.
import importlib
import traceback


def _try_import_models(module_path: str, *, names: list[str] | None = None) -> None:
    try:
        module = importlib.import_module(module_path)
        if names:
            for name in names:
                getattr(module, name)
    except Exception:
        print(f"[alembic/env.py] WARNING: skipped model import {module_path!r} due to error:", file=sys.stderr)
        traceback.print_exc()


_try_import_models("app.domains.users.models")
_try_import_models("app.domains.businesses.models")
_try_import_models("app.domains.catalogs.models")
_try_import_models("app.domains.channels.models")
_try_import_models("app.domains.orders.models")
_try_import_models("app.domains.subscriptions.models")
_try_import_models("app.domains.agents.models")
_try_import_models("app.domains.agents.prompt_optimizer", names=["ConversationOutcome"])
_try_import_models("app.domains.agents.models_reflection", names=["AgentReflection", "ChainOfThoughtLog"])
_try_import_models("app.domains.agents.models_causal", names=["ObjectionPattern", "CausalAnalysis"])
_try_import_models("app.domains.automations.models")
_try_import_models("app.domains.analytics.models")
_try_import_models("app.domains.notifications.models")
_try_import_models("app.domains.security.models")
_try_import_models("app.domains.support.models")
_try_import_models("app.domains.shipments.models")
_try_import_models("app.domains.services.models")
_try_import_models("app.domains.crm.models")
_try_import_models("app.domains.computer_use.models")
_try_import_models("app.domains.computer_use.models_extended")
_try_import_models("app.domains.intelligence.models")
_try_import_models("app.domains.retention.models")
_try_import_models("app.domains.outreach.models")
_try_import_models("app.domains.autopilot.models")
_try_import_models("app.domains.finance.models")
_try_import_models("app.domains.bi.models")
_try_import_models("app.domains.objectives.models")
_try_import_models("app.domains.feedback.models")
_try_import_models("app.domains.alerts.models")
_try_import_models("app.domains.optimization.models")
_try_import_models("app.domains.growth.models")
_try_import_models("app.domains.gamification.models")
_try_import_models("app.domains.provisioning.models")
_try_import_models("app.domains.social_sellers.models")
_try_import_models("app.domains.documents.models")
_try_import_models("app.domains.memory.models")
_try_import_models("app.domains.voice.models")
_try_import_models("app.domains.agents.music_agent.models")
_try_import_models("app.domains.agents.brand_visual.models")
_try_import_models("app.domains.agents.viral_video.models")
_try_import_models("app.domains.agents.app_builder.models")
_try_import_models("app.domains.agents.crm_builder.models")
_try_import_models("app.domains.webhooks.models")
_try_import_models("app.core.semantic_cache", names=["SemanticCacheEmbedding"])

settings = get_settings()

# this is the Alembic Config object
config = context.config

# Set the SQLAlchemy URL from app settings. Alembic runs as a one-shot
# administrative script, so it uses a plain sync driver (psycopg2) instead
# of the app's asyncpg URL — bridging async engines into Alembic's sync
# migration context via run_sync deadlocks on Windows (ProactorEventLoop +
# threaded executor), and there's no benefit to async here anyway.
sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", sync_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Tables owned by app.db.models.Base (the sellbot core app), a separate
# declarative base from app.core.database.Base. Autogenerate only knows
# about target_metadata above, so without this filter it would propose
# DROP TABLE for every one of these on comparison.
_SELLBOT_OWNED_TABLES = {
    "leads", "workflows", "workflow_executions", "lead_sources",
    "email_logs", "webhook_events", "audit_logs", "alembic_version",
}


def include_object(object_, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and name in _SELLBOT_OWNED_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using a plain sync engine."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
