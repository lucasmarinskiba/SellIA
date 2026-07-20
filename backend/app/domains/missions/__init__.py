"""SellIA Missions Domain

Módulos de lógica de negocio para misiones, diagnósticos, playbooks
y asistentes especializados (shipping, ad spend).
"""

from .shipping_assistant import ShippingConnectorAssistant
from .ad_spend_assistant import AdSpendAssistant

__all__ = [
    "ShippingConnectorAssistant",
    "AdSpendAssistant",
]
