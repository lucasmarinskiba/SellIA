"""Visual Analyzer — Screenshot Understanding

Responsibilities:
- Screenshot OCR + text extraction
- Button detection (color, shape, position)
- Form field detection (input, select, textarea, checkbox)
- Layout understanding (header, nav, content, footer)
- Page type classification (login, product, checkout, etc)

No selectors needed. Pure visual understanding.
"""

import base64
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class TextRegion:
    """Texto extraído con posición."""
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.9


@dataclass
class ButtonDetection:
    """Botón detectado en pantalla."""
    label: str
    x: int
    y: int
    width: int
    height: int
    color: str
    shape: str  # "rounded", "rectangular", "circle"
    confidence: float = 0.9


@dataclass
class FormField:
    """Campo de formulario detectado."""
    label: str
    field_type: str  # "input", "select", "textarea", "checkbox", "radio"
    x: int
    y: int
    width: int
    height: int
    required: bool = False
    placeholder: Optional[str] = None
    confidence: float = 0.9


@dataclass
class LayoutRegion:
    """Región de layout (header, nav, content, footer)."""
    region_type: str  # "header", "nav", "content", "footer", "sidebar"
    x: int
    y: int
    width: int
    height: int
    elements_count: int = 0


@dataclass
class PageAnalysis:
    """Análisis completo de página."""
    page_type: str  # "login", "product", "checkout", "list", "form", "unknown"
    title: Optional[str] = None
    url: Optional[str] = None
    all_text: List[TextRegion] = None
    buttons: List[ButtonDetection] = None
    form_fields: List[FormField] = None
    layout_regions: List[LayoutRegion] = None
    navigation_items: List[str] = None
    images_detected: int = 0
    confidence_score: float = 0.85
    raw_response: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.all_text is None:
            self.all_text = []
        if self.buttons is None:
            self.buttons = []
        if self.form_fields is None:
            self.form_fields = []
        if self.layout_regions is None:
            self.layout_regions = []
        if self.navigation_items is None:
            self.navigation_items = []


class VisualAnalyzer:
    """Analiza screenshots usando Computer Vision.

    API backends:
    - Claude Vision (built-in, high accuracy)
    - Google Cloud Vision (backup, OCR + object detection)
    - Tesseract (local, offline)
    """

    def __init__(self, anthropic_client=None, google_vision_client=None):
        self.anthropic = anthropic_client
        self.google_vision = google_vision_client
        self.tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Verifica si Tesseract está disponible localmente."""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    async def analyze_screenshot(
        self,
        screenshot_bytes: bytes,
        url: Optional[str] = None,
        backend: str = "claude"
    ) -> PageAnalysis:
        """Analiza un screenshot completo.

        Args:
            screenshot_bytes: Imagen en bytes
            url: URL actual (opcional)
            backend: "claude", "google", "tesseract"

        Returns:
            PageAnalysis con elementos detectados
        """
        if backend == "claude" and self.anthropic:
            return await self._analyze_with_claude(screenshot_bytes, url)
        elif backend == "google" and self.google_vision:
            return await self._analyze_with_google_vision(screenshot_bytes, url)
        elif backend == "tesseract" and self.tesseract_available:
            return await self._analyze_with_tesseract(screenshot_bytes, url)
        else:
            # Fallback a Claude si está disponible
            if self.anthropic:
                return await self._analyze_with_claude(screenshot_bytes, url)
            else:
                raise ValueError(f"No vision backend available: {backend}")

    async def _analyze_with_claude(
        self,
        screenshot_bytes: bytes,
        url: Optional[str] = None
    ) -> PageAnalysis:
        """Claude Vision para análisis profundo."""
        logger.info("Analyzing screenshot with Claude Vision")

        screenshot_b64 = base64.standard_b64encode(screenshot_bytes).decode("utf-8")

        prompt = """Analiza este screenshot exhaustivamente.

Identifica y estructura:

1. TIPO DE PÁGINA: login, product, checkout, list, form, dashboard, error, loading, other
2. TITULO/HEADING: El título principal visible
3. TEXTO: Todo el texto visible (OCR)
4. BOTONES: Cada botón con:
   - Label exacto
   - Posición aproximada (x,y,width,height como % del viewport)
   - Color dominante
   - Forma (rounded, rectangular, circle)
