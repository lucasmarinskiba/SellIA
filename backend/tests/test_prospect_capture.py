"""Real prospect capture: Google Places search, CSV import and dedupe.

No network and no database: Places is replaced with httpx.MockTransport and the
AsyncSession with mocks. Nothing here should ever produce contact data that was
not in the input.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import HTTPException

from app.api.v1 import business_intelligence
from app.domains.lead_generation import places_source
from app.domains.lead_generation.places_source import (
    PlaceProspect,
    PlacesAPIError,
    PlacesNotConfiguredError,
    parse_text_search_response,
    search_places,
)
from app.domains.lead_generation.prospect_capture import (
    MAX_CSV_ROWS,
    parse_csv_contacts,
    save_csv_contacts,
    save_place_prospects,
)


def _place(place_id: str, name: str, **extra: object) -> dict:
    return {"id": place_id, "displayName": {"text": name, "languageCode": "es"}, **extra}


def _db_with_stored(contact_infos: list[dict]) -> MagicMock:
    """Mock AsyncSession whose select returns the given stored contact_info dicts."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = contact_infos
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.add_all = MagicMock()
    return db


# ---------- Google Places parsing ----------

def test_parse_keeps_open_places_and_maps_fields():
    payload = {
        "places": [
            _place(
                "p1",
                "Peluquería Luna",
                formattedAddress="Av. Pellegrini 1000, Rosario",
                nationalPhoneNumber="0341 444-5555",
                websiteUri="https://luna.example",
                googleMapsUri="https://maps.google.com/?cid=1",
                rating=4.7,
                userRatingCount=132,
                businessStatus="OPERATIONAL",
            )
        ]
    }

    prospects = parse_text_search_response(payload)

    assert prospects == [
        PlaceProspect(
            place_id="p1",
            name="Peluquería Luna",
            address="Av. Pellegrini 1000, Rosario",
            phone="0341 444-5555",
            website="https://luna.example",
            maps_url="https://maps.google.com/?cid=1",
            rating=4.7,
            review_count=132,
        )
    ]


def test_parse_drops_permanently_closed_and_incomplete_places():
    payload = {
        "places": [
            _place("closed", "Cerró", businessStatus="CLOSED_PERMANENTLY"),
            {"id": "no-name", "displayName": {}},
            {"displayName": {"text": "Sin id"}},
            _place("ok", "Abierto", businessStatus="OPERATIONAL"),
        ]
    }

    assert [p.place_id for p in parse_text_search_response(payload)] == ["ok"]


def test_parse_empty_payload_returns_nothing():
    assert parse_text_search_response({}) == []


# ---------- Places HTTP client ----------

async def test_search_without_key_raises_not_configured(monkeypatch):
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)

    with pytest.raises(PlacesNotConfiguredError):
        await search_places("peluquería", "Rosario")


async def test_search_sends_key_mask_and_clamped_limit(monkeypatch):
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test-key")
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers["X-Goog-Api-Key"]
        seen["mask"] = request.headers["X-Goog-FieldMask"]
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"places": [_place("p1", "Luna", businessStatus="OPERATIONAL")]})

    prospects = await search_places("peluquería", "Rosario", 50, transport=httpx.MockTransport(handler))

    assert [p.place_id for p in prospects] == ["p1"]
    assert seen["url"] == places_source.PLACES_TEXT_SEARCH_URL
    assert seen["key"] == "test-key"
    assert "places.nationalPhoneNumber" in seen["mask"]
    body = json.loads(seen["body"])
    assert body["textQuery"] == "peluquería Rosario"
    assert body["maxResultCount"] == 20


async def test_search_error_maps_to_places_api_error_without_leaking_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "secret-key-123")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "API key not valid"}})

    with pytest.raises(PlacesAPIError) as excinfo:
        await search_places("peluquería", transport=httpx.MockTransport(handler))

    assert excinfo.value.status_code == 403
    assert "API key not valid" in str(excinfo.value)
    assert "secret-key-123" not in str(excinfo.value)


async def test_network_failure_maps_to_places_api_error(monkeypatch):
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(PlacesAPIError) as excinfo:
        await search_places("peluquería", transport=httpx.MockTransport(handler))

    assert excinfo.value.status_code == 502


