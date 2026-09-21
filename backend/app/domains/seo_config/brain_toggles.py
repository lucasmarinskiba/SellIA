"""Bridge between seo_config's own switches and the Brain Interaction Map toggles.

The Brain Map keeps ON/OFF state as `AutomationToggle` rows (brain id
`automation.seo_positioning` <-> toggle_key `automation:seo_positioning`, see
app/core/brain/toggle_mapping.py; a missing row means enabled). SEO positioning
also has its own switches (SEOConfig, PlatformSEOStatus, PublicationLink) that
phase12 edits. Left alone those are two disconnected sources of truth: turning
SEO off on the Brain Map would not stop it, and turning it off in phase12
would not show on the Map.

This module makes them agree:
  - the guard/generators ask `is_brain_capability_enabled` in addition to the
    seo_config switches, so an OFF node on the Map really stops the work;
  - the global switch is mirrored both ways (`set_brain_capability` here, and
    SEOConfigService.sync_global_from_brain for the other direction).
"""

import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.brain.toggle_mapping import brain_id_category, brain_id_to_toggle_key
from app.core.logger import get_logger

logger = get_logger(__name__)

SEO_POSITIONING = "automation.seo_positioning"
FOMO_PUBLICATIONS = "automation.fomo_publications"

# Every name callers use for the same agent (the wrapper says "positioning_agent",
# the services say "positioning") maps to one Brain Map node.
AGENT_BRAIN_ID: dict[str, str] = {
    "positioning": SEO_POSITIONING,
    "positioning_agent": SEO_POSITIONING,
    "store_positioning": SEO_POSITIONING,
    "fomo_engine": FOMO_PUBLICATIONS,
    "fomo_engine_agent": FOMO_PUBLICATIONS,
}


def platform_brain_id(platform_name: str | None) -> str | None:
    """`"mercado-libre"` / `"mercado_libre"` / `"MercadoLibre"` -> `"platform.mercadolibre"`.

    The Brain Map spells platform ids without separators; seo_config,
    channels and web_presence each spell them differently.
    """
    slug = re.sub(r"[^a-z0-9]", "", (platform_name or "").lower())
    return f"platform.{slug}" if slug else None


async def is_brain_capability_enabled(db: AsyncSession, business_id: UUID, brain_id: str) -> bool:
    """False only when the business has explicitly turned this Map node OFF."""
    from app.domains.automations.models import AutomationToggle

    result = await db.execute(
        select(AutomationToggle.is_enabled).where(
            AutomationToggle.business_id == business_id,
            AutomationToggle.toggle_key == brain_id_to_toggle_key(brain_id),
        )
    )
    row = result.first()
    return True if row is None else bool(row[0])


async def set_brain_capability(
    db: AsyncSession,
    business_id: UUID,
    brain_id: str,
    enabled: bool,
    *,
    user_id: UUID | None = None,
    user_email: str | None = None,
) -> None:
    """Upsert the Map node's toggle row and audit the change. Does not commit —
    the caller owns the transaction so the switch and its mirror stay atomic."""
    from app.domains.automations.models import AutomationToggle, ToggleAuditLog

    toggle_key = brain_id_to_toggle_key(brain_id)
    result = await db.execute(
        select(AutomationToggle).where(
            AutomationToggle.business_id == business_id,
            AutomationToggle.toggle_key == toggle_key,
        )
    )
    toggle = result.scalar_one_or_none()
    old_enabled = toggle.is_enabled if toggle else True
    if toggle is not None and toggle.is_enabled == enabled:
        return  # already in sync: no row churn, no noise in the audit log

    now = datetime.now(timezone.utc)
    if toggle is None:
        toggle = AutomationToggle(
            business_id=business_id, toggle_key=toggle_key,
            category=brain_id_category(brain_id),
            is_enabled=enabled, display_name=brain_id, changed_by=user_id,
        )
        db.add(toggle)
    else:
        toggle.is_enabled = enabled
        toggle.updated_at = now
        toggle.changed_by = user_id

    toggle.enabled_at = now if enabled else toggle.enabled_at
    toggle.disabled_at = now if not enabled else toggle.disabled_at

    await db.flush()
    db.add(ToggleAuditLog(
        business_id=business_id, toggle_id=toggle.id,
        action="enabled" if enabled else "disabled",
        old_value={"is_enabled": old_enabled}, new_value={"is_enabled": enabled},
        changed_by_user_id=user_id, changed_by_email=user_email,
        reason="Sincronizado desde la configuración SEO",
    ))
