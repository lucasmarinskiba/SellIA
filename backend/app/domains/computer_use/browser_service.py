"""Computer Use — Browser Service

Controla un navegador headless con Playwright para ejecutar acciones
de automatización visual: navegación, clicks, typing, scroll, screenshots.

Optimizado para precisión, velocidad y eficiencia:
  - Esperas inteligentes (network/DOM settle) en vez de sleeps fijos.
  - Bloqueo agresivo de recursos pesados (imágenes/media/fonts/ads).
  - Acciones DOM-precisas (selector/texto/rol) además de coordenadas.
  - Reintentos en navegación y snapshot de elementos interactivos para
    alimentar al agente de visión con coordenadas exactas.
"""

import io
import re
from typing import Optional, Any
from urllib.parse import urlparse

from playwright.async_api import async_playwright
from PIL import Image

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Heavy / tracking resources never needed for automation
_BLOCK_RESOURCE_TYPES = {"image", "media", "font"}
_BLOCK_URL_PATTERNS = [
    r"google-analytics", r"googletagmanager", r"facebook\.com/tr",
    r"doubleclick", r"adsystem", r"adservice", r"/ads?[/?]",
    r"analytics", r"hotjar", r"segment\.(io|com)", r"mixpanel",
    r"fullstory", r"clarity\.ms", r"amplitude", r"intercom",
]
_BLOCK_URL_RE = re.compile("|".join(_BLOCK_URL_PATTERNS), re.IGNORECASE)


