"""
Database models — PostgreSQL SQLAlchemy ORM.

Setup:
  pip install sqlalchemy psycopg2-binary

Env vars:
  - DATABASE_URL=postgresql://user:password@localhost:5432/sellia
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sellia")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Account(Base):
    """Cuenta vendedor."""

    __tablename__ = "accounts"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    business_name = Column(String)
    product_name = Column(String)
    product_description = Column(Text)
    price = Column(Float)
    industry = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    orders = relationship("Order", back_populates="account")
    leads = relationship("Lead", back_populates="account")
    emails = relationship("EmailLog", back_populates="account")


class Lead(Base):
    """Lead capturado."""

    __tablename__ = "leads"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"))
    name = Column(String)
    email = Column(String, index=True)
    phone = Column(String)
    source = Column(String)  # whatsapp, instagram, email, ad, organic
    status = Column(String, default="new")  # new, qualified, contacted, converted
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="leads")


class Order(Base):
    """Orden completada."""

    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"))
    customer_email = Column(String, index=True)
    customer_name = Column(String)
    amount_usd = Column(Float)
    status = Column(String, default="pending")  # pending, paid, shipped, delivered
    payment_status = Column(String, default="pending")  # pending, confirmed, failed
    stripe_payment_intent_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    account = relationship("Account", back_populates="orders")


class EmailLog(Base):
    """Log de emails enviados."""

    __tablename__ = "email_logs"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"))
    to_email = Column(String, index=True)
    subject = Column(String)
    template = Column(String)  # welcome, follow_up, invoice, etc
    status = Column(String)  # sent, bounced, opened, clicked
    sent_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="emails")


class WebhookEvent(Base):
    """Log de webhooks recibidos."""

    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True)
    source = Column(String)  # stripe, whatsapp, instagram, etc
    event_type = Column(String)
    payload = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Strategy(Base):
    """Strategy guardada por account."""

    __tablename__ = "strategies"

    id = Column(String, primary_key=True)
    account_id = Column(String, index=True)
    product_name = Column(String)
    segment = Column(String)  # premium, budget, growth
    channels = Column(JSON)
    tactics = Column(JSON)
    kpis = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Metric(Base):
    """Métricas en vivo."""

    __tablename__ = "metrics"

    id = Column(String, primary_key=True)
    account_id = Column(String, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    leads_captured = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    orders_completed = Column(Integer, default=0)
    revenue_usd = Column(Float, default=0)
    conversion_rate = Column(Float, default=0)
    email_opened = Column(Integer, default=0)
    email_clicked = Column(Integer, default=0)


# Create tables
def init_db():
    """Crea tablas en DB."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency para obtener sesión DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
