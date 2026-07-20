"""Tests de integración para Computer Use API.

Testea la REST API de sesiones de Computer Use y el endpoint WebSocket.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.computer_use.models import ComputerUseSession


@pytest_asyncio.fixture
async def mock_user(db_session):
    """Crea un usuario mock para tests y lo persiste en DB."""
    user = User(
        id=uuid4(),
        email=f"test-computer-use-{uuid4()}@example.com",
        hashed_password="hashed",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_client(async_client, mock_user):
    """Cliente HTTP con usuario autenticado mock."""
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    yield async_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_session(auth_client):
    """Test: crear una sesión de Computer Use."""
    response = await auth_client.post("/api/v1/computer-use/sessions", json={
        "task_description": "Navegar a google.com y buscar 'test'",
        "start_url": "https://google.com",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["task_description"] == "Navegar a google.com y buscar 'test'"
    assert data["status"] == "pending"
    assert data["current_url"] == "https://google.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_session_without_url(auth_client):
    """Test: crear sesión sin URL inicial."""
    response = await auth_client.post("/api/v1/computer-use/sessions", json={
        "task_description": "Crear un post en Instagram",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["current_url"] is None


@pytest.mark.asyncio
async def test_create_session_disabled(auth_client, monkeypatch):
    """Test: Computer Use deshabilitado debe rechazar."""
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "COMPUTER_USE_ENABLED", False)

    response = await auth_client.post("/api/v1/computer-use/sessions", json={
        "task_description": "Test",
    })
    assert response.status_code == 403
    assert "deshabilitado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_session_rate_limit(auth_client):
    """Test: límite de 3 sesiones concurrentes."""
    # Crear 3 sesiones
    for i in range(3):
        response = await auth_client.post("/api/v1/computer-use/sessions", json={
            "task_description": f"Test session {i}",
        })
        assert response.status_code == 201

    # La 4ta debe fallar
    response = await auth_client.post("/api/v1/computer-use/sessions", json={
        "task_description": "Test session 4",
    })
    assert response.status_code == 429
    assert "3 sesiones activas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_sessions(auth_client):
    """Test: listar sesiones del usuario."""
    # Crear una sesión
    create_resp = await auth_client.post("/api/v1/computer-use/sessions", json={
        "task_description": "List test",
    })
    session_id = create_resp.json()["id"]

    # Listar
    response = await auth_client.get("/api/v1/computer-use/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(s["id"] == session_id for s in data["items"])


@pytest.mark.asyncio
async def test_get_session(auth_client):
    """Test: obtener detalle de una sesión."""
    create_resp = await auth_client.post("/api/v1/computer-use/sessions", json={
        "task_description": "Get test",
    })
    session_id = create_resp.json()["id"]

    response = await auth_client.get(f"/api/v1/computer-use/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["task_description"] == "Get test"


@pytest.mark.asyncio
async def test_get_session_not_found(auth_client):
    """Test: sesión inexistente debe devolver 404."""
    fake_id = str(uuid4())
    response = await auth_client.get(f"/api/v1/computer-use/sessions/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(auth_client):
    """Test: eliminar una sesión."""
    create_resp = await auth_client.post("/api/v1/computer-use/sessions", json={
        "task_description": "Delete test",
    })
    session_id = create_resp.json()["id"]

    response = await auth_client.delete(f"/api/v1/computer-use/sessions/{session_id}")
    assert response.status_code == 200

    # Verificar que ya no existe
    get_resp = await auth_client.get(f"/api/v1/computer-use/sessions/{session_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_start_session_no_api_key(auth_client, monkeypatch):
    """Test: iniciar sesión sin API key debe fallar."""
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)

    create_resp = await auth_client.post("/api/v1/computer-use/sessions", json={
        "task_description": "Start test",
    })
    session_id = create_resp.json()["id"]

    response = await auth_client.post(f"/api/v1/computer-use/sessions/{session_id}/start")
    assert response.status_code == 400
    assert "API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_orchestrator_integration(auth_client, mock_user, db_session):
    """Test: el orchestrator puede crear una sesión de Computer Use."""
    from app.api.v1.computer_use import create_computer_use_from_orchestrator

    result = await create_computer_use_from_orchestrator(
        db=db_session,
        user_id=mock_user.id,
        business_id=None,
        task="Crear un banner en Canva",
        start_url="https://canva.com",
    )
    assert result.action == "COMPUTER_USE"
    assert result.task == "Crear un banner en Canva"
    assert result.session_id is not None
    assert "/ws/computer-use/" in result.ws_url
