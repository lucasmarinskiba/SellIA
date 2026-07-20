"""SellIA Brain — unified capability registry.

Aggregates the three pillars of the selling brain into one introspectable
structure: AI agents, internal skills (knowledge + tools) and automations.
"""

from app.core.brain.registry import (
    BrainRegistry,
    get_brain_registry,
    BrainSnapshot,
    Capability,
    CapabilityKind,
)
from app.core.brain.activity import (
    BrainActivityBus,
    ActivityEvent,
    CuaFlowStore,
    get_activity_bus,
    get_cua_store,
    record_activity,
)

__all__ = [
    "BrainRegistry",
    "get_brain_registry",
    "BrainSnapshot",
    "Capability",
    "CapabilityKind",
    "BrainActivityBus",
    "ActivityEvent",
    "CuaFlowStore",
    "get_activity_bus",
    "get_cua_store",
    "record_activity",
]