class BrowserService:
    """Servicio de control de navegador para Computer Use Agents."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Optional[Any] = None
        self._context: Optional[Any] = None
        self._page: Optional[Any] = None
        self._viewport = {"width": 1280, "height": 720}

    # ── lifecycle ───────────────────────────────────────────────────────
    @property
    def page(self) -> Optional[Any]:
        """Active Playwright page (read-only accessor)."""
        return self._page

    async def start(self, headless: bool = True) -> None:
        """Inicia el navegador headless con flags de rendimiento."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--single-process",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-default-apps",
                "--mute-audio",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
            ],
        )
        self._context = await self._browser.new_context(
            viewport=self._viewport,
            device_scale_factor=settings.COMPUTER_USE_DEVICE_SCALE,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="es-ES",
            timezone_id="America/Argentina/Buenos_Aires",
        )
        # Default per-action timeout so individual ops fail fast instead of hanging
        self._context.set_default_timeout(settings.COMPUTER_USE_NAV_TIMEOUT_MS)
        self._page = await self._context.new_page()

        if settings.COMPUTER_USE_BLOCK_RESOURCES:
            await self._page.route("**/*", self._route_handler)
        logger.info("BrowserService started (block_resources=%s)", settings.COMPUTER_USE_BLOCK_RESOURCES)

    async def _route_handler(self, route: Any, request: Any) -> None:
        """Aborta recursos pesados y trackers; deja pasar el resto."""
        try:
            rtype = request.resource_type
            url = request.url
            if rtype in _BLOCK_RESOURCE_TYPES and not url.startswith("data:"):
                await route.abort()
                return
            if _BLOCK_URL_RE.search(url):
                await route.abort()
                return
            await route.continue_()
        except Exception:
            # Never let a routing error stall the page
            try:
                await route.continue_()
            except Exception:
                pass

    async def stop(self) -> None:
        """Cierra el navegador y libera recursos."""
        for closer, label in (
            (lambda: self._context and self._context.close(), "context"),
            (lambda: self._browser and self._browser.close(), "browser"),
            (lambda: self._playwright and self._playwright.stop(), "playwright"),
        ):
            try:
                coro = closer()
                if coro:
                    await coro
            except Exception as e:
                logger.warning(f"Error closing {label}: {e}")
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        logger.info("BrowserService stopped")

    # ── internal helpers ────────────────────────────────────────────────
    async def _settle(self, floor_ms: Optional[int] = None) -> None:
        """Espera inteligente: red inactiva + DOM listo, con piso corto.

        Reemplaza los ``wait_for_timeout`` fijos. Sale apenas la página se
        estabiliza, evitando esperas innecesarias y reduciendo latencia.
        """
        if not self._page:
            return
        floor = settings.COMPUTER_USE_ACTION_SETTLE_MS if floor_ms is None else floor_ms
        try:
            await self._page.wait_for_load_state(
                "networkidle", timeout=settings.COMPUTER_USE_SETTLE_TIMEOUT_MS
            )
        except Exception:
            # networkidle may never fire on streaming pages — fall back to floor
            if floor > 0:
                await self._page.wait_for_timeout(floor)
            return
        if floor > 0:
            await self._page.wait_for_timeout(floor)

    def _validate_url(self, url: str) -> bool:
        """Valida que la URL esté en la whitelist y no en la blacklist."""
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        for blocked in settings.COMPUTER_USE_URL_BLACKLIST:
            if blocked.lower() in hostname:
                logger.warning(f"URL blocked by blacklist: {url} (matched: {blocked})")
                return False

        if not settings.COMPUTER_USE_URL_WHITELIST:
            return True

        for allowed in settings.COMPUTER_USE_URL_WHITELIST:
            if allowed.lower() in hostname:
                return True

        logger.warning(f"URL not in whitelist: {url}")
        return False

    # ── navigation ──────────────────────────────────────────────────────
    async def navigate(self, url: str) -> dict:
        """Navega a una URL (validada) con reintento y espera inteligente."""
        if not self._page:
            raise RuntimeError("Browser not started")
        if not self._validate_url(url):
            raise ValueError(f"URL no permitida: {url}")

        last_err: Optional[str] = None
        for attempt in range(2):
            try:
                response = await self._page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=settings.COMPUTER_USE_NAV_TIMEOUT_MS,
                )
                await self._settle()
                return {
                    "success": True,
                    "url": self._page.url,
                    "title": await self._page.title(),
                    "status": response.status if response else None,
                }
            except Exception as e:
                last_err = str(e)
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
        return {"success": False, "error": last_err}

    # ── screenshots ─────────────────────────────────────────────────────
    async def screenshot(self) -> bytes:
        """Captura la pantalla, comprime y redimensiona a JPEG."""
        if not self._page:
            raise RuntimeError("Browser not started")
        raw_bytes = await self._page.screenshot(type="png", full_page=False)
        return self._encode_jpeg(raw_bytes)

    async def screenshot_element(self, selector: str) -> Optional[bytes]:
        """Captura solo un elemento (más preciso y liviano)."""
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            el = await self._page.query_selector(selector)
            if not el:
                return None
            raw = await el.screenshot(type="png")
            return self._encode_jpeg(raw)
        except Exception as e:
            logger.warning(f"Element screenshot failed: {e}")
            return None

    def _encode_jpeg(self, raw_bytes: bytes) -> bytes:
        img = Image.open(io.BytesIO(raw_bytes))
        max_width = settings.COMPUTER_USE_MAX_SCREENSHOT_WIDTH
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.convert("RGB").save(
            output, format="JPEG", quality=settings.COMPUTER_USE_SCREENSHOT_QUALITY, optimize=True
        )
        output.seek(0)
        return output.getvalue()

    # ── coordinate actions (vision path) ────────────────────────────────
    async def click(self, x: int, y: int) -> dict:
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            await self._page.mouse.click(x, y)
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def double_click(self, x: int, y: int) -> dict:
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            await self._page.mouse.dblclick(x, y)
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def right_click(self, x: int, y: int) -> dict:
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            await self._page.mouse.click(x, y, button="right")
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type(self, text: str) -> dict:
        """Escribe texto en el campo enfocado."""
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            await self._page.keyboard.type(text, delay=settings.COMPUTER_USE_TYPE_DELAY_MS)
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def scroll(self, direction: str, amount: int) -> dict:
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            dx, dy = 0, 0
            if direction == "down":
                dy = amount
            elif direction == "up":
                dy = -amount
            elif direction == "left":
                dx = -amount
            elif direction == "right":
                dx = amount
            await self._page.mouse.wheel(dx, dy)
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def wait(self, seconds: float) -> dict:
        if not self._page:
            raise RuntimeError("Browser not started")
        await self._page.wait_for_timeout(int(seconds * 1000))
        return {"success": True}

    async def press_key(self, key: str) -> dict:
        """Presiona una tecla especial (Enter, Escape, Tab, etc.)."""
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            await self._page.keyboard.press(key)
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── DOM-precise actions (high accuracy path) ────────────────────────
    async def click_selector(self, selector: str) -> dict:
        """Click por selector CSS — preciso, sin depender de coordenadas."""
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            await self._page.click(selector, timeout=settings.COMPUTER_USE_SETTLE_TIMEOUT_MS)
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click_text(self, text: str, exact: bool = False) -> dict:
        """Click sobre el primer elemento que contiene el texto dado."""
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            locator = self._page.get_by_text(text, exact=exact).first
            await locator.click(timeout=settings.COMPUTER_USE_SETTLE_TIMEOUT_MS)
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fill(self, selector: str, value: str) -> dict:
        """Rellena un input de una sola vez (más rápido que type char-a-char)."""
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            await self._page.fill(selector, value, timeout=settings.COMPUTER_USE_SETTLE_TIMEOUT_MS)
            await self._settle()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def wait_for_selector(self, selector: str, timeout_ms: Optional[int] = None) -> dict:
        """Espera a que aparezca un elemento (sincronización determinística)."""
        if not self._page:
            raise RuntimeError("Browser not started")
        try:
            await self._page.wait_for_selector(
                selector, timeout=timeout_ms or settings.COMPUTER_USE_NAV_TIMEOUT_MS
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_page_info(self) -> dict:
        """Obtiene información de la página actual."""
        if not self._page:
            raise RuntimeError("Browser not started")
        return {
            "url": self._page.url,
            "title": await self._page.title(),
        }

    async def get_interactive_elements(self, limit: int = 60) -> list[dict]:
        """Snapshot de elementos interactivos con coordenadas y etiqueta.

        Da al agente de visión un mapa estructurado (rol, texto, bbox center)
        para clicks precisos sin adivinar píxeles desde la imagen.
        """
        if not self._page:
            raise RuntimeError("Browser not started")
        js = """
        (max) => {
          const sel = 'a,button,input,textarea,select,[role=button],[role=link],[role=tab],[onclick]';
          const out = [];
          const nodes = document.querySelectorAll(sel);
          for (let i = 0; i < nodes.length && out.length < max; i++) {
            const el = nodes[i];
            const r = el.getBoundingClientRect();
            if (r.width < 4 || r.height < 4) continue;
            if (r.bottom < 0 || r.top > window.innerHeight) continue;
            const style = window.getComputedStyle(el);
            if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') continue;
            const label = (el.innerText || el.value || el.getAttribute('aria-label')
                          || el.getAttribute('placeholder') || el.name || '').trim().slice(0, 80);
            out.push({
              tag: el.tagName.toLowerCase(),
              role: el.getAttribute('role') || el.type || el.tagName.toLowerCase(),
              label: label,
              x: Math.round(r.x + r.width / 2),
              y: Math.round(r.y + r.height / 2),
              w: Math.round(r.width),
              h: Math.round(r.height),
            });
          }
          return out;
        }
        """
        try:
            return await self._page.evaluate(js, limit)
        except Exception as e:
            logger.warning(f"get_interactive_elements failed: {e}")
            return []
