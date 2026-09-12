"""Brain Interaction Map id ↔ AutomationToggle.toggle_key mapping.

The Brain Map (`GET /brain/graph`) uses dot-separated ids built by
`app/core/brain/registry.py`'s static capability lists: `platform.google_ads`,
`agent.expert.pricing`, `skill.tool.copywriter`, `automation.fomo_campaigns`.

`AutomationToggle.toggle_key` (app/domains/automations/models.py) uses a
colon after the category, e.g. `"automation:cold_email"`.

These two id spaces are otherwise unrelated (built independently, for
different purposes), so a brain id is mapped onto a toggle_key by swapping
just the FIRST dot for a colon -- this is exactly invertible (swap the first
colon back) and, for automation ids with no further dots (the common case,
e.g. `automation.fomo_campaigns` -> `automation:fomo_campaigns`), lines up
with toggle_keys that already exist in `toggle_enforcement.py`'s
PROTECTED_ROUTES, so no separate key needs to be invented for those.
"""

from __future__ import annotations

from app.domains.automations.models import ToggleCategory

_PREFIX_TO_CATEGORY: dict[str, ToggleCategory] = {
    "platform": ToggleCategory.INTEGRATION,
    "agent": ToggleCategory.AGENT,
    "skill": ToggleCategory.FEATURE,
    "automation": ToggleCategory.AUTOMATION,
}


def brain_id_to_toggle_key(brain_id: str) -> str:
    """`"automation.fomo_campaigns"` -> `"automation:fomo_campaigns"`."""
    return brain_id.replace(".", ":", 1)


def toggle_key_to_brain_id(toggle_key: str) -> str:
    """`"automation:fomo_campaigns"` -> `"automation.fomo_campaigns"`."""
    return toggle_key.replace(":", ".", 1)


def brain_id_category(brain_id: str) -> ToggleCategory:
    prefix = brain_id.split(".", 1)[0]
    return _PREFIX_TO_CATEGORY.get(prefix, ToggleCategory.FEATURE)
