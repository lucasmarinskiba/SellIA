"""semantic_cache_embeddings

Revision ID: 94f7a8b9c0d1
Revises: 9b15bf3b57fc
Create Date: 2026-05-21 22:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '94f7a8b9c0d1'
down_revision: Union[str, None] = '9b15bf3b57fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not inspector.has_table("semantic_cache_embeddings"):
        op.create_table(
            'semantic_cache_embeddings',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
            sa.Column('query_text', sa.Text(), nullable=False),
            sa.Column('query_embedding', Vector(768), nullable=False),
            sa.Column('response_text', sa.Text(), nullable=False),
            sa.Column('model_used', sa.String(length=100), nullable=False),
            sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        )

        op.create_index('ix_semantic_cache_embeddings_created_at', 'semantic_cache_embeddings', ['created_at'])
        op.create_index('ix_semantic_cache_embeddings_hit_count', 'semantic_cache_embeddings', ['hit_count'])

        # IVFFlat index for fast approximate nearest neighbor search with cosine similarity
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_semantic_cache_embeddings_embedding ON semantic_cache_embeddings USING ivfflat (query_embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table("semantic_cache_embeddings"):
        op.execute("DROP INDEX IF EXISTS ix_semantic_cache_embeddings_embedding")
        op.drop_index('ix_semantic_cache_embeddings_hit_count', table_name='semantic_cache_embeddings', if_exists=True)
        op.drop_index('ix_semantic_cache_embeddings_created_at', table_name='semantic_cache_embeddings', if_exists=True)
        op.drop_table('semantic_cache_embeddings')
