"""Visual Automation Executor — Execute Actions Based on Vision

Responsibilities:
- Execute actions based on visual description
- Click element by visual similarity
- Fill form based on visual label matching
- Navigate based on visual landmarks
- Confirm actions via visual feedback

Completely selector-free automation.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .visual_analyzer import VisualAnalyzer
from .vision_navigator import VisionNavigator, ElementType, ElementMatch
from .visual_confirmation import VisualConfirmation, Confirmation, ActionResult

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Tipo de acción a ejecutar."""
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    SCROLL = "scroll"
    TYPE = "type"
    WAIT = "wait"
    NAVIGATE = "navigate"


@dataclass
class ExecutionPlan:
    """Plan de ejecución visual."""
    action_type: ActionType
    description: str
    target_element: Optional[ElementMatch] = None
    value: Optional[str] = None
    wait_time: Optional[float] = None
    wait_condition: Optional[Callable] = None
    expected_result: Optional[str] = None


class VisualAutomationExecutor:
    """Ejecuta automatización basada en visión."""

    def __init__(
        self,
        visual_analyzer: VisualAnalyzer,
        vision_navigator: VisionNavigator,
        visual_confirmation: VisualConfirmation,
        browser_controller=None  # Responsable de clicks/typing
    ):
        self.analyzer = visual_analyzer
        self.navigator = vision_navigator
        self.confirmation = visual_confirmation
        self.browser = browser_controller

    async def execute_action(
        self,
        screenshot_bytes: bytes,
        action_description: str,
        expected_result: Optional[str] = None,
        verify_success: bool = True
    ) -> Dict[str, Any]:
        """Ejecuta una acción basada en descripción natural.

        Args:
            screenshot_bytes: Screenshot actual
            action_description: Qué hacer (ej: "Click the red submit button")
            expected_result: Resultado esperado (ej: "Form should submit")
            verify_success: Si verificar que funcionó

        Returns:
            {
                "success": bool,
                "action": str,
                "target": ElementMatch or None,
                "confirmation": Confirmation or None,
                "error": str or None
            }
        """
        logger.info(f"Executing action: {action_description}")

        try:
            # Parsear descripción y encontrar elemento
            action_type, element_desc, value = self._parse_action_description(action_description)

            element = None
            if action_type in [ActionType.CLICK, ActionType.FILL, ActionType.SELECT]:
                element = await self.navigator.find_element_by_description(
                    screenshot_bytes,
                    element_desc
                )

                if not element:
                    return {
                        "success": False,
                        "action": action_description,
                        "target": None,
                        "error": f"Element not found: {element_desc}",
                    }

            # Ejecutar acción
            result = await self._execute_action_internal(
                action_type,
                element,
                value
            )

            if not result["success"]:
                return result

            # Verificar éxito si se pide
            confirmation = None
            if verify_success and self.browser:
                before_screenshot = screenshot_bytes
                await asyncio.sleep(0.5)  # Esperar a que UI se actualice
                after_screenshot = await self.browser.get_screenshot()

                confirmation = await self.confirmation.verify_action_succeeded(
                    before_screenshot,
                    after_screenshot,
                    action_description,
                    [expected_result] if expected_result else None
                )

                result["confirmation"] = confirmation
                result["verified"] = confirmation.result == ActionResult.SUCCESS

            return result

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                "success": False,
                "action": action_description,
                "target": None,
                "error": str(e),
            }

    async def execute_action_sequence(
        self,
        screenshot_getter: Callable,
        actions: List[str],
        verify_each: bool = False
    ) -> List[Dict[str, Any]]:
        """Ejecuta una secuencia de acciones.

        Args:
            screenshot_getter: Función que retorna screenshot actual
            actions: Lista de descripciones de acciones
            verify_each: Si verificar cada acción

        Returns:
            Lista de resultados
        """
        results = []

        for i, action in enumerate(actions):
            logger.info(f"Action {i+1}/{len(actions)}: {action}")

            screenshot = await screenshot_getter()
            result = await self.execute_action(
                screenshot,
                action,
                verify_success=verify_each
            )

            results.append(result)

            if not result["success"]:
                logger.warning(f"Action failed: {result.get('error')}")
                # Continuar o detener?
                break

            # Pequeña pausa entre acciones
            await asyncio.sleep(0.3)

        return results

    async def fill_form(
        self,
        screenshot_bytes: bytes,
        form_data: Dict[str, str],
        verify_success: bool = True
    ) -> Dict[str, Any]:
        """Rellena un formulario usando etiquetas visuales.

        Args:
            screenshot_bytes: Screenshot del formulario
            form_data: {"email": "user@example.com", "password": "123"}
            verify_success: Si verificar que se llenó correctamente

        Returns:
            Resultado de ejecución
        """
        logger.info(f"Filling form with {len(form_data)} fields")

        analysis = await self.analyzer.analyze_screenshot(screenshot_bytes)
        results = {
            "success": True,
            "filled_fields": [],
            "failed_fields": [],
            "errors": [],
        }

        for field_label, value in form_data.items():
            try:
                # Encontrar campo por label
                field = await self.navigator.find_form_field_by_label(
                    screenshot_bytes,
                    field_label
                )

                if not field:
                    results["failed_fields"].append(field_label)
                    results["errors"].append(f"Field not found: {field_label}")
                    continue

                # Ejecutar fill
                action_result = await self._execute_action_internal(
                    ActionType.FILL,
                    ElementMatch(
                        element_type=ElementType.INPUT,
                        label=field.label,
                        description=field_label,
                        x=field.x,
                        y=field.y,
                        width=field.width,
                        height=field.height,
                        confidence=0.9,
                    ),
                    value
                )

                if action_result["success"]:
                    results["filled_fields"].append(field_label)
                else:
                    results["failed_fields"].append(field_label)
                    results["errors"].append(action_result.get("error", "Unknown error"))

                await asyncio.sleep(0.2)

            except Exception as e:
                logger.error(f"Error filling {field_label}: {e}")
                results["failed_fields"].append(field_label)
                results["errors"].append(str(e))

        results["success"] = len(results["failed_fields"]) == 0

        return results

    async def click_element_by_description(
        self,
        screenshot_bytes: bytes,
        description: str,
        verify_success: bool = True
    ) -> Dict[str, Any]:
        """Clickea un elemento por descripción.

        Args:
            screenshot_bytes: Screenshot actual
            description: Descripción del elemento
            verify_success: Si verificar que funcionó

        Returns:
            Resultado
        """
        element = await self.navigator.find_element_by_description(
            screenshot_bytes,
            description,
            ElementType.BUTTON
        )

        if not element:
            return {
                "success": False,
                "element": None,
                "error": f"Element not found: {description}",
            }

        result = await self._execute_action_internal(
            ActionType.CLICK,
            element
        )

        if verify_success and self.browser and result["success"]:
            before = screenshot_bytes
            await asyncio.sleep(0.5)
            after = await self.browser.get_screenshot()

            confirmation = await self.confirmation.verify_action_succeeded(
                before,
                after,
                f"Clicked: {description}",
            )

            result["confirmation"] = confirmation
            result["verified"] = confirmation.result != ActionResult.ERROR

        return result

    async def navigate_by_landmark(
        self,
        screenshot_bytes: bytes,
        landmark_description: str
    ) -> Dict[str, Any]:
        """Navega a un landmark visual (ej: "footer link to contact").

        Args:
            screenshot_bytes: Screenshot actual
            landmark_description: Dónde ir

        Returns:
            Resultado
        """
        logger.info(f"Navigating to landmark: {landmark_description}")

        # Buscar elemento que corresponde al landmark
        element = await self.navigator.find_element_by_description(
            screenshot_bytes,
            landmark_description,
            ElementType.LINK
        )

        if not element:
            return {
                "success": False,
                "landmark": landmark_description,
                "error": f"Landmark not found: {landmark_description}",
            }

        return await self._execute_action_internal(
            ActionType.NAVIGATE,
            element
        )

    def _parse_action_description(self, description: str) -> tuple:
        """Parsea una descripción de acción.

        Retorna: (ActionType, target_element_description, value)
        """
        desc_lower = description.lower()

        if desc_lower.startswith("click"):
            # "Click the red submit button"
            element_desc = description[5:].strip("the ").strip()
            return ActionType.CLICK, element_desc, None

        elif desc_lower.startswith("fill") or desc_lower.startswith("type"):
            # "Fill email field with user@example.com"
            # "Type password: 123456"
            parts = description.split(" with ") if " with " in description else description.split(": ")
            if len(parts) == 2:
                element_desc = parts[0][5:].strip("the ").strip()  # Remove "Fill"/"Type"
                value = parts[1].strip()
                return ActionType.FILL, element_desc, value
            else:
                return ActionType.FILL, parts[0], None

        elif desc_lower.startswith("select"):
            # "Select 'Option 1' from category dropdown"
            parts = description.split(" from ")
            if len(parts) == 2:
                value = parts[0][6:].strip("'\"").strip()
                element_desc = parts[1].strip()
                return ActionType.SELECT, element_desc, value
            else:
                return ActionType.SELECT, description[6:].strip(), None

        elif desc_lower.startswith("check"):
            # "Check the 'I agree' checkbox"
            element_desc = description[5:].strip("the ").strip()
            return ActionType.CHECK, element_desc, None

        elif desc_lower.startswith("uncheck"):
            # "Uncheck the 'Newsletter' checkbox"
            element_desc = description[7:].strip("the ").strip()
            return ActionType.UNCHECK, element_desc, None

        elif desc_lower.startswith("scroll"):
            # "Scroll down" / "Scroll to footer"
            direction = description[6:].strip().lower()
            return ActionType.SCROLL, direction, None

        elif desc_lower.startswith("wait"):
            # "Wait 5 seconds" / "Wait for loading to finish"
            rest = description[4:].strip()
            return ActionType.WAIT, rest, None

        else:
            # Default a CLICK
            return ActionType.CLICK, description, None

    async def _execute_action_internal(
        self,
        action_type: ActionType,
        element: Optional[ElementMatch] = None,
        value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ejecuta acción interna."""
        if not self.browser:
            return {
                "success": False,
                "error": "No browser controller available",
            }

        try:
            if action_type == ActionType.CLICK and element:
                await self.browser.click(element.center_x, element.center_y)
                return {
                    "success": True,
                    "action": "click",
                    "target": element,
                }

            elif action_type == ActionType.FILL and element and value:
                # Primero clickear el elemento
                await self.browser.click(element.center_x, element.center_y)
                await asyncio.sleep(0.2)

                # Luego escribir
                await self.browser.type_text(value)
                return {
                    "success": True,
                    "action": "fill",
                    "target": element,
                    "value": value,
                }

            elif action_type == ActionType.SELECT and element and value:
                await self.browser.click(element.center_x, element.center_y)
                await asyncio.sleep(0.3)

                # En un select, escribir parte del valor y seleccionar
                await self.browser.type_text(value)
                await asyncio.sleep(0.2)
                await self.browser.key_press("Enter")

                return {
                    "success": True,
                    "action": "select",
                    "target": element,
                    "value": value,
                }

            elif action_type == ActionType.CHECK and element:
                # Clickear checkbox
                await self.browser.click(element.center_x, element.center_y)
                return {
                    "success": True,
                    "action": "check",
                    "target": element,
                }

            elif action_type == ActionType.UNCHECK and element:
                # Uncheck (click nuevamente si ya está checked)
                await self.browser.click(element.center_x, element.center_y)
                return {
                    "success": True,
                    "action": "uncheck",
                    "target": element,
                }

            elif action_type == ActionType.SCROLL:
                direction = element.label if element else value
                if "down" in direction.lower():
                    await self.browser.scroll(0, 300)
                elif "up" in direction.lower():
                    await self.browser.scroll(0, -300)
                else:
                    await self.browser.scroll(0, 500)

                return {
                    "success": True,
                    "action": "scroll",
                }

            elif action_type == ActionType.WAIT:
                wait_str = element.label if element else value
                try:
                    # "5 seconds" → 5
                    wait_time = float(wait_str.split()[0])
                    await asyncio.sleep(wait_time)
                except ValueError:
                    await asyncio.sleep(1)

                return {
                    "success": True,
                    "action": "wait",
                }

            elif action_type == ActionType.NAVIGATE and element:
                # Navegación a link
                await self.browser.click(element.center_x, element.center_y)
                return {
                    "success": True,
                    "action": "navigate",
                    "target": element,
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                }

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def execute_with_confirmation_loop(
        self,
        screenshot_getter: Callable,
        action_description: str,
        max_retries: int = 3,
        confirmation_timeout: float = 10
    ) -> Dict[str, Any]:
        """Ejecuta acción con reintentos si falla.

        Args:
            screenshot_getter: Función que retorna screenshot
            action_description: Acción a ejecutar
            max_retries: Intentos máximos
            confirmation_timeout: Tiempo para confirmación

        Returns:
            Resultado final
        """
        for attempt in range(max_retries):
            screenshot = await screenshot_getter()

            result = await self.execute_action(
                screenshot,
                action_description,
                verify_success=True
            )

            if result["success"] and result.get("verified", False):
                logger.info(f"Action succeeded on attempt {attempt + 1}")
                return result

            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(1)

        logger.error(f"Action failed after {max_retries} attempts")
        return {
            "success": False,
            "action": action_description,
            "error": f"Failed after {max_retries} attempts",
        }
