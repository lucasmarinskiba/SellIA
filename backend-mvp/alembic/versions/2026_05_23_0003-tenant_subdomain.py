"""add tenants.subdomain · per-tenant routing

Revision ID: 0003_subdomain
Revises: 0002_rls
Create Date: 2026-05-23 00:02:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_subdomain"
down_revision: Union[str, None] = "0002_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("subdomain", sa.String(63), unique=True))
    op.create_index("ix_tenants_subdomain", "tenants", ["subdomain"])


def downgrade() -> None:
    op.drop_index("ix_tenants_subdomain", table_name="tenants")
    op.drop_column("tenants", "subdomain")
