"""HR domain models — recruitment, onboarding, payroll."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.core.database import Base


class CandidateStage(str, Enum):
    """Recruitment pipeline stages."""
    SOURCED = "sourced"
    SCREENING = "screening"
    INTERVIEWED = "interviewed"
    OFFER_SENT = "offer_sent"
    ACCEPTED = "accepted"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class EmployeeStatus(str, Enum):
    """Employee lifecycle status."""
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    LEAVE = "leave"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class Candidate(Base):
    """Job candidate in recruitment pipeline."""
    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    position: Mapped[str] = mapped_column(String(200))
    stage: Mapped[str] = mapped_column(SQLEnum(CandidateStage, native_enum=False), default=CandidateStage.SOURCED.value)
    sourced_via: Mapped[str | None] = mapped_column(String(100), nullable=True)  # linkedin, referral, job_board, etc.
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    screening_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # 0–100
    interview_feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    offer_salary_aed: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    offer_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    offer_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Employee(Base):
    """Hired employee with onboarding + payroll state."""
    __tablename__ = "employees"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    candidate_id: Mapped[UUID | None] = mapped_column(ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True)
    employee_number: Mapped[str] = mapped_column(String(50), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    position: Mapped[str] = mapped_column(String(200))
    department: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(SQLEnum(EmployeeStatus, native_enum=False), default=EmployeeStatus.ONBOARDING.value)
    hire_date: Mapped[date] = mapped_column(Date)
    salary_aed_monthly: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="AED")
    contract_type: Mapped[str] = mapped_column(String(50))  # full_time, part_time, contract
    reports_to: Mapped[UUID | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    tax_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OnboardingChecklistItem(Base):
    """Onboarding task (equipment, training, docs, access)."""
    __tablename__ = "onboarding_checklist_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(50))  # equipment, training, access, documentation, etc.
    description: Mapped[str] = mapped_column(String(500))
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)  # person responsible
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payroll(Base):
    """Monthly payroll record (salary, deductions, tax, net)."""
    __tablename__ = "payrolls"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    payroll_date: Mapped[date] = mapped_column(Date)
    salary_aed: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    allowances_aed: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    deductions_aed: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax_withheld_aed: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    net_aed: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


HR_TABLES = [Candidate.__table__, Employee.__table__, OnboardingChecklistItem.__table__, Payroll.__table__]
