"""
AI Social Content Generator

Generates Instagram posts, captions, and hashtag sets with one click.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User

router = APIRouter(prefix="/social-content", tags=["social-content"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/generate-post")
async def generate_post(
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Generate an Instagram post using AI."""
    topic = data.get("topic", "ventas")
    tone = data.get("tone", "profesional")
    content_type = data.get("content_type", "carousel")  # carousel | reel | story | single

    # In production, this would call the LLM provider
    # For now, return structured templates
    templates = {
        "carousel": {
            "hook": f"🚀 3 errores que te cuestan ventas en {topic}",
            "slides": [
                "Slide 1: El problema que todos cometen",
                "Slide 2: Error #1 — No seguís a tus leads",
                "Slide 3: Error #2 — Respondés después de 24hs",
                "Slide 4: Error #3 — No tenés un script de ventas",
                "Slide 5: La solución: automatización con IA",
                "Slide 6: CTA — 'Link en bio para probar gratis'",
            ],
            "caption": f"¿Sabías que el 80% de las ventas se pierden por seguimiento? 📉\n\nAcá te dejo los 3 errores más comunes en {topic} y cómo evitarlos con IA 🤖\n\n¿Cuál cometés vos? 👇\n\n#ventas #automation #ia #{topic.replace(' ', '')}",
            "hashtags": ["#ventas", "#automation", "#ia", f"#{topic}", "#emprendedores", "#marketingdigital", "#negocios", "#crecimientodigital"],
            "best_time": "Miércoles 11:00 AM o Jueves 7:00 PM",
        },
        "reel": {
            "hook": f"POV: Descubrís que la IA puede vender por vos 🔥",
            "script": [
                "0-3s: Hook visual con texto 'Esto me cambió el negocio'",
                "3-10s: Mostrar el problema (perdiendo leads)",
                "10-20s: La solución (agente IA respondiendo 24/7)",
                "20-25s: Resultados (screenshot de conversaciones)",
                "25-30s: CTA 'Link en bio'",
            ],
            "caption": f"Así es como vendo mientras duermo 😴💰\n\nMi agente IA atiende, califica y cierra ventas automáticamente.\n\n¿Querés ver cómo funciona? 👆 Link en bio\n\n#{topic.replace(' ', '')} #ia #ventasonline #automation",
            "hashtags": ["#reels", "#viral", f"#{topic}", "#ia", "#negocios"],
            "best_time": "Viernes 7:00 PM o Sábado 10:00 AM",
        },
        "story": {
            "hook": f"⚡ Tip rápido: duplicá tus ventas en 48hs",
            "frames": [
                "Frame 1: '¿Sabías que...?' + encuesta",
                "Frame 2: El dato (80% abandono)",
                "Frame 3: La solución en 1 slide",
                "Frame 4: Link sticker 'Probar gratis'",
            ],
            "caption": "Story tip 💡",
            "hashtags": [],
            "best_time": "Siempre activo",
        },
    }

    result = templates.get(content_type, templates["carousel"])

    # Store in calendar if requested
    if data.get("save_to_calendar"):
        from app.domains.social_growth.models import ContentCalendarSlot
        from datetime import datetime, timezone, timedelta
        slot = ContentCalendarSlot(
            user_id=current_user.id,
            platform="instagram",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            content_type=content_type,
            topic=topic,
            caption_draft=result["caption"],
            hashtag_suggestions=result["hashtags"],
            best_time_reason=result["best_time"],
        )
        db.add(slot)
        await db.commit()

    return {
        "content_type": content_type,
        "topic": topic,
        "tone": tone,
        "generated": result,
        "saved_to_calendar": data.get("save_to_calendar", False),
    }


@router.post("/generate-hashtags")
async def generate_hashtags(data: dict):
    """Generate hashtag sets for a topic."""
    topic = data.get("topic", "ventas")
    return {
        "high_volume": [f"#{topic}", "#emprendedores", "#negocios", "#marketingdigital", "#ventasonline"],
        "niche": [f"#{topic}conia", "#automation", "#agenteia", "#chatbot", "#crm"],
        "branded": ["#sellia", "#vendemientrasduermes", "#iasales"],
        "location_based": ["#argentina", "#latam", "#miami", "#españa"],
        "recommended_mix": [f"#{topic}", "#ia", "#automation", "#emprendedores", "#sellia", "#negociosonline"],
    }
