"""Computer Vision Integration for Computer Use

Complete vision-based automation without selectors.

Modules:
- visual_analyzer: Screenshot analysis (OCR, object detection, layout)
- vision_navigator: Find elements by natural language description
- visual_confirmation: Verify action success using visual feedback
- vision_screenshot_parser: Extract complete page structure
- visual_automation_executor: Execute actions based on vision
- vision_debug: Debugging and visualization tools

Usage:
    from app.core.computer_use.vision import VisionOrchestrator

    orchestrator = VisionOrchestrator(anthropic_client)

    # Find element
    button = await orchestrator.find_button("red submit button")

    # Click it
    result = await orchestrator.click(button)

    # Verify
    confirmed = await orchestrator.verify_action_succeeded(before, after)
"""

from .vision_debug import (
    VisionComparator,
    VisionDebugAnnotator,
    VisionDebugLogger,
)
from .vision_navigator import (
    ElementMatch,
    ElementType,
    ViewportState,
    VisionNavigator,
)
from .vision_screenshot_parser import (
    Heading,
    ImageContent,
    PageMetadata,
    PageStructure,
    ViewportSize,
    VisionScreenshotParser,
)
from .visual_analyzer import (
    ButtonDetection,
    FormField,
    LayoutRegion,
    PageAnalysis,
    TextRegion,
    VisualAnalyzer,
)
from .visual_automation_executor import (
    ActionType,
    ExecutionPlan,
    VisualAutomationExecutor,
)
from .visual_confirmation import (
    ActionResult,
    Confirmation,
    VisualConfirmation,
)

__all__ = [
    "ActionResult",
    "ActionType",
    "ButtonDetection",
    "Confirmation",
    "ElementMatch",
    "ElementType",
    "ExecutionPlan",
    "FormField",
    "Heading",
    "ImageContent",
    "LayoutRegion",
    "PageAnalysis",
    "PageMetadata",
    "PageStructure",
    "TextRegion",
    "ViewportSize",
    "ViewportState",
    "VisionComparator",
    # Debug
    "VisionDebugAnnotator",
    "VisionDebugLogger",
    # Navigator
    "VisionNavigator",
    # Parser
    "VisionScreenshotParser",
    # Analyzer
    "VisualAnalyzer",
    # Executor
    "VisualAutomationExecutor",
    # Confirmation
    "VisualConfirmation",
]
