# Computer Vision Integration — Complete Guide

## Overview

100% vision-based automation. No selectors. Just visual understanding.

**Modules (2,000+ lines):**

1. **visual_analyzer.py** (400L)
   - Screenshot OCR + text extraction
   - Button detection (color, shape, position)
   - Form field detection
   - Layout understanding
   - Page type classification

2. **vision_navigator.py** (400L)
   - Find elements by natural language
   - Find clickable areas
   - Detect form fields by labels
   - Detect tables, lists, cards
   - Viewport analysis

3. **visual_confirmation.py** (300L)
   - Verify action success
   - Detect errors
   - Detect success states
   - Detect loading states
   - Detect popups/modals

4. **vision_screenshot_parser.py** (400L)
   - Complete page structure extraction
   - OCR + text hierarchy
   - All UI elements identification
   - Viewport size detection
   - Image content identification

5. **visual_automation_executor.py** (300L)
   - Execute actions by visual description
   - Click by visual similarity
   - Fill forms by visual labels
   - Navigate by visual landmarks
   - Confirmation loops

6. **vision_debug.py** (200L)
   - Annotate screenshots
   - Debug logging
   - Visual comparisons
   - Report generation

7. **vision_orchestrator_integration.py** (300L)
   - Unified orchestrator
   - High-level API
   - Complete automation workflows

---

## Quick Start

### Initialize

```python
from app.core.computer_use.vision import VisionOrchestrator
import anthropic

anthropic_client = anthropic.Anthropic(api_key="...")

orchestrator = VisionOrchestrator(
    anthropic_client=anthropic_client,
    screenshot_getter=browser.get_screenshot,  # Async function
    browser_controller=browser,  # Has click(), type_text(), etc
    session_id="session_123",
    debug_enabled=True
)
```

### Basic Usage

```python
# Analyze current page
analysis = await orchestrator.analyze_current_page()
print(f"Page type: {analysis.page_type}")
print(f"Found {len(analysis.buttons)} buttons")

# Find elements
button = await orchestrator.find_button("red submit button")
email_field = await orchestrator.find_form_field("email")

# Execute actions
result = await orchestrator.click("submit button")
result = await orchestrator.fill("email", "user@example.com")

# Verify
errors = await orchestrator.detect_errors()
has_success = await orchestrator.verify_action_succeeded("Email filled")
```

### Complete Workflow

```python
# Login example
orchestrator = VisionOrchestrator(...)

# Analyze page
analysis = await orchestrator.analyze_current_page()
print(await orchestrator.summary())

# Fill form
form_data = {
    "email": "user@example.com",
    "password": "secret123"
}
result = await orchestrator.fill_form(form_data)
print(f"Filled {len(result['filled_fields'])} fields")

# Submit
await orchestrator.click("submit button", verify=True)

# Wait for success
is_logged_in = await orchestrator.wait_for_element("Logout button", timeout=10)

# Get page structure
structure = await orchestrator.get_page_structure()
print(f"Page title: {structure.metadata.title}")
```

### Action Sequences

```python
# Execute multiple actions in sequence
actions = [
    "Click the search box",
    "Type 'laptop' in search",
    "Click search button",
    "Wait 2 seconds",
    "Click the first result",
]

results = await orchestrator.execute_action_sequence(actions, verify_each=True)

for i, result in enumerate(results):
    print(f"Action {i+1}: {'SUCCESS' if result['success'] else 'FAILED'}")
    if not result['success']:
        print(f"  Error: {result.get('error')}")
```

---

## Module APIs

### VisualAnalyzer

```python
from app.core.computer_use.vision import VisualAnalyzer

analyzer = VisualAnalyzer(anthropic_client=client)

# Complete analysis
analysis = await analyzer.analyze_screenshot(screenshot_bytes)
print(analysis.page_type)
print(len(analysis.buttons))
print(len(analysis.form_fields))

# Specific analyses
text = await analyzer.extract_text(screenshot_bytes)
buttons = await analyzer.detect_buttons(screenshot_bytes)
fields = await analyzer.detect_form_fields(screenshot_bytes)
page_type = await analyzer.classify_page_type(screenshot_bytes)
layout = await analyzer.get_layout_structure(screenshot_bytes)

# Pretty print
print(analyzer.print_analysis(analysis))
```

