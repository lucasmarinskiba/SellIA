"""voice_agent

Revision ID: a1b2c3d4e5f6
Revises: 0ecfa96b7780
Create Date: 2026-05-20 19:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '0ecfa96b7780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    try:
        inspector = inspect(bind)
        return inspector.has_table(table_name)
    except NoInspectionAvailable:
        return False


def upgrade() -> None:
    if not _has_table("voice_calls"):
        op.create_table(
            'voice_calls',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True),
            sa.Column('phone_number', sa.String(length=50), nullable=False),
            sa.Column('direction', sa.String(length=20), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='ringing'),
            sa.Column('recording_url', sa.String(length=500), nullable=True),
            sa.Column('recording_duration', sa.Integer(), nullable=True),
            sa.Column('transcript', sa.Text(), nullable=True),
            sa.Column('transcript_segments', postgresql.JSONB(), nullable=True),
            sa.Column('ai_summary', sa.Text(), nullable=True),
            sa.Column('outcome', sa.String(length=50), nullable=True),
            sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), server_default='0'),
            sa.Column('extra_data', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("voice_configs"):
        op.create_table(
            'voice_configs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('voice_id', sa.String(length=100), nullable=False),
            sa.Column('tts_provider', sa.String(length=20), nullable=False),
            sa.Column('stt_provider', sa.String(length=20), nullable=False),
            sa.Column('language', sa.String(length=10), nullable=False, server_default='es'),
            sa.Column('greeting_message', sa.Text(), nullable=False),
            sa.Column('max_call_duration', sa.Integer(), nullable=False, server_default='600'),
            sa.Column('allowed_hours_start', sa.Time(), nullable=False, server_default='09:00:00'),
            sa.Column('allowed_hours_end', sa.Time(), nullable=False, server_default='18:00:00'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    if _has_table("voice_configs"):
        op.drop_table('voice_configs')
    if _has_table("voice_calls"):
        op.drop_table('voice_calls')
