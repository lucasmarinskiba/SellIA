"""MercadoLibre Connector.

Handles buyer messages via MercadoLibre Messaging API and order notifications.
Docs: https://developers.mercadolibre.com.ar/
"""

import httpx
from datetime import datetime, timezone
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class MercadoLibreAuthError(Exception):
    """El token de MercadoLibre no sirve: vencido, revocado o ausente."""


class MercadoLibreAPIError(Exception):
    """MercadoLibre respondió con error. Se conservan el status y el mensaje de ML."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"MercadoLibre {status_code}: {message}")
        self.status_code = status_code
        self.message = message


def _error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text[:200]
    if isinstance(body, dict):
        return str(body.get("message") or body.get("error") or body)[:200]
    return str(body)[:200]


def _ml_datetime(value: datetime) -> str:
    """Formato que espera /orders/search: ISO UTC con milisegundos y offset."""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")


async def refresh_credentials(credentials: dict[str, Any]) -> dict[str, Any] | None:
    """Credenciales con access_token nuevo, o None si ML no quiso renovarlo."""
    refresh_token = credentials.get("refresh_token")
    if not refresh_token:
        return None
    from app.core.oauth_connectors import MercadoLibreOAuth

    data = await MercadoLibreOAuth.refresh_token(refresh_token)
    if not data.get("access_token"):
        return None
    return {
        **credentials,
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", refresh_token),
    }


class MercadoLibreConnector(BaseChannelConnector):
    """Conector para MercadoLibre: mensajes, notificaciones, publicación y órdenes."""
    platform = "mercadolibre"
    BASE_URL = "https://api.mercadolibre.com"

    def __init__(
        self,
        credentials: dict[str, Any],
        settings: dict[str, Any],
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.seller_id = credentials.get("seller_id")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        # Inyectable para tests (httpx.MockTransport); None usa la red real.
        self._transport = transport

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        if not self.access_token:
            raise MercadoLibreAuthError("Falta access_token de MercadoLibre")
        async with httpx.AsyncClient(transport=self._transport, timeout=30) as client:
            response = await client.request(
                method,
                f"{self.BASE_URL}{path}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json=json_body,
                params=params,
            )
        if response.status_code == 401:
            raise MercadoLibreAuthError("Token de MercadoLibre vencido o inválido")
        if response.status_code >= 400:
            raise MercadoLibreAPIError(response.status_code, _error_message(response))
        return response.json() if response.content else {}

    async def create_product(self, product: dict[str, Any]) -> dict[str, Any]:
        """Publica un item (POST /items). La descripción va en su propio endpoint."""
        body = dict(product)
        description = (body.pop("description", None) or {}).get("plain_text", "")
        item = await self._request("POST", "/items", json_body=body)
        if description:
            await self._request("POST", f"/items/{item['id']}/description", json_body={"plain_text": description})
        return {"id": item["id"], "permalink": item.get("permalink")}

    async def update_item(
        self,
        item_id: str,
        *,
        price: float | None = None,
        available_quantity: int | None = None,
    ) -> dict[str, Any]:
        """Actualiza precio y/o stock de una publicación (PUT /items/{id}). Lo None no se envía."""
        body: dict[str, Any] = {}
        if price is not None:
            body["price"] = price
        if available_quantity is not None:
            body["available_quantity"] = available_quantity
        if not body:
            return {}
        return await self._request("PUT", f"/items/{item_id}", json_body=body)

    async def list_orders(
        self,
        created_from: datetime | None = None,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Órdenes del vendedor, más recientes primero, con el detalle completo."""
        if not self.seller_id:
            raise ValueError("Falta seller_id de MercadoLibre")
        params: dict[str, Any] = {
            "seller": self.seller_id,
            "sort": "date_desc",
            "limit": limit,
            "offset": offset,
        }
        if created_from is not None:
            params["order.date_created.from"] = _ml_datetime(created_from)
        data = await self._request("GET", "/orders/search", params=params)
        return data.get("results", [])

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.access_token:
            raise ValueError("Falta access_token de MercadoLibre")

        # MercadoLibre messaging API: POST /messages
        # recipient_id is typically the order_id or buyer_id + item combination
        url = f"{self.BASE_URL}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "from": {"user_id": self.seller_id},
            "to": {"user_id": recipient_id},
            "text": content,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse MercadoLibre notification payload.
        
        ML sends topics like:
        - messages: new buyer message
        - orders: new order, payment, shipping update
        - questions: product question
        """
        topic = raw_payload.get("topic", "")
        resource = raw_payload.get("resource", "")
        user_id = raw_payload.get("user_id")

        # Try to extract data from the resource URL or nested data
        data = raw_payload.get("data", {})
        
        if topic == "messages" or "messages" in resource:
            # Message notification
            message_data = data.get("message", {})
            from_data = message_data.get("from", {})
            to_data = message_data.get("to", {})
            
            # Determine if this is inbound (from buyer to seller)
            from_user_id = str(from_data.get("user_id", ""))
            is_inbound = from_user_id != str(self.seller_id) if self.seller_id else True
            
            if is_inbound:
                return WebhookPayload(
                    platform=ChannelPlatform.MERCADOLIBRE,
                    external_id=from_user_id,
                    sender_id=from_user_id,
                    sender_name=from_data.get("name", "Comprador ML"),
                    content=message_data.get("text", ""),
                    content_type="text",
                    extra_data=raw_payload,
                )
        
        elif topic == "questions" or "questions" in resource:
            # Product question
            question_data = data.get("question", {})
            from_data = question_data.get("from", {})
            
            return WebhookPayload(
                platform=ChannelPlatform.MERCADOLIBRE,
                external_id=str(from_data.get("id", user_id or "unknown")),
                sender_id=str(from_data.get("id", "")),
                sender_name=from_data.get("name", "Comprador ML"),
                content=question_data.get("text", ""),
                content_type="text",
                extra_data=raw_payload,
            )
        
        elif topic == "orders" or "orders" in resource:
            # Order notification - create a system message
            order_data = data.get("order", {})
            buyer_data = order_data.get("buyer", {})
            order_id = order_data.get("id", "")
            
            return WebhookPayload(
                platform=ChannelPlatform.MERCADOLIBRE,
                external_id=str(buyer_data.get("id", user_id or "unknown")),
                sender_id=str(buyer_data.get("id", "")),
                sender_name=buyer_data.get("nickname", "Comprador ML"),
                content=f"Nueva orden #{order_id} en MercadoLibre",
                content_type="system",
                extra_data=raw_payload,
            )

        # Generic fallback
        return WebhookPayload(
            platform=ChannelPlatform.MERCADOLIBRE,
            external_id=str(user_id or "unknown"),
            sender_name="MercadoLibre",
            content=f"Notificación: {topic}",
            content_type="system",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            url = f"{self.BASE_URL}/users/me"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
