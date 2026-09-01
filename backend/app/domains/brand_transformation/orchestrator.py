"""Transformation Orchestrator — runs the staged program.

Drives a business through the 8 etapas (knowledge.TRANSFORMATION_STAGES),
feeding each stage's artifact forward as context to the next, and finally
synthesizes a 90/180/365 roadmap + metrics board.

Also runs the standing automations (re-diagnosis, brand-consistency monitor,
FOMO cadence, positioning-drift watch).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.brand_transformation import knowledge as K
from app.domains.brand_transformation.models import (
    BrandAutomation,
    TransformationProgram,
)
from app.domains.brand_transformation.service import (
    BrandIdentityAgent,
    BusinessModelAgent,
    DiagnosisAgent,
    FOMOEngineAgent,
    GoToMarketAgent,
    PositioningAgent,
    RestructuringAgent,
    _ask_json,
    _draft_then_refine,
    _profile_block,
)

logger = get_logger(__name__)

# stage_key -> (agent class, needs_context)
_STAGE_AGENTS = {
    "diagnosis": DiagnosisAgent,
    "positioning": PositioningAgent,
    "brand_identity": BrandIdentityAgent,
    "business_model": BusinessModelAgent,
    "fomo_engine": FOMOEngineAgent,
    "gtm": GoToMarketAgent,
    "restructuring": RestructuringAgent,
}


def _to_dict(row) -> dict:
    return {
        c.name: (str(v) if isinstance(v := getattr(row, c.name), (uuid.UUID, datetime)) else v)
        for c in row.__table__.columns
    }


class TransformationOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ program

    async def create_program(self, business_id: uuid.UUID, name: str, profile: dict) -> TransformationProgram:
        prog = TransformationProgram(
            business_id=business_id,
            name=name,
            current_stage="diagnosis",
            completed_stages=[],
            stage_artifacts={},
            metrics_board={"profile": profile},
        )
        self.db.add(prog)
        await self.db.commit()
        await self.db.refresh(prog)
        return prog

    async def get_program(self, program_id: uuid.UUID) -> TransformationProgram | None:
        r = await self.db.execute(select(TransformationProgram).where(TransformationProgram.id == program_id))
        return r.scalar_one_or_none()

    async def list_programs(self, business_id: uuid.UUID) -> list[TransformationProgram]:
        r = await self.db.execute(
            select(TransformationProgram).where(TransformationProgram.business_id == business_id)
            .order_by(desc(TransformationProgram.created_at))
        )
        return list(r.scalars().all())

    # ------------------------------------------------------------------ stages

    async def run_stage(
        self,
        program: TransformationProgram,
        stage_key: str,
        profile: dict | None = None,
        extra: str | None = None,
    ) -> dict:
        """Run one etapa, persist its artifact, advance the program pointer."""
        if stage_key not in K.STAGE_BY_KEY:
            raise ValueError(f"unknown stage: {stage_key}")

        stage = K.STAGE_BY_KEY[stage_key]
        profile = profile or (program.metrics_board or {}).get("profile") or {}

        if stage_key == "roadmap":
            artifact = await self._synthesize_roadmap(program, profile)
            artifact_id = None
        else:
            agent_cls = _STAGE_AGENTS[stage_key]
            agent = agent_cls(self.db)
            context = self._gather_context(program)
            if stage_key == "diagnosis":
                row = await agent.run(program.business_id, profile, extra)
            else:
                row = await agent.run(program.business_id, profile, context, extra)
            artifact = _to_dict(row)
            artifact_id = row.id

        # advance program
        completed = list(program.completed_stages or [])
        if stage_key not in completed:
            completed.append(stage_key)
        artifacts = dict(program.stage_artifacts or {})
        artifacts[stage_key] = str(artifact_id) if artifact_id else "synthesized"

        order = K.STAGE_ORDER
        idx = order.index(stage_key)
        next_stage = order[idx + 1] if idx + 1 < len(order) else None

        program.completed_stages = completed
        program.stage_artifacts = artifacts
        program.current_stage = next_stage or stage_key
        if next_stage is None:
            program.status = "completed"
        board = dict(program.metrics_board or {})
        board[stage_key] = artifact
        program.metrics_board = board
        await self.db.commit()
        await self.db.refresh(program)

        return {
            "program_id": program.id,
            "stage_key": stage_key,
            "stage_name": stage["name"],
            "artifact_id": artifact_id,
            "artifact": artifact,
            "next_stage": next_stage,
            "completed_stages": completed,
        }

    async def run_all(self, program: TransformationProgram, profile: dict | None = None) -> list[dict]:
        results = []
        for key in K.STAGE_ORDER:
            results.append(await self.run_stage(program, key, profile))
            program = await self.get_program(program.id)  # reload
        return results

    def _gather_context(self, program: TransformationProgram) -> dict:
        board = program.metrics_board or {}
        return {k: board.get(k) for k in K.STAGE_ORDER if board.get(k)}

    # ------------------------------------------------------------------ roadmap

    async def _synthesize_roadmap(self, program: TransformationProgram, profile: dict) -> dict:
        context = self._gather_context(program)
        prompt = f"""{_profile_block(profile)}

