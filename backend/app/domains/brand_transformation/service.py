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


class PositioningAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> PositioningStatement:
        prompt = f"""{_profile_block(profile)}

PRIOR DIAGNOSIS: {json.dumps(context or {}, ensure_ascii=False)[:1800]}

FRAMEWORKS:
{K.frameworks_digest(['dunford_positioning', 'category_design_playbigger'])}

REFERENCE PLAYBOOKS:
{K.origins_digest()}

TASK: Produce a sharp repositioning + category design. Name a REAL enemy (the
actual status quo behaviour customers tolerate — not a straw man competitor).
State a point of view the market can rally around OR reject; a POV nobody could
disagree with is worthless. {extra or ''}

Return JSON:
{{
  "competitive_alternatives": ["what the customer actually does instead today", ...],
  "unique_attributes": ["something true of this business that alternatives can't claim", ...],
  "value_themes": ["the value those attributes unlock, in the customer's words", ...],
  "best_fit_customers": ["the segment that cares most about that value — be narrow", ...],
  "market_category": "existing category to frame within so the value is obvious",
  "new_category_name": "a category this brand could credibly define and lead (or null if premature)",
  "point_of_view": "the manifesto-level belief, 2-3 sentences, the kind that makes some people nod hard and others bristle",
  "the_enemy": "the real status-quo behaviour or belief this brand fights",
  "positioning_statement": "For [customer] who [need], [brand] is the [category] that [unique value], unlike [alternative], because [reason].",
  "one_liner": "<12 word external one-liner a customer could repeat verbatim",
  "alternative_angles": [
    {{"angle": "a genuinely different positioning bet", "enemy": "...", "when_to_pick": "the condition under which this beats the primary"}},
    {{"angle": "a second, different bet", "enemy": "...", "when_to_pick": "..."}}
  ]
}}"""
        d = _draft_then_refine(prompt, {
            "competitive_alternatives": ["Do nothing / live with the problem", "Incumbent competitors", "DIY / in-house"],
            "unique_attributes": ["TBD — needs founder input"],
            "value_themes": ["TBD"], "best_fit_customers": ["TBD"],
            "market_category": profile.get("industry", "n/a"), "new_category_name": None,
            "point_of_view": "The default way this gets done wastes the customer's time and nobody has said so out loud.",
            "the_enemy": "The commoditized status quo everyone has stopped questioning",
            "positioning_statement": "Positioning statement pending founder input.",
            "one_liner": "The better way to " + str(profile.get("what_they_sell", "do this")),
            "alternative_angles": [],
        }, "The enemy and the POV are the whole game here — make them specific and "
           "a little provocative. The two alternative_angles must be real strategic "
           "forks, not reworded versions of the primary.")
        return await self._save(PositioningStatement(
            business_id=business_id,
            competitive_alternatives=d.get("competitive_alternatives"),
            unique_attributes=d.get("unique_attributes"),
            value_themes=d.get("value_themes"),
            best_fit_customers=d.get("best_fit_customers"),
            market_category=d.get("market_category"),
            new_category_name=d.get("new_category_name"),
            point_of_view=d.get("point_of_view"),
            the_enemy=d.get("the_enemy"),
            positioning_statement=d.get("positioning_statement"),
            one_liner=d.get("one_liner"),
            alternative_angles=d.get("alternative_angles"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class BrandIdentityAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> BrandIdentity:
        prompt = f"""{_profile_block(profile)}

PRIOR POSITIONING: {json.dumps(context or {}, ensure_ascii=False)[:2200]}

FRAMEWORKS:
{K.frameworks_digest(['jung_brand_archetypes', 'brand_voice_system'])}

TASK: Build brand identity v1. Pick ONE primary archetype and justify it from the
positioning (not from taste). Decide honestly whether a rename is warranted —
most of the time it is NOT; say so if so. Write a tagline and a short manifesto
that read like a real brand published them, not a template. {extra or ''}

Return JSON:
{{
  "primary_archetype": "one of the 12",
  "secondary_archetype": "one of the 12 or null",
  "archetype_rationale": "why this one follows from the positioning",
  "rename_recommended": true|false,
  "rename_rationale": "one sentence — why keep or why change",
  "name_candidates": ["Name — the idea behind it", ...],
  "tagline": "<=6 words, no colon, no cliché",
  "manifesto": "90-150 words, in the brand voice, with rhythm — read it aloud before you submit it",
  "voice_attributes": ["adj", "adj", "adj", "adj"],
  "voice_do": ["concrete instruction", ...],
  "voice_dont": ["concrete instruction", ...],
  "sample_rewrites": [
    {{"context": "welcome message opener", "text": "..."}},
    {{"context": "out-of-stock / sold-out notice", "text": "..."}},
    {{"context": "price objection reply", "text": "..."}}
  ],
  "visual_brief": {{"mood": "...", "palette_direction": "...", "typography": "...", "imagery": "...", "one_thing_to_avoid": "..."}},
  "brand_architecture": "1-2 sentences: master brand vs sub-brands",
  "alternative_angles": [
    {{"archetype": "a different defensible archetype", "what_changes": "how voice + manifesto would shift", "when_to_pick": "..."}},
    {{"archetype": "...", "what_changes": "...", "when_to_pick": "..."}}
  ]
}}"""
        d = _draft_then_refine(prompt, {
            "primary_archetype": "Hero", "secondary_archetype": "Outlaw",
            "archetype_rationale": "Positioning frames the brand as the one that fights the status quo for the customer.",
            "rename_recommended": False, "rename_rationale": "Existing name has equity; the problem is meaning, not letters.",
            "name_candidates": [], "tagline": "Do it properly.",
            "manifesto": "Manifesto pending positioning sign-off.",
            "voice_attributes": ["blunt", "warm", "expert", "never corporate"],
            "voice_do": ["Say the number", "Take a side", "Cut the intro"],
            "voice_dont": ["Use 'leverage' or 'synergy'", "Hedge with five qualifiers"],
            "sample_rewrites": [], "visual_brief": {"mood": "bold, high-contrast", "palette_direction": "one loud accent + disciplined neutrals", "typography": "grotesk display + humanist body", "imagery": "real people, unretouched", "one_thing_to_avoid": "stock-photo handshakes"},
            "brand_architecture": "Single master brand; no sub-brands until there is a second product line.",
            "alternative_angles": [],
        }, "The manifesto and tagline are judged on whether a real brand would ship "
           "them. Kill anything that sounds like a mission-statement generator.")
        return await self._save(BrandIdentity(
            business_id=business_id,
            primary_archetype=d.get("primary_archetype"),
            secondary_archetype=d.get("secondary_archetype"),
            rename_recommended=bool(d.get("rename_recommended", False)),
            name_candidates=d.get("name_candidates"),
            tagline=d.get("tagline"),
            manifesto=d.get("manifesto"),
            voice_attributes=d.get("voice_attributes"),
            voice_do=d.get("voice_do"),
            voice_dont=d.get("voice_dont"),
            sample_rewrites=d.get("sample_rewrites"),
            visual_brief=d.get("visual_brief"),
            brand_architecture=" | ".join(x for x in [d.get("brand_architecture"), d.get("archetype_rationale"), d.get("rename_rationale")] if x),
            alternative_angles=d.get("alternative_angles"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class BusinessModelAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> BusinessModelRedesign:
        prompt = f"""{_profile_block(profile)}

PRIOR CONTEXT: {json.dumps(context or {}, ensure_ascii=False)[:2200]}

FRAMEWORKS:
{K.frameworks_digest(['business_model_canvas', 'business_model_patterns', 'hormozi_value_equation', 'blue_ocean_errc'])}

REFERENCE PLAYBOOKS (the real engine, not the surface product):
{K.origins_digest()}

TASK: Redesign the business model. Apply 2-3 NAMED patterns and explain how each
transfers to THIS business specifically (do not just copy the example's product).
Build a grand-slam offer using the value equation — push the numerator, shrink the
denominator, and make the guarantee sting a little. Design a pricing architecture
with a real anchor and named psychological tactics. {extra or ''}

Return JSON:
{{
  "canvas": {{"customer_segments": [...], "value_propositions": [...], "channels": [...], "customer_relationships": [...], "revenue_streams": [...], "key_resources": [...], "key_activities": [...], "key_partners": [...], "cost_structure": [...]}},
  "applied_patterns": [{{"pattern": "name", "how_it_applies_here": "specific to this business", "precedent": "brand that ran it"}}, ...],
  "new_revenue_streams": [{{"stream": "...", "mechanism": "...", "rough_contribution": "small|medium|large"}}, ...],
  "grand_slam_offer": {{"dream_outcome": "...", "core": "...", "bonuses": [...], "guarantee": "specific and a little bold", "scarcity": "real, not fake", "urgency": "real deadline with a real reason", "why_saying_no_feels_dumb": "..."}},
  "pricing_architecture": {{"tiers": [{{"name": "...", "price": "...", "for": "...", "the_trick": "what this tier is really there to do"}}], "anchor": "...", "psych_tactics": ["named tactic — why it works here", ...]}},
  "errc_grid": {{"eliminate": [...], "reduce": [...], "raise": [...], "create": [...]}},
  "rationale": "why this model beats the current one — in money terms"
}}"""
        d = _draft_then_refine(prompt, {
            "canvas": {}, "applied_patterns": [
                {"pattern": "membership_club", "how_it_applies_here": "Convert repeat buyers into a paid tier with earned perks", "precedent": "Amazon Prime"},
                {"pattern": "razor_and_blade", "how_it_applies_here": "Low-margin entry product, recurring consumable/service attached", "precedent": "Dollar Shave Club"},
            ],
            "new_revenue_streams": [], "grand_slam_offer": {},
            "pricing_architecture": {}, "errc_grid": {},
            "rationale": "Recurring revenue lifts LTV and makes CAC affordable; today every sale starts from zero.",
        }, "Every applied pattern must say how it transfers here — reject any that "
           "just restate the precedent. The guarantee and pricing 'trick' fields "
           "are where this earns its keep.")
        return await self._save(BusinessModelRedesign(
            business_id=business_id,
            canvas=d.get("canvas"),
            applied_patterns=d.get("applied_patterns"),
            new_revenue_streams=d.get("new_revenue_streams"),
            grand_slam_offer=d.get("grand_slam_offer"),
            pricing_architecture=d.get("pricing_architecture"),
            errc_grid=d.get("errc_grid"),
            rationale=d.get("rationale"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class FOMOEngineAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> FOMOPlaybook:
        prompt = f"""{_profile_block(profile)}

PRIOR CONTEXT: {json.dumps(context or {}, ensure_ascii=False)[:1800]}

FOMO / DESIRE LEVERS (mechanism · cases · anti-pattern):
{K.levers_digest()}

TASK: Design a FOMO / desire engine tuned to THIS business and its ethics. Pick
4-6 levers that genuinely fit. For each: why it fits, a CONCRETE implementation
with a non-obvious detail (the obvious version doesn't count), a KPI, and an
anti-fake guardrail — scarcity and urgency must be real and disprovable-safe.
Add a launch ritual with a name, and a cadence the audience can organise their
week/month around. {extra or ''}

Return JSON:
{{
  "mechanisms": [
    {{"lever": "...", "why_it_fits": "...", "implementation": "concrete steps incl. one non-obvious detail", "kpi": "...", "anti_fake_guardrail": "...", "precedent": "brand that ran this well"}},
    ...
  ],
  "launch_ritual": {{"name": "a name the audience would actually use", "sequence": [...], "payoff": "what members get that others don't", "the_hook": "the single reason people show up"}},
  "cadence": "e.g. 'first Tuesday each month, 11:00' — specific",
  "sequence_of_rollout": ["which mechanism to turn on first and why", "then...", "..."],
  "risk_notes": "where this backfires (trust, fatigue, brand) and the specific guardrail",
  "alternative_angles": [
    {{"angle": "a different mechanism mix for a different risk appetite", "when_to_pick": "..."}},
    {{"angle": "...", "when_to_pick": "..."}}
  ]
}}"""
        d = _draft_then_refine(prompt, {
            "mechanisms": [
                {"lever": "social_proof_velocity", "why_it_fits": "Trust gap in the category", "implementation": "Show verified recent-buyer count + the specific thing they bought, updated hourly", "kpi": "PDP->cart conversion", "anti_fake_guardrail": "Only real, queryable numbers; never round up", "precedent": "Booking.com"},
                {"lever": "anticipation_and_ritual", "why_it_fits": "Customers have nothing to look forward to", "implementation": "Monthly themed release, teased 7 days out with one detail revealed per day", "kpi": "launch-day revenue vs baseline day", "anti_fake_guardrail": "Ship on the promised date every time or the ritual dies", "precedent": "Glossier"},
            ],
            "launch_ritual": {"name": "The Drop", "sequence": ["tease -7d", "daily reveal", "open", "sellout recap + waitlist"], "payoff": "members get 24h early access", "the_hook": "the thing sells out and doesn't come back"},
            "cadence": "monthly",
            "sequence_of_rollout": ["Social proof first (no supply risk)", "then the ritual once inventory is reliable"],
            "risk_notes": "Permanent 'ending soon' banners train customers to ignore every deadline — use real, infrequent ones.",
            "alternative_angles": [],
        }, "Reject any mechanism whose implementation is the textbook version — "
           "each needs one detail a competitor wouldn't think of. Guardrails must "
           "be concrete, not 'be honest'.")
        return await self._save(FOMOPlaybook(
            business_id=business_id,
            mechanisms=d.get("mechanisms"),
            launch_ritual=d.get("launch_ritual"),
            cadence=d.get("cadence"),
            risk_notes=" | ".join(x for x in [d.get("risk_notes"), "Rollout: " + "; ".join(d.get("sequence_of_rollout") or [])] if x and x != "Rollout: "),
            alternative_angles=d.get("alternative_angles"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class GoToMarketAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> GTMPlan:
        prompt = f"""{_profile_block(profile)}

PRIOR CONTEXT: {json.dumps(context or {}, ensure_ascii=False)[:2200]}

FRAMEWORKS:
{K.frameworks_digest(['growth_loops', 'category_design_playbigger', 'hormozi_value_equation'])}

TASK: Build a 90-day go-to-market. Choose ONE primary growth loop the model can
actually sustain (say why the others were rejected). Design a lightning-strike
launch that concentrates force rather than spreading it. Map 3-4 channels, each
with a first concrete action and the signal that tells you it's working or not.
{extra or ''}

Return JSON:
{{
  "primary_growth_loop": {{"type": "viral|content|paid|ugc|sales", "steps": [...], "reinvestment": "what output feeds back into input", "why_not_the_others": "..."}},
  "channels": [{{"channel": "...", "role": "...", "first_action": "...", "kill_signal": "what result after N weeks means stop"}}, ...],
  "lightning_strike": {{"pre_launch": [...], "launch_week": [...], "post_launch": [...], "the_one_moment": "the single thing the launch is built around"}},
  "funnel": {{"awareness": "...", "consideration": "...", "conversion": "...", "retention": "..."}},
  "content_pillars": [{{"pillar": "...", "angle": "the POV, not the topic"}}, ...],
  "plan_90_days": [{{"weeks": "1-2", "focus": "...", "owner": "role", "success_metric": "..."}}, ...],
  "first_domino": "the single highest-leverage thing to do in week 1"
}}"""
        d = _draft_then_refine(prompt, {
            "primary_growth_loop": {"type": "content", "steps": ["publish POV content", "earns search + shares", "converts to trial", "customers produce case studies that feed content"], "reinvestment": "revenue funds more production", "why_not_the_others": "No viral coefficient in the product; paid loop needs margin the model doesn't have yet"},
            "channels": [], "lightning_strike": {}, "funnel": {}, "content_pillars": [],
            "plan_90_days": [], "first_domino": "Publish the point-of-view piece the positioning implies and pin it everywhere.",
        }, "The loop choice must justify why the alternatives were rejected. Each "
           "channel needs a kill signal so this isn't a wish list.")
        return await self._save(GTMPlan(
            business_id=business_id,
            primary_growth_loop=d.get("primary_growth_loop"),
            channels=d.get("channels"),
            lightning_strike=d.get("lightning_strike"),
            funnel=d.get("funnel"),
            content_pillars=d.get("content_pillars"),
            plan_90_days=(d.get("plan_90_days") or []) + ([{"first_domino": d["first_domino"]}] if d.get("first_domino") else []),
            alternative_angles=d.get("alternative_angles"),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))


class RestructuringAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> RestructuringPlan:
        prompt = f"""{_profile_block(profile)}

FULL PRIOR CONTEXT: {json.dumps(context or {}, ensure_ascii=False)[:3200]}

TASK: Turn the strategy into operating reality. Decide what to KILL (with the
sunk-cost objection pre-answered), KEEP, and SCALE. Propose a light org redesign
— roles, not headcount fantasy. Define 3 core processes (owner + SLA + why it
matters to the brand promise). Name the KPIs that would actually prove the new
promise is being kept, not vanity metrics. {extra or ''}

Return JSON:
{{
  "kill": [{{"what": "...", "why": "...", "objection_answered": "the 'but we invested in that' rebuttal"}}, ...],
  "keep": [{{"what": "...", "why": "..."}}, ...],
  "scale": [{{"what": "...", "why": "...", "constraint_to_watch": "..."}}, ...],
  "org_redesign": "2-4 sentences — roles and decision rights, not an org chart",
  "core_processes": [{{"name": "...", "owner": "role", "sla": "...", "why": "how it protects the brand promise"}}, ...],
  "promise_kpis": [{{"kpi": "...", "target": "...", "proves": "which specific brand promise", "not_this": "the vanity metric it replaces"}}, ...],
  "unit_economics_notes": "what must be true (CAC payback, margin, retention) for the model to work — with rough numbers",
  "90_day_operational_priorities": ["...", "...", "..."]
}}"""
        d = _draft_then_refine(prompt, {
            "kill": [], "keep": [], "scale": [],
            "org_redesign": "Keep the team small; one named owner per core process with authority to decide, not just execute.",
            "core_processes": [], "promise_kpis": [],
            "unit_economics_notes": "Contribution margin must cover CAC within ~3 months of first purchase, or growth burns cash.",
            "90_day_operational_priorities": [],
        }, "The kill list is the point — each item needs the sunk-cost rebuttal or "
           "it won't survive the room. KPIs must name the vanity metric they replace.")
        return await self._save(RestructuringPlan(
            business_id=business_id,
            kill=d.get("kill"), keep=d.get("keep"), scale=d.get("scale"),
            org_redesign=d.get("org_redesign"),
            core_processes=d.get("core_processes"),
            promise_kpis=d.get("promise_kpis"),
            unit_economics_notes=" | ".join(x for x in [d.get("unit_economics_notes"), "90d: " + "; ".join(d.get("90_day_operational_priorities") or [])] if x and x != "90d: "),
            confidence=_int(d.get("confidence"), 60),
            frameworks_applied=d.get("frameworks_applied"),
            generated_by=d.get("_generated_by", "unknown"),
        ))