# ---------- CSV import ----------

def test_csv_accepts_valid_rows_and_normalizes_email():
    raw = "Name,Email,Phone\nMaría,MARIA@Mail.com,+54 11 4444-5555\n".encode("utf-8")

    result = parse_csv_contacts(raw)

    assert result.rejected_count == 0
    assert result.contacts[0]["name"] == "María"
    assert result.contacts[0]["email"] == "maria@mail.com"


def test_csv_rejects_bad_rows_with_reasons():
    raw = (
        "name,email,phone\n"
        ",ana@mail.com,\n"            # sin nombre
        "Juan,,\n"                    # sin email ni teléfono
        "Lu,no-es-email,\n"           # email inválido
        "Pedro,pedro@mail.com,\n"
        "Pedro 2,PEDRO@mail.com,\n"   # duplicado dentro del archivo
    ).encode("utf-8")

    result = parse_csv_contacts(raw)

    assert [c["name"] for c in result.contacts] == ["Pedro"]
    assert result.rejected_count == 4
    assert [r["reason"] for r in result.rejected] == [
        "falta el nombre",
        "falta email o teléfono",
        "email inválido",
        "duplicado dentro del archivo",
    ]


def test_csv_duplicate_phone_inside_file_is_rejected():
    raw = "name,phone\nA,+54 11 4444-5555\nB,54 11 4444 5555\n".encode("utf-8")

    result = parse_csv_contacts(raw)

    assert [c["name"] for c in result.contacts] == ["A"]
    assert result.rejected[0]["reason"] == "duplicado dentro del archivo"


def test_csv_without_name_column_is_fatal():
    with pytest.raises(ValueError, match="columna 'name'"):
        parse_csv_contacts("email\nana@mail.com\n".encode("utf-8"))


def test_csv_non_utf8_is_fatal():
    with pytest.raises(ValueError, match="UTF-8"):
        parse_csv_contacts("name\nJosé\n".encode("latin-1") + b"\xff\xfe")


def test_csv_row_limit_is_fatal():
    rows = "\n".join(f"Persona {i},p{i}@mail.com," for i in range(MAX_CSV_ROWS + 1))
    raw = f"name,email,phone\n{rows}\n".encode("utf-8")

    with pytest.raises(ValueError, match="máximo"):
        parse_csv_contacts(raw)


# ---------- Persistence and dedupe (mocked session) ----------

async def test_place_capture_skips_place_ids_already_stored():
    business_id = uuid.uuid4()
    db = _db_with_stored([{"place_id": "p1", "name": "Ya cargado"}])
    prospects = [
        PlaceProspect("p1", "Ya cargado", None, None, None, None, None, None),
        PlaceProspect("p2", "Nuevo", "Calle 1", "+54 341 000", None, None, 4.5, 10),
    ]

    outcome = await save_place_prospects(db, business_id, prospects, "peluquería")

    assert outcome.skipped_duplicates == 1
    assert [c["place_id"] for c in outcome.created] == ["p2"]
    saved = db.add_all.call_args.args[0]
    assert len(saved) == 1
    assert saved[0].contact_info["name"] == "Nuevo"
    assert saved[0].source_detail == "google_places: peluquería"
    db.commit.assert_awaited_once()


async def test_csv_capture_skips_existing_email_or_phone():
    business_id = uuid.uuid4()
    db = _db_with_stored([{"email": "ana@mail.com", "phone": "+54 11 4444-5555"}])
    contacts = [
        {"name": "Ana", "email": "ana@mail.com", "phone": "", "company": "", "website": ""},
        {"name": "Juan", "email": "", "phone": "54 11 4444 5555", "company": "", "website": ""},
        {"name": "Lu", "email": "lu@mail.com", "phone": "", "company": "", "website": ""},
    ]

    outcome = await save_csv_contacts(db, business_id, contacts, "clientes.csv")

    assert outcome.skipped_duplicates == 2
    assert [c["name"] for c in outcome.created] == ["Lu"]
    saved = db.add_all.call_args.args[0]
    assert saved[0].source_detail == "csv_import: clientes.csv"
    assert "company" not in saved[0].contact_info  # campos vacíos no se guardan


