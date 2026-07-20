"""
Diagnostics API Router

Exposes automated diagnostic endpoints for the Self-Service Hub.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.diagnostics import service as diag_service
from app.domains.diagnostics.schemas import DiagnosticRunCreate, DiagnosticRunOut

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/run", response_model=DiagnosticRunOut, status_code=200)
async def run_diagnostic(
    data: DiagnosticRunCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Run an automated diagnostic for the current user."""
    run = await diag_service.run_diagnostic(
        db=db,
        user_id=current_user.id,
        diagnostic_type=data.diagnostic_type,
    )
    return run


@router.get("/history", response_model=list[DiagnosticRunOut])
async def list_diagnostics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
):
    """List recent diagnostic runs for the current user."""
    from sqlalchemy import select, desc
    from app.domains.diagnostics.models import DiagnosticRun
    result = await db.execute(
        select(DiagnosticRun)
        .where(DiagnosticRun.user_id == current_user.id)
        .order_by(desc(DiagnosticRun.created_at))
        .limit(limit)
    )
    return result.scalars().all()