### VisionNavigator

```python
from app.core.computer_use.vision import VisionNavigator, ElementType

navigator = VisionNavigator(analyzer)

# Find by description
button = await navigator.find_element_by_description(
    screenshot_bytes,
    "red submit button",
    element_type=ElementType.BUTTON,
    threshold=0.7
)

# Find form field
email_field = await navigator.find_form_field_by_label(
    screenshot_bytes,
    "email"
)

# Find all clickable
clickables = await navigator.find_clickable_areas(screenshot_bytes, max_results=10)
for elem in clickables:
    print(f"{elem.element_type.value}: {elem.label} @({elem.center_x},{elem.center_y})")

# Detect page structure
tables = await navigator.detect_tables(screenshot_bytes)
lists = await navigator.detect_lists(screenshot_bytes)
cards = await navigator.detect_cards(screenshot_bytes)

# Analyze viewport
viewport = await navigator.analyze_viewport(screenshot_bytes, 1280, 720)
print(f"Visible elements: {viewport.visible_element_count}")
print(f"Below fold: {viewport.below_fold_elements}")
```

### VisualConfirmation

```python
from app.core.computer_use.vision import VisualConfirmation

confirmation = VisualConfirmation(anthropic_client=client)

# Verify action
result = await confirmation.verify_action_succeeded(
    before_screenshot,
    after_screenshot,
    "Clicked submit button",
    expected_indicators=["success message"]
)
print(f"Result: {result.result.value}")
print(f"Confidence: {result.confidence:.0%}")

# Detect errors
errors = await confirmation.detect_errors(screenshot_bytes)
print(f"Found errors: {errors}")

# Detect success
is_success = await confirmation.detect_success_state(screenshot_bytes)

# Detect loading
is_loading = await confirmation.detect_loading_state(screenshot_bytes)

# Detect modal
modal_info = await confirmation.detect_modal_popup(screenshot_bytes)
if modal_info['has_modal']:
    print(f"Modal type: {modal_info['modal_type']}")
    print(f"Content: {modal_info['content']}")

# Wait for condition
success = await confirmation.wait_for_condition(
    screenshot_getter=browser.get_screenshot,
    condition_checker=async_check_condition,
    timeout_seconds=30
)
```

### VisionScreenshotParser

```python
from app.core.computer_use.vision import VisionScreenshotParser

parser = VisionScreenshotParser(anthropic_client=client)

# Complete page structure
structure = await parser.parse_complete_page(screenshot_bytes)
print(f"Title: {structure.metadata.title}")
print(f"Viewport: {structure.metadata.viewport_size_type.value}")
print(f"Elements: {structure.element_count}")

# Extract text
text = await parser.extract_all_text(screenshot_bytes)

# Identify UI elements
elements = await parser.identify_all_ui_elements(screenshot_bytes)
print(f"Buttons: {len(elements.get('buttons', []))}")
print(f"Links: {len(elements.get('links', []))}")

# Detect viewport
viewport_size, is_responsive = await parser.detect_viewport_size(screenshot_bytes)
print(f"Viewport: {viewport_size.value}")
print(f"Responsive: {is_responsive}")

# Identify images
images = await parser.identify_images(screenshot_bytes)

# Summary
summary = await parser.get_page_summary(screenshot_bytes)
print(summary)
```

### VisualAutomationExecutor

```python
from app.core.computer_use.vision import VisualAutomationExecutor

executor = VisualAutomationExecutor(
    visual_analyzer=analyzer,
    vision_navigator=navigator,
    visual_confirmation=confirmation,
    browser_controller=browser
)

# Execute single action
result = await executor.execute_action(
    screenshot_bytes,
    "Click the red submit button",
    expected_result="Form submitted",
    verify_success=True
)

# Fill form
form_result = await executor.fill_form(
    screenshot_bytes,
    {"email": "user@example.com", "password": "pass123"},
    verify_success=True
)
print(f"Filled: {form_result['filled_fields']}")
print(f"Failed: {form_result['failed_fields']}")

# Click by description
click_result = await executor.click_element_by_description(
    screenshot_bytes,
    "submit button",
    verify_success=True
)

# Navigate to landmark
nav_result = await executor.navigate_by_landmark(
    screenshot_bytes,
    "footer contact link"
)

# Execute sequence
results = await executor.execute_action_sequence(
    screenshot_getter=lambda: browser.get_screenshot(),
    actions=[
        "Click search box",
        "Type 'laptop'",
        "Click search button"
    ],
    verify_each=False
)

# Execute with retries
result = await executor.execute_with_confirmation_loop(
    screenshot_getter=lambda: browser.get_screenshot(),
    action_description="Click submit button",
    max_retries=3,
    confirmation_timeout=10
)
```

