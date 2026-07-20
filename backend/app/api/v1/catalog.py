from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Any

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.cache import cached, invalidate_cache_pattern
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.catalogs.models import CatalogItem
from app.domains.catalogs.schemas import CatalogItemCreate, CatalogItemUpdate, CatalogItemResponse

router = APIRouter()


async def _get_business_for_user(
    business_id: UUID, user: User, db: AsyncSession
) -> Business:
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == user.id,
            Business.is_active == True,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.post("/{business_id}/items", response_model=CatalogItemResponse, status_code=status.HTTP_201_CREATED)
async def create_catalog_item(
    business_id: UUID,
    item_in: CatalogItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)

    item = CatalogItem(
        business_id=business_id,
        type=item_in.type,
        name=item_in.name,
        description=item_in.description,
        price=item_in.price,
        currency=item_in.currency,
        stock=item_in.stock,
        is_available=item_in.is_available,
        extra_data=item_in.extra_data or {},
        images=item_in.images,
        tags=item_in.tags,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")
    return item


@router.post("/{business_id}/catalog/sync-push")
async def sync_catalog_push(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Push local catalog items to all connected external platforms."""
    await _get_business_for_user(business_id, current_user, db)

    from app.domains.catalogs.sync_service import CatalogSyncService
    sync_service = CatalogSyncService(db)
    results = await sync_service.push_all(business_id)
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")

    return {
        "results": [
            {
                "platform": r.platform,
                "success": r.success,
                "message": r.message,
                "items_synced": r.items_synced,
                "synced_at": r.synced_at.isoformat(),
            }
            for r in results
        ]
    }


@router.post("/{business_id}/catalog/sync-pull")
async def sync_catalog_pull(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pull products from all connected external platforms into local catalog."""
    await _get_business_for_user(business_id, current_user, db)

    from app.domains.catalogs.sync_service import CatalogSyncService
    sync_service = CatalogSyncService(db)
    results = await sync_service.pull_all(business_id)
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")

    return {
        "results": [
            {
                "platform": r.platform,
                "success": r.success,
                "message": r.message,
                "items_synced": r.items_synced,
                "synced_at": r.synced_at.isoformat(),
            }
            for r in results
        ]
    }


@cached(ttl_seconds=300, key_prefix="catalog")
@router.get("/{business_id}/items", response_model=list[CatalogItemResponse])
async def list_catalog_items(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.business_id == business_id,
            CatalogItem.is_active == True,
        )
    )
    return result.scalars().all()


@cached(ttl_seconds=300, key_prefix="catalog")
@router.get("/{business_id}/items/{item_id}", response_model=CatalogItemResponse)
async def get_catalog_item(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.id == item_id,
            CatalogItem.business_id == business_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return item


@router.put("/{business_id}/items/{item_id}", response_model=CatalogItemResponse)
async def update_catalog_item(
    business_id: UUID,
    item_id: UUID,
    item_in: CatalogItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.id == item_id,
            CatalogItem.business_id == business_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    update_data = item_in.model_dump(exclude_unset=True)
    if "extra_data" in update_data and item.extra_data:
        update_data["extra_data"] = {**item.extra_data, **update_data["extra_data"]}

    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")
    return item


@router.delete("/{business_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog_item(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.id == item_id,
            CatalogItem.business_id == business_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    item.is_active = False
    await db.commit()
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")
    return None


@router.post("/{business_id}/items/{item_id}/enhance-description", response_model=CatalogItemResponse)
async def enhance_catalog_description(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Use AI to enhance a catalog item's description for better sales conversion."""
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.id == item_id,
            CatalogItem.business_id == business_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    from app.domains.agents.ai_reply import generate_raw_ai_response
    from app.domains.agents.prompts import compose_system_prompt

    system_prompt = compose_system_prompt(
        base_slug="copywriter",
        voice_slug="hormozi",
    )

    user_prompt = f"""Mejora esta descripción de producto/servicio para maximizar conversiones.

NOMBRE: {item.name}
PRECIO: ${item.price} {item.currency}
TIPO: {item.type.value if hasattr(item.type, 'value') else item.type}
DESCRIPCIÓN ACTUAL: {item.description or 'Sin descripción'}

Genera una descripción mejorada que:
- Enfatice beneficios, no solo características
- Cree urgencia sutil
- Incluya un CTA implícito
- Sea de 2-4 oraciones

Responde SOLO con la descripción mejorada, sin explicaciones."""

    enhanced = await generate_raw_ai_response(
        db=db,
        business_id=business_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=300,
        temperature=0.7,
    )

    if not enhanced:
        raise HTTPException(status_code=500, detail="No se pudo generar la descripción mejorada")

    item.description = enhanced.strip()
    if not item.extra_data:
        item.extra_data = {}
    item.extra_data["description_enhanced_at"] = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    item.extra_data["original_description"] = item.description
    await db.commit()
    await db.refresh(item)
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")
    return item
