"""Brand Transformation services — the specialist AI agents.

Each agent is a thin, deterministic wrapper around a Claude call:
  1. build a prompt that injects the relevant research (knowledge.py),
  2. ask Claude for strict JSON,
  3. parse with a safe fallback,
  4. persist an artifact row and return it.

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
_MAX_TOKENS = 4000

_SYSTEM = (
    "You are a senior brand strategist and business-model architect. You turn "
    "commoditized, mediocre businesses into category references. You reason from "
    "concrete precedents (Red Bull, Supreme, Starbucks, Tesla, Liquid Death, "
    "Decathlon, Apple) and named frameworks (Dunford positioning, Play Bigger "
    "category design, Jung archetypes, Hormozi value equation, Blue Ocean ERRC, "
    "growth loops). You are specific, opinionated, and allergic to generic advice. "
    "You ALWAYS answer with a single valid JSON object and nothing else."
)


def _client() -> Any:
    """Lazy anthropic client so a missing key never breaks import/startup."""
    import anthropic

    return anthropic.Anthropic()


def _ask_json(prompt: str, fallback: dict) -> dict:
    """Call Claude, expect one JSON object back, fall back on any failure."""
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
    async def run(self, business_id: uuid.UUID, profile: dict, extra: str | None = None) -> BrandDiagnosis:
        prompt = f"""{_profile_block(profile)}

REFERENCE — how iconic brands beat commoditization:
{K.origins_digest()}

FRAMEWORKS:
{K.frameworks_digest(['dunford_positioning', 'category_design_playbigger', 'eeat_authority', 'blue_ocean_errc'])}

TASK: Diagnose why this business is mediocre / undifferentiated today. Score its
"Referent Potential" (0-100 = how realistically it could become a category
reference). {extra or ''}

Return JSON:
{{
  "referent_potential_score": <int 0-100>,
  "commoditization_level": "low|medium|high|severe",
  "symptoms": ["specific observable symptom", ...],
  "root_causes": ["underlying cause", ...],
  "highest_leverage_moves": ["move 1", "move 2", "move 3"],
  "scorecard": {{"positioning": <0-5>, "brand_identity": <0-5>, "offer": <0-5>, "fomo_desire": <0-5>, "distribution": <0-5>, "authority": <0-5>}},
  "summary": "3-4 sentence blunt assessment"
}}"""
        d = _ask_json(prompt, {
            "referent_potential_score": 40,
            "commoditization_level": "high",
            "symptoms": ["Positioning indistinguishable from competitors", "Competes on price"],
            "root_causes": ["No point of view", "No owned category"],
            "highest_leverage_moves": ["Define a category", "Pick an archetype", "Build a grand-slam offer"],
            "scorecard": {"positioning": 1, "brand_identity": 1, "offer": 2, "fomo_desire": 1, "distribution": 2, "authority": 1},
            "summary": "Undifferentiated player in a crowded field; needs positioning and identity work before growth spend.",
        })
        return await self._save(BrandDiagnosis(
            business_id=business_id,
            industry=profile.get("industry", "n/a"),
            current_positioning=profile.get("current_positioning"),
            known_competitors=profile.get("known_competitors"),
            revenue_model=profile.get("revenue_model"),
            notes=profile.get("notes"),
            referent_potential_score=int(d.get("referent_potential_score", 0)),
            commoditization_level=d.get("commoditization_level", "unknown"),
            symptoms=d.get("symptoms"),
            root_causes=d.get("root_causes"),
            highest_leverage_moves=d.get("highest_leverage_moves"),
            scorecard=d.get("scorecard"),
            summary=d.get("summary"),
        ))

    async def latest(self, business_id: uuid.UUID) -> BrandDiagnosis | None:
        r = await self.db.execute(
            select(BrandDiagnosis).where(BrandDiagnosis.business_id == business_id)
            .order_by(desc(BrandDiagnosis.created_at)).limit(1)
        )
        return r.scalar_one_or_none()


class PositioningAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> PositioningStatement:
        prompt = f"""{_profile_block(profile)}

