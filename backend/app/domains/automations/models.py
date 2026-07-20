"""Automations & Workflows Models

Engine for sales automation: triggers, actions, email sequences, chatbot rules.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Boolean, JSON, Interval, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


# ========== Workflow Engine ==========

class WorkflowTriggerType(str, enum.Enum):
    NEW_LEAD = "new_lead"                    # Cuando llega un nuevo lead
    NEW_MESSAGE = "new_message"              # Cuando llega un mensaje
    NO_REPLY = "no_reply"                    # X tiempo sin respuesta del lead
    CART_ABANDONED = "cart_abandoned"        # Carrito abandonado
    APPOINTMENT_MISSED = "appointment_missed"  # No-show a cita
    TAG_ADDED = "tag_added"                  # Se agrega etiqueta
    STAGE_CHANGED = "stage_changed"          # Cambio de etapa en pipeline
    TIME_DELAY = "time_delay"                # Delay programado
    LEAD_SCORE_CHANGED = "lead_score_changed"  # Cambio en lead score
    DEAL_STALLED = "deal_stalled"            # Deal estancado
    PRICE_INQUIRY = "price_inquiry"          # Pregunta de precio
    REPEAT_CUSTOMER = "repeat_customer"      # Cliente repetidor
    REVENUE_EVENT = "revenue_event"          # Evento de venta
    SERVICE_PAID = "service_paid"            # Orden de servicio pagada
    APPOINTMENT_SCHEDULED = "appointment_scheduled"  # Cita agendada
    APPOINTMENT_CONFIRMED = "appointment_confirmed"  # Cliente confirmó asistencia
    APPOINTMENT_NO_SHOW = "appointment_no_show"      # No asistió a cita
    SERVICE_COMPLETED = "service_completed"  # Servicio finalizado
    FEEDBACK_RECEIVED = "feedback_received"  # Cliente dejó feedback


class WorkflowActionType(str, enum.Enum):
    SEND_MESSAGE = "send_message"            # Enviar mensaje por canal
    SEND_EMAIL = "send_email"                # Enviar email
    ASSIGN_AGENT = "assign_agent"            # Asignar a agente humano
    ADD_TAG = "add_tag"                      # Agregar etiqueta
    MOVE_STAGE = "move_stage"                # Mover etapa en pipeline
    WAIT = "wait"                            # Esperar X tiempo
    WEBHOOK = "webhook"                      # Llamar webhook externo
    AI_REPLY = "ai_reply"                    # Responder con IA
    UPDATE_STAGE = "update_stage"            # Actualizar etapa CRM
    UPDATE_SCORE = "update_score"            # Actualizar lead score
    CREATE_DEAL = "create_deal"              # Crear deal/oportunidad
    SET_DEAL_VALUE = "set_deal_value"        # Setear valor de deal
    SEND_NOTIFICATION = "send_notification"  # Notificar al dueño
    START_SEQUENCE = "start_sequence"        # Iniciar secuencia de emails
    AI_WAIT = "ai_wait"                      # Esperar con timing optimizado por IA
    CREATE_SHIPMENT = "create_shipment"      # Crear envío para orden
    CREATE_APPOINTMENT = "create_appointment"  # Crear cita para servicio
    SEND_REMINDER = "send_reminder"          # Enviar recordatorio de cita
    REQUEST_CONFIRMATION = "request_confirmation"  # Pedir confirmación de asistencia
    REQUEST_FEEDBACK = "request_feedback"    # Solicitar feedback post-servicio
    FOLLOW_UP_SEQUENCE = "follow_up_sequence"  # Iniciar seguimiento post-servicio
    UPDATE_SERVICE_STATUS = "update_service_status"  # Actualizar estado de entrega
    # === AI Content Generation Actions ===
    GENERATE_IMAGE = "generate_image"              # Generar imagen con IA para producto/campaña
    GENERATE_VIDEO = "generate_video"              # Generar video con IA para producto/campaña
    GENERATE_COPY = "generate_copy"                # Generar copy/caption/email con IA
    GENERATE_CAROUSEL = "generate_carousel"        # Generar carousel de imágenes con IA
    GENERATE_THUMBNAIL = "generate_thumbnail"      # Generar thumbnail optimizado con IA
    SCHEDULE_POST = "schedule_post"                # Programar publicación en redes sociales
    UPDATE_CATALOG_MEDIA = "update_catalog_media"  # Actualizar imágenes/videos del catálogo
    CREATE_CONTENT_BRIEF = "create_content_brief"  # Crear brief de contenido para equipo creativo


class WorkflowStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DRAFT = "draft"


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(Enum(WorkflowTriggerType), nullable=False)
    trigger_config = Column(JSONB, default=dict, nullable=False)  # ej. {"delay_minutes": 30, "keywords": ["precio"]}
    actions = Column(JSONB, default=list, nullable=False)  # lista de acciones con config
    visual_data = Column(JSONB, nullable=True)  # node/edge data from visual builder
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False)
    execution_count = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("workflow_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    trigger_data = Column(JSONB, default=dict, nullable=False)
    actions_executed = Column(JSONB, default=list, nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # completed, failed, running
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WorkflowVariant(Base):
    """A/B test variant for a workflow."""
    __tablename__ = "workflow_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    variant_name = Column(String(100), nullable=False)
    traffic_split = Column(Integer, default=50, nullable=False)  # 0-100 percentage
    actions = Column(JSONB, default=list, nullable=False)  # variant actions override
    execution_count = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# ========== Email Templates & Sequences ==========

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=False)
    variables = Column(JSONB, default=list, nullable=False)  # ["lead_name", "product_name"]
    category = Column(String(100), nullable=True)  # welcome, sales, follow_up, abandoned_cart
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class EmailSequence(Base):
    __tablename__ = "email_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # welcome, nurture, sales, cart_recovery, re_engagement
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False)
    trigger_type = Column(String(100), nullable=True)  # new_lead, cart_abandoned, tag_added, etc.
    sent_count = Column(Integer, default=0)
    opens_count = Column(Integer, default=0)
    clicks_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SequenceStep(Base):
    __tablename__ = "sequence_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id = Column(UUID(as_uuid=True), ForeignKey("email_sequences.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False, default=0)
    delay_hours = Column(Integer, default=0, nullable=False)  # horas después del trigger o paso anterior
    delay_minutes = Column(Integer, default=0, nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True)
    subject_override = Column(String(500), nullable=True)
    body_override = Column(Text, nullable=True)
    condition = Column(String(200), nullable=True)  # ej. "opened_previous:yes", "clicked:no"
    extra_data = Column(JSONB, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SequenceSubscription(Base):
    """Links a conversation to an email sequence they are subscribed to."""
    __tablename__ = "sequence_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id = Column(UUID(as_uuid=True), ForeignKey("email_sequences.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    current_step_index = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active", nullable=False)  # active, completed, paused, cancelled
    extra_data = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SequenceEmailLog(Base):
    """Log of every email sent via a sequence."""
    __tablename__ = "sequence_email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("sequence_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_id = Column(UUID(as_uuid=True), ForeignKey("email_sequences.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id = Column(UUID(as_uuid=True), ForeignKey("sequence_steps.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    tracking_token = Column(String(64), unique=True, nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, sent, bounced, failed
    extra_data = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ========== Chatbot Intelligence Rules ==========

class ChatbotRule(Base):
    __tablename__ = "chatbot_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    intent = Column(String(100), nullable=False, index=True)  # buy, price, support, complaint, greeting, etc.
    keywords = Column(JSONB, default=list, nullable=False)  # ["precio", "cuanto cuesta", "valor"]
    response_template = Column(Text, nullable=False)
    response_type = Column(String(50), default="text", nullable=False)  # text, template, ai_generated
    priority = Column(Integer, default=0, nullable=False)
    channel_filter = Column(JSONB, default=list, nullable=False)  # ["whatsapp", "instagram"] o [] para todos
    requires_human = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# ========== AI Content Generation ==========

class GeneratedContent(Base):
    """Contenido generado por IA (imágenes, videos, copy, carruseles, thumbnails)."""
    __tablename__ = "generated_contents"

    __table_args__ = (
        # Índices compuestos para queries comunes
        Index("idx_gencontent_business_type_status", "business_id", "content_type", "status"),
        Index("idx_gencontent_business_agent", "business_id", "agent_slug"),
        Index("idx_gencontent_catalog_status", "catalog_item_id", "status"),
        Index("idx_gencontent_status_created", "status", "created_at"),
        Index("idx_gencontent_business_approval", "business_id", "approval_status"),
        # GIN indices para JSONB
        Index("idx_gencontent_variations_gin", "variations", postgresql_using="gin"),
        Index("idx_gencontent_config_gin", "generation_config", postgresql_using="gin"),
        Index("idx_gencontent_perf_gin", "performance_data", postgresql_using="gin"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    catalog_item_id = Column(UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="SET NULL"), nullable=True, index=True)

    content_type = Column(String(50), nullable=False)  # image, video, copy, carousel, thumbnail, email, ad
    agent_slug = Column(String(100), nullable=False)  # ai-image-architect, ai-video-director, etc.
    status = Column(String(50), default="pending", nullable=False)  # pending, generating, completed, failed, approved, rejected

    # Prompts y configuración
    prompt = Column(Text, nullable=True)  # El prompt principal usado
    negative_prompt = Column(Text, nullable=True)  # Para generación de imagen/video
    generation_config = Column(JSONB, default=dict, nullable=False)  # modelo, dimensiones, estilo, etc.

    # Resultados
    source_url = Column(String(1000), nullable=True)  # URL del asset generado (imagen/video)
    thumbnail_url = Column(String(1000), nullable=True)  # URL de thumbnail/preview
    text_content = Column(Text, nullable=True)  # Para copy, captions, scripts, emails
    variations = Column(JSONB, default=list, nullable=False)  # Variaciones generadas [{"url": ..., "prompt": ...}]

    # Metadatos y uso
    platform = Column(String(50), nullable=True)  # instagram, tiktok, facebook, email, etc.
    purpose = Column(String(100), nullable=True)  # hero_image, lifestyle, ad, carousel_cover, reel, etc.
    usage_count = Column(Integer, default=0)
    performance_data = Column(JSONB, default=dict, nullable=False)  # reach, engagement, clicks, conversions

    # Control de calidad y aprobación
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approval_status = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected, needs_revision
    feedback_notes = Column(Text, nullable=True)

    # Presupuesto y costos
    generation_cost = Column(Integer, default=0, nullable=False)  # Costo en créditos o moneda base (centavos)
    ai_model_used = Column(String(100), nullable=True)  # dalle-3, midjourney, sora, runway, etc.

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ContentCalendar(Base):
    """Calendario de contenido programado para publicación."""
    __tablename__ = "content_calendar"

    __table_args__ = (
        Index("idx_calendar_business_scheduled", "business_id", "scheduled_at"),
        Index("idx_calendar_business_status", "business_id", "status"),
        Index("idx_calendar_business_platform", "business_id", "platform"),
        Index("idx_calendar_status_scheduled", "status", "scheduled_at"),
        Index("idx_calendar_hashtags_gin", "hashtags", postgresql_using="gin"),
        Index("idx_calendar_media_gin", "media_urls", postgresql_using="gin"),
        Index("idx_calendar_extra_gin", "extra_data", postgresql_using="gin"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_content_id = Column(UUID(as_uuid=True), ForeignKey("generated_contents.id", ondelete="SET NULL"), nullable=True, index=True)
    catalog_item_id = Column(UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True, index=True)

    # Programación
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    status = Column(String(50), default="scheduled", nullable=False)  # scheduled, published, failed, cancelled, draft

    # Plataforma y formato
    platform = Column(String(50), nullable=False)  # instagram, tiktok, facebook, linkedin, email, etc.
    content_format = Column(String(50), nullable=False)  # feed_post, reel, story, carousel, email, ad
    channel_connection_id = Column(UUID(as_uuid=True), ForeignKey("channel_connections.id", ondelete="SET NULL"), nullable=True)

    # Contenido
    caption = Column(Text, nullable=True)
    hashtags = Column(JSONB, default=list, nullable=False)
    alt_text = Column(Text, nullable=True)
    media_urls = Column(JSONB, default=list, nullable=False)  # URLs de imágenes/videos a publicar
    cta_text = Column(String(500), nullable=True)
    link_in_bio = Column(String(1000), nullable=True)

    # Engagement tracking
    published_at = Column(DateTime(timezone=True), nullable=True)
    published_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    external_post_id = Column(String(500), nullable=True)  # ID del post en la plataforma externa
    external_url = Column(String(1000), nullable=True)

    # Métricas
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    engagement = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Integer, default=0)  # En centavos

    # Workflow
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True)
    auto_publish = Column(Boolean, default=False, nullable=False)
    requires_approval = Column(Boolean, default=True, nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Extra
    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
