"""Positioning bridge — a PositioningAgent statement into real competitive-
intelligence assets.

Etapa 1 (`PositioningAgent`) names the enemy, the competitive alternatives
(`alternatives_matrix`), and the attributes that beat them
(`attribute_value_proof`). This module turns that into:
  - a `competitive.CompetitiveMonitor` per named competitor (24/7 tracking)
  - a `competitive.CompetitiveBattlecard` per competitor, pre-filled from the
    positioning (our strengths / their strengths / their weaknesses / the
    enemy framing)

Deterministic, no LLM. Competitors need a URL (the monitor model requires it);
a competitor with only a name is reported as skipped.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.brand_transformation.models import PositioningStatement

logger = get_logger(__name__)


def _battlecard_from(statement: PositioningStatement, competitor: str) -> dict:
    matrix = statement.alternatives_matrix or []
    match = next(
        (m for m in matrix if isinstance(m, dict) and competitor.lower() in str(m.get("alternative", "")).lower()),
        None,
    )
    our_strengths = [a.get("attribute") for a in (statement.attribute_value_proof or []) if isinstance(a, dict) and a.get("attribute")]
    their_strengths = [match["what_customer_keeps"]] if match and match.get("what_customer_keeps") else []
    their_weaknesses = [match["what_they_lose"]] if match and match.get("what_they_lose") else []
    notes_bits = [
        f"Enemy: {(statement.enemy_analysis or {}).get('enemy') or statement.the_enemy}",
        f"Our position: {statement.positioning_statement or statement.one_liner}",
    ]
    return {
        "competitor_name": competitor,
        "our_strengths": our_strengths,
        "our_weaknesses": [],
        "their_strengths": their_strengths,
        "their_weaknesses": their_weaknesses,
        "price_comparison": (statement.reframe or {}).get("to"),
        "feature_comparison": {},
        "notes": " | ".join(x for x in notes_bits if x and "None" not in x),
    }


def build_plan(statement: PositioningStatement, competitors: list[dict] | None) -> dict:
    """competitors: [{name, url, products?}]. Falls back to nothing if none given."""
    comps = competitors or []
    monitors, battlecards, skipped = [], [], []
    for c in comps:
        name = (c.get("name") or "").strip()
        url = (c.get("url") or "").strip()
        if not name:
            continue
        if not url:
            skipped.append({"competitor": name, "reason": "no URL — monitor requires one; battlecard only"})
        else:
            monitors.append({"competitor_name": name, "competitor_url": url, "products_to_track": c.get("products") or []})
        battlecards.append(_battlecard_from(statement, name))
    return {
        "statement_id": str(statement.id),
        "enemy": (statement.enemy_analysis or {}).get("enemy") or statement.the_enemy,
        "monitors": monitors,
        "battlecards": battlecards,
        "skipped": skipped,
        "note": "Battlecards are pre-filled from the positioning; monitors need a competitor URL.",
    }


class PositioningBridge:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def preview(self, statement: PositioningStatement, competitors: list[dict] | None) -> dict:
        return build_plan(statement, competitors)

    async def deploy(
        self,
        statement: PositioningStatement,
        owner_user_id: uuid.UUID,
        competitors: list[dict] | None,
        dry_run: bool = False,
    ) -> dict:
        plan = build_plan(statement, competitors)
        if dry_run:
            plan["dry_run"] = True
            return plan

        created: list[dict] = []

        # monitors
        try:
            from app.domains.competitive.intelligence_engine import CompetitiveIntelligenceEngine

            engine = CompetitiveIntelligenceEngine(self.db)
            for m in plan["monitors"]:
                try:
                    mon = await engine.monitor_competitor(
                        business_id=statement.business_id,
                        competitor_url=m["competitor_url"],
                        competitor_name=m["competitor_name"],
                        products_to_track=m["products_to_track"],
                    )
                    created.append({"competitor": m["competitor_name"], "monitor_id": str(mon.id)})
                except Exception as e:  # noqa: BLE001
                    created.append({"competitor": m["competitor_name"], "monitor_error": str(e)[:160]})
        except Exception as e:  # noqa: BLE001
            plan["monitor_error"] = f"competitive domain unavailable: {str(e)[:160]}"

        # battlecards
        try:
            from app.domains.competitive.service import create_battlecard

            by_name: dict[str, dict] = {c["competitor"]: c for c in created if "competitor" in c}
            for b in plan["battlecards"]:
                try:
                    card = await create_battlecard(self.db, owner_user_id, {**b, "competitor_url": next(
                        (m["competitor_url"] for m in plan["monitors"] if m["competitor_name"] == b["competitor_name"]), None,
                    )})
                    entry = by_name.setdefault(b["competitor_name"], {"competitor": b["competitor_name"]})
                    entry["battlecard_id"] = str(card.id)
                except Exception as e:  # noqa: BLE001
                    by_name.setdefault(b["competitor_name"], {"competitor": b["competitor_name"]})["battlecard_error"] = str(e)[:160]
            created = list(by_name.values())
        except Exception as e:  # noqa: BLE001
            plan["battlecard_error"] = f"battlecard service unavailable: {str(e)[:160]}"

        try:
            statement.deployed_competitive = (statement.deployed_competitive or []) + created
            await self.db.commit()
        except Exception as e:  # noqa: BLE001
            await self.db.rollback()
            plan["writeback_error"] = str(e)[:160]

        plan["deployed"] = created
        plan["created_count"] = sum(1 for c in created if c.get("monitor_id") or c.get("battlecard_id"))
        return plan
