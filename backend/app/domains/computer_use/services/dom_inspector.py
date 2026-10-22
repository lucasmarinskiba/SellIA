"""Computer Use — DOM Inspector

Extrae información estructurada del DOM para ayudar al agente a
tomar decisiones más precisas: botones, links, inputs, y su estado.
"""

from dataclasses import dataclass
from typing import Any, ClassVar

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DOMElement:
    """Representación simplificada de un elemento DOM."""

    tag: str
    text: str
    id: str | None
    classes: list[str]
    xpath: str
    attributes: dict[str, str]
    bounding_box: dict[str, float] | None  # x, y, width, height
    is_visible: bool
    is_interactive: bool


class DOMInspector:
    """Inspector del DOM para Computer Use."""

    INTERACTIVE_TAGS: ClassVar[set] = {
        "button",
        "a",
        "input",
        "select",
        "textarea",
        "label",
    }
    INTERACTIVE_ROLES: ClassVar[set] = {
        "button",
        "link",
        "textbox",
        "checkbox",
        "radio",
        "menuitem",
    }

    async def extract_interactive_elements(self, page) -> list[DOMElement]:
        """Extrae todos los elementos interactivos de la página."""
        try:
            elements = await page.query_selector_all(
                "button, a, input, select, textarea, [role='button'], [role='link'], [onclick]"
            )
            result = []
            for i, el in enumerate(elements):
                try:
                    info = await self._extract_element_info(el, i)
                    if info and info.is_visible:
                        result.append(info)
                except Exception:
                    logger.exception("extract_interactive_elements: error inesperado")
                    continue
            return result
        except Exception as e:
            logger.warning(f"DOM extraction failed: {e}", exc_info=True)
            return []

    async def _extract_element_info(self, element, index: int) -> DOMElement | None:
        """Extrae información de un elemento individual."""
        try:
            tag = await element.evaluate("el => el.tagName.toLowerCase()")
            text = await element.evaluate(
                "el => el.textContent?.trim()?.substring(0, 100) || ''"
            )
            elem_id = await element.evaluate("el => el.id || null")
            classes = await element.evaluate("el => Array.from(el.classList)")
            xpath = await element.evaluate("""
                el => {
                    const idx = (sib, name) => sib 
                        ? 1 + idx(sib.previousElementSibling, name) 
                        : 1;
                    const segs = elm => !elm || elm.nodeType !== 1 
                        ? [''] 
                        : [...segs(elm.parentNode), `${elm.tagName.toLowerCase()}[${idx(elm, elm.tagName)}]`];
                    return segs(elm).join('/');
                }
            """)

            # Bounding box
            box = await element.bounding_box()

            # Visibility
            is_visible = await element.is_visible()

            # Interactive check
            role = await element.evaluate("el => el.getAttribute('role')")
            is_interactive = (
                tag in self.INTERACTIVE_TAGS
                or role in self.INTERACTIVE_ROLES
                or await element.evaluate(
                    "el => el.onclick !== null || el.getAttribute('onclick') !== null"
                )
            )

            # Key attributes
            attrs = {}
            for attr in ["href", "type", "placeholder", "name", "value", "aria-label"]:
                val = await element.evaluate(f"el => el.getAttribute('{attr}')")
                if val:
                    attrs[attr] = val[:200]

            return DOMElement(
                tag=tag,
                text=text,
                id=elem_id,
                classes=classes[:10],
                xpath=xpath,
                attributes=attrs,
                bounding_box=box,
                is_visible=is_visible,
                is_interactive=is_interactive,
            )
        except Exception:
            logger.exception("_extract_element_info: error inesperado")
            return None

    async def find_clickable_by_text(self, page, text: str) -> dict[str, Any] | None:
        """Encuentra un elemento clickeable por su texto."""
        try:
            # Try exact match first
            selector = f"text={text}"
            element = await page.query_selector(selector)
            if not element:
                # Try case-insensitive
                elements = await page.query_selector_all("button, a, [role='button']")
                for el in elements:
                    el_text = await el.text_content()
                    if el_text and text.lower() in el_text.lower():
                        element = el
                        break

            if element:
                box = await element.bounding_box()
                return {
                    "found": True,
                    "x": box["x"] + box["width"] / 2 if box else 0,
                    "y": box["y"] + box["height"] / 2 if box else 0,
                    "text": text,
                }
            return {"found": False}
        except Exception as e:
            logger.warning(f"Find clickable failed: {e}", exc_info=True)
            return {"found": False, "error": str(e)}

    async def get_page_accessibility_tree(self, page) -> dict[str, Any]:
        """Obtiene un árbol de accesibilidad simplificado."""
        try:
            tree = await page.accessibility.snapshot()
            return self._simplify_tree(tree)
        except Exception as e:
            logger.warning(f"Accessibility tree failed: {e}", exc_info=True)
            return {}

    def _simplify_tree(self, node: dict[str, Any]) -> dict[str, Any]:
        """Simplifica el árbol de accesibilidad."""
        result = {
            "role": node.get("role", "unknown"),
            "name": node.get("name", ""),
        }
        if "value" in node:
            result["value"] = node["value"]
        if "children" in node:
            result["children"] = [
                self._simplify_tree(child)
                for child in node["children"]
                if child.get("role") not in ("none", "generic")
            ]
        return result

    async def get_form_state(self, page) -> list[dict[str, Any]]:
        """Obtiene el estado actual de todos los formularios."""
        try:
            return await page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
                    return inputs.map(el => ({
                        tag: el.tagName.toLowerCase(),
                        type: el.type,
                        name: el.name,
                        id: el.id,
                        value: el.value?.substring(0, 100) || '',
                        checked: el.checked,
                        placeholder: el.placeholder,
                        label: document.querySelector(`label[for="${el.id}"]`)?.textContent?.trim() ||
                               el.closest('label')?.textContent?.trim() || ''
                    }));
                }
            """)
        except Exception as e:
            logger.warning(f"Form state extraction failed: {e}", exc_info=True)
            return []
