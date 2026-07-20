"""Tests para KnowledgeEngine — descubrimiento dinámico de la biblioteca.

Antes CATEGORIES estaba hardcodeada (9 categorías) y los JSON nuevos de
finanzas/cripto/inmobiliario quedaban huérfanos: existían en library/ pero el
motor que alimenta a los agentes nunca los cargaba. Estos tests fijan que toda
categoría con archivo `*.json` se cargue y sea detectable para inyección.
"""

import pytest

from app.core.knowledge.knowledge_engine import KnowledgeEngine
from app.core.knowledge.llm_integration import KnowledgeContextProvider

_FINANCE = ("crypto", "investing", "real_estate", "business_models", "trading_analysis")


def test_discovers_finance_categories():
    eng = KnowledgeEngine()
    counts = eng.count()
    for cat in _FINANCE:
        assert counts.get(cat, 0) > 0, f"categoría {cat} no cargada"


def test_curated_order_preserved_first():
    eng = KnowledgeEngine()
    eng._load_all()
    # Las curadas van primero, en su orden.
    assert eng.categories[:3] == ["sales", "persuasion", "habits"]
    # Las extras quedan después de las curadas.
    assert set(_FINANCE).issubset(set(eng.categories))


def test_total_is_sum_of_categories():
    eng = KnowledgeEngine()
    counts = eng.count()
    total = counts.pop("total")
    assert total == sum(counts.values())


# ── anti-regresión: carga silenciosa de JSON ───────────────────────────────
# La carga está envuelta en try/except: un JSON roto carga 0 items y solo
# loguea un warning. Estos tests convierten esa pérdida silenciosa en fallo.
def test_every_discovered_category_has_items():
    eng = KnowledgeEngine()
    counts = eng.count()
    for cat in eng.categories:
        assert counts.get(cat, 0) > 0, f"categoría '{cat}' cargó 0 items (¿JSON roto?)"


def test_all_item_ids_unique():
    eng = KnowledgeEngine()
    eng._load_all()
    ids = [i.id for i in eng._items]
    dups = {i for i in ids if ids.count(i) > 1}
    assert not dups, f"IDs duplicados: {dups}"


def test_all_items_have_required_fields():
    eng = KnowledgeEngine()
    eng._load_all()
    for i in eng._items:
        assert i.principle, f"{i.id} sin principle"
        assert i.tactic, f"{i.id} sin tactic"
        assert isinstance(i.tags, list), f"{i.id} tags no es lista"
        assert isinstance(i._confidence_weight, (int, float)), f"{i.id} peso no numérico"


# ── validación de schema al cargar ──────────────────────────────────────────
def test_validate_item_accepts_well_formed():
    ok = {
        "id": "x_1", "principle": "p", "tactic": "t",
        "tags": ["a"], "_confidence_weight": 1.2,
    }
    assert KnowledgeEngine._validate_item(ok, "cat") is None


@pytest.mark.parametrize("bad", [
    {"principle": "p", "tactic": "t"},                       # sin id
    {"id": "", "principle": "p", "tactic": "t"},             # id vacío
    {"id": "x", "principle": "", "tactic": "t"},             # principle vacío
    {"id": "x", "principle": "p"},                           # sin tactic
    {"id": "x", "principle": "p", "tactic": "t", "tags": "a"},               # tags no lista
    {"id": "x", "principle": "p", "tactic": "t", "_confidence_weight": "1"},  # peso string
    {"id": "x", "principle": "p", "tactic": "t", "framework": 3},             # framework no string
])
def test_validate_item_rejects_malformed(bad):
    assert KnowledgeEngine._validate_item(bad, "cat") is not None


# Categorías de referentes/figuras que deben existir y estar pobladas.
_LEGENDS = (
    "sales_legends", "business_legends", "negotiation_legends", "statecraft_legends",
    "warren_buffett", "trump_dealmaking", "juan_pablo_ii", "belfort_method",
    "copywriting", "sales_frameworks",
)


def test_legend_categories_loaded():
    eng = KnowledgeEngine()
    counts = eng.count()
    for cat in _LEGENDS:
        assert counts.get(cat, 0) > 0, f"categoría de referentes '{cat}' no cargada"


def test_warren_buffett_has_depth():
    # Warren es el referente con más profundidad solicitada: exigir volumen.
    eng = KnowledgeEngine()
    items = eng.query(category="warren_buffett", top_k=50)
    assert len(items) >= 10
    assert all(i.category == "warren_buffett" for i in items)


def test_query_returns_crypto_items():
    eng = KnowledgeEngine()
    items = eng.query(category="crypto", top_k=10)
    assert items
    assert all(i.category == "crypto" for i in items)


def test_detect_finance_categories():
    p = KnowledgeContextProvider()
    assert "crypto" in p._detect_categories("quiero invertir en bitcoin")
    assert "real_estate" in p._detect_categories("comprar una propiedad en alquiler")
    assert "trading_analysis" in p._detect_categories("dónde pongo el stop loss en este trade")


def test_build_context_injects_finance_knowledge():
    p = KnowledgeContextProvider()
    ctx = p.build_context("me conviene comprar ethereum ahora?")
    assert ctx
    assert "Principio" in ctx
    # No filtra fuentes internas al prompt.
    assert "_source_hint" not in ctx


