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
    pass

def downgrade() -> None:
    pass
