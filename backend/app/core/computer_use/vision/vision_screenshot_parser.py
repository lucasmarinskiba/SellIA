"""Vision Screenshot Parser — Extract All Page Data

Responsibilities:
- Extract all text (OCR)
- Identify all UI elements (buttons, links, inputs, images)
- Understand page structure (hierarchy, spacing)
- Detect breakpoints (desktop, mobile, tablet)
- Identify image content (product photos, logos, etc)

Comprehensive page understanding.
"""

import logging
import base64
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ViewportSize(Enum):
    """Tamaño de viewport detectado."""
    MOBILE = "mobile"  # < 600px
    TABLET = "tablet"  # 600-1000px
    DESKTOP = "desktop"  # >= 1000px


@dataclass
class ImageContent:
    """Información de imagen detectada."""
    url: Optional[str] = None
    alt_text: Optional[str] = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    content_type: str = "unknown"  # "logo", "product", "banner", "icon", "photo"
    confidence: float = 0.8


@dataclass
class Heading:
    """Encabezado (H1-H6)."""
    level: int  # 1-6
    text: str
    x: int
    y: int
    font_size: int = 0
    importance: float = 1.0


@dataclass
class PageMetadata:
    """Metadata extraído de página."""
    title: str
    description: Optional[str] = None
    lang: str = "es"
    charset: str = "utf-8"
    viewport_size_type: ViewportSize = ViewportSize.DESKTOP
    is_responsive: bool = False
    has_mobile_menu: bool = False


@dataclass
class PageStructure:
    """Estructura completa de página."""
    metadata: PageMetadata
    headings: List[Heading]
    images: List[ImageContent]
    text_hierarchy: List[Dict[str, Any]]
    all_text: str
    unique_text_regions: int
    element_count: int
    link_count: int
    button_count: int
    form_count: int
    table_count: int
    list_count: int


class VisionScreenshotParser:
    """Parser visual completo de screenshots."""

    def __init__(self, anthropic_client=None):
        self.anthropic = anthropic_client

    async def parse_complete_page(
        self,
        screenshot_bytes: bytes,
        url: Optional[str] = None
    ) -> PageStructure:
        """Parsea completamente una página."""
        if not self.anthropic:
            raise ValueError("Anthropic client required")

        logger.info("Parsing complete page structure")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """Analiza COMPLETA y exhaustivamente esta página web.

ESTRUCTURA A EXTRAER:
1. METADATA: Título, descripción, lenguaje
2. HEADINGS: Todos los H1-H6 con posición
3. IMÁGENES: Todas las imágenes (logos, productos, banners)
4. JERARQUÍA DE TEXTO: Estructura lógica (qué es importante, subtítulos, etc)
5. ELEMENTOS: Contar botones, links, forms, tables, listas
6. VIEWPORT: Desktop/Tablet/Mobile, responsive?
7. SEMANTIC: Estructura HTML semántica (article, section, nav, aside)

Responde SOLO en JSON:
{
  "metadata": {
    "title": "...",
    "description": "...",
    "lang": "es",
    "viewport_size_type": "desktop|tablet|mobile",
    "is_responsive": true|false,
    "has_mobile_menu": false
  },
  "headings": [
    {"level": 1, "text": "Main Title", "x": 0, "y": 20, "font_size": 32, "importance": 1.0}
  ],
  "images": [
    {"url": null, "alt_text": "Company logo", "x": 10, "y": 5, "width": 80, "height": 30, "content_type": "logo"}
  ],
  "text_hierarchy": [
    {"type": "heading", "level": 1, "text": "..."},
    {"type": "paragraph", "text": "..."},
    {"type": "list_item", "text": "..."}
  ],
  "all_text": "Complete concatenated text",
  "unique_text_regions": 25,
  "element_counts": {
    "total": 120,
    "links": 15,
    "buttons": 5,
    "forms": 2,
    "tables": 1,
    "lists": 3
  },
  "semantic_structure": ["header", "nav", "main", "footer"],
  "confidence": 0.92
}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=4500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            data = json.loads(response_text)

            return self._parse_page_structure(data)

        except Exception as e:
            logger.error(f"Page parsing failed: {e}")
            raise

    async def extract_all_text(
        self,
        screenshot_bytes: bytes
    ) -> str:
        """Extrae todo el texto de la página."""
        logger.info("Extracting all text")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """Extrae TODO el texto visible en este screenshot.

