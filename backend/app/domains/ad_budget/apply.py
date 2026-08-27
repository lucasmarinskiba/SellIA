"""Push a decided budget to the ad platform.

Meta campaigns can be updated through the API. Google / TikTok connectors
don't expose budget writes yet, so those decisions are returned as
`manual_required` — the dashboard and the reallocation record surface them
for a human (or a computer-use run) to apply.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.ad_budget.models import AdChannel, AdPlatform

logger = get_logger(__name__)

CENT = Decimal("0.01")


class BudgetApplier:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply(
        self, business_id: uuid.UUID, channel: AdChannel, new_budget: Decimal, *, pause: bool = False
    ) -> dict[str, Any]:
        new_budget = Decimal(str(new_budget)).quantize(CENT, rounding=ROUND_HALF_UP)

        if pause:
            result = await self._pause(channel)
        elif channel.platform == AdPlatform.META.value:
            result = await self._apply_meta(channel, new_budget)
        elif channel.platform == AdPlatform.GOOGLE.value:
            result = await self._apply_google(channel, new_budget)
        elif channel.platform == AdPlatform.TIKTOK.value:
            result = await self._apply_tiktok(channel, new_budget)
        else:
            result = {"applied": False, "manual_required": True,
                      "message": f"El conector de {channel.platform} no permite escribir presupuesto todavía"}

        if result.get("applied"):
            channel.current_daily_budget = new_budget if not pause else Decimal("0")
            if pause:
                channel.is_paused = True
        return result

    async def _connector(self, channel: AdChannel):
        if not channel.channel_connection_id:
            return None
        from app.domains.channels.connectors import get_connector
        from app.domains.channels.models import ChannelConnection

        conn = (
            await self.db.execute(
                select(ChannelConnection).where(ChannelConnection.id == channel.channel_connection_id)
            )
        ).scalar_one_or_none()
        if not conn:
            return None
        return get_connector(conn.platform, conn.credentials, conn.settings)

    async def _apply_meta(self, channel: AdChannel, new_budget: Decimal) -> dict[str, Any]:
        connector = await self._connector(channel)
        if connector is None or not hasattr(connector, "update_campaign_budget"):
            return {"applied": False, "manual_required": True,
                    "message": "Sin conexión Meta Ads válida"}
        refs = [str(r) for r in (channel.campaign_refs or []) if r]
        if not refs:
            return {"applied": False, "manual_required": True,
                    "message": "El canal no tiene campañas (campaign_refs) asignadas"}

        per_campaign_minor = int((new_budget / len(refs) * 100).to_integral_value(rounding=ROUND_HALF_UP))
        errors = []
        for ref in refs:
            try:
                await connector.update_campaign_budget(ref, per_campaign_minor)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{ref}: {e}")
        if errors:
            logger.warning("ad_budget: Meta budget update partial failure: %s", errors)
            return {"applied": len(errors) < len(refs), "manual_required": bool(errors),
                    "message": "; ".join(errors)}
        return {"applied": True, "message": f"{len(refs)} campañas actualizadas a {new_budget} total"}

    async def _apply_google(self, channel: AdChannel, new_budget: Decimal) -> dict[str, Any]:
        """Apply budget via Google Ads API (campaigns.update)."""
        connector = await self._connector(channel)
        if connector is None or not hasattr(connector, "update_campaign_budget"):
            return {"applied": False, "manual_required": True,
                    "message": "Sin conexión Google Ads válida"}
        refs = [str(r) for r in (channel.campaign_refs or []) if r]
        if not refs:
            return {"applied": False, "manual_required": True,
                    "message": "El canal no tiene campañas (campaign_refs) asignadas"}

        per_campaign = (new_budget / len(refs)).quantize(CENT, rounding=ROUND_HALF_UP)
        errors = []
        for ref in refs:
            try:
                await connector.update_campaign_budget(ref, per_campaign)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{ref}: {e}")
        if errors:
            logger.warning("ad_budget: Google budget update partial failure: %s", errors)
            return {"applied": len(errors) < len(refs), "manual_required": bool(errors),
                    "message": "; ".join(errors)}
        return {"applied": True, "message": f"{len(refs)} campañas Google actualizadas a {new_budget} total"}

    async def _apply_tiktok(self, channel: AdChannel, new_budget: Decimal) -> dict[str, Any]:
        """Apply budget via TikTok Ads API (ad_group.update)."""
        connector = await self._connector(channel)
        if connector is None or not hasattr(connector, "update_campaign_budget"):
            return {"applied": False, "manual_required": True,
                    "message": "Sin conexión TikTok Ads válida"}
        refs = [str(r) for r in (channel.campaign_refs or []) if r]
        if not refs:
            return {"applied": False, "manual_required": True,
                    "message": "El canal no tiene campañas (campaign_refs) asignadas"}

        per_campaign = (new_budget / len(refs)).quantize(CENT, rounding=ROUND_HALF_UP)
        errors = []
        for ref in refs:
            try:
                await connector.update_campaign_budget(ref, per_campaign)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{ref}: {e}")
        if errors:
            logger.warning("ad_budget: TikTok budget update partial failure: %s", errors)
            return {"applied": len(errors) < len(refs), "manual_required": bool(errors),
                    "message": "; ".join(errors)}
        return {"applied": True, "message": f"{len(refs)} campañas TikTok actualizadas a {new_budget} total"}

    async def _pause(self, channel: AdChannel) -> dict[str, Any]:
        connector = await self._connector(channel)
        if connector is None or not hasattr(connector, "pause_campaign"):
            return {"applied": False, "manual_required": True,
                    "message": f"Pausar manualmente el canal {channel.display_name}"}
        errors = []
        for ref in [str(r) for r in (channel.campaign_refs or []) if r]:
            try:
                await connector.pause_campaign(ref)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{ref}: {e}")
        if errors:
            return {"applied": False, "manual_required": True, "message": "; ".join(errors)}
        return {"applied": True, "message": "campañas pausadas"}
