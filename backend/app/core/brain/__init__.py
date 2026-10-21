"""SellIA Brain — unified capability registry.

Aggregates the three pillars of the selling brain into one introspectable
structure: AI agents, internal skills (knowledge + tools) and automations.
"""

from app.core.brain.activity import (
    ActivityEvent,
    BrainActivityBus,
    CuaFlowStore,
    get_activity_bus,
    get_cua_store,
    record_activity,
)
from app.core.brain.registry import (
    BrainRegistry,
    BrainSnapshot,
    Capability,
    CapabilityKind,
    get_brain_registry,
)

__all__ = [
    "ActivityEvent",
    "BrainActivityBus",
    "BrainRegistry",
    "BrainSnapshot",
    "Capability",
    "CapabilityKind",
    "CuaFlowStore",
    "get_activity_bus",
    "get_brain_registry",
    "get_cua_store",
    "record_activity",
]