Incluye:
- Headings
- Body text
- Button labels
- Form field labels
- Links
- Navigation items
- Any other visible text

Responde SOLO el texto concatenado (no JSON)."""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""

    async def identify_all_ui_elements(
        self,
        screenshot_bytes: bytes
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Identifica TODOS los elementos UI."""
        logger.info("Identifying all UI elements")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """Identifica y enumera TODOS los elementos interactivos de la UI.

ELEMENTOS A DETECTAR:
- Buttons (todos, con labels exactos)
- Links (href visible o destino inferido)
- Input fields (text, email, password, number, date, etc)
- Checkboxes
- Radio buttons
- Dropdowns/Select
- Textareas
- File uploads
- Toggle switches
- Sliders
- Navigation items
- Search boxes
- Forms

Responde SOLO en JSON:
{
  "buttons": [
    {"label": "...", "type": "primary|secondary|tertiary|danger", "visible": true}
  ],
  "links": [
    {"text": "...", "destination": "...", "type": "internal|external"}
  ],
  "inputs": [
    {"label": "...", "type": "text|email|password|number", "required": false}
  ],
  "forms": [
    {"id": "...", "fields": 5, "has_submit": true}
  ],
  "total_interactive_elements": 25,
  "by_category": {
    "buttons": 5,
    "links": 12,
    "inputs": 6,
    "other": 2
  }
}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=2500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            return json.loads(response_text)

        except Exception as e:
            logger.error(f"UI element identification failed: {e}")
            return {}

    async def detect_viewport_size(
        self,
        screenshot_bytes: bytes,
        actual_width: Optional[int] = None
    ) -> Tuple[ViewportSize, bool]:
        """Detecta tamaño de viewport y si es responsive.

        Returns:
            (viewport_type, is_responsive)
        """
        logger.info("Detecting viewport size")

        if actual_width:
            if actual_width < 600:
                return ViewportSize.MOBILE, True
            elif actual_width < 1000:
                return ViewportSize.TABLET, True
            else:
                return ViewportSize.DESKTOP, True

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """¿Qué tamaño de viewport es este?

Basándote en:
- Tamaño de elementos
- Número de columnas
- Tamaño de texto
- Tamaño de botones

¿Es MOBILE (<600px), TABLET (600-1000px) o DESKTOP (>1000px)?
¿Se ve responsive (ajusta bien a diferentes tamaños)?

