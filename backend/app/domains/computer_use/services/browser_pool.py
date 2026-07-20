"""Computer Use — Browser Pool Manager

Gestiona múltiples instancias de navegador simultáneas (Chrome, Firefox, WebKit)
con un pool reutilizable. Permite ejecutar sesiones en paralelo con diferentes
configuraciones de navegador.
"""

import asyncio
import json
import os
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from uuid import UUID

from PIL import Image
import io

from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class BrowserInstance:
    """Una instancia de navegador del pool."""
    instance_id: str
    browser_type: str  # chromium, firefox, webkit
    browser: Any
    context: Any
    page: Any
    playwright: Any
    in_use: bool = False
    session_id: Optional[str] = None
    profile: Optional[dict] = None


class BrowserPoolManager:
    """Pool de navegadores reutilizables para Computer Use."""

    def __init__(self, max_instances: int = 6):
        self.max_instances = max_instances
        self._instances: Dict[str, BrowserInstance] = {}
        self._playwright = None
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_instances)

    async def _get_playwright(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        return self._playwright

    async def create_instance(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        profile: Optional[dict] = None,
        proxy: Optional[dict] = None,
    ) -> BrowserInstance:
        """Crea una nueva instancia de navegador."""
        async with self._lock:
            # Check pool capacity
            available = sum(1 for i in self._instances.values() if not i.in_use)
            if available == 0 and len(self._instances) >= self.max_instances:
                raise RuntimeError(f"Pool lleno: {self.max_instances} instancias máximas")

            playwright = await self._get_playwright()

            # Launch browser
            if browser_type == "firefox":
                launcher = playwright.firefox
            elif browser_type == "webkit":
                launcher = playwright.webkit
            else:
                launcher = playwright.chromium

            launch_args = {
                "headless": headless,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            }
            if proxy:
                launch_args["proxy"] = proxy

            browser = await launcher.launch(**launch_args)

            # Context with profile settings
            context_args = {
                "viewport": {
                    "width": profile.get("viewport_width", 1280) if profile else 1280,
                    "height": profile.get("viewport_height", 720) if profile else 720,
                },
                "locale": profile.get("locale", "es-ES") if profile else "es-ES",
                "timezone_id": profile.get("timezone_id", "America/Argentina/Buenos_Aires") if profile else "America/Argentina/Buenos_Aires",
            }
            if profile and profile.get("user_agent"):
                context_args["user_agent"] = profile["user_agent"]
            if profile and profile.get("geolocation"):
                context_args["geolocation"] = profile["geolocation"]
                context_args["permissions"] = ["geolocation"]

            context = await browser.new_context(**context_args)

            # Set cookies and localStorage if profile provided
            if profile:
                if profile.get("cookies"):
                    await context.add_cookies(profile["cookies"])

            page = await context.new_page()

            # Inject localStorage
            if profile and profile.get("local_storage"):
                for key, value in profile["local_storage"].items():
                    await page.evaluate(f"""localStorage.setItem({json.dumps(key)}, {json.dumps(value)});""")

            instance_id = f"{browser_type}_{os.urandom(4).hex()}"
            instance = BrowserInstance(
                instance_id=instance_id,
                browser_type=browser_type,
                browser=browser,
                context=context,
                page=page,
                playwright=playwright,
                in_use=True,
                profile=profile,
            )
            self._instances[instance_id] = instance
            logger.info(f"BrowserPool: created {browser_type} instance {instance_id}")
            return instance

    async def acquire_instance(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        profile: Optional[dict] = None,
        proxy: Optional[dict] = None,
    ) -> BrowserInstance:
        """Adquiere una instancia del pool (reutiliza si hay disponibles)."""
        async with self._semaphore:
            async with self._lock:
                # Try to reuse an available instance of the same type
                for inst in self._instances.values():
                    if not inst.in_use and inst.browser_type == browser_type:
                        inst.in_use = True
                        logger.info(f"BrowserPool: reused instance {inst.instance_id}")
                        return inst

            # Create new instance
            return await self.create_instance(browser_type, headless, profile, proxy)

    async def release_instance(self, instance_id: str, recycle: bool = True):
        """Libera una instancia del pool."""
        async with self._lock:
            instance = self._instances.get(instance_id)
            if not instance:
                return

            if recycle:
                # Clear state for reuse
                try:
                    await instance.context.clear_cookies()
                    await instance.page.goto("about:blank")
                    instance.in_use = False
                    instance.session_id = None
                    logger.info(f"BrowserPool: recycled instance {instance_id}")
                except Exception as e:
                    logger.warning(f"BrowserPool: failed to recycle {instance_id}: {e}")
                    await self._destroy_instance(instance_id)
            else:
                await self._destroy_instance(instance_id)

    async def _destroy_instance(self, instance_id: str):
        """Destruye una instancia permanentemente."""
        instance = self._instances.pop(instance_id, None)
        if not instance:
            return
        try:
            await instance.context.close()
            await instance.browser.close()
            logger.info(f"BrowserPool: destroyed instance {instance_id}")
        except Exception as e:
            logger.warning(f"BrowserPool: error destroying {instance_id}: {e}")

    async def get_instance_for_session(self, session_id: str) -> Optional[BrowserInstance]:
        """Obtiene la instancia asociada a una sesión."""
        for inst in self._instances.values():
            if inst.session_id == session_id:
                return inst
        return None

    async def attach_session(self, instance_id: str, session_id: str):
        """Asocia una instancia a una sesión."""
        async with self._lock:
            instance = self._instances.get(instance_id)
            if instance:
                instance.session_id = session_id

    async def shutdown(self):
        """Cierra todas las instancias del pool."""
        async with self._lock:
            for instance_id in list(self._instances.keys()):
                await self._destroy_instance(instance_id)
            self._instances.clear()
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("BrowserPool: shutdown complete")

    def get_stats(self) -> dict:
        """Estadísticas del pool."""
        total = len(self._instances)
        in_use = sum(1 for i in self._instances.values() if i.in_use)
        by_type = {}
        for i in self._instances.values():
            by_type[i.browser_type] = by_type.get(i.browser_type, 0) + 1
        return {
            "total_instances": total,
            "in_use": in_use,
            "available": total - in_use,
            "max": self.max_instances,
            "by_type": by_type,
        }


# Global pool instance
_pool_manager: Optional[BrowserPoolManager] = None


def get_browser_pool() -> BrowserPoolManager:
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = BrowserPoolManager()
    return _pool_manager


async def shutdown_browser_pool():
    global _pool_manager
    if _pool_manager:
        await _pool_manager.shutdown()
        _pool_manager = None
