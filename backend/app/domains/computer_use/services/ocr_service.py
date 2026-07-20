"""Computer Use — OCR Service

Extrae texto de screenshots usando pytesseract o easyocr.
Permite al agente "leer" el contenido de la página visualmente
complementando el DOM.
"""

import io
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from PIL import Image

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OCRRegion:
    """Región de texto detectada."""
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


class OCRService:
    """Servicio de OCR para screenshots."""

    def __init__(self):
        self._engine = None
        self._engine_name = None

    def _init_engine(self):
        """Inicializa el motor OCR disponible."""
        if self._engine is not None:
            return

        # Try easyocr first (more accurate)
        try:
            import easyocr
            self._engine = easyocr.Reader(['es', 'en'], gpu=False)
            self._engine_name = "easyocr"
            logger.info("OCR engine: easyocr")
            return
        except ImportError:
            pass

        # Fallback to pytesseract
        try:
            import pytesseract
            self._engine = pytesseract
            self._engine_name = "pytesseract"
            logger.info("OCR engine: pytesseract")
            return
        except ImportError:
            pass

        logger.warning("No OCR engine available. Install pytesseract or easyocr.")

    async def extract_text(self, screenshot_bytes: bytes) -> str:
        """Extrae todo el texto de un screenshot."""
        self._init_engine()
        if self._engine is None:
            return ""

        try:
            img = Image.open(io.BytesIO(screenshot_bytes))

            if self._engine_name == "easyocr":
                result = self._engine.readtext(
                    img,
                    detail=0,
                    paragraph=True,
                )
                return "\n".join(result)

            elif self._engine_name == "pytesseract":
                return self._engine.image_to_string(img, lang="spa+eng")

        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return ""

        return ""

    async def extract_regions(self, screenshot_bytes: bytes) -> List[OCRRegion]:
        """Extrae texto con coordenadas de cada región."""
        self._init_engine()
        if self._engine is None:
            return []

        regions = []
        try:
            img = Image.open(io.BytesIO(screenshot_bytes))

            if self._engine_name == "easyocr":
                results = self._engine.readtext(img, detail=1)
                for bbox, text, conf in results:
                    x_coords = [p[0] for p in bbox]
                    y_coords = [p[1] for p in bbox]
                    regions.append(OCRRegion(
                        text=text,
                        x=int(min(x_coords)),
                        y=int(min(y_coords)),
                        width=int(max(x_coords) - min(x_coords)),
                        height=int(max(y_coords) - min(y_coords)),
                        confidence=float(conf),
                    ))

            elif self._engine_name == "pytesseract":
                data = self._engine.image_to_data(img, lang="spa+eng", output_type=self._engine.Output.DICT)
                for i in range(len(data["text"])):
                    if int(data["conf"][i]) > 30:  # Min confidence
                        regions.append(OCRRegion(
                            text=data["text"][i],
                            x=data["left"][i],
                            y=data["top"][i],
                            width=data["width"][i],
                            height=data["height"][i],
                            confidence=data["conf"][i] / 100.0,
                        ))

        except Exception as e:
            logger.warning(f"OCR region extraction failed: {e}")

        return regions

    async def find_text(self, screenshot_bytes: bytes, target: str) -> Optional[OCRRegion]:
        """Busca texto específico en un screenshot y retorna su ubicación."""
        regions = await self.extract_regions(screenshot_bytes)
        target_lower = target.lower()
        for region in regions:
            if target_lower in region.text.lower():
                return region
        return None

    async def extract_form_fields(self, screenshot_bytes: bytes) -> List[Dict[str, Any]]:
        """Intenta identificar campos de formulario visuales."""
        text = await self.extract_text(screenshot_bytes)
        fields = []

        # Heurística: buscar labels comunes
        label_patterns = [
            r"(?:nombre|name|usuario|user|email|correo|contraseña|password|teléfono|phone|dirección|address)",
        ]

        import re
        lines = text.split("\n")
        for i, line in enumerate(lines):
            for pattern in label_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Next line might be the value or input placeholder
                    value = lines[i + 1] if i + 1 < len(lines) else ""
                    fields.append({
                        "label": line.strip(),
                        "value": value.strip(),
                        "line": i,
                    })

        return fields
