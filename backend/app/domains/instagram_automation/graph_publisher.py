"""Instagram Graph API Content Publishing — real posts to @sell_.ia feed.

Flujo oficial de Meta para publicar en el feed (no DMs, no Shop):
  1. POST /{ig-user-id}/media          (image_url/video_url + caption) -> creation_id
  2. GET  /{creation_id}?fields=status_code   (poll hasta FINISHED, solo video)
  3. POST /{ig-user-id}/media_publish  (creation_id) -> media id
  4. GET  /{media-id}?fields=permalink        (URL real del post publicado)

Credenciales requeridas (no incluidas — deben configurarse en el dashboard de
Meta Business Suite para la cuenta @sell_.ia):
  INSTAGRAM_BUSINESS_ACCOUNT_ID  - ID numérico de la cuenta IG Business/Creator
  INSTAGRAM_ACCESS_TOKEN         - Token de larga duración con permiso
                                    instagram_content_publish

Sin estas dos variables, publish_image()/publish_reel() fallan con
InstagramNotConfiguredError en vez de simular un post exitoso — coherente
con la regla de integridad del framework FOMO: nada se "publica" si no es real.
"""
import os
import asyncio
import httpx


class InstagramNotConfiguredError(Exception):
    """Faltan credenciales de Meta Graph API para @sell_.ia."""


class InstagramPublishError(Exception):
    """La API de Meta rechazó la publicación (ver .detail para la respuesta cruda)."""

    def __init__(self, message: str, detail: dict | None = None):
        super().__init__(message)
        self.detail = detail or {}


class InstagramGraphPublisher:
    """Cliente real de Instagram Graph API para publicar contenido en el feed."""

    GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
    TIMEOUT = 30

    def __init__(self, business_account_id: str | None = None, access_token: str | None = None):
        self.business_account_id = business_account_id or os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")

    def is_configured(self) -> bool:
        return bool(self.business_account_id and self.access_token)

    def _require_configured(self) -> None:
        if not self.is_configured():
            raise InstagramNotConfiguredError(
                "Faltan INSTAGRAM_BUSINESS_ACCOUNT_ID / INSTAGRAM_ACCESS_TOKEN. "
                "Configurar en Meta Business Suite (cuenta @sell_.ia) antes de publicar."
            )

    async def publish_image(self, image_url: str, caption: str) -> dict:
        """Publica una imagen o carousel-single en el feed. Devuelve media_id + permalink reales."""
        self._require_configured()

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            container = await client.post(
                f"{self.GRAPH_API_BASE}/{self.business_account_id}/media",
                params={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self.access_token,
                },
            )
            self._raise_for_graph_error(container)
            creation_id = container.json()["id"]

            publish = await client.post(
                f"{self.GRAPH_API_BASE}/{self.business_account_id}/media_publish",
                params={"creation_id": creation_id, "access_token": self.access_token},
            )
            self._raise_for_graph_error(publish)
            media_id = publish.json()["id"]

            permalink_resp = await client.get(
                f"{self.GRAPH_API_BASE}/{media_id}",
                params={"fields": "permalink,timestamp", "access_token": self.access_token},
            )
            self._raise_for_graph_error(permalink_resp)
            permalink_data = permalink_resp.json()

        return {
            "media_id": media_id,
            "permalink": permalink_data.get("permalink"),
            "posted_at": permalink_data.get("timestamp"),
        }

    async def publish_reel(self, video_url: str, caption: str, cover_url: str | None = None) -> dict:
        """Publica un reel. Video necesita procesamiento async -> polling de status_code."""
        self._require_configured()

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            params = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": self.access_token,
            }
            if cover_url:
                params["cover_url"] = cover_url

            container = await client.post(
                f"{self.GRAPH_API_BASE}/{self.business_account_id}/media", params=params
            )
            self._raise_for_graph_error(container)
            creation_id = container.json()["id"]

            status = await self._poll_container_ready(client, creation_id)
            if status != "FINISHED":
                raise InstagramPublishError(
                    f"El contenedor de video no terminó de procesar (status={status})",
                    detail={"creation_id": creation_id, "status": status},
                )

            publish = await client.post(
                f"{self.GRAPH_API_BASE}/{self.business_account_id}/media_publish",
                params={"creation_id": creation_id, "access_token": self.access_token},
            )
            self._raise_for_graph_error(publish)
            media_id = publish.json()["id"]

            permalink_resp = await client.get(
                f"{self.GRAPH_API_BASE}/{media_id}",
                params={"fields": "permalink,timestamp", "access_token": self.access_token},
            )
            self._raise_for_graph_error(permalink_resp)
            permalink_data = permalink_resp.json()

        return {
            "media_id": media_id,
            "permalink": permalink_data.get("permalink"),
            "posted_at": permalink_data.get("timestamp"),
        }

    async def _poll_container_ready(
        self, client: httpx.AsyncClient, creation_id: str, max_attempts: int = 20, interval_seconds: int = 5
    ) -> str:
        for _ in range(max_attempts):
            resp = await client.get(
                f"{self.GRAPH_API_BASE}/{creation_id}",
                params={"fields": "status_code", "access_token": self.access_token},
            )
            self._raise_for_graph_error(resp)
            status = resp.json().get("status_code")
            if status in ("FINISHED", "ERROR", "EXPIRED"):
                return status
            await asyncio.sleep(interval_seconds)
        return "TIMEOUT"

    @staticmethod
    def _raise_for_graph_error(response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = {"raw": response.text}
            error_message = detail.get("error", {}).get("message", "Error desconocido de Graph API")
            raise InstagramPublishError(f"Graph API error: {error_message}", detail=detail)
