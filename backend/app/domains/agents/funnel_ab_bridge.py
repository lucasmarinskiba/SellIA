"""Funnel-Stage A/B Testing Bridge.

Connects FUNNEL_STAGE_VOICE_SLUGS (app/core/prompts/funnel_specialists.py)
to the existing prompt-experiment engine (app/domains/agents/ab_service.py),
so that when a funnel stage has 2+ recommended expert voices, SellIA
automatically A/B tests between them instead of always defaulting to the
primary recommendation — and promotes the voice that actually converts
better, per stage, over time.

Experiments here are global (business_id=None) and keyed by
agent_type=f"funnel_{stage.value}", auto-provisioned on first use. The
existing `PromptExperiment.variant_a_prompt` / `variant_b_prompt` columns
are repurposed to store the two candidate voice SLUGS (e.g. "jordan-belfort")
rather than full raw prompt text — the actual prompt composition still goes
through compose_system_prompt(), preserving the functional role + business
context + funnel tactics layering. Only the voice choice is what's tested.
"""

import uuid
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.ab_service import ABTestEngine
from app.domains.channels.models import Conversation
from app.core.prompts.funnel_specialists import FunnelStage, get_recommended_voice_slugs
from app.core.logger import get_logger

logger = get_logger(__name__)

_MIN_SAMPLES = 20
_CONFIDENCE_THRESHOLD = 0.90


def _experiment_agent_type(stage: FunnelStage) -> str:
    return f"funnel_{stage.value}"


async def _get_or_create_stage_experiment(db: AsyncSession, stage: FunnelStage):
    """Return the running global experiment for a stage, auto-creating it
    the first time a stage with 2+ recommended voices is used."""
    agent_type = _experiment_agent_type(stage)

    experiment = await ABTestEngine.get_active_experiment_for_agent(
        db, agent_type=agent_type, business_id=None
    )
    if experiment:
        return experiment

    slugs = get_recommended_voice_slugs(stage)
    if len(slugs) < 2:
        return None

    experiment = await ABTestEngine.create_experiment(
        db,
        name=f"Funnel voice test — {stage.value}",
        agent_type=agent_type,
        variant_a_name=slugs[0],
        variant_a_prompt=slugs[0],
        variant_b_name=slugs[1],
        variant_b_prompt=slugs[1],
        metric="conversion",
        business_id=None,
        confidence_threshold=_CONFIDENCE_THRESHOLD,
        min_samples=_MIN_SAMPLES,
    )
    experiment = await ABTestEngine.start_experiment(db, experiment.id)
    logger.info(f"Auto-created funnel voice experiment for stage '{stage.value}': {slugs[0]} vs {slugs[1]}")
    return experiment


async def get_stage_voice_slug(
    db: AsyncSession,
    stage: FunnelStage,
    conversation: Conversation,
) -> Tuple[Optional[str], Optional[uuid.UUID], Optional[str]]:
    """Pick the voice slug to use for this stage, running an A/B test when
    the stage has multiple recommended voices.

    Returns (voice_slug, experiment_id, variant). experiment_id/variant are
    None when no experiment applies (single-voice stage, or lookup failed) —
    voice_slug still falls back to the primary recommendation in that case.
    """
    slugs = get_recommended_voice_slugs(stage)
    fallback = slugs[0] if slugs else None

    try:
        experiment = await _get_or_create_stage_experiment(db, stage)
        if not experiment:
            return fallback, None, None

        variant = ABTestEngine.get_variant_for_conversation(db, experiment.id, conversation.id)
        voice_slug = experiment.variant_a_prompt if variant == "a" else experiment.variant_b_prompt

        # Remember the assignment on the conversation so a later conversion
        # event can be attributed back to this experiment/variant.
        extra_data = dict(conversation.extra_data or {})
        existing = extra_data.get("funnel_ab")
        if not existing or existing.get("experiment_id") != str(experiment.id):
            extra_data["funnel_ab"] = {
                "experiment_id": str(experiment.id),
                "variant": variant,
                "stage": stage.value,
            }
            conversation.extra_data = extra_data
            db.add(conversation)
            await db.commit()

        return voice_slug, experiment.id, variant

    except Exception as e:
        logger.warning(f"Funnel A/B voice selection failed for stage '{stage.value}': {e}")
        return fallback, None, None


async def record_stage_conversion(db: AsyncSession, conversation: Conversation) -> None:
    """Record a conversion outcome for the conversation's tracked funnel A/B
    assignment, if any, and check for auto-promotion.

    Safe to call unconditionally when an order becomes paid/completed —
    it's a no-op if the conversation was never enrolled in an experiment.
    """
    try:
        tracking = (conversation.extra_data or {}).get("funnel_ab")
        if not tracking:
            return

        experiment_id = uuid.UUID(tracking["experiment_id"])
        variant = tracking["variant"]

        await ABTestEngine.record_result(
            db,
            experiment_id=experiment_id,
            conversation_id=conversation.id,
            variant=variant,
            outcome="converted",
        )
        await ABTestEngine.check_auto_promote(db, experiment_id)

    except Exception as e:
        logger.warning(f"Failed to record funnel A/B conversion: {e}")


__all__ = ["get_stage_voice_slug", "record_stage_conversion"]
