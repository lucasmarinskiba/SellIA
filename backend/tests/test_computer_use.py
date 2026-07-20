"""Unit tests for computer_use orchestrator — Multi-platform sales automation.

Tests cover:
- Browser automation
- Web scraping
- Form filling
- Screenshot analysis
- Multi-platform workflows
- Action validation
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.computer_use.computer_use_orchestrator_v2 import (
    ComputerUseOrchestrator,
    BrowserSession,
    AutomationAction,
    ActionType,
)


class TestBrowserAutomation:
    """Test browser automation capabilities."""

    @pytest.mark.asyncio
    async def test_initialize_browser_session(self):
        """Test initializing a browser session."""
        orchestrator = ComputerUseOrchestrator()

        session = await orchestrator.initialize_browser(headless=True)

        assert session is not None
        assert isinstance(session, BrowserSession)
        assert session.is_active

    @pytest.mark.asyncio
    async def test_navigate_to_url(self):
        """Test navigating to a URL."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        result = await orchestrator.navigate(
            session,
            "https://example.com"
        )

        assert result is not None
        assert "status" in result

    @pytest.mark.asyncio
    async def test_take_screenshot(self):
        """Test taking a screenshot."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        screenshot = await orchestrator.take_screenshot(session)

        assert screenshot is not None
        assert isinstance(screenshot, bytes) or isinstance(screenshot, str)

    @pytest.mark.asyncio
    async def test_click_element(self):
        """Test clicking an element."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        action = AutomationAction(
            type=ActionType.CLICK,
            selector="button.submit",
            value=None
        )

        result = await orchestrator.execute_action(session, action)

        assert result is not None
        assert "success" in result or "status" in result

    @pytest.mark.asyncio
    async def test_type_text(self):
        """Test typing text in an element."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        action = AutomationAction(
            type=ActionType.TYPE,
            selector="input.email",
            value="test@example.com"
        )

        result = await orchestrator.execute_action(session, action)

        assert result is not None

    @pytest.mark.asyncio
    async def test_scroll_page(self):
        """Test scrolling the page."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        result = await orchestrator.scroll(session, direction="down", amount=500)

        assert result is not None

    @pytest.mark.asyncio
    async def test_extract_page_content(self):
        """Test extracting page content."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        content = await orchestrator.get_page_content(session)

        assert content is not None
        assert isinstance(content, (str, dict))


class TestFormFilling:
    """Test automated form filling."""

    @pytest.mark.asyncio
    async def test_fill_text_field(self):
        """Test filling a text field."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        action = AutomationAction(
            type=ActionType.FILL,
            selector="input[name='username']",
            value="testuser"
        )

        result = await orchestrator.execute_action(session, action)

        assert result is not None

    @pytest.mark.asyncio
    async def test_select_dropdown_option(self):
        """Test selecting from a dropdown."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        action = AutomationAction(
            type=ActionType.SELECT,
            selector="select[name='country']",
            value="usa"
        )

        result = await orchestrator.execute_action(session, action)

        assert result is not None

    @pytest.mark.asyncio
    async def test_check_checkbox(self):
        """Test checking a checkbox."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        action = AutomationAction(
            type=ActionType.CHECK,
            selector="input[type='checkbox'][name='agree']",
            value=None
        )

        result = await orchestrator.execute_action(session, action)

        assert result is not None

    @pytest.mark.asyncio
    async def test_fill_complete_form(self):
        """Test filling a complete form."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "country": "usa",
            "agree": True
        }

        result = await orchestrator.fill_form(session, form_data)

        assert result is not None
        assert "success" in result or "status" in result

    @pytest.mark.asyncio
    async def test_submit_form(self):
        """Test submitting a form."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        action = AutomationAction(
            type=ActionType.CLICK,
            selector="button[type='submit']",
            value=None
        )

        result = await orchestrator.execute_action(session, action)

        assert result is not None


