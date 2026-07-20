"""Base provider interface for content generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ContentQuality(str, Enum):
    """Quality tier for generation."""
    DRAFT = "draft"          # Más barato, para previews/iteración
    STANDARD = "standard"    # Balance calidad/costo
    PREMIUM = "premium"      # Máxima calidad, más caro


class ContentType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    COPY = "copy"


@dataclass
class GenerationResult:
    """Resultado de una generación de contenido."""
    success: bool
    url: Optional[str] = None
    text_content: Optional[str] = None
    local_path: Optional[str] = None
    cost_usd: float = 0.0
    model_used: str = ""
    quality_tier: ContentQuality = ContentQuality.STANDARD
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class GenerationConfig:
    """Configuración para generación de contenido."""
    prompt: str
    content_type: ContentType
    quality: ContentQuality = ContentQuality.STANDARD
    negative_prompt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None  # 16:9, 9:16, 1:1, etc.
    duration_seconds: Optional[int] = None
    num_frames: Optional[int] = None
    seed: Optional[int] = None
    num_variations: int = 1
    style: Optional[str] = None
    reference_image_url: Optional[str] = None
    reference_audio_url: Optional[str] = None
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class BaseProvider(ABC):
    """Interfaz base para proveedores de generación de contenido."""

    name: str = ""
    slug: str = ""
    supports: List[ContentType] = []

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Retorna True si el proveedor está configurado y disponible."""
        pass

    @abstractmethod
    async def generate(self, config: GenerationConfig) -> GenerationResult:
        """Genera contenido según la configuración."""
        pass

    @abstractmethod
    def estimate_cost(self, config: GenerationConfig) -> float:
        """Estima el costo en USD de la generación."""
        pass

    @abstractmethod
    def get_pricing_table(self) -> Dict[str, float]:
        """Retorna tabla de precios por unidad."""
        pass

    def supports_quality(self, quality: ContentQuality) -> bool:
        """Verifica si soporta un tier de calidad."""
        return True  # Por defecto, todos soportan todos
