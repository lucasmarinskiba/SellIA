"""memory engine

Revision ID: 95g8b9c0d1e2
Revises: da7167e07273
Create Date: 2026-05-20 19:43:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.types import UserDefinedType

# revision identifiers, used by Alembic.
revision: str = '95g8b9c0d1e2'
down_revision: Union[str, None] = 'da7167e07273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class Vector(UserDefinedType):
    """Custom SQLAlchemy type for PostgreSQL pgvector VECTOR(dim)."""

    def __init__(self, dim: int):
        self.dim = dim

    def get_col_spec(self):
        return f"VECTOR({self.dim})"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    if not inspector.has_table("conversation_memory_chunks"):
        op.create_table(
            'conversation_memory_chunks',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('embedding', Vector(768), nullable=True),
            sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_conversation_memory_chunks_conversation_id'), 'conversation_memory_chunks', ['conversation_id'], unique=False)
        op.create_index(op.f('ix_conversation_memory_chunks_business_id'), 'conversation_memory_chunks', ['business_id'], unique=False)
        op.create_index(op.f('ix_conversation_memory_chunks_user_id'), 'conversation_memory_chunks', ['user_id'], unique=False)
        op.create_index(op.f('ix_conversation_memory_chunks_agent_id'), 'conversation_memory_chunks', ['agent_id'], unique=False)
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_memory_chunks_embedding_hnsw "
            "ON conversation_memory_chunks USING hnsw (embedding vector_cosine_ops)"
        )

    if not inspector.has_table("customer_memories"):
        op.create_table(
            'customer_memories',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('memory_type', sa.String(length=50), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('embedding', Vector(768), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('source_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['source_conversation_id'], ['conversations.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_customer_memories_business_id'), 'customer_memories', ['business_id'], unique=False)
        op.create_index(op.f('ix_customer_memories_customer_id'), 'customer_memories', ['customer_id'], unique=False)
        op.create_index(op.f('ix_customer_memories_memory_type'), 'customer_memories', ['memory_type'], unique=False)
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_customer_memories_embedding_hnsw "
            "ON customer_memories USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_customer_memories_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_memory_chunks_embedding_hnsw")
    op.drop_index(op.f('ix_customer_memories_memory_type'), table_name='customer_memories')
    op.drop_index(op.f('ix_customer_memories_customer_id'), table_name='customer_memories')
    op.drop_index(op.f('ix_customer_memories_business_id'), table_name='customer_memories')
    op.drop_table('customer_memories')
    op.drop_index(op.f('ix_conversation_memory_chunks_agent_id'), table_name='conversation_memory_chunks')
    op.drop_index(op.f('ix_conversation_memory_chunks_user_id'), table_name='conversation_memory_chunks')
    op.drop_index(op.f('ix_conversation_memory_chunks_business_id'), table_name='conversation_memory_chunks')
    op.drop_index(op.f('ix_conversation_memory_chunks_conversation_id'), table_name='conversation_memory_chunks')
    op.drop_table('conversation_memory_chunks')
