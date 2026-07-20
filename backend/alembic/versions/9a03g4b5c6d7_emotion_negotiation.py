"""Add emotion and negotiation tables

Revision ID: 9a03g4b5c6d7
Revises: 0e797dd2bbe, a1b2c3d4e5f6
Create Date: 2026-05-22 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '9a03g4b5c6d7'
down_revision: Union[str, Sequence[str], None] = ('0e797dd2bbe', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("emotion_detections"):
        op.create_table(
            'emotion_detections',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('emotion', sa.String(length=20), nullable=False),
            sa.Column('intensity', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('triggers', postgresql.JSONB(), server_default='[]'),
            sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_emotion_detections_conversation_id'), 'emotion_detections', ['conversation_id'], unique=False)
        op.create_index(op.f('ix_emotion_detections_message_id'), 'emotion_detections', ['message_id'], unique=False)

    if not inspector.has_table("negotiation_states"):
        op.create_table(
            'negotiation_states',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('original_price', sa.Numeric(12, 2), nullable=False),
            sa.Column('current_offer', sa.Numeric(12, 2), nullable=False),
            sa.Column('minimum_acceptable', sa.Numeric(12, 2), nullable=False),
            sa.Column('max_discount_percent', sa.Numeric(5, 2), nullable=False, server_default='0.0'),
            sa.Column('round', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('concessions_made', postgresql.JSONB(), server_default='[]'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_negotiation_states_conversation_id'), 'negotiation_states', ['conversation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_negotiation_states_conversation_id'), table_name='negotiation_states')
    op.drop_table('negotiation_states')
    op.drop_index(op.f('ix_emotion_detections_message_id'), table_name='emotion_detections')
    op.drop_index(op.f('ix_emotion_detections_conversation_id'), table_name='emotion_detections')
    op.drop_table('emotion_detections')
