"""baseline_webhook_tables

Revision ID: p6q7r8s9t0u1
Revises: n4o5p6q7r8s9
Create Date: 2026-08-07 21:00:00.000000+00:00

app.domains.webhooks.models was never imported in alembic/env.py, so
webhook_subscriptions and webhook_deliveries were missed by every prior
baseline pass — Base.metadata never even knew these two tables existed.
Fixed the missing import and add the tables here (hand-written, matching
the model exactly; only two tables with no complex types).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Text


# revision identifiers, used by Alembic.
revision: str = 'p6q7r8s9t0u1'
down_revision: Union[str, None] = 'k1l2m3n4o5p6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('webhook_subscriptions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('events', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('secret', sa.String(length=255), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_webhook_subscriptions_user_id'), 'webhook_subscriptions', ['user_id'], unique=False)

    op.create_table('webhook_deliveries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('subscription_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('response_status', sa.Integer(), nullable=True),
    sa.Column('response_body', sa.Text(), nullable=True),
    sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['subscription_id'], ['webhook_subscriptions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_webhook_deliveries_subscription_id'), 'webhook_deliveries', ['subscription_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_webhook_deliveries_subscription_id'), table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    op.drop_index(op.f('ix_webhook_subscriptions_user_id'), table_name='webhook_subscriptions')
    op.drop_table('webhook_subscriptions')
