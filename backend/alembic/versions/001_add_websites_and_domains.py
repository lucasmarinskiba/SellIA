"""Add websites and domains tables for Tier 1 onboarding.

Revision ID: 001_websites_domains
Revises:
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_websites_domains'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create websites table
    op.create_table(
        'websites',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template', sa.Enum('MINIMAL', 'CLASSIC', 'MODERN', 'ECOMMERCE', 'PORTFOLIO', name='websitetemplate'), nullable=False, server_default='MODERN'),
        sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', name='websitestatus'), nullable=False, server_default='DRAFT'),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hero_image_url', sa.String(500), nullable=True),
        sa.Column('meta_title', sa.String(255), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('meta_keywords', sa.String(500), nullable=True),
        sa.Column('og_image_url', sa.String(500), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('pages', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_websites_business_id'), 'websites', ['business_id'], unique=False)

    # Create domains table
    op.create_table(
        'domains',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('website_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subdomain', sa.String(63), nullable=False, unique=True),
        sa.Column('custom_domain', sa.String(255), nullable=True, unique=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dns_records', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_domains_website_id'), 'domains', ['website_id'], unique=False)
    op.create_index(op.f('ix_domains_subdomain'), 'domains', ['subdomain'], unique=True)
    op.create_index(op.f('ix_domains_custom_domain'), 'domains', ['custom_domain'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_domains_custom_domain'), table_name='domains')
    op.drop_index(op.f('ix_domains_subdomain'), table_name='domains')
    op.drop_index(op.f('ix_domains_website_id'), table_name='domains')
    op.drop_table('domains')
    op.drop_index(op.f('ix_websites_business_id'), table_name='websites')
    op.drop_table('websites')
