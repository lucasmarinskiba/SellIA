"""Tests para Computer Use Services"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from app.domains.computer_use.services.action_validator import ActionValidator
from app.domains.computer_use.services.retry_handler import RetryHandler, CircuitBreaker, CircuitBreakerOpen
from app.domains.computer_use.services.captcha_detector import CaptchaDetector
from app.domains.computer_use.services.screenshot_compare import ScreenshotComparator
from app.domains.computer_use.services.proxy_manager import ProxyManager, ProxyConfig


class TestActionValidator:
    def test_validate_navigate_valid(self):
        validator = ActionValidator()
        valid, error = validator.validate_action("navigate", {"url": "https://example.com"})
        assert valid is True
        assert error is None

    def test_validate_navigate_blocked_scheme(self):
        validator = ActionValidator()
        valid, error = validator.validate_action("navigate", {"url": "javascript:alert(1)"})
        assert valid is False
        assert "Esquema URL bloqueado" in error

    def test_validate_click_valid(self):
        validator = ActionValidator()
        valid, error = validator.validate_action("click", {"x": 100, "y": 200})
        assert valid is True

    def test_validate_click_out_of_range(self):
        validator = ActionValidator()
        valid, error = validator.validate_action("click", {"x": 10000, "y": 200})
        assert valid is False
        assert "fuera de rango" in error

    def test_validate_type_too_long(self):
        validator = ActionValidator()
        valid, error = validator.validate_action("type", {"text": "x" * 20000})
        assert valid is False
        assert "demasiado largo" in error

    def test_validate_scroll_invalid_direction(self):
        validator = ActionValidator()
        valid, error = validator.validate_action("scroll", {"direction": "diagonal", "amount": 100})
        assert valid is False
        assert "Dirección" in error


class TestRetryHandler:
    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        handler = RetryHandler()
        result = await handler.execute(lambda: 42)
        assert result == 42

    @pytest.mark.asyncio
    async def test_retry_then_success(self):
        handler = RetryHandler()
        mock_func = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        result = await handler.execute(mock_func)
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        handler = RetryHandler()
        mock_func = MagicMock(side_effect=Exception("always fails"))
        with pytest.raises(Exception, match="always fails"):
            await handler.execute(mock_func)
        assert mock_func.call_count == 4  # initial + 3 retries


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_closes_after_success(self):
        cb = CircuitBreaker("test")
        result = await cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state.value == "closed"

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        cb = CircuitBreaker("test", MagicMock(failure_threshold=2, recovery_timeout=1, half_open_max_calls=1))
        # Force failures
        for _ in range(3):
            try:
                await cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
            except Exception:
                pass
        assert cb.state.value == "open"

    @pytest.mark.asyncio
    async def test_circuit_rejects_when_open(self):
        cb = CircuitBreaker("test", MagicMock(failure_threshold=1, recovery_timeout=3600, half_open_max_calls=1))
        try:
            await cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass
        with pytest.raises(CircuitBreakerOpen):
            await cb.call(lambda: "ok")


class TestCaptchaDetector:
    def test_detect_recaptcha(self):
        detector = CaptchaDetector(confidence_threshold=0.4)
        text = "<div>Please complete the reCAPTCHA challenge</div>"
        is_captcha, confidence, reason = detector.detect_from_text(text)
        assert is_captcha is True
        assert confidence > 0.4

    def test_detect_normal_page(self):
        detector = CaptchaDetector()
        text = "<div>Welcome to our website</div>"
        is_captcha, confidence, _ = detector.detect_from_text(text)
        assert is_captcha is False

    def test_user_message_high_confidence(self):
        detector = CaptchaDetector()
        msg = detector.get_user_message(0.95)
        assert "alta confianza" in msg


class TestScreenshotComparator:
    def test_identical_images(self):
        comparator = ScreenshotComparator()
        from PIL import Image
        img = Image.new("RGB", (10, 10), color="red")
        buf = BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        result = comparator.compare(png_bytes, png_bytes)
        assert result.changed is False
        assert result.similarity == 1.0

    def test_different_images(self):
        comparator = ScreenshotComparator()
        from PIL import Image
        img1 = Image.new("RGB", (10, 10), color="red")
        img2 = Image.new("RGB", (10, 10), color="blue")
        buf1 = BytesIO()
        buf2 = BytesIO()
        img1.save(buf1, format="PNG")
        img2.save(buf2, format="PNG")
        result = comparator.compare(buf1.getvalue(), buf2.getvalue())
        assert result.changed is True
        assert result.similarity < 1.0


class TestProxyManager:
    def test_add_and_get_proxy(self):
        manager = ProxyManager()
        config = ProxyConfig(host="proxy.example.com", port=8080, username="user", password="pass")
        manager.add_proxy(config)
        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080

    def test_to_playwright_format(self):
        config = ProxyConfig(host="proxy.example.com", port=8080, username="user", password="pass")
        pw_format = config.to_playwright_format()
        assert pw_format["server"] == "http://proxy.example.com:8080"
        assert pw_format["username"] == "user"
        assert pw_format["password"] == "pass"

    def test_mark_unhealthy(self):
        manager = ProxyManager()
        config = ProxyConfig(host="proxy.example.com", port=8080)
        manager.add_proxy(config)
        manager.mark_unhealthy("proxy.example.com", 8080)
        stats = manager.get_stats()
        assert stats["healthy"] == 0
        assert stats["unhealthy"] == 1
