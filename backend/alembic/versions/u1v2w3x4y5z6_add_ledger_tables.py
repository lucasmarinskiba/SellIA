"""Add double-entry ledger tables

Revision ID: u1v2w3x4y5z6
Revises: 20260823_create_users_table, t0u1v2w3x4y5
Create Date: 2026-08-27 00:00:00.000000+00:00

Creates the general-ledger schema: chart of accounts, accounting periods,
journal entries/lines, and bank reconciliation tables. Also merges the two
open migration heads.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "u1v2w3x4y5z6"
down_revision: Union[str, Sequence[str], None] = ("20260823_create_users_table", "t0u1v2w3x4y5")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "ledger_accounts",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("parent_id", _uuid(), nullable=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("subtype", sa.String(60), nullable=True),
        sa.Column("normal_balance", sa.String(10), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ARS"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tax_code", sa.String(30), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["ledger_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id", "code", name="uq_ledger_account_business_code"),
    )
    op.create_index("ix_ledger_accounts_business_id", "ledger_accounts", ["business_id"])
    op.create_index("ix_ledger_accounts_business_type", "ledger_accounts", ["business_id", "type"])

    op.create_table(
        "accounting_periods",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("name", sa.String(20), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="open"),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", _uuid(), nullable=True),
        sa.Column("closing_entry_id", _uuid(), nullable=True),
        sa.Column("net_income", sa.Numeric(18, 2), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id", "name", name="uq_accounting_period_business_name"),
    )
    op.create_index("ix_accounting_periods_business_id", "accounting_periods", ["business_id"])
    op.create_index("ix_accounting_periods_business_status", "accounting_periods", ["business_id", "status"])

    op.create_table(
        "journal_entries",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("period_id", _uuid(), nullable=True),
        sa.Column("entry_number", sa.String(40), nullable=False),
        sa.Column("entry_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("source_ref", sa.String(120), nullable=True),
        sa.Column("idempotency_key", sa.String(160), nullable=True),
        sa.Column("status", sa.String(10), nullable=False, server_default="draft"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", _uuid(), nullable=True),
        sa.Column("reversal_of_id", _uuid(), nullable=True),
        sa.Column("total_debit", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("total_credit", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ARS"),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["period_id"], ["accounting_periods.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reversal_of_id"], ["journal_entries.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id", "entry_number", name="uq_journal_entry_business_number"),
        sa.UniqueConstraint("business_id", "idempotency_key", name="uq_journal_entry_business_idem"),
    )
    op.create_index("ix_journal_entries_business_id", "journal_entries", ["business_id"])
    op.create_index("ix_journal_entries_business_date", "journal_entries", ["business_id", "entry_date"])
    op.create_index("ix_journal_entries_business_status", "journal_entries", ["business_id", "status"])
    op.create_index("ix_journal_entries_business_source", "journal_entries", ["business_id", "source", "source_ref"])
    op.create_index("ix_journal_entries_source_ref", "journal_entries", ["source_ref"])

    op.create_table(
        "journal_lines",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("entry_id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("account_id", _uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("debit", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ARS"),
        sa.Column("fx_rate", sa.Numeric(18, 8), nullable=False, server_default="1"),
        sa.Column("base_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("contact_type", sa.String(20), nullable=True),
        sa.Column("contact_id", _uuid(), nullable=True),
        sa.Column("tax_code", sa.String(30), nullable=True),
        sa.Column("line_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["entry_id"], ["journal_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["ledger_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_journal_lines_entry_id", "journal_lines", ["entry_id"])
    op.create_index("ix_journal_lines_business_id", "journal_lines", ["business_id"])
    op.create_index("ix_journal_lines_account_id", "journal_lines", ["account_id"])
    op.create_index("ix_journal_lines_business_account", "journal_lines", ["business_id", "account_id"])

    op.create_table(
        "bank_accounts",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("gl_account_id", _uuid(), nullable=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("institution", sa.String(120), nullable=True),
        sa.Column("account_ref_masked", sa.String(60), nullable=True),
        sa.Column("provider", sa.String(40), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ARS"),
        sa.Column("current_balance", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gl_account_id"], ["ledger_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bank_accounts_business_id", "bank_accounts", ["business_id"])

    op.create_table(
        "bank_transactions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("bank_account_id", _uuid(), nullable=False),
        sa.Column("txn_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ARS"),
        sa.Column("external_id", sa.String(160), nullable=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="unmatched"),
        sa.Column("matched_entry_id", _uuid(), nullable=True),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("match_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("reconciled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_entry_id"], ["journal_entries.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_account_id", "external_id", name="uq_bank_txn_account_external"),
    )
    op.create_index("ix_bank_transactions_business_id", "bank_transactions", ["business_id"])
    op.create_index("ix_bank_transactions_bank_account_id", "bank_transactions", ["bank_account_id"])
    op.create_index("ix_bank_transactions_business_status", "bank_transactions", ["business_id", "status"])

    op.create_table(
        "reconciliation_rules",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("account_id", _uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("match_contains", sa.String(200), nullable=True),
        sa.Column("match_min_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("match_max_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("direction", sa.String(10), nullable=True),
        sa.Column("contact_type", sa.String(20), nullable=True),
        sa.Column("contact_id", _uuid(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["ledger_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reconciliation_rules_business_id", "reconciliation_rules", ["business_id"])


def downgrade() -> None:
    op.drop_table("reconciliation_rules")
    op.drop_table("bank_transactions")
    op.drop_table("bank_accounts")
    op.drop_table("journal_lines")
    op.drop_table("journal_entries")
    op.drop_table("accounting_periods")
    op.drop_table("ledger_accounts")
