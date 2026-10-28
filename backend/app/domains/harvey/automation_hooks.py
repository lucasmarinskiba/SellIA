"""Harvey events into the business's own workflows (the real engine in ``domains.automations``).

Harvey reuses existing trigger types, so nothing new is needed in the database:
  new_lead              a prospect answered and became a deal
  stage_changed         that deal moved ("from"/"to" in the data)
  appointment_scheduled the prospect booked a meeting
  revenue_event         the prospect paid

Every event carries ``source="harvey"``. The engine only runs a workflow on such an event when the workflow asked
for it (``trigger_config = {"sources": ["harvey"]}``), so a chat automation built for WhatsApp leads never fires on
a prospecting email by surprise.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

SOURCE = "harvey"
TRIGGERS = ("new_lead", "stage_changed", "appointment_scheduled", "revenue_event")


async def fire(db: AsyncSession, trigger: str, business_id: uuid.UUID, data: dict[str, Any]) -> None:
    """Run the business's matching workflows. Never raises and never touches the caller's session.

    The engine commits (and rolls back on failure), so it gets its own session on the same engine: whatever goes
    wrong there cannot expire the caller's objects or undo the deal and alert that are already saved.
    """
    if trigger not in TRIGGERS:
        return
    try:
        from app.domains.automations.engine import WorkflowEngine
        from app.domains.automations.models import WorkflowTriggerType

        engine = db.bind
        if engine is None:
            from app.core.database import AsyncSessionLocal

            factory: Any = AsyncSessionLocal
            own = factory()
        else:
            own = AsyncSession(engine, expire_on_commit=False)
        async with own:
            await WorkflowEngine(own).process_trigger(
                trigger_type=WorkflowTriggerType(trigger),
                business_id=business_id,
                conversation_id=None,
                trigger_data={**data, "source": SOURCE},
            )
    except Exception:  # noqa: BLE001 - the deal and the alert are already saved
        logger.warning("harvey: workflow trigger %s failed", trigger, exc_info=True)