Responde SOLO: {"viewport_size": "mobile|tablet|desktop", "is_responsive": true|false, "confidence": 0.9}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            data = json.loads(response_text)

            size_map = {
                "mobile": ViewportSize.MOBILE,
                "tablet": ViewportSize.TABLET,
                "desktop": ViewportSize.DESKTOP,
            }

            return (
                size_map.get(data.get("viewport_size", "desktop"), ViewportSize.DESKTOP),
                data.get("is_responsive", False)
            )

        except Exception as e:
            logger.error(f"Viewport detection failed: {e}")
            return ViewportSize.DESKTOP, False

    async def identify_images(
        self,
        screenshot_bytes: bytes
    ) -> List[ImageContent]:
        """Identifica todas las imágenes en la página."""
        logger.info("Identifying images")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """Identifica TODAS las imágenes en esta página.

Para cada imagen, determina:
- Tipo de contenido (logo, product, banner, icon, photo, screenshot, etc)
- Alt text o descripción visible
- Posición aproximada
- Tamaño relativo

Responde SOLO en JSON:
{
  "images": [
    {"alt_text": "Company logo", "content_type": "logo", "x": 10, "y": 5, "width": 80, "height": 30},
    {"alt_text": "Product photo", "content_type": "product", "x": 20, "y": 100, "width": 150, "height": 200}
  ],
  "total_images": 5,
  "image_types_detected": ["logo", "product", "banner"]
}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = response.content[0].text
            data = json.loads(response_text)

            images = []
            for img_data in data.get("images", []):
                images.append(ImageContent(
                    alt_text=img_data.get("alt_text"),
                    content_type=img_data.get("content_type", "unknown"),
                    x=img_data.get("x", 0),
                    y=img_data.get("y", 0),
                    width=img_data.get("width", 0),
                    height=img_data.get("height", 0),
                ))

            return images

        except Exception as e:
            logger.error(f"Image identification failed: {e}")
            return []

    def _parse_page_structure(self, data: Dict[str, Any]) -> PageStructure:
        """Parsea la estructura de página."""
        metadata_data = data.get("metadata", {})
        viewport_str = metadata_data.get("viewport_size_type", "desktop").lower()
        viewport_map = {
            "mobile": ViewportSize.MOBILE,
            "tablet": ViewportSize.TABLET,
            "desktop": ViewportSize.DESKTOP,
        }

        metadata = PageMetadata(
            title=metadata_data.get("title", ""),
            description=metadata_data.get("description"),
            lang=metadata_data.get("lang", "es"),
            viewport_size_type=viewport_map.get(viewport_str, ViewportSize.DESKTOP),
            is_responsive=metadata_data.get("is_responsive", False),
            has_mobile_menu=metadata_data.get("has_mobile_menu", False),
        )

        headings = [
            Heading(
                level=h.get("level", 1),
                text=h.get("text", ""),
                x=h.get("x", 0),
                y=h.get("y", 0),
                font_size=h.get("font_size", 0),
                importance=h.get("importance", 1.0),
            )
            for h in data.get("headings", [])
        ]

        images = [
            ImageContent(
                url=img.get("url"),
                alt_text=img.get("alt_text"),
                x=img.get("x", 0),
                y=img.get("y", 0),
                width=img.get("width", 0),
                height=img.get("height", 0),
                content_type=img.get("content_type", "unknown"),
            )
            for img in data.get("images", [])
        ]

        element_counts = data.get("element_counts", {})

        return PageStructure(
            metadata=metadata,
            headings=headings,
            images=images,
            text_hierarchy=data.get("text_hierarchy", []),
            all_text=data.get("all_text", ""),
            unique_text_regions=data.get("unique_text_regions", 0),
            element_count=element_counts.get("total", 0),
            link_count=element_counts.get("links", 0),
            button_count=element_counts.get("buttons", 0),
            form_count=element_counts.get("forms", 0),
            table_count=element_counts.get("tables", 0),
            list_count=element_counts.get("lists", 0),
        )

    async def get_page_summary(self, screenshot_bytes: bytes) -> str:
        """Retorna resumen legible de la página."""
        structure = await self.parse_complete_page(screenshot_bytes)

        lines = [
            f"PAGE TITLE: {structure.metadata.title}",
            f"DESCRIPTION: {structure.metadata.description or 'N/A'}",
            f"VIEWPORT: {structure.metadata.viewport_size_type.value}",
            f"RESPONSIVE: {structure.metadata.is_responsive}",
            f"",
            f"HEADINGS ({len(structure.headings)}):",
        ]

        for h in structure.headings[:5]:
            lines.append(f"  H{h.level}: {h.text}")

        lines.extend([
            f"",
            f"ELEMENTS:",
            f"  Total: {structure.element_count}",
            f"  Buttons: {structure.button_count}",
            f"  Links: {structure.link_count}",
            f"  Forms: {structure.form_count}",
            f"  Tables: {structure.table_count}",
            f"  Lists: {structure.list_count}",
            f"  Images: {len(structure.images)}",
            f"",
            f"IMAGES:",
        ])

        for img in structure.images[:5]:
            lines.append(f"  - {img.alt_text or 'no alt'} ({img.content_type})")

        lines.append(f"")
        lines.append(f"TEXT ({len(structure.all_text)} chars):")
        lines.append(structure.all_text[:300])

        return "\n".join(lines)
