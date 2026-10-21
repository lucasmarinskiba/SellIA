"""HR API schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    email: str
    position: str
    stage: str
    screening_score: Decimal | None = None
    offer_salary_aed: Decimal | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    employee_number: str
    full_name: str
    email: str
    position: str
    department: str
    status: str
    hire_date: date
    salary_aed_monthly: Decimal


class OnboardingItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category: str
    description: str
    assigned_to: str | None = None
    completed_at: datetime | None = None


class PayrollOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    payroll_date: date
    salary_aed: Decimal
    allowances_aed: Decimal
    deductions_aed: Decimal
    tax_withheld_aed: Decimal
    net_aed: Decimal


class CandidateCreate(BaseModel):
    full_name: str
    email: str
    position: str
    sourced_via: str = "manual"


class OfferCreate(BaseModel):
    salary_aed: Decimal = Field(gt=0)


class PayrollCalcRequest(BaseModel):
    allowances_aed: Decimal = Field(default=Decimal(0), ge=0)
