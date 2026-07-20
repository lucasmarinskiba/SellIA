"""create_webhooks

Revision ID: 92d4e5f6a7b8
Revises: 16a3957a8fbe
Create Date: 2026-05-21 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '92d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = ('16a3957a8fbe', '93e5f6a7b8c9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("webhook_subscriptions"):
        op.create_table(
            'webhook_subscriptions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('url', sa.String(500), nullable=False),
            sa.Column('events', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('secret', sa.String(255), nullable=False),
            sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not inspector.has_table("webhook_deliveries"):
        op.create_table(
            'webhook_deliveries',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('webhook_subscriptions.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('event_type', sa.String(100), nullable=False),
            sa.Column('payload', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('response_status', sa.Integer(), nullable=True),
            sa.Column('response_body', sa.Text(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        )


def downgrade() -> None:
    op.drop_table('webhook_deliveries')
    op.drop_table('webhook_subscriptions')
