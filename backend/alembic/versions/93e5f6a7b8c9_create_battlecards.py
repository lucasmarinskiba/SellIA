"""create_battlecards

Revision ID: 93e5f6a7b8c9
Revises: 16a3957a8fbe
Create Date: 2026-05-20 19:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '93e5f6a7b8c9'
down_revision: Union[str, None] = '16a3957a8fbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("competitive_battlecards"):
        op.create_table(
            'competitive_battlecards',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('competitor_name', sa.String(255), nullable=False),
            sa.Column('competitor_url', sa.String(500), nullable=True),
            sa.Column('our_strengths', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('our_weaknesses', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('their_strengths', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('their_weaknesses', postgresql.JSONB(), nullable=False, server_default='[]'),
            sa.Column('price_comparison', sa.Text(), nullable=True),
            sa.Column('feature_comparison', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('market_share_estimate', sa.String(50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    op.drop_table('competitive_battlecards')
