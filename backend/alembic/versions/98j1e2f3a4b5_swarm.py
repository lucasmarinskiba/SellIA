"""create_swarm_tables

Revision ID: 98j1e2f3a4b5
Revises: 0e797dd2bbe
Create Date: 2026-05-20 19:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = '98j1e2f3a4b5'
down_revision: Union[str, None] = '0e797dd2bbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    try:
        inspector = inspect(bind)
        return inspector.has_table(table_name)
    except NoInspectionAvailable:
        # Offline mode (alembic --sql): assume table does not exist
        return False


def upgrade() -> None:
    if not _has_table("swarm_sessions"):
        op.create_table(
            'swarm_sessions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('task', sa.Text(), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_conversations.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('agents_involved', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('shared_context', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('round_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('consensus_reached', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('final_response', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("swarm_messages"):
        op.create_table(
            'swarm_messages',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('swarm_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('agent_id', sa.String(100), nullable=False),
            sa.Column('role', sa.String(50), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('message_type', sa.String(50), nullable=False),
            sa.Column('round', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table("swarm_messages"):
        op.drop_table('swarm_messages')
    if _has_table("swarm_sessions"):
        op.drop_table('swarm_sessions')
