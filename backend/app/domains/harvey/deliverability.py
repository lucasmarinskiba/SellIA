"""Will this business's email reach the inbox? Reads the sender domain's public DNS (SPF, DKIM, DMARC).

Explained in plain words, with what to do. Read-only: it only looks up public DNS records. A free mailbox
(Gmail, Outlook, ...) is skipped: the provider already signs and authenticates its own mail.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from app.domains.channels.email_setup import detect_provider

# Selectors the big providers and hosts use by default. A custom selector cannot be guessed.
DKIM_SELECTORS = ("google", "selector1", "selector2", "default", "k1", "k2", "mail", "dkim", "s1", "s2", "zoho", "mandrill")
_FREE = {"gmail", "outlook", "yahoo", "icloud", "zoho"}

Resolver = Callable[[str], list[str]]


def dns_txt(name: str) -> list[str]:
    """TXT records of a name, or [] when there are none or DNS is unreachable."""
    try:
        import dns.resolver  # transitive dependency of email-validator

        answers = dns.resolver.resolve(name, "TXT", lifetime=4)
        return ["".join(part.decode("utf-8", "replace") for part in r.strings) for r in answers]
    except Exception:  # noqa: BLE001 - NXDOMAIN, no answer, timeout: all mean "nothing found"
        return []


def _item(key: str, status: str, title: str, detail: str, fix: str = "") -> dict[str, Any]:
    return {"key": key, "status": status, "title": title, "detail": detail, "fix": fix}


def check_spf(records: list[str]) -> dict[str, Any]:
    spf = [r for r in records if r.lower().startswith("v=spf1")]
    if not spf:
        return _item(
            "spf", "bad", "Autorización de envío (SPF) ausente",
            "Sin este registro, muchos servidores marcan tus emails como sospechosos.",
            "Agregá en el DNS de tu dominio un registro TXT que autorice a tu proveedor de correo (él te da el texto exacto).",
        )
    if len(spf) > 1:
        return _item(
            "spf", "bad", "SPF duplicado", "Tenés más de un registro SPF y eso lo invalida.",
            "Dejá un solo registro SPF que junte todos los servicios que envían por vos.",
        )
    r = spf[0].lower()
    if "+all" in r or r.endswith(" ?all"):
        return _item("spf", "warn", "SPF demasiado permisivo", "Autoriza a cualquiera a enviar en tu nombre.", "Terminalo en ~all o -all.")
    return _item("spf", "ok", "Autorización de envío (SPF) correcta", "Tu dominio declara quién puede enviar por él.")


def check_dmarc(records: list[str]) -> dict[str, Any]:
    dmarc = [r for r in records if r.lower().replace(" ", "").startswith("v=dmarc1")]
    if not dmarc:
        return _item(
            "dmarc", "bad", "Política DMARC ausente",
            "Gmail y Yahoo la piden a quienes envían muchos emails; sin ella aumenta el riesgo de spam.",
            "Agregá un registro TXT en _dmarc.tudominio con: v=DMARC1; p=none; rua=mailto:tu@email.com",
        )
    if "p=none" in dmarc[0].lower().replace(" ", ""):
        return _item(
            "dmarc", "warn", "DMARC en modo observación",
            "Está bien para empezar. Cuando todo funcione, endurecerlo mejora la protección.",
            "Más adelante, cambiá p=none por p=quarantine.",
        )
    return _item("dmarc", "ok", "Política DMARC activa", "Tu dominio indica qué hacer con los emails falsificados.")


def check_dkim(found_selector: str | None) -> dict[str, Any]:
    if found_selector:
        return _item("dkim", "ok", "Firma de los emails (DKIM) encontrada", f"Detectamos la firma ({found_selector}).")
    return _item(
        "dkim", "unknown", "No pudimos confirmar la firma (DKIM)",
        "Puede estar bien: cada proveedor usa un nombre propio que no siempre podemos adivinar.",
        "Pedile a tu proveedor de correo que confirme que DKIM está activo para tu dominio.",
    )


async def check_domain(email: str, resolver: Resolver = dns_txt) -> dict[str, Any]:
    _, at, domain = (email or "").rpartition("@")
    domain = domain.strip().lower()
    if not at or not domain:
        return {"domain": "", "free_mail": False, "score": None, "items": []}
    if detect_provider(email).key in _FREE:
        return {"domain": domain, "free_mail": True, "score": None, "items": []}

    async def txt(name: str) -> list[str]:
        return await asyncio.to_thread(resolver, name)

    spf, dmarc, *dkim_hits = await asyncio.gather(
        txt(domain), txt(f"_dmarc.{domain}"), *(txt(f"{s}._domainkey.{domain}") for s in DKIM_SELECTORS)
    )
    selector = next((s for s, recs in zip(DKIM_SELECTORS, dkim_hits, strict=True) if any("v=dkim1" in r.lower() or "p=" in r for r in recs)), None)
    items = [check_spf(spf), check_dkim(selector), check_dmarc(dmarc)]
    graded = [i for i in items if i["status"] != "unknown"]
    score = round(100 * sum(1 for i in graded if i["status"] == "ok") / len(graded)) if graded else None
    return {"domain": domain, "free_mail": False, "score": score, "items": items}
