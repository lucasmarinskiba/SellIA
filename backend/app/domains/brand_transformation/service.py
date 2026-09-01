"""Brand Transformation services — the specialist AI agents.

Each agent runs a two-pass pipeline for professional-grade output:
  1. DRAFT   — prompt injects the relevant research (knowledge.py) + the
               quality bar, Claude returns strict JSON.
  2. REFINE  — an adversarial critique pass grades the draft against the
               quality bar (cut clichés, sharpen vague claims, add a named
               precedent, raise eloquence/ocurrencia) and returns the same
               keys, sharper — plus `confidence` and `frameworks_applied`.
  3. persist an artifact row and return it.

Agents:
  DiagnosisAgent        -> BrandDiagnosis           (Etapa 0)
  PositioningAgent      -> PositioningStatement     (Etapa 1)
  BrandIdentityAgent    -> BrandIdentity            (Etapa 2)
  BusinessModelAgent    -> BusinessModelRedesign    (Etapa 3)
  FOMOEngineAgent       -> FOMOPlaybook             (Etapa 4)
  GoToMarketAgent       -> GTMPlan                  (Etapa 5)
  RestructuringAgent    -> RestructuringPlan        (Etapa 6)
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.brand_transformation import knowledge as K
from app.domains.brand_transformation.models import (
    BrandDiagnosis,
    BrandIdentity,
    BusinessModelRedesign,
    FOMOPlaybook,
    GTMPlan,
    PositioningStatement,
    RestructuringPlan,
)

logger = get_logger(__name__)

_MODEL = "claude-opus-5"
_MAX_TOKENS = 4500

_SYSTEM = (
    "You are a senior brand strategist and business-model architect who turns "
    "commoditized, mediocre businesses into category references. You reason from "
    "concrete precedents (Red Bull, Supreme, Starbucks, Tesla, Liquid Death, "
    "Decathlon, Apple, Coca-Cola, Nike) and named frameworks (Dunford positioning, "
    "Play Bigger category design, Jung archetypes, Hormozi value equation, Blue "
    "Ocean ERRC, growth loops). You are specific, opinionated, witty, and allergic "
    "to generic marketing filler.\n\n"
    + K.QUALITY_BAR
    + "\n\nYou ALWAYS answer with a single valid JSON object and nothing else."
)


# env var names an Anthropic key might be stored under, in priority order
_KEY_ENV_NAMES = ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_KEY", "ANTHROPIC_AUTH_TOKEN")

_missing_key_warned = False


def _resolve_api_key() -> str | None:
    """Anthropic key from settings first, then any of the known env var names."""
    import os

    try:
        from app.core.config import get_settings

        key = getattr(get_settings(), "ANTHROPIC_API_KEY", None)
        if key:
            return key
    except Exception:  # noqa: BLE001
        pass
    for name in _KEY_ENV_NAMES:
        if os.environ.get(name):
            return os.environ[name]
    return None


def llm_available() -> bool:
    return _resolve_api_key() is not None


def _client() -> Any:
    """Lazy anthropic client so a missing key never breaks import/startup."""
    import anthropic

    key = _resolve_api_key()
    return anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()


def _ask_json(prompt: str, fallback: dict) -> dict:
    """One Claude call; expect a single JSON object back; fall back on failure."""
    global _missing_key_warned
    if not llm_available():
        if not _missing_key_warned:
            logger.error(
                "brand_transformation: no Anthropic API key configured (checked settings "
                "+ %s) — every agent will return TEMPLATED FALLBACK output, not AI. "
                "Set ANTHROPIC_API_KEY to enable the agents.",
                ", ".join(_KEY_ENV_NAMES),
            )
            _missing_key_warned = True
        return fallback
    try:
        msg = _client().messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text
        start, end = text.find("{"), text.rfind("}") + 1
        data = json.loads(text[start:end])
        if not isinstance(data, dict):
            raise ValueError("not an object")
        return data
    except Exception as e:  # noqa: BLE001
        logger.warning("brand_transformation: LLM call failed, using fallback: %s", str(e)[:200])
        return fallback


def _draft_then_refine(prompt: str, fallback: dict, refine_focus: str) -> dict:
    """Draft -> adversarial critique -> refined final. Two Claude calls.

    The refine pass must return the SAME keys as the draft (nothing added or
    removed except the two provenance keys), so downstream persistence is
    unaffected by the extra round-trip.
    """
    draft = _ask_json(prompt, fallback)
    used_fallback = draft is fallback

    if not used_fallback:
        refine_prompt = f"""You produced this DRAFT:

{json.dumps(draft, ensure_ascii=False, indent=2)[:8000]}

Now CRITIQUE it hard against the quality bar, then return the FINAL improved
version. {refine_focus}

Rules for the final JSON:
- Keep EXACTLY the same keys as the draft (same structure, same nesting).
- Replace every cliché or generic sentence with a specific, concrete one.
- Every recommendation must trace to a mechanism, a number, or a named
  precedent — if a claim can't be justified, cut it or make it defensible.
- Raise the prose: shorter sentences, concrete imagery, no hedging.
- Where the draft is vague, get sharper. Where it is safe and forgettable,
  find the more interesting angle that is still defensible.
- ADD two keys if not already present:
    "confidence": <int 0-100> — honest self-assessment of how rigorous and
       well-grounded this output is (low if you had thin input).
    "frameworks_applied": [<names of the frameworks / brand playbooks you
       actually used, e.g. "dunford_positioning", "Red Bull">]

Return ONLY the final JSON object."""
        refined = _ask_json(refine_prompt, draft)
    else:
        refined = draft

    refined.setdefault("confidence", 45 if used_fallback else 72)
    refined.setdefault("frameworks_applied", [])
    refined["_generated_by"] = "fallback" if used_fallback else "llm"
    return refined


def _profile_block(p: dict) -> str:
    return (
        f"BUSINESS PROFILE\n"
        f"- Industry: {p.get('industry', 'n/a')}\n"
        f"- Sells: {p.get('what_they_sell', 'n/a')}\n"
        f"- Current positioning: {p.get('current_positioning') or 'undefined'}\n"
        f"- Competitors: {', '.join(p.get('known_competitors') or []) or 'n/a'}\n"
        f"- Revenue model: {p.get('revenue_model') or 'n/a'}\n"
        f"- Target customer: {p.get('target_customer') or 'n/a'}\n"
        f"- Price point: {p.get('price_point') or 'n/a'}\n"
        f"- Notes: {p.get('notes') or 'none'}\n"
    )


def _int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


# fields on DiagnosisIn beyond the base profile that make the call more grounded
_EVIDENCE_FIELDS = (
    "time_in_market", "monthly_revenue", "gross_margin_pct", "repeat_purchase_rate",
    "pricing", "channels", "differentiation_claims", "customer_quotes", "recent_marketing",
)


def _evidence_snapshot(p: dict) -> dict:
    return {k: p[k] for k in _EVIDENCE_FIELDS if p.get(k)}


def _evidence_quality(snap: dict) -> str:
    n = len(snap)
    return "solid" if n >= 6 else "partial" if n >= 3 else "thin"


def _evidence_block(p: dict) -> str:
    snap = _evidence_snapshot(p)
    if not snap:
        return "EVIDENCE: none supplied beyond the profile above — flag every conclusion that rests on assumption."
    lines = ["EVIDENCE SUPPLIED:"]
    for k, v in snap.items():
        v = ", ".join(map(str, v)) if isinstance(v, list) else v
        lines.append(f"- {k}: {v}")
    lines.append(f"(evidence quality: {_evidence_quality(snap)})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------


class _BaseAgent:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _save(self, row):
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row


class DiagnosisAgent(_BaseAgent):
    """Etapa 0 — a multi-lens diagnosis, not a one-liner verdict.

    Produces: headline score + commoditization level, then five lenses
    (commoditization by dimension, per-axis referent gap, closest precedent
    from the 12 origin playbooks, moat assessment, quick-wins vs structural
    moves) and honest kill criteria for when 'become a referent' is the wrong
    goal. Confidence is floored by how much real evidence was supplied.
    """

    async def run(self, business_id: uuid.UUID, profile: dict, extra: str | None = None) -> BrandDiagnosis:
        snap = _evidence_snapshot(profile)
        eq = _evidence_quality(snap)
        prompt = f"""{_profile_block(profile)}

