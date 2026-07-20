"""
Computer Use Intelligence Layer for SellIA
Automates browser/UI interactions with reasoning (plan → execute → validate)
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ── Enums ──────────────────────────────────────────────

class ActionType(Enum):
    SCREENSHOT = "screenshot"
    CLICK = "click"
    FILL_TEXT = "fill_text"
    EXTRACT_DATA = "extract_data"
    SCROLL = "scroll"
    NAVIGATE = "navigate"
    WAIT = "wait"

class BrowserContext(Enum):
    AMAZON = "amazon"
    SHOPIFY = "shopify"
    FACEBOOK_MARKETPLACE = "facebook_marketplace"
    INSTAGRAM = "instagram"
    EBAY = "ebay"
    CUSTOM_ECOMMERCE = "custom_ecommerce"

# ── Data Models ──────────────────────────────────────

@dataclass
class ComputerUseAction:
    action_type: ActionType
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    wait_time: Optional[int] = None
    expect_text: Optional[str] = None

@dataclass
class ComputerUsePlan:
    goal: str
    context: BrowserContext
    steps: list[ComputerUseAction]
    expected_outcome: str
    fallback_strategy: str

@dataclass
class ExecutionResult:
    success: bool
    actions_executed: int
    screenshot_final: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    validation_passed: bool = False

# ── Computer Use Planner ──────────────────────────────

class ComputerUsePlanner:
    """Plans browser automation sequences before executing"""

    @staticmethod
    def plan_product_listing(product_name: str, price: float, context: BrowserContext) -> ComputerUsePlan:
        """Plan listing product on marketplace"""
        return ComputerUsePlan(
            goal=f"List '{product_name}' for ${price}",
            context=context,
            steps=[
                ComputerUseAction(ActionType.NAVIGATE, url="https://example.com/seller/products/new"),
                ComputerUseAction(ActionType.SCREENSHOT),
                ComputerUseAction(ActionType.FILL_TEXT, selector="[name='product_name']", text=product_name),
                ComputerUseAction(ActionType.FILL_TEXT, selector="[name='price']", text=str(price)),
                ComputerUseAction(ActionType.CLICK, selector="[type='submit']"),
                ComputerUseAction(ActionType.WAIT, wait_time=3),
                ComputerUseAction(ActionType.SCREENSHOT),
                ComputerUseAction(ActionType.EXTRACT_DATA, selector=".success-message"),
            ],
            expected_outcome="Product listed successfully with confirmation message",
            fallback_strategy="Retry from product name field after 2 second delay"
        )

    @staticmethod
    def plan_customer_outreach(customer_email: str, product_name: str) -> ComputerUsePlan:
        """Plan sending customer message"""
        return ComputerUsePlan(
            goal=f"Send message to {customer_email} about {product_name}",
            context=BrowserContext.CUSTOM_ECOMMERCE,
            steps=[
                ComputerUseAction(ActionType.NAVIGATE, url="https://example.com/messages/new"),
                ComputerUseAction(ActionType.FILL_TEXT, selector="[name='recipient']", text=customer_email),
                ComputerUseAction(ActionType.FILL_TEXT, selector="[name='subject']",
                                 text=f"Check out {product_name}"),
                ComputerUseAction(ActionType.FILL_TEXT, selector="[name='message']",
                                 text=f"Hi! I thought you'd be interested in {product_name}. Let me know!"),
                ComputerUseAction(ActionType.CLICK, selector="[type='submit']"),
                ComputerUseAction(ActionType.WAIT, wait_time=2),
                ComputerUseAction(ActionType.SCREENSHOT),
            ],
            expected_outcome="Message sent confirmation displayed",
            fallback_strategy="Check if email field has validation error, retry with corrected email"
        )

    @staticmethod
    def plan_order_fulfillment(order_id: str) -> ComputerUsePlan:
        """Plan processing order fulfillment"""
        return ComputerUsePlan(
            goal=f"Mark order {order_id} as shipped",
            context=BrowserContext.CUSTOM_ECOMMERCE,
            steps=[
                ComputerUseAction(ActionType.NAVIGATE, url=f"https://example.com/orders/{order_id}"),
                ComputerUseAction(ActionType.SCREENSHOT),
                ComputerUseAction(ActionType.CLICK, selector="[data-action='mark_shipped']"),
                ComputerUseAction(ActionType.FILL_TEXT, selector="[name='tracking_number']", text="tracking123"),
                ComputerUseAction(ActionType.CLICK, selector=".confirm-button"),
                ComputerUseAction(ActionType.WAIT, wait_time=2),
                ComputerUseAction(ActionType.SCREENSHOT),
                ComputerUseAction(ActionType.EXTRACT_DATA, selector=".status-message"),
            ],
            expected_outcome="Order status changed to 'Shipped' with tracking number",
            fallback_strategy="Reload page and retry from mark_shipped button"
        )

# ── Computer Use Executor ──────────────────────────────

class ComputerUseExecutor:
    """Executes planned browser automation with validation"""

    async def execute_plan(self, plan: ComputerUsePlan) -> ExecutionResult:
        """Execute automation plan with reasoning"""
        logger.info(f"[SellIA Computer Use] Executing plan: {plan.goal}")

        actions_executed = 0
        extracted_data: Dict[str, Any] = {}

        try:
            for step in plan.steps:
                logger.debug(f"[SellIA] Action: {step.action_type.value}")

                if step.action_type == ActionType.NAVIGATE:
                    # Simulated: await browser.navigate(step.url)
                    pass

                elif step.action_type == ActionType.SCREENSHOT:
                    # Simulated: screenshot = await browser.screenshot()
                    pass

                elif step.action_type == ActionType.FILL_TEXT:
                    # Simulated: await browser.fill(step.selector, step.text)
                    pass

                elif step.action_type == ActionType.CLICK:
                    # Simulated: await browser.click(step.selector)
                    pass

                elif step.action_type == ActionType.EXTRACT_DATA:
                    # Simulated: data = await browser.extract_text(step.selector)
                    extracted_data[step.selector] = "extracted_value"

                elif step.action_type == ActionType.WAIT:
                    # Simulated: await browser.wait(step.wait_time)
                    pass

                actions_executed += 1

            # Validate execution
            validation_passed = self._validate_execution(plan, extracted_data)

            return ExecutionResult(
                success=True,
                actions_executed=actions_executed,
                extracted_data=extracted_data,
                validation_passed=validation_passed
            )

        except Exception as e:
            logger.error(f"[SellIA] Execution failed: {str(e)}")
            return ExecutionResult(
                success=False,
                actions_executed=actions_executed,
                error=str(e),
                validation_passed=False
            )

    @staticmethod
    def _validate_execution(plan: ComputerUsePlan, data: Dict[str, Any]) -> bool:
        """Validate execution against expected outcomes"""
        # Check if expected_outcome keywords present in extracted data
        expected_keywords = plan.expected_outcome.lower().split()
        data_str = str(data).lower()

        matched = sum(1 for kw in expected_keywords if kw in data_str)
        return matched >= len(expected_keywords) * 0.6  # 60% match threshold

# ── Workflow Orchestrator ──────────────────────────────

class ComputerUseWorkflow:
    """Chains multiple computer use plans into workflows"""

    def __init__(self):
        self.planner = ComputerUsePlanner()
        self.executor = ComputerUseExecutor()
        self.workflow_history: list[ExecutionResult] = []

    async def list_and_promote_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Workflow: List product → Promote to similar customers"""

        # Step 1: List product
        listing_plan = self.planner.plan_product_listing(
            product['name'],
            product['price'],
            BrowserContext.AMAZON
        )
        listing_result = await self.executor.execute_plan(listing_plan)
        self.workflow_history.append(listing_result)

        if not listing_result.success:
            return {"success": False, "error": "Product listing failed"}

        # Step 2: Send to similar customers (if available)
        for customer_email in product.get('target_emails', [])[:5]:  # Max 5 customers
            outreach_plan = self.planner.plan_customer_outreach(
                customer_email,
                product['name']
            )
            outreach_result = await self.executor.execute_plan(outreach_plan)
            self.workflow_history.append(outreach_result)

        return {
            "success": True,
            "steps_completed": len(self.workflow_history),
            "product_listed": listing_result.success,
            "customers_contacted": sum(1 for r in self.workflow_history[1:] if r.success)
        }

    async def process_orders_batch(self, order_ids: list[str]) -> Dict[str, Any]:
        """Workflow: Process multiple orders for fulfillment"""

        results = []
        for order_id in order_ids:
            plan = self.planner.plan_order_fulfillment(order_id)
            result = await self.executor.execute_plan(plan)
            results.append(result)
            self.workflow_history.append(result)

        return {
            "success": True,
            "total_orders": len(order_ids),
            "successfully_processed": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success)
        }

# ── Public API ─────────────────────────────────────

async def automate_product_listing(product: Dict[str, Any]) -> ExecutionResult:
    """Entry point: Automate product listing"""
    planner = ComputerUsePlanner()
    executor = ComputerUseExecutor()

    plan = planner.plan_product_listing(
        product['name'],
        product['price'],
        BrowserContext.CUSTOM_ECOMMERCE
    )

    return await executor.execute_plan(plan)

async def automate_customer_outreach(customer: Dict[str, Any], product: Dict[str, Any]) -> ExecutionResult:
    """Entry point: Automate customer outreach"""
    planner = ComputerUsePlanner()
    executor = ComputerUseExecutor()

    plan = planner.plan_customer_outreach(customer['email'], product['name'])

    return await executor.execute_plan(plan)

async def automate_order_processing(order_id: str) -> ExecutionResult:
    """Entry point: Automate order processing"""
    planner = ComputerUsePlanner()
    executor = ComputerUseExecutor()

    plan = planner.plan_order_fulfillment(order_id)

    return await executor.execute_plan(plan)
