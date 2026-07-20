"""Computer Use — AI Suggestions

Sugiere acciones basadas en el historial de sesiones exitosas similares.
Usa embeddings y similitud de coseno para encontrar patrones.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Suggestion:
    action_type: str
    params: Dict[str, Any]
    confidence: float
    reason: str
    based_on_sessions: int


class AISuggestions:
    """Motor de sugerencias basado en historial."""

    def __init__(self):
        self._action_patterns: Dict[str, List[Dict]] = {}
        self._embedding_cache: Dict[str, List[float]] = {}

    def _simple_embed(self, text: str) -> List[float]:
        """Embedding simple basado en frecuencia de palabras (fallback sin OpenAI)."""
        words = text.lower().split()
        # Simple bag-of-words hash
        vec = [0.0] * 64
        for word in words:
            h = hash(word) % 64
            vec[h] += 1.0
        # Normalize
        norm = sum(x ** 2 for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Similitud de coseno entre dos vectores."""
        dot = sum(x * y for x, y in zip(a, b))
        return dot  # Already normalized

    def index_session(self, task: str, actions: List[Dict[str, Any]], success: bool) -> None:
        """Indexa una sesión completada para futuras sugerencias."""
        if not success:
            return

        task_embed = self._simple_embed(task)
        key = task.lower().strip()[:100]
        self._embedding_cache[key] = task_embed
        self._action_patterns[key] = actions

    def suggest(
        self,
        task: str,
        current_step: int,
        current_url: str,
        history: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> List[Suggestion]:
        """Sugiere acciones basadas en sesiones similares previas."""
        if not self._embedding_cache:
            return []

        task_embed = self._simple_embed(task)

        # Find similar tasks
        similarities = []
        for key, embed in self._embedding_cache.items():
            sim = self._cosine_similarity(task_embed, embed)
            if sim > 0.3:  # Minimum similarity threshold
                similarities.append((key, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        suggestions = []
        seen_actions = set()

        for key, sim in similarities[:top_k]:
            actions = self._action_patterns.get(key, [])
            if current_step < len(actions):
                next_action = actions[current_step]
                action_key = f"{next_action.get('action_type')}:{json.dumps(next_action.get('params', {}), sort_keys=True)}"
                if action_key not in seen_actions:
                    seen_actions.add(action_key)
                    suggestions.append(Suggestion(
                        action_type=next_action.get("action_type", "unknown"),
                        params=next_action.get("params", {}),
                        confidence=round(sim, 2),
                        reason=f"Basado en {len([k for k, s in similarities if s > 0.3])} sesiones similares",
                        based_on_sessions=len([k for k, s in similarities if s > 0.3]),
                    ))

        return suggestions

    def suggest_recovery(
        self,
        task: str,
        error_message: str,
        history: List[Dict[str, Any]],
    ) -> Optional[Suggestion]:
        """Sugiere una acción de recuperación tras un error."""
        common_recoveries = {
            "timeout": {"action_type": "wait", "params": {"seconds": 3}, "reason": "La página puede estar lenta, esperar un poco más"},
            "navigation": {"action_type": "navigate", "params": {"url": ""}, "reason": "Reintentar navegación"},
            "element": {"action_type": "screenshot", "params": {}, "reason": "Tomar screenshot para reevaluar el estado"},
        }

        error_lower = error_message.lower()
        for pattern, recovery in common_recoveries.items():
            if pattern in error_lower:
                return Suggestion(
                    action_type=recovery["action_type"],
                    params=recovery["params"],
                    confidence=0.7,
                    reason=recovery["reason"],
                    based_on_sessions=1,
                )

        # Default: screenshot and wait
        return Suggestion(
            action_type="screenshot",
            params={},
            confidence=0.5,
            reason="Error desconocido, tomar screenshot para reevaluar",
            based_on_sessions=1,
        )
