"""Computer Use — Proxy Manager

Gestiona proxies rotativos para sesiones de Computer Use. Soporta proxies
HTTP, HTTPS y SOCKS5 con autenticación básica. Incluye rotación automática
de IP y health checks.
"""

import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timezone
from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class ProxyConfig:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"  # http, https, socks5

    def to_playwright_format(self) -> Dict[str, str]:
        """Convierte a formato de proxy de Playwright."""
        server = f"{self.proxy_type}://{self.host}:{self.port}"
        result = {"server": server}
        if self.username:
            result["username"] = self.username
        if self.password:
            result["password"] = self.password
        return result

    def to_url(self) -> str:
        """URL del proxy para logging/debug."""
        auth = ""
        if self.username:
            auth = f"{self.username}:****@"
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"


class ProxyManager:
    """Gestor de proxies para Computer Use."""

    def __init__(self):
        self._proxies: List[ProxyConfig] = []
        self._health_status: Dict[str, bool] = {}
        self._use_counts: Dict[str, int] = {}
        self._last_rotation: Dict[str, datetime] = {}

    def add_proxy(self, config: ProxyConfig) -> None:
        """Agrega un proxy al pool."""
        key = f"{config.host}:{config.port}"
        if not any(f"{p.host}:{p.port}" == key for p in self._proxies):
            self._proxies.append(config)
            self._health_status[key] = True
            self._use_counts[key] = 0
            logger.info(f"Proxy added: {config.to_url()}")

    def add_proxies_from_string(self, proxy_string: str) -> None:
        """Agrega proxies desde un string (formato: type://user:pass@host:port)."""
        # Format: http://user:pass@host:port or socks5://host:port
        import re
        pattern = r"(\w+)://(?:(\w+):(\w+)@)?([\w.-]+):(\d+)"
        for match in re.finditer(pattern, proxy_string):
            proxy_type, user, password, host, port = match.groups()
            self.add_proxy(ProxyConfig(
                host=host,
                port=int(port),
                username=user,
                password=password,
                proxy_type=proxy_type,
            ))

    def get_proxy(self, strategy: str = "round_robin") -> Optional[ProxyConfig]:
        """Obtiene un proxy según la estrategia."""
        healthy = [p for p in self._proxies if self._health_status.get(f"{p.host}:{p.port}", True)]
        if not healthy:
            return None

        if strategy == "random":
            proxy = random.choice(healthy)
        elif strategy == "least_used":
            proxy = min(healthy, key=lambda p: self._use_counts.get(f"{p.host}:{p.port}", 0))
        else:  # round_robin
            proxy = healthy[0]

        key = f"{proxy.host}:{proxy.port}"
        self._use_counts[key] = self._use_counts.get(key, 0) + 1
        self._last_rotation[key] = datetime.now(timezone.utc)

        return proxy

    def mark_unhealthy(self, host: str, port: int) -> None:
        """Marca un proxy como no saludable."""
        key = f"{host}:{port}"
        self._health_status[key] = False
        logger.warning(f"Proxy marked unhealthy: {key}")

    def mark_healthy(self, host: str, port: int) -> None:
        """Marca un proxy como saludable."""
        key = f"{host}:{port}"
        self._health_status[key] = True
        logger.info(f"Proxy marked healthy: {key}")

    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del pool de proxies."""
        total = len(self._proxies)
        healthy = sum(1 for p in self._proxies if self._health_status.get(f"{p.host}:{p.port}", True))
        return {
            "total": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "use_counts": self._use_counts.copy(),
        }

    async def health_check(self, proxy: ProxyConfig, timeout: int = 10) -> bool:
        """Realiza un health check HTTP a través del proxy."""
        import aiohttp
        try:
            proxy_url = f"{proxy.proxy_type}://{proxy.host}:{proxy.port}"
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                proxy_arg = proxy_url
                if proxy.username and proxy.password:
                    proxy_arg = f"{proxy.proxy_type}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
                async with session.get(
                    "https://httpbin.org/ip",
                    proxy=proxy_arg,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.warning(f"Proxy health check failed for {proxy.to_url()}: {e}")
            return False

    async def rotate_all(self) -> None:
        """Rota todos los proxies verificando health."""
        for proxy in self._proxies:
            is_healthy = await self.health_check(proxy)
            if is_healthy:
                self.mark_healthy(proxy.host, proxy.port)
            else:
                self.mark_unhealthy(proxy.host, proxy.port)


# Global proxy manager
_proxy_manager: Optional[ProxyManager] = None


def get_proxy_manager() -> ProxyManager:
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager
