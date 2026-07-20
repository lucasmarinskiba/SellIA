"""Pilar 1 — Auto-Configuración (Self-Configuration)

El sistema se ajusta por sí solo dependiendo de los cambios en el entorno,
la carga de trabajo, los proveedores disponibles y las preferencias del negocio.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.logger import get_logger

logger = get_logger(__name__)

# Configuración de umbrales del sistema
CONFIG_THRESHOLDS = {
    "high_load_conversations": 50,      # conversaciones activas simultáneas
    "high_load_tasks_queued": 100,      # tareas en cola Celery
    "api_rate_limit_warning": 0.8,      # % de límite de API utilizado
    "db_connection_warning": 0.85,      # % de pool de conexiones usado
    "response_time_warning_ms": 3000,   # ms de tiempo de respuesta aceptable
    "low_balance_threshold": 5.0,       # USD de crédito mínimo en proveedor AI
}

# Configuraciones adaptativas por escenario
ADAPTIVE_CONFIGS = {
    "high_load": {
        "llm_temperature": 0.2,         # más determinista bajo carga
        "llm_max_tokens": 500,          # respuestas más cortas
        "cache_ttl_seconds": 300,       # cache más agresivo
        "batch_size": 5,                # lotes más pequeños
        "preferred_model": "gpt-4o-mini",
    },
    "normal_load": {
        "llm_temperature": 0.5,
        "llm_max_tokens": 1500,
        "cache_ttl_seconds": 60,
        "batch_size": 20,
        "preferred_model": "gpt-4o",
    },
    "low_load": {
        "llm_temperature": 0.7,
        "llm_max_tokens": 2000,
        "cache_ttl_seconds": 30,
        "batch_size": 50,
        "preferred_model": "gpt-4o",
    },
}


class SelfConfigEngine:
    """Motor de auto-configuración del sistema SellIA."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._current_config: dict[str, Any] = ADAPTIVE_CONFIGS["normal_load"].copy()
        self._config_history: list[dict] = []

    async def run_config_cycle(self, business_id: Optional[uuid.UUID] = None) -> dict[str, Any]:
        """Ejecuta un ciclo completo de auto-configuración."""
        logger.info("[SelfConfig] Iniciando ciclo de auto-configuración")

        metrics = await self._collect_system_metrics(business_id)
        load_state = self._classify_load_state(metrics)
        config_applied = self._apply_adaptive_config(load_state, metrics)
        api_config = await self._configure_ai_providers()
        channel_config = await self._configure_channel_limits(business_id)

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "load_state": load_state,
            "metrics": metrics,
            "config_applied": config_applied,
            "api_providers": api_config,
            "channel_config": channel_config,
        }

        self._config_history.append(result)
        if len(self._config_history) > 100:
            self._config_history = self._config_history[-50:]

        logger.info(f"[SelfConfig] Ciclo completado. Estado: {load_state}")
        return result

    async def _collect_system_metrics(self, business_id: Optional[uuid.UUID]) -> dict[str, Any]:
        """Recolecta métricas actuales del sistema."""
        metrics: dict[str, Any] = {
            "active_conversations": 0,
            "pending_deals": 0,
            "tasks_queued": 0,
            "avg_response_time_ms": 0,
            "db_connections_used": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            from app.domains.channels.models import Conversation
            conv_query = select(func.count(Conversation.id)).where(
                Conversation.is_active == True
            )
            if business_id:
                conv_query = conv_query.where(Conversation.business_id == business_id)
            result = await self.db.execute(conv_query)
            metrics["active_conversations"] = result.scalar() or 0
        except Exception as e:
            logger.warning(f"[SelfConfig] No se pudo obtener conversaciones activas: {e}")

        try:
            from app.domains.crm.models import Deal
            deals_query = select(func.count(Deal.id)).where(
                Deal.is_active == True
            )
            if business_id:
                deals_query = deals_query.where(Deal.business_id == business_id)
            result = await self.db.execute(deals_query)
            metrics["pending_deals"] = result.scalar() or 0
        except Exception as e:
            logger.warning(f"[SelfConfig] No se pudo obtener deals pendientes: {e}")

        try:
            import redis.asyncio as aioredis
            from app.core.config import get_settings
            settings = get_settings()
            r = aioredis.from_url(settings.REDIS_URL)
            queue_lengths = await asyncio.gather(
                r.llen("celery"),
                r.llen("celery.priority"),
                return_exceptions=True,
            )
            await r.aclose()
            total = sum(q for q in queue_lengths if isinstance(q, int))
            metrics["tasks_queued"] = total
        except Exception as e:
            logger.warning(f"[SelfConfig] No se pudo obtener cola Redis: {e}")

        return metrics

    def _classify_load_state(self, metrics: dict[str, Any]) -> str:
        """Clasifica el estado de carga del sistema."""
        conversations = metrics.get("active_conversations", 0)
        tasks = metrics.get("tasks_queued", 0)

        if (conversations >= CONFIG_THRESHOLDS["high_load_conversations"] or
                tasks >= CONFIG_THRESHOLDS["high_load_tasks_queued"]):
            return "high_load"
        elif conversations < 10 and tasks < 10:
            return "low_load"
        else:
            return "normal_load"

    def _apply_adaptive_config(self, load_state: str, metrics: dict) -> dict[str, Any]:
        """Aplica la configuración adaptativa según el estado de carga."""
        new_config = ADAPTIVE_CONFIGS.get(load_state, ADAPTIVE_CONFIGS["normal_load"]).copy()

        if load_state != self._current_config.get("_load_state"):
            prev_state = self._current_config.get("_load_state", "unknown")
            logger.info(f"[SelfConfig] Cambiando configuración: {prev_state} → {load_state}")
            self._current_config = {**new_config, "_load_state": load_state}

        return new_config

    async def _configure_ai_providers(self) -> dict[str, Any]:
        """Configura y verifica disponibilidad de proveedores AI."""
        provider_status: dict[str, Any] = {}

        # Verificar OpenAI
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            provider_status["openai"] = {
                "available": True,
                "key_configured": True,
                "preferred_model": self._current_config.get("preferred_model", "gpt-4o-mini"),
            }
        else:
            provider_status["openai"] = {"available": False, "key_configured": False}

        # Verificar Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            provider_status["anthropic"] = {
                "available": True,
                "key_configured": True,
                "preferred_model": "claude-sonnet-4-6",
            }
        else:
            provider_status["anthropic"] = {"available": False, "key_configured": False}

        # Verificar Ollama (local)
        ollama_url = os.getenv("OLLAMA_BASE_URL", "")
        provider_status["ollama"] = {
            "available": bool(ollama_url),
            "url_configured": bool(ollama_url),
        }

        # Determinar proveedor principal
        if provider_status.get("openai", {}).get("available"):
            provider_status["active_provider"] = "openai"
        elif provider_status.get("anthropic", {}).get("available"):
            provider_status["active_provider"] = "anthropic"
        elif provider_status.get("ollama", {}).get("available"):
            provider_status["active_provider"] = "ollama"
        else:
            provider_status["active_provider"] = "none"
            logger.warning("[SelfConfig] ¡Sin proveedor AI disponible! Verificar API keys.")

        return provider_status

    async def _configure_channel_limits(self, business_id: Optional[uuid.UUID]) -> dict[str, Any]:
        """Ajusta límites de mensajería por canal según carga."""
        channel_config: dict[str, Any] = {
            "whatsapp": {"rate_limit_per_minute": 20, "batch_delay_ms": 500},
            "email": {"rate_limit_per_minute": 60, "batch_delay_ms": 100},
            "instagram": {"rate_limit_per_minute": 10, "batch_delay_ms": 1000},
            "telegram": {"rate_limit_per_minute": 30, "batch_delay_ms": 200},
        }

        load_state = self._current_config.get("_load_state", "normal_load")
        if load_state == "high_load":
            for ch in channel_config:
                channel_config[ch]["rate_limit_per_minute"] = int(
                    channel_config[ch]["rate_limit_per_minute"] * 0.7
                )
                logger.info(f"[SelfConfig] Canal {ch} throttled por alta carga")

        return channel_config

    def get_current_llm_config(self) -> dict[str, Any]:
        """Retorna configuración LLM actual para que otros módulos la usen."""
        return {
            "temperature": self._current_config.get("llm_temperature", 0.5),
            "max_tokens": self._current_config.get("llm_max_tokens", 1500),
            "model": self._current_config.get("preferred_model", "gpt-4o-mini"),
        }

    def get_current_load_state(self) -> str:
        return self._current_config.get("_load_state", "normal_load")


import asyncio
