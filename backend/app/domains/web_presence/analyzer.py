"""Real on-page SEO analysis of HTML that was actually fetched.

Everything reported here is READ OUT OF THE PAGE — the title that is really in
the <head>, the images that really have no alt, the JSON-LD blocks that really
parse. Nothing is modelled, sampled or estimated. The things this deployment
genuinely cannot measure without a paid API (search volume, keyword difficulty,
lab Core Web Vitals) are deliberately absent rather than invented; what IS
measurable for free — TTFB, page weight, structured data, on-page hygiene,
cross-linking between the account's own properties — is measured properly.

Parsing uses the stdlib html.parser: adding beautifulsoup4/lxml to
requirements.txt for this would be a new build dependency on the Railway image
for markup this simple.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}

# Google truncates around these; they are display limits, not guesses.
TITLE_MIN, TITLE_MAX = 30, 60
DESC_MIN, DESC_MAX = 70, 160


@dataclass
class PageAudit:
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical: Optional[str] = None
    robots: Optional[str] = None
    lang: Optional[str] = None
    has_viewport: bool = False
    h1: list[str] = field(default_factory=list)
    h2_count: int = 0
    h3_count: int = 0
    images_total: int = 0
    images_without_alt: int = 0
    internal_links: int = 0
    external_links: int = 0
    external_hosts: list[str] = field(default_factory=list)
    json_ld_types: list[str] = field(default_factory=list)
    json_ld_invalid: int = 0
    json_ld_same_as: list[str] = field(default_factory=list)
    open_graph: dict[str, str] = field(default_factory=dict)
    twitter_card: dict[str, str] = field(default_factory=dict)
    word_count: int = 0
    is_https: bool = False
    issues: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "title_length": len(self.title) if self.title else 0,
            "meta_description": self.meta_description,
            "meta_description_length": len(self.meta_description) if self.meta_description else 0,
            "canonical": self.canonical,
            "robots": self.robots,
            "lang": self.lang,
            "has_viewport": self.has_viewport,
            "h1": self.h1,
            "h2_count": self.h2_count,
            "h3_count": self.h3_count,
            "images_total": self.images_total,
            "images_without_alt": self.images_without_alt,
            "internal_links": self.internal_links,
            "external_links": self.external_links,
            "external_hosts": self.external_hosts,
            "json_ld_types": self.json_ld_types,
            "json_ld_invalid": self.json_ld_invalid,
            "json_ld_same_as": self.json_ld_same_as,
            "open_graph": self.open_graph,
            "twitter_card": self.twitter_card,
            "word_count": self.word_count,
            "is_https": self.is_https,
            "issues": self.issues,
        }


class _PageParser(HTMLParser):
    """Pulls the SEO-relevant bits out of a page in one pass."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.audit = PageAudit()
        self._skip_depth = 0            # inside <script>/<style>/<noscript>
        self._in_title = False
        self._in_ld_json = False
        self._ld_buffer: list[str] = []
        self._heading: Optional[str] = None
        self._text_parts: list[str] = []
        self.raw_links: list[str] = []

    # ── tags ──
    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}

        if tag in ("script", "style", "noscript"):
            if tag == "script" and "ld+json" in a.get("type", "").lower():
                self._in_ld_json = True
                self._ld_buffer = []
            self._skip_depth += 1
            return

        if tag == "html":
            self.audit.lang = a.get("lang") or None
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            self._handle_meta(a)
        elif tag == "link" and "canonical" in a.get("rel", "").lower():
            self.audit.canonical = a.get("href") or None
        elif tag in ("h1", "h2", "h3"):
            self._heading = tag
            if tag == "h2":
                self.audit.h2_count += 1
            elif tag == "h3":
                self.audit.h3_count += 1
        elif tag == "img":
            self.audit.images_total += 1
            if not a.get("alt", "").strip():
                self.audit.images_without_alt += 1
        elif tag == "a":
            href = a.get("href", "").strip()
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                self.raw_links.append(href)

    def _handle_meta(self, a: dict[str, str]) -> None:
        name = a.get("name", "").lower()
        prop = a.get("property", "").lower()
        content = a.get("content", "").strip()
        if name == "description":
            self.audit.meta_description = content or None
        elif name == "robots":
            self.audit.robots = content or None
        elif name == "viewport":
            self.audit.has_viewport = True
        elif prop.startswith("og:"):
            self.audit.open_graph[prop] = content
        elif name.startswith("twitter:"):
            self.audit.twitter_card[name] = content

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            if tag == "script" and self._in_ld_json:
                self._consume_ld_json("".join(self._ld_buffer))
                self._in_ld_json = False
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3"):
            self._heading = None

    def handle_data(self, data: str) -> None:
        if self._in_ld_json:
            self._ld_buffer.append(data)
            return
        if self._skip_depth:
            return
        if self._in_title:
            self.audit.title = ((self.audit.title or "") + data).strip() or None
            return
        if self._heading == "h1":
            text = data.strip()
            if text:
                self.audit.h1.append(text)
        self._text_parts.append(data)

    # ── structured data ──
    def _consume_ld_json(self, blob: str) -> None:
        blob = blob.strip()
        if not blob:
            return
        try:
            parsed = json.loads(blob)
        except (ValueError, TypeError):
            self.audit.json_ld_invalid += 1
            return
        for node in _iter_ld_nodes(parsed):
            node_type = node.get("@type")
            for t in (node_type if isinstance(node_type, list) else [node_type]):
                if isinstance(t, str) and t not in self.audit.json_ld_types:
                    self.audit.json_ld_types.append(t)
            same_as = node.get("sameAs")
            if isinstance(same_as, str):
                same_as = [same_as]
            if isinstance(same_as, list):
                for s in same_as:
                    if isinstance(s, str) and s not in self.audit.json_ld_same_as:
                        self.audit.json_ld_same_as.append(s)

    @property
    def text(self) -> str:
        return " ".join(self._text_parts)