{_evidence_block(profile)}

REFERENCE — how iconic brands beat commoditization (note the REAL engine, not
the surface product):
{K.origins_digest()}

SCORECARD RUBRIC — score each axis 0-5 strictly against these definitions:
{K.scorecard_rubric_digest()}

MOAT TYPES a referent brand defends:
{K.moat_types_digest()}

FRAMEWORKS:
{K.frameworks_digest(['dunford_positioning', 'category_design_playbigger', 'eeat_authority', 'blue_ocean_errc'])}

TASK: Diagnose why this business is mediocre / undifferentiated today. Be blunt
and specific. Score its "Referent Potential" (0-100 = how realistically it could
become a category reference in 12-18 months given honest constraints). Where the
evidence is {eq}, say which conclusions are assumptions. {extra or ''}

Return JSON:
{{
  "referent_potential_score": <int 0-100>,
  "commoditization_level": "low|medium|high|severe",
  "commoditization_analysis": {{
     "price": {{"score_0_5": <int>, "evidence": "the tell"}},
     "product": {{"score_0_5": <int>, "evidence": "..."}},
     "distribution": {{"score_0_5": <int>, "evidence": "..."}},
     "brand": {{"score_0_5": <int>, "evidence": "..."}}
  }},
  "symptoms": ["specific, observable symptom", ...],
  "root_causes": ["the cause one level deeper than the symptom", ...],
  "scorecard": {{"positioning": <0-5>, "brand_identity": <0-5>, "offer": <0-5>, "fomo_desire": <0-5>, "distribution": <0-5>, "authority": <0-5>}},
  "referent_gap": {{
     "positioning": {{"current": "...", "referent_looks_like": "...", "the_gap": "the specific move to close it"}},
     "brand_identity": {{...}}, "offer": {{...}}, "fomo_desire": {{...}}, "distribution": {{...}}, "authority": {{...}}
  }},
  "closest_precedent": {{"brand": "one of the 12 origin playbooks", "why_it_fits": "...", "what_to_copy": "the transferable mechanism", "what_not_to_copy": "the part that doesn't transfer"}},
  "moat_assessment": {{"has_moat_today": true|false, "buildable_moat_type": "from the moat list", "how": "the concrete path to it", "why_it_holds": "..."}},
  "highest_leverage_moves": ["ranked, each stating the MECHANISM not just the goal", "", ""],
  "quick_wins": ["<=30-day move that shifts perception or conversion now", ...],
  "structural_moves": ["6-12 month move that builds the moat / category", ...],
  "kill_criteria": ["a signal that would mean 'don't chase referent status here — pivot or sell instead'", ...],
  "second_order_risk": "what breaks if they scale the current model unchanged",
  "evidence_quality": "{eq}",
  "summary": "4-5 sentences a founder would want to read — direct, quotable, no hedging"
}}"""
        d = _draft_then_refine(prompt, {
            "referent_potential_score": 40,
            "commoditization_level": "high",
            "commoditization_analysis": {
                "price": {"score_0_5": 4, "evidence": "Sells at market price; discounts to close"},
                "product": {"score_0_5": 3, "evidence": "Quality parity with competitors, no signature element"},
                "distribution": {"score_0_5": 3, "evidence": "Same channels as everyone, no owned audience"},
                "brand": {"score_0_5": 4, "evidence": "Interchangeable name/story; no point of view"},
            },
            "symptoms": ["Positioning indistinguishable from competitors", "Wins deals on price, not preference"],
            "root_causes": ["No stated point of view", "No category the business owns"],
            "scorecard": {"positioning": 1, "brand_identity": 1, "offer": 2, "fomo_desire": 1, "distribution": 2, "authority": 1},
            "referent_gap": {},
            "closest_precedent": {"brand": "Red Bull", "why_it_fits": "Commoditized liquid, won on identity + owned culture", "what_to_copy": "Fund content/culture that carries the identity; charge for the badge", "what_not_to_copy": "Extreme-sports theme — pick this business's own subculture"},
            "moat_assessment": {"has_moat_today": False, "buildable_moat_type": "brand", "how": "Own a category + point of view until customers refuse substitutes", "why_it_holds": "Meaning is expensive to copy once it's established"},
            "highest_leverage_moves": ["Name and own a category (frame the value so competitors look generic)", "Commit to one archetype (make voice + story consistent everywhere)", "Build a grand-slam offer (tilt the value equation so price stops being the axis)"],
            "quick_wins": ["Rewrite the homepage around one point of view", "Add real social proof above the fold", "Kill the blanket discount"],
            "structural_moves": ["Launch a category-defining content asset", "Introduce a membership / recurring tier", "Build one growth loop"],
            "kill_criteria": ["Margin can't support any brand investment for 12 months", "Founder unwilling to take a polarising position", "Category is a true commodity with switching cost near zero and no premium segment"],
            "second_order_risk": "Scaling ad spend on an undifferentiated offer just raises CAC until margin disappears.",
            "evidence_quality": eq,
            "summary": "Undifferentiated player in a crowded field, competing on price. Needs positioning and identity before growth spend, or it buys unprofitable volume.",
        }, "Make the summary sharp enough to quote back to the founder. Every "
           "leverage move and referent_gap entry must name the mechanism. The "
           "closest_precedent must explain what transfers and what does not.")

        # confidence can't exceed what the evidence supports
        cap = {"thin": 55, "partial": 75, "solid": 92}[eq]
        conf = min(_int(d.get("confidence"), 55), cap)

        return await self._save(BrandDiagnosis(
            business_id=business_id,
            industry=profile.get("industry", "n/a"),
            current_positioning=profile.get("current_positioning"),
            known_competitors=profile.get("known_competitors"),
            revenue_model=profile.get("revenue_model"),
            notes=profile.get("notes"),
            evidence_snapshot=snap or None,
            referent_potential_score=_int(d.get("referent_potential_score")),
            commoditization_level=d.get("commoditization_level", "unknown"),
            symptoms=d.get("symptoms"),
            root_causes=d.get("root_causes"),
            highest_leverage_moves=d.get("highest_leverage_moves"),
            scorecard=d.get("scorecard"),
            summary=d.get("summary"),
            commoditization_analysis=d.get("commoditization_analysis"),
            referent_gap=d.get("referent_gap"),
            closest_precedent=d.get("closest_precedent"),
            moat_assessment=d.get("moat_assessment"),
            quick_wins=d.get("quick_wins"),
            structural_moves=d.get("structural_moves"),
            kill_criteria=d.get("kill_criteria"),
            second_order_risk=d.get("second_order_risk"),
            evidence_quality=d.get("evidence_quality") or eq,
            confidence=conf,
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))

    async def latest(self, business_id: uuid.UUID) -> BrandDiagnosis | None:
        r = await self.db.execute(
            select(BrandDiagnosis).where(BrandDiagnosis.business_id == business_id)
            .order_by(desc(BrandDiagnosis.created_at)).limit(1)
        )
        return r.scalar_one_or_none()

    async def history(self, business_id: uuid.UUID, limit: int = 12) -> list[BrandDiagnosis]:
        r = await self.db.execute(
            select(BrandDiagnosis).where(BrandDiagnosis.business_id == business_id)
            .order_by(desc(BrandDiagnosis.created_at)).limit(limit)
        )
        return list(r.scalars().all())


_DIAGNOSIS_CARRY = (
    "referent_gap", "closest_precedent", "moat_assessment", "root_causes",
    "commoditization_analysis", "highest_leverage_moves", "referent_potential_score",
)


def _diagnosis_digest(context: dict | None) -> str:
    """Pull just the parts of a prior diagnosis that positioning needs."""
    if not context:
        return "PRIOR DIAGNOSIS: none — infer from the profile, flag assumptions."
    keep = {k: context[k] for k in _DIAGNOSIS_CARRY if context.get(k) is not None}
    keep = keep or context
    return "PRIOR DIAGNOSIS (key parts):\n" + json.dumps(keep, ensure_ascii=False)[:2400]


class PositioningAgent(_BaseAgent):
    """Etapa 1 — a positioning + category-design workshop.

    Runs the enemy test, the POV test, and the category-king test explicitly
    so the output can't be a mushy enemy, a POV nobody disagrees with, or a
    "new category" this business can't lead. Produces the full messaging kit:
    positioning statement, one-liner, 30s elevator, 3 pillars with proof, and
    a FROM->TO reframe — plus the migration risk (who repositioning loses).
    """

    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> PositioningStatement:
        prompt = f"""{_profile_block(profile)}

