"""Computer Use — Credential Manager

Gestiona credenciales seguras para auto-login durante sesiones de
Computer Use. Las contraseñas se almacenan encriptadas con Fernet.
El agente puede usar estas credenciales para loguearse automáticamente
en sitios configurados.

Now integrated with persistent DB storage via CredentialService.
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.logger import get_logger
from app.core.encryption import encrypt_value, decrypt_value

logger = get_logger(__name__)


@dataclass
class SiteCredential:
    """Credenciales para un sitio específico."""
    site_domain: str
    username: str
    password_encrypted: str
    login_url: Optional[str] = None
    username_selector: Optional[str] = None
    password_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    extra_fields: Optional[Dict[str, str]] = None


class CredentialManager:
    """Gestor de credenciales para auto-login.
    
    Falls back to in-memory storage if no DB session is provided.
    When db_session is available, uses persistent CredentialService.
    """

    def __init__(self, db_session=None, user_id=None):
        self._credentials: Dict[str, SiteCredential] = {}
        self._db = db_session
        self._user_id = user_id
        self._service = None
        if db_session and user_id:
            from app.domains.credentials.service import CredentialService
            self._service = CredentialService(db_session)

    def add_credential(self, credential: SiteCredential) -> None:
        """Agrega credenciales para un dominio."""
        domain = self._normalize_domain(credential.site_domain)
        self._credentials[domain] = credential
        logger.info(f"Credential added for {domain}")

    def get_credential(self, url: str) -> Optional[SiteCredential]:
        """Obtiene credenciales para una URL."""
        domain = self._normalize_domain(urlparse(url).hostname or "")
        
        # Try persistent storage first
        if self._service and self._user_id:
            import asyncio
            try:
                cred = asyncio.get_event_loop().run_until_complete(
                    self._service.get(self._user_id, domain)
                )
                if cred:
                    return SiteCredential(
                        site_domain=domain,
                        username=cred.get("username", ""),
                        password_encrypted=encrypt_value(cred.get("password", "")) if cred.get("password") else "",
                        login_url=url,
                    )
            except Exception as e:
                logger.debug(f"DB credential lookup failed: {e}")
        
        return self._credentials.get(domain)

    def has_credential(self, url: str) -> bool:
        """Verifica si hay credenciales para una URL."""
        return self.get_credential(url) is not None

    def _normalize_domain(self, domain: str) -> str:
        """Normaliza un dominio."""
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    async def attempt_login(self, page, url: str) -> Dict[str, Any]:
        """Attempt to log in using stored credentials."""
        domain = self._normalize_domain(urlparse(url).hostname or "")
        
        # Try persistent credentials first
        if self._service and self._user_id:
            cred = await self._service.get(self._user_id, domain)
            if cred and cred.get("username") and cred.get("password"):
                return await self._perform_login(page, url, cred["username"], cred["password"], domain)
        
        # Fall back to in-memory
        cred = self._credentials.get(domain)
        if cred and cred.username:
            password = decrypt_value(cred.password_encrypted) or ""
            return await self._perform_login(page, url, cred.username, password, domain)
        
        return {"success": False, "reason": "no_credentials"}

    async def _perform_login(self, page, url: str, username: str, password: str, domain: str) -> Dict[str, Any]:
        """Perform the actual login on the page."""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            
            # Find and fill username
            username_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[name='username']",
                "input[id='email']",
                "input[id='username']",
                "input[placeholder*='email' i]",
                "input[placeholder*='usuario' i]",
                "input[placeholder*='user' i]",
            ]
            for sel in username_selectors:
                try:
                    await page.fill(sel, username, timeout=2000)
                    break
                except Exception:
                    continue
            
            # Find and fill password
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[id='password']",
                "input[placeholder*='contraseña' i]",
                "input[placeholder*='password' i]",
            ]
            for sel in password_selectors:
                try:
                    await page.fill(sel, password, timeout=2000)
                    break
                except Exception:
                    continue
            
            # Click submit
            submit_selectors = [
                "button[type='submit']",
                "button:has-text('Log In')",
                "button:has-text('Sign In')",
                "button:has-text('Entrar')",
                "button:has-text('Iniciar')",
                "input[type='submit']",
                "[data-testid='login-button']",
            ]
            for sel in submit_selectors:
                try:
                    await page.click(sel, timeout=3000)
                    break
                except Exception:
                    continue
            
            await page.wait_for_timeout(3000)
            
            # Mark as used in DB if applicable
            if self._service and self._user_id:
                result = await self._service.db.execute(
                    __import__('sqlalchemy').select(__import__('app.domains.credentials.models', fromlist=['SiteCredential']).SiteCredential)
                    .where(
                        __import__('app.domains.credentials.models', fromlist=['SiteCredential']).SiteCredential.user_id == self._user_id,
                        __import__('app.domains.credentials.models', fromlist=['SiteCredential']).SiteCredential.domain == domain,
                    )
                )
                db_cred = result.scalar_one_or_none()
                if db_cred:
                    await self._service.mark_used(db_cred.id, success=True)
            
            return {"success": True, "domain": domain}
        except Exception as e:
            logger.error(f"Login attempt failed for {domain}: {e}")
            return {"success": False, "reason": "login_failed", "error": str(e)}
