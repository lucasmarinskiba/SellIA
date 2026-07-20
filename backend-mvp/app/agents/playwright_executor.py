"""Playwright executor · runs ToolAction from CUAClient against real browser.

Bridge between Anthropic Computer Use API and headless Chromium.

Usage:
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width":1280,"height":800})
        executor = PlaywrightExecutor(page)
        sess = await CUAClient().run(task="...", executor=executor.execute)
        await browser.close()
"""
import asyncio
import base64
import logging
from typing import Any

from app.agents.cua_client import ToolAction, ToolResult


logger = logging.getLogger(__name__)


class PlaywrightExecutor:
    """Maps Anthropic computer tool actions to Playwright API.

    Supported actions: screenshot · key · type · mouse_move · left_click ·
    left_click_drag · right_click · middle_click · double_click · scroll ·
    cursor_position · wait
    """

    def __init__(self, page: Any):  # playwright.async_api.Page
        self._page = page
        self._cursor_x = 0
        self._cursor_y = 0

    async def execute(self, action: ToolAction) -> ToolResult:
        """Dispatch by action name."""
        try:
            handler = getattr(self, f"_do_{action.action}", None)
            if handler is None:
                # Bash and editor tools not supported in browser context
                if action.tool in ("bash", "str_replace_editor"):
                    return ToolResult(
                        tool_use_id=action.tool_use_id,
                        content=f"Tool {action.tool} not available in browser sandbox",
                        is_error=True,
                    )
                return ToolResult(
                    tool_use_id=action.tool_use_id,
                    content=f"Unknown action: {action.action}",
                    is_error=True,
                )
            return await handler(action)
        except Exception as e:
            logger.exception("playwright_action_failed", extra={"action": action.action, "error": str(e)})
            return ToolResult(
                tool_use_id=action.tool_use_id,
                content=f"Action {action.action} failed: {e}",
                is_error=True,
            )

    # ─── Action handlers ───────────────────────────────────────────────────

    async def _do_screenshot(self, action: ToolAction) -> ToolResult:
        png = await self._page.screenshot(type="png", full_page=False)
        return ToolResult(
            tool_use_id=action.tool_use_id,
            image_base64=base64.b64encode(png).decode(),
        )

    async def _do_mouse_move(self, action: ToolAction) -> ToolResult:
        coord = action.params.get("coordinate", [0, 0])
        x, y = int(coord[0]), int(coord[1])
        await self._page.mouse.move(x, y)
        self._cursor_x, self._cursor_y = x, y
        return ToolResult(tool_use_id=action.tool_use_id, content=f"moved to ({x},{y})")

    async def _do_left_click(self, action: ToolAction) -> ToolResult:
        coord = action.params.get("coordinate")
        if coord:
            x, y = int(coord[0]), int(coord[1])
            await self._page.mouse.click(x, y)
            self._cursor_x, self._cursor_y = x, y
        else:
            await self._page.mouse.click(self._cursor_x, self._cursor_y)
        return ToolResult(tool_use_id=action.tool_use_id, content="clicked")

    async def _do_left_click_drag(self, action: ToolAction) -> ToolResult:
        start = action.params.get("start_coordinate", [self._cursor_x, self._cursor_y])
        end = action.params.get("coordinate", [self._cursor_x, self._cursor_y])
        await self._page.mouse.move(int(start[0]), int(start[1]))
        await self._page.mouse.down()
        await self._page.mouse.move(int(end[0]), int(end[1]), steps=10)
        await self._page.mouse.up()
        self._cursor_x, self._cursor_y = int(end[0]), int(end[1])
        return ToolResult(tool_use_id=action.tool_use_id, content="dragged")

    async def _do_right_click(self, action: ToolAction) -> ToolResult:
        coord = action.params.get("coordinate", [self._cursor_x, self._cursor_y])
        await self._page.mouse.click(int(coord[0]), int(coord[1]), button="right")
        return ToolResult(tool_use_id=action.tool_use_id, content="right-clicked")

    async def _do_middle_click(self, action: ToolAction) -> ToolResult:
        coord = action.params.get("coordinate", [self._cursor_x, self._cursor_y])
        await self._page.mouse.click(int(coord[0]), int(coord[1]), button="middle")
        return ToolResult(tool_use_id=action.tool_use_id, content="middle-clicked")

    async def _do_double_click(self, action: ToolAction) -> ToolResult:
        coord = action.params.get("coordinate", [self._cursor_x, self._cursor_y])
        await self._page.mouse.dblclick(int(coord[0]), int(coord[1]))
        return ToolResult(tool_use_id=action.tool_use_id, content="double-clicked")

    async def _do_type(self, action: ToolAction) -> ToolResult:
        text = action.params.get("text", "")
        await self._page.keyboard.type(text, delay=20)
        return ToolResult(tool_use_id=action.tool_use_id, content=f"typed {len(text)} chars")

    async def _do_key(self, action: ToolAction) -> ToolResult:
        # Anthropic passes keys like "Return", "ctrl+a", "Escape" — Playwright uses "Enter", "Control+A"
        key = action.params.get("text", "").strip()
        mapped = (
            key.replace("Return", "Enter")
               .replace("Page_Up", "PageUp")
               .replace("Page_Down", "PageDown")
               .replace("ctrl+", "Control+")
               .replace("cmd+", "Meta+")
               .replace("alt+", "Alt+")
               .replace("shift+", "Shift+")
        )
        for k in mapped.split("+"):
            await self._page.keyboard.press(mapped.replace("+", "+"))  # press whole chord
            break
        return ToolResult(tool_use_id=action.tool_use_id, content=f"pressed {key}")

    async def _do_scroll(self, action: ToolAction) -> ToolResult:
        direction = action.params.get("scroll_direction", "down")
        amount = int(action.params.get("scroll_amount", 3))
        coord = action.params.get("coordinate")
        if coord:
            await self._page.mouse.move(int(coord[0]), int(coord[1]))
        dy = amount * 100 * (1 if direction == "down" else -1)
        dx = amount * 100 * (1 if direction == "right" else -1) if direction in ("left", "right") else 0
        if direction in ("left", "right"):
            await self._page.mouse.wheel(dx, 0)
        else:
            await self._page.mouse.wheel(0, dy)
        return ToolResult(tool_use_id=action.tool_use_id, content=f"scrolled {direction} {amount}")

    async def _do_cursor_position(self, action: ToolAction) -> ToolResult:
        return ToolResult(tool_use_id=action.tool_use_id, content=f"X={self._cursor_x},Y={self._cursor_y}")

    async def _do_wait(self, action: ToolAction) -> ToolResult:
        duration = float(action.params.get("duration", 1.0))
        await asyncio.sleep(min(duration, 10.0))  # cap 10s
        return ToolResult(tool_use_id=action.tool_use_id, content=f"waited {duration}s")
