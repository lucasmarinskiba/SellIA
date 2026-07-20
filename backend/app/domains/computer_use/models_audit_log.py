"""Computer Use Audit Log — Activity trace for all agent actions.

Registra TODA actividad:
- Agent usado
- Estrategia
- Plataforma (whatsapp/instagram/etc)
- Entrada (mensaje recibido)
- Salida (respuesta enviada)
- Resultado (success/pending/failed)
- Confianza
"""

from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class ComputerUseAuditLog(Base):
    """Audit log para todas las actividades de Computer Use."""

    __tablename__ = "computer_use_audit_logs"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("user.id"), index=True)
    session_id = Column(String(36), ForeignKey("computer_use_sessions.id"), nullable=True, index=True)

    # Tiempo
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    executed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, default=0)

    # Contexto
    platform = Column(String(50), index=True)  # whatsapp, instagram, tiktok, facebook, mercadolibre, amazon, hotmart, website
    action_type = Column(String(50), index=True)  # message_response, comment_response, sale_closed, calendar_scheduled, etc

    # Agent + Estrategia
    agent_name = Column(String(100), nullable=True)  # acquisition_strategist, auto_responder, closer, etc
    strategy_name = Column(String(100), nullable=True)  # attention_grabber, closing_technique, etc
    tactics = Column(JSONB, nullable=True)  # ["authentic_approach", "value_first"]

    # Confianza
    confidence_score = Column(Float, default=0.0)  # 0-1
    requires_approval = Column(Boolean, default=False)

    # Datos
    input_data = Column(Text, nullable=True)  # Mensaje recibido, comentario, etc (truncated to 5000 chars)
    output_data = Column(Text, nullable=True)  # Respuesta enviada (truncated to 5000 chars)

    # Resultado
    status = Column(String(50), index=True)  # success, pending_approval, failed, escalated
    error_message = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)  # Datos adicionales: customer_id, order_id, etc

    # Auditoría
    user_approved = Column(Boolean, nullable=True)  # True: user approved, False: user rejected, None: pending
    approval_at = Column(DateTime, nullable=True)
    approved_by_user_id = Column(String(36), ForeignKey("user.id"), nullable=True)

    def __repr__(self):
        return (
            f"<ComputerUseAuditLog "
            f"id={self.id} "
            f"platform={self.platform} "
            f"action={self.action_type} "
            f"status={self.status}>"
        )


class ComputerUseAuditLogSearchFilter:
    """Helper para búsquedas en audit log."""

    def __init__(
        self,
        user_id: str,
        platform: str = None,
        action_type: str = None,
        agent_name: str = None,
        status: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 100,
        offset: int = 0,
    ):
        self.user_id = user_id
        self.platform = platform
        self.action_type = action_type
        self.agent_name = agent_name
        self.status = status
        self.date_from = date_from
        self.date_to = date_to
        self.limit = limit
        self.offset = offset
