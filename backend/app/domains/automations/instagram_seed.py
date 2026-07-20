"""Seed pre-built Instagram-specific automations, workflows, DM sequences and chatbot rules.

These automations are designed to work with the Instagram Sales Specialist agents
(kylie-jenner, chiara-ferragni, huda-kattan, jay-shetty, amy-porterfield,
lewis-howes, brendon-burchard, rachel-rodgers, jenna-kutcher, instagram-orchestrator,
ig-dm-closer, ig-reel-optimizer, ig-story-closer, ig-live-seller).

They cover the complete Instagram funnel:
- Attraction (Reels, Stories, DMs)
- Qualification (DM automation, story polls)
- Conversion (DM closing, LIVE selling, cart recovery)
- Retention (UGC requests, reviews, re-engagement)
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.automations.models import (
    Workflow, WorkflowTriggerType, WorkflowActionType, WorkflowStatus,
    EmailTemplate, EmailSequence, ChatbotRule,
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


async def get_or_create_template(db: AsyncSession, business_id: uuid.UUID, name: str, **defaults) -> EmailTemplate:
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.business_id == business_id, EmailTemplate.name == name)
    )
    tpl = result.scalar_one_or_none()
    if not tpl:
        tpl = EmailTemplate(business_id=business_id, name=name, **defaults)
        db.add(tpl)
        await db.flush()
    return tpl


async def get_or_create_sequence(db: AsyncSession, business_id: uuid.UUID, name: str, **defaults) -> EmailSequence:
    result = await db.execute(
        select(EmailSequence).where(EmailSequence.business_id == business_id, EmailSequence.name == name)
    )
    seq = result.scalar_one_or_none()
    if not seq:
        seq = EmailSequence(business_id=business_id, name=name, **defaults)
        db.add(seq)
        await db.flush()
    return seq


async def get_or_create_chatbot_rule(db: AsyncSession, business_id: uuid.UUID, name: str, **defaults) -> ChatbotRule:
    result = await db.execute(
        select(ChatbotRule).where(ChatbotRule.business_id == business_id, ChatbotRule.name == name)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        rule = ChatbotRule(business_id=business_id, name=name, **defaults)
        db.add(rule)
        await db.flush()
    return rule


async def seed_instagram_automations(db: AsyncSession, business_id: uuid.UUID):
    """Seed a complete Instagram sales automation stack for a business."""

    # ========== INSTAGRAM WORKFLOWS ==========
    workflows = [
        {
            "name": "📱 Instagram: DM Auto-Bienvenida a Nuevos Seguidores",
            "description": "Cuando alguien empieza a seguir en Instagram, envía DM de bienvenida + lead magnet en 5 minutos.",
            "trigger_type": WorkflowTriggerType.NEW_LEAD,
            "trigger_config": {"channel": "instagram", "delay_minutes": 5},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "Send a warm welcome DM to a new Instagram follower. Introduce yourself, thank them for following, and offer a free valuable resource related to their interests. Ask ONE discovery question to start a conversation."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_new_follower"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 24}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "Follow up with new follower who hasn't responded. Share a quick tip or insight related to the lead magnet. Soft CTA: 'If you want the full guide, just reply GUIDE and I'll send it.'"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📱 Instagram: Comment-to-DM Atracción Automática",
            "description": "Cuando alguien comenta INFO, PRECIO, LINK o QUIERO en un Reel/post, envía DM automático de cualificación.",
            "trigger_type": WorkflowTriggerType.NEW_MESSAGE,
            "trigger_config": {"channel": "instagram", "keywords": ["info", "precio", "link", "quiero", "interesado", "me interesa", "dm", "cuanto", "como compro"]},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "Send an automatic DM to someone who commented keywords on a Reel/post. Acknowledge their comment, ask ONE qualifying question about their current situation, and tease the solution. Keep it under 100 words."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_comment_lead"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 6}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "cualificador", "message": "If they responded to the first DM, ask a BANT-style follow-up question. If they didn't respond, send a value bomb related to the original topic and re-ask softly."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📱 Instagram: Story Reply → DM Cualificación",
            "description": "Cuando alguien responde a una Story con emoji o texto, envía DM automático de cualificación en 2 minutos.",
            "trigger_type": WorkflowTriggerType.NEW_MESSAGE,
            "trigger_config": {"channel": "instagram", "message_type": "story_reply"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-story-closer", "message": "Send a warm DM to someone who replied to a Story. Reference the specific story they replied to. Ask a qualifying question related to the story content. Make it feel personal and hand-typed."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_story_reply"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 12}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "Follow up with story reply lead who hasn't responded. Share a quick win, testimonial, or tip related to the story topic. Soft close: 'If you want to know more, just ask.'"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📱 Instagram: Recuperación de Carrito por DM",
            "description": "Cuando alguien abandona el checkout desde el link de la bio, envía secuencia de DM de recuperación.",
            "trigger_type": WorkflowTriggerType.CART_ABANDONED,
            "trigger_config": {"channel": "instagram", "delay_minutes": 60},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "Send a friendly DM to someone who abandoned their cart from Instagram bio link. Assume they had a technical issue or question. Offer help and remind them what they left behind. No discount yet."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_cart_recovery"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 6}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "Second DM recovery attempt. Address common objections (price, shipping, uncertainty). Offer a small incentive if appropriate. Create gentle urgency."}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 18}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "objection-crusher", "message": "Final DM recovery attempt. Use scarcity or social proof. Be direct but warm. 'Hey, I noticed you didn't complete your order. Is there something I can help clarify?'"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📱 Instagram: DM de Reactivación de Leads Fríos (30 días)",
            "description": "Reactiva leads de Instagram que no respondieron en 30 días con contenido nuevo o novedad.",
            "trigger_type": WorkflowTriggerType.NO_REPLY,
            "trigger_config": {"channel": "instagram", "delay_days": 30},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "Send a win-back DM to a cold Instagram lead. Reference something specific from your original conversation if available. Share something NEW: a recent result, a new product, a success story. Make them feel they discovered something, not that they're being sold to."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_reactivation"}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 3}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "re-engagement", "message": "Final re-engagement DM. Use the 'breakup' technique gently. 'I don't want to bother you if this isn't a fit. Should I close your file or is there something I can help with?'"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📱 Instagram: Post-Compra + Solicitud UGC",
            "description": "Después de la primera compra desde Instagram, envía secuencia de onboarding y solicitud de contenido generado por usuario.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "ig_cliente_nuevo"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "post-venta", "message": "Send a personalized DM to a new Instagram customer. Confirm their order, set delivery expectations, and share a quick tip on how to get the most out of their purchase. Make them feel like a VIP."}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 3}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "post-venta", "message": "Check-in DM. Ask if everything arrived OK and if they have any questions. Share a pro tip about usage."}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 7}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "post-venta", "message": "UGC request DM. Ask for a photo or video of them using the product. Offer an incentive: discount on next purchase, feature on your page, or entry into a giveaway. Make it easy and exciting."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_ugc_requested"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📱 Instagram: LIVE Selling Post-Event",
            "description": "Después de un Instagram LIVE, envía DMs a viewers activos con oferta extendida y replay.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "ig_live_completed"},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"minutes": 10}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-live-seller", "message": "DM to active LIVE viewers. Thank them for joining. Share the replay link. Remind them of the LIVE-exclusive offer and give them a short extension (2-4 hours). Clear CTA."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_live_followup"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 24}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-live-seller", "message": "Second follow-up to LIVE viewers who haven't purchased. Share a testimonial from someone who bought during the LIVE. Remind them the extended offer closes soon."}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 24}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "re-engagement", "message": "Final follow-up to non-buying LIVE viewers. If they missed the offer, invite them to the next LIVE or offer a waitlist for the next launch. Leave the door open."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📱 Instagram: Cierre por DM (Hot Lead)",
            "description": "Cuando un lead de Instagram alcanza score HOT, activa secuencia de cierre por DM con IA.",
            "trigger_type": WorkflowTriggerType.LEAD_SCORE_CHANGED,
            "trigger_config": {"min_score": 80, "channel": "instagram"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "DM to a HOT Instagram lead. Review their qualification data. Present the offer with absolute certainty. Use a soft close with choice: 'Which option works better for you?' or 'Should I send you the link now?'"}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_hot_dm_sent"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 12}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "ig-dm-closer", "message": "Follow-up to hot lead who hasn't bought. Address the most common objection for this product. Use social proof or scarcity. Remain confident and warm."}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 24}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "objection-crusher", "message": "Final DM close attempt. Direct but respectful. 'I know this is a big decision. What would make you feel 100% confident moving forward?' If no response, tag for long-term nurture."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
    ]

    for wf_data in workflows:
        await get_or_create_workflow(db, business_id, wf_data["name"], **wf_data)

    # ========== INSTAGRAM EMAIL TEMPLATES ==========
    templates = [
        {
            "name": "Instagram Lead Magnet Delivery",
            "subject": "🎁 Aquí está tu guía de Instagram + un bonus",
            "body_text": (
                "Hola {{lead_name}},\n\n"
                "Gracias por tu interés en {{business_name}} a través de Instagram.\n\n"
                "Como te prometí, aquí está tu guía gratuita:\n"
                "[Descargar Guía]\n\n"
                "PERO ESPERA — quería darte algo extra:\n\n"
                "Una mini-clase de 10 minutos donde te muestro exactamente cómo [resultado específico]. "
                "Es el complemento perfecto de la guía.\n\n"
                "[Ver mini-clase gratuita]\n\n"
                "¿Te sirvió? Respondé a este email o escribime por Instagram DM. "
                "Leo y respondo personalmente cada mensaje.\n\n"
                "{{business_name}}"
            ),
            "body_html": (
                "<p>Hola {{lead_name}},</p>"
                "<p>Gracias por tu interés en <strong>{{business_name}}</strong> a través de Instagram.</p>"
                "<p><a href='{{guide_url}}'>📥 Descargar tu guía gratuita</a></p>"
                "<p><strong>BONUS:</strong> <a href='{{video_url}}'>🎥 Ver mini-clase de 10 min</a></p>"
            ),
            "variables": ["lead_name", "business_name", "guide_url", "video_url"],
            "category": "instagram",
        },
        {
            "name": "Instagram LIVE Replay + Oferta Extendida",
            "subject": "🎥 Replay del LIVE + 4 horas más de tu oferta exclusiva",
            "body_text": (
                "Hola {{lead_name}},\n\n"
                "Gracias por estar en mi LIVE de Instagram.\n\n"
                "Si te perdiste algo o querés verlo de nuevo, aquí está el replay completo:\n"
                "[Ver Replay]\n\n"
                "Y como estuviste en el LIVE, extendí tu oferta exclusiva por 4 horas más:\n\n"
                "[Acceder a la oferta LIVE]\n\n"
                "Después de eso, el precio vuelve a normal y los bonos desaparecen.\n\n"
                "Nos vemos en el próximo LIVE,\n"
                "{{business_name}}"
            ),
            "body_html": (
                "<p>Hola {{lead_name}},</p>"
                "<p>Gracias por estar en mi LIVE de Instagram.</p>"
                "<p><a href='{{replay_url}}'>🎥 Ver Replay</a></p>"
                "<p><a href='{{offer_url}}'>🔥 Acceder a tu oferta exclusiva (4h más)</a></p>"
            ),
            "variables": ["lead_name", "business_name", "replay_url", "offer_url"],
            "category": "instagram",
        },
        {
            "name": "Instagram UGC Request",
            "subject": "📸 ¿Podés hacernos un favor? (Hay premio)",
            "body_text": (
                "Hola {{lead_name}},\n\n"
                "Esperamos que estés amando tu {{product_name}}.\n\n"
                "Te queremos pedir un favor: ¿podés sacarte una foto o video usando el producto "
                "y etiquetarnos en Instagram?\n\n"
                "Como agradecimiento, te damos:\n"
                "• 15% OFF en tu próxima compra\n"
                "• Chance de aparecer en nuestra cuenta ({{follower_count}}+ seguidores)\n"
                "• Entrada automática a nuestro sorteo mensual\n\n"
                "[Subir mi foto/video]\n\n"
                "Gracias por ser parte de la comunidad {{business_name}}."
            ),
            "body_html": (
                "<p>Hola {{lead_name}},</p>"
                "<p>¿Podés sacarte una foto usando <strong>{{product_name}}</strong>?</p>"
                "<p>🎁 <strong>Beneficios:</strong> 15% OFF + feature en nuestra cuenta + sorteo mensual</p>"
                "<p><a href='{{upload_url}}'>Subir mi foto/video</a></p>"
            ),
            "variables": ["lead_name", "product_name", "business_name", "follower_count", "upload_url"],
            "category": "instagram",
        },
    ]

    for tpl_data in templates:
        await get_or_create_template(db, business_id, tpl_data["name"], **tpl_data)

    # ========== INSTAGRAM EMAIL SEQUENCES ==========
    sequences = [
        {
            "name": "📱 Instagram: Nurturing desde DM (7 días)",
            "description": "Secuencia para leads captados por Instagram DM que dejaron su email.",
            "category": "instagram_nurture",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "tag_added",
        },
        {
            "name": "📱 Instagram: Recuperación Carrito DM (24h)",
            "description": "Emails de respaldo para recuperación de carrito desde Instagram.",
            "category": "instagram_cart_recovery",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "cart_abandoned",
        },
        {
            "name": "📱 Instagram: Post-LIVE Conversion (48h)",
            "description": "Secuencia post-LIVE para viewers que no compraron durante el evento.",
            "category": "instagram_live",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "tag_added",
        },
    ]

    for seq_data in sequences:
        await get_or_create_sequence(db, business_id, seq_data["name"], **seq_data)

    # ========== INSTAGRAM CHATBOT RULES ==========
    rules = [
        {
            "name": "IG Saludo Inicial / Bienvenida",
            "intent": "greeting",
            "keywords": ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "hi", "hello", "que tal", "como va", "👋"],
            "response_template": "¡Hola! 👋 Bienvenido/a a {{business_name}} por Instagram. Veo que llegaste por acá — eso significa que algo de nuestro contenido te resonó. 💡\n\nEstoy acá para ayudarte con info sobre nuestros productos, responder dudas, o lo que necesites. ¿En qué puedo ayudarte hoy?",
            "response_type": "text",
            "priority": 10,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Consulta de Precio",
            "intent": "price",
            "keywords": ["precio", "cuanto cuesta", "valor", "tarifa", "costo", "cuanto sale", "precios", "cuanto vale", "presupuesto", "$$", "💰"],
            "response_template": "¡Buena pregunta! 💰\n\nNuestros planes/productos arrancan desde {{min_price}}. El más popular es {{popular_plan}} porque incluye {{popular_feature}}.\n\nPero antes de darte el precio exacto, me gustaría entender mejor qué necesitás. ¿Te parece si me contás un poco sobre tu situación? Así te recomiendo la opción que más te conviene. 👇",
            "response_type": "text",
            "priority": 20,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Comment INFO Trigger",
            "intent": "info_request",
            "keywords": ["info", "informacion", "más info", "quiero saber", "como funciona", "detalles", "explicame", "contame"],
            "response_template": "¡Claro! Acá te va el resumen rápido:\n\n{{product_summary}}\n\n¿Qué te gustaría saber primero?\n• Precios 💰\n• Cómo funciona paso a paso 🔧\n• Resultados de clientes 📊\n• Agendar una demo 📅\n\nEscribime el número o la palabra y te cuento todo.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Link / Compra Directa",
            "intent": "buy",
            "keywords": ["link", "comprar", "quiero comprar", "pasame el link", "donde compro", "checkout", "pago", "tarjeta", "como pago", "🛒"],
            "response_template": "¡Me encanta que quieras avanzar! 🚀\n\nAcá está tu link seguro de compra:\n{{checkout_url}}\n\n¿Tenés alguna duda antes de completar? Estoy acá para ayudarte en tiempo real.",
            "response_type": "text",
            "priority": 25,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Disponibilidad / Stock",
            "intent": "availability",
            "keywords": ["tenes stock", "hay disponible", "disponibilidad", "hay", "queda", "stock", "cuando llega", "envio", "🚚"],
            "response_template": "Sí, tenemos stock disponible y enviamos en {{shipping_time}} 🚚.\n\n¿Te gustaría que te reserve una unidad? Solo confirmame y te paso el link de pago seguro por acá mismo.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Objeción: 'Es Caro'",
            "intent": "objection",
            "keywords": ["caro", "muy caro", "no me alcanza", "no puedo pagar", "es mucho", "sale caro", "esta caro", "💸"],
            "response_template": "Te entiendo completamente — invertir siempre requiere pensarlo bien. 💡\n\nAcá te va una pregunta honesta: ¿cuánto te está costando HOY no resolver {{pain_point}}? Es decir, el tiempo, las oportunidades perdidas, o el estrés de no tenerlo resuelto.\n\nMuchos clientes me dicen que recuperan la inversión en {{payback_time}}. ¿Te gustaría que te muestre un caso similar al tuyo? 📊",
            "response_type": "text",
            "priority": 25,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Objeción: 'Lo voy a pensar'",
            "intent": "objection",
            "keywords": ["voy a pensarlo", "lo pienso", "dame tiempo", "necesito pensar", "consultar", "hablar con", "me lo pensare", "🤔"],
            "response_template": "Claro, pensarlo es inteligente 👍.\n\nSolo una pregunta rápida: ¿qué info te falta para sentirte 100% seguro/a? Puede ser una demo, un caso de estudio de tu industria, o hablar con alguien que ya lo compró.\n\nTe lo pregunto porque muchas veces 'pensarlo' no es falta de interés, es falta de certeza. Y estoy acá para darte esa certeza. ¿Qué necesitás? 🤝",
            "response_type": "text",
            "priority": 25,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Agendar Demo / Llamada",
            "intent": "appointment",
            "keywords": ["demo", "llamada", "cita", "reunion", "hablar", "videollamada", "consulta", "asesoria", "📅"],
            "response_template": "¡Me encanta que quieras verlo en acción! 🚀\n\nTenemos slots disponibles esta semana. ¿Qué día y horario te queda mejor?\n\nOpciones rápidas:\n• Mañana (10-12hs)\n• Tarde (15-17hs)\n• Noche (19-21hs)\n\nConfirmame y te mando el link de Zoom/WhatsApp.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Reclamo / Soporte",
            "intent": "complaint",
            "keywords": ["no funciona", "problema", "reclamo", "mal", "error", "falla", "devolucion", "quiero cancelar", "no me gusta", "😠"],
            "response_template": "Lamento mucho que estés pasando por esto 😔. Tu satisfacción es lo primero.\n\nVoy a derivarte con un especialista de nuestro equipo de soporte que va a resolver tu situación en menos de 2 horas.\n\nMientras tanto, ¿podés contarme un poco más sobre qué pasó exactamente? Así llegamos con la solución lista. 🛠️",
            "response_type": "text",
            "priority": 30,
            "channel_filter": ["instagram"],
            "requires_human": True,
        },
        {
            "name": "IG UGC / Reseña",
            "intent": "review",
            "keywords": ["reseña", "review", "opinion", "que te parecio", "foto", "video", "etiquetar", "tag", "📸", "⭐"],
            "response_template": "¡Me alegra que quieras compartir! 📸⭐\n\nSi nos etiquetás en Instagram con una foto o video usando {{product_name}}, te damos:\n• 15% OFF en tu próxima compra\n• Chance de aparecer en nuestra cuenta oficial\n• Entrada automática a nuestro sorteo mensual\n\nSimplemente subí tu contenido, etiquetá a {{instagram_handle}}, y enviame un screenshot por acá para validar tu descuento. ¡Gracias por ser parte de la comunidad! 🙌",
            "response_type": "text",
            "priority": 20,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Despedida / Gracias",
            "intent": "goodbye",
            "keywords": ["gracias", "muchas gracias", "adios", "chau", "hasta luego", "nos vemos", "ok gracias", "👋"],
            "response_template": "¡De nada! 🙌 Estoy acá 24/7 por Instagram DM para lo que necesites.\n\nSi surge cualquier duda, mandame un mensaje. ¡Y no te olvides de seguirnos para contenido nuevo todos los días! 🔔\n\nQue tengas un excelente día ✨",
            "response_type": "text",
            "priority": 10,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
        {
            "name": "IG Fallback General",
            "intent": "default",
            "keywords": [],
            "response_template": "Entiendo tu mensaje. Para darte la mejor respuesta posible, ¿podés contarme un poco más sobre qué estás buscando?\n\nPor ejemplo:\n• Info sobre precios 💰\n• Agendar una demo 📅\n• Soporte técnico 🛠️\n• Conocer nuestros productos 📦\n• Dejar una reseña ⭐\n\nElegí la opción que más te sirva o escribime directamente.",
            "response_type": "text",
            "priority": 0,
            "channel_filter": ["instagram"],
            "requires_human": False,
        },
    ]

    for rule_data in rules:
        await get_or_create_chatbot_rule(db, business_id, rule_data["name"], **rule_data)

    await db.commit()
