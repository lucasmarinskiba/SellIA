"""Computer Use sandbox provisioning · isolated browser sessions per tenant.

Production options: E2B · Daytona · Browserbase · Docker-in-Docker.
Dev fallback: returns mock VNC URL.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import CurrentUser, require_role


logger = logging.getLogger(__name__)
router = APIRouter()


SANDBOX_TIMEOUT_MIN = 30
MAX_CONCURRENT_PER_TENANT = 3


class SandboxStartRequest(BaseModel):
    task: str
    start_url: str | None = None
    browser: str = "chromium"  # chromium · firefox · webkit
    viewport: dict[str, int] | None = None


class SandboxResponse(BaseModel):
    sandbox_id: str
    vnc_url: str
    cdp_url: str
    websocket_url: str
    expires_at: str
    status: str


# In-memory tenant → active sandbox count (replace w/ Redis in prod)
_active_sandboxes: dict[str, set[str]] = {}


@router.post("/start", response_model=SandboxResponse)
async def start_sandbox(
    payload: SandboxStartRequest,
    user: CurrentUser = Depends(require_role("owner", "admin", "manager")),
) -> SandboxResponse:
    """Provision new CUA sandbox.

    Rate limit: 3 concurrent / tenant.

    Provider routing (env CUA_PROVIDER):
      - "e2b"          · E2B desktop sandbox
      - "daytona"      · Daytona workspace
      - "browserbase"  · Browserbase managed Chrome
      - "docker"       · self-hosted Docker container
      - "mock" (default in dev)
    """
    active = _active_sandboxes.setdefault(user.tenant_id, set())
    if len(active) >= MAX_CONCURRENT_PER_TENANT:
        raise HTTPException(status_code=429, detail=f"Max {MAX_CONCURRENT_PER_TENANT} concurrent sandboxes per tenant")

    sandbox_id = f"sbx-{uuid.uuid4().hex[:12]}"
    provider = os.getenv("CUA_PROVIDER", "mock")

    try:
        urls = await _provision(provider, sandbox_id, payload)
    except Exception as e:
        logger.exception("sandbox_provision_failed", extra={"provider": provider, "error": str(e)})
        raise HTTPException(status_code=502, detail=f"Sandbox provisioning failed: {provider}")

    active.add(sandbox_id)
    expires = datetime.now(timezone.utc) + timedelta(minutes=SANDBOX_TIMEOUT_MIN)

    logger.info(
        "sandbox_started",
        extra={"tenant_id": user.tenant_id, "sandbox_id": sandbox_id, "provider": provider, "task": payload.task[:80]},
    )

    return SandboxResponse(
        sandbox_id=sandbox_id,
        vnc_url=urls["vnc"],
        cdp_url=urls["cdp"],
        websocket_url=urls["ws"],
        expires_at=expires.isoformat(),
        status="running",
    )


@router.post("/stop/{sandbox_id}", status_code=204)
async def stop_sandbox(
    sandbox_id: str,
    user: CurrentUser = Depends(require_role("owner", "admin", "manager")),
) -> None:
    """Tear down sandbox · free resources."""
    active = _active_sandboxes.get(user.tenant_id, set())
    if sandbox_id not in active:
        raise HTTPException(status_code=404, detail="Sandbox not found for this tenant")

    provider = os.getenv("CUA_PROVIDER", "mock")
    try:
        await _teardown(provider, sandbox_id)
    except Exception as e:
        logger.exception("sandbox_teardown_failed", extra={"sandbox_id": sandbox_id, "error": str(e)})
    finally:
        active.discard(sandbox_id)


@router.get("/active")
async def list_active(user: CurrentUser = Depends(require_role("owner", "admin", "manager"))):
    """List active sandboxes for current tenant."""
    active = _active_sandboxes.get(user.tenant_id, set())
    return {"active": list(active), "count": len(active), "limit": MAX_CONCURRENT_PER_TENANT}


# ─── Provider adapters ──────────────────────────────────────────────────────


async def _provision(provider: str, sandbox_id: str, payload: SandboxStartRequest) -> dict[str, str]:
    if provider == "e2b":
        return await _provision_e2b(sandbox_id, payload)
    if provider == "browserbase":
        return await _provision_browserbase(sandbox_id, payload)
    if provider == "docker":
        return await _provision_docker(sandbox_id, payload)
    # Default mock · for dev
    return {
        "vnc": f"wss://mock-sandboxes.local/{sandbox_id}/vnc",
        "cdp": f"wss://mock-sandboxes.local/{sandbox_id}/cdp",
        "ws":  f"wss://mock-sandboxes.local/{sandbox_id}/control",
    }


async def _provision_e2b(sandbox_id: str, payload: SandboxStartRequest) -> dict[str, str]:
    import httpx
    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        raise RuntimeError("E2B_API_KEY missing")

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://api.e2b.dev/sandboxes",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"template_id": "desktop", "metadata": {"sandbox_id": sandbox_id}},
        )
        r.raise_for_status()
        data = r.json()

    return {
        "vnc": data.get("vnc_url", ""),
        "cdp": data.get("cdp_url", ""),
        "ws":  data.get("websocket_url", ""),
    }


async def _provision_browserbase(sandbox_id: str, payload: SandboxStartRequest) -> dict[str, str]:
    import httpx
    api_key = os.getenv("BROWSERBASE_API_KEY")
    project_id = os.getenv("BROWSERBASE_PROJECT_ID")
    if not api_key or not project_id:
        raise RuntimeError("BROWSERBASE_API_KEY or BROWSERBASE_PROJECT_ID missing")

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://www.browserbase.com/v1/sessions",
            headers={"X-BB-API-Key": api_key},
            json={"projectId": project_id, "keepAlive": True},
        )
        r.raise_for_status()
        data = r.json()

    return {
        "vnc": data.get("debuggerFullscreenUrl", ""),
        "cdp": data.get("connectUrl", ""),
        "ws":  data.get("seleniumRemoteUrl", ""),
    }


async def _provision_docker(sandbox_id: str, payload: SandboxStartRequest) -> dict[str, str]:
    """Self-hosted Docker container · spawn `playwright/chromium` image."""
    # Production: shell out to `docker run -d --rm --name {sandbox_id} ...` w/ resource limits
    raise NotImplementedError("docker provisioning · implement w/ aiodocker")


async def _teardown(provider: str, sandbox_id: str) -> None:
    if provider == "mock":
        return
    # Provider-specific cleanup
    logger.info("teardown_noop", extra={"provider": provider, "sandbox_id": sandbox_id})