ALL STAGE OUTPUTS SO FAR:
{json.dumps(context, ensure_ascii=False)[:6000]}

TASK: Consolidate every stage into ONE execution roadmap that reads like a
battle plan, not a to-do list. Sequence matters — order the 90-day actions so
each unblocks the next. Every action ties to a named owner-role and a single
success metric. Flag dependencies. Then give a review ritual and a metrics board
(5-8 KPIs across positioning, brand, offer, FOMO, growth, retention), each KPI
naming the vanity metric it replaces.

Return JSON:
{{
  "north_star": "the one sentence that says what 'won' looks like in 12 months",
  "roadmap": {{
    "90": [{{"action": "...", "owner": "role", "metric": "...", "stage": "which etapa", "depends_on": "prior action or null"}}, ...],
    "180": [...],
    "365": [...]
  }},
  "sequencing_logic": "why the 90-day order is what it is",
  "biggest_risk": "the thing most likely to derail this and the early-warning signal",
  "review_ritual": {{"weekly": "...", "monthly": "...", "quarterly": "..."}},
  "metrics_board": [{{"kpi": "...", "baseline": "unknown|value", "target": "...", "dimension": "positioning|brand|offer|fomo|growth|retention", "replaces_vanity_metric": "..."}}, ...]
}}"""
        d = _draft_then_refine(prompt, {
            "north_star": "Be the name customers say first in this category, at a price we set.",
            "roadmap": {"90": [], "180": [], "365": []},
            "sequencing_logic": "Positioning and offer land before any spend; spend before scale.",
            "biggest_risk": "Executing the tactics while skipping the positioning commitment underneath them.",
            "review_ritual": {"weekly": "15-min metrics standup", "monthly": "stage retro + roadmap re-rank", "quarterly": "re-run diagnosis, compare score"},
            "metrics_board": [],
        }, "The 90-day sequence is the deliverable — make the ordering deliberate "
           "and the dependencies explicit. Cut any action without an owner and a metric.")
        program.roadmap = d.get("roadmap")
        board = dict(program.metrics_board or {})
        board["roadmap_synthesis"] = d
        program.metrics_board = board
        return d

    # ------------------------------------------------------------------ automations

    async def create_automation(self, business_id: uuid.UUID, automation_type: str, schedule: str, config: dict | None) -> BrandAutomation:
        row = BrandAutomation(
            business_id=business_id, automation_type=automation_type,
            schedule=schedule, config=config or {},
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def list_automations(self, business_id: uuid.UUID) -> list[BrandAutomation]:
        r = await self.db.execute(
            select(BrandAutomation).where(BrandAutomation.business_id == business_id)
            .order_by(desc(BrandAutomation.created_at))
        )
        return list(r.scalars().all())

    async def run_automation(self, automation: BrandAutomation) -> dict:
        """Execute one automation now. Returns its result payload."""
        bid = automation.business_id
        cfg = automation.config or {}
        profile = cfg.get("profile", {})
        result: dict

        if automation.automation_type == "rediagnosis":
            prior = await DiagnosisAgent(self.db).latest(bid)
            prior_score = prior.referent_potential_score if prior else None
            extra = "Periodic re-diagnosis."
            if prior:
                extra += (
                    f" Prior Referent Potential Score was {prior_score} on "
                    f"{prior.created_at:%Y-%m-%d}; prior symptoms: {json.dumps(prior.symptoms or [])[:600]}. "
                    "State explicitly what improved, what regressed, and what is still unaddressed."
                )
            row = await DiagnosisAgent(self.db).run(bid, profile, extra)
            delta = (row.referent_potential_score - prior_score) if prior_score is not None else None
            if prior is not None:
                row.compared_to_diagnosis_id = prior.id
                row.score_delta = delta
                await self.db.commit()
            result = {
                "type": "rediagnosis",
                "score": row.referent_potential_score,
                "prior_score": prior_score,
                "score_delta": delta,
                "trend": ("improving" if (delta or 0) > 2 else "declining" if (delta or 0) < -2 else "flat"),
                "summary": row.summary,
                "still_unaddressed": row.root_causes,
                "diagnosis_id": str(row.id),
            }

        elif automation.automation_type == "fomo_cadence":
            row = await FOMOEngineAgent(self.db).run(
                bid, profile, cfg.get("context"),
                "Generate ONLY the next cycle's activation: one lead mechanism + the "
                "ritual beat for this period + the exact copy hook. Keep it shippable this week.",
            )
            result = {"type": "fomo_cadence", "cadence": row.cadence, "next_activation": row.mechanisms, "ritual": row.launch_ritual, "playbook_id": str(row.id)}

        elif automation.automation_type in ("brand_consistency_monitor", "positioning_drift_watch", "competitor_narrative_watch"):
            samples = cfg.get("samples", [])
            _focus = {
                "brand_consistency_monitor": "voice, tone, and vocabulary vs the brand voice system (do/don't list, cliché blocklist)",
                "positioning_drift_watch": "whether the messaging still fights the stated enemy and holds the category frame, or has drifted back to feature-listing",
                "competitor_narrative_watch": "whether competitor messaging (in the samples) is encroaching on this brand's owned position, and how to counter it",
            }[automation.automation_type]
            prompt = f"""{_profile_block(profile)}

