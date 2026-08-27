"""HR services — recruitment, onboarding, payroll."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.hr.models import (
    Candidate,
    CandidateStage,
    Employee,
    EmployeeStatus,
    OnboardingChecklistItem,
    Payroll,
)

logger = get_logger(__name__)


class RecruitmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_candidate(
        self, business_id: uuid.UUID, full_name: str, email: str, position: str, sourced_via: str = "manual"
    ) -> Candidate:
        """Add candidate to pipeline."""
        cand = Candidate(
            business_id=business_id,
            full_name=full_name,
            email=email,
            position=position,
            sourced_via=sourced_via,
        )
        self.db.add(cand)
        await self.db.commit()
        return cand

    async def score_screening(self, candidate_id: uuid.UUID, score: Decimal) -> Candidate:
        """Screening score (0–100); advance if >= 60."""
        cand = (await self.db.execute(select(Candidate).where(Candidate.id == candidate_id))).scalar_one()
        cand.screening_score = score
        if score >= 60:
            cand.stage = CandidateStage.SCREENING.value
        else:
            cand.stage = CandidateStage.REJECTED.value
        await self.db.commit()
        return cand

    async def send_offer(self, candidate_id: uuid.UUID, salary_aed: Decimal) -> Candidate:
        """Send job offer."""
        cand = (await self.db.execute(select(Candidate).where(Candidate.id == candidate_id))).scalar_one()
        cand.stage = CandidateStage.OFFER_SENT.value
        cand.offer_salary_aed = salary_aed
        cand.offer_sent_at = datetime.now(timezone.utc)
        await self.db.commit()
        return cand

    async def accept_offer(self, candidate_id: uuid.UUID) -> Employee:
        """Accept offer → hire → create employee."""
        cand = (await self.db.execute(select(Candidate).where(Candidate.id == candidate_id))).scalar_one()
        cand.stage = CandidateStage.HIRED.value
        cand.offer_accepted_at = datetime.now(timezone.utc)
        cand.hired_at = datetime.now(timezone.utc)

        emp_num = f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        emp = Employee(
            business_id=cand.business_id,
            candidate_id=candidate_id,
            employee_number=emp_num,
            full_name=cand.full_name,
            email=cand.email,
            phone=cand.phone,
            position=cand.position,
            department="unassigned",
            hire_date=date.today(),
            salary_aed_monthly=cand.offer_salary_aed or Decimal("0"),
            contract_type="full_time",
        )
        self.db.add(emp)
        await self.db.commit()
        logger.info(f"Employee created: {emp_num} ({cand.full_name})")
        return emp


class OnboardingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_checklist(self, employee_id: uuid.UUID, business_id: uuid.UUID) -> list[OnboardingChecklistItem]:
        """Auto-create standard onboarding checklist."""
        items = [
            ("equipment", "Provision laptop & peripherals"),
            ("equipment", "Setup phone & SIM"),
            ("access", "Create email account"),
            ("access", "Setup access card & building access"),
            ("access", "Grant system access (HR portal, tools, VPN)"),
            ("training", "Company orientation (culture, policies)"),
            ("training", "Role-specific training"),
            ("documentation", "Employment contract signed"),
            ("documentation", "Tax documents (TIN, banking)"),
            ("documentation", "Handbook acknowledgment"),
        ]
        created = []
        for category, desc in items:
            item = OnboardingChecklistItem(
                employee_id=employee_id,
                business_id=business_id,
                category=category,
                description=desc,
            )
            self.db.add(item)
            created.append(item)
        await self.db.commit()
        return created

    async def complete_item(self, item_id: uuid.UUID, notes: Optional[str] = None) -> OnboardingChecklistItem:
        """Mark onboarding task complete."""
        item = (await self.db.execute(select(OnboardingChecklistItem).where(OnboardingChecklistItem.id == item_id))).scalar_one()
        item.completed_at = datetime.now(timezone.utc)
        if notes:
            item.notes = notes
        await self.db.commit()
        return item

    async def onboarding_status(self, employee_id: uuid.UUID) -> dict:
        """Get onboarding completion status."""
        items = (
            await self.db.execute(
                select(OnboardingChecklistItem)
                .where(OnboardingChecklistItem.employee_id == employee_id)
                .order_by(OnboardingChecklistItem.category)
            )
        ).scalars().all()
        total = len(items)
        completed = sum(1 for i in items if i.completed_at)
        return {
            "total_items": total,
            "completed_items": completed,
            "pct_complete": (completed / total * 100) if total else 0,
            "pending_items": [
                {"category": i.category, "description": i.description, "assigned_to": i.assigned_to}
                for i in items
                if not i.completed_at
            ],
        }


class PayrollService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_payroll(
        self, employee_id: uuid.UUID, payroll_date: date, allowances_aed: Decimal = Decimal("0")
    ) -> Payroll:
        """Calculate monthly payroll: salary + allowances - deductions - tax."""
        emp = (await self.db.execute(select(Employee).where(Employee.id == employee_id))).scalar_one()

        salary = emp.salary_aed_monthly
        deductions = Decimal("0")  # placeholder for loans, etc.
        tax = (salary + allowances_aed - deductions) * Decimal("0.05")  # simplified 5% tax

        net = salary + allowances_aed - deductions - tax

        payroll = Payroll(
            employee_id=employee_id,
            business_id=emp.business_id,
            payroll_date=payroll_date,
            salary_aed=salary,
            allowances_aed=allowances_aed,
            deductions_aed=deductions,
            tax_withheld_aed=tax,
            net_aed=net,
        )
        self.db.add(payroll)
        await self.db.commit()
        return payroll

    async def process_payroll_batch(
        self, business_id: uuid.UUID, payroll_date: date
    ) -> dict[str, int]:
        """Generate payroll for all active employees."""
        emps = (
            await self.db.execute(
                select(Employee).where(
                    Employee.business_id == business_id,
                    Employee.status == EmployeeStatus.ACTIVE.value,
                    Employee.is_active == True,
                )
            )
        ).scalars().all()

        created = 0
        for emp in emps:
            await self.calculate_payroll(emp.id, payroll_date)
            created += 1

        logger.info(f"Payroll processed: {created} employees for {payroll_date}")
        return {"business_id": str(business_id), "payroll_date": payroll_date.isoformat(), "employees": created}

    async def payroll_summary(self, business_id: uuid.UUID, payroll_date: date) -> dict:
        """Summary of payroll for a date."""
        rows = (
            await self.db.execute(
                select(Payroll).where(
                    Payroll.business_id == business_id,
                    Payroll.payroll_date == payroll_date,
                )
            )
        ).scalars().all()

        total_salary = sum(p.salary_aed for p in rows)
        total_allowances = sum(p.allowances_aed for p in rows)
        total_deductions = sum(p.deductions_aed for p in rows)
        total_tax = sum(p.tax_withheld_aed for p in rows)
        total_net = sum(p.net_aed for p in rows)

        return {
            "payroll_date": payroll_date.isoformat(),
            "employee_count": len(rows),
            "total_salary": float(total_salary),
            "total_allowances": float(total_allowances),
            "total_deductions": float(total_deductions),
            "total_tax": float(total_tax),
            "total_net": float(total_net),
        }