{_diagnosis_digest(context)}

FRAMEWORKS:
{K.frameworks_digest(['dunford_positioning', 'category_design_playbigger', 'blue_ocean_errc'])}

{K.positioning_tests_digest()}

REFERENCE PLAYBOOKS:
{K.origins_digest()}

TASK: Run a full positioning + category-design pass. Work the tests above, don't
just assert. The enemy must pass the ENEMY TEST. The POV must score >=1 on every
POV TEST axis. Only recommend "design a new category" if the CATEGORY-KING TEST
mostly passes — otherwise frame within an existing category. {extra or ''}

Return JSON:
{{
  "alternatives_matrix": [
    {{"alternative": "what the customer does instead today", "why_tolerated": "...", "what_customer_keeps": "...", "what_they_lose": "..."}}
  ],
  "attribute_value_proof": [
    {{"attribute": "true of this business, alternatives can't claim it", "value": "in the customer's words", "proof_point": "what makes it believable — a number, a demo, a track record"}}
  ],
  "best_fit_customers": ["the narrow segment that cares MOST about that value", ...],
  "enemy_analysis": {{
    "enemy": "the status-quo behaviour or belief this brand fights",
    "test_results": [{{"check": "<the ENEMY TEST check>", "pass": true|false, "note": "..."}}],
    "passes": true|false
  }},
  "point_of_view": "2-3 sentences — makes some nod hard, others bristle",
  "pov_validation": {{
    "who_nods": "...", "who_bristles": "...", "cost_to_hold_it": "what the brand gives up by saying this",
    "evidence": "why this brand can defend it",
    "scores": {{"polarising": 0-2, "defensible": 0-2, "actionable": 0-2, "ownable": 0-2, "durable": 0-2}}
  }},
  "category_decision": {{
    "recommendation": "play_in_existing | design_new",
    "market_category": "the existing category to frame within",
    "new_category_name": "only if design_new — a name customers can repeat (else null)",
    "king_test": {{"can_be_number_one": "...", "market_feels_the_pain": "...", "frame_is_teachable": "...", "economics_concentrate": "...", "not_just_a_feature": "..."}},
    "rationale": "why this call",
    "name_candidates": ["Category name — the idea behind it", ...]
  }},
  "reframe": {{"from": "the frame customers use today", "to": "the frame this positioning installs"}},
  "positioning_statement": "For [customer] who [need], [brand] is the [category] that [unique value], unlike [alternative], because [reason].",
  "one_liner": "<12 words, a customer repeats it verbatim",
  "elevator_pitch": "~30 seconds spoken, first person, no jargon",
  "messaging_pillars": [{{"pillar": "one of 3 supporting messages", "proof": "the evidence behind it"}}],
  "migration_risks": {{"who_we_lose": "the customers this repositioning pushes away", "acceptable": true|false, "mitigation": "how to soften the transition"}},
  "alternative_angles": [
    {{"angle": "a genuinely different positioning bet", "enemy": "...", "when_to_pick": "the condition under which this beats the primary"}},
    {{"angle": "a second, different bet", "enemy": "...", "when_to_pick": "..."}}
  ]
}}"""
        d = _draft_then_refine(prompt, {
            "alternatives_matrix": [
                {"alternative": "Do nothing / live with the problem", "why_tolerated": "The pain is chronic, not acute", "what_customer_keeps": "Zero switching effort", "what_they_lose": "Compounding time/quality cost"},
                {"alternative": "Incumbent competitors", "why_tolerated": "Familiar, 'nobody got fired for it'", "what_customer_keeps": "Safety", "what_they_lose": "Any real improvement"},
            ],
            "attribute_value_proof": [{"attribute": "TBD — needs founder input", "value": "TBD", "proof_point": "TBD"}],
            "best_fit_customers": ["TBD — narrow segment"],
            "enemy_analysis": {"enemy": "The commoditized status quo everyone has stopped questioning", "test_results": [], "passes": False},
            "point_of_view": "The default way this gets done quietly wastes the customer's money, and the whole industry pretends that's normal.",
            "pov_validation": {"who_nods": "customers who've been burned", "who_bristles": "incumbents", "cost_to_hold_it": "alienates the price-only buyer", "evidence": "pending founder input", "scores": {"polarising": 1, "defensible": 1, "actionable": 1, "ownable": 1, "durable": 1}},
            "category_decision": {"recommendation": "play_in_existing", "market_category": profile.get("industry", "n/a"), "new_category_name": None, "king_test": {}, "rationale": "Not enough evidence yet to lead a new category; sharpen the position first.", "name_candidates": []},
            "reframe": {"from": f"{profile.get('what_they_sell', 'this')} is a commodity you shop on price", "to": f"{profile.get('what_they_sell', 'this')} is a choice that signals something"},
            "positioning_statement": "Positioning statement pending founder input.",
            "one_liner": "The better way to " + str(profile.get("what_they_sell", "do this")),
            "elevator_pitch": "Pending founder input.",
            "messaging_pillars": [],
            "migration_risks": {"who_we_lose": "pure price shoppers", "acceptable": True, "mitigation": "Keep an entry tier while the premium position builds"},
            "alternative_angles": [],
        }, "The enemy and POV are the whole game — make them specific and a little "
           "provocative, and show the test results. category_decision must be "
           "justified by the king_test, not asserted. alternative_angles are real "
           "strategic forks, not rewordings.")

        cat = d.get("category_decision") or {}
        return await self._save(PositioningStatement(
            business_id=business_id,
            competitive_alternatives=[m.get("alternative") for m in (d.get("alternatives_matrix") or []) if isinstance(m, dict)] or None,
            unique_attributes=[a.get("attribute") for a in (d.get("attribute_value_proof") or []) if isinstance(a, dict)] or None,
            value_themes=[a.get("value") for a in (d.get("attribute_value_proof") or []) if isinstance(a, dict)] or None,
            best_fit_customers=d.get("best_fit_customers"),
            market_category=cat.get("market_category") or d.get("market_category"),
            new_category_name=cat.get("new_category_name") or d.get("new_category_name"),
            point_of_view=d.get("point_of_view"),
            the_enemy=(d.get("enemy_analysis") or {}).get("enemy") or d.get("the_enemy"),
            positioning_statement=d.get("positioning_statement"),
            one_liner=d.get("one_liner"),
            elevator_pitch=d.get("elevator_pitch"),
            alternatives_matrix=d.get("alternatives_matrix"),
            attribute_value_proof=d.get("attribute_value_proof"),
            enemy_analysis=d.get("enemy_analysis"),
            pov_validation=d.get("pov_validation"),
            category_decision=d.get("category_decision"),
            reframe=d.get("reframe"),
            messaging_pillars=d.get("messaging_pillars"),
            migration_risks=d.get("migration_risks"),
            alternative_angles=d.get("alternative_angles"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


_POSITIONING_CARRY = (
    "positioning_statement", "one_liner", "point_of_view", "enemy_analysis",
    "the_enemy", "reframe", "category_decision", "messaging_pillars",
    "best_fit_customers", "migration_risks",
)


def _positioning_digest(context: dict | None) -> str:
    if not context:
        return "PRIOR POSITIONING: none — infer from the profile, flag assumptions."
    keep = {k: context[k] for k in _POSITIONING_CARRY if context.get(k) is not None}
    return "PRIOR POSITIONING (key parts):\n" + json.dumps(keep or context, ensure_ascii=False)[:2600]


_STAGE_HIGHLIGHTS = {
    "diagnosis": ("referent_potential_score", "highest_leverage_moves", "moat_assessment", "closest_precedent", "kill_criteria"),
    "positioning": ("positioning_statement", "one_liner", "point_of_view", "the_enemy", "category_decision", "messaging_pillars", "best_fit_customers", "reframe"),
    "brand_identity": ("primary_archetype", "tagline", "story_spine", "verbal_identity", "identity_consistency_rules"),
    "business_model": ("applied_patterns", "grand_slam_offer", "pricing_architecture", "unit_economics_targets", "value_equation"),
    "fomo_engine": ("mechanisms", "launch_ritual", "cadence", "content_hooks", "activation_sequence"),
    "gtm": ("primary_growth_loop", "lightning_strike", "channel_plan", "plan_90_days", "north_star_metric"),
    "restructuring": ("kill", "keep", "scale", "core_processes", "promise_kpis"),
}


def _stage_context_digest(context: dict | None, want: tuple[str, ...] | None = None) -> str:
    """Compact digest of prior-stage artifacts.

    Accepts either the orchestrator's {stage_key: artifact_dict} shape or a
    single artifact dict. `want` limits which stages to include.
    """
    if not context:
        return "PRIOR STAGES: none — infer from the profile, flag assumptions."
    stage_keys = set(_STAGE_HIGHLIGHTS)
    if not (set(context) & stage_keys):  # a single artifact dict, not stage-keyed
        return "PRIOR CONTEXT:\n" + json.dumps(context, ensure_ascii=False)[:2600]
    out = []
    for sk, art in context.items():
        if sk not in _STAGE_HIGHLIGHTS or not isinstance(art, dict):
            continue
        if want and sk not in want:
            continue
        picked = {k: art[k] for k in _STAGE_HIGHLIGHTS[sk] if art.get(k) is not None}
        if picked:
            out.append(f"[{sk}] " + json.dumps(picked, ensure_ascii=False)[:1500])
    return "PRIOR STAGES (highlights):\n" + "\n".join(out) if out else "PRIOR STAGES: present but empty."


class BrandIdentityAgent(_BaseAgent):
    """Etapa 2 — the full identity system, derived from the positioning.

    Shortlists archetypes and scores each on positioning-fit /
    differentiation-in-category / founder-authenticity before picking. Builds a
    real verbal identity (voice attributes with 'sounds like / not', a
    use/ban lexicon tied to the cliché blocklist, rhythm, humour), a naming
    decision against explicit criteria, a 4-beat story spine downstream agents
    reuse, an actionable visual brief with moodboard search terms, and 5
    identity non-negotiables that feed the brand_consistency_monitor.
    """

    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> BrandIdentity:
        prompt = f"""{_profile_block(profile)}

