"""E2E Tests para Automation Toggles"""

import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.domains.automations.models import AutomationToggle, ToggleAuditLog
from app.domains.automations.seed_toggles import seed_toggles_for_business


@pytest.mark.asyncio
async def test_e2e_create_business_seed_toggles_update(db: AsyncSession):
    """
    E2E:
    1. Crear negocio
    2. Seed toggles
    3. Listar toggles
    4. Cambiar estado de uno
    5. Verificar audit log
    """
    # Step 1: Setup
    business_id = uuid4()
    user_id = uuid4()

    # Step 2: Seed toggles para el negocio
    await seed_toggles_for_business(business_id, db)

    # Step 3: Listar toggles
    result = await db.execute(
        select(AutomationToggle)
        .where(AutomationToggle.business_id == business_id)
        .order_by(AutomationToggle.category)
    )
    toggles = result.scalars().all()
    assert len(toggles) == 12

    # Step 4: Obtener lead_scorer toggle
    lead_scorer = next(
        (t for t in toggles if t.toggle_key == "agent:lead_scorer"),
        None,
    )
    assert lead_scorer is not None
    assert lead_scorer.is_enabled is True
    assert lead_scorer.monthly_limit == 1000

    # Step 5: Cambiar estado (deshabilitar)
    lead_scorer.is_enabled = False
    lead_scorer.changed_by = user_id

    # Crear audit log
    audit = ToggleAuditLog(
        business_id=business_id,
        toggle_id=lead_scorer.id,
        action="disabled",
        old_value={"is_enabled": True},
        new_value={"is_enabled": False},
        changed_by_user_id=user_id,
        changed_by_email="admin@test.com",
        reason="Testing E2E flow",
    )
    db.add(audit)
    await db.commit()

    # Step 6: Verificar que cambió
    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.id == lead_scorer.id)
    )
    updated = result.scalar_one()
    assert updated.is_enabled is False

    # Step 7: Verificar audit log
    result = await db.execute(
        select(ToggleAuditLog).where(ToggleAuditLog.toggle_id == lead_scorer.id)
    )
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].action == "disabled"
    assert logs[0].changed_by_email == "admin@test.com"


@pytest.mark.asyncio
async def test_e2e_usage_increment_hits_limit(db: AsyncSession):
    """
    E2E:
    1. Seed toggles
    2. Obtener cold_email (limit 500)
    3. Incrementar usage hasta casi el límite
    4. Verificar que está en 99%
    """
    business_id = uuid4()
    await seed_toggles_for_business(business_id, db)

    result = await db.execute(
        select(AutomationToggle)
        .where(AutomationToggle.business_id == business_id)
        .where(AutomationToggle.toggle_key == "agent:cold_email")
    )
    cold_email = result.scalar_one()

    assert cold_email.monthly_limit == 500
    assert cold_email.current_month_usage == 0

    # Simular 495 usos (99%)
    for _ in range(495):
        cold_email.current_month_usage += 1

    await db.commit()

    # Verificar
    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.id == cold_email.id)
    )
    updated = result.scalar_one()

    usage_percent = (updated.current_month_usage / updated.monthly_limit) * 100
    assert usage_percent == 99.0


@pytest.mark.asyncio
async def test_e2e_change_limit_and_log(db: AsyncSession):
    """
    E2E:
    1. Seed toggles
    2. Cambiar monthly_limit
    3. Crear audit log con valores old/new
    4. Verificar audit
    """
    business_id = uuid4()
    user_id = uuid4()
    await seed_toggles_for_business(business_id, db)

    result = await db.execute(
        select(AutomationToggle)
        .where(AutomationToggle.business_id == business_id)
        .where(AutomationToggle.toggle_key == "automation:sms_marketing")
    )
    sms = result.scalar_one()

    old_limit = sms.monthly_limit
    new_limit = 10000

    # Cambiar límite
    sms.monthly_limit = new_limit
    sms.changed_by = user_id

    # Audit log
    audit = ToggleAuditLog(
        business_id=business_id,
        toggle_id=sms.id,
        action="limit_changed",
        old_value={"monthly_limit": old_limit},
        new_value={"monthly_limit": new_limit},
        changed_by_user_id=user_id,
        changed_by_email="admin@test.com",
        reason="Increased capacity for Q4 campaign",
    )
    db.add(audit)
    await db.commit()

    # Verificar
    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.id == sms.id)
    )
    updated = result.scalar_one()
    assert updated.monthly_limit == new_limit

    result = await db.execute(
        select(ToggleAuditLog).where(ToggleAuditLog.toggle_id == sms.id)
    )
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].new_value["monthly_limit"] == new_limit


@pytest.mark.asyncio
async def test_e2e_category_distribution(db: AsyncSession):
    """
    E2E: Verificar que seed distribuye toggles correctamente por categoría
    """
    business_id = uuid4()
    await seed_toggles_for_business(business_id, db)

    result = await db.execute(
        select(AutomationToggle)
        .where(AutomationToggle.business_id == business_id)
        .order_by(AutomationToggle.category)
    )
    toggles = result.scalars().all()

    # Contar por categoría
    by_cat = {}
    for t in toggles:
        by_cat[t.category] = by_cat.get(t.category, 0) + 1

    # Esperamos: agent(4), automation(3), feature(3), integration(2)
    expected = {
        "agent": 4,
        "automation": 3,
        "feature": 3,
        "integration": 2,
    }

    assert by_cat == expected, f"Distribution mismatch: {by_cat} vs {expected}"

    # Verificar que todos los "agent" tienen límites razonables
    agents = [t for t in toggles if t.category == "agent"]
    for agent in agents:
        assert agent.display_name, "Agent sin display_name"
        # Algunos agentes pueden no tener límite (competitor intel)
        if agent.monthly_limit:
            assert agent.monthly_limit > 0