# ── búsqueda semántica (embeddings) ───────────────────────────────────────
_KW = ["cripto", "bitcoin", "chain", "stop", "inmueble", "alquiler", "venta", "objecion"]


def _fake_vec(text: str):
    t = text.lower()
    return [1.0 if kw in t else 0.0 for kw in _KW]


@pytest.mark.asyncio
async def test_semantic_query_ranks_by_embedding(monkeypatch):
    import app.core.embeddings as emb

    async def fake_embed_text(text):
        return _fake_vec(text)

    async def fake_embed_batch(texts):
        return [_fake_vec(t) for t in texts]

    monkeypatch.setattr(emb.embedding_service, "embed_text", fake_embed_text)
    monkeypatch.setattr(emb.embedding_service, "embed_batch", fake_embed_batch)

    eng = KnowledgeEngine()
    items = await eng.semantic_query("bitcoin cripto on-chain", top_k=3)
    assert items
    assert any(i.category == "crypto" for i in items)


@pytest.mark.asyncio
async def test_semantic_query_falls_back_on_error(monkeypatch):
    import app.core.embeddings as emb

    async def boom(*a, **k):
        raise RuntimeError("embeddings down")

    monkeypatch.setattr(emb.embedding_service, "embed_text", boom)
    monkeypatch.setattr(emb.embedding_service, "embed_batch", boom)

    eng = KnowledgeEngine()
    # No revienta: cae a keyword search y devuelve resultados.
    items = await eng.semantic_query("cómo cierro una venta con objeciones", top_k=3)
    assert items


# ── routing por afinidad (nº de keywords, no orden de inserción) ────────────
def test_detect_prioritizes_specific_over_generic():
    p = KnowledgeContextProvider()
    # Mensaje con keywords de belfort + genéricas de sales: belfort no debe
    # quedar fuera del top por estar listado después en el keyword_map.
    cats = p._detect_categories("quiero mejorar mi tonalidad y la transferencia de certeza en la línea recta para cerrar la venta")
    assert "belfort_method" in cats


def test_detect_warren_specific():
    p = KnowledgeContextProvider()
    cats = p._detect_categories("cómo aplica buffett el margen de seguridad y el círculo de competencia al invertir")
    assert "warren_buffett" in cats


# ── gaps temáticos: pricing / customer_success / branding / funnels / saas ──
def test_detect_thematic_gap_categories():
    p = KnowledgeContextProvider()
    assert "pricing" in p._detect_categories("cuánto cobrar, cómo fijar precio y armar planes con anclaje")
    assert "customer_success" in p._detect_categories("bajar el churn y mejorar la retención con buen onboarding")
    assert "branding" in p._detect_categories("posicionamiento de marca y diferenciación al estilo ries y trout")
    assert "marketing_funnels" in p._detect_categories("optimizar el embudo de conversión y el lead magnet de la landing")
    assert "saas_metrics" in p._detect_categories("mi relación ltv cac y el mrr con net revenue retention")


def test_query_returns_pricing_items():
    eng = KnowledgeEngine()
    items = eng.query(category="pricing", top_k=10)
    assert items
    assert all(i.category == "pricing" for i in items)


# ── Meta Ads ────────────────────────────────────────────────────────────────
def test_detect_meta_ads_category():
    p = KnowledgeContextProvider()
    assert "meta_ads" in p._detect_categories("cómo armo una campaña de facebook ads con remarketing y el píxel")
    assert "meta_ads" in p._detect_categories("mi creativo de instagram ads no frena el scroll y el cpm está alto")


def test_meta_ads_has_depth():
    eng = KnowledgeEngine()
    items = eng.query(category="meta_ads", top_k=50)
    assert len(items) >= 15
    assert all(i.category == "meta_ads" for i in items)


# ── build_context_async / inject_knowledge_async (semántico) ────────────────
@pytest.mark.asyncio
async def test_build_context_async_uses_semantic(monkeypatch):
    import app.core.embeddings as emb

    async def fake_embed_text(text):
        return _fake_vec(text)

    async def fake_embed_batch(texts):
        return [_fake_vec(t) for t in texts]

    monkeypatch.setattr(emb.embedding_service, "embed_text", fake_embed_text)
    monkeypatch.setattr(emb.embedding_service, "embed_batch", fake_embed_batch)

    p = KnowledgeContextProvider()
    ctx = await p.build_context_async("cómo cierro una venta con objeciones")
    assert ctx
    assert "Principio" in ctx
    assert "_source_hint" not in ctx


@pytest.mark.asyncio
async def test_inject_knowledge_async_falls_back(monkeypatch):
    import app.core.embeddings as emb
    from app.core.knowledge.llm_integration import inject_knowledge_async

    async def boom(*a, **k):
        raise RuntimeError("embeddings down")

    monkeypatch.setattr(emb.embedding_service, "embed_text", boom)
    monkeypatch.setattr(emb.embedding_service, "embed_batch", boom)

    # Aun con embeddings caídos, no revienta y devuelve el prompt base enriquecido.
    out = await inject_knowledge_async("cierro una venta con objeciones de precio", "PROMPT_BASE")
    assert "PROMPT_BASE" in out