def _iter_ld_nodes(value: Any) -> list[dict[str, Any]]:
    """Flatten a JSON-LD document (which may be a graph, a list, or nested)."""
    out: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            out.extend(_iter_ld_nodes(item))
    elif isinstance(value, dict):
        out.append(value)
        for key in ("@graph", "mainEntity", "itemListElement"):
            if key in value:
                out.extend(_iter_ld_nodes(value[key]))
    return out


def analyze(html: str, final_url: str) -> PageAudit:
    """Parse a real page body into a real audit."""
    parser = _PageParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # noqa: BLE001 -- malformed markup must still yield what we got
        pass

    audit = parser.audit
    audit.is_https = final_url.lower().startswith("https://")
    audit.word_count = len([w for w in re.split(r"\s+", parser.text) if len(w) > 1])

    base_host = (urlparse(final_url).hostname or "").lower().lstrip("www.")
    hosts: list[str] = []
    for href in parser.raw_links:
        host = (urlparse(urljoin(final_url, href)).hostname or "").lower().lstrip("www.")
        if not host or host == base_host:
            audit.internal_links += 1
        else:
            audit.external_links += 1
            if host not in hosts:
                hosts.append(host)
    audit.external_hosts = hosts[:60]

    audit.issues = _find_issues(audit)
    return audit


