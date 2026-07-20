"""conversation outcomes

Revision ID: 97i0d1e2f3a4
Revises: 94f7a8b9c0d1
Create Date: 2026-05-20 20:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '97i0d1e2f3a4'
down_revision: Union[str, None] = '94f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    if not inspector.has_table("conversation_outcomes"):
        op.create_table(
            'conversation_outcomes',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('agent_type', sa.String(length=50), nullable=False),
            sa.Column('outcome', sa.String(length=50), nullable=False),
            sa.Column('revenue', sa.Numeric(12, 2), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('feedback', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(
            op.f('ix_conversation_outcomes_conversation_id'),
            'conversation_outcomes',
            ['conversation_id'],
            unique=False,
        )
        op.create_index(
            op.f('ix_conversation_outcomes_agent_type'),
            'conversation_outcomes',
            ['agent_type'],
            unique=False,
        )
        op.create_index(
            op.f('ix_conversation_outcomes_outcome'),
            'conversation_outcomes',
            ['outcome'],
            unique=False,
        )
        op.create_index(
            op.f('ix_conversation_outcomes_created_at'),
            'conversation_outcomes',
            ['created_at'],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    if inspector.has_table("conversation_outcomes"):
        op.drop_index(
            op.f('ix_conversation_outcomes_created_at'),
            table_name='conversation_outcomes',
            if_exists=True,
        )
        op.drop_index(
            op.f('ix_conversation_outcomes_outcome'),
            table_name='conversation_outcomes',
            if_exists=True,
        )
        op.drop_index(
            op.f('ix_conversation_outcomes_agent_type'),
            table_name='conversation_outcomes',
            if_exists=True,
        )
        op.drop_index(
            op.f('ix_conversation_outcomes_conversation_id'),
            table_name='conversation_outcomes',
            if_exists=True,
        )
        op.drop_table('conversation_outcomes')
