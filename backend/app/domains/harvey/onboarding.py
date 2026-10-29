"""Suggest a business's Harvey profile (offer, benefits, ideal client) from its own public website.

Nothing is saved: the person gets a suggestion, edits it and saves it. The site text is untrusted input to the
model (fenced), and the model is told to use only what the page says, so a benefit is never invented.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from app.domains.harvey import ai_budget
from app.domains.harvey import competitors as reader
from app.domains.harvey import discovery
from app.domains.harvey.competitors_service import clean_list
from app.domains.harvey.discovery import DiscoveryError
from app.domains.harvey.gate import UNTRUSTED_RULE, fence
from app.domains.harvey.llm import ask_json, llm_available

TEXT_CHARS = 2500


def _visible_text(html: str) -> str:
    parser = reader._Parser()
    try:
        parser.feed(html)
    except Exception:  # noqa: BLE001 - malformed markup: keep what was parsed
        pass
    return " ".join(" ".join(parser.text).split())[:TEXT_CHARS]


async def read_site(client: httpx.AsyncClient, raw_url: str) -> dict[str, Any]:
    """Title, description, headlines and the start of the visible text of the home page."""
    url = discovery.normalize_url(raw_url)
    parts = urlparse(url)
    root = f"{parts.scheme}://{parts.netloc}"
    if not await discovery.robots_allows(client, root):
        raise DiscoveryError("Ese sitio no permite que lo lean (robots.txt)")
    page = await discovery.fetch(client, root + "/")
    if page.status != 200:
        raise DiscoveryError(f"El sitio respondió {page.status}")
    found = reader.extract(page.text)
    return {
        "url": root,
        "title": found["title"],
        "description": found["description"],
        "headlines": found["headlines"],
        "text": _visible_text(page.text),
    }


def facts_only(site: dict[str, Any]) -> dict[str, Any]:
    """What can be said without a model: the page's own description and headlines, unedited."""
    return {
        "offer": (site["description"] or site["title"])[:600],
        "benefits": clean_list(site["headlines"], 5, 120),
        "keywords": [],
        "locations": [],
        "source": "facts",
    }


async def suggest(
    raw_url: str,
    business_name: str,
    client: httpx.AsyncClient | None = None,
    *,
    db: Any = None,
    business: Any = None,
) -> dict[str, Any]:
    """``db`` and ``business`` put the model call under the owner's monthly AI cap (without them it is not metered)."""
    own = client is None
    client = client or discovery.make_client()
    try:
        site = await read_site(client, raw_url)
    finally:
        if own:
            await client.aclose()

    out = facts_only(site)
    if llm_available():
        # Built outside the f-string: a backslash or the same quote inside {...} only parses on Python 3.12,
        # and production runs 3.11.
        headlines = "; ".join(site["headlines"])
        fenced_site = fence(
            "Título: " + site["title"] + "\nDescripción: " + site["description"]
            + "\nTitulares: " + headlines + "\nTexto: " + site["text"],
            "sitio del negocio",
        )
        prompt = f"""Armá el perfil comercial de "{business_name}" a partir de su sitio web.

{fenced_site}

{UNTRUSTED_RULE}

Reglas: usá SOLO lo que dice el sitio. No inventes beneficios, cifras, premios ni clientes. Si algo no está, dejalo vacío.
Respondé SOLO con JSON:
{{"offer": "1-2 frases: qué vende y a quién",
 "benefits": ["hasta 5 beneficios que el sitio afirma"],
 "keywords": ["hasta 5 palabras clave para encontrar clientes como los suyos"],
 "locations": ["zonas donde atiende, solo si el sitio las nombra"]}}"""
        system = "Sos un asistente comercial para pymes. Respondés SOLO con un objeto JSON."
        try:
            if db is not None and business is not None:
                async with ai_budget.metered(db, business):
                    result = await ask_json(system, prompt)
            else:
                result = await ask_json(system, prompt)
        except ai_budget.BudgetExceeded:
            result = None  # no AI left this month: the site's own words, as without a model
        if result and str(result.get("offer") or "").strip():
            out = {
                "offer": str(result["offer"]).strip()[:600],
                "benefits": clean_list(result.get("benefits"), 5, 140),
                "keywords": clean_list(result.get("keywords"), 5, 60),
                "locations": clean_list(result.get("locations"), 5, 60),
                "source": "model",
            }
    out["site"] = site["url"]
    return out
