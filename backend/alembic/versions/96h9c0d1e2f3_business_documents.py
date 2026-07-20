"""business documents

Revision ID: 96h9c0d1e2f3
Revises: da7167e07273
Create Date: 2026-05-21 15:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '96h9c0d1e2f3'
down_revision: Union[str, Sequence[str], None] = 'da7167e07273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("business_documents"):
        op.create_table(
            'business_documents',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('file_path', sa.String(500), nullable=False),
            sa.Column('file_type', sa.String(50), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status', sa.String(20), nullable=False, server_default='processing'),
            sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('extra_data', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

    if not inspector.has_table("document_chunks"):
        op.create_table(
            'document_chunks',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
            sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_documents.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('embedding', sa.Text(), nullable=True),  # stored as vector via raw sql later or pgvector
            sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('page_number', sa.Integer(), nullable=True),
            sa.Column('chunk_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )
        op.create_index('ix_document_chunks_business_id_embedding', 'document_chunks', ['business_id'])

    # Create pgvector extension if available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Alter embedding column to VECTOR(768) if pgvector is present
    # We do this via raw SQL with a try/catch approach in Alembic
    try:
        op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(768) USING embedding::vector(768)")
    except Exception:
        # pgvector may not be installed; leave as text and handle in app
        pass


def downgrade() -> None:
    op.drop_index('ix_document_chunks_business_id_embedding', table_name='document_chunks')
    op.drop_table('document_chunks')
    op.drop_table('business_documents')