### VisionDebugLogger

```python
from app.core.computer_use.vision import VisionDebugLogger

logger = VisionDebugLogger("session_123", output_dir="./vision_debug")

# Log analysis
logger.log_analysis(
    step=1,
    screenshot_path="screenshot_1.png",
    analysis={"page_type": "login", "buttons": 3},
    action_taken="Analyzed login page"
)

# Log element search
logger.log_element_search(
    step=2,
    search_query="submit button",
    found_element={"label": "Submit", "type": "button"},
    confidence=0.95
)

# Log action
logger.log_action_execution(
    step=3,
    action="click",
    target="submit button",
    result="success"
)

# Log confirmation
logger.log_confirmation(
    step=4,
    action="submit form",
    confirmation_result="success",
    details={"message": "Form submitted successfully"}
)

# Generate report
report = logger.generate_report()
print(report)

# Save report
path = logger.save_report()
print(f"Report saved: {path}")
```

### VisionDebugAnnotator

```python
from app.core.computer_use.vision import VisionDebugAnnotator

# Annotate with buttons
annotated = VisionDebugAnnotator.annotate_with_buttons(
    screenshot_bytes,
    buttons=[{"label": "Submit", "x": 100, "y": 200, "width": 80, "height": 40}],
    output_path="annotated_buttons.png"
)

# Annotate with form fields
annotated = VisionDebugAnnotator.annotate_with_form_fields(
    screenshot_bytes,
    fields=[{"label": "Email", "type": "input", "x": 50, "y": 100, "width": 200, "height": 30}],
    output_path="annotated_fields.png"
)

# Annotate all elements
annotated = VisionDebugAnnotator.annotate_with_all_elements(
    screenshot_bytes,
    analysis={"buttons": [...], "form_fields": [...], "all_text": [...]},
    output_path="annotated_all.png"
)

# Compare before/after
comparison = VisionDebugAnnotator.create_comparison_image(
    before_bytes,
    after_bytes,
    output_path="comparison.png"
)
```

---

## Integration with ComputerUseOrchestratorV2

```python
# In session_manager_v2.py or computer_use_orchestrator.py

from app.core.computer_use.vision import VisionOrchestrator

class ComputerUseSessionManagerV2:
    def __init__(self, ...):
        # ... existing init ...
        
        # Initialize vision
        self.vision = VisionOrchestrator(
            anthropic_client=self.anthropic,
            screenshot_getter=self.browser.get_screenshot,
            browser_controller=self.browser,
            session_id=str(session_id),
            debug_enabled=True
        )
    
    async def step(self):
        # Get current state
        analysis = await self.vision.analyze_current_page()
        
        # Make decision based on vision
        if analysis.page_type == "form":
            # Fill form
            await self.vision.fill_form(form_data)
            await self.vision.click("submit")
        elif analysis.page_type == "error":
            # Handle error
            errors = await self.vision.detect_errors()
            # ...
        
        # Verify success
        errors = await self.vision.detect_errors()
        if not errors:
            # Continue
            pass
```

---

## Advanced Usage

### Custom Element Matching

```python
# Increase threshold for strict matching
button = await orchestrator.find_button("confirm", threshold=0.9)

# Find by element type
inputs = await navigator.find_elements_of_type(
    screenshot,
    ElementType.INPUT
)

# Multiple element types
elements = await navigator.find_clickable_areas(screenshot, max_results=20)
```

### Conditional Automation

```python
# Wait for condition
email_field = await orchestrator.find_form_field("email")

# Execute only if element found
if email_field:
    await orchestrator.fill("email", "test@example.com")

# Custom condition
async def check_for_success(screenshot):
    return "Success" in await orchestrator.parser.extract_all_text(screenshot)

success = await orchestrator.wait_for_condition(check_for_success, timeout=30)
```

