"""Tests para BrowserService.

Testea el control de navegador con mocks de Playwright para evitar
lanzar un browser real en los tests.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.computer_use.browser_service import BrowserService


@pytest_asyncio.fixture
async def browser_service():
    """Fixture de BrowserService con mocks."""
    service = BrowserService()
    return service


@pytest.mark.asyncio
async def test_validate_url_whitelist():
    """Test: URLs en whitelist son permitidas."""
    service = BrowserService()
    assert service._validate_url("https://canva.com/design") is True
    assert service._validate_url("https://docs.google.com") is True
    assert service._validate_url("https://google.com/search") is True


@pytest.mark.asyncio
async def test_validate_url_blacklist():
    """Test: URLs en blacklist son rechazadas."""
    service = BrowserService()
    assert service._validate_url("https://santander.com.ar") is False
    assert service._validate_url("https://localhost:3000") is False
    assert service._validate_url("https://192.168.1.1") is False


@pytest.mark.asyncio
async def test_validate_url_unknown():
    """Test: URLs desconocidas son rechazadas si hay whitelist."""
    service = BrowserService()
    assert service._validate_url("https://unknown-malicious-site.com") is False


@pytest.mark.asyncio
async def test_navigate_validates_url(browser_service):
    """Test: navigate rechaza URLs no permitidas."""
    browser_service._page = AsyncMock()
    with pytest.raises(ValueError, match="URL no permitida"):
        await browser_service.navigate("https://banco.com/login")


@pytest.mark.asyncio
async def test_navigate_without_browser_started(browser_service):
    """Test: navigate falla si browser no iniciado."""
    with pytest.raises(RuntimeError, match="Browser not started"):
        await browser_service.navigate("https://google.com")


@pytest.mark.asyncio
async def test_screenshot_without_browser(browser_service):
    """Test: screenshot falla si browser no iniciado."""
    with pytest.raises(RuntimeError, match="Browser not started"):
        await browser_service.screenshot()


@pytest.mark.asyncio
async def test_browser_lifecycle():
    """Test: start y stop del browser."""
    service = BrowserService()

    with patch("app.domains.computer_use.browser_service.async_playwright") as mock_pw:
        # Setup mocks
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.set_default_timeout = MagicMock()  # sync in Playwright
        mock_page.route = AsyncMock()
        mock_page.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_page.wait_for_timeout = AsyncMock()
        from PIL import Image
        from io import BytesIO
        _img = Image.new("RGB", (10, 10), color="red")
        _buf = BytesIO()
        _img.save(_buf, format="PNG")
        mock_page.screenshot = AsyncMock(return_value=_buf.getvalue())
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Example")
        mock_page.mouse.click = AsyncMock()
        mock_page.keyboard.type = AsyncMock()
        mock_page.mouse.wheel = AsyncMock()
        mock_page.keyboard.press = AsyncMock()

        # Start
        await service.start(headless=True)
        assert service._page is mock_page

        # Navigate
        result = await service.navigate("https://google.com")
        assert result["success"] is True

        # Screenshot
        screenshot = await service.screenshot()
        assert isinstance(screenshot, bytes)
        assert len(screenshot) > 0

        # Click
        result = await service.click(100, 200)
        assert result["success"] is True

        # Type
        result = await service.type("hello world")
        assert result["success"] is True

        # Scroll
        result = await service.scroll("down", 500)
        assert result["success"] is True

        # Get page info
        info = await service.get_page_info()
        assert info["url"] == "https://example.com"
        assert info["title"] == "Example"

        # Stop
        await service.stop()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_on_exception():
    """Test: stop limpia recursos incluso con errores."""
    service = BrowserService()

    with patch("app.domains.computer_use.browser_service.async_playwright") as mock_pw:
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()

        mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.set_default_timeout = MagicMock()  # sync in Playwright
        mock_context.new_page = AsyncMock(side_effect=Exception("Page error"))

        with pytest.raises(Exception):
            await service.start(headless=True)

        # Stop no debe fallar
        await service.stop()


# ── resource routing ────────────────────────────────────────────────────
def _route_req(resource_type: str, url: str):
    """Helper: mock Playwright route + request pair."""
    route = AsyncMock()
    request = MagicMock()
    request.resource_type = resource_type
    request.url = url
    return route, request


@pytest.mark.asyncio
async def test_route_handler_blocks_heavy_resources(browser_service):
    """Test: imágenes/media/fonts se abortan."""
    for rtype in ("image", "media", "font"):
        route, req = _route_req(rtype, "https://cdn.site.com/asset")
        await browser_service._route_handler(route, req)
        route.abort.assert_awaited_once()
        route.continue_.assert_not_awaited()


@pytest.mark.asyncio
async def test_route_handler_blocks_trackers(browser_service):
    """Test: trackers/ads se abortan aunque sean documents/scripts."""
    for url in (
        "https://www.google-analytics.com/collect",
        "https://connect.facebook.com/tr?id=1",
        "https://cdn.segment.io/analytics.js",
    ):
        route, req = _route_req("script", url)
        await browser_service._route_handler(route, req)
        route.abort.assert_awaited_once()


@pytest.mark.asyncio
async def test_route_handler_allows_normal(browser_service):
    """Test: documents/scripts normales continúan."""
    route, req = _route_req("document", "https://canva.com/design")
    await browser_service._route_handler(route, req)
    route.continue_.assert_awaited_once()
    route.abort.assert_not_awaited()


@pytest.mark.asyncio
async def test_route_handler_allows_data_uri_images(browser_service):
    """Test: imágenes inline data: no se bloquean."""
    route, req = _route_req("image", "data:image/png;base64,AAAA")
    await browser_service._route_handler(route, req)
    route.continue_.assert_awaited_once()


# ── smart settle ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_settle_waits_networkidle(browser_service):
    """Test: _settle espera networkidle y luego piso corto."""
    page = AsyncMock()
    browser_service._page = page
    await browser_service._settle(floor_ms=0)
    page.wait_for_load_state.assert_awaited_once()
    # floor=0 → no timeout wait
    page.wait_for_timeout.assert_not_awaited()


@pytest.mark.asyncio
async def test_settle_falls_back_on_timeout(browser_service):
    """Test: si networkidle nunca dispara, cae al piso (timeout)."""
    page = AsyncMock()
    page.wait_for_load_state = AsyncMock(side_effect=Exception("timeout"))
    browser_service._page = page
    await browser_service._settle(floor_ms=200)
    page.wait_for_timeout.assert_awaited_once()


@pytest.mark.asyncio
async def test_settle_noop_without_page(browser_service):
    """Test: _settle no rompe si no hay page."""
    browser_service._page = None
    await browser_service._settle()  # no exception


# ── DOM-precise actions ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_click_selector_success(browser_service):
    page = AsyncMock()
    browser_service._page = page
    result = await browser_service.click_selector("button#go")
    assert result["success"] is True
    page.click.assert_awaited_once()


@pytest.mark.asyncio
async def test_click_text_success(browser_service):
    page = AsyncMock()
    locator = AsyncMock()
    page.get_by_text = MagicMock(return_value=MagicMock(first=locator))
    browser_service._page = page
    result = await browser_service.click_text("Aceptar")
    assert result["success"] is True
    locator.click.assert_awaited_once()


@pytest.mark.asyncio
async def test_fill_success(browser_service):
    page = AsyncMock()
    browser_service._page = page
    result = await browser_service.fill("input[name=email]", "a@b.com")
    assert result["success"] is True
    page.fill.assert_awaited_once()


@pytest.mark.asyncio
async def test_wait_for_selector_failure_returns_error(browser_service):
    page = AsyncMock()
    page.wait_for_selector = AsyncMock(side_effect=Exception("not found"))
    browser_service._page = page
    result = await browser_service.wait_for_selector(".missing", timeout_ms=100)
    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_dom_actions_guard_without_browser(browser_service):
    """Test: acciones DOM fallan si browser no iniciado."""
    browser_service._page = None
    for coro in (
        browser_service.click_selector("x"),
        browser_service.click_text("x"),
        browser_service.fill("x", "y"),
        browser_service.wait_for_selector("x"),
    ):
        with pytest.raises(RuntimeError, match="Browser not started"):
            await coro


# ── interactive elements snapshot ───────────────────────────────────────
@pytest.mark.asyncio
async def test_get_interactive_elements(browser_service):
    page = AsyncMock()
    page.evaluate = AsyncMock(return_value=[
        {"tag": "button", "role": "button", "label": "Enviar", "x": 10, "y": 20, "w": 80, "h": 30},
    ])
    browser_service._page = page
    out = await browser_service.get_interactive_elements(limit=10)
    assert out and out[0]["label"] == "Enviar"
    page.evaluate.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_interactive_elements_swallows_error(browser_service):
    page = AsyncMock()
    page.evaluate = AsyncMock(side_effect=Exception("eval boom"))
    browser_service._page = page
    out = await browser_service.get_interactive_elements()
    assert out == []


# ── page property ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_page_property(browser_service):
    assert browser_service.page is None
    sentinel = MagicMock()
    browser_service._page = sentinel
    assert browser_service.page is sentinel
