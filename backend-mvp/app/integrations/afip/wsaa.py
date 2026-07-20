"""AFIP WSAA · Web Service Authentication Agent.

Flow:
  1. Generate Login Ticket Request (TRA) XML w/ unique generationTime/uniqueId
  2. Sign w/ tenant's certificate + private key (PKCS7-DER → CMS)
  3. POST to WSAAUrl (homo/prod)
  4. Receive Token + Sign (TA) · cache 12h in Redis

Token reused across calls to WSFE (factura electrónica).
Cert + key per tenant stored encrypted in tenant.settings.afip_cert / afip_key.
"""
import asyncio
import base64
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from xml.etree import ElementTree as ET

import httpx
import redis.asyncio as aioredis

from app.core.config import settings


logger = logging.getLogger(__name__)


WSAA_URL_HOMO = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
WSAA_URL_PROD = "https://wsaa.afip.gov.ar/ws/services/LoginCms"
TOKEN_TTL_SEC = 11 * 3600  # AFIP TA valid 12h · refresh 1h early


@dataclass
class AFIPTokenAuth:
    """Result of WSAA login. Use Token + Sign + CUIT for WSFE calls."""
    token: str
    sign: str
    expires_at: int  # unix ts
    cuit: str

    def is_valid(self) -> bool:
        return self.expires_at - int(time.time()) > 300  # 5min buffer


class AFIPClient:
    """Per-tenant AFIP client. Caches TA in Redis to avoid 1-req/10sec WSAA limit."""

    def __init__(
        self,
        cuit: str,
        cert_pem: str,
        key_pem: str,
        *,
        service: str = "wsfe",
        production: bool = False,
        redis_url: str | None = None,
    ):
        self.cuit = cuit
        self.cert_pem = cert_pem
        self.key_pem = key_pem
        self.service = service
        self.wsaa_url = WSAA_URL_PROD if production else WSAA_URL_HOMO
        self._redis_url = redis_url or settings.REDIS_URL
        self._redis: aioredis.Redis | None = None

    async def _r(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def _cache_key(self) -> str:
        return f"afip:ta:{self.cuit}:{self.service}"

    async def get_auth(self) -> AFIPTokenAuth:
        """Return cached TA or fetch new one via WSAA login."""
        r = await self._r()
        cached = await r.get(self._cache_key())
        if cached:
            import json
            data = json.loads(cached)
            ta = AFIPTokenAuth(**data)
            if ta.is_valid():
                return ta

        ta = await self._wsaa_login()
        import json
        await r.setex(self._cache_key(), TOKEN_TTL_SEC, json.dumps(ta.__dict__))
        return ta

    async def _wsaa_login(self) -> AFIPTokenAuth:
        """Build TRA · sign · POST to WSAA · parse TA."""
        tra = self._build_tra()
        cms = self._sign_pkcs7(tra)
        cms_b64 = base64.b64encode(cms).decode()

        envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsaa="http://wsaa.view.sua.dvadac.desein.afip.gov">
  <soapenv:Header/>
  <soapenv:Body>
    <wsaa:loginCms>
      <wsaa:in0>{cms_b64}</wsaa:in0>
    </wsaa:loginCms>
  </soapenv:Body>
</soapenv:Envelope>"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.wsaa_url,
                content=envelope,
                headers={"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": ""},
            )
            resp.raise_for_status()

        # Parse response · extract inner XML w/ Token + Sign
        return self._parse_login_response(resp.text)

    def _build_tra(self) -> str:
        """Login Ticket Request · unique per attempt (AFIP rejects repeats within 24h)."""
        now = datetime.now(timezone.utc)
        gen = now.strftime("%Y-%m-%dT%H:%M:%S-00:00")
        exp = (now + timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%S-00:00")
        unique = str(int(now.timestamp()))
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
  <header>
    <uniqueId>{unique}</uniqueId>
    <generationTime>{gen}</generationTime>
    <expirationTime>{exp}</expirationTime>
  </header>
  <service>{self.service}</service>
</loginTicketRequest>"""

    def _sign_pkcs7(self, data: str) -> bytes:
        """Sign data with cert + key using PKCS7/CMS detached signature.

        Requires `cryptography` lib (not pinned · install on tenants needing AFIP).
        """
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.serialization import pkcs7
            from cryptography.x509 import load_pem_x509_certificate
        except ImportError as e:
            raise RuntimeError("`cryptography` package required for AFIP signing") from e

        cert = load_pem_x509_certificate(self.cert_pem.encode())
        key = serialization.load_pem_private_key(self.key_pem.encode(), password=None)

        signer = (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(data.encode())
            .add_signer(cert, key, hashes.SHA256())
        )
        return signer.sign(
            encoding=serialization.Encoding.DER,
            options=[],
        )

    def _parse_login_response(self, soap_xml: str) -> AFIPTokenAuth:
        """Parse SOAP envelope → loginCmsReturn XML → Token+Sign."""
        # Strip soap envelope · extract loginCmsReturn payload
        soap = ET.fromstring(soap_xml)
        ns = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}
        return_node = soap.find(".//loginCmsReturn") or soap.find(".//{*}loginCmsReturn")
        if return_node is None or not return_node.text:
            raise RuntimeError(f"WSAA response missing loginCmsReturn: {soap_xml[:400]}")

        # The text is inner XML (escaped) · parse it
        inner = ET.fromstring(return_node.text)
        token_el = inner.find(".//token")
        sign_el = inner.find(".//sign")
        expiry_el = inner.find(".//expirationTime")

        if token_el is None or sign_el is None:
            raise RuntimeError("WSAA inner XML missing token/sign")

        # expirationTime is ISO8601 · convert to unix
        expires_at = int(time.time()) + TOKEN_TTL_SEC
        if expiry_el is not None and expiry_el.text:
            try:
                expires_at = int(datetime.fromisoformat(expiry_el.text.replace("Z", "+00:00")).timestamp())
            except ValueError:
                pass

        return AFIPTokenAuth(
            token=token_el.text or "",
            sign=sign_el.text or "",
            expires_at=expires_at,
            cuit=self.cuit,
        )