### Error Recovery

```python
# Execute with automatic retry
result = await orchestrator.executor.execute_with_confirmation_loop(
    screenshot_getter=orchestrator.get_current_screenshot,
    action_description="Click submit button",
    max_retries=3
)

if not result['success']:
    # Get error details
    errors = await orchestrator.detect_errors()
    print(f"Errors: {errors}")
    
    # Take debug screenshot
    orchestrator.debug_annotate_current_page("error_state.png")
```

### Multi-Step Workflows

```python
# Complex workflow with verification
workflow = [
    ("Click search box", "Search box is focused"),
    ("Type 'laptop'", "Search text is entered"),
    ("Click search button", "Results are loading"),
    ("Wait for loading to finish", "Results are displayed"),
    ("Click first result", "Product page is loaded"),
    ("Click add to cart", "Item added to cart"),
]

for action, expected in workflow:
    print(f"Executing: {action}")
    result = await orchestrator.execute_action(
        await orchestrator.get_current_screenshot(),
        action,
        expected_result=expected,
        verify_success=True
    )
    
    if not result.get('verified'):
        print(f"Warning: Could not verify '{expected}'")
        # Continue anyway or break
```

---

## Performance Tips

1. **Reuse VisualAnalyzer**: Don't create new instances for each screenshot
2. **Cache analyses**: Save PageAnalysis results if using same screenshot multiple times
3. **Batch element searches**: Use `find_all_clickable()` once instead of multiple searches
4. **Set appropriate thresholds**: Use higher threshold (0.8-0.9) for critical elements
5. **Disable debug when not needed**: Saves CPU/API calls
6. **Use `verify_each=False` in sequences**: Only verify final action for speed

---

## Architecture Diagram

```
VisionOrchestrator (High-level API)
    ├─ VisualAnalyzer
    │   ├─ Claude Vision
    │   ├─ Google Vision (fallback)
    │   └─ Tesseract (offline)
    ├─ VisionNavigator
    │   └─ Uses VisualAnalyzer
    ├─ VisualConfirmation
    │   └─ Claude Vision for comparison
    ├─ VisualAutomationExecutor
    │   ├─ Uses VisionNavigator
    │   ├─ Calls BrowserController
    │   └─ Uses VisualConfirmation
    ├─ VisionScreenshotParser
    │   └─ Claude Vision for structure
    ├─ VisionDebugLogger
    │   └─ JSONL log files
    └─ VisionDebugAnnotator
        └─ PIL image annotation
```

---

## Error Handling

```python
try:
    button = await orchestrator.find_button("submit")
    if not button:
        print("Button not found!")
        errors = await orchestrator.detect_errors()
        print(f"Errors: {errors}")
        
    result = await orchestrator.click("submit")
    if not result['success']:
        print(f"Click failed: {result.get('error')}")
        
except Exception as e:
    print(f"Exception: {e}")
    # Get debug info
    report = orchestrator.get_debug_report()
    print(report)
```

---

## Future Enhancements

1. **Video Recording**: Combine screenshots into video
2. **Machine Learning**: Train on successful/failed actions
3. **Multi-Language Support**: OCR in multiple languages
4. **Mobile Testing**: Specialized mobile element detection
5. **Performance Metrics**: Speed optimization analysis
6. **Collaborative Debugging**: Share/compare sessions

---

## Constants & Defaults

```python
# Confidence thresholds
DEFAULT_ELEMENT_THRESHOLD = 0.7
STRICT_ELEMENT_THRESHOLD = 0.9

# Timeouts
DEFAULT_WAIT_TIMEOUT = 30
DEFAULT_POLL_INTERVAL = 0.5

# Viewport sizes
MOBILE_MAX_WIDTH = 600
TABLET_MAX_WIDTH = 1000

# API
CLAUDE_VISION_MODEL = "claude-3-5-sonnet-20241022"
CLAUDE_MAX_TOKENS_ANALYSIS = 4000
CLAUDE_MAX_TOKENS_VERIFICATION = 1500
```

---

*For questions or issues, check INTEGRATION_GUIDE.md or see examples in tests/*