{K.QUALITY_BAR}

MONITOR: {automation.automation_type} — focus on {_focus}.
MATERIAL TO CHECK:
{json.dumps(samples, ensure_ascii=False)[:5000]}
BRAND REFERENCE (voice / positioning / enemy / category):
{json.dumps(cfg.get('brand_reference', {}), ensure_ascii=False)[:2500]}

TASK: Grade consistency 0-100. List specific violations with the exact offending
phrase and a rewrite. Give ONE sharp, quotable recommendation the team can act
on this week.

Return JSON:
{{
  "consistency_score": <int 0-100>,
  "verdict": "on-brand|minor-drift|major-drift",
  "violations": [{{"where": "...", "offending_phrase": "...", "issue": "...", "rewrite": "..."}}],
  "single_priority_fix": "the one thing to change first",
  "trend_note": "if prior runs exist in the reference, is this better or worse"
}}"""
            result = _ask_json(prompt, {"consistency_score": 70, "verdict": "minor-drift", "violations": [], "single_priority_fix": "Provide brand_reference + samples in config for a real check."})
            result["type"] = automation.automation_type
        else:
            result = {"type": automation.automation_type, "note": "no runner implemented"}

        automation.last_run_at = datetime.now(timezone.utc)
        automation.last_result = result
        automation.runs_count = (automation.runs_count or 0) + 1
        await self.db.commit()
        return result
