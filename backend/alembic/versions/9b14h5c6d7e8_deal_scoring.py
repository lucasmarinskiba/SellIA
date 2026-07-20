"""deal scoring

Revision ID: 9b14h5c6d7e8
Revises: 97i0d1e2f3a4
Create Date: 2026-05-20 21:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '9b14h5c6d7e8'
down_revision: Union[str, None] = '97i0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    if not inspector.has_table("deal_scores"):
        op.create_table(
            'deal_scores',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('category', sa.String(length=20), nullable=False, server_default='cold'),
            sa.Column('factors', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('recommendation', sa.Text(), nullable=True),
            sa.Column('previous_score', sa.Integer(), nullable=True),
            sa.Column('score_change', sa.Integer(), nullable=True),
            sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(
            op.f('ix_deal_scores_conversation_id'),
            'deal_scores',
            ['conversation_id'],
            unique=False,
        )
        op.create_index(
            op.f('ix_deal_scores_business_id'),
            'deal_scores',
            ['business_id'],
            unique=False,
        )
        op.create_index(
            op.f('ix_deal_scores_customer_id'),
            'deal_scores',
            ['customer_id'],
            unique=False,
        )

    if not inspector.has_table("deal_alerts"):
        op.create_table(
            'deal_alerts',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('deal_score_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('alert_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False, server_default='low'),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['deal_score_id'], ['deal_scores.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(
            op.f('ix_deal_alerts_conversation_id'),
            'deal_alerts',
            ['conversation_id'],
            unique=False,
        )
        op.create_index(
            op.f('ix_deal_alerts_alert_type'),
            'deal_alerts',
            ['alert_type'],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    if inspector.has_table("deal_alerts"):
        op.drop_index(
            op.f('ix_deal_alerts_alert_type'),
            table_name='deal_alerts',
            if_exists=True,
        )
        op.drop_index(
            op.f('ix_deal_alerts_conversation_id'),
            table_name='deal_alerts',
            if_exists=True,
        )
        op.drop_table('deal_alerts')

    if inspector.has_table("deal_scores"):
        op.drop_index(
            op.f('ix_deal_scores_customer_id'),
            table_name='deal_scores',
            if_exists=True,
        )
        op.drop_index(
            op.f('ix_deal_scores_business_id'),
            table_name='deal_scores',
            if_exists=True,
        )
        op.drop_index(
            op.f('ix_deal_scores_conversation_id'),
            table_name='deal_scores',
            if_exists=True,
        )
        op.drop_table('deal_scores')
