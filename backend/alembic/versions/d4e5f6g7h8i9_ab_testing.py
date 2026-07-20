"""Add A/B testing tables for prompt experiments

Revision ID: d4e5f6g7h8i9
Revises: 23c526738ecb, c3d4e5f6g7h8
Create Date: 2026-05-23 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = ('23c526738ecb', 'c3d4e5f6g7h8')
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
    if not _has_table("prompt_experiments"):
        op.create_table(
            'prompt_experiments',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id'), nullable=True, index=True),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('agent_type', sa.String(50), nullable=False, index=True),
            sa.Column('metric', sa.String(20), nullable=False, server_default='conversion'),
            sa.Column('variant_a_name', sa.String(100), nullable=False),
            sa.Column('variant_a_prompt', sa.Text(), nullable=False),
            sa.Column('variant_b_name', sa.String(100), nullable=False),
            sa.Column('variant_b_prompt', sa.Text(), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
            sa.Column('confidence_threshold', sa.Float(), nullable=False, server_default='0.95'),
            sa.Column('min_samples', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('winner_variant', sa.String(1), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("prompt_experiment_results"):
        op.create_table(
            'prompt_experiment_results',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('experiment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('prompt_experiments.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('variant', sa.String(1), nullable=False),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('outcome', sa.String(50), nullable=True),
            sa.Column('revenue', sa.Numeric(10, 2), nullable=True),
            sa.Column('engagement_score', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    if _has_table("prompt_experiment_results"):
        op.drop_table('prompt_experiment_results')
    if _has_table("prompt_experiments"):
        op.drop_table('prompt_experiments')
