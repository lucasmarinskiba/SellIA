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
        category=item_in.category,
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


@router.post("/debug/add-listing-columns", tags=["debug"])
async def debug_add_listing_columns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Temporary: force-apply the catalog_items schema patch (category,
    source_platform, external_id + the dedup unique constraint) immediately.

    schema_bootstrap.py only creates tables that don't exist yet -- it never
    ALTERs one that's already there, so these new columns need this same
    superuser-gated one-shot pattern already used for businesses.type/.config
    (backend/app/api/v1/businesses.py). Call once after deploy.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")
    from sqlalchemy import text
    try:
        await db.execute(text("ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS category VARCHAR(120)"))
        await db.execute(text("ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS source_platform VARCHAR(50)"))
        await db.execute(text("ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS external_id VARCHAR(255)"))
        await db.execute(text("ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS listing_url VARCHAR(1024)"))
        await db.execute(text(
            "ALTER TABLE catalog_items ADD CONSTRAINT uq_catalog_item_external "
            "UNIQUE (business_id, source_platform, external_id)"
        ))
        await db.commit()
        return {"status": "ok"}
    except Exception as e:
        await db.rollback()
        return {"status": "error", "error": str(e)}


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

    original_description = item.description
    item.description = enhanced.strip()
    if not item.extra_data:
        item.extra_data = {}
    item.extra_data["description_enhanced_at"] = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    item.extra_data["original_description"] = original_description
    await db.commit()
    await db.refresh(item)
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")
    return item


@router.post("/{business_id}/items/{item_id}/seo-optimize", response_model=CatalogItemResponse)
async def seo_optimize_catalog_item(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate real per-item SEO: an optimized title, a meta description,
    and a schema.org Product/Service JSON-LD block. The only SEO that
    existed before this was site-level (backend/app/api/v1/seo.py) -- this
    is the first that touches an individual listing.

    Never fabricates reviews, ratings, or any field the item doesn't
    actually have.
    """
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

    item_type = item.type.value if hasattr(item.type, "value") else item.type
    platform_hint = (
        f"El título debe seguir las convenciones de búsqueda de {item.source_platform} "
        f"(no un <title> de sitio web genérico)."
        if item.source_platform else
        "No está publicado en ninguna plataforma externa todavía -- generá un título para SEO de sitio web propio."
    )

    system_prompt = """Sos un especialista en SEO de e-commerce. Respondé SOLO con un objeto JSON
en este formato exacto:
{"title": "...", "meta_description": "..."}

Reglas:
- title: 50-60 caracteres, con la keyword principal al inicio.
- meta_description: 120-160 caracteres, resume el valor real del ítem, sin inventar datos.
- No inventes reseñas, calificaciones, ofertas ni ningún dato que no se te haya dado.
- Respondé SOLO el JSON, sin markdown ni explicaciones."""

    user_prompt = f"""NOMBRE: {item.name}
TIPO: {item_type}
CATEGORÍA: {item.category or 'sin especificar'}
PRECIO: {item.currency} {item.price}
DESCRIPCIÓN: {item.description or 'sin descripción'}
{platform_hint}"""

    import json as _json

    raw = await generate_raw_ai_response(
        db=db, business_id=business_id, system_prompt=system_prompt,
        user_prompt=user_prompt, max_tokens=200, temperature=0.4,
    )
    if not raw:
        raise HTTPException(status_code=500, detail="No se pudo generar el SEO")

    try:
        parsed = _json.loads(raw.strip())
        title = str(parsed.get("title", item.name))[:70]
        meta_description = str(parsed.get("meta_description", ""))[:170]
    except Exception:
        title, meta_description = item.name, (item.description or "")[:160]

    schema_type = "Service" if item_type == "service" else "Product"
    schema_json: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": item.name,
        "description": item.description or "",
    }
    if schema_type == "Product":
        schema_json["offers"] = {
            "@type": "Offer",
            "price": str(item.price),
            "priceCurrency": item.currency,
            "availability": "https://schema.org/InStock" if item.is_available else "https://schema.org/OutOfStock",
        }
    else:
        schema_json["offers"] = {
            "@type": "Offer",
            "price": str(item.price),
            "priceCurrency": item.currency,
        }

    if not item.extra_data:
        item.extra_data = {}
    item.extra_data["seo"] = {
        "title": title,
        "meta_description": meta_description,
        "schema_json": schema_json,
        "generated_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
    }
    await db.commit()
    await db.refresh(item)
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")
    return item


@router.post("/{business_id}/items/{item_id}/fomo-generate", response_model=CatalogItemResponse)
async def fomo_generate_catalog_item(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate urgency/value copy for one listing, grounded only in real
    data (price, real stock if any, availability). This codebase already
    had a "1234 vistas" fake-stats incident fixed on this exact page
    (dashboard/listings) -- the prompt here explicitly forbids inventing
    view/purchase counts, and `angle` tells the frontend whether the copy
    is backed by real scarcity (low real stock) or is value-oriented
    (no real scarcity signal), so the UI never shows a fabricated urgency
    claim as if it were a fact.
    """
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

    has_real_scarcity = item.stock is not None and item.stock <= 5
    angle = "scarcity" if has_real_scarcity else "value"

    system_prompt = """Sos un copywriter de e-commerce. Respondé SOLO con un objeto JSON
en este formato exacto:
{"headline": "..."}

Reglas CRÍTICAS:
- NUNCA inventes cifras de vistas, compras, calificaciones ni stock que no se te dieron explícitamente.
- Si te dan un stock real bajo, podés mencionarlo tal cual (ej. "Quedan 3 unidades").
- Si NO hay señal real de escasez, el copy tiene que vender por VALOR/beneficio, sin fabricar urgencia falsa.
- headline: máximo 90 caracteres, en español, directo.
- Respondé SOLO el JSON, sin markdown ni explicaciones."""

    stock_line = f"STOCK REAL: {item.stock} unidades" if item.stock is not None else "STOCK: no aplica / sin dato real"
    user_prompt = f"""NOMBRE: {item.name}
TIPO: {item.type.value if hasattr(item.type, 'value') else item.type}
PRECIO: {item.currency} {item.price}
DISPONIBLE: {'sí' if item.is_available else 'no'}
{stock_line}
ÁNGULO A USAR: {'escasez real (stock bajo real)' if angle == 'scarcity' else 'valor/beneficio, sin inventar urgencia'}"""

    import json as _json

    raw = await generate_raw_ai_response(
        db=db, business_id=business_id, system_prompt=system_prompt,
        user_prompt=user_prompt, max_tokens=100, temperature=0.6,
    )
    if not raw:
        raise HTTPException(status_code=500, detail="No se pudo generar el copy de FOMO")

    try:
        parsed = _json.loads(raw.strip())
        headline = str(parsed.get("headline", ""))[:120]
    except Exception:
        headline = raw.strip()[:120]

    if not item.extra_data:
        item.extra_data = {}
    item.extra_data["fomo"] = {
        "headline": headline,
        "angle": angle,
        "generated_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
    }
    await db.commit()
    await db.refresh(item)
    await invalidate_cache_pattern(f"catalog:*:{business_id}:*")
    return item
