"""Suggest BusinessLinks from platforms the account already connected in
/dashboard/platforms (ChannelConnection), so the user doesn't have to
re-type a URL SellIA already has the credentials for.

Only 3 platforms give a public URL we can derive with certainty from the
credentials already saved -- the rest hand us internal IDs (a seller_id,
an account_id), not the public handle/nickname a browser could open, so
inventing a URL there would risk pointing at something wrong. Those get
an honest "connected, no derivable link" notice instead.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.channels.models import ChannelConnection, ChannelPlatform
from .models import PLATFORM_KINDS, BusinessLink


def _derive_url(platform: ChannelPlatform, credentials: dict[str, Any]) -> str | None:
    if platform == ChannelPlatform.SHOPIFY:
        shop_domain = credentials.get("shop_domain")
        return f"https://{shop_domain}" if shop_domain else None
    if platform == ChannelPlatform.WOOCOMMERCE:
        return credentials.get("site_url") or None
    if platform == ChannelPlatform.AMAZON:
        seller_id = credentials.get("seller_id")
        return f"https://www.amazon.com/sp?seller={seller_id}" if seller_id else None
    return None


async def suggest_links_from_channels(
    db: AsyncSession, user_id: uuid.UUID, business_ids: list[uuid.UUID],
) -> list[dict[str, Any]]:
    """One suggestion per connected platform not already covered by a saved
    BusinessLink -- `derivable=True` entries carry a real `url` ready to add
    with one click; `derivable=False` ones only tell the user the platform
    is connected and needs its link typed in by hand."""
    if not business_ids:
        return []

    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.business_id.in_(business_ids),
            ChannelConnection.is_active == True,
        )
    )
    channels = list(result.scalars().all())
    if not channels:
        return []

    existing_urls_result = await db.execute(
        select(BusinessLink.url).where(BusinessLink.user_id == user_id)
    )
    existing_urls = {row[0] for row in existing_urls_result.all()}
    existing_platforms_result = await db.execute(
        select(BusinessLink.platform).where(BusinessLink.user_id == user_id)
    )
    existing_platforms = {row[0] for row in existing_platforms_result.all()}

    suggestions: list[dict[str, Any]] = []
    seen_platforms: set[str] = set()
    for channel in channels:
        platform_slug = channel.platform.value if hasattr(channel.platform, "value") else str(channel.platform)
        if platform_slug not in PLATFORM_KINDS or platform_slug in seen_platforms:
            continue
        if platform_slug in existing_platforms:
            continue
        seen_platforms.add(platform_slug)

        _, label = PLATFORM_KINDS[platform_slug]
        url = _derive_url(channel.platform, channel.credentials or {})
        if url and url in existing_urls:
            continue

        suggestions.append({
            "platform": platform_slug,
            "label": label,
            "url": url,
            "derivable": url is not None,
        })

    return suggestions
