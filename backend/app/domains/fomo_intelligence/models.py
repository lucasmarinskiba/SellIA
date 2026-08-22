"""FOMO Intelligence: registers + learns from the 4 core FOMO strategies.

Estrategias:
  ESCASEZ_REAL   - cupos/stock realmente limitados (no inventados)
  PRUEBA_SOCIAL  - testimonios/fotos/mensajes de compradores reales
  EXCLUSIVIDAD   - acceso a grupo reducido o por tiempo limitado
  TRANSPARENCIA  - resultados y logros reales de la comunidad

Regla de integridad: toda aplicación de estrategia debe declarar
`real_data_source` (de dónde sale el número/dato) y `data_snapshot`
(el dato real capturado en ese momento). Sin eso, no se registra:
FOMO fabricado destruye confianza y viola la estrategia de Transparencia.
"""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, Enum
from app.db.models import Base


class FOMOStrategyType(str, enum.Enum):
    ESCASEZ_REAL = "escasez_real"
    PRUEBA_SOCIAL = "prueba_social"
    EXCLUSIVIDAD = "exclusividad"
    TRANSPARENCIA = "transparencia"


class FOMOStrategyApplication(Base):
    """Un uso concreto de una estrategia FOMO, con el dato real que la respalda."""
    __tablename__ = "fomo_strategy_applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), nullable=False, index=True)
    strategy_type = Column(Enum(FOMOStrategyType), nullable=False, index=True)

    # Contexto de aplicación
    target_type = Column(String(50), nullable=False)  # product, campaign, cohort, landing_page
    target_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(50), nullable=True)  # instagram, email, whatsapp, landing_page
    personality_target = Column(String(50), nullable=True)  # de X9: pragmatist, impulse_buyer, etc

    # Integridad del dato: obligatorio declarar la fuente real
    real_data_source = Column(String(200), nullable=False)
    # ej: "inventory_count", "testimonial_id:abc123", "cohort_capacity", "conversion_engine.win_deal"
    data_snapshot = Column(JSON, nullable=False)
    # ej: {"slots_remaining": 3, "total_slots": 50} o {"reviewer": "María G.", "rating": 5}

    # Mensaje generado a partir del dato real
    generated_message = Column(Text, nullable=True)

    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FOMOStrategyOutcome(Base):
    """Resultado medido de una aplicación de estrategia (impresiones -> conversión)."""
    __tablename__ = "fomo_strategy_outcomes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), nullable=False, index=True)

    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)

    # Señal de confianza: si el usuario reporta la FOMO como genuina o forzada
    perceived_as_genuine = Column(Boolean, nullable=True)

    measured_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FOMOStrategyIntelligence(Base):
    """Conocimiento agregado: qué estrategia funciona mejor para qué segmento."""
    __tablename__ = "fomo_strategy_intelligence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_type = Column(Enum(FOMOStrategyType), nullable=False, index=True)
    personality_type = Column(String(50), nullable=True, index=True)  # null = agregado general

    sample_size = Column(Integer, default=0)
    total_impressions = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    avg_conversion_rate = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.0)  # % perceived_as_genuine=True
    confidence_level = Column(String(20), default="low")  # low, medium, high (según sample_size)

    recommendation = Column(Text, nullable=True)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
