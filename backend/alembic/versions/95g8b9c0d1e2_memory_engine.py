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
    pass

def downgrade() -> None:
    pass
