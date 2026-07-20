"""Add simulation training tables

Revision ID: 9d16e7f8g0h1
Revises: 0ecfa96b7780
Create Date: 2026-05-23 01:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '9d16e7f8g0h1'
down_revision: Union[str, None] = '0ecfa96b7780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("training_scenarios"):
        op.create_table(
            'training_scenarios',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='medium'),
            sa.Column('customer_persona', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
            sa.Column('objective', sa.String(length=100), nullable=False, server_default='close_sale'),
            sa.Column('success_criteria', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
            sa.Column('agent_type', sa.String(length=50), nullable=False, server_default='general'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_training_scenarios_business_id'), 'training_scenarios', ['business_id'], unique=False)

    if not inspector.has_table("training_runs"):
        op.create_table(
            'training_runs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='running'),
            sa.Column('messages', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
            sa.Column('score', sa.Integer(), nullable=True),
            sa.Column('objective_achieved', sa.Boolean(), nullable=True),
            sa.Column('time_to_close_seconds', sa.Integer(), nullable=True),
            sa.Column('customer_satisfaction', sa.Float(), nullable=True),
            sa.Column('skills_tested', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
            sa.Column('feedback', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_training_runs_scenario_id'), 'training_runs', ['scenario_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_training_runs_scenario_id'), table_name='training_runs')
    op.drop_table('training_runs')
    op.drop_index(op.f('ix_training_scenarios_business_id'), table_name='training_scenarios')
    op.drop_table('training_scenarios')