def _find_issues(a: PageAudit) -> list[dict[str, str]]:
    """Concrete, checkable problems — each with the fix, not just a complaint."""
    issues: list[dict[str, str]] = []

    def add(severity: str, key: str, title: str, detail: str, fix: str) -> None:
        issues.append({"severity": severity, "key": key, "title": title, "detail": detail, "fix": fix})

    if not a.title:
        add("critical", "title_missing", "Falta el <title>",
            "La página no tiene título. Google lo usa como el enlace azul del resultado.",
            "Agregá <title> con la keyword principal + la marca, entre 30 y 60 caracteres.")
    elif len(a.title) > TITLE_MAX:
        add("warning", "title_long", "Título demasiado largo",
            f"Tiene {len(a.title)} caracteres; Google corta cerca de {TITLE_MAX}.",
            f"Recortalo a {TITLE_MAX} caracteres dejando la keyword al principio.")
    elif len(a.title) < TITLE_MIN:
        add("warning", "title_short", "Título demasiado corto",
            f"Tiene {len(a.title)} caracteres: estás desperdiciando espacio en el resultado.",
            f"Llevalo a entre {TITLE_MIN} y {TITLE_MAX} caracteres sumando el beneficio o la ciudad.")

    if not a.meta_description:
        add("critical", "desc_missing", "Falta la meta description",
            "Sin meta description, Google arma el resumen con texto suelto de la página.",
            f"Agregá <meta name=\"description\"> de {DESC_MIN}-{DESC_MAX} caracteres con la promesa y un CTA.")
    elif len(a.meta_description) > DESC_MAX:
        add("warning", "desc_long", "Meta description demasiado larga",
            f"Tiene {len(a.meta_description)} caracteres; se corta cerca de {DESC_MAX}.",
            f"Recortala a {DESC_MAX} caracteres.")

    if not a.h1:
        add("critical", "h1_missing", "No hay H1",
            "La página no declara de qué trata con un encabezado principal.",
            "Poné un solo <h1> con el tema principal de la página.")
    elif len(a.h1) > 1:
        add("warning", "h1_multiple", f"Hay {len(a.h1)} H1",
            "Varios H1 diluyen cuál es el tema principal.",
            "Dejá un único <h1> y bajá el resto a <h2>.")

    if a.robots and "noindex" in a.robots.lower():
        add("critical", "noindex", "La página está bloqueada con noindex",
            f"La meta robots dice \"{a.robots}\": Google no la va a mostrar nunca.",
            "Sacá noindex de la meta robots si querés posicionar esta página.")

    if not a.is_https:
        add("critical", "no_https", "El sitio no usa HTTPS",
            "HTTPS es señal de ranking y el navegador marca el sitio como no seguro.",
            "Activá el certificado SSL (gratis con Let's Encrypt o en tu hosting).")

    if not a.canonical:
        add("info", "canonical_missing", "Sin URL canónica",
            "Sin canonical, la misma página con distintos parámetros compite consigo misma.",
            "Agregá <link rel=\"canonical\" href=\"…\"> con la URL definitiva.")

    if not a.has_viewport:
        add("critical", "no_viewport", "No declara viewport móvil",
            "Sin viewport la página se renderiza como escritorio en el celular, donde está la mayoría del tráfico.",
            "Agregá <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">.")

    if not a.json_ld_types:
        add("warning", "no_schema", "Sin datos estructurados (JSON-LD)",
            "No hay schema.org: se pierden estrellas, precio y stock en el resultado de búsqueda.",
            "Agregá al menos Organization y, si vendés online, Product con precio y disponibilidad.")
    if a.json_ld_invalid:
        add("warning", "schema_invalid", f"{a.json_ld_invalid} bloque(s) JSON-LD con error",
            "El JSON no parsea, así que Google lo descarta entero.",
            "Validá el bloque en search.google.com/test/rich-results.")

    if a.images_without_alt:
        pct = round(a.images_without_alt / a.images_total * 100) if a.images_total else 0
        add("warning", "img_alt", f"{a.images_without_alt} imágenes sin alt",
            f"{pct}% de las imágenes no tienen texto alternativo: no rankean en Google Imágenes ni son accesibles.",
            "Escribí alt describiendo el producto (no \"foto1.jpg\").")

    if not a.open_graph.get("og:title") or not a.open_graph.get("og:image"):
        add("warning", "no_og", "Sin Open Graph completo",
            "Cuando compartís el link en WhatsApp o Instagram no se ve título ni imagen.",
            "Agregá og:title, og:description y og:image (1200×630).")

    if a.word_count < 300:
        add("warning", "thin_content", "Contenido escaso",
            f"Solo {a.word_count} palabras: a Google le sobra poco texto para entender el tema.",
            "Sumá descripción real del producto/servicio, preguntas frecuentes y casos de uso.")

    if not a.lang:
        add("info", "no_lang", "Sin atributo lang",
            "El <html> no declara idioma; afecta targeting por país e idioma.",
            "Poné <html lang=\"es-AR\"> (o el que corresponda).")

    issues.sort(key=lambda i: SEVERITY_ORDER.get(i["severity"], 9))
    return issues


def score_page(audit: PageAudit, response_ms: Optional[int] = None) -> float:
    """0-100 from the real findings. Deductions are fixed per issue severity, so
    the same page always scores the same — this is a checklist result, not a
    simulation of what a ranking tool would say."""
    score = 100.0
    for issue in audit.issues:
        score -= {"critical": 12.0, "warning": 5.0, "info": 2.0}.get(issue["severity"], 0.0)
    # Real measured latency, the one performance signal available without a
    # Lighthouse run. Slow servers genuinely hurt ranking.
    if response_ms is not None:
        if response_ms > 3000:
            score -= 10
        elif response_ms > 1500:
            score -= 5
    return round(max(0.0, min(100.0, score)), 1)
