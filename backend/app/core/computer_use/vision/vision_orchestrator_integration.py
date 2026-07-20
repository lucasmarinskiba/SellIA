"""Vision Orchestrator Integration — Complete Vision-Based Automation

Integra todos los módulos de vision en un orquestador único.

Flujo:
1. Tomar screenshot
2. Analizar con VisualAnalyzer
3. Encontrar elemento con VisionNavigator
4. Ejecutar acción con VisualAutomationExecutor
5. Verificar éxito con VisualConfirmation
6. Debuggear con VisionDebugLogger

100% sin selectores. Solo visión.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .visual_analyzer import VisualAnalyzer, PageAnalysis
from .vision_navigator import VisionNavigator, ElementType, ElementMatch
from .visual_confirmation import VisualConfirmation, Confirmation, ActionResult
from .vision_screenshot_parser import VisionScreenshotParser, PageStructure
from .visual_automation_executor import VisualAutomationExecutor, ActionType
from .vision_debug import VisionDebugLogger, VisionDebugAnnotator, VisionComparator

logger = logging.getLogger(__name__)


@dataclass
class VisionExecutionContext:
    """Contexto de ejecución."""
    session_id: str
    step: int = 0
    screenshot_getter: Optional[Callable] = None
    browser_controller: Optional[Any] = None
    anthropic_client: Optional[Any] = None
    google_vision_client: Optional[Any] = None
    debug_enabled: bool = False
    debug_logger: Optional[VisionDebugLogger] = None


class VisionOrchestrator:
    """Orquestador completo de automation basada en visión.

    Responsabilidades:
    - Tomar screenshots
    - Analizar interfaz
    - Encontrar elementos
    - Ejecutar acciones
    - Verificar resultados
    - Debuggear y reportar
    """

    def __init__(
        self,
        anthropic_client,
        screenshot_getter: Callable,
        browser_controller: Any,
        session_id: str,
        google_vision_client: Optional[Any] = None,
        debug_enabled: bool = False
    ):
        self.context = VisionExecutionContext(
            session_id=session_id,
            screenshot_getter=screenshot_getter,
            browser_controller=browser_controller,
            anthropic_client=anthropic_client,
            google_vision_client=google_vision_client,
            debug_enabled=debug_enabled,
        )

        # Inicializar módulos
        self.analyzer = VisualAnalyzer(
            anthropic_client=anthropic_client,
            google_vision_client=google_vision_client
        )

        self.navigator = VisionNavigator(self.analyzer)

        self.confirmation = VisualConfirmation(
            anthropic_client=anthropic_client,
            visual_analyzer=self.analyzer
        )

        self.executor = VisualAutomationExecutor(
            visual_analyzer=self.analyzer,
            vision_navigator=self.navigator,
            visual_confirmation=self.confirmation,
            browser_controller=browser_controller
        )

        self.parser = VisionScreenshotParser(anthropic_client=anthropic_client)

        # Debug
        if debug_enabled:
            self.context.debug_logger = VisionDebugLogger(session_id)
        else:
            self.context.debug_logger = None

    async def get_current_screenshot(self) -> bytes:
        """Obtiene screenshot actual."""
        if not self.context.screenshot_getter:
            raise ValueError("screenshot_getter not configured")

        return await self.context.screenshot_getter()

    async def analyze_current_page(self) -> PageAnalysis:
        """Analiza la página actual completa."""
        screenshot = await self.get_current_screenshot()

        self.context.step += 1
        analysis = await self.analyzer.analyze_screenshot(screenshot)

        if self.context.debug_logger:
            self.context.debug_logger.log_analysis(
                self.context.step,
                None,
                analysis.raw_response or {},
            )

        logger.info(f"Page analyzed: {analysis.page_type}")
        return analysis

    async def get_page_structure(self) -> PageStructure:
        """Obtiene estructura completa de página."""
        screenshot = await self.get_current_screenshot()
        return await self.parser.parse_complete_page(screenshot)

    async def find_button(
        self,
        description: str,
        threshold: float = 0.7
    ) -> Optional[ElementMatch]:
        """Encuentra un botón por descripción."""
        screenshot = await self.get_current_screenshot()

        element = await self.navigator.find_element_by_description(
            screenshot,
            description,
            ElementType.BUTTON,
            threshold
        )

        if self.context.debug_logger and element:
            self.context.debug_logger.log_element_search(
                self.context.step,
                description,
                {"label": element.label, "type": "button"},
                element.confidence
            )

        return element

    async def find_form_field(
        self,
        label: str,
        threshold: float = 0.7
    ) -> Optional[ElementMatch]:
        """Encuentra un campo de formulario."""
        screenshot = await self.get_current_screenshot()

        # Buscar en cualquier tipo de campo
        for elem_type in [ElementType.INPUT, ElementType.SELECT, ElementType.TEXTAREA]:
            element = await self.navigator.find_element_by_description(
                screenshot,
                label,
                elem_type,
                threshold
            )
            if element:
                if self.context.debug_logger:
                    self.context.debug_logger.log_element_search(
                        self.context.step,
                        label,
                        {"label": element.label, "type": elem_type.value},
                        element.confidence
                    )
                return element

        return None

    async def find_element(
        self,
        description: str,
        element_type: Optional[ElementType] = None,
        threshold: float = 0.7
    ) -> Optional[ElementMatch]:
        """Encuentra cualquier elemento."""
        screenshot = await self.get_current_screenshot()

        element = await self.navigator.find_element_by_description(
            screenshot,
            description,
            element_type,
            threshold
        )

        if self.context.debug_logger and element:
            self.context.debug_logger.log_element_search(
                self.context.step,
                description,
                {"label": element.label},
                element.confidence
            )

        return element

    async def find_all_clickable(self, max_results: int = 10) -> List[ElementMatch]:
        """Encuentra todos los elementos clickeables."""
        screenshot = await self.get_current_screenshot()
        return await self.navigator.find_clickable_areas(screenshot, max_results)

    async def click(
        self,
        description: str,
        verify: bool = True
    ) -> Dict[str, Any]:
        """Clickea un elemento."""
        screenshot_before = await self.get_current_screenshot()

        result = await self.executor.click_element_by_description(
            screenshot_before,
            description,
            verify_success=verify
        )

        self.context.step += 1

        if self.context.debug_logger:
            self.context.debug_logger.log_action_execution(
                self.context.step,
                "click",
                description,
                "success" if result["success"] else "failed",
                result.get("error")
            )

        return result

    async def fill(
        self,
        field_label: str,
        value: str,
        verify: bool = True
    ) -> Dict[str, Any]:
        """Rellena un campo de formulario."""
        screenshot_before = await self.get_current_screenshot()

        result = await self.executor.execute_action(
            screenshot_before,
            f"Fill {field_label} with {value}",
            expected_result=f"Field {field_label} contains {value}",
            verify_success=verify
        )

        self.context.step += 1

        if self.context.debug_logger:
            self.context.debug_logger.log_action_execution(
                self.context.step,
                "fill",
                field_label,
                "success" if result["success"] else "failed",
                result.get("error")
            )

        return result

    async def fill_form(
        self,
        form_data: Dict[str, str],
        verify: bool = True
    ) -> Dict[str, Any]:
        """Rellena un formulario completo."""
        screenshot = await self.get_current_screenshot()

        result = await self.executor.fill_form(
            screenshot,
            form_data,
            verify_success=verify
        )

        self.context.step += 1

        if self.context.debug_logger:
            for field in result.get("filled_fields", []):
                self.context.debug_logger.log_action_execution(
                    self.context.step,
                    "fill_form",
                    field,
                    "success",
                    None
                )

        return result

    async def select(
        self,
        field_label: str,
        option_value: str,
        verify: bool = True
    ) -> Dict[str, Any]:
        """Selecciona una opción en un dropdown."""
        screenshot_before = await self.get_current_screenshot()

        result = await self.executor.execute_action(
            screenshot_before,
            f"Select '{option_value}' from {field_label}",
            expected_result=f"{option_value} selected",
            verify_success=verify
        )

        self.context.step += 1

        if self.context.debug_logger:
            self.context.debug_logger.log_action_execution(
                self.context.step,
                "select",
                field_label,
                "success" if result["success"] else "failed",
                result.get("error")
            )

        return result

    async def check(
        self,
        checkbox_label: str,
        verify: bool = True
    ) -> Dict[str, Any]:
        """Marca un checkbox."""
        screenshot_before = await self.get_current_screenshot()

        result = await self.executor.execute_action(
            screenshot_before,
            f"Check {checkbox_label}",
            expected_result=f"{checkbox_label} is checked",
            verify_success=verify
        )

        self.context.step += 1
        return result

    async def execute_action_sequence(
        self,
        actions: List[str],
        verify_each: bool = False
    ) -> List[Dict[str, Any]]:
        """Ejecuta una secuencia de acciones."""
        logger.info(f"Executing sequence of {len(actions)} actions")

        return await self.executor.execute_action_sequence(
            self.get_current_screenshot,
            actions,
            verify_each=verify_each
        )

    async def verify_action_succeeded(
        self,
        action_description: str,
        expected_indicators: Optional[List[str]] = None
    ) -> Confirmation:
        """Verifica que una acción tuvo éxito.

        Requiere tomar before/after screenshots antes.
        """
        # Implementar lógica de verificación
        screenshot = await self.get_current_screenshot()

        has_success = await self.confirmation.detect_success_state(screenshot)
        errors = await self.confirmation.detect_errors(screenshot)

        if errors:
            result_type = ActionResult.ERROR
        elif has_success:
            result_type = ActionResult.SUCCESS
        else:
            result_type = ActionResult.UNKNOWN

        confirmation = Confirmation(
            result=result_type,
            confidence=0.8 if has_success else 0.5,
            message=action_description,
            error_messages=errors,
        )

        if self.context.debug_logger:
            self.context.debug_logger.log_confirmation(
                self.context.step,
                action_description,
                result_type.value,
            )

        return confirmation

    async def wait_for_element(
        self,
        description: str,
        timeout: float = 30,
        poll_interval: float = 0.5
    ) -> bool:
        """Espera a que aparezca un elemento."""
        async def condition_checker(screenshot):
            element = await self.navigator.find_element_by_description(
                screenshot,
                description,
                threshold=0.6
            )
            return element is not None

        return await self.confirmation.wait_for_condition(
            self.get_current_screenshot,
            condition_checker,
            timeout,
            poll_interval
        )

    async def wait_for_condition(
        self,
        condition_checker: Callable,
        timeout: float = 30
    ) -> bool:
        """Espera una condición visual."""
        return await self.confirmation.wait_for_condition(
            self.get_current_screenshot,
            condition_checker,
            timeout
        )

    async def get_page_text(self) -> str:
        """Extrae todo el texto de la página."""
        screenshot = await self.get_current_screenshot()
        return await self.parser.extract_all_text(screenshot)

    async def get_all_ui_elements(self) -> Dict[str, Any]:
        """Obtiene todos los elementos UI."""
        screenshot = await self.get_current_screenshot()
        return await self.parser.identify_all_ui_elements(screenshot)

    async def detect_errors(self) -> List[str]:
        """Detecta mensajes de error."""
        screenshot = await self.get_current_screenshot()
        return await self.confirmation.detect_errors(screenshot)

    async def detect_loading_state(self) -> bool:
        """Detecta si hay una pantalla de carga."""
        screenshot = await self.get_current_screenshot()
        return await self.confirmation.detect_loading_state(screenshot)

    async def detect_modal(self) -> Dict[str, Any]:
        """Detecta si hay un modal abierto."""
        screenshot = await self.get_current_screenshot()
        return await self.confirmation.detect_modal_popup(screenshot)

    def debug_annotate_current_page(self, output_path: Optional[str] = None) -> bytes:
        """Anota la página actual con elementos detectados."""
        # Implementar anotación
        pass

    def get_debug_report(self) -> str:
        """Retorna reporte de debug."""
        if self.context.debug_logger:
            return self.context.debug_logger.generate_report()
        return "Debug logging not enabled"

    def save_debug_report(self, output_file: Optional[str] = None) -> str:
        """Guarda reporte de debug."""
        if self.context.debug_logger:
            return self.context.debug_logger.save_report(output_file)
        return ""

    def enable_debug(self) -> None:
        """Habilita debug logging."""
        if not self.context.debug_logger:
            self.context.debug_logger = VisionDebugLogger(self.context.session_id)
            self.context.debug_enabled = True
            logger.info("Debug logging enabled")

    def disable_debug(self) -> None:
        """Deshabilita debug logging."""
        self.context.debug_enabled = False
        logger.info("Debug logging disabled")

    async def summary(self) -> str:
        """Retorna resumen del estado actual."""
        analysis = await self.analyze_current_page()

        lines = [
            f"VISION ORCHESTRATOR SUMMARY",
            f"Session: {self.context.session_id}",
            f"Step: {self.context.step}",
            f"",
            f"Current Page: {analysis.page_type}",
            f"Confidence: {analysis.confidence_score:.0%}",
            f"",
            f"Elements Detected:",
            f"  Buttons: {len(analysis.buttons)}",
            f"  Form Fields: {len(analysis.form_fields)}",
            f"  Text Regions: {len(analysis.all_text)}",
            f"  Layout Regions: {len(analysis.layout_regions)}",
        ]

        return "\n".join(lines)
