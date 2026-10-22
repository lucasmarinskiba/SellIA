"""Content Generation Integrations

Sistema inteligente de generación de contenido con IA que:
- Enruta a la API más económica según calidad requerida
- Cachea prompts y resultados en Redis
- Controla presupuestos por negocio
- Comprime assets para reducir costos de DB y storage
"""

from .budget import BudgetController
from .cache import ContentCache
from .router import ContentGenerationRouter

__all__ = ["BudgetController", "ContentCache", "ContentGenerationRouter"]
