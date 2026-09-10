"""What SellIA can really do on each platform, read off the connector classes.

The connectors are wildly uneven: Amazon's implements get_orders,
get_order_items, get_inventory and catalog push/pull; TikTok Shop can list
orders, sync products, update stock and create shipments; Hotmart lists sales;
MercadoLibre and WooCommerce currently do messages and webhooks only.

A hand-written table of "features per platform" would drift from that the first
time a connector gains or loses a method, and a UI promising order sync on a
platform whose connector cannot do it is the same class of lie this codebase has
been removing all along. So the matrix is derived by introspection: a capability
exists if the method that implements it exists on the connector class.
"""

from __future__ import annotations

from typing import Any

#: capability -> (label, what it means for the seller, connector method names).
#: A capability is available when the connector defines ANY of its methods.
CAPABILITY_SPECS: dict[str, dict[str, Any]] = {
    "messages": {
        "label": "Responder mensajes",
        "detail": "La IA contesta las consultas que entran por esta plataforma.",
        "methods": ["send_message"],
    },
    "orders": {
        "label": "Traer ventas",
        "detail": "Importar las órdenes reales para ver facturación y márgenes.",
        "methods": ["get_orders", "list_orders", "list_sales"],
    },
    "catalog_push": {
        "label": "Publicar productos",
        "detail": "Subir o actualizar tus publicaciones desde SellIA.",
        "methods": ["push_catalog_item", "sync_products_to_tiktok"],
    },
    "catalog_pull": {
        "label": "Importar publicaciones",
        "detail": "Traer lo que ya tenés publicado en la plataforma.",
        "methods": ["pull_catalog_items"],
    },
    "inventory": {
        "label": "Actualizar stock",
        "detail": "Mantener el stock sincronizado para no vender lo que no tenés.",
        "methods": ["update_inventory", "get_inventory"],
    },
    "shipping": {
        "label": "Generar envíos",
        "detail": "Crear el envío desde SellIA cuando entra una venta.",
        "methods": ["create_shipment"],
    },
}


def _connector_class(platform: str):
    """The real connector class for a platform, or None.

    Read straight out of CONNECTOR_REGISTRY rather than instantiated: nothing
    here should construct a connector, and no platform credentials are involved
    in answering "what could this platform do".
    """
    from app.domains.channels.connectors import CONNECTOR_REGISTRY
    from app.domains.channels.models import ChannelPlatform

    try:
        return CONNECTOR_REGISTRY.get(ChannelPlatform(platform))
    except (ValueError, KeyError):
        return None


def capabilities_for(platform: str) -> dict[str, bool]:
    """Which capabilities this platform's connector really implements."""
    connector_cls = _connector_class(platform)
    if connector_cls is None:
        return {key: False for key in CAPABILITY_SPECS}

    return {
        key: any(
            callable(getattr(connector_cls, method, None))
            for method in spec["methods"]
        )
        for key, spec in CAPABILITY_SPECS.items()
    }


def describe(platform: str) -> list[dict[str, Any]]:
    """Capability list for the UI: label, meaning, and whether it is real here."""
    available = capabilities_for(platform)
    return [
        {
            "key": key,
            "label": spec["label"],
            "detail": spec["detail"],
            "available": available.get(key, False),
        }
        for key, spec in CAPABILITY_SPECS.items()
    ]


def can(platform: str, capability: str) -> bool:
    return capabilities_for(platform).get(capability, False)


def order_method(platform: str):
    """The connector method that actually pulls orders, whatever it is called."""
    connector_cls = _connector_class(platform)
    if connector_cls is None:
        return None
    for method in CAPABILITY_SPECS["orders"]["methods"]:
        if callable(getattr(connector_cls, method, None)):
            return method
    return None
