"""Seed pre-built platform-specific automations, workflows, and chatbot rules.

Designed for marketplace/e-commerce platforms: Amazon, MercadoLibre, Shopify,
WooCommerce, Hotmart, TikTok Shop, Instagram Shopping, eBay, Etsy, Shopee.

These automations work with the platform specialist agents in
13_platform_specialists.py and integrate with the existing order/revenue system.
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


async def seed_platform_automations(db: AsyncSession, business_id: uuid.UUID):
    """Seed a complete platform-specific sales automation stack for a business."""

    # ========== PLATFORM WORKFLOWS ==========
    workflows = [
        # Amazon Workflows
        {
            "name": "📦 Amazon: Auto-Respuesta a Buyer Messages",
            "description": "Responde automáticamente a mensajes de compradores en Amazon en menos de 2 horas.",
            "trigger_type": WorkflowTriggerType.NEW_MESSAGE,
            "trigger_config": {"channel": "amazon"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "amazon-master", "message": "Respond to an Amazon buyer message professionally and concisely. Address their question directly. If pre-sale, qualify gently. If post-sale, resolve or escalate. Keep under 150 words."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "amazon_buyer_msg"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📦 Amazon: Solicitud de Review Post-Entrega",
            "description": "7 días después de entrega, solicita review al comprador de Amazon.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "amazon_delivered"},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"days": 7}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "post-venta", "message": "Send a polite Amazon review request. Thank the buyer. Ask for honest feedback. Do NOT ask for positive reviews or offer incentives. Comply with Amazon TOS."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "amazon_review_requested"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "📦 Amazon: Alerta de Buy Box Lost",
            "description": "Notifica cuando el Buy Box percentage baja de 90% y sugiere acciones.",
            "trigger_type": WorkflowTriggerType.LEAD_SCORE_CHANGED,
            "trigger_config": {"metric": "buy_box_pct", "threshold": 90, "operator": "less_than"},
            "actions": [
                {"type": WorkflowActionType.SEND_NOTIFICATION, "config": {"message": "ALERTA: Buy Box % bajó de 90% para un ASIN. Revisar precio, stock, y métricas de seller."}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "amazon-master", "message": "Analyze why Buy Box was lost. Check competitor pricing, stock levels, seller metrics, and FBA status. Provide 3 actionable steps to regain Buy Box."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        # MercadoLibre Workflows
        {
            "name": "🛒 ML: Auto-Respuesta a Preguntas",
            "description": "Responde automáticamente a preguntas de compradores en MercadoLibre en menos de 5 minutos.",
            "trigger_type": WorkflowTriggerType.NEW_MESSAGE,
            "trigger_config": {"channel": "mercadolibre"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "mercadolibre-master", "message": "Respond to a MercadoLibre pregunta quickly and professionally. Answer the specific question. If it's a pre-sale question, add a soft close. Keep it under 100 words."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ml_pregunta"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🛒 ML: Gestión de Reputación Post-Venta",
            "description": "Solicita calificación y gestiona reputación después de la venta en ML.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "ml_entregado"},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"hours": 48}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "post-venta", "message": "Send a warm follow-up to ML buyer. Confirm they received the product. Ask if everything is OK. Indirectly encourage a positive rating by expressing how much their opinion helps. Do NOT explicitly ask for 5 stars."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ml_reputacion_gestionada"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🛒 ML: Alerta de Competencia de Precio",
            "description": "Alerta cuando un competidor baja el precio debajo del tuyo en un listing ganador.",
            "trigger_type": WorkflowTriggerType.PRICE_INQUIRY,
            "trigger_config": {"platform": "mercadolibre", "trigger": "competitor_price_drop"},
            "actions": [
                {"type": WorkflowActionType.SEND_NOTIFICATION, "config": {"message": "Competidor bajó precio en ML. Revisar listing y evaluar ajuste."}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "mercadolibre-master", "message": "Analyze the competitor price drop. Should we match, undercut slightly, or hold price? Consider margin, Buy Box impact, and brand positioning. Provide recommendation with numbers."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        # Shopify Workflows
        {
            "name": "🛍️ Shopify: Abandoned Checkout Recovery",
            "description": "Recupera carritos abandonados en Shopify con email + AI message en 1h, 6h, 24h.",
            "trigger_type": WorkflowTriggerType.CART_ABANDONED,
            "trigger_config": {"platform": "shopify", "delay_minutes": 60},
            "actions": [
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "shopify_cart_recovery_1"}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "shopify-master", "message": "Send a friendly abandoned cart reminder via WhatsApp/IG if email not opened. Mention items left behind and offer help."}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 5}},
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "shopify_cart_recovery_2"}},
                {"type": WorkflowActionType.WAIT, "config": {"hours": 18}},
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "shopify_cart_recovery_3"}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "shopify_recovery_attempted"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🛍️ Shopify: Post-Purchase Upsell",
            "description": "1 día después de la entrega, recomienda producto complementario con descuento.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "shopify_delivered"},
            "actions": [
                {"type": WorkflowActionType.WAIT, "config": {"days": 1}},
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "upsell-specialist", "message": "Send a post-purchase upsell email/message. Recommend a complementary product based on what they bought. Offer 15% discount for 48 hours. Make it feel personalized."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "shopify_upsell_sent"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🛍️ Shopify: Win-Back Sequence",
            "description": "Reactiva clientes de Shopify inactivos por 60+ días.",
            "trigger_type": WorkflowTriggerType.NO_REPLY,
            "trigger_config": {"platform": "shopify", "delay_days": 60},
            "actions": [
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "shopify_winback_1"}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 7}},
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "shopify_winback_2"}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "shopify_winback_attempted"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        # Hotmart Workflows
        {
            "name": "🎓 Hotmart: Affiliate Recruitment DM",
            "description": "Cuando alguien pregunta por ser afiliado, envía DM automático con info y link de aplicación.",
            "trigger_type": WorkflowTriggerType.NEW_MESSAGE,
            "trigger_config": {"keywords": ["afiliado", "affiliate", "quiero vender", "como ser afiliado", "quero ser afiliado"]},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "hotmart-master", "message": "Send an enthusiastic affiliate recruitment response. Explain commission structure, promotional materials available, and how to apply. Include application link."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "hotmart_affiliate_lead"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🎓 Hotmart: Launch Sequence Pre-Event",
            "description": "Secuencia de 7 días pre-launch con contenido automatizado para Hotmart.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "hotmart_prelaunch"},
            "actions": [
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "hotmart_prelaunch_day_1"}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 1}},
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "hotmart_prelaunch_day_3"}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 2}},
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "hotmart_prelaunch_day_5"}},
                {"type": WorkflowActionType.WAIT, "config": {"days": 2}},
                {"type": WorkflowActionType.SEND_EMAIL, "config": {"template": "hotmart_prelaunch_day_7"}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "hotmart_launch_sequence_sent"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        # Cross-Platform Workflows
        {
            "name": "🌐 Cross-Platform: Inventory Sync Alert",
            "description": "Alerta cuando el stock en una plataforma difiere del stock maestro.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "inventory_sync_check"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "cross-platform-orchestrator", "message": "Analyze inventory discrepancy across platforms. Identify which channel is out of sync. Recommend immediate action to prevent overselling."}},
                {"type": WorkflowActionType.SEND_NOTIFICATION, "config": {"message": "ALERTA: Discrepancia de inventario detectada entre plataformas. Revisar CatalogSyncService."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🌐 Cross-Platform: Dynamic Pricing Monitor",
            "description": "Monitorea cambios de precio de competidores en múltiples canales.",
            "trigger_type": WorkflowTriggerType.PRICE_INQUIRY,
            "trigger_config": {"trigger": "competitor_price_change"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "cross-platform-orchestrator", "message": "Analyze competitor pricing change across channels. Should we adjust our price? Consider margin by channel, Buy Box impact, and brand positioning. Provide data-driven recommendation."}},
                {"type": WorkflowActionType.SEND_NOTIFICATION, "config": {"message": "Competidor cambió precio. Revisar recomendación del Orchestrator."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        # TikTok Shop Workflows
        {
            "name": "🛍️ TikTok Shop: Shop Health Monitor",
            "description": "Alerta diaria si el Shop Health Score baja de 'Good'.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "tiktok_shop_daily_check"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "tiktok-shop-master", "message": "Analyze TikTok Shop health score components. Identify which metric is dragging down the score: fulfillment speed, product quality, return rate, or customer service. Provide 3 immediate fixes."}},
                {"type": WorkflowActionType.SEND_NOTIFICATION, "config": {"message": "TikTok Shop Health Score requiere atención. Revisar métricas."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🛍️ TikTok Shop: Affiliate Commission Optimization",
            "description": "Sugiere ajustes de comisión basados en conversion rate de afiliados.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "tiktok_affiliate_review"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "tiktok-shop-master", "message": "Analyze affiliate performance data. Which affiliates are converting? Which are not? Recommend commission adjustments, bonus tiers, or affiliate pruning."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        # Instagram Shopping Workflows
        {
            "name": "🛒 Instagram Shop: Product Tag Engagement DM",
            "description": "Envía DM automático a quien guarda un producto taggeado en Instagram.",
            "trigger_type": WorkflowTriggerType.NEW_MESSAGE,
            "trigger_config": {"channel": "instagram", "trigger": "product_save"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "instagram-shop-master", "message": "Send a friendly DM to someone who saved an Instagram Shopping product. Acknowledge their interest. Answer potential questions. Offer a limited-time incentive to complete purchase."}},
                {"type": WorkflowActionType.ADD_TAG, "config": {"tag": "ig_shop_engaged"}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
        {
            "name": "🛒 Instagram Shop: Shop Tab Discovery Optimization",
            "description": "Optimización automática de productos para el algoritmo del Shop tab.",
            "trigger_type": WorkflowTriggerType.TAG_ADDED,
            "trigger_config": {"tag": "ig_shop_tab_audit"},
            "actions": [
                {"type": WorkflowActionType.AI_REPLY, "config": {"personality": "instagram-shop-master", "message": "Audit Instagram Shop tab products for algorithmic optimization. Check: image quality, description completeness, price competitiveness, and engagement signals. Recommend changes to boost discovery."}},
            ],
            "status": WorkflowStatus.DRAFT,
        },
    ]

    for wf_data in workflows:
        await get_or_create_workflow(db, business_id, wf_data["name"], **wf_data)

    # ========== PLATFORM EMAIL TEMPLATES ==========
    templates = [
        {
            "name": "Shopify Cart Recovery - Email 1",
            "subject": "🛍️ ¿Te olvidaste de algo? Te lo guardamos",
            "body_text": (
                "Hola {{lead_name}},\n\n"
                "Vimos que dejaste {{product_name}} en tu carrito.\n\n"
                "No te preocupes, lo guardamos por 24 horas más.\n\n"
                "[Completar compra ahora]\n\n"
                "Si tenés alguna duda, respondé este email o escribinos por WhatsApp.\n\n"
                "{{business_name}}"
            ),
            "body_html": (
                "<p>Hola {{lead_name}},</p>"
                "<p>Vimos que dejaste <strong>{{product_name}}</strong> en tu carrito.</p>"
                "<p><a href='{{checkout_url}}'>Completar compra ahora →</a></p>"
            ),
            "variables": ["lead_name", "product_name", "checkout_url", "business_name"],
            "category": "cart_recovery",
        },
        {
            "name": "Shopify Cart Recovery - Email 2 (Última chance)",
            "subject": "⏰ Últimas horas: tu carrito expira pronto",
            "body_text": (
                "Hola {{lead_name}},\n\n"
                "Quedan pocas horas antes de que liberemos tu carrito.\n\n"
                "{{product_name}} sigue esperándote.\n\n"
                "[Completar compra ahora]\n\n"
                "¿Tenés alguna pregunta? Estamos para ayudarte.\n\n"
                "{{business_name}}"
            ),
            "body_html": (
                "<p>Hola {{lead_name}},</p>"
                "<p>Quedan pocas horas antes de que liberemos tu carrito.</p>"
                "<p><a href='{{checkout_url}}'>Completar compra ahora →</a></p>"
            ),
            "variables": ["lead_name", "product_name", "checkout_url", "business_name"],
            "category": "cart_recovery",
        },
        {
            "name": "Shopify Win-Back - Email 1",
            "subject": "Te extrañamos 💙 Tenemos algo especial para vos",
            "body_text": (
                "Hola {{lead_name}},\n\n"
                "Hace un tiempo que no nos visitás.\n\n"
                "Queremos darte la bienvenida de vuelta con un 15% OFF en tu próxima compra.\n\n"
                "Código: VOLVER15\n\n"
                "[Ver novedades]\n\n"
                "{{business_name}}"
            ),
            "body_html": (
                "<p>Hola {{lead_name}},</p>"
                "<p>Hace un tiempo que no nos visitás.</p>"
                "<p><strong>Código: VOLVER15 (15% OFF)</strong></p>"
                "<p><a href='{{shop_url}}'>Ver novedades →</a></p>"
            ),
            "variables": ["lead_name", "shop_url", "business_name"],
            "category": "re_engagement",
        },
        {
            "name": "Hotmart Pre-Launch Day 1",
            "subject": "Algo grande viene... 🚀",
            "body_text": (
                "Hola {{lead_name}},\n\n"
                "En 7 días lanzamos algo que cambiará cómo {{pain_point}}.\n\n"
                "Estoy preparando este proyecto hace meses y quiero que seas de los primeros en saber.\n\n"
                "Mantenete atento/a a tu email.\n\n"
                "{{business_name}}"
            ),
            "body_html": (
                "<p>Hola {{lead_name}},</p>"
                "<p>En 7 días lanzamos algo que cambiará cómo {{pain_point}}.</p>"
                "<p>Mantenete atento/a.</p>"
            ),
            "variables": ["lead_name", "pain_point", "business_name"],
            "category": "hotmart_launch",
        },
        {
            "name": "Hotmart Pre-Launch Day 7 (Cart Open)",
            "subject": "🚪 Las puertas están abiertas",
            "body_text": (
                "Hola {{lead_name}},\n\n"
                "Llegó el día. Las puertas acaban de abrirse.\n\n"
                "Durante las próximas 48 horas, tenés acceso exclusivo con precio de lanzamiento.\n\n"
                "[Ver la oferta ahora]\n\n"
                "Después de eso, el precio sube y los bonos especiales desaparecen.\n\n"
                "{{business_name}}"
            ),
            "body_html": (
                "<p>Hola {{lead_name}},</p>"
                "<p>Las puertas acaban de abrirse.</p>"
                "<p><a href='{{offer_url}}'>Ver la oferta ahora →</a></p>"
            ),
            "variables": ["lead_name", "offer_url", "business_name"],
            "category": "hotmart_launch",
        },
    ]

    for tpl_data in templates:
        await get_or_create_template(db, business_id, tpl_data["name"], **tpl_data)

    # ========== PLATFORM EMAIL SEQUENCES ==========
    sequences = [
        {
            "name": "🛍️ Shopify: Cart Recovery Sequence (24h)",
            "description": "3 emails para recuperar carritos abandonados en Shopify.",
            "category": "shopify_cart_recovery",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "cart_abandoned",
        },
        {
            "name": "🛍️ Shopify: Win-Back Sequence (60 días)",
            "description": "2 emails para reactivar clientes inactivos de Shopify.",
            "category": "shopify_winback",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "tag_added",
        },
        {
            "name": "🎓 Hotmart: Pre-Launch Sequence (7 días)",
            "description": "Secuencia de emails pre-launch para productos digitales en Hotmart.",
            "category": "hotmart_launch",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "tag_added",
        },
        {
            "name": "📦 Amazon: Post-Purchase Review Sequence",
            "description": "Emails de respaldo para solicitar reviews en Amazon.",
            "category": "amazon_review",
            "status": WorkflowStatus.DRAFT,
            "trigger_type": "tag_added",
        },
    ]

    for seq_data in sequences:
        await get_or_create_sequence(db, business_id, seq_data["name"], **seq_data)

    # ========== PLATFORM CHATBOT RULES ==========
    rules = [
        {
            "name": "Platform: Consulta de Envío",
            "intent": "shipping",
            "keywords": ["envio", "shipping", "cuanto tarda", "donde esta mi pedido", "tracking", "seguimiento", "cuando llega", "🚚"],
            "response_template": "Te entiendo — querés saber cuándo llega tu pedido. 🚚\n\nSi ya compraste, podés trackearlo acá: {{tracking_url}}\n\nSi todavía no compraste, estos son nuestros tiempos de envío:\n• Envío standard: {{standard_shipping_time}}\n• Envío express: {{express_shipping_time}}\n\n¿Te gustaría que te reserve una unidad con envío express?",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Consulta de Stock / Disponibilidad",
            "intent": "availability",
            "keywords": ["tenes stock", "hay disponible", "disponibilidad", "hay", "queda", "stock", "cuando llega", "reponen"],
            "response_template": "Sí, tenemos stock disponible de {{product_name}}. 📦\n\nUnidades restantes: {{stock_count}}\n\nSi querés que te reserve una, confirmame y te paso el link de pago seguro. También puedo avisarte cuando vuelva a stock si se agota. ¿Te sirve?",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Devolución / Reembolso",
            "intent": "return",
            "keywords": ["devolucion", "reembolso", "quiero devolver", "no me sirvio", "cambio", "return", "refund", "garantia"],
            "response_template": "Lamento que necesites hacer una devolución. 😔\n\nNuestra política es simple: {{return_policy_days}} días para devolver sin preguntas.\n\nPara iniciar el proceso, necesito:\n1. Número de orden\n2. Motivo de la devolución\n3. ¿Preferís reembolso o cambio?\n\nUna vez que me pases esos datos, te envío la etiqueta de envío gratuita. Tu satisfacción es lo primero.",
            "response_type": "text",
            "priority": 25,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Garantía",
            "intent": "warranty",
            "keywords": ["garantia", "garantía", "funciona mal", "no funciona", "defecto", "warranty", "falla", "roto"],
            "response_template": "Entiendo tu preocupación. 🔧\n\nTodos nuestros productos tienen garantía de {{warranty_period}}.\n\nPara ayudarte rápido, necesito:\n1. Número de orden\n2. Descripción del problema\n3. Foto o video del defecto (si aplica)\n\nSi es un defecto de fábrica, te enviamos reemplazo inmediato sin costo. Si es daño por uso, te damos opciones de reparación con descuento. ¿Me pasás los datos?",
            "response_type": "text",
            "priority": 25,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Talla / Color / Especificación",
            "intent": "specs",
            "keywords": ["talla", "color", "medida", "dimension", "tamaño", "size", "colour", "specs", "especificaciones"],
            "response_template": "¡Buena pregunta! 📏\n\nAcá te paso las especificaciones de {{product_name}}:\n\n{{product_specs}}\n\nSi tenés dudas sobre qué talla/color te conviene, contame un poco más sobre qué buscás y te recomiendo la mejor opción.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Comparación de Productos",
            "intent": "comparison",
            "keywords": ["diferencia", "comparar", "cual es mejor", "vs", "versus", "que elegir", "recomendas"],
            "response_template": "¡Me encanta que quieras elegir lo mejor! 💡\n\nAcá va la comparación rápida:\n\n{{product_comparison}}\n\nMi recomendación depende de tu situación:\n• Si {{scenario_a}} → te recomiendo {{product_a}}\n• Si {{scenario_b}} → te recomiendo {{product_b}}\n\n¿Cuál se acerca más a lo que necesitás?",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Pedido Mayorista / B2B",
            "intent": "b2b",
            "keywords": ["mayorista", "mayor", "bulk", "b2b", "empresa", "negocio", "cantidad", "wholesale", "distribuidor"],
            "response_template": "¡Me encanta que estés interesado/a en compras al por mayor! 🏢\n\nOfrecemos precios especiales para pedidos mayores a {{min_bulk_quantity}} unidades.\n\nPara darte la mejor cotización, necesito saber:\n1. ¿Qué productos te interesan?\n2. ¿Qué cantidad aproximada necesitás?\n3. ¿Es para reventa o uso interno?\n4. ¿En qué país/ciudad estás?\n\nUna vez que me pases esos datos, te preparo una propuesta personalizada en 24 horas.",
            "response_type": "text",
            "priority": 25,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Descuento / Cupón",
            "intent": "discount",
            "keywords": ["descuento", "cupon", "codigo", "promo", "oferta", "más barato", "discount", "coupon", "code"],
            "response_template": "¡Claro que sí! 🎁\n\nAcá tenés nuestros descuentos activos:\n\n• {{active_discount_1}}\n• {{active_discount_2}}\n\nSi ninguno se ajusta a lo que buscás, contame qué producto te interesa y qué cantidad, y veo si puedo conseguirte algo especial.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Pedido Urgente / Express",
            "intent": "urgent",
            "keywords": ["urgente", "rapido", "hoy", "ya", "express", "prioritario", "lo necesito ya", " asap"],
            "response_template": "Entiendo que lo necesitás urgente. ⚡\n\nOpciones de envío express:\n• Same-day delivery: disponible en {{same_day_cities}} (pedir antes de las {{same_day_cutoff}})\n• Express 24-48h: disponible en todo el país\n\nEl costo de express es {{express_cost}}.\n\nSi confirmás ahora, puedo preparar tu pedido para despacho inmediato. ¿Te sirve?",
            "response_type": "text",
            "priority": 25,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Métodos de Pago",
            "intent": "payment",
            "keywords": ["pago", "metodo de pago", "tarjeta", "transferencia", "cuotas", "mercadopago", "stripe", "paypal", "efectivo"],
            "response_template": "Aceptamos todos estos métodos de pago seguros: 💳\n\n• Tarjetas de crédito y débito (Visa, Mastercard, Amex)\n• MercadoPago\n• Transferencia bancaria\n• PayPal\n• Cuotas sin interés con {{installment_provider}}\n\n¿Tenés preferencia por alguno? Si necesitás cuotas, te confirmo las opciones disponibles para tu tarjeta.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Estado de Orden",
            "intent": "order_status",
            "keywords": ["donde esta mi orden", "estado de mi pedido", "numero de orden", "tracking", "seguimiento", "mi compra", "cuando llega"],
            "response_template": "Te ayudo con tu pedido enseguida. 📦\n\n¿Me podés pasar tu número de orden? Así veo el estado exacto y te doy una fecha estimada de llegada.\n\nSi no tenés el número a mano, también puedo buscarlo con el email que usaste para comprar.",
            "response_type": "text",
            "priority": 20,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Recomendación de Producto",
            "intent": "recommendation",
            "keywords": ["que me recomendas", "que me sugeris", "no se que elegir", "ayuda para elegir", "recommend", "suggestion"],
            "response_template": "¡Con gusto te ayudo a elegir! 🎯\n\nContame un poco más:\n1. ¿Para quién es el producto? (vos, regalo, negocio)\n2. ¿Qué presupuesto tenés?\n3. ¿Hay algo específico que necesitás que haga?\n\nCon esos datos te doy mi recomendación honesta en 30 segundos.",
            "response_type": "text",
            "priority": 15,
            "channel_filter": [],
            "requires_human": False,
        },
        {
            "name": "Platform: Fallback General",
            "intent": "default",
            "keywords": [],
            "response_template": "Entiendo tu mensaje. Para darte la mejor respuesta posible, ¿podés contarme un poco más sobre qué estás buscando?\n\nPor ejemplo:\n• Info sobre precios 💰\n• Envío y tracking 🚚\n• Devoluciones y garantía 🛡️\n• Métodos de pago 💳\n• Recomendación de producto 🎯\n• Pedido mayorista / B2B 🏢\n\nElegí la opción que más te sirva o escribime directamente.",
            "response_type": "text",
            "priority": 0,
            "channel_filter": [],
            "requires_human": False,
        },
    ]

    for rule_data in rules:
        await get_or_create_chatbot_rule(db, business_id, rule_data["name"], **rule_data)

    await db.commit()
