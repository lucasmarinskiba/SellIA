"""Proximity marketing domain — detect nearby users and trigger automations."""

from .proximity_engine import ProximityEngine, GeoPoint, ProximityMatch, ProximityTriggerConfig

__all__ = ["ProximityEngine", "GeoPoint", "ProximityMatch", "ProximityTriggerConfig"]
