"""Mercado Libre listing sync connector."""

from typing import Any
import httpx
import re

from app.core.logger import get_logger
from app.domains.seo_config.platform_sync_base import PlatformListingSyncConnector

logger = get_logger(__name__)


class MercadoLibreListingSync(PlatformListingSyncConnector):
    """Sync FOMO copy to Mercado Libre listings."""

    platform_name = "mercado-libre"
    API_BASE = "https://api.mercadolibre.com"

    def __init__(self, credentials: dict[str, Any]):
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.seller_id = credentials.get("seller_id")

    async def validate_credentials(self) -> bool:
        """Check if access token is valid."""
        if not self.access_token or not self.seller_id:
            logger.error("MercadoLibre: missing access_token or seller_id")
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.API_BASE}/users/{self.seller_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"MercadoLibre credentials validation failed: {str(e)[:100]}")
            return False

    async def extract_listing_id(self, url: str) -> str | None:
        """Extract MercadoLibre listing ID from URL.

        URLs look like:
        - https://mercadolibre.com.ar/product-MLM123456789
        - https://www.mercadolibre.com.ar/items/MLM123456789
        """
        # Listing permalinks spell the id with a hyphen (`MLA-123456789-title`)
        # while the API id has none (`MLA123456789`): accept both, return the API form.
        match = re.search(r'(?<![A-Za-z])(ML[A-Z]?)-?(\d{6,})', url)
        if match:
            return f"{match.group(1)}{match.group(2)}"
        return None

    async def update_listing_title(self, external_id: str, title: str) -> dict[str, Any]:
        """Update listing title on MercadoLibre."""
        if not self.access_token:
            return {"status": "failed", "error_message": "Missing access_token"}

        try:
            payload = {"title": title}
            async with httpx.AsyncClient() as client:
                resp = await client.put(
                    f"{self.API_BASE}/items/{external_id}",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=15,
                )

                if resp.status_code in (200, 201):
                    logger.info(f"MercadoLibre: updated title for listing {external_id}")
                    return {"status": "synced", "response": resp.json()}
                else:
                    error = resp.json().get("message", resp.text)
                    logger.error(f"MercadoLibre title update failed: {error}")
                    return {"status": "failed", "error_message": error}

        except Exception as e:
            error_msg = str(e)[:200]
            logger.error(f"MercadoLibre title sync error: {error_msg}")
            return {"status": "failed", "error_message": error_msg}

    async def update_listing_description(self, external_id: str, description: str) -> dict[str, Any]:
        """Update listing description on MercadoLibre.

        MercadoLibre uses a separate 'descriptions' endpoint for item descriptions.
        """
        if not self.access_token:
            return {"status": "failed", "error_message": "Missing access_token"}

        try:
            # First, get current item data to preserve other fields
            async with httpx.AsyncClient() as client:
                # Get current item
                get_resp = await client.get(
                    f"{self.API_BASE}/items/{external_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10,
                )

                if get_resp.status_code != 200:
                    error = get_resp.json().get("message", get_resp.text)
                    return {"status": "failed", "error_message": f"Could not fetch item: {error}"}

                # Update description via descriptions endpoint
                desc_payload = {"plain_text": description}
                desc_resp = await client.put(
                    f"{self.API_BASE}/items/{external_id}/descriptions",
                    json=desc_payload,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=15,
                )

                if desc_resp.status_code in (200, 201):
                    logger.info(f"MercadoLibre: updated description for listing {external_id}")
                    return {"status": "synced", "response": desc_resp.json()}
                else:
                    error = desc_resp.json().get("message", desc_resp.text)
                    logger.error(f"MercadoLibre description update failed: {error}")
                    return {"status": "failed", "error_message": error}

        except Exception as e:
            error_msg = str(e)[:200]
            logger.error(f"MercadoLibre description sync error: {error_msg}")
            return {"status": "failed", "error_message": error_msg}