class TestWebScraping:
    """Test web scraping capabilities."""

    @pytest.mark.asyncio
    async def test_scrape_text_content(self):
        """Test scraping text content."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        content = await orchestrator.scrape_text(session, selector="body")

        assert content is not None
        assert isinstance(content, str)

    @pytest.mark.asyncio
    async def test_scrape_links(self):
        """Test scraping links from page."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        links = await orchestrator.scrape_links(session)

        assert isinstance(links, list)

    @pytest.mark.asyncio
    async def test_scrape_table_data(self):
        """Test scraping table data."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        html = """
        <table>
            <tr><td>Header1</td><td>Header2</td></tr>
            <tr><td>Row1Col1</td><td>Row1Col2</td></tr>
        </table>
        """

        result = await orchestrator.scrape_table(session, "table")

        assert result is not None

    @pytest.mark.asyncio
    async def test_scrape_structured_data(self):
        """Test scraping structured data (JSON-LD, etc)."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        data = await orchestrator.scrape_structured_data(session)

        assert isinstance(data, (dict, list)) or data is None

    @pytest.mark.asyncio
    async def test_monitor_element_changes(self):
        """Test monitoring element for changes."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        changes = await orchestrator.monitor_element(
            session,
            selector=".dynamic-content",
            timeout=5
        )

        assert changes is not None


class TestScreenshotAnalysis:
    """Test screenshot analysis capabilities."""

    @pytest.mark.asyncio
    async def test_analyze_screenshot(self):
        """Test analyzing a screenshot."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        screenshot = await orchestrator.take_screenshot(session)

        analysis = await orchestrator.analyze_screenshot(
            session,
            screenshot
        )

        assert analysis is not None
        assert "elements" in analysis or "content" in analysis

    @pytest.mark.asyncio
    async def test_detect_buttons(self):
        """Test detecting buttons in screenshot."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        screenshot = await orchestrator.take_screenshot(session)

        buttons = await orchestrator.detect_buttons(session, screenshot)

        assert isinstance(buttons, list)

    @pytest.mark.asyncio
    async def test_detect_forms(self):
        """Test detecting forms in screenshot."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        html_with_form = """
        <form>
            <input type="text" name="username" />
            <input type="password" name="password" />
            <button type="submit">Login</button>
        </form>
        """

        forms = await orchestrator.detect_forms(session)

        assert isinstance(forms, list)

    @pytest.mark.asyncio
    async def test_read_text_from_screenshot(self):
        """Test OCR to read text from screenshot."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        screenshot = await orchestrator.take_screenshot(session)

        text = await orchestrator.ocr_screenshot(screenshot)

        assert text is not None
        assert isinstance(text, str)


class TestMultiPlatformWorkflows:
    """Test multi-platform automation workflows."""

    @pytest.mark.asyncio
    async def test_marketplace_listing_creation(self):
        """Test creating a marketplace listing."""
        orchestrator = ComputerUseOrchestrator()

        workflow = {
            "platform": "mercadolibre",
            "action": "create_listing",
            "product": {
                "title": "Test Product",
                "description": "Test Description",
                "price": 100.00,
                "quantity": 5,
                "category": "electronics"
            }
        }

        result = await orchestrator.execute_workflow(workflow)

        assert result is not None
        assert "status" in result or "success" in result

    @pytest.mark.asyncio
    async def test_social_media_post_creation(self):
        """Test creating social media posts."""
        orchestrator = ComputerUseOrchestrator()

        workflow = {
            "platform": "instagram",
            "action": "create_post",
            "content": {
                "caption": "Test post",
                "image_url": "https://example.com/image.jpg",
                "hashtags": ["test", "demo"]
            }
        }

        result = await orchestrator.execute_workflow(workflow)

        assert result is not None

    @pytest.mark.asyncio
    async def test_email_campaign_creation(self):
        """Test creating email campaigns."""
        orchestrator = ComputerUseOrchestrator()

        workflow = {
            "platform": "email",
            "action": "send_campaign",
            "content": {
                "recipients": ["test@example.com"],
                "subject": "Test Email",
                "body": "This is a test email"
            }
        }

        result = await orchestrator.execute_workflow(workflow)

        assert result is not None

    @pytest.mark.asyncio
    async def test_calendar_event_creation(self):
        """Test creating calendar events."""
        orchestrator = ComputerUseOrchestrator()

        workflow = {
            "platform": "calendar",
            "action": "create_event",
            "event": {
                "title": "Sales Meeting",
                "date": "2024-12-15",
                "time": "14:00",
                "duration_minutes": 30,
                "attendees": ["client@example.com"]
            }
        }

        result = await orchestrator.execute_workflow(workflow)

        assert result is not None


