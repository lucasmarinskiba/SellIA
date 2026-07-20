"""add_gamification_models

Revision ID: 02eb019f71fe
Revises: 69a2f112522c
Create Date: 2026-05-12 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '02eb019f71fe'
down_revision: Union[str, None] = '69a2f112522c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # achievements
    op.create_table(
        'achievements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('sales', 'growth', 'consistency', 'mastery', 'social', 'zen', 'milestone', name='achievementcategory'), nullable=False),
        sa.Column('tier', sa.Enum('bronze', 'silver', 'gold', 'platinum', 'diamond', name='achievementtier'), nullable=False, server_default='bronze'),
        sa.Column('requirement_type', sa.String(50), nullable=False),
        sa.Column('requirement_value', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('requirement_context', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('garden_reward', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('icon', sa.String(100), nullable=False, server_default='trophy'),
        sa.Column('color', sa.String(20), nullable=False, server_default='#FFD700'),
        sa.Column('animation', sa.String(50), nullable=False, server_default='bounce'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )

    # user_gamification_profiles
    op.create_table(
        'user_gamification_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('level_title', sa.String(100), nullable=False, server_default='Emprendedor Novato'),
        sa.Column('total_xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('xp_to_next_level', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('progress_pct', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('current_login_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_login_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_login_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('autopilot_trust_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_achievements', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_sales_closed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_revenue_generated', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('total_leads_acquired', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_content_published', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_reviews_collected', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_referrals_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('garden_state', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('companion_name', sa.String(50), nullable=False, server_default='Selia'),
        sa.Column('companion_mood', sa.String(20), nullable=False, server_default='happy'),
        sa.Column('companion_last_message', sa.Text(), nullable=True),
        sa.Column('user_mood_today', sa.String(20), nullable=True),
        sa.Column('mood_history', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )

    # user_achievements
    op.create_table(
        'user_achievements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('achievement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('was_celebrated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shared_to_social', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.create_index('ix_user_achievements_user_achievement', 'user_achievements', ['user_id', 'achievement_id'], unique=True)

    # celebration_events
    op.create_table(
        'celebration_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('event_title', sa.String(200), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('event_value', sa.Numeric(14, 2), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('intensity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('was_shown', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shown_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('companion_message', sa.Text(), nullable=True),
        sa.Column('companion_emotion', sa.String(20), nullable=False, server_default='happy'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_celebration_events_user_unshown', 'celebration_events', ['user_id', 'was_shown'])

    # daily_mood_logs
    op.create_table(
        'daily_mood_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('mood', sa.String(20), nullable=False),
        sa.Column('energy_level', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_mood_logs_user_date', 'daily_mood_logs', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('daily_mood_logs')
    op.drop_table('celebration_events')
    op.drop_table('user_achievements')
    op.drop_table('user_gamification_profiles')
    op.drop_table('achievements')
    op.execute("DROP TYPE IF EXISTS achievementcategory")
    op.execute("DROP TYPE IF EXISTS achievementtier")