async def test_nothing_new_means_no_commit():
    db = _db_with_stored([{"place_id": "p1"}])

    outcome = await save_place_prospects(
        db, uuid.uuid4(), [PlaceProspect("p1", "Ya", None, None, None, None, None, None)], "x"
    )

    assert outcome.created == []
    db.add_all.assert_not_called()
    db.commit.assert_not_awaited()


# ---------- Business-intelligence endpoint (no more invented leads) ----------

async def test_find_prospects_returns_real_search_results(monkeypatch):
    fake_search = AsyncMock(return_value=[
        PlaceProspect("p1", "Luna", "Av. 1", "+54 341 1", None, None, 4.0, 3),
    ])
    monkeypatch.setattr(business_intelligence, "search_places", fake_search)

    response = await business_intelligence.find_prospects(
        query="peluquería", location="Rosario", limit=5, current_user=MagicMock()
    )

    fake_search.assert_awaited_once_with("peluquería", "Rosario", 5)
    assert response["count"] == 1
    assert response["prospects"][0]["place_id"] == "p1"
    assert "email" not in response["prospects"][0]


async def test_find_prospects_without_key_is_503(monkeypatch):
    monkeypatch.setattr(
        business_intelligence,
        "search_places",
        AsyncMock(side_effect=PlacesNotConfiguredError("Falta GOOGLE_PLACES_API_KEY")),
    )

    with pytest.raises(HTTPException) as excinfo:
        await business_intelligence.find_prospects(
            query="peluquería", location="", limit=5, current_user=MagicMock()
        )

    assert excinfo.value.status_code == 503


# ---------- HTTP wiring (dependencies overridden, no DB) ----------

@pytest.fixture
def growth_client(monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.core.deps import get_current_user
    from app.domains.growth import router as growth_router
    from app.main import app

    db = _db_with_stored([])
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: MagicMock()
    monkeypatch.setattr(growth_router, "resolve_business_id", AsyncMock(return_value=uuid.uuid4()))
    try:
        yield TestClient(app), growth_router, db
    finally:
        app.dependency_overrides.clear()


def test_csv_endpoint_saves_valid_rows_and_reports_rejections(growth_client):
    client, _, db = growth_client
    csv_bytes = b"name,email\nAna,ana@mail.com\nsin-email,\n"

    response = client.post(
        "/api/v1/growth/leads/import",
        files={"file": ("clientes.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 1
    assert body["rejected_count"] == 1
    assert body["rejected"][0]["reason"] == "falta email o teléfono"
    db.add_all.assert_called_once()


def test_prospect_search_without_key_returns_503(growth_client, monkeypatch):
    client, growth_router, _ = growth_client
    monkeypatch.setattr(
        growth_router,
        "search_places",
        AsyncMock(side_effect=PlacesNotConfiguredError("Falta GOOGLE_PLACES_API_KEY en el entorno")),
    )

    response = client.post(
        "/api/v1/growth/prospects/search",
        json={"query": "peluquería", "location": "Rosario", "limit": 5},
    )

    assert response.status_code == 503
    assert "GOOGLE_PLACES_API_KEY" in response.json()["detail"]


def test_prospect_search_saves_only_new_places(growth_client, monkeypatch):
    client, growth_router, db = growth_client
    db.execute.return_value.scalars.return_value.all.return_value = [{"place_id": "p1"}]
    monkeypatch.setattr(
        growth_router,
        "search_places",
        AsyncMock(return_value=[
            PlaceProspect("p1", "Ya", None, None, None, None, None, None),
            PlaceProspect("p2", "Nuevo", "Calle 1", "+54 341 000", None, None, 4.5, 10),
        ]),
    )

    response = client.post(
        "/api/v1/growth/prospects/search",
        json={"query": "peluquería", "location": "Rosario", "limit": 5},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["found"] == 2
    assert body["created"] == 1
    assert body["skipped_duplicates"] == 1
    assert body["prospects"][0]["place_id"] == "p2"
