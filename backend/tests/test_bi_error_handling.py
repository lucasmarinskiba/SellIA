"""business-intelligence: un error interno devuelve 500 sin filtrar el detalle al cliente."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import business_intelligence as bi


def test_analyze_business_hides_internal_error_detail(monkeypatch):
    monkeypatch.setattr(
        bi.detector,
        "detect_model",
        MagicMock(side_effect=RuntimeError("falló el pool con la clave hunter2")),
    )
    app = FastAPI()
    app.include_router(bi.router, prefix="/api/v1")
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/v1/business-intelligence/analyze-business",
        params={"business_description": "panadería"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "No se pudo analizar el negocio"
    assert "hunter2" not in response.text