5. CAMPOS DE FORMULARIO: Tipo, label, posición, requerido, placeholder
6. LAYOUT: Identificar regiones (header, nav, content, footer, sidebar)
7. NAVEGACIÓN: Items de menu/nav
8. IMÁGENES: Cantidad de imágenes/logos

Responde SOLO en JSON válido:
{
  "page_type": "...",
  "title": "...",
  "all_text": [{"text": "...", "x": 0, "y": 0, "width": 100, "height": 20}],
  "buttons": [{"label": "...", "x": 10, "y": 50, "width": 80, "height": 40, "color": "#FF0000", "shape": "rounded"}],
  "form_fields": [{"label": "...", "type": "input", "x": 10, "y": 100, "width": 200, "height": 30, "required": true, "placeholder": "..."}],
  "layout_regions": [{"type": "header", "x": 0, "y": 0, "width": 100, "height": 15}],
  "navigation_items": ["Home", "Products", ...],
  "images_detected": 5,
  "confidence_score": 0.95
}"""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
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

            return self._parse_claude_response(data, url)

        except Exception as e:
            logger.error(f"Claude Vision analysis failed: {e}")
            raise

    async def _analyze_with_google_vision(
        self,
        screenshot_bytes: bytes,
        url: Optional[str] = None
    ) -> PageAnalysis:
        """Google Cloud Vision API para OCR + object detection."""
        logger.info("Analyzing screenshot with Google Vision API")

        from google.cloud import vision as google_vision_lib

        try:
            client = google_vision_lib.ImageAnnotatorClient()
            image = google_vision_lib.Image(content=screenshot_bytes)

            # OCR
            response = await asyncio.to_thread(
                client.document_text_detection,
                image=image
            )

            texts = response.text_annotations
            all_text = self._parse_google_text_detection(texts)

            # Object detection
            response_objects = await asyncio.to_thread(
                client.object_localization,
                image=image
            )

            analysis = PageAnalysis(
                page_type="unknown",
                url=url,
                all_text=all_text,
                images_detected=len(response_objects.localized_object_annotations),
                raw_response={"google_vision": "analyzed"}
            )

            return analysis

        except Exception as e:
            logger.error(f"Google Vision analysis failed: {e}")
            raise

    async def _analyze_with_tesseract(
        self,
        screenshot_bytes: bytes,
        url: Optional[str] = None
    ) -> PageAnalysis:
        """Tesseract OCR local para modo offline."""
        logger.info("Analyzing screenshot with Tesseract OCR")

        try:
            import pytesseract
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(screenshot_bytes))
            text = await asyncio.to_thread(pytesseract.image_to_string, image)

            analysis = PageAnalysis(
                page_type="unknown",
                url=url,
                all_text=[TextRegion(text=text, x=0, y=0, width=100, height=100, confidence=0.7)],
            )

            return analysis

        except Exception as e:
            logger.error(f"Tesseract analysis failed: {e}")
            raise

    def _parse_claude_response(
        self,
        data: Dict[str, Any],
        url: Optional[str] = None
    ) -> PageAnalysis:
        """Parsea respuesta JSON de Claude."""
        # Parsear texto
        all_text = [
            TextRegion(
                text=t["text"],
                x=int(t.get("x", 0)),
                y=int(t.get("y", 0)),
                width=int(t.get("width", 100)),
                height=int(t.get("height", 20)),
                confidence=t.get("confidence", 0.9)
            )
            for t in data.get("all_text", [])
        ]

        # Parsear botones
        buttons = [
            ButtonDetection(
                label=b["label"],
                x=int(b.get("x", 0)),
                y=int(b.get("y", 0)),
                width=int(b.get("width", 80)),
                height=int(b.get("height", 40)),
                color=b.get("color", "#000000"),
                shape=b.get("shape", "rectangular"),
                confidence=b.get("confidence", 0.9)
            )
            for b in data.get("buttons", [])
        ]

        # Parsear campos de formulario
        form_fields = [
            FormField(
                label=f["label"],
                field_type=f.get("type", "input"),
                x=int(f.get("x", 0)),
                y=int(f.get("y", 0)),
                width=int(f.get("width", 200)),
                height=int(f.get("height", 30)),
                required=f.get("required", False),
                placeholder=f.get("placeholder"),
                confidence=f.get("confidence", 0.9)
            )
            for f in data.get("form_fields", [])
        ]

        # Parsear layout
        layout_regions = [
            LayoutRegion(
                region_type=r["type"],
                x=int(r.get("x", 0)),
                y=int(r.get("y", 0)),
                width=int(r.get("width", 100)),
                height=int(r.get("height", 20)),
                elements_count=r.get("elements_count", 0)
            )
            for r in data.get("layout_regions", [])
        ]

        return PageAnalysis(
            page_type=data.get("page_type", "unknown"),
            title=data.get("title"),
            url=url,
            all_text=all_text,
            buttons=buttons,
            form_fields=form_fields,
            layout_regions=layout_regions,
            navigation_items=data.get("navigation_items", []),
            images_detected=data.get("images_detected", 0),
            confidence_score=data.get("confidence_score", 0.85),
            raw_response=data
        )

    def _parse_google_text_detection(self, texts) -> List[TextRegion]:
        """Parsea resultado de Google Text Detection."""
        regions = []
        for text_annotation in texts[1:]:  # Skip first (full text)
            vertices = text_annotation.bounding_poly.vertices
            if vertices:
                x = vertices[0].x
                y = vertices[0].y
                width = vertices[2].x - vertices[0].x
                height = vertices[2].y - vertices[0].y

                regions.append(TextRegion(
                    text=text_annotation.description,
                    x=int(x),
                    y=int(y),
                    width=int(width),
                    height=int(height),
                    confidence=0.9
                ))
        return regions

    async def extract_text(
        self,
        screenshot_bytes: bytes,
        backend: str = "claude"
    ) -> str:
        """Extrae solo el texto del screenshot."""
        analysis = await self.analyze_screenshot(screenshot_bytes, backend=backend)
        text_content = "\n".join([t.text for t in analysis.all_text])
        return text_content

    async def detect_buttons(
        self,
        screenshot_bytes: bytes
    ) -> List[ButtonDetection]:
        """Detecta solo botones."""
        analysis = await self.analyze_screenshot(screenshot_bytes)
        return analysis.buttons

    async def detect_form_fields(
        self,
        screenshot_bytes: bytes
    ) -> List[FormField]:
        """Detecta solo campos de formulario."""
        analysis = await self.analyze_screenshot(screenshot_bytes)
        return analysis.form_fields

    async def classify_page_type(
        self,
        screenshot_bytes: bytes
    ) -> str:
        """Clasifica el tipo de página."""
        analysis = await self.analyze_screenshot(screenshot_bytes)
        return analysis.page_type

    async def get_layout_structure(
        self,
        screenshot_bytes: bytes
    ) -> List[LayoutRegion]:
        """Obtiene la estructura del layout."""
        analysis = await self.analyze_screenshot(screenshot_bytes)
        return analysis.layout_regions

    def print_analysis(self, analysis: PageAnalysis) -> str:
        """Retorna análisis en formato legible."""
        lines = [
            f"PAGE TYPE: {analysis.page_type}",
            f"TITLE: {analysis.title or 'N/A'}",
            f"URL: {analysis.url or 'N/A'}",
            f"CONFIDENCE: {analysis.confidence_score:.2%}",
            f"\nTEXT ({len(analysis.all_text)} items):",
        ]

        for text in analysis.all_text[:5]:  # First 5
            lines.append(f"  - '{text.text}' @({text.x},{text.y})")

        lines.append(f"\nBUTTONS ({len(analysis.buttons)}):")
        for btn in analysis.buttons:
            lines.append(f"  - '{btn.label}' {btn.color} @({btn.x},{btn.y}) {btn.shape}")

        lines.append(f"\nFORM FIELDS ({len(analysis.form_fields)}):")
        for field in analysis.form_fields:
            lines.append(f"  - '{field.label}' ({field.field_type}) @({field.x},{field.y})")

        lines.append(f"\nLAYOUT REGIONS ({len(analysis.layout_regions)}):")
        for region in analysis.layout_regions:
            lines.append(f"  - {region.region_type} @({region.x},{region.y})")

        lines.append(f"\nNAVIGATION: {', '.join(analysis.navigation_items)}")
        lines.append(f"IMAGES: {analysis.images_detected}")

        return "\n".join(lines)