{_positioning_digest(context)}

FRAMEWORKS:
{K.frameworks_digest(['jung_brand_archetypes', 'brand_voice_system'])}

NAMING CRITERIA (score candidates 0-2 on each):
{K.naming_criteria_digest()}

STORY SPINE (4 beats — the problem beat IS the positioning's enemy):
{K.story_spine_digest()}

CLICHÉ BLOCKLIST (the lexicon 'ban' list must include these): {', '.join(K.CLICHE_BLOCKLIST)}

IDENTITY NON-NEGOTIABLES: {K.IDENTITY_NON_NEGOTIABLES_HINT}

TASK: Build the identity system. Pick ONE primary archetype, justified from the
positioning — not taste. A rename is usually NOT warranted; only recommend it
with a hard reason. The manifesto and tagline are judged on whether a real brand
would actually ship them. {extra or ''}

Return JSON:
{{
  "archetype_analysis": {{
    "shortlist": [{{"archetype": "one of the 12", "positioning_fit": 0-2, "differentiation_in_category": 0-2, "founder_authenticity": 0-2, "note": "..."}}],
    "primary": "the pick", "secondary": "supporting archetype or null",
    "blend": "e.g. '70% Outlaw / 30% Sage' and what that means in practice",
    "rationale": "why this follows from the positioning"
  }},
  "story_spine": {{"world": "...", "problem": "the enemy, in story form", "insight": "what the founder saw", "mission": "what the brand makes true"}},
  "manifesto": "90-150 words in the brand voice, with rhythm — read it aloud first",
  "tagline": "<=6 words, no colon, no cliché",
  "taglines_alt": ["3 alternates, each a different angle", "", ""],
  "verbal_identity": {{
    "attributes": [{{"adj": "...", "sounds_like": "a sentence that IS this", "not": "the nearby thing to avoid"}}],
    "lexicon": {{"use": ["signature words"], "ban": ["words that break the voice — include the cliché blocklist"]}},
    "rhythm": "sentence-length pattern, punctuation habits",
    "humor": "how much, what kind, where it's off-limits",
    "first_line_rule": "what every piece of copy must do in sentence one"
  }},
  "sample_rewrites": [
    {{"context": "homepage hero", "text": "..."}},
    {{"context": "welcome message", "text": "..."}},
    {{"context": "sold-out notice", "text": "..."}},
    {{"context": "price objection reply", "text": "..."}},
    {{"context": "shipping delay apology", "text": "..."}}
  ],
  "naming": {{
    "decision": "keep | rename | add_descriptor",
    "rationale": "one sentence",
    "candidates": [{{"name": "...", "idea": "...", "scores": {{"distinctive": 0-2, "memorable": 0-2, "sayable": 0-2, "meaning_carrying": 0-2, "room_to_grow": 0-2, "legally_plausible": 0-2}}}}],
    "name_test": "the one question that decides it"
  }},
  "visual_brief": {{
    "mood": "3-4 adjectives",
    "palette_direction": "the role of each colour, not hex — e.g. 'one loud accent for CTAs, everything else near-black + paper'",
    "typography": "a pairing + why it fits the archetype",
    "imagery_do": ["..."], "imagery_dont": ["..."],
    "logo_direction": "wordmark / symbol / etc + why",
    "moodboard_search_terms": ["5 phrases to paste into an image search", "", "", "", ""],
    "one_thing_to_avoid": "the category default this brand must never look like"
  }},
  "brand_architecture": "master brand vs sub-brands + endorsement model + how future products get named",
  "identity_consistency_rules": ["5 non-negotiables a non-designer can check on any asset", "", "", "", ""],
  "alternative_angles": [
    {{"archetype": "a different defensible archetype", "what_changes": "how voice + manifesto + visuals shift", "when_to_pick": "..."}},
    {{"archetype": "...", "what_changes": "...", "when_to_pick": "..."}}
  ]
}}"""
        d = _draft_then_refine(prompt, {
            "archetype_analysis": {"shortlist": [], "primary": "Hero", "secondary": "Outlaw", "blend": "70% Hero / 30% Outlaw — earnest about the customer's goal, irreverent about the industry", "rationale": "Positioning frames the brand as the one that fights the status quo for the customer."},
            "story_spine": {"world": "Customers accept the category default.", "problem": "The default quietly costs them.", "insight": "It doesn't have to.", "mission": "Make the better way the obvious way."},
            "manifesto": "Manifesto pending positioning sign-off.",
            "tagline": "Do it properly.", "taglines_alt": [],
            "verbal_identity": {"attributes": [{"adj": "blunt", "sounds_like": "Here's the number. Here's what it means.", "not": "aggressive"}], "lexicon": {"use": [], "ban": list(K.CLICHE_BLOCKLIST)}, "rhythm": "short sentences, one idea each", "humor": "dry, never at the customer's expense", "first_line_rule": "name the enemy or the outcome — never warm up"},
            "sample_rewrites": [],
            "naming": {"decision": "keep", "rationale": "Existing name has equity; the gap is meaning, not letters.", "candidates": [], "name_test": "Would a customer repeat it correctly after hearing it once?"},
            "visual_brief": {"mood": "bold, high-contrast, plain", "palette_direction": "one loud accent for action, near-black + paper for everything else", "typography": "grotesk display + humanist body", "imagery_do": ["real people, unretouched"], "imagery_dont": ["stock handshakes", "gradients on everything"], "logo_direction": "wordmark — the name is the asset", "moodboard_search_terms": [], "one_thing_to_avoid": "looking like every other option in the category"},
            "brand_architecture": "Single master brand; no sub-brands until a second product line exists; future products take descriptive names under the master.",
            "identity_consistency_rules": [],
            "alternative_angles": [],
        }, "The manifesto, tagline and sample rewrites are judged on whether a real "
           "brand would ship them — kill anything that reads like a generator. The "
           "archetype pick must be defended by the shortlist scores.")

        aa = d.get("archetype_analysis") or {}
        vi = d.get("verbal_identity") or {}
        naming = d.get("naming") or {}
        return await self._save(BrandIdentity(
            business_id=business_id,
            primary_archetype=aa.get("primary") or d.get("primary_archetype"),
            secondary_archetype=aa.get("secondary") or d.get("secondary_archetype"),
            rename_recommended=(naming.get("decision") in ("rename", "add_descriptor")),
            name_candidates=[c.get("name") for c in (naming.get("candidates") or []) if isinstance(c, dict)] or d.get("name_candidates"),
            tagline=d.get("tagline"),
            manifesto=d.get("manifesto"),
            voice_attributes=[a.get("adj") for a in (vi.get("attributes") or []) if isinstance(a, dict)] or d.get("voice_attributes"),
            voice_do=[a.get("sounds_like") for a in (vi.get("attributes") or []) if isinstance(a, dict)] or d.get("voice_do"),
            voice_dont=(vi.get("lexicon") or {}).get("ban") or d.get("voice_dont"),
            sample_rewrites=d.get("sample_rewrites"),
            visual_brief=d.get("visual_brief"),
            brand_architecture=" | ".join(x for x in [d.get("brand_architecture"), aa.get("rationale"), naming.get("rationale")] if x),
            alternative_angles=d.get("alternative_angles"),
            archetype_analysis=d.get("archetype_analysis"),
            verbal_identity=d.get("verbal_identity"),
            naming=d.get("naming"),
            story_spine=d.get("story_spine"),
            taglines_alt=d.get("taglines_alt"),
            identity_consistency_rules=d.get("identity_consistency_rules"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class BusinessModelAgent(_BaseAgent):
    """Etapa 3 — business-model redesign as a costed decision, not a canvas fill.

    Diagnoses how the model earns today and where margin leaks, scores a
    shortlist of named patterns on 5 axes before applying 2-3, rewrites the
    canvas block-by-block with dependency notes, quantifies the Hormozi value
    equation, sets unit-economics targets with the assumption behind each, and
    gives a pricing-migration path so the change doesn't trigger a revolt.
    """

    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> BusinessModelRedesign:
        prompt = f"""{_profile_block(profile)}

{_evidence_block(profile)}

{_positioning_digest(context)}

FRAMEWORKS:
{K.frameworks_digest(['business_model_canvas', 'business_model_patterns', 'hormozi_value_equation', 'blue_ocean_errc'])}

SCORE EACH CANDIDATE PATTERN 0-2 ON THESE AXES:
{K.bm_pattern_axes_digest()}

PRICING PSYCHOLOGY TACTICS to draw from (name the ones you use):
{K.pricing_tactics_digest()}

UNIT ECONOMICS: {K.UNIT_ECONOMICS_TARGETS_HINT}

REFERENCE PLAYBOOKS (the real engine, not the surface product):
{K.origins_digest()}

TASK: Redesign the model so price stops being the axis of competition. Show the
work: diagnose the current economics, score patterns before picking, rewrite the
canvas with dependencies, quantify the value equation, set unit-economics targets.
The guarantee must carry real risk and you must state the worst-case abuse cost.
{extra or ''}

Return JSON:
{{
  "model_diagnosis": {{"how_it_earns_now": "...", "margin_leaks": ["..."], "every_sale_from_zero": true|false, "fragility": "the single biggest structural weakness"}},
  "pattern_evaluation": [
    {{"pattern": "named pattern", "scores": {{"positioning_fit": 0-2, "margin_impact": 0-2, "retention_impact": 0-2, "execution_difficulty": 0-2, "time_to_cash": 0-2}}, "verdict": "apply | later | reject", "how_it_transfers_here": "specific, not the precedent's product", "precedent": "brand"}}
  ],
  "applied_patterns": ["the 2-3 you chose, with the one-line reason"],
  "canvas": {{"customer_segments": [...], "value_propositions": [...], "channels": [...], "customer_relationships": [...], "revenue_streams": [...], "key_resources": [...], "key_activities": [...], "key_partners": [...], "cost_structure": [...]}},
  "canvas_changes": [{{"block": "...", "from": "today", "to": "redesigned", "why": "...", "forces_change_in": "the other block this drags with it"}}],
  "new_revenue_streams": [{{"stream": "...", "mechanism": "...", "rough_contribution": "small|medium|large", "time_to_first_dollar": "..."}}],
  "value_equation": {{
    "dream_outcome": "...",
    "perceived_likelihood": {{"current": "low|med|high", "levers_to_raise": ["proof, guarantee, case studies..."]}},
    "time_delay": {{"before": "...", "after": "..."}},
    "effort_and_sacrifice": {{"before": "...", "after": "..."}},
    "net_effect": "one sentence — which direction perceived value moves and why"
  }},
  "grand_slam_offer": {{"dream_outcome": "...", "core": "...", "bonuses": [{{"bonus": "...", "objection_it_removes": "..."}}], "guarantee": "specific, carries real risk", "worst_case_abuse_cost": "what it costs if abused, and why that's acceptable", "scarcity": "real", "urgency": "real deadline + real reason", "why_saying_no_feels_dumb": "..."}},
  "pricing_architecture": {{"tiers": [{{"name": "outcome-named", "price": "...", "for": "...", "the_trick": "why this tier exists", "expected_mix_pct": <int>}}], "anchor": "...", "psych_tactics": ["named tactic — why it works here"]}},
  "pricing_migration": {{"from": "current pricing", "to": "new", "how": "grandfather / phase-in / new-customers-only", "who_might_churn": "...", "message": "how it's communicated"}},
  "unit_economics_targets": {{"gross_margin_pct": {{"target": "...", "assumption": "..."}}, "cac_ceiling": {{"target": "...", "assumption": "..."}}, "cac_payback_months": {{"target": "...", "assumption": "..."}}, "ltv_cac": {{"target": "...", "assumption": "..."}}, "contribution_margin": {{"target": "...", "assumption": "..."}}}},
  "errc_grid": {{"eliminate": [...], "reduce": [...], "raise": [...], "create": [...]}},
  "rollout": {{"change_first": "lowest-risk move that proves the thesis", "validate_before_committing": ["..."], "sequence": ["step 1", "step 2", "..."]}},
  "risks": [{{"risk": "cannibalization | ops load | churn if done wrong | ...", "likelihood": "low|med|high", "mitigation": "..."}}],
  "rationale": "why this model beats the current one — in money terms",
  "alternative_angles": [{{"model": "a different structural bet", "when_to_pick": "..."}}, {{"model": "...", "when_to_pick": "..."}}]
}}"""
        d = _draft_then_refine(prompt, {
            "model_diagnosis": {"how_it_earns_now": "One-off transactional sales at market price", "margin_leaks": ["Discounting to close", "No recurring revenue"], "every_sale_from_zero": True, "fragility": "Revenue resets to zero every month; no compounding base"},
            "pattern_evaluation": [
                {"pattern": "membership_club", "scores": {"positioning_fit": 2, "margin_impact": 1, "retention_impact": 2, "execution_difficulty": 1, "time_to_cash": 1}, "verdict": "apply", "how_it_transfers_here": "Turn repeat buyers into a paid tier with earned perks tied to the brand's point of view", "precedent": "Amazon Prime"},
                {"pattern": "razor_and_blade", "scores": {"positioning_fit": 1, "margin_impact": 2, "retention_impact": 2, "execution_difficulty": 1, "time_to_cash": 1}, "verdict": "apply", "how_it_transfers_here": "Low-margin entry product, recurring consumable/service attached", "precedent": "Dollar Shave Club"},
            ],
            "applied_patterns": ["membership_club — recurring base", "razor_and_blade — attach recurring value"],
            "canvas": {}, "canvas_changes": [], "new_revenue_streams": [],
            "value_equation": {"dream_outcome": "The result the customer actually wants", "perceived_likelihood": {"current": "low", "levers_to_raise": ["guarantee", "case studies"]}, "time_delay": {"before": "weeks", "after": "days"}, "effort_and_sacrifice": {"before": "high", "after": "low"}, "net_effect": "Perceived value up: same outcome, less risk and wait."},
            "grand_slam_offer": {}, "pricing_architecture": {}, "pricing_migration": {},
            "unit_economics_targets": {}, "errc_grid": {}, "rollout": {}, "risks": [],
            "rationale": "Recurring revenue lifts LTV and makes CAC affordable; today every sale starts from zero.",
            "alternative_angles": [],
        }, "Show the pattern scores — an applied pattern with weak scores gets "
           "rejected. The value_equation must be concrete (before/after), and every "
           "unit-economics target must name its assumption. Guarantee needs a real "
           "worst-case number.")
        return await self._save(BusinessModelRedesign(
            business_id=business_id,
            canvas=d.get("canvas"),
            applied_patterns=d.get("applied_patterns"),
            new_revenue_streams=d.get("new_revenue_streams"),
            grand_slam_offer=d.get("grand_slam_offer"),
            pricing_architecture=d.get("pricing_architecture"),
            errc_grid=d.get("errc_grid"),
            rationale=d.get("rationale"),
            model_diagnosis=d.get("model_diagnosis"),
            pattern_evaluation=d.get("pattern_evaluation"),
            canvas_changes=d.get("canvas_changes"),
            value_equation=d.get("value_equation"),
            unit_economics_targets=d.get("unit_economics_targets"),
            pricing_migration=d.get("pricing_migration"),
            rollout=d.get("rollout"),
            risks=d.get("risks"),
            alternative_angles=d.get("alternative_angles"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class FOMOEngineAgent(_BaseAgent):
    """Etapa 4 — a desire engine that stays on the right side of the line.

    Scores all 7 levers on 5 axes (including ethical risk) before choosing,
    runs an explicit manipulation review ('would the customer nod or feel used
    if we explained this on a podcast?'), gives each mechanism a measurable
    anti-fake guardrail plus the honest alternative to fall back on, sequences
    activation by risk, and maps every mechanism to the concrete SellIA
    fomo-domain action that implements it.
    """

    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> FOMOPlaybook:
        prompt = f"""{_profile_block(profile)}

{_positioning_digest(context)}

FOMO / DESIRE LEVERS (mechanism · cases · anti-pattern):
{K.levers_digest()}

SCORE ALL 7 LEVERS 0-2 ON THESE AXES, then choose 4-6:
{K.fomo_lever_axes_digest()}

THE MANIPULATION LINE:
{K.MANIPULATION_LINE}

SELLIA FOMO-DOMAIN MAP (map each chosen mechanism to the concrete action):
{K.fomo_domain_map_digest()}

TASK: Design a desire engine tuned to THIS business, its supply reality, and its
archetype. Nothing theatrical — if the product can't support a lever, say so and
skip it. Each mechanism needs a MEASURABLE anti-fake guardrail (how you'd prove
it's real) and an honest_alternative (what to do instead if you can't make it
real this cycle). {extra or ''}

Return JSON:
{{
  "lever_selection": [
    {{"lever": "one of the 7", "scores": {{"business_fit": 0-2, "ethical_risk": 0-2, "operational_feasibility": 0-2, "brand_consistency": 0-2, "expected_impact": 0-2}}, "chosen": true|false, "note": "why chosen or skipped"}}
  ],
  "mechanisms": [
    {{"lever": "...", "why_it_fits": "...", "implementation": "concrete steps incl. one non-obvious detail", "trigger": "the psychological trigger it pulls", "kpi": "...", "measurement": "how it's tracked", "anti_fake_guardrail": "measurable — how you'd prove it's real", "honest_alternative": "the fallback if it can't be real this cycle", "precedent": "brand that ran this well"}}
  ],
  "ethics_review": {{
    "the_line_for_this_brand": "where desire-building would become manipulation here",
    "never_do": ["specific practices this brand rules out"],
    "shown_from_inside_test": "would the customer nod or feel used if we explained the mechanism publicly — and why"
  }},
  "activation_sequence": {{"first": "the lowest-risk mechanism to turn on and why", "gating_conditions": ["what must be true before the next one"], "ramp_90d": ["week 1-2 ...", "week 3-6 ...", "week 7-12 ..."]}},
  "launch_ritual": {{"name": "a name the audience would actually use", "sequence": [...], "the_hook": "the single reason people show up", "payoff": "what participants get that others don't", "what_makes_it_repeatable": "..."}},
  "cadence": "specific — 'first Tuesday each month, 11:00'",
  "content_hooks": [{{"mechanism": "...", "copy_angle": "the exact line/angle to use — reusable by the GTM copy"}}],
  "measurement": {{"leading": ["waitlist growth rate, drop sellout time, ..."], "lagging": ["repeat rate, price realised, referral rate"]}},
  "integration_notes": [{{"mechanism": "...", "sellia_domain_action": "the concrete endpoint/campaign to create, from the domain map"}}],
  "risk_matrix": [{{"mechanism": "...", "backfire_mode": "...", "early_warning": "the metric that flips first", "kill_switch": "how to stop it fast"}}],
  "risk_notes": "the one sentence a founder must remember about running this",
  "alternative_angles": [
    {{"angle": "a different mechanism mix for a different risk appetite", "when_to_pick": "..."}},
    {{"angle": "...", "when_to_pick": "..."}}
  ]
}}"""
        d = _draft_then_refine(prompt, {
            "lever_selection": [],
            "mechanisms": [
                {"lever": "social_proof_velocity", "why_it_fits": "Trust gap in the category", "implementation": "Show verified recent-buyer count + the specific item, updated hourly", "trigger": "informational social influence", "kpi": "PDP->cart conversion", "measurement": "cohort A/B on the widget", "anti_fake_guardrail": "Numbers query straight from orders; never round up; link to a public methodology note", "honest_alternative": "Show total lifetime customers instead of 'today'", "precedent": "Booking.com"},
                {"lever": "anticipation_and_ritual", "why_it_fits": "Customers have nothing to look forward to", "implementation": "Monthly themed release teased 7 days out, one detail revealed per day", "trigger": "anticipation / dopamine gap", "kpi": "launch-day revenue vs baseline day", "measurement": "revenue delta on drop day", "anti_fake_guardrail": "Ship on the promised date every time", "honest_alternative": "A monthly note with no product if there's nothing ready", "precedent": "Glossier"},
            ],
            "ethics_review": {"the_line_for_this_brand": "Any scarcity a customer could disprove; any pressure on a first-time visitor mid-crisis", "never_do": ["Fake countdown timers", "Invented 'X people viewing'", "Manufactured stock warnings"], "shown_from_inside_test": "A customer seeing the real order feed behind the counter would nod — it's true."},
            "activation_sequence": {"first": "Social proof — no supply risk", "gating_conditions": ["Inventory reliable before running the ritual"], "ramp_90d": ["w1-2: social proof live", "w3-6: first drop", "w7-12: members tier"]},
            "launch_ritual": {"name": "The Drop", "sequence": ["tease -7d", "daily reveal", "open", "sellout recap + waitlist"], "the_hook": "it sells out and doesn't come back", "payoff": "members get 24h early access", "what_makes_it_repeatable": "a fixed date + a fresh theme each cycle"},
            "cadence": "monthly",
            "content_hooks": [], "measurement": {"leading": ["waitlist growth", "sellout time"], "lagging": ["repeat rate", "price realised"]},
            "integration_notes": [
                {"mechanism": "social_proof_velocity", "sellia_domain_action": "fomo_intelligence POST /generate-social-proof + fomo GET /social-proof widget"},
                {"mechanism": "anticipation_and_ritual", "sellia_domain_action": "fomo POST /campaigns type=drop then scheduled /activate"},
            ],
            "risk_matrix": [{"mechanism": "anticipation_and_ritual", "backfire_mode": "missed drop date kills trust", "early_warning": "prep milestones slipping", "kill_switch": "announce a skip early, don't fake it"}],
            "risk_notes": "Run few, real deadlines — permanent 'ending soon' trains customers to ignore every one.",
            "alternative_angles": [],
        }, "Reject any mechanism the product can't actually support. Every guardrail "
           "must be measurable ('numbers query from orders'), not 'be honest'. The "
           "ethics_review must name specific practices this brand rules out.")
        return await self._save(FOMOPlaybook(
            business_id=business_id,
            mechanisms=d.get("mechanisms"),
            launch_ritual=d.get("launch_ritual"),
            cadence=d.get("cadence"),
            risk_notes=d.get("risk_notes"),
            alternative_angles=d.get("alternative_angles"),
            lever_selection=d.get("lever_selection"),
            ethics_review=d.get("ethics_review"),
            activation_sequence=d.get("activation_sequence"),
            content_hooks=d.get("content_hooks"),
            measurement=d.get("measurement"),
            integration_notes=d.get("integration_notes"),
            risk_matrix=d.get("risk_matrix"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class GoToMarketAgent(_BaseAgent):
    """Etapa 5 — a 90-day GTM built around ONE loop, not a channel wish-list.

    Scores loop types on 5 axes before committing, quantifies the chosen
    loop (the variable it turns on, the metric that says it's turning, target
    cycle time), gives every channel a hypothesis + effort estimate + a kill
    signal, builds a content engine off the brand's story spine with a
    repurposing chain, and names explicit anti-goals for the 90 days.
    """

    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> GTMPlan:
        prompt = f"""{_profile_block(profile)}

{_stage_context_digest(context, want=("positioning", "brand_identity", "business_model", "fomo_engine"))}

FRAMEWORKS:
{K.frameworks_digest(['growth_loops', 'category_design_playbigger', 'hormozi_value_equation'])}

GROWTH LOOP TYPES:
{K.gtm_loop_types_digest()}

SCORE EACH LOOP TYPE 0-2 ON THESE AXES, then pick ONE primary (+ optional secondary):
{K.growth_loop_axes_digest()}

CHANNEL ROLES: {', '.join(K.CHANNEL_ROLES)}

TASK: Build a 90-day GTM that concentrates force. Pick ONE primary growth loop
the model can actually sustain — show the scores and why the others lose. Give
each channel a hypothesis, an effort estimate, and a kill signal so this is a
plan, not a wish list. Build the content engine off the brand's story spine.
{extra or ''}

Return JSON:
{{
  "loop_evaluation": [
    {{"loop": "content|viral|paid|ugc|sales_led|community", "scores": {{"model_fit": 0-2, "margin_supports_it": 0-2, "time_to_compound": 0-2, "defensibility": 0-2, "team_can_run_it": 0-2}}, "verdict": "primary | secondary | reject", "note": "..."}}
  ],
  "primary_growth_loop": {{
    "type": "the pick",
    "steps": ["input -> ... -> output that feeds the next input"],
    "the_variable_it_turns": "the one input the loop compounds",
    "turning_metric": "the single number that says the loop is working",
    "cycle_time": "how long one turn takes",
    "reinvestment": "what output feeds back into input",
    "why_not_the_others": "one line per rejected loop"
  }},
  "channel_plan": [
    {{"channel": "...", "role": "one of the channel roles", "hypothesis": "why this channel reaches the best-fit customer", "first_action": "concrete, this week", "effort": "rough hours/$ per week", "leading_signal": "what tells you early it's working", "kill_signal": "result after N weeks that means stop"}}
  ],
  "lightning_strike": {{"the_one_moment": "the single thing the launch is built around", "carrying_asset": "the piece that does the work", "pre_launch": [{{"task": "...", "owner": "role"}}], "launch_week": [{{"day": "...", "move": "..."}}], "post_launch": ["..."], "success_number": "the metric + threshold that defines a win"}},
  "content_engine": {{
    "pillars": [{{"pillar": "from the messaging pillars / story spine", "angle": "the POV, not the topic", "formats": ["..."]}}],
    "cadence": "how often, per format",
    "repurposing_chain": "1 anchor piece -> N derivatives (name them)",
    "owner": "who makes it"
  }},
  "funnel": [{{"stage": "awareness|consideration|conversion|retention", "the_job": "what must happen here", "asset": "the thing that does it", "metric": "...", "top_dropoff_risk": "..."}}],
  "plan_90_days": [{{"milestone": "...", "weeks": "1-2", "focus": "...", "owner": "role", "success_metric": "...", "depends_on": "prior milestone or null"}}],
  "week_1_actions": ["3 concrete things to do in the first 7 days", "", ""],
  "budget_shape": {{"allocation": {{"content": "%", "channels": "%", "tools": "%"}}, "constraint": "the binding limit — cash or time"}},
  "north_star_metric": "the one metric the whole team watches for 90 days",
  "anti_goals": ["what NOT to do in 90 days — spreading thin, vanity metrics, premature paid, ..."],
  "alternative_angles": [{{"angle": "a different GTM bet (e.g. sales-led instead of content)", "when_to_pick": "..."}}, {{"angle": "...", "when_to_pick": "..."}}]
}}"""
        d = _draft_then_refine(prompt, {
            "loop_evaluation": [],
            "primary_growth_loop": {"type": "content", "steps": ["publish POV content", "earns search + shares", "converts to trial", "customers produce case studies that feed content"], "the_variable_it_turns": "indexable POV assets", "turning_metric": "organic sessions -> trial rate", "cycle_time": "~6 weeks per asset to rank", "reinvestment": "revenue funds more production", "why_not_the_others": "viral: no in-product share reason; paid: margin not ready; sales-led: ACV too low"},
            "channel_plan": [], "lightning_strike": {}, "content_engine": {}, "funnel": [],
            "plan_90_days": [], "week_1_actions": ["Publish the POV piece the positioning implies", "Pin it everywhere the brand has presence", "DM 10 best-fit customers for reactions"],
            "budget_shape": {"allocation": {"content": "60%", "channels": "25%", "tools": "15%"}, "constraint": "founder time"},
            "north_star_metric": "weekly best-fit trials started",
            "anti_goals": ["Run paid before the offer converts organically", "Post on 6 platforms at once", "Chase follower count"],
            "alternative_angles": [],
        }, "The loop choice must show scores and beat the alternatives on them. "
           "Every channel needs an effort estimate and a kill signal. The content "
           "engine must derive from the brand's story spine, not generic topics.")
        return await self._save(GTMPlan(
            business_id=business_id,
            primary_growth_loop=d.get("primary_growth_loop"),
            channels=d.get("channel_plan") or d.get("channels"),
            lightning_strike=d.get("lightning_strike"),
            funnel=d.get("funnel"),
            content_pillars=(d.get("content_engine") or {}).get("pillars") or d.get("content_pillars"),
            plan_90_days=d.get("plan_90_days"),
            loop_evaluation=d.get("loop_evaluation"),
            channel_plan=d.get("channel_plan"),
            content_engine=d.get("content_engine"),
            week_1_actions=d.get("week_1_actions"),
            budget_shape=d.get("budget_shape"),
            anti_goals=d.get("anti_goals"),
            north_star_metric=d.get("north_star_metric"),
            alternative_angles=d.get("alternative_angles"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class RestructuringAgent(_BaseAgent):
    """Etapa 6 — turn the strategy into an operating system.

    Every kill carries its sunk-cost rebuttal and names who pushes back.
    Decision rights are assigned one-owner-per-decision (no committees).
    Core processes each protect a named brand promise and declare their
    failure mode. Unit-economics targets from Etapa 3 become a gate with an
    explicit 'pause growth spend' trigger. The 90-day operating plan is
    sequenced with dependencies.
    """

    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> RestructuringPlan:
        prompt = f"""{_profile_block(profile)}

{_stage_context_digest(context)}

DECISION RIGHTS: {K.DECISION_RIGHTS_MODEL}
BUILD / BUY / BORROW: {K.BUILD_BUY_BORROW}
OPERATING RHYTHM (adapt, don't just copy):
{K.operating_rhythm_digest()}
PROMISE KPIs: {K.PROMISE_KPI_HINT}

TASK: Turn the strategy into operating reality. The kill list is the point —
each item needs the sunk-cost rebuttal or it won't survive the room. Assign one
owner per decision. Every core process must protect a specific brand promise from
the positioning. Carry the unit-economics targets from the business-model stage
into a gate. {extra or ''}

Return JSON:
{{
  "kill": [{{"what": "...", "why": "...", "sunk_cost_rebuttal": "the 'but we invested in that' answer", "frees": "time | cash | focus — be specific", "who_pushes_back": "role/person + why"}}],
  "keep": [{{"what": "...", "why": "...", "risk_if_dropped": "..."}}],
  "scale": [{{"what": "...", "why": "...", "first_constraint": "what breaks first when this grows", "prereq": "what must be true before scaling it"}}],
  "capability_gaps": [{{"gap": "skill/system/partner the strategy needs and the org lacks", "build_buy_borrow": "build|buy|borrow", "reason": "..."}}],
  "the_one_hire": "the single role that unblocks the most, or 'none — no hire in 90 days' with why",
  "org_redesign": "2-4 sentences — roles and where authority sits, not an org chart",
  "decision_rights": [{{"decision": "e.g. pricing changes / what ships / brand exceptions", "owner": "one role", "consulted": ["..."], "informed": ["..."]}}],
  "core_processes": [{{"name": "...", "owner": "role", "trigger": "what starts it", "steps": ["brief"], "sla": "...", "promise_protected": "the specific brand promise this keeps", "failure_mode": "what going wrong looks like"}}],
  "operating_rhythm": {{"daily": {{"purpose": "...", "attendees": "...", "output": "the decision it produces"}}, "weekly": {{...}}, "monthly": {{...}}, "quarterly": {{...}}}},
  "promise_kpis": [{{"kpi": "...", "target": "...", "proves": "which promise", "replaces_vanity_metric": "...", "source": "where the number comes from", "baseline": "value or unknown"}}],
  "unit_economics_gate": {{"must_hold": [{{"metric": "gross margin / CAC payback / LTV:CAC / contribution", "threshold": "...", "why": "..."}}], "pause_growth_trigger": "the condition that means stop spending on acquisition"}},
  "unit_economics_notes": "the one paragraph a founder must internalise",
  "operating_plan_90d": [{{"change": "...", "owner": "role", "done_looks_like": "observable", "depends_on": "prior change or null"}}],
  "transition_risks": [{{"risk": "morale | capacity | customer disruption during the change", "mitigation": "..."}}],
  "alternative_angles": [{{"angle": "lean — founder holds more, hires later", "when_to_pick": "..."}}, {{"angle": "hire ahead of the curve", "when_to_pick": "..."}}]
}}"""
        d = _draft_then_refine(prompt, {
            "kill": [], "keep": [], "scale": [], "capability_gaps": [],
            "the_one_hire": "none — no hire in the first 90 days; fix process before adding people",
            "org_redesign": "Keep the team small; one named owner per core process and per key decision, with authority to decide, not just execute.",
            "decision_rights": [], "core_processes": [],
            "operating_rhythm": {"daily": {"purpose": "unblock", "attendees": "core team", "output": "today's ship list"}, "weekly": {"purpose": "metrics + one decision", "attendees": "owners", "output": "the week's call"}, "monthly": {"purpose": "stage retro", "attendees": "all", "output": "re-ranked roadmap"}, "quarterly": {"purpose": "re-diagnose", "attendees": "founder + advisors", "output": "reset targets"}},
            "promise_kpis": [],
            "unit_economics_gate": {"must_hold": [{"metric": "CAC payback", "threshold": "<= 3 months", "why": "beyond that, growth burns cash faster than it earns"}], "pause_growth_trigger": "CAC payback slips past 4 months two months running"},
            "unit_economics_notes": "Contribution margin must cover CAC within ~3 months of first purchase, or scaling makes losses bigger, not the business.",
            "operating_plan_90d": [], "transition_risks": [], "alternative_angles": [],
        }, "The kill list is the point — each needs the sunk-cost rebuttal and who "
           "fights it. One owner per decision, no committees. Every core process "
           "names the promise it protects. The gate needs a concrete pause trigger.")
        return await self._save(RestructuringPlan(
            business_id=business_id,
            kill=d.get("kill"), keep=d.get("keep"), scale=d.get("scale"),
            org_redesign=d.get("org_redesign"),
            core_processes=d.get("core_processes"),
            promise_kpis=d.get("promise_kpis"),
            unit_economics_notes=d.get("unit_economics_notes"),
            capability_gaps=d.get("capability_gaps"),
            decision_rights=d.get("decision_rights"),
            operating_rhythm=d.get("operating_rhythm"),
            unit_economics_gate=d.get("unit_economics_gate"),
            operating_plan_90d=d.get("operating_plan_90d"),
            transition_risks=d.get("transition_risks"),
            the_one_hire=d.get("the_one_hire"),
            alternative_angles=d.get("alternative_angles"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))