PRIOR DIAGNOSIS: {json.dumps(context or {}, ensure_ascii=False)[:1500]}

FRAMEWORKS:
{K.frameworks_digest(['dunford_positioning', 'category_design_playbigger'])}

REFERENCE PLAYBOOKS:
{K.origins_digest()}

TASK: Produce a sharp repositioning + category design. Name an enemy. State a
point of view the market can rally around or reject. {extra or ''}

Return JSON:
{{
  "competitive_alternatives": [...],
  "unique_attributes": [...],
  "value_themes": [...],
  "best_fit_customers": [...],
  "market_category": "existing category to frame within",
  "new_category_name": "a category this brand could own (or null)",
  "point_of_view": "the manifesto-level belief, 2-3 sentences",
  "the_enemy": "the status quo / villain this brand fights",
  "positioning_statement": "For [customer] who [need], [brand] is the [category] that [unique value], unlike [alternative], because [reason].",
  "one_liner": "<12 word external one-liner"
}}"""
        d = _ask_json(prompt, {
            "competitive_alternatives": ["Do nothing", "Incumbent competitors", "DIY"],
            "unique_attributes": ["TBD"], "value_themes": ["TBD"], "best_fit_customers": ["TBD"],
            "market_category": profile.get("industry", "n/a"), "new_category_name": None,
            "point_of_view": "The current way is broken; there is a better one.",
            "the_enemy": "The commoditized status quo",
            "positioning_statement": "Positioning statement pending refinement.",
            "one_liner": "The better way to " + profile.get("what_they_sell", "do this"),
        })
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
        ))


class BrandIdentityAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> BrandIdentity:
        prompt = f"""{_profile_block(profile)}

PRIOR POSITIONING: {json.dumps(context or {}, ensure_ascii=False)[:1800]}

FRAMEWORKS:
{K.frameworks_digest(['jung_brand_archetypes', 'brand_voice_system'])}

TASK: Build brand identity v1 — pick ONE primary archetype and justify it. Decide
if a rename is warranted. Write a tagline and a short manifesto in the brand voice.
{extra or ''}

Return JSON:
{{
  "primary_archetype": "one of the 12",
  "secondary_archetype": "one of the 12 or null",
  "rename_recommended": true|false,
  "name_candidates": ["Name — rationale", ...],
  "tagline": "<=6 words",
  "manifesto": "80-140 words, in the brand voice",
  "voice_attributes": ["adj", "adj", "adj", "adj"],
  "voice_do": [...],
  "voice_dont": [...],
  "sample_rewrites": [{{"context": "welcome email opener", "text": "..."}}, {{"context": "out-of-stock notice", "text": "..."}}],
  "visual_brief": {{"mood": "...", "palette_direction": "...", "typography": "...", "imagery": "..."}},
  "brand_architecture": "1-2 sentences on master brand vs sub-brands"
}}"""
        d = _ask_json(prompt, {
            "primary_archetype": "Hero", "secondary_archetype": "Outlaw", "rename_recommended": False,
            "name_candidates": [], "tagline": "Do it better.",
            "manifesto": "Manifesto pending refinement.",
            "voice_attributes": ["blunt", "warm", "expert", "never corporate"],
            "voice_do": ["Speak plainly", "Take a side"], "voice_dont": ["Use jargon", "Hedge"],
            "sample_rewrites": [], "visual_brief": {"mood": "bold, high-contrast", "palette_direction": "one strong accent + neutrals", "typography": "grotesk display + humanist body", "imagery": "real people, unpolished"},
            "brand_architecture": "Single master brand.",
        })
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
            brand_architecture=d.get("brand_architecture"),
        ))


class BusinessModelAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> BusinessModelRedesign:
        prompt = f"""{_profile_block(profile)}

PRIOR CONTEXT: {json.dumps(context or {}, ensure_ascii=False)[:1800]}

