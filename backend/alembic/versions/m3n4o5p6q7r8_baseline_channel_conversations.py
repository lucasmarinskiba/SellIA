"""baseline_channel_conversations

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-08-06 19:30:00.000000+00:00

Growth domain models and other domains reference `conversations` and
`channel_connections` tables which were never captured in migrations.
Baseline generated via alembic.autogenerate scoped to just these two.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Text


# revision identifiers, used by Alembic.
revision: str = 'm3n4o5p6q7r8'
down_revision: Union[str, None] = 'l2m3n4o5p6q7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('channel_connections',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('platform', sa.Enum('WHATSAPP', 'EMAIL', 'INSTAGRAM', 'MERCADOLIBRE', 'AMAZON', 'BEACONS', 'LINKEDIN', 'TELEGRAM', 'WEBCHAT', 'MESSENGER', 'FACEBOOK_ADS', 'META_ADS', 'GOOGLE_ADS', 'SHOPIFY', 'TIKTOK', 'TIKTOK_ADS', 'TWITTER', 'THREADS', name='channelplatform'), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('credentials', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('settings', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'CONNECTED', 'ERROR', 'DISABLED', name='channelstatus'), nullable=False),
    sa.Column('status_message', sa.Text(), nullable=True),
    sa.Column('webhook_url', sa.String(length=512), nullable=True),
    sa.Column('webhook_token', sa.String(length=64), nullable=False),
    sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('webhook_token')
    )
    op.create_index(op.f('ix_channel_connections_business_id'), 'channel_connections', ['business_id'], unique=False)
    op.create_table('conversations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('channel_connection_id', sa.UUID(), nullable=True),
    sa.Column('external_id', sa.String(length=255), nullable=True),
    sa.Column('lead_name', sa.String(length=255), nullable=True),
    sa.Column('lead_email', sa.String(length=255), nullable=True),
    sa.Column('lead_phone', sa.String(length=50), nullable=True),
    sa.Column('lead_source', sa.String(length=100), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', 'SPAM', name='conversationstatus'), nullable=False),
    sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['channel_connection_id'], ['channel_connections.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_business_id'), 'conversations', ['business_id'], unique=False)
    op.create_index(op.f('ix_conversations_external_id'), 'conversations', ['external_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_conversations_external_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_business_id'), table_name='conversations')
    op.drop_table('conversations')
    op.drop_index(op.f('ix_channel_connections_business_id'), table_name='channel_connections')
    op.drop_table('channel_connections')
