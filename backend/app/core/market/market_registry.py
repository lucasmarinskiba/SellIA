"""Market Registry - Central registry de tipos de mercado, agentes y reglas.

Mantiene registros de:
- Todos los tipos de mercado soportados
- Agentes cargados disponibles
- Rule sets disponibles
- Health checks por mercado
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# ENUMS & DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────


class HealthStatus(str, Enum):
    """Status de salud de componente."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class MarketRegistryEntry:
    """Entrada en registry de mercado."""
    market_name: str
    industry: str
    supported: bool
    enabled: bool
    loaded_agents: List[str]
    available_rules: List[str]
    health_status: HealthStatus
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRegistryEntry:
    """Entrada en registry de agentes."""
    agent_name: str
    agent_role: str
    version: str
    market_applicable: List[str]  # Mercados donde aplica
    capabilities: List[str]
    status: str  # "loaded", "unloaded", "error"
    last_loaded: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleSetRegistryEntry:
    """Entrada en registry de rule sets."""
    rule_set_name: str
    industry: str
    version: str
    market_applicable: List[str]
    status: str  # "loaded", "unloaded", "error"
    last_updated: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────
# MARKET REGISTRY
# ─────────────────────────────────────────────────────────────────────────


class MarketRegistry:
    """Registry central de mercados, agentes y reglas."""

    def __init__(self):
        """Inicializa registry."""
        self.markets: Dict[str, MarketRegistryEntry] = {}
        self.agents: Dict[str, AgentRegistryEntry] = {}
        self.rule_sets: Dict[str, RuleSetRegistryEntry] = {}
        self.last_sync: Optional[str] = None

    def register_market(
        self,
        market_name: str,
        industry: str,
        supported: bool = True,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registra tipo de mercado.

        Args:
            market_name: Nombre del mercado
            industry: Industria correspondiente
            supported: Si está soportado
            enabled: Si está habilitado
            metadata: Metadata adicional
        """
        entry = MarketRegistryEntry(
            market_name=market_name,
            industry=industry,
            supported=supported,
            enabled=enabled,
            loaded_agents=[],
            available_rules=[],
            health_status=HealthStatus.HEALTHY if supported else HealthStatus.UNHEALTHY,
            metadata=metadata or {},
        )

        self.markets[market_name] = entry
        logger.info(f"Registered market: {market_name} ({industry})")

    def register_agent(
        self,
        agent_name: str,
        agent_role: str,
        version: str,
        market_applicable: List[str],
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registra agente.

        Args:
            agent_name: Nombre único del agente
            agent_role: Rol/especialidad
            version: Versión semver
            market_applicable: Mercados donde aplica
            capabilities: Capacidades del agente
            metadata: Metadata adicional
        """
        entry = AgentRegistryEntry(
            agent_name=agent_name,
            agent_role=agent_role,
            version=version,
            market_applicable=market_applicable,
            capabilities=capabilities,
            status="unloaded",
            metadata=metadata or {},
        )

        self.agents[agent_name] = entry

        # Actualiza markets con este agente
        for market in market_applicable:
            if market in self.markets:
                if agent_name not in self.markets[market].loaded_agents:
                    self.markets[market].loaded_agents.append(agent_name)

        logger.info(f"Registered agent: {agent_name} (v{version})")

    def register_rule_set(
        self,
        rule_set_name: str,
        industry: str,
        version: str,
        market_applicable: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registra rule set.

        Args:
            rule_set_name: Nombre del rule set
            industry: Industria correspondiente
            version: Versión
            market_applicable: Mercados donde aplica
            metadata: Metadata adicional
        """
        entry = RuleSetRegistryEntry(
            rule_set_name=rule_set_name,
            industry=industry,
            version=version,
            market_applicable=market_applicable,
            status="unloaded",
            metadata=metadata or {},
        )

        self.rule_sets[rule_set_name] = entry

        # Actualiza markets con este rule set
        for market in market_applicable:
            if market in self.markets:
                if rule_set_name not in self.markets[market].available_rules:
                    self.markets[market].available_rules.append(rule_set_name)

        logger.info(f"Registered rule set: {rule_set_name} (v{version})")

    def get_market(self, market_name: str) -> Optional[MarketRegistryEntry]:
        """Obtiene entrada de mercado."""
        return self.markets.get(market_name)

    def get_agent(self, agent_name: str) -> Optional[AgentRegistryEntry]:
        """Obtiene entrada de agente."""
        return self.agents.get(agent_name)

    def get_rule_set(self, rule_set_name: str) -> Optional[RuleSetRegistryEntry]:
        """Obtiene entrada de rule set."""
        return self.rule_sets.get(rule_set_name)

    def get_agents_for_market(self, market_name: str) -> List[AgentRegistryEntry]:
        """Obtiene agentes disponibles para mercado.

        Args:
            market_name: Nombre del mercado

        Returns:
            Lista de agentes aplicables
        """
        market = self.get_market(market_name)
        if not market:
            return []

        return [
            self.agents[agent_name]
            for agent_name in market.loaded_agents
            if agent_name in self.agents
        ]

    def get_rule_sets_for_market(self, market_name: str) -> List[RuleSetRegistryEntry]:
        """Obtiene rule sets disponibles para mercado.

        Args:
            market_name: Nombre del mercado

        Returns:
            Lista de rule sets aplicables
        """
        market = self.get_market(market_name)
        if not market:
            return []

        return [
            self.rule_sets[rule_name]
            for rule_name in market.available_rules
            if rule_name in self.rule_sets
        ]

    def get_agents_by_capability(self, capability: str) -> List[AgentRegistryEntry]:
        """Obtiene agentes con capacidad específica.

        Args:
            capability: Nombre de capacidad

        Returns:
            Agentes con esa capacidad
        """
        return [
            agent for agent in self.agents.values()
            if capability in agent.capabilities
        ]

    def mark_agent_loaded(self, agent_name: str, last_loaded: Optional[str] = None) -> None:
        """Marca agente como cargado.

        Args:
            agent_name: Nombre del agente
            last_loaded: Timestamp de carga
        """
        if agent_name in self.agents:
            self.agents[agent_name].status = "loaded"
            self.agents[agent_name].last_loaded = (
                last_loaded or datetime.utcnow().isoformat()
            )

    def mark_agent_error(self, agent_name: str, error_msg: str) -> None:
        """Marca agente con error.

        Args:
            agent_name: Nombre del agente
            error_msg: Mensaje de error
        """
        if agent_name in self.agents:
            self.agents[agent_name].status = "error"
            self.agents[agent_name].metadata["error"] = error_msg

    def mark_rule_set_loaded(self, rule_set_name: str) -> None:
        """Marca rule set como cargado."""
        if rule_set_name in self.rule_sets:
            self.rule_sets[rule_set_name].status = "loaded"
            self.rule_sets[rule_set_name].last_updated = datetime.utcnow().isoformat()

    def check_market_health(self, market_name: str) -> HealthStatus:
        """Verifica salud de mercado.

        Args:
            market_name: Nombre del mercado

        Returns:
            HealthStatus del mercado
        """
        market = self.get_market(market_name)
        if not market:
            return HealthStatus.UNHEALTHY

        # Verifica que tenga agentes cargados
        agents = self.get_agents_for_market(market_name)
        loaded_agents = [a for a in agents if a.status == "loaded"]

        if not loaded_agents:
            return HealthStatus.UNHEALTHY

        # Verifica que tenga rule sets
        rule_sets = self.get_rule_sets_for_market(market_name)
        if not rule_sets:
            return HealthStatus.DEGRADED

        # Checkea si hay errores
        errors = [a for a in agents if a.status == "error"]
        if errors:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def update_market_health(self, market_name: str) -> None:
        """Actualiza status de salud de mercado.

        Args:
            market_name: Nombre del mercado
        """
        if market_name in self.markets:
            status = self.check_market_health(market_name)
            self.markets[market_name].health_status = status

    def get_all_markets(self) -> List[MarketRegistryEntry]:
        """Obtiene todos los mercados."""
        return list(self.markets.values())

    def get_all_agents(self) -> List[AgentRegistryEntry]:
        """Obtiene todos los agentes."""
        return list(self.agents.values())

    def get_all_rule_sets(self) -> List[RuleSetRegistryEntry]:
        """Obtiene todos los rule sets."""
        return list(self.rule_sets.values())

    def get_registry_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del registry.

        Returns:
            Resumen con conteos y status
        """
        markets_healthy = sum(
            1 for m in self.markets.values()
            if m.health_status == HealthStatus.HEALTHY
        )
        agents_loaded = sum(
            1 for a in self.agents.values() if a.status == "loaded"
        )
        agents_error = sum(
            1 for a in self.agents.values() if a.status == "error"
        )

        return {
            "markets": {
                "total": len(self.markets),
                "healthy": markets_healthy,
            },
            "agents": {
                "total": len(self.agents),
                "loaded": agents_loaded,
                "errors": agents_error,
            },
            "rule_sets": {
                "total": len(self.rule_sets),
                "loaded": sum(
                    1 for rs in self.rule_sets.values()
                    if rs.status == "loaded"
                ),
            },
            "last_sync": self.last_sync,
        }

    def export_registry(self) -> Dict[str, Any]:
        """Exporta registry completo.

        Returns:
            Snapshot del registry
        """
        return {
            "markets": {
                name: {
                    "industry": entry.industry,
                    "supported": entry.supported,
                    "enabled": entry.enabled,
                    "health_status": entry.health_status.value,
                    "loaded_agents": entry.loaded_agents,
                    "available_rules": entry.available_rules,
                }
                for name, entry in self.markets.items()
            },
            "agents": {
                name: {
                    "role": entry.agent_role,
                    "version": entry.version,
                    "status": entry.status,
                    "market_applicable": entry.market_applicable,
                    "capabilities": entry.capabilities,
                }
                for name, entry in self.agents.items()
            },
            "rule_sets": {
                name: {
                    "industry": entry.industry,
                    "version": entry.version,
                    "status": entry.status,
                    "market_applicable": entry.market_applicable,
                }
                for name, entry in self.rule_sets.items()
            },
        }