FRAMEWORKS:
{K.frameworks_digest(['business_model_canvas', 'business_model_patterns', 'hormozi_value_equation', 'blue_ocean_errc'])}

REFERENCE PLAYBOOKS (note the real engine, not the surface product):
{K.origins_digest()}

TASK: Redesign the business model. Apply 2-3 named patterns. Build a grand-slam
offer using the value equation. Design a pricing architecture with psychological
anchors. {extra or ''}

Return JSON:
{{
  "canvas": {{"customer_segments": [...], "value_propositions": [...], "channels": [...], "customer_relationships": [...], "revenue_streams": [...], "key_resources": [...], "key_activities": [...], "key_partners": [...], "cost_structure": [...]}},
  "applied_patterns": ["pattern — how it applies here", ...],
  "new_revenue_streams": [...],
  "grand_slam_offer": {{"dream_outcome": "...", "core": "...", "bonuses": [...], "guarantee": "...", "scarcity": "...", "urgency": "..."}},
  "pricing_architecture": {{"tiers": [{{"name": "...", "price": "...", "for": "..."}}], "anchor": "...", "psych_tactics": [...]}},
  "errc_grid": {{"eliminate": [...], "reduce": [...], "raise": [...], "create": [...]}},
  "rationale": "why this model beats the current one"
}}"""
        d = _ask_json(prompt, {
            "canvas": {}, "applied_patterns": ["subscription", "membership_club"],
            "new_revenue_streams": [], "grand_slam_offer": {},
            "pricing_architecture": {}, "errc_grid": {},
            "rationale": "Shift from one-off transactions to recurring membership to build retention and predictability.",
        })
        return await self._save(BusinessModelRedesign(
            business_id=business_id,
            canvas=d.get("canvas"),
            applied_patterns=d.get("applied_patterns"),
            new_revenue_streams=d.get("new_revenue_streams"),
            grand_slam_offer=d.get("grand_slam_offer"),
            pricing_architecture=d.get("pricing_architecture"),
            errc_grid=d.get("errc_grid"),
            rationale=d.get("rationale"),
        ))


class FOMOEngineAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> FOMOPlaybook:
        prompt = f"""{_profile_block(profile)}

PRIOR CONTEXT: {json.dumps(context or {}, ensure_ascii=False)[:1500]}

FOMO / DESIRE LEVERS (mechanism · cases · anti-pattern):
{K.levers_digest()}

TASK: Design a FOMO / desire engine tuned to THIS business and its ethics. Pick
4-6 levers that genuinely fit. For each: why it fits, concrete implementation, a
KPI, and an anti-fake guardrail (scarcity/urgency must be real). Add a launch
ritual and a cadence. {extra or ''}

Return JSON:
{{
  "mechanisms": [{{"lever": "...", "why_it_fits": "...", "implementation": "concrete steps", "kpi": "...", "anti_fake_guardrail": "..."}}, ...],
  "launch_ritual": {{"name": "...", "sequence": [...], "payoff": "..."}},
  "cadence": "e.g. 'monthly limited drop, first Tuesday'",
  "risk_notes": "where this could backfire and how to avoid it"
}}"""
        d = _ask_json(prompt, {
            "mechanisms": [
                {"lever": "social_proof_velocity", "why_it_fits": "Trust gap in category", "implementation": "Surface review count + recent activity", "kpi": "conv. rate lift", "anti_fake_guardrail": "Only real, verifiable numbers"},
                {"lever": "anticipation_and_ritual", "why_it_fits": "Nothing to look forward to today", "implementation": "Monthly themed release with countdown", "kpi": "launch-day revenue", "anti_fake_guardrail": "Always deliver on the promised date"},
            ],
            "launch_ritual": {"name": "The Drop", "sequence": ["tease -7d", "preview -2d", "open", "sellout recap"], "payoff": "members get first access"},
            "cadence": "monthly", "risk_notes": "Avoid permanent 'ending soon' banners; they train customers to ignore deadlines.",
        })
        return await self._save(FOMOPlaybook(
            business_id=business_id,
            mechanisms=d.get("mechanisms"),
            launch_ritual=d.get("launch_ritual"),
            cadence=d.get("cadence"),
            risk_notes=d.get("risk_notes"),
        ))


class GoToMarketAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> GTMPlan:
        prompt = f"""{_profile_block(profile)}

