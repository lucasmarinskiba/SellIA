"""SellIA Missions — Playbook Library

Playbooks predefinidos que SellIA puede ejecutar para resolver problemas
específicos de negocio. Cada playbook descompone un objetivo en pasos
executables en múltiples plataformas.
"""

from typing import List, Dict, Any, Optional
from .schemas import PlaybookRead, PlaybookStep


PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    # ─── Lanzamiento & Contenido ───────────────────────────────────────────────
    "instagram_launch": {
        "name": "Lanzamiento en Instagram",
        "description": "Crea perfil profesional, publica 9 posts, programa stories, activa Shopping",
        "category": "launch",
        "platforms": ["instagram", "shopify", "facebook"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "optimize_profile", "title": "Optimizar perfil de Instagram Business", "url_template": "https://instagram.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "connect_shopping", "title": "Conectar Instagram Shopping con catálogo Shopify", "url_template": "https://business.facebook.com/commerce", "requires_approval": True},
            {"platform": "api", "action_type": "create_content_calendar", "title": "Generar calendario de contenido (9 posts)", "params": {"platform": "instagram", "posts": 9, "include_stories": True}, "requires_approval": False},
            {"platform": "computer_use", "action_type": "schedule_posts", "title": "Programar primeros 3 posts en Creator Studio", "url_template": "https://business.facebook.com/creatorstudio", "requires_approval": False},
            {"platform": "api", "action_type": "send_welcome_dms", "title": "Enviar DMs de bienvenida a nuevos followers", "params": {"template": "welcome_dm"}, "requires_approval": True},
        ],
    },
    "tiktok_viral_launch": {
        "name": "Lanzamiento Viral TikTok",
        "description": "Crea cuenta TikTok Business, conecta TikTok Shop, publica 5 videos virales",
        "category": "launch",
        "platforms": ["tiktok", "tiktok_shop"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_business_account", "title": "Configurar TikTok Business Account", "url_template": "https://tiktok.com/business", "requires_approval": False},
            {"platform": "computer_use", "action_type": "connect_tiktok_shop", "title": "Conectar TikTok Shop y sincronizar catálogo", "url_template": "https://seller.tiktok.com", "requires_approval": True},
            {"platform": "api", "action_type": "generate_video_scripts", "title": "Generar 5 scripts de video viral", "params": {"count": 5, "style": "viral", "hook_types": ["problem_agitation", "storytelling", "transformation"]}, "requires_approval": False},
            {"platform": "computer_use", "action_type": "schedule_videos", "title": "Programar publicación de videos en TikTok", "url_template": "https://tiktok.com", "requires_approval": False},
        ],
    },
    # ─── SEO & Posicionamiento ─────────────────────────────────────────────────
    "google_local_seo": {
        "name": "Posicionamiento Local Google",
        "description": "Configura Google Business Profile, solicita reseñas, optimiza SEO local",
        "category": "seo",
        "platforms": ["google", "website"],
        "estimated_duration_minutes": 90,
        "steps": [
            {"platform": "computer_use", "action_type": "optimize_gbp", "title": "Configurar/optimizar Google Business Profile", "url_template": "https://business.google.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "add_local_keywords", "title": "Añadir keywords locales al sitio web", "url_template": "{user_website}", "requires_approval": True},
            {"platform": "api", "action_type": "request_reviews", "title": "Solicitar reseñas a clientes satisfechos", "params": {"via": "whatsapp", "template": "review_request", "max_per_day": 5}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "audit_local_competitors", "title": "Auditar competidores locales en Google Maps", "url_template": "https://google.com/maps", "requires_approval": False},
        ],
    },
    "seo_technical_audit": {
        "name": "Auditoría SEO Técnica",
        "description": "Audita y corrige problemas técnicos de SEO en el sitio web",
        "category": "seo",
        "platforms": ["website", "google"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "check_indexing", "title": "Verificar indexación en Google Search Console", "url_template": "https://search.google.com/search-console", "requires_approval": False},
            {"platform": "computer_use", "action_type": "audit_pagespeed", "title": "Auditar velocidad de página con PageSpeed", "url_template": "https://pagespeed.web.dev", "requires_approval": False},
            {"platform": "computer_use", "action_type": "fix_meta_tags", "title": "Corregir meta titles y descriptions faltantes", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "computer_use", "action_type": "generate_sitemap", "title": "Crear/generar sitemap.xml", "url_template": "{user_website}", "requires_approval": True},
            {"platform": "computer_use", "action_type": "fix_broken_links", "title": "Detectar y corregir links rotos", "url_template": "{user_website}", "requires_approval": True},
        ],
    },
    # ─── Publicidad ────────────────────────────────────────────────────────────
    "meta_ads_funnel": {
        "name": "Funnel de Ventas Meta Ads",
        "description": "Crea campaña de awareness + retargeting + conversión en Meta Ads",
        "category": "ads",
        "platforms": ["meta_ads", "instagram", "facebook"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "computer_use", "action_type": "create_campaign", "title": "Crear campaña de Awareness (alcance)", "url_template": "https://business.facebook.com/adsmanager", "params": {"objective": "AWARENESS", "budget": 10}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_campaign", "title": "Crear campaña de Retargeting (tráfico)", "url_template": "https://business.facebook.com/adsmanager", "params": {"objective": "TRAFFIC", "budget": 15, "audience": "website_visitors_30d"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_campaign", "title": "Crear campaña de Conversión (ventas)", "url_template": "https://business.facebook.com/adsmanager", "params": {"objective": "SALES", "budget": 25, "audience": "add_to_cart_7d"}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_pixel_events", "title": "Configurar eventos de Pixel", "params": {"events": ["PageView", "ViewContent", "AddToCart", "InitiateCheckout", "Purchase"]}, "requires_approval": True},
        ],
    },
    "google_ads_search": {
        "name": "Google Ads Search Express",
        "description": "Campaña de búsqueda en Google Ads con keywords de alto intento de compra",
        "category": "ads",
        "platforms": ["google_ads"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "research_keywords", "title": "Investigar keywords en Google Keyword Planner", "url_template": "https://ads.google.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "create_search_campaign", "title": "Crear campaña de búsqueda con 3 ad groups", "url_template": "https://ads.google.com", "params": {"ad_groups": 3, "budget_daily": 20}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_conversion_tracking", "title": "Configurar conversion tracking", "url_template": "https://ads.google.com", "requires_approval": True},
        ],
    },
    "tiktok_ads_launch": {
        "name": "Lanzamiento TikTok Ads",
        "description": "Crea campaña de video ads en TikTok para alcance + conversión",
        "category": "ads",
        "platforms": ["tiktok_ads", "tiktok"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_tiktok_ads_account", "title": "Configurar TikTok Ads Account", "url_template": "https://ads.tiktok.com", "requires_approval": False},
            {"platform": "api", "action_type": "generate_video_ad_creatives", "title": "Generar 3 creativos de video para ads", "params": {"count": 3, "duration": 15, "style": "native"}, "requires_approval": False},
            {"platform": "computer_use", "action_type": "create_tiktok_campaign", "title": "Crear campaña de conversión en TikTok Ads", "url_template": "https://ads.tiktok.com", "params": {"objective": "CONVERSIONS", "budget": 30}, "requires_approval": True},
        ],
    },
    # ─── Recuperación & Conversión ─────────────────────────────────────────────
    "cart_recovery_sequence": {
        "name": "Recuperación de Carritos Abandonados",
        "description": "Secuencia de 3 mensajes + cupón + urgencia en redes",
        "category": "recovery",
        "platforms": ["shopify", "whatsapp", "email", "instagram"],
        "estimated_duration_minutes": 60,
        "steps": [
            {"platform": "api", "action_type": "create_discount_code", "title": "Crear cupón de descuento 15%", "params": {"type": "percentage", "value": 15, "expires_in_hours": 24, "code_prefix": "VUELVE"}, "requires_approval": True},
            {"platform": "api", "action_type": "send_abandoned_cart_message", "title": "Enviar WhatsApp a carritos abandonados (1h)", "params": {"channel": "whatsapp", "delay_minutes": 60, "include_coupon": True}, "requires_approval": True},
            {"platform": "api", "action_type": "send_abandoned_cart_email", "title": "Enviar email de recuperación (4h)", "params": {"delay_hours": 4, "template": "abandoned_cart_v2", "include_coupon": True}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "post_urgency_story", "title": "Publicar story de 'últimas unidades' con cupón", "url_template": "https://instagram.com", "requires_approval": True},
        ],
    },
    "lead_nurture_sequence": {
        "name": "Secuencia de Nutrición de Leads",
        "description": "Secuencia de 5 touchpoints para convertir leads tibios en clientes",
        "category": "recovery",
        "platforms": ["email", "whatsapp", "instagram"],
        "estimated_duration_minutes": 90,
        "steps": [
            {"platform": "api", "action_type": "create_email_sequence", "title": "Crear secuencia de 5 emails de nutrición", "params": {"emails": 5, "spacing_days": [0, 2, 5, 8, 12], "objective": "nurture"}, "requires_approval": True},
            {"platform": "api", "action_type": "send_whatsapp_nurture", "title": "Enviar mensaje de valor por WhatsApp", "params": {"template": "value_proposition", "delay_hours": 24}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "engage_leads_ig", "title": "Responder stories y DMs de leads en Instagram", "url_template": "https://instagram.com", "requires_approval": False},
        ],
    },
    # ─── Expansión & Logística ─────────────────────────────────────────────────
    "cross_border_expansion": {
        "name": "Expansión Cross-Border",
        "description": "Prepara el negocio para vender en país vecino (Brasil, Chile, Uruguay, México)",
        "category": "expansion",
        "platforms": ["mercadolibre", "amazon", "dhl", "fedex"],
        "estimated_duration_minutes": 240,
        "steps": [
            {"platform": "api", "action_type": "translate_catalog", "title": "Traducir catálogo al idioma del país destino", "params": {"target_language": "pt", "platform": "mercadolibre"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_ml_listing", "title": "Crear publicación en MercadoLibre de país destino", "url_template": "https://mercadolibre.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_international_shipping", "title": "Configurar envío internacional DHL/FedEx", "url_template": "https://dhl.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "adjust_pricing", "title": "Ajustar precios con impuestos de importación", "url_template": "https://mercadolibre.com", "requires_approval": True},
            {"platform": "api", "action_type": "update_inventory_sync", "title": "Activar sincronización de stock multi-país", "params": {"sync_mode": "centralized"}, "requires_approval": True},
        ],
    },
    "local_delivery_setup": {
        "name": "Configuración de Envío Local",
        "description": "Configura envíos locales con múltiples carriers y zonas de cobertura",
        "category": "logistics",
        "platforms": ["andreani", "oca", "shopify", "mercadolibre"],
        "estimated_duration_minutes": 90,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_andreani", "title": "Configurar cuenta Andreani y cotizador", "url_template": "https://andreani.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_oca", "title": "Configurar cuenta OCA", "url_template": "https://oca.com.ar", "requires_approval": True},
            {"platform": "api", "action_type": "configure_shipping_zones", "title": "Configurar zonas de envío en Shopify/ML", "params": {"zones": ["caba", "gba", "interior", "internacional"]}, "requires_approval": True},
            {"platform": "api", "action_type": "set_shipping_rules", "title": "Reglas de envío gratis + express", "params": {"free_shipping_threshold": 25000, "express_surcharge": 15}, "requires_approval": True},
        ],
    },
    # ─── Branding ──────────────────────────────────────────────────────────────
    "brand_identity_refresh": {
        "name": "Renovación de Identidad de Marca",
        "description": "Actualiza logo, colores, bio y branding en todas las redes",
        "category": "branding",
        "platforms": ["instagram", "facebook", "linkedin", "tiktok", "website"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "api", "action_type": "generate_brand_kit", "title": "Generar Brand Kit con IA", "params": {"include": ["logo", "colors", "fonts", "bio", "tagline", "brand_voice"]}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "update_instagram_branding", "title": "Actualizar perfil de Instagram con nuevo branding", "url_template": "https://instagram.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "update_facebook_branding", "title": "Actualizar perfil de Facebook", "url_template": "https://facebook.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "update_linkedin_branding", "title": "Actualizar perfil de LinkedIn", "url_template": "https://linkedin.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "update_website_branding", "title": "Actualizar branding del sitio web", "url_template": "{user_website}/admin", "requires_approval": True},
        ],
    },
    "influencer_outreach": {
        "name": "Outreach a Micro-Influencers",
        "description": "Encuentra y contacta micro-influencers del nicho para colaboraciones",
        "category": "branding",
        "platforms": ["instagram", "tiktok", "email"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "search_instagram_influencers", "title": "Buscar micro-influencers en Instagram por hashtag", "url_template": "https://instagram.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "search_tiktok_influencers", "title": "Buscar micro-influencers en TikTok por hashtag", "url_template": "https://tiktok.com", "requires_approval": False},
            {"platform": "api", "action_type": "send_outreach_emails", "title": "Enviar emails de propuesta de colaboración", "params": {"template": "collaboration_proposal", "max_per_day": 10}, "requires_approval": True},
        ],
    },
    # ─── Automatización ────────────────────────────────────────────────────────
    "full_automation_setup": {
        "name": "Automatización Completa del Negocio",
        "description": "Configura automatizaciones end-to-end: respuestas IA, seguimiento, reportes",
        "category": "automation",
        "platforms": ["whatsapp", "instagram", "email", "shopify", "mercadolibre"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "api", "action_type": "setup_chatbot_rules", "title": "Configurar reglas de chatbot IA para cada canal", "params": {"channels": ["whatsapp", "instagram", "email"], "auto_reply": True}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_followup_sequences", "title": "Activar secuencias de follow-up automáticas", "params": {"triggers": ["no_reply_24h", "quote_sent", "meeting_booked"]}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_daily_reports", "title": "Configurar reportes diarios automáticos", "params": {"channels": ["whatsapp", "email"], "time": "09:00"}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_stock_alerts", "title": "Alertas de stock bajo y reposición automática", "params": {"threshold": 5}, "requires_approval": True},
        ],
    },
    # ─── Consultoría/Coaching ──────────────────────────────────────────────────
    "consulting_b2b_lead_gen": {
        "name": "Lead Gen B2B para Consultoría",
        "description": "Genera leads B2B mediante LinkedIn Sales Navigator, contenido de valor y secuencias de outreach",
        "category": "business_type",
        "platforms": ["linkedin", "email", "website"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "optimize_linkedin_profile", "title": "Optimizar perfil de LinkedIn para conversión", "url_template": "https://linkedin.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "setup_sales_navigator", "title": "Configurar búsquedas guardadas en Sales Navigator", "url_template": "https://linkedin.com/sales", "requires_approval": False},
            {"platform": "api", "action_type": "generate_lead_magnet", "title": "Crear lead magnet PDF (guía/caso de estudio)", "params": {"type": "pdf", "topic": "industry_insights"}, "requires_approval": True},
            {"platform": "api", "action_type": "send_connection_requests", "title": "Enviar solicitudes de conexión personalizadas", "params": {"max_per_day": 20, "follow_up_days": [3, 7]}, "requires_approval": True},
            {"platform": "api", "action_type": "create_email_sequence", "title": "Crear secuencia de nutrición B2B (5 emails)", "params": {"emails": 5, "spacing_days": [0, 3, 7, 14, 21], "objective": "nurture"}, "requires_approval": True},
        ],
    },
    "consulting_calendly_booking": {
        "name": "Funnel de Agendamiento Calendly",
        "description": "Configura Calendly/integraciones para convertir consultas en reuniones agendadas",
        "category": "business_type",
        "platforms": ["calendly", "website", "linkedin", "email"],
        "estimated_duration_minutes": 90,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_calendly", "title": "Configurar eventos y disponibilidad en Calendly", "url_template": "https://calendly.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "embed_calendly", "title": "Insertar widget Calendly en sitio web", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "setup_reminders", "title": "Configurar recordatorios WhatsApp + email previos a reunión", "params": {"reminders": ["24h", "1h"]}, "requires_approval": True},
            {"platform": "api", "action_type": "create_post_meeting_sequence", "title": "Crear secuencia post-reunión (propuesta + seguimiento)", "params": {"emails": 3, "spacing_days": [0, 3, 7]}, "requires_approval": True},
        ],
    },
    # ─── Software/SaaS/Apps ────────────────────────────────────────────────────
    "saas_product_hunt_launch": {
        "name": "Lanzamiento en Product Hunt",
        "description": "Prepara y ejecuta un lanzamiento exitoso en Product Hunt para SaaS",
        "category": "business_type",
        "platforms": ["product_hunt", "twitter", "linkedin", "email"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "computer_use", "action_type": "create_ph_listing", "title": "Crear listing en Product Hunt con imágenes y video", "url_template": "https://www.producthunt.com/dashboard", "requires_approval": True},
            {"platform": "api", "action_type": "generate_launch_copy", "title": "Generar copy de lanzamiento (tagline, description, first comment)", "params": {"tone": "exciting", "include_gallery": True}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "schedule_launch_day_posts", "title": "Programar posts de apoyo en Twitter/X y LinkedIn", "url_template": "https://twitter.com", "requires_approval": True},
            {"platform": "api", "action_type": "send_launch_email", "title": "Enviar email a early adopters invitando a upvotear", "params": {"segment": "early_adopters"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "engage_comments", "title": "Responder comentarios en tiempo real durante el launch", "url_template": "https://www.producthunt.com", "requires_approval": False},
        ],
    },
    "saas_app_store_optimization": {
        "name": "App Store Optimization (ASO)",
        "description": "Optimiza listing de app en App Store y Google Play para maximizar descargas",
        "category": "business_type",
        "platforms": ["app_store", "google_play", "website"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "research_aso_keywords", "title": "Investigar keywords de alto volumen y baja competencia", "url_template": "https://appfollow.io", "requires_approval": False},
            {"platform": "api", "action_type": "optimize_metadata", "title": "Optimizar título, subtítulo y keywords del listing", "params": {"stores": ["app_store", "google_play"]}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_screenshots", "title": "Generar screenshots y preview video con copy", "params": {"count": 5, "include_preview": True}, "requires_approval": True},
            {"platform": "api", "action_type": "request_app_reviews", "title": "Solicitar reviews in-app a usuarios activos", "params": {"trigger": "after_3_sessions"}, "requires_approval": True},
        ],
    },
    "saas_demo_scheduling": {
        "name": "Funnel de Demo Scheduling SaaS",
        "description": "Configura funnel para que visitantes agenden demo del producto",
        "category": "business_type",
        "platforms": ["website", "calendly", "meta_ads", "email"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "create_demo_landing_page", "title": "Crear landing page de demo con formulario", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_meta_conversion_campaign", "title": "Crear campaña de conversión Meta Ads para demos", "url_template": "https://business.facebook.com/adsmanager", "params": {"objective": "LEAD_GENERATION", "budget": 30}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_demo_reminders", "title": "Configurar recordatorios y secuencia post-demo", "params": {"reminders": ["24h", "1h"], "follow_up_emails": 3}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "add_demo_cta", "title": "Añadir CTAs de 'Agendar Demo' en sitio y emails", "url_template": "{user_website}", "requires_approval": True},
        ],
    },
    # ─── Servicios Profesionales ───────────────────────────────────────────────
    "pro_services_portfolio": {
        "name": "Portfolio Profesional de Servicios",
        "description": "Construye un portfolio atractivo con casos de éxito, testimonios y métricas",
        "category": "business_type",
        "platforms": ["website", "instagram", "linkedin"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "api", "action_type": "generate_case_studies", "title": "Generar 3 case studies con estructura problema-solución-resultado", "params": {"count": 3, "format": "web"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_portfolio_page", "title": "Crear página de portfolio en el sitio web", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "design_portfolio_pdf", "title": "Diseñar PDF de portfolio descargable", "params": {"pages": 6}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "share_portfolio", "title": "Publicar carrusel de proyectos en Instagram y LinkedIn", "url_template": "https://instagram.com", "requires_approval": True},
        ],
    },
    "pro_services_testimonials": {
        "name": "Colección de Testimonios Profesionales",
        "description": "Solicita, organiza y publica testimonios de clientes satisfechos",
        "category": "business_type",
        "platforms": ["google", "linkedin", "website", "whatsapp"],
        "estimated_duration_minutes": 90,
        "steps": [
            {"platform": "api", "action_type": "send_testimonial_requests", "title": "Enviar solicitudes de testimonio vía WhatsApp/email", "params": {"template": "testimonial_request", "max_per_day": 5}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_google_review_link", "title": "Generar enlace directo para reseñas en Google", "url_template": "https://business.google.com", "requires_approval": False},
            {"platform": "api", "action_type": "generate_testimonial_graphics", "title": "Crear gráficas de testimonios para redes sociales", "params": {"count": 5, "style": "professional"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "embed_testimonials", "title": "Incrustar testimonios en sitio web", "url_template": "{user_website}/admin", "requires_approval": True},
        ],
    },
    "pro_services_local_ads": {
        "name": "Local Service Ads para Profesionales",
        "description": "Configura Google Local Service Ads para captar clientes locales",
        "category": "business_type",
        "platforms": ["google_ads", "google", "website"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_local_services_account", "title": "Crear cuenta de Google Local Services", "url_template": "https://ads.google.com/localservices", "requires_approval": True},
            {"platform": "computer_use", "action_type": "verify_business", "title": "Completar verificación de negocio y licencias", "url_template": "https://ads.google.com/localservices", "requires_approval": True},
            {"platform": "computer_use", "action_type": "set_weekly_budget", "title": "Definir presupuesto semanal y zonas de servicio", "url_template": "https://ads.google.com/localservices", "requires_approval": True},
            {"platform": "api", "action_type": "setup_review_requests", "title": "Solicitar reviews a clientes atendidos vía LSAs", "params": {"via": "email"}, "requires_approval": True},
        ],
    },
    # ─── Restaurantes/Food ─────────────────────────────────────────────────────
    "restaurant_delivery_apps": {
        "name": "Presencia en Apps de Delivery",
        "description": "Configura y optimiza perfiles en PedidosYa, Rappi, UberEats y MercadoLibre",
        "category": "business_type",
        "platforms": ["pedidosya", "rappi", "ubereats", "mercadolibre"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "create_delivery_profiles", "title": "Crear/optimizar perfiles en cada app de delivery", "url_template": "https://partners.pedidosya.com", "requires_approval": True},
            {"platform": "api", "action_type": "generate_menu_photos", "title": "Generar fotos de menú profesionales con IA", "params": {"count": 12, "style": "food_photography"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_promotions", "title": "Configurar promociones de primer pedido y combos", "url_template": "https://partners.pedidosya.com", "requires_approval": True},
            {"platform": "api", "action_type": "sync_inventory", "title": "Sincronizar disponibilidad de menú entre plataformas", "params": {"platforms": ["pedidosya", "rappi", "ubereats"]}, "requires_approval": True},
        ],
    },
    "restaurant_instagram_food": {
        "name": "Contenido Food para Instagram",
        "description": "Crea y programa contenido visual de platos, behind-the-scenes y UGC",
        "category": "business_type",
        "platforms": ["instagram", "tiktok"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "api", "action_type": "generate_content_calendar", "title": "Generar calendario mensual de contenido food (15 posts)", "params": {"posts": 15, "include_reels": True, "themes": ["plato_estrella", "behind_scenes", "ugc", "chef_special"]}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_reel_scripts", "title": "Generar 5 scripts de Reels/TikTok food", "params": {"count": 5, "hooks": ["satisfying", "recipe", "trend"]}, "requires_approval": False},
            {"platform": "computer_use", "action_type": "schedule_posts", "title": "Programar posts y reels en Meta Business Suite", "url_template": "https://business.facebook.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "engage_ugc", "title": "Compartir stories de clientes y responder menciones", "url_template": "https://instagram.com", "requires_approval": False},
        ],
    },
    "restaurant_local_seo": {
        "name": "SEO Local para Restaurantes",
        "description": "Domina búsquedas locales de restaurantes con Google Business, reseñas y menú digital",
        "category": "business_type",
        "platforms": ["google", "website", "instagram"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "optimize_gbp_restaurant", "title": "Optimizar Google Business Profile con menú, horarios y fotos", "url_template": "https://business.google.com", "requires_approval": True},
            {"platform": "api", "action_type": "generate_menu_schema", "title": "Crear schema.org de menú para SEO local", "params": {"format": "json_ld"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "add_local_keywords", "title": "Añadir keywords locales al sitio (ciudad + tipo de comida)", "url_template": "{user_website}", "requires_approval": True},
            {"platform": "api", "action_type": "request_reviews", "title": "Solicitar reseñas a comensales post-visita", "params": {"via": "whatsapp", "template": "restaurant_review", "delay_hours": 2}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "audit_local_competitors", "title": "Auditar restaurantes competidores en Google Maps", "url_template": "https://google.com/maps", "requires_approval": False},
        ],
    },
    # ─── Fashion/Beauty ────────────────────────────────────────────────────────
    "fashion_visual_content": {
        "name": "Contenido Visual Fashion & Beauty",
        "description": "Crea lookbooks digitales, reels de outfit y contenido beauty para Instagram/TikTok",
        "category": "business_type",
        "platforms": ["instagram", "tiktok", "pinterest"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "api", "action_type": "generate_lookbook", "title": "Generar lookbook digital de temporada (8 outfits)", "params": {"outfits": 8, "format": "carousel"}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_reel_scripts", "title": "Generar scripts de Reels/TikTok (GRWM, haul, styling)", "params": {"count": 5, "style": "fashion_beauty"}, "requires_approval": False},
            {"platform": "computer_use", "action_type": "schedule_visual_content", "title": "Programar publicaciones en Instagram, TikTok y Pinterest", "url_template": "https://business.facebook.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "setup_instagram_shopping", "title": "Etiquetar productos en posts y stories (Shopping)", "url_template": "https://business.facebook.com/commerce", "requires_approval": True},
        ],
    },
    "fashion_influencer_collabs": {
        "name": "Colaboraciones con Influencers Fashion",
        "description": "Identifica, contacta y gestiona colaboraciones con micro/macro influencers del nicho",
        "category": "business_type",
        "platforms": ["instagram", "tiktok", "email"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "computer_use", "action_type": "search_fashion_influencers", "title": "Buscar influencers por nicho, seguidores y engagement", "url_template": "https://instagram.com", "requires_approval": False},
            {"platform": "api", "action_type": "generate_collab_proposal", "title": "Generar propuesta de colaboración personalizada", "params": {"template": "fashion_collab", "include_brief": True}, "requires_approval": True},
            {"platform": "api", "action_type": "send_outreach_emails", "title": "Enviar propuestas a influencers seleccionados", "params": {"template": "influencer_outreach", "max_per_day": 8}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "track_collaborations", "title": "Crear tracker de entregables y métricas de colabs", "url_template": "https://docs.google.com", "requires_approval": False},
        ],
    },
    "fashion_lookbook": {
        "name": "Lookbook Digital de Temporada",
        "description": "Crea un lookbook digital interactivo con productos enlazados al e-commerce",
        "category": "business_type",
        "platforms": ["website", "instagram", "pinterest"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "api", "action_type": "generate_lookbook_pages", "title": "Generar páginas de lookbook con copy y productos", "params": {"pages": 10, "style": "seasonal"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_lookbook_page", "title": "Publicar lookbook en sitio web (lookbook/season)", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "generate_pinterest_pins", "title": "Crear pins de Pinterest para cada look", "params": {"count": 10, "size": "1000x1500"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "promote_lookbook", "title": "Promocionar lookbook en Instagram Stories y Reels", "url_template": "https://instagram.com", "requires_approval": True},
        ],
    },
    # ─── Health/Wellness ───────────────────────────────────────────────────────
    "wellness_appointment_booking": {
        "name": "Sistema de Turnos Online Wellness",
        "description": "Configura reservas online para clínicas, spas, gimnasios o consultorios",
        "category": "business_type",
        "platforms": ["website", "whatsapp", "google", "calendly"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_booking_system", "title": "Configurar sistema de turnos en el sitio web", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "setup_whatsapp_booking", "title": "Activar reserva de turnos vía WhatsApp Business", "params": {"flow": "appointment_booking"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "add_booking_cta_gbp", "title": "Añadir botón de reserva en Google Business Profile", "url_template": "https://business.google.com", "requires_approval": True},
            {"platform": "api", "action_type": "setup_appointment_reminders", "title": "Configurar recordatorios automáticos (24h + 1h)", "params": {"channels": ["whatsapp", "email"]}, "requires_approval": True},
        ],
    },
    "wellness_testimonial_videos": {
        "name": "Videos Testimonio para Wellness",
        "description": "Solicita, edita y publica videos testimonio de pacientes/clientes satisfechos",
        "category": "business_type",
        "platforms": ["instagram", "tiktok", "youtube", "website"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "api", "action_type": "send_video_testimonial_request", "title": "Solicitar videos testimonio a clientes (guía + incentivo)", "params": {"via": "whatsapp", "template": "video_testimonial_request"}, "requires_approval": True},
            {"platform": "api", "action_type": "edit_testimonial_videos", "title": "Editar videos con intro, música y subtítulos", "params": {"style": "professional", "max_duration": 60}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "publish_testimonials", "title": "Publicar videos en Instagram Reels, TikTok y YouTube Shorts", "url_template": "https://instagram.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "embed_video_testimonials", "title": "Incrustar videos de testimonios en sitio web", "url_template": "{user_website}/admin", "requires_approval": True},
        ],
    },
    "wellness_community": {
        "name": "Comunidad Online Wellness",
        "description": "Crea y gestiona comunidad en WhatsApp, Telegram o Discord para retención",
        "category": "business_type",
        "platforms": ["whatsapp", "telegram", "instagram", "email"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "api", "action_type": "create_community_group", "title": "Crear grupo/comunidad exclusiva para clientes", "params": {"platform": "whatsapp", "name": "Comunidad VIP"}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_weekly_content", "title": "Generar plan de contenido semanal para la comunidad", "params": {"posts_per_week": 5, "types": ["tips", "challenges", "live_qa"]}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_welcome_sequence", "title": "Configurar mensaje de bienvenida y onboarding", "params": {"messages": 3, "delay_hours": [0, 24, 72]}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "promote_community", "title": "Promocionar comunidad en redes e email", "url_template": "https://instagram.com", "requires_approval": True},
        ],
    },
    # ─── Home/Decor ────────────────────────────────────────────────────────────
    "home_decor_pinterest_seo": {
        "name": "Pinterest SEO para Home & Decor",
        "description": "Optimiza perfil, boards y pins para captar tráfico desde Pinterest",
        "category": "business_type",
        "platforms": ["pinterest", "website"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "optimize_pinterest_profile", "title": "Optimizar perfil de Pinterest Business con keywords", "url_template": "https://pinterest.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "create_seo_boards", "title": "Crear boards organizados por categoría y keywords", "url_template": "https://pinterest.com", "requires_approval": True},
            {"platform": "api", "action_type": "generate_pinterest_pins", "title": "Generar 15 pins optimizados con keywords y URLs", "params": {"count": 15, "size": "1000x1500", "include_rich_pins": True}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "schedule_pins", "title": "Programar pins con Tailwind o Pinterest Native", "url_template": "https://pinterest.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "enable_rich_pins", "title": "Activar Rich Pins desde el sitio web", "url_template": "{user_website}", "requires_approval": True},
        ],
    },
    "home_decor_before_after": {
        "name": "Contenido Before/After Home",
        "description": "Crea y publica contenido de transformaciones para Instagram, TikTok y Pinterest",
        "category": "business_type",
        "platforms": ["instagram", "tiktok", "pinterest", "website"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "api", "action_type": "generate_before_after_assets", "title": "Generar gráficas before/after con copy persuasivo", "params": {"count": 8, "style": "transformation"}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_reel_scripts", "title": "Generar scripts de Reels/TikTok de transformaciones", "params": {"count": 4, "hook": "antes_y_despues"}, "requires_approval": False},
            {"platform": "computer_use", "action_type": "schedule_content", "title": "Programar carruseles, reels y pins de before/after", "url_template": "https://business.facebook.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "create_portfolio_page", "title": "Crear página de proyectos antes/después en el sitio", "url_template": "{user_website}/admin", "requires_approval": True},
        ],
    },
    "home_decor_local_showroom": {
        "name": "Showroom Local Home & Decor",
        "description": "Atrae visitas al showroom local con Google Maps, eventos y contenido geo-targeteado",
        "category": "business_type",
        "platforms": ["google", "instagram", "website", "meta_ads"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "optimize_gbp_showroom", "title": "Optimizar Google Business Profile con fotos 360 y horarios", "url_template": "https://business.google.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_local_event", "title": "Crear evento de inauguración/showroom en Facebook/Instagram", "url_template": "https://facebook.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_local_awareness_ads", "title": "Crear campaña de awareness local en Meta Ads", "url_template": "https://business.facebook.com/adsmanager", "params": {"objective": "AWARENESS", "radius_km": 15}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_local_content", "title": "Generar contenido geo-targeteado (ciudad + barrio)", "params": {"posts": 6, "include_stories": True}, "requires_approval": True},
        ],
    },
    # ─── Artesanías/Handcraft ──────────────────────────────────────────────────
    "handcraft_etsy_setup": {
        "name": "Tienda Etsy para Artesanías",
        "description": "Crea y optimiza tienda Etsy con SEO, fotos y políticas de envío",
        "category": "business_type",
        "platforms": ["etsy", "website", "pinterest"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "computer_use", "action_type": "create_etsy_shop", "title": "Crear tienda Etsy con banner, about y políticas", "url_template": "https://www.etsy.com/sell", "requires_approval": True},
            {"platform": "api", "action_type": "optimize_etsy_listings", "title": "Optimizar títulos, tags y descripciones para Etsy SEO", "params": {"listings": 10}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_product_photos", "title": "Generar fotos de producto estilo lifestyle y flatlay", "params": {"count": 20, "style": "handcraft"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_etsy_ads", "title": "Configurar Etsy Ads con presupuesto diario", "url_template": "https://www.etsy.com", "params": {"budget_daily": 5}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "connect_pinterest_etsy", "title": "Conectar Pinterest con catálogo de Etsy", "url_template": "https://pinterest.com", "requires_approval": True},
        ],
    },
    "handcraft_mercadolibre": {
        "name": "MercadoLibre para Artesanías",
        "description": "Publica artesanías en MercadoLibre con fotos, descripciones SEO y envío MercadoEnvíos",
        "category": "business_type",
        "platforms": ["mercadolibre", "mercadopago"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "create_ml_listings", "title": "Crear publicaciones en MercadoLibre (título, fotos, descripción)", "url_template": "https://mercadolibre.com", "requires_approval": True},
            {"platform": "api", "action_type": "optimize_ml_seo", "title": "Optimizar títulos y descripciones para búsqueda ML", "params": {"listings": 10}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_mercadoenvios", "title": "Configurar MercadoEnvíos y etiquetas", "url_template": "https://mercadolibre.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_mercadopago", "title": "Configurar MercadoPago y cuotas sin interés", "url_template": "https://mercadopago.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_ml_ads", "title": "Crear campañas de publicidad dentro de MercadoLibre", "url_template": "https://ads.mercadolibre.com", "requires_approval": True},
        ],
    },
    "handcraft_storytelling": {
        "name": "Storytelling para Artesanías",
        "description": "Crea contenido narrativo que cuente la historia detrás de cada pieza artesanal",
        "category": "business_type",
        "platforms": ["instagram", "tiktok", "website", "email"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "api", "action_type": "generate_origin_story", "title": "Generar historia de marca y origen del artesano", "params": {"format": "long_form", "include_video_script": True}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_product_stories", "title": "Crear storytelling para 5 productos estrella", "params": {"count": 5, "style": "emotional"}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_reel_scripts", "title": "Generar scripts de Reels/TikTok (proceso creativo)", "params": {"count": 4, "hook": "making_of"}, "requires_approval": False},
            {"platform": "computer_use", "action_type": "publish_storytelling_blog", "title": "Publicar blog de historia de marca en el sitio", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "create_email_sequence", "title": "Crear secuencia de email storytelling (bienvenida)", "params": {"emails": 4, "objective": "storytelling"}, "requires_approval": True},
        ],
    },
    # ─── Geographic Reach ──────────────────────────────────────────────────────
    "regional_expansion": {
        "name": "Expansión Regional Multi-Ciudad",
        "description": "Expande tu negocio a múltiples ciudades de la misma provincia/región",
        "category": "expansion",
        "platforms": ["meta_ads", "google_ads", "website"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "create_regional_landing_pages", "title": "Crear landing pages por ciudad con contenido localizado", "url_template": "{user_website}/admin", "params": {"cities": 3}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_regional_ads", "title": "Configurar campañas geo-targeteadas por ciudad", "url_template": "https://business.facebook.com/adsmanager", "params": {"objective": "AWARENESS", "cities": 3}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_google_local_ads", "title": "Crear campañas de búsqueda local por ciudad", "url_template": "https://ads.google.com", "requires_approval": True},
            {"platform": "api", "action_type": "generate_local_content", "title": "Generar contenido específico para cada ciudad", "params": {"cities": 3, "posts_per_city": 3}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_regional_shipping", "title": "Configurar zonas de envío regionales", "params": {"zones": ["provincia", "region"]}, "requires_approval": True},
        ],
    },
    "national_expansion": {
        "name": "Expansión Nacional",
        "description": "Escala a nivel país con envíos nacionales, marketplaces y ads nacional",
        "category": "expansion",
        "platforms": ["mercadolibre", "meta_ads", "google_ads", "website"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_national_shipping", "title": "Configurar envío a todo el país con múltiples carriers", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_national_marketplace_listings", "title": "Crear publicaciones en marketplaces nacionales", "url_template": "https://mercadolibre.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_national_ads", "title": "Crear campañas nacionales en Meta y Google", "url_template": "https://business.facebook.com/adsmanager", "requires_approval": True},
            {"platform": "api", "action_type": "generate_national_campaign", "title": "Generar campaña de lanzamiento nacional", "params": {"channels": ["email", "social", "ads"], "duration_days": 14}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_inventory_sync", "title": "Sincronizar inventario nacional centralizado", "params": {"sync_mode": "national"}, "requires_approval": True},
        ],
    },
    "cross_border_latam": {
        "name": "Cross-Border LATAM",
        "description": "Vende en Brasil, Chile, Uruguay, México y Colombia con logística y pagos locales",
        "category": "expansion",
        "platforms": ["mercadolibre", "amazon", "dhl", "fedex", "stripe"],
        "estimated_duration_minutes": 240,
        "steps": [
            {"platform": "api", "action_type": "translate_catalog", "title": "Traducir catálogo a portugués y español neutro", "params": {"languages": ["pt", "es"], "platforms": ["mercadolibre", "amazon"]}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_cross_border_listings", "title": "Crear publicaciones en ML Brasil, Chile, México, Colombia", "url_template": "https://mercadolibre.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_cross_border_shipping", "title": "Configurar envío cross-border DHL/FedEx", "url_template": "https://dhl.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_local_payments", "title": "Configurar pagos locales (Stripe, MercadoPago, PayPal)", "url_template": "https://stripe.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "adjust_pricing_taxes", "title": "Ajustar precios con impuestos de importación y shipping", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "setup_multi_country_inventory", "title": "Activar sincronización de stock multi-país", "params": {"countries": ["BR", "CL", "UY", "MX", "CO"]}, "requires_approval": True},
        ],
    },
    "global_expansion": {
        "name": "Expansión Global",
        "description": "Vende internacionalmente con multi-idioma, shipping global y ads internacionales",
        "category": "expansion",
        "platforms": ["amazon", "shopify", "google_ads", "meta_ads", "dhl", "fedex"],
        "estimated_duration_minutes": 240,
        "steps": [
            {"platform": "api", "action_type": "translate_website", "title": "Traducir sitio web a inglés, español y portugués", "params": {"languages": ["en", "es", "pt"]}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_international_shipping", "title": "Configurar envío internacional DHL/FedEx/UPS", "url_template": "https://dhl.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_global_marketplace_accounts", "title": "Crear cuentas en Amazon US/EU y eBay", "url_template": "https://sellercentral.amazon.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_global_ads", "title": "Configurar campañas globales en Meta y Google", "url_template": "https://business.facebook.com/adsmanager", "requires_approval": True},
            {"platform": "api", "action_type": "setup_multi_currency", "title": "Activar multi-moneda en checkout", "params": {"currencies": ["USD", "EUR", "BRL", "MXN"]}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_global_tax", "title": "Configurar impuestos y compliance internacional", "params": {"regions": ["US", "EU", "LATAM"]}, "requires_approval": True},
        ],
    },
    # ─── Marketing: SEO ────────────────────────────────────────────────────────
    "seo_on_page": {
        "name": "SEO On-Page Completo",
        "description": "Optimiza títulos, meta descriptions, headings, URLs, schema markup y contenido",
        "category": "seo",
        "platforms": ["website", "google"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "audit_on_page", "title": "Auditar SEO on-page con Screaming Frog/Sitebulb", "url_template": "https://www.screamingfrog.co.uk", "requires_approval": False},
            {"platform": "api", "action_type": "optimize_titles_meta", "title": "Optimizar meta titles y descriptions de todas las páginas", "params": {"max_length_title": 60, "max_length_desc": 160}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "fix_headings_structure", "title": "Corregir estructura de headings H1-H6", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "add_schema_markup", "title": "Añadir schema markup (Product, LocalBusiness, FAQ)", "params": {"schemas": ["Product", "LocalBusiness", "FAQPage"]}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "optimize_internal_links", "title": "Optimizar estructura de internal linking", "url_template": "{user_website}", "requires_approval": True},
            {"platform": "computer_use", "action_type": "optimize_images", "title": "Optimizar alt text, compresión y lazy loading de imágenes", "url_template": "{user_website}/admin", "requires_approval": True},
        ],
    },
    "seo_off_page": {
        "name": "SEO Off-Page & Link Building",
        "description": "Construye backlinks de calidad, guest posts y citaciones locales",
        "category": "seo",
        "platforms": ["website", "google"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "computer_use", "action_type": "audit_backlinks", "title": "Auditar perfil de backlinks actual", "url_template": "https://ahrefs.com", "requires_approval": False},
            {"platform": "api", "action_type": "generate_guest_post_outreach", "title": "Generar lista de sitios y emails para guest posts", "params": {"niche": "auto", "count": 20}, "requires_approval": True},
            {"platform": "api", "action_type": "send_guest_post_emails", "title": "Enviar propuestas de guest post", "params": {"template": "guest_post", "max_per_day": 5}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "submit_local_directories", "title": "Enviar negocio a directorios locales relevantes", "url_template": "https://google.com", "requires_approval": False},
            {"platform": "api", "action_type": "create_linkable_asset", "title": "Crear asset linkable (infografía, estudio, herramienta)", "params": {"type": "infographic"}, "requires_approval": True},
        ],
    },
    # ─── Marketing: SEM/Ads ────────────────────────────────────────────────────
    "sem_google_display_shopping": {
        "name": "Google Ads Display + Shopping",
        "description": "Crea campañas de Google Display Network y Shopping Ads para e-commerce",
        "category": "ads",
        "platforms": ["google_ads", "website"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_google_merchant_center", "title": "Configurar Google Merchant Center y feed de productos", "url_template": "https://merchants.google.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_shopping_campaign", "title": "Crear campaña de Shopping con PMax o Standard", "url_template": "https://ads.google.com", "params": {"budget_daily": 25}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_display_creatives", "title": "Generar banners para Google Display Network", "params": {"sizes": ["300x250", "728x90", "336x280"], "count": 6}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_display_campaign", "title": "Crear campaña de Display con remarketing", "url_template": "https://ads.google.com", "params": {"objective": "remarketing", "budget_daily": 15}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_remarketing_lists", "title": "Configurar listas de remarketing en Google Ads", "url_template": "https://ads.google.com", "requires_approval": True},
        ],
    },
    "meta_ads_awareness": {
        "name": "Meta Ads Awareness",
        "description": "Campaña de alcance y reconocimiento de marca en Meta (Facebook + Instagram)",
        "category": "ads",
        "platforms": ["meta_ads", "instagram", "facebook"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "create_awareness_campaign", "title": "Crear campaña de alcance (Reach) con CPM optimizado", "url_template": "https://business.facebook.com/adsmanager", "params": {"objective": "AWARENESS", "budget": 15}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_brand_creatives", "title": "Generar creativos de marca (video + carousel)", "params": {"count": 4, "formats": ["video", "carousel"]}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_brand_lift", "title": "Configurar Brand Lift Study para medir impacto", "url_template": "https://business.facebook.com/adsmanager", "requires_approval": False},
            {"platform": "computer_use", "action_type": "optimize_audience", "title": "Definir audiencias de interés, lookalike y broad", "url_template": "https://business.facebook.com/adsmanager", "requires_approval": True},
        ],
    },
    "meta_ads_retargeting": {
        "name": "Meta Ads Retargeting Avanzado",
        "description": "Campañas de retargeting multi-etapa para visitantes, carritos e interacciones",
        "category": "ads",
        "platforms": ["meta_ads", "instagram", "facebook"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "computer_use", "action_type": "create_retargeting_campaign", "title": "Crear campaña de retargeting de visitantes (30 días)", "url_template": "https://business.facebook.com/adsmanager", "params": {"audience": "website_visitors_30d", "budget": 15}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_cart_retar_campaign", "title": "Crear campaña de retargeting de carritos abandonados", "url_template": "https://business.facebook.com/adsmanager", "params": {"audience": "add_to_cart_7d", "budget": 20}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_engagement_retar_campaign", "title": "Crear campaña de retargeting de engagement (IG/FB)", "url_template": "https://business.facebook.com/adsmanager", "params": {"audience": "engaged_14d", "budget": 10}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_urgency_creatives", "title": "Generar creativos con urgencia y descuento", "params": {"count": 4, "style": "retargeting"}, "requires_approval": True},
        ],
    },
    "tiktok_spark_collection_ads": {
        "name": "TikTok Spark + Collection Ads",
        "description": "Crea Spark Ads desde contenido orgánico y Collection Ads para e-commerce",
        "category": "ads",
        "platforms": ["tiktok_ads", "tiktok"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "select_organic_posts", "title": "Seleccionar posts orgánicos de alto engagement para Spark Ads", "url_template": "https://ads.tiktok.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_spark_ads", "title": "Crear Spark Ads autorizando contenido orgánico", "url_template": "https://ads.tiktok.com", "params": {"budget": 20}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_collection_ads", "title": "Crear Collection Ads con catálogo de productos", "url_template": "https://ads.tiktok.com", "params": {"budget": 25}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_tiktok_creatives", "title": "Generar videos nativos para TikTok Ads", "params": {"count": 3, "style": "native", "duration": 15}, "requires_approval": True},
        ],
    },
    # ─── Marketing: Organic & Social ───────────────────────────────────────────
    "organic_content_marketing": {
        "name": "Content Marketing Orgánico",
        "description": "Crea blog posts, guías y recursos para atraer tráfico orgánico de calidad",
        "category": "organic",
        "platforms": ["website", "pinterest", "linkedin"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "api", "action_type": "keyword_research_blog", "title": "Investigar keywords de blog con alto volumen y baja competencia", "params": {"count": 10}, "requires_approval": False},
            {"platform": "api", "action_type": "generate_blog_posts", "title": "Generar 4 blog posts optimizados para SEO", "params": {"count": 4, "length": 1500, "include_images": True}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "publish_blog_posts", "title": "Publicar posts en blog con schema y CTA", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "generate_pinterest_pins", "title": "Crear pins para cada blog post", "params": {"count": 8, "size": "1000x1500"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "share_linkedin", "title": "Compartir artículos en LinkedIn con copy nativo", "url_template": "https://linkedin.com", "requires_approval": False},
        ],
    },
    "social_media_positioning": {
        "name": "Posicionamiento en Redes Sociales",
        "description": "Estrategia integral de posicionamiento en Instagram, TikTok y LinkedIn",
        "category": "organic",
        "platforms": ["instagram", "tiktok", "linkedin"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "api", "action_type": "generate_content_strategy", "title": "Generar estrategia de contenido mensual por plataforma", "params": {"platforms": ["instagram", "tiktok", "linkedin"], "posts_per_week": 5}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_content_calendar", "title": "Crear calendario de contenido con temas y formatos", "params": {"posts": 20, "include_reels": True, "include_carousels": True}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_reel_scripts", "title": "Generar scripts de video para TikTok y Reels", "params": {"count": 8, "style": "trending"}, "requires_approval": False},
            {"platform": "computer_use", "action_type": "schedule_posts", "title": "Programar contenido en todas las plataformas", "url_template": "https://business.facebook.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "engage_community", "title": "Responder comentarios y DMs diariamente", "url_template": "https://instagram.com", "requires_approval": False},
        ],
    },
    # ─── Marketing: Branding ───────────────────────────────────────────────────
    "brand_kit_creation": {
        "name": "Brand Kit Completo",
        "description": "Crea un kit de marca completo: logo, colores, tipografías, voz y guías visuales",
        "category": "branding",
        "platforms": ["website", "instagram", "linkedin", "tiktok"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "api", "action_type": "generate_brand_strategy", "title": "Generar estrategia de marca (posicionamiento, arquetipo, valores)", "params": {"include_competitor_analysis": True}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_brand_kit", "title": "Generar Brand Kit con logo, colores, tipografías y patterns", "params": {"include": ["logo", "colors", "fonts", "patterns", "social_templates"]}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_brand_voice", "title": "Crear guía de voz de marca (tono, palabras, ejemplos)", "params": {"formats": ["guia_pdf", "cheat_sheet"]}, "requires_approval": True},
            {"platform": "api", "action_type": "generate_social_templates", "title": "Generar templates de redes con el nuevo branding", "params": {"platforms": ["instagram", "tiktok", "linkedin", "facebook"], "count": 12}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "update_all_profiles", "title": "Actualizar branding en todos los perfiles sociales", "url_template": "https://instagram.com", "requires_approval": True},
        ],
    },
    # ─── Operations ────────────────────────────────────────────────────────────
    "shipping_carriers_full": {
        "name": "Setup Completo de Envíos",
        "description": "Configura Andreani, DHL, FedEx, UPS, OCA y Correo Argentino con reglas automáticas",
        "category": "logistics",
        "platforms": ["andreani", "oca", "dhl", "fedex", "ups", "shopify"],
        "estimated_duration_minutes": 180,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_andreani", "title": "Configurar cuenta Andreani y cotizador online", "url_template": "https://andreani.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_oca", "title": "Configurar cuenta OCA e integración", "url_template": "https://oca.com.ar", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_dhl", "title": "Configurar cuenta DHL Express para envíos", "url_template": "https://dhl.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_fedex", "title": "Configurar cuenta FedEx e integración", "url_template": "https://fedex.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_correo_argentino", "title": "Configurar Correo Argentino y MercadoEnvíos", "url_template": "https://correoargentino.com.ar", "requires_approval": True},
            {"platform": "api", "action_type": "configure_shipping_rules", "title": "Configurar reglas automáticas de carrier por zona y peso", "params": {"rules": ["caba", "gba", "interior", "internacional"]}, "requires_approval": True},
        ],
    },
    "cross_border_shipping": {
        "name": "Envío Cross-Border",
        "description": "Configura logística internacional con documentación aduanera y tracking",
        "category": "logistics",
        "platforms": ["dhl", "fedex", "ups", "website"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_dhl_international", "title": "Configurar DHL Express Worldwide y paperless", "url_template": "https://dhl.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_fedex_international", "title": "Configurar FedEx International Priority", "url_template": "https://fedex.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_customs_docs", "title": "Configurar documentación aduanera automática", "url_template": "{user_website}/admin", "requires_approval": True},
            {"platform": "api", "action_type": "setup_duties_taxes", "title": "Configurar DDP/DDU y cálculo de impuestos en checkout", "params": {"options": ["DDP", "DDU"]}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_tracking_notifications", "title": "Configurar notificaciones de tracking internacional", "params": {"channels": ["email", "whatsapp"]}, "requires_approval": True},
        ],
    },
    "payment_processors_setup": {
        "name": "Setup de Pasarelas de Pago",
        "description": "Configura MercadoPago, Stripe, PayPal, Payoneer y Wise para cobros locales e internacionales",
        "category": "operations",
        "platforms": ["mercadopago", "stripe", "paypal", "wise", "website"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_mercadopago", "title": "Configurar MercadoPago (checkout, cuotas, webhooks)", "url_template": "https://mercadopago.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_stripe", "title": "Configurar Stripe (tarjetas, PIX, Boleto, OXXO)", "url_template": "https://stripe.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_paypal", "title": "Configurar PayPal Business y Smart Buttons", "url_template": "https://paypal.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_payoneer", "title": "Configurar Payoneer para cobros internacionales", "url_template": "https://payoneer.com", "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_wise", "title": "Configurar Wise (TransferWise) para transferencias", "url_template": "https://wise.com", "requires_approval": True},
            {"platform": "api", "action_type": "setup_fallback_payments", "title": "Configurar fallback automático entre pasarelas", "params": {"priority": ["mercadopago", "stripe", "paypal"]}, "requires_approval": True},
        ],
    },
    "email_marketing_setup": {
        "name": "Email Marketing con Mailchimp/ConvertKit",
        "description": "Configura secuencias automatizadas, newsletters y segmentación en Mailchimp o ConvertKit",
        "category": "operations",
        "platforms": ["mailchimp", "convertkit", "website"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "computer_use", "action_type": "setup_email_platform", "title": "Configurar cuenta e integrar con sitio web", "url_template": "https://mailchimp.com", "requires_approval": True},
            {"platform": "api", "action_type": "create_welcome_sequence", "title": "Crear secuencia de bienvenida (5 emails)", "params": {"emails": 5, "objective": "onboarding"}, "requires_approval": True},
            {"platform": "api", "action_type": "create_newsletter_template", "title": "Diseñar template de newsletter mensual", "params": {"style": "branded"}, "requires_approval": True},
            {"platform": "api", "action_type": "setup_abandoned_cart_email", "title": "Configurar email de carrito abandonado (3 pasos)", "params": {"emails": 3, "delay_hours": [1, 24, 72]}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "setup_segments", "title": "Crear segmentos (compradores, leads, inactivos)", "url_template": "https://mailchimp.com", "requires_approval": True},
            {"platform": "api", "action_type": "setup_automation_triggers", "title": "Configurar triggers (post-compra, cumpleaños, reactivación)", "params": {"triggers": ["purchase", "birthday", "inactive_30d"]}, "requires_approval": True},
        ],
    },
    # ─── Recovery ──────────────────────────────────────────────────────────────
    "cart_recovery_whatsapp_sms": {
        "name": "Recuperación de Carritos WhatsApp + SMS + Email",
        "description": "Secuencia multicanal de recuperación con WhatsApp, SMS y email en 24h",
        "category": "recovery",
        "platforms": ["whatsapp", "sms", "email", "shopify"],
        "estimated_duration_minutes": 90,
        "steps": [
            {"platform": "api", "action_type": "create_discount_code", "title": "Crear cupón de descuento 10% válido 24h", "params": {"type": "percentage", "value": 10, "expires_in_hours": 24, "code_prefix": "RECUPERA"}, "requires_approval": True},
            {"platform": "api", "action_type": "send_whatsapp_abandoned", "title": "Enviar WhatsApp a carritos abandonados (30 min)", "params": {"delay_minutes": 30, "include_coupon": True}, "requires_approval": True},
            {"platform": "api", "action_type": "send_sms_abandoned", "title": "Enviar SMS de recordatorio (2h)", "params": {"delay_hours": 2, "include_coupon": False}, "requires_approval": True},
            {"platform": "api", "action_type": "send_abandoned_cart_email", "title": "Enviar email de recuperación (4h)", "params": {"delay_hours": 4, "template": "abandoned_cart_final", "include_coupon": True}, "requires_approval": True},
        ],
    },
    "lead_nurture_7_touch": {
        "name": "Lead Nurturing 7-Touch Sequence",
        "description": "Secuencia de 7 touchpoints en 21 días para convertir leads en clientes",
        "category": "recovery",
        "platforms": ["email", "whatsapp", "linkedin", "instagram"],
        "estimated_duration_minutes": 150,
        "steps": [
            {"platform": "api", "action_type": "create_email_sequence", "title": "Crear secuencia de 7 emails de nutrición", "params": {"emails": 7, "spacing_days": [0, 2, 4, 7, 10, 14, 21], "objective": "nurture"}, "requires_approval": True},
            {"platform": "api", "action_type": "send_whatsapp_value", "title": "Enviar mensaje de valor por WhatsApp (día 3)", "params": {"delay_days": 3, "template": "value_tip"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "engage_linkedin", "title": "Interactuar con contenido del lead en LinkedIn", "url_template": "https://linkedin.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "send_dm_instagram", "title": "Enviar DM de valor en Instagram (día 7)", "url_template": "https://instagram.com", "requires_approval": True},
            {"platform": "api", "action_type": "create_retargeting_audience", "title": "Crear audiencia de retargeting de leads en Meta", "params": {"source": "email_list"}, "requires_approval": True},
        ],
    },
    "win_back_campaign": {
        "name": "Win-Back Clientes Inactivos",
        "description": "Reactiva clientes que no compran hace 60+ días con ofertas exclusivas",
        "category": "recovery",
        "platforms": ["email", "whatsapp", "meta_ads", "sms"],
        "estimated_duration_minutes": 120,
        "steps": [
            {"platform": "api", "action_type": "identify_inactive_customers", "title": "Identificar clientes inactivos (60-90-180 días)", "params": {"thresholds": [60, 90, 180]}, "requires_approval": False},
            {"platform": "api", "action_type": "create_win_back_offer", "title": "Crear oferta exclusiva de win-back (20% + regalo)", "params": {"discount": 20, "include_gift": True}, "requires_approval": True},
            {"platform": "api", "action_type": "send_win_back_email", "title": "Enviar email de 'Te extrañamos' con oferta", "params": {"template": "win_back", "delay_hours": 0}, "requires_approval": True},
            {"platform": "api", "action_type": "send_whatsapp_win_back", "title": "Enviar WhatsApp de reactivación (3 días después)", "params": {"delay_days": 3, "template": "win_back_reminder"}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "create_win_back_ads", "title": "Crear campaña de retargeting para inactivos en Meta", "url_template": "https://business.facebook.com/adsmanager", "requires_approval": True},
        ],
    },
    "review_generation_all": {
        "name": "Generación de Reseñas Multi-Plataforma",
        "description": "Solicita y gestiona reseñas en Google, Facebook y MercadoLibre",
        "category": "recovery",
        "platforms": ["google", "facebook", "mercadolibre", "whatsapp"],
        "estimated_duration_minutes": 90,
        "steps": [
            {"platform": "computer_use", "action_type": "create_google_review_link", "title": "Generar enlace directo de reseña en Google", "url_template": "https://business.google.com", "requires_approval": False},
            {"platform": "computer_use", "action_type": "create_facebook_review_link", "title": "Activar reseñas en página de Facebook", "url_template": "https://facebook.com", "requires_approval": False},
            {"platform": "api", "action_type": "send_review_requests", "title": "Enviar solicitudes de reseña post-compra vía WhatsApp", "params": {"via": "whatsapp", "template": "review_request", "delay_hours": 48, "max_per_day": 10}, "requires_approval": True},
            {"platform": "computer_use", "action_type": "request_ml_reviews", "title": "Solicitar reseñas en MercadoLibre a compradores recientes", "url_template": "https://mercadolibre.com", "requires_approval": True},
            {"platform": "api", "action_type": "generate_review_thank_you", "title": "Generar mensajes de agradecimiento por reseñas positivas", "params": {"template": "thank_you_review"}, "requires_approval": False},
        ],
    },
}


def get_playbook(slug: str) -> Optional[PlaybookRead]:
    """Obtener un playbook por su slug."""
    data = PLAYBOOKS.get(slug)
    if not data:
        return None
    return PlaybookRead(
        slug=slug,
        name=data["name"],
        description=data["description"],
        category=data["category"],
        platforms=data["platforms"],
        estimated_duration_minutes=data["estimated_duration_minutes"],
        steps=[PlaybookStep(**step) for step in data["steps"]],
    )


def list_playbooks(category: Optional[str] = None) -> List[PlaybookRead]:
    """Listar todos los playbooks, opcionalmente filtrados por categoría."""
    result = []
    for slug, data in PLAYBOOKS.items():
        if category and data["category"] != category:
            continue
        result.append(
            PlaybookRead(
                slug=slug,
                name=data["name"],
                description=data["description"],
                category=data["category"],
                platforms=data["platforms"],
                estimated_duration_minutes=data["estimated_duration_minutes"],
                steps=[PlaybookStep(**step) for step in data["steps"]],
            )
        )
    return result


def get_recommended_playbooks(diagnostics: List[Any]) -> List[PlaybookRead]:
    """Sugerir playbooks basados en diagnósticos."""
    recommended_slugs = set()
    for diag in diagnostics:
        slug = getattr(diag, "recommended_mission_slug", None)
        if slug:
            recommended_slugs.add(slug)
    return [get_playbook(s) for s in recommended_slugs if get_playbook(s)]
