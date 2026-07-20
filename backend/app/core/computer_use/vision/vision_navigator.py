"""Vision Navigator — Find UI Elements by Description

Responsibilities:
- Find element by natural language description
- Find clickable areas (buttons, links, form fields)
- Detect form fields by labels
- Detect tables, lists, cards
- Viewport analysis (what's visible)

No selectors needed. Pure visual matching.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import difflib

from .visual_analyzer import (
    VisualAnalyzer, PageAnalysis, ButtonDetection, FormField,
    TextRegion, LayoutRegion
)

logger = logging.getLogger(__name__)


class ElementType(Enum):
    """Tipos de elementos UI."""
    BUTTON = "button"
    LINK = "link"
    INPUT = "input"
    SELECT = "select"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    LIST = "list"
    CARD = "card"
    UNKNOWN = "unknown"


@dataclass
class ElementMatch:
    """Elemento encontrado en pantalla."""
    element_type: ElementType
    label: str
    description: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    center_x: Optional[int] = None
    center_y: Optional[int] = None

    def __post_init__(self):
        if self.center_x is None:
            self.center_x = self.x + self.width // 2
        if self.center_y is None:
            self.center_y = self.y + self.height // 2


@dataclass
class ViewportState:
    """Estado actual del viewport."""
    viewport_width: int
    viewport_height: int
    scroll_top: int = 0
    scroll_left: int = 0
    visible_area_height: int = 0
    visible_element_count: int = 0
    below_fold_elements: int = 0


class VisionNavigator:
    """Navega UI usando solo visión, sin selectores."""

    def __init__(self, visual_analyzer: VisualAnalyzer):
        self.analyzer = visual_analyzer

    async def find_element_by_description(
        self,
        screenshot_bytes: bytes,
        description: str,
        element_type: Optional[ElementType] = None,
        threshold: float = 0.7
    ) -> Optional[ElementMatch]:
        """Encuentra un elemento por descripción natural.

        Args:
            screenshot_bytes: Screenshot actual
            description: Descripción natural (ej: "red submit button", "email field")
            element_type: Filtro de tipo (opcional)
            threshold: Confianza mínima (0-1)

        Returns:
            ElementMatch si encuentra, None si no
        """
        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)

        best_match = None
        best_score = threshold

        # Buscar en botones
        if not element_type or element_type == ElementType.BUTTON:
            for btn in analysis.buttons:
                score = self._calculate_similarity(
                    description.lower(),
                    f"{btn.label} {btn.color} button".lower()
                )
                if score > best_score:
                    best_score = score
                    best_match = ElementMatch(
                        element_type=ElementType.BUTTON,
                        label=btn.label,
                        description=description,
                        x=btn.x,
                        y=btn.y,
                        width=btn.width,
                        height=btn.height,
                        confidence=score
                    )

        # Buscar en campos de formulario
        if not element_type or element_type in [ElementType.INPUT, ElementType.SELECT, ElementType.TEXTAREA]:
            for field in analysis.form_fields:
                score = self._calculate_similarity(
                    description.lower(),
                    f"{field.label} {field.field_type} field".lower()
                )
                if score > best_score:
                    field_type_map = {
                        "input": ElementType.INPUT,
                        "select": ElementType.SELECT,
                        "textarea": ElementType.TEXTAREA,
                        "checkbox": ElementType.CHECKBOX,
                        "radio": ElementType.RADIO,
                    }
                    best_score = score
                    best_match = ElementMatch(
                        element_type=field_type_map.get(field.field_type, ElementType.INPUT),
                        label=field.label,
                        description=description,
                        x=field.x,
                        y=field.y,
                        width=field.width,
                        height=field.height,
                        confidence=score
                    )

        # Buscar en texto
        if not element_type or element_type == ElementType.TEXT:
            for text in analysis.all_text:
                score = self._calculate_similarity(
                    description.lower(),
                    text.text.lower()
                )
                if score > best_score:
                    best_score = score
                    best_match = ElementMatch(
                        element_type=ElementType.TEXT,
                        label=text.text,
                        description=description,
                        x=text.x,
                        y=text.y,
                        width=text.width,
                        height=text.height,
                        confidence=score
                    )

        logger.info(
            f"Found element '{description}': {best_match.label if best_match else 'NOT FOUND'} "
            f"(confidence: {best_score:.2%})"
        )

        return best_match

    async def find_clickable_areas(
        self,
        screenshot_bytes: bytes,
        max_results: int = 10
    ) -> List[ElementMatch]:
        """Encuentra todas las áreas clickeables (botones, links, form inputs)."""
        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)

        clickables = []

        # Botones
        for btn in analysis.buttons:
            clickables.append(ElementMatch(
                element_type=ElementType.BUTTON,
                label=btn.label,
                description=f"Button: {btn.label}",
                x=btn.x,
                y=btn.y,
                width=btn.width,
                height=btn.height,
                confidence=btn.confidence
            ))

        # Campos de formulario
        for field in analysis.form_fields:
            field_type_map = {
                "input": ElementType.INPUT,
                "select": ElementType.SELECT,
                "textarea": ElementType.TEXTAREA,
                "checkbox": ElementType.CHECKBOX,
                "radio": ElementType.RADIO,
            }
            clickables.append(ElementMatch(
                element_type=field_type_map.get(field.field_type, ElementType.INPUT),
                label=field.label,
                description=f"{field.field_type.title()}: {field.label}",
                x=field.x,
                y=field.y,
                width=field.width,
                height=field.height,
                confidence=field.confidence
            ))

        # Ordenar por confianza
        clickables.sort(key=lambda x: x.confidence, reverse=True)
        return clickables[:max_results]

    async def find_form_field_by_label(
        self,
        screenshot_bytes: bytes,
        label: str,
        threshold: float = 0.7
    ) -> Optional[FormField]:
        """Encuentra un campo de formulario por su label."""
        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)

        best_field = None
        best_score = threshold

        for field in analysis.form_fields:
            score = self._calculate_similarity(label.lower(), field.label.lower())
            if score > best_score:
                best_score = score
                best_field = field

        logger.info(f"Found form field '{label}': {best_field.label if best_field else 'NOT FOUND'}")
        return best_field

    async def find_elements_of_type(
        self,
        screenshot_bytes: bytes,
        element_type: ElementType
    ) -> List[ElementMatch]:
        """Encuentra todos los elementos de un tipo específico."""
        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)

        matches = []

        if element_type == ElementType.BUTTON:
            for btn in analysis.buttons:
                matches.append(ElementMatch(
                    element_type=ElementType.BUTTON,
                    label=btn.label,
                    description=f"Button: {btn.label}",
                    x=btn.x,
                    y=btn.y,
                    width=btn.width,
                    height=btn.height,
                    confidence=btn.confidence
                ))

        elif element_type in [ElementType.INPUT, ElementType.SELECT, ElementType.TEXTAREA]:
            field_type_str = element_type.value
            for field in analysis.form_fields:
                if field.field_type == field_type_str:
                    matches.append(ElementMatch(
                        element_type=element_type,
                        label=field.label,
                        description=f"{field.field_type.title()}: {field.label}",
                        x=field.x,
                        y=field.y,
                        width=field.width,
                        height=field.height,
                        confidence=field.confidence
                    ))

        elif element_type == ElementType.TEXT:
            for text in analysis.all_text:
                matches.append(ElementMatch(
                    element_type=ElementType.TEXT,
                    label=text.text,
                    description=text.text,
                    x=text.x,
                    y=text.y,
                    width=text.width,
                    height=text.height,
                    confidence=text.confidence
                ))

        matches.sort(key=lambda x: (x.y, x.x))  # Sort top-to-bottom, left-to-right
        return matches

    async def detect_tables(
        self,
        screenshot_bytes: bytes
    ) -> List[Dict[str, Any]]:
        """Detecta tablas en la página."""
        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)

        # Buscar patrones de tabla (filas y columnas alineadas)
        tables = []

        # Heurística: detectar grupos de texto alineados verticalmente
        text_by_y = {}
        for text in analysis.all_text:
            y_key = round(text.y / 10) * 10  # Agrupar por altura similar
            if y_key not in text_by_y:
                text_by_y[y_key] = []
            text_by_y[y_key].append(text)

        # Si hay múltiples filas con múltiples columnas, es probablemente una tabla
        if len(text_by_y) >= 2:
            sorted_y = sorted(text_by_y.keys())
            rows = []
            for y_key in sorted_y:
                columns = sorted(text_by_y[y_key], key=lambda t: t.x)
                if len(columns) >= 2:
                    rows.append([c.text for c in columns])

            if len(rows) >= 2:
                tables.append({
                    "type": "text_table",
                    "rows": rows,
                    "column_count": len(rows[0]) if rows else 0,
                    "row_count": len(rows),
                    "confidence": 0.7
                })

        return tables

    async def detect_lists(
        self,
        screenshot_bytes: bytes
    ) -> List[Dict[str, Any]]:
        """Detecta listas (bullets, numbered, etc)."""
        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)

        lists = []

        # Buscar patrones de lista (items alineados verticalmente)
        items_by_group = {}
        min_y_spacing = 20

        sorted_texts = sorted(analysis.all_text, key=lambda t: (t.x, t.y))

        current_group = []
        last_y = -999

        for text in sorted_texts:
            if text.y - last_y > min_y_spacing and current_group:
                if len(current_group) >= 2:
                    items_by_group[last_y] = current_group
                current_group = []

            current_group.append(text.text)
            last_y = text.y

        if len(current_group) >= 2:
            items_by_group[last_y] = current_group

        # Si encontramos múltiples grupos, son listas
        if len(items_by_group) >= 1:
            for y_pos, items in items_by_group.items():
                lists.append({
                    "type": "text_list",
                    "items": items,
                    "count": len(items),
                    "y_position": y_pos,
                    "confidence": 0.8
                })

        return lists

    async def detect_cards(
        self,
        screenshot_bytes: bytes
    ) -> List[Dict[str, Any]]:
        """Detecta cards/containers."""
        # Basado en layout regions y agrupaciones de elementos
        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)

        cards = []

        # Heurística: si hay regiones de contenido separadas, son cards
        if len(analysis.layout_regions) >= 2:
            for region in analysis.layout_regions:
                if region.region_type == "content":
                    cards.append({
                        "type": "card",
                        "region": region,
                        "x": region.x,
                        "y": region.y,
                        "width": region.width,
                        "height": region.height,
                        "elements_count": region.elements_count,
                        "confidence": 0.75
                    })

        return cards

    async def analyze_viewport(
        self,
        screenshot_bytes: bytes,
        viewport_width: int = 1280,
        viewport_height: int = 720
    ) -> ViewportState:
        """Analiza el estado actual del viewport."""
        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)

        # Detectar elementos visibles vs below-fold
        visible_count = 0
        below_fold_count = 0
        max_y = 0

        for text in analysis.all_text:
            if text.y + text.height > viewport_height:
                below_fold_count += 1
            else:
                visible_count += 1
            max_y = max(max_y, text.y + text.height)

        for btn in analysis.buttons:
            if btn.y + btn.height > viewport_height:
                below_fold_count += 1
            else:
                visible_count += 1
            max_y = max(max_y, btn.y + btn.height)

        return ViewportState(
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            visible_area_height=viewport_height,
            visible_element_count=visible_count,
            below_fold_elements=below_fold_count
        )

    def _calculate_similarity(self, desc1: str, desc2: str) -> float:
        """Calcula similitud entre dos strings (0-1)."""
        # Usar SequenceMatcher para similitud
        ratio = difflib.SequenceMatcher(None, desc1, desc2).ratio()

        # Bonus si una string contiene la otra
        if desc1 in desc2 or desc2 in desc1:
            ratio = min(1.0, ratio + 0.2)

        return ratio

    async def get_all_clickable_elements_summary(
        self,
        screenshot_bytes: bytes
    ) -> str:
        """Retorna resumen de elementos clickeables en formato legible."""
        clickables = await self.find_clickable_areas(screenshot_bytes, max_results=20)

        lines = [f"CLICKABLE ELEMENTS ({len(clickables)}):"]
        for i, elem in enumerate(clickables, 1):
            lines.append(f"{i}. [{elem.element_type.value.upper()}] {elem.label}")
            lines.append(f"   Position: ({elem.center_x}, {elem.center_y}) | Confidence: {elem.confidence:.1%}")

        return "\n".join(lines)
