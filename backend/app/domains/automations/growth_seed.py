"""Growth Automation Seeds — Pre-built workflows for organic customer acquisition.

Implements the "vender sin vender" philosophy through automated:
- Lead magnet delivery
- Educational nurturing sequences
- Post-purchase review collection
- UGC requests
- Referral activation
- Comment auto-reply
- SEO content generation
- Cold lead warming
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.automations.models import (
    Workflow, WorkflowTriggerType, WorkflowActionType, WorkflowStatus,
)


async def get_or_create_workflow(db: AsyncSession, business_id: uuid.UUID, name: str, **defaults) -> Workflow:
    result = await db.execute(
        select(Workflow).where(Workflow.business_id == business_id, Workflow.name == name)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        wf = Workflow(business_id=business_id, name=name, **defaults)
        db.add(wf)
        await db.flush()
    return wf


async def seed_growth_automations(db: AsyncSession, business_id: uuid.UUID):
    """Seed a complete organic growth automation stack for a business."""

    growth_workflows = [
        {
            "name": "🧲 Lead Magnet: Bienvenida + Entrega",
            "description": "Cuando llega un nuevo lead orgánico, entrega automáticamente el lead magnet activo y comienza nurturing.",
            "trigger_type": WorkflowTriggerType.NEW_LEAD,
            "trigger_config": {"channel": "any", "source": "organic"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "captador",
                    "message": "Send a warm welcome to a new organic lead. Thank them for their interest, deliver the lead magnet with enthusiasm, and ask ONE discovery question to start a conversation. Keep it under 100 words."
                }},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "organic_lead"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 24}},
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "captador",
                    "message": "Follow up with the lead who downloaded the lead magnet. Share ONE quick tip related to the lead magnet topic. Ask if they found it useful. NO sales pitch."
                }},
            ],
            "status": WorkflowStatus.DRAFT,
            "is_active": True,
        },
        {
            "name": "📚 Secuencia Educativa: 3 Toques de Valor",
            "description": "Enrolla leads fríos en una secuencia de 3 mensajes educativos sin CTA de venta (Jab-Jab-Jab-Right-Hook).",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "cold_lead_nurture"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "captador",
                    "message": "Send VALUE BOMB #1: An educational tip or insight that solves a small problem for the lead. NO product mention. NO sales pitch. Pure value. 80-120 words."
                }},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 48}},
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "captador",
                    "message": "Send VALUE BOMB #2: A practical how-to or step-by-step that the lead can apply today. Include a mini checklist. NO product mention. NO sales pitch. 80-120 words."
                }},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 72}},
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "vendedor",
                    "message": "Send SOFT RIGHT HOOK: After 2 value bombs, offer a free consultation, demo, or assessment. Frame it as 'I'd love to help you implement this' — NOT 'buy my product'. 80-100 words."
                }},
                {"type": WorkflowActionType.UPDATE_SCORE, "config": {"points": 15}},
            ],
            "status": WorkflowStatus.DRAFT,
            "is_active": True,
        },
        {
            "name": "⭐ Review Automática Post-Compra",
            "description": "3 días después de una orden completada, solicita review automáticamente.",
            "trigger_type": WorkflowTriggerType.REVENUE_EVENT,
            "trigger_config": {"event_type": "order_completed", "delay_hours": 72},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"hours": 72}},
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "post-venta",
                    "message": "Send a warm, grateful review request. Thank the customer sincerely. Ask for a quick review (stars 1-5 + one sentence). Mention how much it helps other customers decide. NO incentive mentioned. 60-80 words."
                }},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "review_requested"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 120}},
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "post-venta",
                    "message": "Gentle follow-up for review request. ONLY if they haven't responded. Remind them briefly how much their feedback matters. Very soft, no pressure. 40-60 words."
                }},
            ],
            "status": WorkflowStatus.DRAFT,
            "is_active": True,
        },
        {
            "name": "🎁 Solicitud de UGC Post-Entrega",
            "description": "7 días después de entrega, solicita foto/video del cliente usando el producto.",
            "trigger_type": WorkflowTriggerType.REVENUE_EVENT,
            "trigger_config": {"event_type": "order_delivered", "delay_hours": 168},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"hours": 168}},
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "post-venta",
                    "message": "Send a friendly UGC request. Ask the customer to share a photo or video using the product. Make it sound like a fun challenge, not a corporate request. Mention they'll be featured (with permission). 70-90 words."
                }},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ugc_requested"}},
            ],
            "status": WorkflowStatus.DRAFT,
            "is_active": True,
        },
        {
            "name": "🔗 Activación de Referido Post-Satisfacción",
            "description": "Cuando un cliente deja review positiva (4-5 estrellas), genera código de referido y envía mensaje de share.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "positive_review_given"},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"hours": 24}},
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "post-venta",
                    "message": "Send a referral activation message to a happy customer. Thank them for their review. Introduce the referral program naturally: 'Since you loved it, maybe you know someone who needs this too?' Include their unique referral code. 80-100 words."
                }},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "referral_activated"}},
            ],
            "status": WorkflowStatus.DRAFT,
            "is_active": True,
        },
        {
            "name": "💬 Auto-Reply a Comentarios de Valor",
            "description": "Cuando alguien comenta palabras clave en redes, responde con valor y mueve a DM.",
            "trigger_type": WorkflowTriggerType.NEW_MESSAGE,
            "trigger_config": {"channel": "instagram", "keywords": ["tips", "consejos", "ayuda", "cómo", "como", "tutorial", "gratis", "free", "guía", "guia"]},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "ig-dm-closer",
                    "message": "Reply to a comment asking for tips/help. Give a mini value bomb RIGHT IN THE COMMENT (1-2 sentences). Then say 'Te mandé un DM con más detalles 👆' to move them to DMs."
                }},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "comment_value_lead"}},
            ],
            "status": WorkflowStatus.DRAFT,
            "is_active": True,
        },
        {
            "name": "🔍 SEO Content: Auto-Generación Semanal",
            "description": "Genera automáticamente un artículo SEO cada semana y lo programa en el ContentCalendar.",
            "trigger_type": WorkflowTriggerType.TIME_DELAY,
            "trigger_config": {"cron": "0 6 * * 1", "timezone": "America/Argentina/Buenos_Aires"},  # Every Monday 6 AM
            "actions": [
                {"type": WorkflowActionType.CREATE_CONTENT_BRIEF, "config": {
                    "agent": "seo-content",
                    "brief_type": "blog_post",
                    "auto_generate": True,
                }},
                {"type": WorkflowActionType.GENERATE_COPY, "config": {
                    "agent": "seo-content",
                    "copy_types": ["blog_post"],
                    "schedule": True,
                }},
                {"type": WorkflowActionType.SCHEDULE_POST, "config": {
                    "platform": "blog",
                    "auto_publish": False,
                    "requires_approval": True,
                }},
            ],
            "status": WorkflowStatus.DRAFT,
            "is_active": True,
        },
        {
            "name": "🎯 Nurturing de Leads Fríos con Contenido",
            "description": "Cada 14 días, envía contenido de valor a leads fríos para mantenerlos calentitos.",
            "trigger_type": WorkflowTriggerType.TIME_DELAY,
            "trigger_config": {"cron": "0 10 * * 3", "timezone": "America/Argentina/Buenos_Aires"},  # Every Wednesday 10 AM
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {
                    "personality": "captador",
                    "message": "Send a 'value bomb' to cold leads. Share an insight, tip, or mini-case study related to their industry. NO sales pitch. NO product mention. Pure educational value. Goal: stay top-of-mind and build trust. 80-120 words."
                }},
                {"type": WorkflowActionType.UPDATE_SCORE, "config": {"points": 5}},
            ],
            "status": WorkflowStatus.DRAFT,
            "is_active": True,
        },
    ]

    for wf_data in growth_workflows:
        await get_or_create_workflow(db, business_id, wf_data["name"], **wf_data)

    await db.commit()
