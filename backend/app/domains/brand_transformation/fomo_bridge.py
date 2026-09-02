"""FOMO bridge — turn a FOMOEngineAgent playbook into real fomo-domain campaigns.

Etapa 4 (`FOMOEngineAgent`) produces a `FOMOPlaybook` with `mechanisms`
(each keyed by a lever), `content_hooks` (copy angles), a `launch_ritual` and a
`cadence`. This module maps each chosen mechanism to a concrete
`app.domains.fomo` `FOMOCampaign` — deterministically, no LLM — and can create +
activate them, writing the campaign links back onto the playbook
(`deployed_campaigns`).

Deliberately conservative: unmapped levers are skipped and reported; a missing
`fomo_widget_campaigns` table or any per-campaign failure is caught so one bad
mechanism never blocks the rest.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.brand_transformation.models import FOMOPlaybook

logger = get_logger(__name__)

# brand_transformation lever  ->  fomo.FOMOCampaign.campaign_type
#   campaign_type in: countdown | limited_spots | flash_sale | social_proof |
#                     progress | scarcity | exclusivity
_LEVER_TO_CAMPAIGN: dict[str, dict[str, Any]] = {
    "artificial_scarcity":       {"type": "limited_spots", "emoji": "🔥", "trigger": "product_view",  "cta": "Reservar mi lugar"},
    "social_proof_velocity":     {"type": "social_proof",  "emoji": "👀", "trigger": "page_view",     "cta": "Ver por qué"},
    "loss_and_urgency_framing":  {"type": "countdown",     "emoji": "⏳", "trigger": "cart_abandon",  "cta": "Aprovechar ahora"},
    "anticipation_and_ritual":   {"type": "countdown",     "emoji": "🗓️", "trigger": "page_view",     "cta": "Avisarme del drop"},
    "exclusivity_and_status":    {"type": "exclusivity",   "emoji": "✨", "trigger": "page_view",     "cta": "Solicitar acceso"},
    "velocity_of_novelty":       {"type": "flash_sale",    "emoji": "⚡", "trigger": "product_view",  "cta": "Ver lo nuevo"},
    # identity_and_tribe has no on-site widget primitive — skipped, reported
}


def _hook_for(playbook: FOMOPlaybook, lever: str) -> str | None:
    for h in (playbook.content_hooks or []):
        if isinstance(h, dict) and (h.get("mechanism") == lever or lever in str(h.get("mechanism", ""))):
            return h.get("copy_angle")
    return None


def _cadence_hours(cadence: str | None) -> int:
    c = (cadence or "").lower()
    if "week" in c or "seman" in c:
        return 24 * 7
    if "day" in c or "diari" in c or "dia" in c:
        return 24
    return 24 * 30  # default: monthly


def build_specs(playbook: FOMOPlaybook, levers: list[str] | None = None) -> dict:
    """Map the playbook's mechanisms to proposed FOMOCampaign specs. No writes."""
    specs: list[dict] = []
    skipped: list[dict] = []
    ritual = playbook.launch_ritual or {}

    for mech in (playbook.mechanisms or []):
        if not isinstance(mech, dict):
            continue
        lever = mech.get("lever") or ""
        if levers and lever not in levers:
            continue
        mapping = _LEVER_TO_CAMPAIGN.get(lever)
        if not mapping:
            skipped.append({"lever": lever, "reason": "no on-site campaign primitive for this lever"})
            continue

        hook = _hook_for(playbook, lever)
        headline = (hook or ritual.get("the_hook") or mech.get("why_it_fits") or "").strip()[:250] or f"{lever.replace('_', ' ').title()}"
        subheadline = (mech.get("implementation") or "")[:600] or None

        config = {
            "source": "brand_transformation.fomo_bridge",
            "playbook_id": str(playbook.id),
            "lever": lever,
            "trigger_psychology": mech.get("trigger"),
            "anti_fake_guardrail": mech.get("anti_fake_guardrail"),
            "kpi": mech.get("kpi"),
            "cadence": playbook.cadence,
            "countdownHours": _cadence_hours(playbook.cadence),
        }
        spec = {
            "lever": lever,
            "campaign_type": mapping["type"],
            "name": f"[BT] {lever.replace('_', ' ').title()}",
            "headline": headline,
            "subheadline": subheadline,
            "cta_text": mapping["cta"],
            "trigger_type": mapping["trigger"],
            "emoji": mapping["emoji"],
            "config": config,
        }
        if mapping["type"] in ("countdown", "flash_sale"):
            spec["ends_at"] = (datetime.now(timezone.utc) + timedelta(hours=config["countdownHours"])).isoformat()
        specs.append(spec)

    return {
        "playbook_id": str(playbook.id),
        "cadence": playbook.cadence,
        "campaign_specs": specs,
        "skipped_levers": skipped,
        "note": "identity_and_tribe and any lever without an on-site widget are handled via content/GTM, not the fomo widget domain.",
    }


class FOMOBridge:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def preview(self, playbook: FOMOPlaybook, levers: list[str] | None = None) -> dict:
        return build_specs(playbook, levers)

    async def deploy(
        self,
        playbook: FOMOPlaybook,
        owner_user_id: uuid.UUID,
        activate: bool = False,
        levers: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict:
        plan = build_specs(playbook, levers)
        if dry_run:
            plan["dry_run"] = True
            return plan

        try:
            from app.domains.fomo.service import FOMOService
        except Exception as e:  # noqa: BLE001
            return {**plan, "deployed": [], "error": f"fomo domain unavailable: {str(e)[:160]}"}

        deployed: list[dict] = []
        for spec in plan["campaign_specs"]:
            try:
                kwargs = {
                    "subheadline": spec.get("subheadline"),
                    "cta_text": spec.get("cta_text"),
                    "emoji": spec.get("emoji"),
                }
                if spec.get("ends_at"):
                    kwargs["ends_at"] = datetime.fromisoformat(spec["ends_at"])
                campaign = await FOMOService.create_campaign(
                    self.db,
                    user_id=owner_user_id,
                    name=spec["name"],
                    campaign_type=spec["campaign_type"],
                    headline=spec["headline"] or spec["name"],
                    config=spec["config"],
                    trigger_type=spec.get("trigger_type"),
                    **{k: v for k, v in kwargs.items() if v is not None},
                )
                status = "draft"
                if activate:
                    await FOMOService.activate_campaign(self.db, campaign.id)
                    status = "active"
                deployed.append({
                    "mechanism": spec["lever"], "lever": spec["lever"],
                    "campaign_id": str(campaign.id), "campaign_type": spec["campaign_type"],
                    "status": status,
                })
            except Exception as e:  # noqa: BLE001
                logger.warning("fomo_bridge: campaign for %s failed: %s", spec["lever"], str(e)[:200])
                deployed.append({"mechanism": spec["lever"], "lever": spec["lever"], "error": str(e)[:200]})

        # write links back onto the playbook
        playbook.deployed_campaigns = (playbook.deployed_campaigns or []) + deployed
        await self.db.commit()

        ok = [d for d in deployed if d.get("campaign_id")]
        return {
            **plan,
            "deployed": deployed,
            "created_count": len(ok),
            "activated": activate,
        }

    async def deployed_for(self, playbook: FOMOPlaybook) -> list[dict]:
        return playbook.deployed_campaigns or []
