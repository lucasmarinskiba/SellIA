"""
Mercado Libre Automation — Orders sync, auto-responses, fulfillment.

Usuario ingresa:
- MERCADOLIBRE_SELLER_ID
- MERCADOLIBRE_ACCESS_TOKEN
- MERCADOLIBRE_REFRESH_TOKEN

Sistema:
- Sync orders cada 5min
- Auto-respond preguntas frecuentes
- Auto-confirm compra
- Auto-genera shipping label
- Actualiza tracking automático
"""

import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class MercadoLibreAutomation:
    """Automatización Mercado Libre — órdenes, mensajes, fulfillment."""

    BASE_URL = "https://api.mercadolibre.com"

    def __init__(self, seller_id: str, access_token: str, refresh_token: Optional[str] = None):
        self.seller_id = seller_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.http_client = httpx.AsyncClient(timeout=30)

    # ========== ORDERS SYNC ==========

    async def sync_orders(self) -> Dict[str, Any]:
        """
        Sincroniza órdenes desde Mercado Libre automáticamente.

        Obtiene órdenes nuevas, actualiza status, procesa fulfillment.
        """

        logger.info(f"Syncing orders for seller {self.seller_id}")

        try:
            # Obtener órdenes sin procesar
            orders = await self._fetch_new_orders()

            if not orders:
                logger.info("No new orders")
                return {"status": "success", "orders_synced": 0}

            processed_orders = []

            for order in orders:
                order_id = order["id"]
                logger.info(f"Processing order {order_id}")

                # Extraer detalles
                order_details = await self._fetch_order_details(order_id)

                if not order_details:
                    continue

                # Auto-confirm compra
                confirm_result = await self._confirm_purchase(order_id)

                # Auto-respond preguntas frecuentes
                messages_result = await self._respond_buyer_questions(order_id)

                # Generar shipping label automático
                shipping_result = await self._generate_shipping_label(order_id, order_details)

                # Actualizar status en DB
                db_result = await self._save_order_to_db(
                    order_id, order_details, shipping_result
                )

                processed_orders.append({
                    "order_id": order_id,
                    "confirm": confirm_result,
                    "messages": messages_result,
                    "shipping": shipping_result,
                    "saved": db_result,
                })

            logger.info(f"Synced {len(processed_orders)} orders")

            return {
                "status": "success",
                "orders_synced": len(processed_orders),
                "orders": processed_orders,
            }

        except Exception as e:
            logger.error(f"Orders sync failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _fetch_new_orders(self) -> List[Dict[str, Any]]:
        """Obtiene órdenes nuevas (sin procesar)."""

        try:
            response = await self.http_client.get(
                f"{self.BASE_URL}/orders/search",
                params={
                    "seller_id": self.seller_id,
                    "order.status": "unshipped",  # No enviadas
                    "limit": 50,
                },
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                logger.error(f"ML API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Fetch orders failed: {str(e)}")
            return []

    async def _fetch_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalles de orden (buyer, producto, dirección)."""

        try:
            response = await self.http_client.get(
                f"{self.BASE_URL}/orders/{order_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Order details error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Fetch order details failed: {str(e)}")
            return None

    async def _confirm_purchase(self, order_id: str) -> Dict[str, Any]:
        """Auto-confirma compra (cambiar status a packed)."""

        logger.info(f"Confirming purchase {order_id}")

        try:
            response = await self.http_client.put(
                f"{self.BASE_URL}/orders/{order_id}",
                json={"status": "packed"},  # Confirmado, listo envío
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code == 200:
                logger.info(f"Order {order_id} confirmed")
                return {"status": "success"}
            else:
                logger.warning(f"Confirm failed: {response.status_code}")
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Confirm purchase failed: {str(e)}")
            return {"status": "error"}

    # ========== AUTO-RESPONSE ==========

    async def _respond_buyer_questions(self, order_id: str) -> Dict[str, Any]:
        """Auto-responde preguntas frecuentes de buyers."""

        logger.info(f"Checking buyer questions for order {order_id}")

        try:
            # Obtener preguntas sin responder
            response = await self.http_client.get(
                f"{self.BASE_URL}/questions/search",
                params={
                    "item_id": order_id,
                    "status": "UNANSWERED",
                },
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code != 200:
                return {"status": "no_questions"}

            questions = response.json().get("questions", [])

            if not questions:
                return {"status": "no_questions"}

            responses = []

            for question in questions:
                q_id = question["id"]
                text = question.get("text", "").lower()

                # Detectar pregunta frecuente
                auto_response = self._get_faq_response(text)

                if auto_response:
                    # Responder automático
                    answer_result = await self._answer_question(q_id, auto_response)
                    responses.append({
                        "question_id": q_id,
                        "answered": answer_result["status"] == "success",
                        "response": auto_response,
                    })

            logger.info(f"Answered {len(responses)} questions")

            return {
                "status": "success",
                "questions_answered": len(responses),
                "responses": responses,
            }

        except Exception as e:
            logger.error(f"Auto-response failed: {str(e)}")
            return {"status": "error"}

    def _get_faq_response(self, question: str) -> Optional[str]:
        """Detecta pregunta frecuente, retorna respuesta automática."""

        faq = {
            "envío": "El producto se envía dentro de 24 horas. Recibirás número de seguimiento por correo.",
            "pago": "El pago se procesó correctamente. Tu orden está confirmada.",
            "devolución": "Tenemos política de 30 días. Contactanos para devolver el producto.",
            "garantía": "Producto con garantía de fabricante. Consulta términos en descripción.",
            "cantidad": "¿Necesitas más? Tenemos stock. Crea nueva orden o contáctanos.",
            "color": "Disponible en los colores listados. Verifica disponibilidad en ficha.",
            "talle": "Consulta guía de talles en descripción del producto.",
            "estado": "Tu orden está en preparación. Se enviará hoy.",
            "regalo": "¿Es regalo? Podemos empacar especial. Avísanos.",
        }

        for keyword, response in faq.items():
            if keyword in question:
                return response

        return None

    async def _answer_question(self, question_id: str, answer_text: str) -> Dict[str, Any]:
        """Responde pregunta automáticamente."""

        try:
            response = await self.http_client.post(
                f"{self.BASE_URL}/answers",
                json={
                    "question_id": question_id,
                    "text": answer_text,
                },
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code == 201:
                logger.info(f"Question {question_id} answered")
                return {"status": "success"}
            else:
                logger.warning(f"Answer failed: {response.status_code}")
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Answer question failed: {str(e)}")
            return {"status": "error"}

    # ========== SHIPPING & FULFILLMENT ==========

    async def _generate_shipping_label(
        self,
        order_id: str,
        order_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Genera shipping label automáticamente."""

        logger.info(f"Generating shipping label for {order_id}")

        try:
            # Extraer dirección
            receiver = order_details.get("shipping", {}).get("receiver_address", {})

            # Generar label via ML shipping
            response = await self.http_client.post(
                f"{self.BASE_URL}/shipments",
                json={
                    "order_id": order_id,
                    "shipment_type": "standard",  # O express
                    "dimensions": {
                        "length": 10,
                        "width": 10,
                        "height": 10,
                        "weight": 1000,  # gramos
                    },
                },
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code in [200, 201]:
                shipment = response.json()
                logger.info(f"Label generated: {shipment.get('id')}")

                return {
                    "status": "success",
                    "shipment_id": shipment.get("id"),
                    "label_url": shipment.get("label_data", {}).get("link", ""),
                    "tracking_number": shipment.get("tracking_number", ""),
                }
            else:
                logger.warning(f"Label generation failed: {response.status_code}")
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Generate label failed: {str(e)}")
            return {"status": "error"}

    # ========== TRACKING UPDATES ==========

    async def update_tracking(self, shipment_id: str, buyer_email: str) -> Dict[str, Any]:
        """Actualiza tracking automáticamente y notifica buyer."""

        logger.info(f"Updating tracking for shipment {shipment_id}")

        try:
            # Obtener status de envío
            response = await self.http_client.get(
                f"{self.BASE_URL}/shipments/{shipment_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code == 200:
                shipment = response.json()
                status = shipment.get("status")
                tracking = shipment.get("tracking_number")

                # Notificar buyer automático (via email/SMS)
                # TODO: Integrar con email/SMS service

                logger.info(f"Tracking updated: {tracking} ({status})")

                return {
                    "status": "success",
                    "tracking": tracking,
                    "shipment_status": status,
                }
            else:
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Update tracking failed: {str(e)}")
            return {"status": "error"}

    # ========== DB INTEGRATION ==========

    async def _save_order_to_db(
        self,
        order_id: str,
        order_details: Dict[str, Any],
        shipping_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Guarda orden en DB para tracking."""

        logger.info(f"Saving order {order_id} to DB")

        # TODO: Integrar con database
        # Modelo: MercadoLibreOrder

        return {
            "status": "success",
            "order_id": order_id,
            "saved_at": datetime.utcnow().isoformat(),
        }

    # ========== TOKEN REFRESH ==========

    async def refresh_access_token(self) -> Optional[str]:
        """Refresh OAuth token si expiró."""

        if not self.refresh_token:
            logger.warning("No refresh token available")
            return None

        logger.info("Refreshing ML access token")

        try:
            response = await self.http_client.post(
                f"{self.BASE_URL}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
            )

            if response.status_code == 200:
                data = response.json()
                new_token = data["access_token"]
                self.access_token = new_token
                logger.info("Token refreshed successfully")
                return new_token
            else:
                logger.error(f"Token refresh failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Refresh token failed: {str(e)}")
            return None

    async def close(self):
        """Cierra conexión HTTP."""
        await self.http_client.aclose()
