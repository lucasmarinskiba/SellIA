"""Computer Use — CAPTCHA Detector

Detecta la presencia de CAPTCHAs en screenshots usando heurísticas visuales
(cambios de tamaño inesperados, textos típicos) y opcionalmente un modelo
de visión liviano. Cuando detecta un CAPTCHA, pausa la sesión y notifica.
"""

import re
from typing import Optional, Tuple
from PIL import Image
import io

from app.core.logger import get_logger

logger = get_logger(__name__)


class CaptchaDetector:
    """Detector de CAPTCHAs en screenshots."""

    # Keywords commonly found in CAPTCHA pages
    CAPTCHA_KEYWORDS = [
        r"captcha",
        r"recaptcha",
        r"hcaptcha",
        r"i['\u2019]m not a robot",
        r"verify you are human",
        r"security check",
        r"prove you['\u2019]re human",
        r"cloudflare",
        r"ddos protection",
        r"bot detection",
        r"challenge",
        r"select all",
        r"images? containing",
    ]

    # Common CAPTCHA element selectors (for page source analysis)
    CAPTCHA_SELECTORS = [
        "#recaptcha",
        ".g-recaptcha",
        "[data-sitekey]",
        ".h-captcha",
        "#cf-challenge-running",
        "#turnstile",
    ]

    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold

    def detect_from_text(self, page_text: str, page_url: str = "") -> Tuple[bool, float, str]:
        """Detecta CAPTCHA analizando texto de la página."""
        text_lower = page_text.lower()
        url_lower = page_url.lower()

        score = 0.0
        matched_keywords = []

        for keyword in self.CAPTCHA_KEYWORDS:
            if re.search(keyword, text_lower, re.IGNORECASE):
                score += 0.15
                matched_keywords.append(keyword)

        # URL-based indicators
        if "recaptcha" in url_lower or "captcha" in url_lower:
            score += 0.3

        # Title-based
        if any(word in text_lower[:200] for word in ["challenge", "verify", "security check"]):
            score += 0.2

        is_captcha = score >= self.confidence_threshold
        reason = f"Keywords matched: {matched_keywords[:3]}" if matched_keywords else "No CAPTCHA indicators"

        return is_captcha, min(score, 1.0), reason

    def detect_from_image(self, screenshot_bytes: bytes) -> Tuple[bool, float, str]:
        """Detecta CAPTCHA analizando la imagen (heurísticas simples)."""
        try:
            img = Image.open(io.BytesIO(screenshot_bytes))
            width, height = img.size

            # CAPTCHA pages often have specific dimensions or patterns
            # Check if page is mostly a form (simplified heuristic)
            # In a production system, this would use an ML model

            # For now, return low confidence - real implementation would use OCR or ML
            # This is a placeholder for future vision model integration
            return False, 0.0, "Image analysis not implemented (requires vision model)"

        except Exception as e:
            logger.warning(f"CaptchaDetector image analysis failed: {e}")
            return False, 0.0, f"Analysis error: {e}"

    async def detect_from_page(self, page) -> Tuple[bool, float, str]:
        """Detecta CAPTCHA analizando la página activa de Playwright."""
        try:
            # Get page content
            content = await page.content()
            url = page.url

            # Check for CAPTCHA selectors
            for selector in self.CAPTCHA_SELECTORS:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        return True, 0.95, f"CAPTCHA element found: {selector}"
                except Exception:
                    pass

            # Text-based detection
            is_captcha, score, reason = self.detect_from_text(content, url)

            # Additional: check for iframe-based CAPTCHAs
            frames = page.frames
            for frame in frames:
                try:
                    frame_url = frame.url
                    if any(keyword in frame_url.lower() for keyword in ["recaptcha", "hcaptcha", "turnstile"]):
                        return True, 0.95, f"CAPTCHA iframe detected: {frame_url}"
                except Exception:
                    pass

            return is_captcha, score, reason

        except Exception as e:
            logger.warning(f"CaptchaDetector page analysis failed: {e}")
            return False, 0.0, f"Page analysis error: {e}"

    def get_user_message(self, confidence: float) -> str:
        """Mensaje para mostrar al usuario cuando se detecta CAPTCHA."""
        if confidence > 0.9:
            return "🔒 CAPTCHA detectado con alta confianza. La sesión ha sido pausada. Por favor resuelvelo manualmente y luego reanudá."
        elif confidence > 0.7:
            return "⚠️ Posible CAPTCHA detectado. La sesión fue pausada por precaución. Verificá y reanudá si todo está bien."
        return "ℹ️ Se detectaron indicadores de CAPTCHA. Revisá la página y reanudá la sesión si es necesario."
