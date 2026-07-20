"""Content Generation Integrations

Sistema inteligente de generación de contenido con IA que:
- Enruta a la API más económica según calidad requerida
- Cachea prompts y resultados en Redis
- Controla presupuestos por negocio
- Comprime assets para reducir costos de DB y storage
"""

from .router import ContentGenerationRouter
from .cache import ContentCache
from .budget import BudgetController

__all__ = ["ContentGenerationRouter", "ContentCache", "BudgetController"]
