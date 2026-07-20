"""Add simulation tables

Revision ID: c3d4e5f6g7h8
Revises: 9c15d6e7f8g9, 9d16e7f8g0h1
Create Date: 2026-05-20 19:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', '9d16e7f8g0h1')
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
    # NOTE: simulation_scenarios and simulation_runs are created by
    # revision 9d16e7f8g0h1 with the canonical schema. This migration
    # only ensures the optional simulation_leaderboards table exists.

    if not _has_table("simulation_scenarios"):
        op.create_table(
            'simulation_scenarios',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('difficulty', sa.String(20), nullable=False, server_default='beginner'),
            sa.Column('objective', sa.String(100), nullable=False, server_default='close_sale'),
            sa.Column('customer_persona', postgresql.JSONB(), server_default='{}'),
            sa.Column('agent_type', sa.String(50), nullable=False),
            sa.Column('success_criteria', postgresql.JSONB(), server_default='{}'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("simulation_runs"):
        op.create_table(
            'simulation_runs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('simulation_scenarios.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('agent_config', postgresql.JSONB(), server_default='{}'),
            sa.Column('status', sa.String(20), nullable=False, server_default='running'),
            sa.Column('messages', postgresql.JSONB(), server_default='[]'),
            sa.Column('score', sa.Integer(), nullable=True),
            sa.Column('outcome', sa.String(50), nullable=True),
            sa.Column('skills_tested', postgresql.JSONB(), server_default='{}'),
            sa.Column('feedback', sa.Text(), nullable=True),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not _has_table("simulation_leaderboards"):
        op.create_table(
            'simulation_leaderboards',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('agent_type', sa.String(50), nullable=False),
            sa.Column('total_runs', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('avg_score', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('best_score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('success_rate', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )


def downgrade() -> None:
    if _has_table("simulation_leaderboards"):
        op.drop_table('simulation_leaderboards')
    if _has_table("simulation_runs"):
        op.drop_table('simulation_runs')
    if _has_table("simulation_scenarios"):
        op.drop_table('simulation_scenarios')
