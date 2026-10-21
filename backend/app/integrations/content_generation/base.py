"""Base provider interface for content generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    url: str | None = None
    text_content: str | None = None
    local_path: str | None = None
    cost_usd: float = 0.0
    model_used: str = ""
    quality_tier: ContentQuality = ContentQuality.STANDARD
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    metadata: dict[str, Any] = None
    error_message: str | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class GenerationConfig:
    """Configuración para generación de contenido."""
    prompt: str
    content_type: ContentType
    quality: ContentQuality = ContentQuality.STANDARD
    negative_prompt: str | None = None
    width: int | None = None
    height: int | None = None
    aspect_ratio: str | None = None  # 16:9, 9:16, 1:1, etc.
    duration_seconds: int | None = None
    num_frames: int | None = None
    seed: int | None = None
    num_variations: int = 1
    style: str | None = None
    reference_image_url: str | None = None
    reference_audio_url: str | None = None
    extra_params: dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class BaseProvider(ABC):
    """Interfaz base para proveedores de generación de contenido."""

    name: str = ""
    slug: str = ""
    supports: list[ContentType] = []

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Retorna True si el proveedor está configurado y disponible."""

    @abstractmethod
    async def generate(self, config: GenerationConfig) -> GenerationResult:
        """Genera contenido según la configuración."""

    @abstractmethod
    def estimate_cost(self, config: GenerationConfig) -> float:
        """Estima el costo en USD de la generación."""

    @abstractmethod
    def get_pricing_table(self) -> dict[str, float]:
        """Retorna tabla de precios por unidad."""

    def supports_quality(self, quality: ContentQuality) -> bool:
        """Verifica si soporta un tier de calidad."""
        return True  # Por defecto, todos soportan todos
