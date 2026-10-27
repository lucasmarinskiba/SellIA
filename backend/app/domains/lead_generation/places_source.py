"""Prospect discovery through the Google Places API (Text Search, New).

Real data source for the growth funnel: returns the businesses Google lists for
a query, with the phone, website and address they publish. It needs
GOOGLE_PLACES_API_KEY. Without the key nothing is invented: callers get
PlacesNotConfiguredError.

Google's terms allow keeping place_id indefinitely but the other fields only for
a limited time, so refresh or purge stored contact_info older than 30 days.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
# Only the fields we store. Each field in the mask is billed at its SKU tier,
# so keep this list short.
PLACES_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,"
    "places.websiteUri,places.googleMapsUri,places.rating,places.userRatingCount,"
    "places.businessStatus"
)
MAX_RESULTS_PER_QUERY = 20  # Text Search (New) caps a single page at 20
REQUEST_TIMEOUT_SECONDS = 10.0


class PlacesNotConfiguredError(RuntimeError):
    """GOOGLE_PLACES_API_KEY is not set, so no prospect search can run."""


class PlacesAPIError(RuntimeError):
    """Google answered with an error. The message never contains the key."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Google Places respondió {status_code}: {message}")
        self.status_code = status_code


@dataclass(frozen=True)
class PlaceProspect:
    place_id: str
    name: str
    address: str | None
    phone: str | None
    website: str | None
    maps_url: str | None
    rating: float | None
    review_count: int | None

    def to_contact_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "phone": self.phone,
            "website": self.website,
            "address": self.address,
            "maps_url": self.maps_url,
            "place_id": self.place_id,
            "rating": self.rating,
            "review_count": self.review_count,
        }


def parse_text_search_response(payload: dict[str, Any]) -> list[PlaceProspect]:
    """Turn a Text Search payload into prospects. Drops closed and unnamed places."""
    prospects: list[PlaceProspect] = []
    for place in payload.get("places", []):
        if place.get("businessStatus") == "CLOSED_PERMANENTLY":
            continue
        place_id = place.get("id")
        name = (place.get("displayName") or {}).get("text")
        if not place_id or not name:
            continue
        prospects.append(PlaceProspect(
            place_id=place_id,
            name=name,
            address=place.get("formattedAddress"),
            phone=place.get("nationalPhoneNumber"),
            website=place.get("websiteUri"),
            maps_url=place.get("googleMapsUri"),
            rating=place.get("rating"),
            review_count=place.get("userRatingCount"),
        ))
    return prospects


def _read_api_key() -> str:
    key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not key:
        raise PlacesNotConfiguredError("Falta GOOGLE_PLACES_API_KEY en el entorno")
    return key


def _error_message(response: httpx.Response) -> str:
    try:
        return str(response.json().get("error", {}).get("message", "sin detalle"))
    except ValueError:
        return response.text[:200]


async def search_places(
    query: str,
    location: str | None = None,
    limit: int = MAX_RESULTS_PER_QUERY,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[PlaceProspect]:
    """Search Google Places for `query` (optionally inside `location`).

    `transport` exists so tests can replace the network; production leaves it None.
    """
    api_key = _read_api_key()
    text_query = " ".join(part for part in (query.strip(), (location or "").strip()) if part)
    body = {
        "textQuery": text_query,
        "maxResultCount": max(1, min(limit, MAX_RESULTS_PER_QUERY)),
        "languageCode": "es",
    }
    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": PLACES_FIELD_MASK}

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, transport=transport) as client:
            response = await client.post(PLACES_TEXT_SEARCH_URL, json=body, headers=headers)
    except httpx.HTTPError as exc:
        logger.warning("Places text search network error: %s", type(exc).__name__)
        raise PlacesAPIError(502, "sin conexión o tiempo de espera agotado") from exc

    if response.status_code != 200:
        logger.warning("Places text search failed: status=%s", response.status_code)
        raise PlacesAPIError(response.status_code, _error_message(response))

    return parse_text_search_response(response.json())
