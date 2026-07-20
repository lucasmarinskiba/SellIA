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

from .visual_analyzer import (
    VisualAnalyzer,
    PageAnalysis,
    ButtonDetection,
    FormField,
    TextRegion,
    LayoutRegion,
)

from .vision_navigator import (
    VisionNavigator,
    ElementType,
    ElementMatch,
    ViewportState,
)

from .visual_confirmation import (
    VisualConfirmation,
    Confirmation,
    ActionResult,
)

from .vision_screenshot_parser import (
    VisionScreenshotParser,
    ViewportSize,
    PageStructure,
    PageMetadata,
    Heading,
    ImageContent,
)

from .visual_automation_executor import (
    VisualAutomationExecutor,
    ActionType,
    ExecutionPlan,
)

from .vision_debug import (
    VisionDebugAnnotator,
    VisionDebugLogger,
    VisionComparator,
)

__all__ = [
    # Analyzer
    "VisualAnalyzer",
    "PageAnalysis",
    "ButtonDetection",
    "FormField",
    "TextRegion",
    "LayoutRegion",

    # Navigator
    "VisionNavigator",
    "ElementType",
    "ElementMatch",
    "ViewportState",

    # Confirmation
    "VisualConfirmation",
    "Confirmation",
    "ActionResult",

    # Parser
    "VisionScreenshotParser",
    "ViewportSize",
    "PageStructure",
    "PageMetadata",
    "Heading",
    "ImageContent",

    # Executor
    "VisualAutomationExecutor",
    "ActionType",
    "ExecutionPlan",

    # Debug
    "VisionDebugAnnotator",
    "VisionDebugLogger",
    "VisionComparator",
]
