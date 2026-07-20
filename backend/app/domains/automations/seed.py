"""Seed pre-built automations, workflows, email templates, sequences and chatbot rules."""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.automations.models import (
    Workflow, WorkflowTriggerType, WorkflowActionType, WorkflowStatus,
    EmailTemplate, EmailSequence, SequenceStep, ChatbotRule,
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


async def seed_automations(db: AsyncSession, business_id: uuid.UUID):
    """Seed a complete sales automation stack for a business."""

    # ========== WORKFLOWS ==========
    workflows = [
        {
            "name": "🎣 Captación Automática de Leads",
            "description": "Cuando llega un nuevo lead, envía bienvenida y asigna al cualificador.",
            "trigger_type": WorkflowTriggerType.NEW_LEAD,
            "trigger_config": {},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "captador", "delay_seconds": 5}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "nuevo_lead"}},
                {"type": WorkflowActionType.WAIT, "config": {"minutes": 10}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "cualificador", "message": "Qualify this lead with BANT questions"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🛒 Recuperación de Carrito Abandonado",
            "description": "Secuencia multicanal para recuperar carritos abandonados en 24h usando IA con voz experta.",
            "trigger_type": WorkflowTriggerType.CART_ABANDONED,
            "trigger_config": {"delay_minutes": 60},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "cart-recovery", "message": "Send a friendly cart abandonment reminder. Mention the items left behind and create gentle urgency without being pushy."}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 6}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "cart-recovery", "message": "Send a second recovery message with a stronger incentive. Address common objections like price or shipping."}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 18}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "objection-crusher", "message": "Final attempt. Break down any remaining objections. Use scarcity or social proof. Be direct but respectful."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "cart_recovery_attempted"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "⏰ Follow-up Post-Cita No-Show",
            "description": "Cuando alguien no aparece a una cita, reactiva con empatía y valor usando IA.",
            "trigger_type": WorkflowTriggerType.APPOINTMENT_MISSED,
            "trigger_config": {},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "appointment-setter", "message": "Send a compassionate no-show follow-up. Assume positive intent. Offer to reschedule with minimal friction."}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 2}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "post-venta", "message": "Send a value-packed re-engagement. Share a useful resource or insight related to their original interest. Re-offer the appointment."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "noshow_followed_up"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🔥 Reactivación de Leads Fríos (30 días)",
            "description": "Activa leads que no respondieron en 30 días con IA y nueva oferta.",
            "trigger_type": WorkflowTriggerType.NO_REPLY,
            "trigger_config": {"delay_days": 30},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "re-engagement", "message": "Send a win-back message. Reference something specific from their original inquiry. Announce something new since they last engaged."}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 3}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "re-engagement", "message": "Final re-engagement attempt. Use the 'breakup email' technique. Make them feel they're about to miss out permanently."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "reactivation_attempted"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🤝 Onboarding de Nuevo Cliente",
            "description": "Secuencia de bienvenida y onboarding tras la primera compra.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "cliente_nuevo"},
            "actions": [
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "welcome_new_client"}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 1}},
                {"type": WorkflowActionType.SEND_MESSAGE, "config": {"channel": "whatsapp", "template": "onboarding_tip_1"}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 3}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "post-venta", "message": "Check in with new client for satisfaction"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
    ]

    for wf_data in workflows:
        await get_or_create_workflow(db, business_id, wf_data["name"], **wf_data)

    # ========== EMAIL TEMPLATES ==========
    templates = [
        {
            "name": "Bienvenida Nuevo Lead",
            "subject": "👋 ¡Bienvenido! Esto es lo que sigue...",
            "body_text": "Hola {{lead_name}},\n\nGracias por tu interés en {{business_name}}.\n\nEn los próximos minutos te voy a enviar información valiosa sobre cómo {{product_name}} puede ayudarte a {{dream_outcome}}.\n\nMientras tanto, ¿cuál es tu mayor desafío actual con {{pain_point}}?\n\nSaludos,\nEl equipo de {{business_name}}",
            "body_html": "<p>Hola {{lead_name}},</p><p>Gracias por tu interés en <strong>{{business_name}}</strong>.</p><p>Te enviaremos información valiosa pronto.</p>",
            "variables": ["lead_name", "business_name", "product_name", "dream_outcome", "pain_point"],
            "category": "welcome",
        },
        {
            "name": "Recuperación Carrito - Email 1",
            "subject": "🛒 ¿Te olvidaste de algo? Tenés un 10% OFF",
            "body_text": "Hola {{lead_name}},\n\nVimos que dejaste {{product_name}} en tu carrito.\n\nTe entendemos — a veces hay que pensarlo. Por eso te damos un 10% de descuento por las próximas 24 horas.\n\nUsá el código: VOLVER10\n\n[Completar compra]\n\n¿Tenés alguna duda? Respondé este email o escribinos por WhatsApp.",
            "body_html": "<p>Hola {{lead_name}},</p><p>Vimos que dejaste <strong>{{product_name}}</strong> en tu carrito.</p><p><strong>Código: VOLVER10 (10% OFF por 24h)</strong></p><p><a href='{{checkout_url}}'>Completar compra →</a></p>",
            "variables": ["lead_name", "product_name", "checkout_url"],
            "category": "cart_recovery",
        },
        {
            "name": "Recuperación Carrito - Email 2 (Última chance)",
            "subject": "⏰ Últimas horas: Tu 10% OFF expira pronto",
            "body_text": "Hola {{lead_name}},\n\nQuedan menos de 6 horas para usar tu código VOLVER10.\n\nDespués de eso, el precio vuelve a normal.\n\n[Completar compra ahora]\n\nSi no estás seguro, respondé con tus dudas y te ayudamos en minutos.",
            "body_html": "<p>Hola {{lead_name}},</p><p><strong>Quedan menos de 6 horas para tu 10% OFF.</strong></p><p><a href='{{checkout_url}}'>Completar compra →</a></p>",
            "variables": ["lead_name", "product_name", "checkout_url"],
            "category": "cart_recovery",
        },
        {
            "name": "Win-Back Lead Frío",
            "subject": "¿Todavía te interesa {{product_name}}? Tenemos novedades 🚀",
            "body_text": "Hola {{lead_name}},\n\nHace un tiempo conversamos sobre {{product_name}}. Desde entonces agregamos nuevas funciones que creo te van a encantar.\n\n¿Te gustaría una demo rápida de 10 minutos esta semana?\n\n[Agendar demo]\n\nSaludos,\n{{business_name}}",
            "body_html": "<p>Hola {{lead_name}},</p><p>¿Todavía te interesa <strong>{{product_name}}</strong>?</p><p><a href='{{booking_url}}'>Agendar demo de 10 min →</a></p>",
            "variables": ["lead_name", "product_name", "business_name", "booking_url"],
            "category": "re_engagement",
        },
        {
            "name": "Post-Compra: Solicitud de Review",
            "subject": "¿Cómo te fue con {{product_name}}? 🌟",
            "body_text": "Hola {{lead_name}},\n\nEsperamos que estés disfrutando {{product_name}}.\n\n¿Podés dedicarnos 30 segundos para dejarnos una review? Nos ayuda un montón.\n\n[Dejar review]\n\nSi tenés alguna duda o problema, respondé este email y te ayudamos al toque.",
            "body_html": "<p>Hola {{lead_name}},</p><p>¿Podés dedicarnos 30 segundos para una review? 🌟</p><p><a href='{{review_url}}'>Dejar review →</a></p>",
            "variables": ["lead_name", "product_name", "review_url"],
            "category": "follow_up",
        },
        {
            "name": "No-Show: Reagendar con Valor",
            "subject": "No pasa nada — reagendemos cuando quieras 📅",
            "body_text": "Hola {{lead_name}},\n\nVi que no pudiste conectarte a la llamada. No pasa nada, la vida es así.\n\nMientras tanto, te comparto un recurso que creo te va a servir mucho:\n\n[Descargar recurso gratuito]\n\n¿Te gustaría reagendar para la próxima semana?\n\n[Reagendar ahora]",
            "body_html": "<p>Hola {{lead_name}},</p><p>No pasa nada por no poder conectarte.</p><p><a href='{{booking_url}}'>Reagendar llamada →</a></p>",
            "variables": ["lead_name", "booking_url"],
            "category": "follow_up",
        },
    ]

    for tpl_data in templates:
        await get_or_create_template(db, business_id, tpl_data["name"], **tpl_data)

    # ========== EMAIL SEQUENCES ==========
    sequences = [
        {
            "name": "🎣 Nurturing para Nuevos Leads (5 días)",
            "description": "Secuencia de 5 emails que nutre leads nuevos desde la bienvenida hasta la oferta.",
            "category": "nurture",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "new_lead",
        },
        {
            "name": "🛒 Recuperación de Carrito (48h)",
            "description": "2 emails + WhatsApp para recuperar carritos abandonados.",
            "category": "cart_recovery",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "cart_abandoned",
        },
        {
            "name": "🤝 Onboarding Nuevo Cliente (7 días)",
            "description": "Bienvenida, tips de uso, check-in y solicitud de review.",
            "category": "onboarding",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "tag_added",
        },
    ]

    for seq_data in sequences:
        await get_or_create_sequence(db, business_id, seq_data["name"], **seq_data)

    # ========== CHATBOT RULES ==========
    rules = [
        {
            "name": "Saludo Inicial",
            "intent": "greeting",
            "keywords": ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "hi", "hello", "que tal", "como va"],
            "response_template": "¡Hola! 👋 Soy el asistente virtual de {{business_name}}. Estoy acá para ayudarte con info sobre nuestros productos, precios, o lo que necesites. ¿En qué puedo ayudarte hoy?",
            "response_type": "text",
            "priority": 10,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Consulta de Precio",
            "intent": "price",
            "keywords": ["precio", "cuanto cuesta", "valor", "tarifa", "costo", "cuanto sale", "precios", "cuanto vale", "presupuesto"],
            "response_template": "¡Buena pregunta! 💰 Nuestros planes arrancan desde $0 (Free) hasta $49/mes (Pro). El plan más popular es Pro porque incluye 5 agentes IA, todos los canales y automatizaciones ilimitadas.\n\n¿Te gustaría que te explique las diferencias entre los planes o preferís una demo personalizada?",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Disponibilidad / Stock",
            "intent": "availability",
            "keywords": ["tenes stock", "hay disponible", "disponibilidad", "hay", "queda", "stock", "cuando llega", "envio"],
            "response_template": "Tenemos stock disponible y enviamos en 24-48hs hábiles 🚚. ¿Te gustaría que te reserve una unidad? Solo necesito tu dirección y te paso el link de pago seguro.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Objeción: 'Es Caro'",
            "intent": "objection",
            "keywords": ["caro", "muy caro", "no me alcanza", "no puedo pagar", "es mucho", "sale caro", "esta caro"],
            "response_template": "Te entiendo — invertir en tu negocio siempre requiere pensarlo bien. 💡\n\nAcá te va una pregunta: ¿cuánto te está costando HOY no tener este sistema? Es decir, las ventas que perdés respondiendo tarde, los leads que se enfrían, o el tiempo que gastás en tareas repetitivas.\n\nMuchos clientes recuperan la inversión en la primera semana. ¿Te gustaría que te muestre un caso similar al tuyo?",
            "response_type": "text",
            "priority": 25,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Objeción: 'Lo voy a pensar'",
            "intent": "objection",
            "keywords": ["voy a pensarlo", "lo pienso", "dame tiempo", "necesito pensar", "consultar", "hablar con"],
            "response_template": "Claro, pensarlo es inteligente 👍.\n\nSolo una pregunta: ¿qué info te falta para sentirte 100% seguro? Puede ser una demo, un caso de estudio de tu industria, o hablar con alguien que ya lo usa.\n\nTe lo pregunto porque la mayoría de las veces 'pensarlo' no es falta de interés, es falta de certeza. Y estoy acá para darte esa certeza. ¿Qué necesitás?",
            "response_type": "text",
            "priority": 25,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Reclamo / Soporte",
            "intent": "complaint",
            "keywords": ["no funciona", "problema", "reclamo", "mal", "error", "falla", "devolucion", "quiero cancelar", "no me gusta"],
            "response_template": "Lamento mucho que estés pasando por esto 😔. Tu satisfacción es lo primero.\n\nVoy a derivarte con un especialista de nuestro equipo de soporte que va a resolver tu situación en menos de 2 horas.\n\nMientras tanto, ¿podés contarme un poco más sobre qué pasó exactamente? Así llegamos con la solución lista.",
            "response_type": "text",
            "priority": 30,
            "channel_filter": [],
            "requires_human": True,
        },
        {
            "name": "Agendar Demo / Llamada",
            "intent": "appointment",
            "keywords": ["demo", "llamada", "cita", "reunion", "hablar", "videollamada", "consulta", "asesoria"],
            "response_template": "¡Me encanta que quieras verlo en acción! 🚀\n\nTenemos slots disponibles esta semana. ¿Qué día y horario te queda mejor?\n\nOpciones rápidas:\n• Mañana (10-12hs)\n• Tarde (15-17hs)\n• Noche (19-21hs)\n\nConfirmame y te mando el link de Zoom/WhatsApp.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Despedida / Gracias",
            "intent": "goodbye",
            "keywords": ["gracias", "muchas gracias", "adios", "chau", "hasta luego", "nos vemos", "ok gracias"],
            "response_template": "¡De nada! 🙌 Estoy acá 24/7 para lo que necesites.\n\nSi surge cualquier duda, mandame un mensaje. ¡Que tengas un excelente día!",
            "response_type": "text",
            "priority": 10,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Fallback General",
            "intent": "default",
            "keywords": [],
            "response_template": "Entiendo tu mensaje. Para darte la mejor respuesta posible, ¿podés contarme un poco más sobre qué estás buscando?\n\nPor ejemplo:\n• Info sobre precios 💰\n• Agendar una demo 📅\n• Soporte técnico 🛠️\n• Conocer nuestros productos 📦\n\nElegí la opción que más te sirva o escribime directamente.",
            "response_type": "text",
            "priority": 0,
            "channel_filter": [],
            "requires_human": False,
        },
    ]

    for rule_data in rules:
        await get_or_create_chatbot_rule(db, business_id, rule_data["name"], **rule_data)

    await db.commit()

    # === Service Workflows ===
    service_workflows = [
        {
            "name": "🗓️ Auto-Agendar Servicio Post-Pago",
            "description": "Cuando un cliente paga un servicio, crea automáticamente la entrega y agenda una cita.",
            "trigger_type": WorkflowTriggerType.SERVICE_PAID,
            "trigger_config": {},
            "actions": [
                {"type": WorkflowActionType.CREATE_APPOINTMENT, "config": {"modality": "remote", "duration_minutes": 60}},
                {"type": WorkflowActionType.SEND_NOTIFICATION, "config": {"message": "Nuevo servicio agendado automáticamente"}},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "📅 Recordatorio 24h antes de Cita",
            "description": "Envía recordatorio al cliente 24 horas antes de la cita programada.",
            "trigger_type": WorkflowTriggerType.APPOINTMENT_SCHEDULED,
            "trigger_config": {},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"delay": "23h"}},
                {"type": WorkflowActionType.SEND_REMINDER, "config": {"channel": "whatsapp"}},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "✅ Confirmación de Asistencia",
            "description": "Pide confirmación de asistencia 48h antes de la cita.",
            "trigger_type": WorkflowTriggerType.APPOINTMENT_SCHEDULED,
            "trigger_config": {},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"delay": "46h"}},
                {"type": WorkflowActionType.REQUEST_CONFIRMATION, "config": {"channel": "whatsapp"}},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "🙏 Feedback Post-Servicio",
            "description": "Solicita feedback al cliente 2 horas después de completar el servicio.",
            "trigger_type": WorkflowTriggerType.SERVICE_COMPLETED,
            "trigger_config": {},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"delay": "2h"}},
                {"type": WorkflowActionType.REQUEST_FEEDBACK, "config": {"channel": "whatsapp"}},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
        {
            "name": "😔 Follow-up No-Show",
            "description": "Cuando un cliente no asiste, envía mensaje para reagendar.",
            "trigger_type": WorkflowTriggerType.APPOINTMENT_NO_SHOW,
            "trigger_config": {},
            "actions": [
                {"type": WorkflowActionType.SEND_MESSAGE, "config": {"content": "Vimos que no pudiste asistir a la cita. ¿Te gustaría reagendar? Estamos disponibles mañana o pasado. 📅"}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "no_show_recontact"}},
            ],
            "status": WorkflowStatus.ACTIVE,
            "is_active": True,
        },
    ]

    for wf_data in service_workflows:
        await get_or_create_workflow(db, business_id, wf_data["name"], **wf_data)

    await db.commit()

    # Seed Instagram-specific automations
    from app.domains.automations.instagram_seed import seed_instagram_automations
    await seed_instagram_automations(db, business_id)

    # Seed platform-specific automations
    from app.domains.automations.platform_seed import seed_platform_automations
    await seed_platform_automations(db, business_id)

    # Seed content generation automations
    from app.domains.automations.content_seed import seed_content_automations
    await seed_content_automations(db, business_id)
