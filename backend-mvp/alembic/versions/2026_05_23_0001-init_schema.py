"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-05-23 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # tenants
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("plan", sa.String(40), server_default="trial"),
        sa.Column("stripe_customer_id", sa.String(120), unique=True),
        sa.Column("stripe_subscription_id", sa.String(120)),
        sa.Column("settings", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # users
    user_role = sa.Enum("owner", "admin", "manager", "viewer", name="userrole")
    user_role.create(op.get_bind())
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(120)),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("role", user_role, server_default="viewer"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # channels
    channel_kind = sa.Enum("whatsapp", "instagram", "email", "web", "telegram", name="channelkind")
    channel_kind.create(op.get_bind())
    op.create_table(
        "channels",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("kind", channel_kind),
        sa.Column("external_id", sa.String(255)),
        sa.Column("config", JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_channels_tenant_kind", "channels", ["tenant_id", "kind"])

    # contacts
    op.create_table(
        "contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("phone", sa.String(40), index=True),
        sa.Column("email", sa.String(255), index=True),
        sa.Column("name", sa.String(120)),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # deals
    deal_stage = sa.Enum("prospect", "qualified", "negotiation", "won", "lost", name="dealstage")
    deal_stage.create(op.get_bind())
    op.create_table(
        "deals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("contact_id", UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(200)),
        sa.Column("value_cents", sa.BigInteger, server_default="0"),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column("stage", deal_stage, server_default="prospect"),
        sa.Column("probability", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_deals_tenant_stage", "deals", ["tenant_id", "stage"])

    # conversations + messages
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("channel_id", UUID(as_uuid=True), sa.ForeignKey("channels.id")),
        sa.Column("contact_id", UUID(as_uuid=True), sa.ForeignKey("contacts.id")),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    msg_role = sa.Enum("inbound", "outbound_ai", "outbound_human", name="messagerole")
    msg_role.create(op.get_bind())
    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE")),
        sa.Column("role", msg_role),
        sa.Column("body", sa.Text),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), index=True),
    )

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("actor_type", sa.String(20)),
        sa.Column("actor_id", sa.String(120)),
        sa.Column("action", sa.String(80)),
        sa.Column("resource", sa.String(255)),
        sa.Column("severity", sa.String(20), server_default="info"),
        sa.Column("ip", sa.String(45)),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), index=True),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("deals")
    op.drop_table("contacts")
    op.drop_table("channels")
    op.drop_table("users")
    op.drop_table("tenants")
    for enum_name in ("messagerole", "dealstage", "channelkind", "userrole"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