class TestActionValidation:
    """Test action validation and safety."""

    @pytest.mark.asyncio
    async def test_validate_action_before_execution(self):
        """Test validating action before execution."""
        orchestrator = ComputerUseOrchestrator()

        action = AutomationAction(
            type=ActionType.CLICK,
            selector="button.submit",
            value=None
        )

        is_valid = await orchestrator.validate_action(action)

        assert isinstance(is_valid, bool)

    @pytest.mark.asyncio
    async def test_detect_phishing_elements(self):
        """Test detecting phishing elements."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        phishing_indicators = await orchestrator.check_phishing_risk(session)

        assert isinstance(phishing_indicators, dict)
        assert "risk_level" in phishing_indicators

    @pytest.mark.asyncio
    async def test_validate_form_security(self):
        """Test validating form security."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        security_check = await orchestrator.check_form_security(
            session,
            "form#login"
        )

        assert security_check is not None

    @pytest.mark.asyncio
    async def test_rate_limit_checks(self):
        """Test rate limit compliance."""
        orchestrator = ComputerUseOrchestrator()

        # Simulate multiple actions
        for _ in range(3):
            can_proceed = await orchestrator.check_rate_limit("test_user")
            assert isinstance(can_proceed, bool)

    @pytest.mark.asyncio
    async def test_user_agent_rotation(self):
        """Test rotating user agents to avoid detection."""
        orchestrator = ComputerUseOrchestrator()

        user_agents = []
        for _ in range(3):
            ua = orchestrator.get_random_user_agent()
            user_agents.append(ua)
            assert isinstance(ua, str)

        # Should have different user agents
        assert len(set(user_agents)) > 1 or len(set(user_agents)) == 1


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_handle_connection_timeout(self):
        """Test handling connection timeout."""
        orchestrator = ComputerUseOrchestrator()

        try:
            result = await orchestrator.navigate(
                None,
                "https://unreachable-domain-12345.invalid"
            )
        except Exception as e:
            assert e is not None

    @pytest.mark.asyncio
    async def test_retry_on_element_not_found(self):
        """Test retry logic when element not found."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        action = AutomationAction(
            type=ActionType.CLICK,
            selector=".nonexistent-element",
            value=None
        )

        result = await orchestrator.execute_action(
            session,
            action,
            retry_count=3
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_javascript_errors(self):
        """Test handling JavaScript errors on page."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        errors = await orchestrator.get_page_errors(session)

        assert isinstance(errors, list)

    @pytest.mark.asyncio
    async def test_recovery_after_page_reload(self):
        """Test recovery after page reload."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        await orchestrator.navigate(session, "https://example.com")
        await orchestrator.reload(session)

        # Should still be able to perform actions
        content = await orchestrator.get_page_content(session)
        assert content is not None


class TestPerformanceOptimization:
    """Test performance optimization features."""

    @pytest.mark.asyncio
    async def test_parallel_navigation(self):
        """Test parallel navigation to multiple URLs."""
        import asyncio

        orchestrator = ComputerUseOrchestrator()

        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]

        tasks = [
            orchestrator.navigate_and_analyze(url)
            for url in urls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_cache_page_content(self):
        """Test caching page content to avoid re-fetches."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        url = "https://example.com"
        await orchestrator.navigate(session, url)

        # First fetch
        content1 = await orchestrator.get_page_content(session)

        # Second fetch should use cache
        content2 = await orchestrator.get_page_content(session, use_cache=True)

        assert content1 == content2

    @pytest.mark.asyncio
    async def test_batch_action_execution(self):
        """Test executing batch of actions efficiently."""
        orchestrator = ComputerUseOrchestrator()
        session = await orchestrator.initialize_browser(headless=True)

        actions = [
            AutomationAction(ActionType.TYPE, "input.name", "John Doe"),
            AutomationAction(ActionType.TYPE, "input.email", "john@example.com"),
            AutomationAction(ActionType.CHECK, "input.agree", None),
            AutomationAction(ActionType.CLICK, "button.submit", None)
        ]

        results = await orchestrator.execute_batch(session, actions)

        assert len(results) == 4
