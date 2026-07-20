"""
Shipping Automation — DHL/FedEx label generation + tracking + notifications.

Usuario ingresa:
- DHL_API_KEY + DHL_ACCOUNT_NUMBER
- FEDEX_API_KEY + FEDEX_ACCOUNT_NUMBER

Sistema:
- Auto-genera label post-pago
- Tracking automático
- Notifica buyer (WhatsApp/email)
- Integra con órdenes
"""

import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64

logger = logging.getLogger(__name__)


class ShippingAutomation:
    """Shipping automation — labels + tracking."""

    def __init__(
        self,
        dhl_api_key: Optional[str] = None,
        dhl_account: Optional[str] = None,
        fedex_api_key: Optional[str] = None,
        fedex_account: Optional[str] = None,
    ):
        self.dhl_api_key = dhl_api_key
        self.dhl_account = dhl_account
        self.fedex_api_key = fedex_api_key
        self.fedex_account = fedex_account
        self.http_client = httpx.AsyncClient(timeout=30)

    # ========== LABEL GENERATION ==========

    async def generate_shipping_label(
        self,
        order_id: str,
        recipient: Dict[str, str],  # {name, address, city, state, zip, country}
        sender: Dict[str, str],
        package: Dict[str, Any],  # {weight_kg, dimensions, contents}
        carrier: str = "dhl",  # "dhl" or "fedex"
    ) -> Dict[str, Any]:
        """
        Genera shipping label automáticamente.

        recipient: datos destino
        sender: datos origen
        package: peso + dimensiones
        carrier: DHL o FedEx
        """

        logger.info(f"Generating {carrier.upper()} label for order {order_id}")

        if carrier.lower() == "dhl":
            return await self._generate_dhl_label(order_id, recipient, sender, package)
        elif carrier.lower() == "fedex":
            return await self._generate_fedex_label(order_id, recipient, sender, package)
        else:
            return {"status": "error", "error": f"Carrier {carrier} not supported"}

    async def _generate_dhl_label(
        self,
        order_id: str,
        recipient: Dict[str, str],
        sender: Dict[str, str],
        package: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Genera label DHL."""

        logger.info(f"Generating DHL label for {order_id}")

        try:
            payload = {
                "shipments": [
                    {
                        "plannedShippingDateAndTime": datetime.utcnow().isoformat(),
                        "pickup": {
                            "isRequested": False,
                        },
                        "productCode": "N",  # N = DHL Express Nationwide
                        "account": self.dhl_account,
                        "customsDeclarations": None,
                        "requestedPackages": [
                            {
                                "weight": package.get("weight_kg", 1.0),
                                "dimensions": package.get("dimensions", {}),
                                "sequenceNumber": 1,
                            }
                        ],
                        "recipients": [
                            {
                                "postalAddress": {
                                    "postalCode": recipient.get("zip"),
                                    "cityName": recipient.get("city"),
                                    "countryCode": recipient.get("country", "AR"),
                                    "addressLine1": recipient.get("address"),
                                    "provinceCode": recipient.get("state"),
                                },
                                "unstructuredAddress": {
                                    "name": recipient.get("name"),
                                },
                                "contactInformation": {
                                    "phone": recipient.get("phone", ""),
                                    "email": recipient.get("email", ""),
                                },
                            }
                        ],
                        "shippers": [
                            {
                                "postalAddress": {
                                    "postalCode": sender.get("zip"),
                                    "cityName": sender.get("city"),
                                    "countryCode": sender.get("country", "AR"),
                                    "addressLine1": sender.get("address"),
                                    "provinceCode": sender.get("state"),
                                },
                                "unstructuredAddress": {
                                    "name": sender.get("name"),
                                },
                            }
                        ],
                    }
                ]
            }

            response = await self.http_client.post(
                "https://express.api.dhl.com/mydhl/shipments",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.dhl_api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code in [200, 201]:
                data = response.json()
                shipment = data.get("shipments", [{}])[0]

                logger.info(f"DHL label generated: {shipment.get('shipmentTrackingNumber')}")

                return {
                    "status": "success",
                    "carrier": "DHL",
                    "tracking_number": shipment.get("shipmentTrackingNumber"),
                    "label_url": shipment.get("documents", [{}])[0].get("content") if shipment.get("documents") else None,
                    "label_format": "PDF",
                }
            else:
                logger.error(f"DHL label failed: {response.status_code}")
                return {"status": "error", "error": response.text}

        except Exception as e:
            logger.error(f"DHL label generation failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _generate_fedex_label(
        self,
        order_id: str,
        recipient: Dict[str, str],
        sender: Dict[str, str],
        package: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Genera label FedEx."""

        logger.info(f"Generating FedEx label for {order_id}")

        try:
            payload = {
                "labelResponseOptions": "LABEL_ONLY",
                "requestedShipment": {
                    "shipper": {
                        "address": {
                            "streetLines": [sender.get("address", "")],
                            "city": sender.get("city", ""),
                            "stateOrProvinceCode": sender.get("state", ""),
                            "postalCode": sender.get("zip", ""),
                            "countryCode": sender.get("country", "AR"),
                        },
                        "contact": {
                            "personName": sender.get("name", ""),
                            "emailAddress": sender.get("email", ""),
                            "phoneNumber": sender.get("phone", ""),
                        },
                    },
                    "recipients": [
                        {
                            "address": {
                                "streetLines": [recipient.get("address", "")],
                                "city": recipient.get("city", ""),
                                "stateOrProvinceCode": recipient.get("state", ""),
                                "postalCode": recipient.get("zip", ""),
                                "countryCode": recipient.get("country", "AR"),
                            },
                            "contact": {
                                "personName": recipient.get("name", ""),
                                "emailAddress": recipient.get("email", ""),
                                "phoneNumber": recipient.get("phone", ""),
                            },
                        }
                    ],
                    "shipDatestamp": datetime.utcnow().strftime("%Y-%m-%d"),
                    "serviceType": "INTERNATIONAL_PRIORITY",
                    "packages": [
                        {
                            "weight": {
                                "units": "KG",
                                "value": package.get("weight_kg", 1.0),
                            },
                            "dimensions": package.get("dimensions", {}),
                        }
                    ],
                },
            }

            response = await self.http_client.post(
                "https://apis.fedex.com/ship/v1/shipments",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.fedex_api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code in [200, 201]:
                data = response.json()

                logger.info(f"FedEx label generated")

                return {
                    "status": "success",
                    "carrier": "FedEx",
                    "tracking_number": data.get("shipmentDetails", [{}])[0].get("trackingIds", [{}])[0].get("trackingNumber", ""),
                    "label_url": data.get("output", {}).get("transactionShipments", [{}])[0].get("shipmentDocuments", [{}])[0].get("url", ""),
                    "label_format": "PDF",
                }
            else:
                logger.error(f"FedEx label failed: {response.status_code}")
                return {"status": "error", "error": response.text}

        except Exception as e:
            logger.error(f"FedEx label generation failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ========== TRACKING ==========

    async def track_shipment(
        self,
        tracking_number: str,
        carrier: str,
    ) -> Dict[str, Any]:
        """Obtiene status de envío."""

        logger.info(f"Tracking {carrier} {tracking_number}")

        if carrier.lower() == "dhl":
            return await self._track_dhl(tracking_number)
        elif carrier.lower() == "fedex":
            return await self._track_fedex(tracking_number)
        else:
            return {"status": "error"}

    async def _track_dhl(self, tracking_number: str) -> Dict[str, Any]:
        """Track DHL shipment."""

        try:
            response = await self.http_client.get(
                f"https://express.api.dhl.com/mydhl/shipments/{tracking_number}/tracking",
                headers={"Authorization": f"Bearer {self.dhl_api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                shipment = data.get("shipments", [{}])[0]

                return {
                    "status": "success",
                    "carrier": "DHL",
                    "tracking_number": tracking_number,
                    "shipment_status": shipment.get("status", "UNKNOWN"),
                    "events": shipment.get("events", []),
                    "estimated_delivery": shipment.get("estimatedDeliveryDate"),
                }
            else:
                return {"status": "error"}

        except Exception as e:
            logger.error(f"DHL tracking failed: {str(e)}")
            return {"status": "error"}

    async def _track_fedex(self, tracking_number: str) -> Dict[str, Any]:
        """Track FedEx shipment."""

        try:
            payload = {
                "includeDetailedScans": True,
                "trackingInfo": [
                    {
                        "trackingNumberInfo": {
                            "trackingNumber": tracking_number,
                        }
                    }
                ],
            }

            response = await self.http_client.post(
                "https://apis.fedex.com/track/v1/trackedshipments",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.fedex_api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                data = response.json()
                shipment = data.get("shipments", [{}])[0]

                return {
                    "status": "success",
                    "carrier": "FedEx",
                    "tracking_number": tracking_number,
                    "shipment_status": shipment.get("statusCode"),
                    "events": shipment.get("events", []),
                    "estimated_delivery": shipment.get("estimatedDeliveryTimestamp"),
                }
            else:
                return {"status": "error"}

        except Exception as e:
            logger.error(f"FedEx tracking failed: {str(e)}")
            return {"status": "error"}

    async def close(self):
        """Cierra conexión HTTP."""
        await self.http_client.aclose()
