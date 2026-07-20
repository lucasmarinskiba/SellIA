"""Customer Service Auto-Agent Router"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.customer_service import service as cs_service
from app.domains.agents.customer_service.schemas import (
    CustomerMessageIn,
    CustomerMessageOut,
    ServiceBotConfigCreate,
    ServiceBotConfigUpdate,
    ServiceBotConfigOut,
    ServiceInteractionOut,
    FAQSearchIn,
    FAQSearchOut,
)

router = APIRouter(prefix="/customer-service", tags=["customer-service"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/message", response_model=CustomerMessageOut)
async def handle_message(
    data: CustomerMessageIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Handle an incoming customer message with the service bot."""
    try:
        result = await cs_service.handle_customer_message(
            db=db,
            bot_config_id=data.bot_config_id,
            customer_id=data.customer_id,
            message=data.message,
            channel=data.channel,
            conversation_id=data.conversation_id,
        )
        return CustomerMessageOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/interactions", response_model=list[ServiceInteractionOut])
async def list_interactions(
    bot_config_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """List service interactions."""
    return await cs_service.list_interactions(db, bot_config_id, limit, offset)


@router.get("/interactions/{interaction_id}", response_model=ServiceInteractionOut)
async def get_interaction(
    interaction_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a single interaction."""
    interaction = await cs_service.get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interacción no encontrada")
    return interaction


@router.post("/config", response_model=ServiceBotConfigOut, status_code=status.HTTP_201_CREATED)
async def create_or_update_config(
    data: ServiceBotConfigCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create or update service bot config for the user's business."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")

    config = await cs_service.create_or_update_config(
        db=db,
        business_id=business.id,
        data=data.model_dump(),
    )
    return config


@router.patch("/config/{config_id}", response_model=ServiceBotConfigOut)
async def update_config(
    config_id: UUID,
    data: ServiceBotConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update an existing service bot config."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")

    config = await cs_service.create_or_update_config(
        db=db,
        business_id=business.id,
        data=data.model_dump(exclude_unset=True),
        config_id=config_id,
    )
    return config


@router.get("/config", response_model=ServiceBotConfigOut)
async def get_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get active service bot config for the user's business."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")

    config = await cs_service.get_config_by_business(db, business.id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuración no encontrada")
    return config


@router.post("/faq", response_model=FAQSearchOut)
async def search_faq(
    data: FAQSearchIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Semantic search over business FAQ/documents."""
    result = await cs_service.get_faq_answer(db, data.business_id, data.query)
    return FAQSearchOut(**result)
