"""OAuth Connectors for Mercado Libre, Amazon, Hotmart."""

import httpx
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_integration import PlatformCredential
from app.core.config import get_settings

settings = get_settings()


class MercadoLibreOAuth:
    """Mercado Libre OAuth2 connector."""

    AUTH_URL = "https://auth.mercadolibre.com.ar/authorization"
    TOKEN_URL = "https://api.mercadolibre.com/oauth/token"

    @classmethod
    def get_auth_url(cls) -> str:
        """Generate authorization URL for user."""
        return (
            f"{cls.AUTH_URL}?"
            f"response_type=code&"
            f"client_id={settings.MERCADO_LIBRE_CLIENT_ID}&"
            f"redirect_uri={settings.MERCADO_LIBRE_REDIRECT_URI}"
        )

    @classmethod
    async def exchange_code(cls, code: str) -> dict:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cls.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.MERCADO_LIBRE_CLIENT_ID,
                    "client_secret": settings.MERCADO_LIBRE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.MERCADO_LIBRE_REDIRECT_URI,
                },
            )
            return response.json()

    @classmethod
    async def refresh_token(cls, refresh_token: str) -> dict:
        """Refresh access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cls.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": settings.MERCADO_LIBRE_CLIENT_ID,
                    "client_secret": settings.MERCADO_LIBRE_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                },
            )
            return response.json()

    @classmethod
    async def get_seller_info(cls, access_token: str) -> dict:
        """Get authenticated seller info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.mercadolibre.com/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response.json()


class AmazonSPAPI:
    """Amazon Selling Partner API connector."""

    TOKEN_URL = "https://api.amazon.com/auth/o2/token"
    RESTRICTED_DATA_TOKEN_URL = "https://sellingpartnerapi-na.amazon.com/tokens/2021-03-01/restrictedDataToken"

    @classmethod
    async def exchange_code(cls, code: str) -> dict:
        """Exchange authorization code for refresh token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cls.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.AMAZON_CLIENT_ID,
                    "client_secret": settings.AMAZON_CLIENT_SECRET,
                    "code": code,
                },
            )
            return response.json()

    @classmethod
    async def get_seller_info(cls, access_token: str) -> dict:
        """Get seller merchant ID."""
        # Simplified — actual implementation needs LWA + SP-API signature
        return {"merchant_id": "placeholder"}


class HotmartOAuth:
    """Hotmart OAuth2 connector."""

    AUTH_URL = "https://app.hotmart.com/oauth/authorize"
    TOKEN_URL = "https://app.hotmart.com/oauth/token"

    @classmethod
    def get_auth_url(cls) -> str:
        """Generate authorization URL."""
        return (
            f"{cls.AUTH_URL}?"
            f"response_type=code&"
            f"client_id={settings.HOTMART_CLIENT_ID}&"
            f"redirect_uri={settings.HOTMART_REDIRECT_URI}&"
            f"scope=account%20products"
        )

    @classmethod
    async def exchange_code(cls, code: str) -> dict:
        """Exchange code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cls.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.HOTMART_CLIENT_ID,
                    "client_secret": settings.HOTMART_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.HOTMART_REDIRECT_URI,
                },
            )
            return response.json()

    @classmethod
    async def get_seller_info(cls, access_token: str) -> dict:
        """Get authenticated seller info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://app.hotmart.com/api/v1/account/info",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response.json()


async def store_platform_credential(
    db: AsyncSession,
    seller_id: str,
    platform: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    seller_username: Optional[str] = None,
    token_expiry_minutes: int = 3600,
) -> PlatformCredential:
    """Store platform OAuth credential in database."""
    token_expiry = datetime.utcnow() + timedelta(minutes=token_expiry_minutes)

    cred = PlatformCredential(
        seller_id=seller_id,
        platform=platform,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=token_expiry,
        seller_username=seller_username,
        is_active=True,
    )
    db.add(cred)
    await db.commit()
    await db.refresh(cred)
    return cred


async def get_platform_credential(
    db: AsyncSession,
    seller_id: str,
    platform: str,
) -> Optional[PlatformCredential]:
    """Retrieve platform credential."""
    stmt = select(PlatformCredential).where(
        PlatformCredential.seller_id == seller_id,
        PlatformCredential.platform == platform,
        PlatformCredential.is_active == True,
    )
    result = await db.execute(stmt)
    return result.scalars().first()
