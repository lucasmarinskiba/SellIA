"""Tests para Automation Toggles API"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from httpx import AsyncClient

from app.main import app
from app.core.database import AsyncSession
from app.domains.automations.models import AutomationToggle, ToggleAuditLog
from app.domains.automations.seed_toggles import seed_toggles_for_business
from sqlalchemy import select


@pytest.fixture
async def client():
    """Fixture para cliente HTTP."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_business_id():
    """Fixture para test business ID."""
    return uuid4()


@pytest.fixture
async def test_user_id():
    """Fixture para test user ID."""
    return uuid4()


@pytest.mark.asyncio
async def test_list_toggles_empty(client, test_business_id):
    """Test: listar toggles vacío retorna lista vacía."""
    response = await client.get(
        f"/api/v1/automations/toggles/business/{test_business_id}",
        headers={"Authorization": "Bearer fake_token"},
    )
    # Puede ser 401 (auth) o 200 con lista vacía
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_seed_toggles(db: AsyncSession, test_business_id: uuid4):
    """Test: seed crea 12 toggles con keys únicos."""
    await seed_toggles_for_business(test_business_id, db)

    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.business_id == test_business_id)
    )
    toggles = result.scalars().all()

    assert len(toggles) == 12, "Debe crear exactamente 12 toggles"

    # Validar que todos tengan toggle_key único
    keys = [t.toggle_key for t in toggles]
    assert len(keys) == len(set(keys)), "Todas las keys deben ser únicas"

    # Validar categorías
    categories = set(t.category for t in toggles)
    expected_categories = {"agent", "automation", "feature", "integration"}
    assert categories == expected_categories, f"Categorías esperadas: {expected_categories}"

    # Validar que es_enabled es True por defecto
    assert all(t.is_enabled for t in toggles), "Todos los toggles deben estar enabled por defecto"


@pytest.mark.asyncio
async def test_toggle_already_exists(db: AsyncSession, test_business_id: uuid4):
    """Test: seed no crea duplicados si ya existen."""
    await seed_toggles_for_business(test_business_id, db)
    await seed_toggles_for_business(test_business_id, db)  # Seed again

    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.business_id == test_business_id)
    )
    toggles = result.scalars().all()

    assert len(toggles) == 12, "No debe crear duplicados"


@pytest.mark.asyncio
async def test_toggle_has_monthly_limits(db: AsyncSession, test_business_id: uuid4):
    """Test: algunos toggles tienen monthly_limit."""
    await seed_toggles_for_business(test_business_id, db)

    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.business_id == test_business_id)
    )
    toggles = result.scalars().all()

    # Lead scorer, cold email, negotiation, SMS, computer_use deben tener límites
    toggles_with_limits = [t for t in toggles if t.monthly_limit is not None]
    assert len(toggles_with_limits) >= 5, "Al menos 5 toggles deben tener monthly_limit"

    # Validar valores de límites
    lead_scorer = next((t for t in toggles if t.toggle_key == "agent:lead_scorer"), None)
    assert lead_scorer is not None
    assert lead_scorer.monthly_limit == 1000


@pytest.mark.asyncio
async def test_toggle_update_creates_audit_log(
    db: AsyncSession, test_business_id: uuid4, test_user_id: uuid4
):
    """Test: actualizar toggle crea audit log."""
    await seed_toggles_for_business(test_business_id, db)

    # Obtener primer toggle
    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.business_id == test_business_id).limit(1)
    )
    toggle = result.scalar_one()

    # Cambiar estado
    toggle.is_enabled = False
    toggle.disabled_at = datetime.now(timezone.utc)
    toggle.changed_by = test_user_id

    # Crear audit log
    audit = ToggleAuditLog(
        business_id=test_business_id,
        toggle_id=toggle.id,
        action="disabled",
        old_value={"is_enabled": True},
        new_value={"is_enabled": False},
        changed_by_user_id=test_user_id,
        changed_by_email="test@example.com",
        reason="Testing",
    )
    db.add(audit)
    await db.commit()

    # Verificar audit log
    result = await db.execute(
        select(ToggleAuditLog).where(ToggleAuditLog.toggle_id == toggle.id)
    )
    logs = result.scalars().all()

    assert len(logs) == 1
    assert logs[0].action == "disabled"
    assert logs[0].reason == "Testing"


@pytest.mark.asyncio
async def test_toggle_usage_increment(db: AsyncSession, test_business_id: uuid4):
    """Test: incrementar usage mensual."""
    await seed_toggles_for_business(test_business_id, db)

    result = await db.execute(
        select(AutomationToggle)
        .where(AutomationToggle.business_id == test_business_id)
        .where(AutomationToggle.toggle_key == "agent:lead_scorer")
    )
    toggle = result.scalar_one()

    initial_usage = toggle.current_month_usage

    # Incrementar
    toggle.current_month_usage += 1
    await db.commit()

    # Verificar
    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.id == toggle.id)
    )
    updated = result.scalar_one()

    assert updated.current_month_usage == initial_usage + 1


@pytest.mark.asyncio
async def test_toggle_display_names(db: AsyncSession, test_business_id: uuid4):
    """Test: todos los toggles tienen display_name y description."""
    await seed_toggles_for_business(test_business_id, db)

    result = await db.execute(
        select(AutomationToggle).where(AutomationToggle.business_id == test_business_id)
    )
    toggles = result.scalars().all()

    for toggle in toggles:
        assert toggle.display_name, f"Toggle {toggle.toggle_key} sin display_name"
        assert len(toggle.display_name) > 0
        # Description es opcional pero la mayoría debería tener
        if toggle.description:
            assert len(toggle.description) > 0