PRIOR CONTEXT: {json.dumps(context or {}, ensure_ascii=False)[:1800]}

FRAMEWORKS:
{K.frameworks_digest(['growth_loops', 'category_design_playbigger', 'hormozi_value_equation'])}

TASK: Build a 90-day go-to-market. Choose ONE primary growth loop the model can
sustain. Design a lightning-strike launch. Map 3-4 channels with a first action
each. {extra or ''}

Return JSON:
{{
  "primary_growth_loop": {{"type": "viral|content|paid|ugc", "steps": [...], "reinvestment": "what output feeds back to input"}},
  "channels": [{{"channel": "...", "role": "...", "first_action": "..."}}, ...],
  "lightning_strike": {{"pre_launch": [...], "launch_week": [...], "post_launch": [...]}},
  "funnel": {{"awareness": "...", "consideration": "...", "conversion": "...", "retention": "..."}},
  "content_pillars": [...],
  "plan_90_days": [{{"weeks": "1-2", "focus": "...", "outcome": "..."}}, ...]
}}"""
        d = _ask_json(prompt, {
            "primary_growth_loop": {"type": "content", "steps": ["publish POV content", "earns search + shares", "converts to trial", "customers create case studies"], "reinvestment": "revenue funds more content production"},
            "channels": [], "lightning_strike": {}, "funnel": {}, "content_pillars": [],
            "plan_90_days": [],
        })
        return await self._save(GTMPlan(
            business_id=business_id,
            primary_growth_loop=d.get("primary_growth_loop"),
            channels=d.get("channels"),
            lightning_strike=d.get("lightning_strike"),
            funnel=d.get("funnel"),
            content_pillars=d.get("content_pillars"),
            plan_90_days=d.get("plan_90_days"),
        ))


class RestructuringAgent(_BaseAgent):
    async def run(self, business_id: uuid.UUID, profile: dict, context: dict | None = None, extra: str | None = None) -> RestructuringPlan:
        prompt = f"""{_profile_block(profile)}

FULL PRIOR CONTEXT: {json.dumps(context or {}, ensure_ascii=False)[:2400]}

TASK: Turn strategy into operating reality. Decide what to KILL, KEEP, and SCALE.
Propose a light org redesign, 3 core processes (owner + SLA + why), and the KPIs
that actually prove the new brand promise. {extra or ''}

Return JSON:
{{
  "kill": ["thing — why"], "keep": ["thing — why"], "scale": ["thing — why"],
  "org_redesign": "2-4 sentences",
  "core_processes": [{{"name": "...", "owner": "role", "sla": "...", "why": "..."}}, ...],
  "promise_kpis": [{{"kpi": "...", "target": "...", "proves": "which brand promise"}}, ...],
  "unit_economics_notes": "what must be true for the model to work"
}}"""
        d = _ask_json(prompt, {
            "kill": [], "keep": [], "scale": [],
            "org_redesign": "Keep the team small; assign one owner per core process.",
            "core_processes": [], "promise_kpis": [],
            "unit_economics_notes": "Contribution margin must cover CAC payback within 3 months.",
        })
        return await self._save(RestructuringPlan(
            business_id=business_id,
            kill=d.get("kill"), keep=d.get("keep"), scale=d.get("scale"),
            org_redesign=d.get("org_redesign"),
            core_processes=d.get("core_processes"),
            promise_kpis=d.get("promise_kpis"),
            unit_economics_notes=d.get("unit_economics_notes"),
        ))
