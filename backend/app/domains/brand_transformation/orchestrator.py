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
    BrandIdentity,
    PositioningStatement,
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
    _int,
    _profile_block,
    _stage_context_digest,
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

    async def create_program(
        self,
        business_id: uuid.UUID,
        name: str,
        profile: dict,
        auto_bridges: dict | None = None,
        owner_user_id: uuid.UUID | None = None,
    ) -> TransformationProgram:
        prog = TransformationProgram(
            business_id=business_id,
            name=name,
            current_stage="diagnosis",
            completed_stages=[],
            stage_artifacts={},
            metrics_board={"profile": profile},
            auto_bridges=auto_bridges or None,
            owner_user_id=owner_user_id,
        )
        self.db.add(prog)
        await self.db.commit()
        await self.db.refresh(prog)
        return prog

    async def set_auto_bridges(self, program: TransformationProgram, auto_bridges: dict, owner_user_id: uuid.UUID | None = None) -> TransformationProgram:
        program.auto_bridges = auto_bridges or None
        if owner_user_id is not None:
            program.owner_user_id = owner_user_id
        await self.db.commit()
        await self.db.refresh(program)
        return program

    async def _run_stage_bridge(self, program: TransformationProgram, stage_key: str) -> dict | None:
        """After a stage completes, fire its bridge if the program opted in."""
        cfg = program.auto_bridges or {}
        try:
            if stage_key == "positioning" and cfg.get("competitive"):
                from app.domains.brand_transformation.positioning_bridge import PositioningBridge

                st = await PositioningAgent(self.db).latest(program.business_id)
                comps = cfg.get("competitors")  # optional [{name,url}]
                if not comps:
                    names = (program.metrics_board or {}).get("profile", {}).get("known_competitors") or []
                    comps = [{"name": n} for n in names]
                if st and comps and program.owner_user_id:
                    return await PositioningBridge(self.db).deploy(
                        st, owner_user_id=program.owner_user_id, competitors=comps,
                    )
            elif stage_key == "brand_identity" and cfg.get("assets"):
                from app.domains.brand_transformation.identity_bridge import IdentityBridge

                it = await BrandIdentityAgent(self.db).latest(program.business_id)
                if it:
                    return await IdentityBridge(self.db).deploy(it)
            elif stage_key == "fomo_engine" and (cfg.get("fomo") or {}).get("enabled"):
                from app.domains.brand_transformation.fomo_bridge import FOMOBridge

                pb = await FOMOEngineAgent(self.db).latest(program.business_id)
                if pb and program.owner_user_id:
                    return await FOMOBridge(self.db).deploy(
                        pb, owner_user_id=program.owner_user_id,
                        activate=bool((cfg.get("fomo") or {}).get("activate", False)),
                    )
        except Exception as e:  # noqa: BLE001
            logger.warning("auto-bridge for stage %s failed: %s", stage_key, str(e)[:200])
            return {"bridge_error": str(e)[:200]}
        return None

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

        # opt-in auto-bridges: push this stage's artifact into the real domain
        bridge_result = None
        if stage_key != "roadmap" and program.auto_bridges:
            bridge_result = await self._run_stage_bridge(program, stage_key)
            if bridge_result is not None:
                board = dict(program.metrics_board or {})
                board[f"{stage_key}_bridge"] = bridge_result
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
            "bridge_result": bridge_result,
        }

    async def run_all(self, program: TransformationProgram, profile: dict | None = None) -> list[dict]:
        results = []
        for key in K.STAGE_ORDER:
            results.append(await self.run_stage(program, key, profile))
            program = await self.get_program(program.id)  # reload
        # full program done -> audit internal coherence
        try:
            await self.coherence_audit(program)
        except Exception as e:  # noqa: BLE001
            logger.warning("coherence_audit after run_all failed: %s", str(e)[:160])
        return results

    def _gather_context(self, program: TransformationProgram) -> dict:
        board = program.metrics_board or {}
        return {k: board.get(k) for k in K.STAGE_ORDER if board.get(k)}

    # ------------------------------------------------------------------ coherence

    async def coherence_audit(self, program: TransformationProgram) -> dict:
        """Do the 7 stage artifacts actually agree with each other?

        Program-level check: catches internal drift between stages (three
        different enemies, an offer that can't fund the loop, FOMO that fails
        the brand's own ethics review, a roadmap that violates its own
        dependencies). Read-only over the artifacts; writes the audit back
        onto the program.
        """
        context = self._gather_context(program)
        done = [k for k in K.STAGE_ORDER if k in context and k != "roadmap"]
        prompt = f"""{_profile_block((program.metrics_board or {}).get("profile") or {})}

{_stage_context_digest(context)}

STAGES PRESENT: {', '.join(done) or 'none'}

RUN THESE CROSS-STAGE COHERENCE CHECKS:
{K.coherence_checks_digest()}

TASK: For each check, decide pass / warn / fail based ONLY on the artifacts
above. If a stage needed for a check is missing, mark it "n/a". Quote the
specific contradicting text. Then give an overall 0-100 coherence score and the
list of things that must be fixed before launch.

Return JSON:
{{
  "score": <int 0-100>,
  "checks": [{{"id": "<check id>", "verdict": "pass|warn|fail|n/a", "contradiction": "the specific clash, quoting both sides — or null", "fix": "the concrete change to make them agree"}}],
  "must_fix_before_launch": ["the fails, in priority order"],
  "summary": "2-3 sentences — is this program internally consistent or is it drifting?"
}}"""
        d = _draft_then_refine(prompt, {
            "score": 60,
            "checks": [{"id": c["id"], "verdict": "n/a", "contradiction": None, "fix": "Run the relevant stages first."} for c in K.COHERENCE_CHECKS],
            "must_fix_before_launch": [],
            "summary": "Not enough stages completed to judge coherence — run the full program, then re-audit.",
        }, "Every verdict must cite the artifact text it's based on. 'warn' needs a "
           "real tension, not a nitpick. The fix must be a concrete edit to one "
           "named stage.")

        program.coherence_audit = {
            "score": _int(d.get("score"), 0),
            "checks": d.get("checks"),
            "must_fix_before_launch": d.get("must_fix_before_launch"),
            "summary": d.get("summary"),
            "stages_audited": done,
            "generated_by": d.get("_generated_by", "unknown"),
        }
        await self.db.commit()
        return program.coherence_audit

    # ------------------------------------------------------------------ roadmap

    async def _synthesize_roadmap(self, program: TransformationProgram, profile: dict) -> dict:
        """Etapa 7 — consolidate all stages into a sequenced execution plan.

        Not a to-do list: a dependency graph, a critical path, decision gates
        with a real 'pause' option at each horizon, a leading-indicator
        dashboard that predicts the lagging KPIs, and explicit kill switches.
        """
        context = self._gather_context(program)
        prompt = f"""{_profile_block(profile)}

{_stage_context_digest(context)}

HORIZONS:
{K.roadmap_horizons_digest()}

DECISION GATES: {K.DECISION_GATE_TEMPLATE}
LEADING INDICATORS: {K.LEADING_INDICATOR_HINT}

TASK: Consolidate every stage into ONE execution plan. Sequence is the point —
build the dependency graph first, then lay actions on it. Every horizon ends in
a decision gate with a real 'pause' option. The leading-indicator dashboard must
predict the lagging KPIs, not restate them. Pull kill switches from the
diagnosis kill_criteria and the restructuring unit_economics_gate.

Return JSON:
{{
  "north_star": "one sentence — what 'won' looks like in 12 months",
  "dependency_graph": [{{"move": "a major move", "stage": "which etapa", "blocked_by": ["moves that must finish first"], "unblocks": ["moves it enables"]}}],
  "critical_path": ["the ordered chain of moves that sets total time — the longest pole"],
  "workstreams": [{{"name": "e.g. positioning+brand / offer+pricing / fomo / gtm / ops", "owner": "role", "this_quarter_goal": "..."}}],
  "roadmap": {{
    "90": {{"theme": "prove the thesis", "entry_gate": "what must be true to start", "actions": [{{"action": "...", "owner": "role", "metric": "...", "stage": "...", "depends_on": "prior action or null"}}], "exit_gate": {{"question": "...", "data_needed": "...", "calls": ["double down", "adjust", "pause"], "proceed_criteria": "..."}}}},
    "180": {{"theme": "compound it", ...}},
    "365": {{"theme": "own it", ...}}
  }},
  "decision_gates": [{{"day": 30, "question": "...", "data_needed": "...", "possible_calls": ["..."]}}, {{"day": 60, ...}}, {{"day": 90, ...}}, {{"day": 180, ...}}],
  "kill_switches": [{{"condition": "from diagnosis kill_criteria / unit_economics_gate", "means": "stop the transformation and pivot/sell", "check_at": "which gate"}}],
  "resourcing": {{"founder_time_split": {{"positioning/brand": "%", "gtm": "%", "ops": "%"}}, "outsource": ["..."], "the_one_hire": "from restructuring, or none", "budget_shape": "from GTM"}},
  "leading_indicators": [{{"metric": "...", "source": "...", "green": "...", "yellow": "...", "red": "...", "forecasts_lagging_kpi": "..."}}],
  "metrics_board": [{{"kpi": "lagging outcome", "baseline": "value|unknown", "target": "...", "dimension": "positioning|brand|offer|fomo|growth|retention", "replaces_vanity_metric": "..."}}],
  "first_2_weeks": [{{"action": "concrete kickoff task, pulled from the stages' quick-wins / week-1", "owner": "role"}}],
  "sequencing_logic": "why the order is what it is",
  "biggest_risk": "most likely derailment + the early-warning signal",
  "operating_rhythm_ref": "use the restructuring plan's operating_rhythm if present, else: weekly metrics + monthly retro + quarterly re-diagnosis"
}}"""
        d = _draft_then_refine(prompt, {
            "north_star": "Be the name customers say first in this category, at a price we set.",
            "dependency_graph": [
                {"move": "Lock positioning + POV", "stage": "positioning", "blocked_by": ["Diagnosis"], "unblocks": ["Brand identity", "Offer redesign", "Content engine"]},
                {"move": "Ship grand-slam offer", "stage": "business_model", "blocked_by": ["Positioning"], "unblocks": ["GTM launch", "FOMO mechanisms"]},
            ],
            "critical_path": ["Diagnosis", "Positioning", "Offer redesign", "GTM launch", "Loop turning", "Moat move"],
            "workstreams": [],
            "roadmap": {
                "90": {"theme": "prove the thesis", "entry_gate": "Diagnosis done, founder committed to a POV", "actions": [], "exit_gate": {"question": "Did the new positioning + offer beat the old on conversion?", "data_needed": "A/B or before/after conv. + qualitative", "calls": ["double down", "adjust", "pause"], "proceed_criteria": "conversion up or clear qualitative pull"}},
                "180": {"theme": "compound it", "entry_gate": "90-day gate passed", "actions": [], "exit_gate": {"question": "Is the growth loop turning without founder push?", "data_needed": "loop turning_metric trend", "calls": ["scale spend", "fix the loop", "pause"], "proceed_criteria": "loop metric compounding 8+ weeks"}},
                "365": {"theme": "own it", "entry_gate": "loop compounding", "actions": [], "exit_gate": {"question": "Does the market use our category frame / pay our price?", "data_needed": "inbound language, price realised, win rate", "calls": ["press the lead", "reposition", "hold"], "proceed_criteria": "category recognition + pricing power visible"}},
            },
            "decision_gates": [
                {"day": 30, "question": "Is the POV landing with best-fit customers?", "data_needed": "10+ customer reactions", "possible_calls": ["proceed", "sharpen the enemy", "pause"]},
                {"day": 90, "question": "New positioning + offer beating the old?", "data_needed": "conversion delta", "possible_calls": ["double down", "adjust", "pause"]},
            ],
            "kill_switches": [
                {"condition": "Margin can't fund any brand investment for 12 months", "means": "Don't chase referent status — fix economics or pivot", "check_at": "day 30"},
                {"condition": "CAC payback past 4 months two months running", "means": "Pause acquisition spend", "check_at": "day 90 gate"},
            ],
            "resourcing": {"founder_time_split": {"positioning/brand": "40%", "gtm": "40%", "ops": "20%"}, "outsource": ["design production", "content editing"], "the_one_hire": "none in first 90 days", "budget_shape": "60% content / 25% channels / 15% tools"},
            "leading_indicators": [
                {"metric": "best-fit trials started / week", "source": "signups tagged by ICP", "green": "growing wk/wk", "yellow": "flat", "red": "declining 3 wks", "forecasts_lagging_kpi": "MRR"},
                {"metric": "POV content shares", "source": "social + referral logs", "green": ">X", "yellow": "some", "red": "none", "forecasts_lagging_kpi": "organic acquisition"},
            ],
            "metrics_board": [],
            "first_2_weeks": [
                {"action": "Publish the POV piece the positioning implies; pin everywhere", "owner": "founder"},
                {"action": "Rewrite homepage + hero around the one-liner and enemy", "owner": "founder"},
                {"action": "DM 10 best-fit customers for reactions to the new frame", "owner": "founder"},
            ],
            "sequencing_logic": "Positioning and offer land before any spend; spend before scale; moat moves only once the loop turns.",
            "biggest_risk": "Executing tactics while skipping the positioning commitment underneath — early signal: the team can't state the enemy in one sentence.",
            "operating_rhythm_ref": "weekly metrics + monthly retro + quarterly re-diagnosis",
        }, "The dependency graph and critical path are the deliverable. Every "
           "horizon needs a real 'pause' call. Leading indicators must forecast a "
           "named lagging KPI, not duplicate it. Kill switches must be concrete "
           "conditions, not 'if it's not working'.")

        program.roadmap = {
            k: d.get(k) for k in ("north_star", "roadmap", "workstreams", "sequencing_logic", "biggest_risk", "metrics_board")
        }
        program.execution_plan = {
            k: d.get(k) for k in (
                "dependency_graph", "critical_path", "decision_gates", "kill_switches",
                "resourcing", "leading_indicators", "first_2_weeks", "operating_rhythm_ref",
            )
        }
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

    async def automation_alerts(self, business_id: uuid.UUID) -> list[dict]:
        """Every automation currently flagging an alert (warn/critical)."""
        rows = await self.list_automations(business_id)
        out = []
        for a in rows:
            if a.last_alert:
                out.append({
                    "automation_id": str(a.id),
                    "type": a.automation_type,
                    "severity": a.last_severity,
                    "at": a.last_run_at.isoformat() if a.last_run_at else None,
                    "headline": (a.last_result or {}).get("headline") or (a.last_result or {}).get("summary"),
                    "recommended_action": (a.last_result or {}).get("recommended_action"),
                })
        return out

    async def _hydrate_brand_reference(self, bid: uuid.UUID) -> dict:
        """Latest positioning + identity, for monitors that weren't given a reference."""
        pos = (await self.db.execute(
            select(PositioningStatement).where(PositioningStatement.business_id == bid)
            .order_by(desc(PositioningStatement.created_at)).limit(1)
        )).scalar_one_or_none()
        ident = (await self.db.execute(
            select(BrandIdentity).where(BrandIdentity.business_id == bid)
            .order_by(desc(BrandIdentity.created_at)).limit(1)
        )).scalar_one_or_none()
        ref: dict = {}
        if pos:
            ref["positioning_statement"] = pos.positioning_statement
            ref["one_liner"] = pos.one_liner
            ref["the_enemy"] = pos.the_enemy
            ref["point_of_view"] = pos.point_of_view
            ref["market_category"] = pos.market_category
            ref["new_category_name"] = pos.new_category_name
        if ident:
            ref["primary_archetype"] = ident.primary_archetype
            ref["tagline"] = ident.tagline
            ref["voice_attributes"] = ident.voice_attributes
            ref["verbal_identity"] = ident.verbal_identity
            ref["identity_consistency_rules"] = ident.identity_consistency_rules
        return ref

    @staticmethod
    def _grade_severity(score: int | None, verdict: str | None) -> tuple[str, bool]:
        """(severity, is_alert) from a 0-100 consistency/coherence score + verdict."""
        v = (verdict or "").lower()
        if "major" in v or (score is not None and score < 45):
            return "critical", True
        if "minor" in v or (score is not None and score < 70):
            return "warn", True
        return "ok", False

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
            trend = "improving" if (delta or 0) > 2 else "declining" if (delta or 0) < -2 else "flat"
            alert_below = cfg.get("alert_below")
            severity, alert = "ok", False
            if trend == "declining":
                severity, alert = "warn", True
            if alert_below is not None and row.referent_potential_score < alert_below:
                severity, alert = "critical", True
            result = {
                "type": "rediagnosis",
                "score": row.referent_potential_score,
                "prior_score": prior_score,
                "score_delta": delta,
                "trend": trend,
                "severity": severity,
                "alert": alert,
                "headline": f"Referent Potential {row.referent_potential_score} ({trend}, Δ{delta if delta is not None else 'n/a'})",
                "recommended_action": (
                    "Re-run the transformation program's weakest stage" if alert
                    else "On track — no action"
                ),
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

            # optionally push the cycle's mechanisms straight into real fomo campaigns
            if cfg.get("auto_deploy") and cfg.get("owner_user_id"):
                try:
                    from app.domains.brand_transformation.fomo_bridge import FOMOBridge

                    dep = await FOMOBridge(self.db).deploy(
                        row, owner_user_id=cfg["owner_user_id"],
                        activate=bool(cfg.get("activate", False)),
                    )
                    result["deployed_campaigns"] = dep.get("deployed")
                    result["campaigns_created"] = dep.get("created_count")
                except Exception as e:  # noqa: BLE001
                    result["deploy_error"] = str(e)[:200]

        elif automation.automation_type in ("brand_consistency_monitor", "positioning_drift_watch", "competitor_narrative_watch"):
            samples = cfg.get("samples", [])
            _focus = {
                "brand_consistency_monitor": "voice, tone, and vocabulary vs the brand voice system (do/don't list, cliché blocklist)",
                "positioning_drift_watch": "whether the messaging still fights the stated enemy and holds the category frame, or has drifted back to feature-listing",
                "competitor_narrative_watch": "whether competitor messaging (in the samples) is encroaching on this brand's owned position, and how to counter it",
            }[automation.automation_type]
            _fix_stage = {
                "brand_consistency_monitor": "brand_identity",
                "positioning_drift_watch": "positioning",
                "competitor_narrative_watch": "positioning",
            }[automation.automation_type]
            brand_ref = cfg.get("brand_reference") or await self._hydrate_brand_reference(bid)
            prev_scores = [h.get("score") for h in (automation.run_history or []) if h.get("score") is not None][-5:]
            prompt = f"""{_profile_block(profile)}

{K.QUALITY_BAR}

MONITOR: {automation.automation_type} — focus on {_focus}.
MATERIAL TO CHECK:
{json.dumps(samples, ensure_ascii=False)[:5000]}
BRAND REFERENCE (voice / positioning / enemy / category — pulled from the program):
{json.dumps(brand_ref, ensure_ascii=False)[:3000]}
PRIOR CONSISTENCY SCORES (oldest→newest): {prev_scores or "none"}

TASK: Grade consistency 0-100. List specific violations with the exact offending
phrase and a rewrite. Give ONE sharp recommendation for THIS week, and say
whether the fix is a copy edit or needs the '{_fix_stage}' stage re-run.

Return JSON:
{{
  "consistency_score": <int 0-100>,
  "verdict": "on-brand|minor-drift|major-drift",
  "violations": [{{"where": "...", "offending_phrase": "...", "issue": "...", "rewrite": "..."}}],
  "single_priority_fix": "the one thing to change first",
  "fix_type": "copy_edit | rerun_stage",
  "trend_note": "vs the prior scores: improving / flat / worsening"
}}"""
            result = _ask_json(prompt, {
                "consistency_score": 70, "verdict": "minor-drift", "violations": [],
                "single_priority_fix": "Provide samples in config for a real check.",
                "fix_type": "copy_edit", "trend_note": "n/a",
            })
            result["type"] = automation.automation_type
            result["score"] = result.get("consistency_score")
            sev, alert = self._grade_severity(result.get("consistency_score"), result.get("verdict"))
            result["severity"], result["alert"] = sev, alert
            result["headline"] = f"{automation.automation_type}: {result.get('verdict')} ({result.get('consistency_score')}/100)"
            result["recommended_action"] = (
                f"Re-run the '{_fix_stage}' stage" if result.get("fix_type") == "rerun_stage"
                else result.get("single_priority_fix")
            )

        elif automation.automation_type == "roadmap_gate_check":
            prog = None
            pid = cfg.get("program_id")
            if pid:
                prog = await self.get_program(uuid.UUID(pid) if isinstance(pid, str) else pid)
            if not prog:
                progs = await self.list_programs(bid)
                prog = progs[0] if progs else None
            plan = (prog.execution_plan if prog else None) or {}
            readings = cfg.get("indicator_readings", {})  # {metric: current value/status}
            prompt = f"""{_profile_block(profile)}

EXECUTION PLAN (decision gates + leading indicators):
{json.dumps({k: plan.get(k) for k in ('decision_gates', 'leading_indicators', 'kill_switches')}, ensure_ascii=False)[:4000]}

CURRENT INDICATOR READINGS (from the business): {json.dumps(readings, ensure_ascii=False)[:2000]}
DAYS SINCE PROGRAM START: {cfg.get('days_elapsed', 'unknown')}

TASK: For the gate that is due (or most recently passed), evaluate the leading
indicators against their green/yellow/red thresholds and any kill switches. Make
the call.

Return JSON:
{{
  "gate": "which decision gate this is",
  "indicator_status": [{{"metric": "...", "reading": "...", "zone": "green|yellow|red"}}],
  "kill_switch_triggered": true|false,
  "call": "double_down | adjust | pause | pivot",
  "why": "...",
  "next_actions": ["..."]
}}"""
            result = _ask_json(prompt, {
                "gate": "unknown", "indicator_status": [], "kill_switch_triggered": False,
                "call": "adjust", "why": "Provide indicator_readings + program_id in config.",
                "next_actions": [],
            })
            result["type"] = "roadmap_gate_check"
            call = str(result.get("call", "")).lower()
            if result.get("kill_switch_triggered") or call in ("pause", "pivot"):
                result["severity"], result["alert"] = "critical", True
            elif call == "adjust":
                result["severity"], result["alert"] = "warn", True
            else:
                result["severity"], result["alert"] = "ok", False
            result["headline"] = f"Gate '{result.get('gate')}': {result.get('call')}"
            result["recommended_action"] = "; ".join(result.get("next_actions") or []) or result.get("why")

        elif automation.automation_type == "transformation_pulse":
            diag = await DiagnosisAgent(self.db).latest(bid)
            progs = await self.list_programs(bid)
            prog = progs[0] if progs else None
            all_auto = await self.list_automations(bid)
            open_alerts = [
                {"type": a.automation_type, "severity": a.last_severity,
                 "headline": (a.last_result or {}).get("headline")}
                for a in all_auto if a.last_alert and a.id != automation.id
            ]
            coh = (prog.coherence_audit if prog else None) or {}
            result = {
                "type": "transformation_pulse",
                "referent_potential_score": diag.referent_potential_score if diag else None,
                "score_trend": (diag.score_delta if diag else None),
                "program_status": prog.status if prog else "none",
                "stages_completed": len(prog.completed_stages or []) if prog else 0,
                "coherence_score": coh.get("score"),
                "coherence_must_fix": coh.get("must_fix_before_launch") or [],
                "open_alerts": open_alerts,
                "headline": (
                    f"Score {diag.referent_potential_score if diag else '?'} · "
                    f"{len(prog.completed_stages or []) if prog else 0}/8 etapas · "
                    f"coherencia {coh.get('score', '?')} · {len(open_alerts)} alertas"
                ),
            }
            crit = any(a["severity"] == "critical" for a in open_alerts) or (coh.get("score") or 100) < 50
            result["severity"] = "critical" if crit else ("warn" if open_alerts else "ok")
            result["alert"] = bool(crit or open_alerts)
            result["recommended_action"] = (
                "Address the open critical alerts first" if crit
                else "Review open alerts" if open_alerts else "Healthy — keep the cadence"
            )
        else:
            result = {"type": automation.automation_type, "note": "no runner implemented", "severity": "ok", "alert": False}

        from app.domains.brand_transformation.service import llm_available

        result.setdefault("llm_used", llm_available())
        result.setdefault("severity", "ok")
        result.setdefault("alert", False)

        now = datetime.now(timezone.utc)
        automation.last_run_at = now
        automation.last_result = result
        automation.runs_count = (automation.runs_count or 0) + 1
        automation.last_severity = result["severity"]
        automation.last_alert = bool(result["alert"])
        hist = list(automation.run_history or [])
        hist.append({
            "at": now.isoformat(),
            "severity": result["severity"],
            "alert": bool(result["alert"]),
            "score": result.get("score") or result.get("referent_potential_score") or result.get("coherence_score"),
            "headline": result.get("headline") or result.get("summary"),
        })
        automation.run_history = hist[-20:]
        await self.db.commit()
        return result
