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
from app.domains.users import models as user_models  # noqa: F401
from app.domains.businesses import models as business_models  # noqa: F401
from app.domains.catalogs import models as catalog_models  # noqa: F401
from app.domains.channels import models as channel_models  # noqa: F401
from app.domains.orders import models as order_models  # noqa: F401
from app.domains.subscriptions import models as subscription_models  # noqa: F401
from app.domains.agents import models as agent_models  # noqa: F401
from app.domains.agents.prompt_optimizer import ConversationOutcome  # noqa: F401
from app.domains.agents.models_reflection import AgentReflection, ChainOfThoughtLog  # noqa: F401
from app.domains.agents.models_causal import ObjectionPattern, CausalAnalysis  # noqa: F401
from app.domains.automations import models as automation_models  # noqa: F401
from app.domains.analytics import models as analytics_models  # noqa: F401
from app.domains.notifications import models as notification_models  # noqa: F401
from app.domains.security import models as security_models  # noqa: F401
from app.domains.support import models as support_models  # noqa: F401
from app.domains.shipments import models as shipment_models  # noqa: F401
from app.domains.services import models as service_models  # noqa: F401
from app.domains.crm import models as crm_models  # noqa: F401
from app.domains.computer_use import models as computer_use_models  # noqa: F401
from app.domains.computer_use import models_extended  # noqa: F401
from app.domains.intelligence import models as intelligence_models  # noqa: F401
from app.domains.retention import models as retention_models  # noqa: F401
from app.domains.outreach import models as outreach_models  # noqa: F401
from app.domains.autopilot import models as autopilot_models  # noqa: F401
from app.domains.finance import models as finance_models  # noqa: F401
from app.domains.bi import models as bi_models  # noqa: F401
from app.domains.objectives import models as objectives_models  # noqa: F401
from app.domains.feedback import models as feedback_models  # noqa: F401
from app.domains.alerts import models as alerts_models  # noqa: F401
from app.domains.optimization import models as optimization_models  # noqa: F401
from app.domains.growth import models as growth_models  # noqa: F401
from app.domains.gamification import models as gamification_models  # noqa: F401
from app.domains.provisioning import models as provisioning_models  # noqa: F401
from app.domains.social_sellers import models as social_sellers_models  # noqa: F401
from app.domains.social_sellers import models as social_seller_models  # noqa: F401
from app.domains.documents import models as documents_models  # noqa: F401
from app.domains.memory import models as memory_models  # noqa: F401
from app.domains.voice import models as voice_models  # noqa: F401
from app.domains.agents.music_agent import models as music_agent_models  # noqa: F401
from app.domains.agents.brand_visual import models as brand_visual_models  # noqa: F401
from app.domains.agents.viral_video import models as viral_video_models  # noqa: F401
from app.domains.agents.app_builder import models as app_builder_models  # noqa: F401
from app.domains.agents.crm_builder import models as crm_builder_models  # noqa: F401
from app.core.semantic_cache import SemanticCacheEmbedding  # noqa: F401

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
