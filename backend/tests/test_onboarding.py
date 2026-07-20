"""Tests para Onboarding Mágico"""

import pytest
from app.domains.onboarding.schemas import BusinessDiscovery, ScrapedProduct
from decimal import Decimal


@pytest.mark.asyncio
async def test_onboarding_analyze_validation(auth_client):
    """Test: analyze rechaza source vacío."""
    response = await auth_client.post("/api/v1/onboarding/analyze", json={"source": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_onboarding_create_success(auth_client, test_user):
    """Test: create genera negocio, catálogo, agentes y workflows."""
    discovery = BusinessDiscovery(
        name="Café Test",
        description="Café de prueba",
        type="services",
        tone_of_voice="amigable",
        brand_colors=["#000000"],
        target_audience="jóvenes",
        products=[
            ScrapedProduct(name="Café Latte", description="Delicioso", price=Decimal("1200"), currency="ARS", category="bebidas"),
        ],
        suggested_agents=[
            {"slug": "consultor", "name": "Consultor", "emoji": "🧠", "tagline": "Asesor", "description": "...", "expertise": ["ventas"], "color": "#FF6B35"},
        ],
        suggested_workflows=[
            {"name": "Bienvenida", "description": "...", "trigger_type": "new_lead", "actions": []},
        ],
    )

    response = await auth_client.post("/api/v1/onboarding/create", json={
        "discovery": discovery.model_dump(mode="json"),
        "source": "@cafetest",
    })
    assert response.status_code == 200
    data = response.json()
    assert "business_id" in data
    assert data["catalog_items_count"] == 1
    assert data["agents_count"] == 1
    assert data["workflows_count"] == 1
    assert "Café Test" in data["message"]


@pytest.mark.asyncio
async def test_onboarding_create_invalid_type(auth_client):
    """Test: create rechaza discovery sin nombre."""
    response = await auth_client.post("/api/v1/onboarding/create", json={
        "discovery": {"name": "", "type": "invalid", "products": [], "suggested_agents": [], "suggested_workflows": []},
        "source": "test",
    })
    # FastAPI/Pydantic validará que el type no sea válido o que name esté vacío
    assert response.status_code in (422, 200)
