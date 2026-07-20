"""Knowledge Engine — Motor de consulta de la biblioteca interna

Selecciona principios, tácticas y frameworks relevantes según el
contexto de la conversación, sin revelar nunca al usuario la fuente
de los conocimientos aplicados.
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from functools import lru_cache

from app.core.logger import get_logger

logger = get_logger(__name__)


def _emit_activity(category: Optional[str], mode: str) -> None:
    """Emite un evento real al bus de actividad del cerebro (best-effort)."""
    if not category:
        return
    try:
        from app.core.brain.activity import record_activity
        record_activity(
            "knowledge",
            source=f"skill.knowledge.{category}",
            detail=f"Consulta de conocimiento ({mode}) · categoría {category}",
        )
    except Exception:  # pragma: no cover - nunca romper el camino caliente
        pass


@dataclass
class KnowledgeItem:
    """Un item de conocimiento de la biblioteca."""
    id: str
    category: str
    subcategory: str
    principle: str
    tactic: str
    framework: Optional[str]
    script_template: Optional[str]
    when_to_use: List[str]
    when_not_to_use: List[str]
    tags: List[str]
    # Atributos internos (nunca revelados al usuario)
    _source_hint: Optional[str] = None
    _confidence_weight: float = 1.0


class KnowledgeEngine:
    """Motor de consulta y selección de conocimiento."""

    # Orden curado de las categorías base; cualquier otro `*.json` que aparezca
    # en library/ se descubre y carga automáticamente (ver _discover_categories).
    CURATED_ORDER = [
        "sales", "persuasion", "habits", "negotiation",
        "entrepreneurship", "wealth", "communication", "psychology", "strategy"
    ]

    def __init__(self):
        self._items: List[KnowledgeItem] = []
        self._index: Dict[str, List[KnowledgeItem]] = {}
        self._loaded = False
        # Categorías efectivamente cargadas (se completa en _load_all).
        self.categories: List[str] = []
        # Cache de embeddings por id de item (búsqueda semántica).
        self._vectors: Dict[str, List[float]] = {}

    def _discover_categories(self, base_path: str) -> List[str]:
        """Descubre categorías por los `*.json` presentes en library/.

        Respeta el orden curado y añade el resto alfabéticamente, así los
        archivos de conocimiento nuevos quedan disponibles sin tocar código.
        """
        try:
            found = {
                f[:-5] for f in os.listdir(base_path)
                if f.endswith(".json") and not f.startswith("_")
            }
        except OSError as e:
            logger.warning(f"Cannot list knowledge library dir: {e}")
            return list(self.CURATED_ORDER)

        ordered = [c for c in self.CURATED_ORDER if c in found]
        extras = sorted(found - set(self.CURATED_ORDER))
        return ordered + extras

    @staticmethod
    def _validate_item(item_data: Dict[str, Any], category: str) -> Optional[str]:
        """Valida el schema de un item. Retorna mensaje de error o None si OK.

        Antes la carga era permisiva: un `_confidence_weight` string o un `tags`
        no-lista pasaban sin chequeo y reventaban más tarde en query/scoring.
        Esta validación convierte el dato malformado en skip+warning explícito.
        """
        iid = item_data.get("id")
        if not isinstance(iid, str) or not iid.strip():
            return "id ausente o no-string"
        for field in ("principle", "tactic"):
            val = item_data.get(field, "")
            if not isinstance(val, str) or not val.strip():
                return f"{field} vacío o no-string"
        for field in ("when_to_use", "when_not_to_use", "tags"):
            if field in item_data and not isinstance(item_data[field], list):
                return f"{field} no es lista"
        if "_confidence_weight" in item_data and not isinstance(
            item_data["_confidence_weight"], (int, float)
        ):
            return "_confidence_weight no numérico"
        for field in ("subcategory", "framework", "script_template", "_source_hint"):
            if field in item_data and item_data[field] is not None and not isinstance(
                item_data[field], str
            ):
                return f"{field} no es string"
        return None

    def _load_all(self) -> None:
        """Carga todo el conocimiento de la biblioteca."""
        if self._loaded:
            return

        base_path = os.path.join(os.path.dirname(__file__), "library")
        self.categories = self._discover_categories(base_path)

        for category in self.categories:
            file_path = os.path.join(base_path, f"{category}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for item_data in data.get("items", []):
                        err = self._validate_item(item_data, category)
                        if err:
                            logger.warning(
                                f"Skipping malformed item in {category} "
                                f"({item_data.get('id', '?')}): {err}"
                            )
                            continue
                        item = KnowledgeItem(
                            id=item_data["id"],
                            category=category,
                            subcategory=item_data.get("subcategory", ""),
                            principle=item_data.get("principle", ""),
                            tactic=item_data.get("tactic", ""),
                            framework=item_data.get("framework"),
                            script_template=item_data.get("script_template"),
                            when_to_use=item_data.get("when_to_use", []),
                            when_not_to_use=item_data.get("when_not_to_use", []),
                            tags=item_data.get("tags", []),
                            _source_hint=item_data.get("_source_hint"),
                            _confidence_weight=item_data.get("_confidence_weight", 1.0),
                        )
                        self._items.append(item)
                        # Index by tags
                        for tag in item.tags:
                            self._index.setdefault(tag.lower(), []).append(item)
                        # Index by subcategory
                        self._index.setdefault(item.subcategory.lower(), []).append(item)
                except Exception as e:
                    logger.warning(f"Failed to load knowledge {category}: {e}")

        self._loaded = True
        logger.info(f"KnowledgeEngine loaded: {len(self._items)} items across {len(self.categories)} categories")

    def query(
        self,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        tags: Optional[List[str]] = None,
        context: Optional[str] = None,
        top_k: int = 5,
    ) -> List[KnowledgeItem]:
        """Consulta la biblioteca y retorna los items más relevantes.

        Args:
            category: Categoría principal (sales, persuasion, etc.)
            subcategory: Subcategoría específica
            tags: Lista de tags para filtrar
            context: Texto del contexto actual (para scoring)
            top_k: Cuántos items retornar
        """
        self._load_all()

        candidates = self._items

        # Filter by category
        if category:
            candidates = [c for c in candidates if c.category == category.lower()]
            _emit_activity(category.lower(), "keyword")

        # Filter by subcategory
        if subcategory:
            candidates = [c for c in candidates if c.subcategory.lower() == subcategory.lower()]

        # Filter by tags
        if tags:
            tag_set = set(t.lower() for t in tags)
            candidates = [c for c in candidates if tag_set & set(t.lower() for t in c.tags)]

        # Score by context relevance (simple keyword matching)
        if context:
            context_lower = context.lower()
            scored = []
            for c in candidates:
                score = 0
                text = f"{c.principle} {c.tactic} {' '.join(c.tags)}"
                # Keyword overlap
                for word in context_lower.split():
                    if len(word) > 3 and word in text.lower():
                        score += 1
                # Weighted by confidence
                score *= c._confidence_weight
                scored.append((score, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            candidates = [c for _, c in scored]

        return candidates[:top_k]

    @staticmethod
    def _item_text(item: KnowledgeItem) -> str:
        """Texto representativo de un item para embeber."""
        return " ".join(filter(None, [item.principle, item.tactic, " ".join(item.tags)]))

    async def semantic_query(
        self,
        context: str,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> List[KnowledgeItem]:
        """Búsqueda semántica por embeddings (cosine similarity).

        Más precisa que `query()` (que es overlap de keywords). Si el servicio
        de embeddings o numpy fallan, cae a `query()` para no romper el flujo
        del agente.
        """
        self._load_all()

        candidates = self._items
        if category:
            candidates = [c for c in candidates if c.category == category.lower()]
            _emit_activity(category.lower(), "semantic")
        if not candidates or not context:
            return self.query(category=category, context=context, top_k=top_k)

        try:
            import numpy as np
            from app.core.embeddings import embedding_service

            # Embeber los items que aún no tengan vector (batch).
            missing = [c for c in candidates if c.id not in self._vectors]
            if missing:
                vecs = await embedding_service.embed_batch([self._item_text(c) for c in missing])
                for c, v in zip(missing, vecs):
                    self._vectors[c.id] = v

            q = np.asarray(await embedding_service.embed_text(context), dtype="float32")
            q_norm = float(np.linalg.norm(q)) or 1.0

            scored: List[tuple[float, KnowledgeItem]] = []
            for c in candidates:
                vec = self._vectors.get(c.id)
                if vec is None:
                    continue
                m = np.asarray(vec, dtype="float32")
                denom = (float(np.linalg.norm(m)) or 1.0) * q_norm
                sim = float(np.dot(q, m) / denom)
                scored.append((sim * c._confidence_weight, c))

            if not scored:
                return self.query(category=category, context=context, top_k=top_k)

            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for _, c in scored[:top_k]]
        except Exception as e:
            logger.warning(f"semantic_query fell back to keyword search: {e}")
            return self.query(category=category, context=context, top_k=top_k)

    def get_by_id(self, item_id: str) -> Optional[KnowledgeItem]:
        """Obtiene un item por su ID."""
        self._load_all()
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def get_random_insight(self, category: Optional[str] = None) -> Optional[KnowledgeItem]:
        """Obtiene un insight aleatorio (para variar respuestas)."""
        import random
        self._load_all()
        pool = self._items
        if category:
            pool = [c for c in pool if c.category == category.lower()]
        if not pool:
            return None
        return random.choice(pool)

    def get_framework(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtiene un framework completo por nombre."""
        self._load_all()
        for item in self._items:
            if item.framework and name.lower() in item.framework.lower():
                return {
                    "name": item.framework,
                    "principle": item.principle,
                    "tactic": item.tactic,
                    "script": item.script_template,
                }
        return None

    def get_script(self, situation: str) -> Optional[str]:
        """Obtiene un script template para una situación específica."""
        items = self.query(context=situation, top_k=1)
        if items and items[0].script_template:
            return items[0].script_template
        return None

    def count(self) -> Dict[str, int]:
        """Estadísticas de la biblioteca."""
        self._load_all()
        stats = {}
        for cat in self.categories:
            stats[cat] = len([i for i in self._items if i.category == cat])
        stats["total"] = len(self._items)
        return stats


# Singleton instance
_knowledge_engine: Optional[KnowledgeEngine] = None


def get_knowledge_engine() -> KnowledgeEngine:
    global _knowledge_engine
    if _knowledge_engine is None:
        _knowledge_engine = KnowledgeEngine()
    return _knowledge_engine
