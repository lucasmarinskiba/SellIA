"""Integrations API — what is really configured on this deployment."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.domains.users.models import User

from . import registry

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/status")
async def integrations_status(_: User = Depends(get_current_user)) -> dict[str, Any]:
    """Which external APIs each tool needs and which are actually set here.

    Authenticated because it maps this deployment's configuration surface;
    it reports presence only, never a key's value.
    """
    return registry.status()
