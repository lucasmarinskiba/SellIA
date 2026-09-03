"""Identity bridge — a BrandIdentityAgent identity system into the real
content / asset pipeline (`app.domains.ai_content_generation`).

Etapa 2 (`BrandIdentityAgent`) produces the verbal identity, manifesto,
tagline(s), sample rewrites, story spine and visual brief. This module turns
that into:
  - one reusable brand-voice `ContentTemplate` (the voice system as a prompt)
  - ready `GeneratedContent` rows for the manifesto, taglines, each sample
    rewrite, the story spine, and the visual brief (as a designer handoff)

Deterministic, no LLM. Assets are saved as drafts (not approved / published).
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.brand_transformation.models import BrandIdentity

logger = get_logger(__name__)


def _voice_template_prompt(ident: BrandIdentity) -> str:
    vi = ident.verbal_identity or {}
    lex = vi.get("lexicon") or {}
    lines = [
        f"BRAND VOICE — {ident.primary_archetype or 'archetype n/a'}"
        + (f" / {ident.secondary_archetype}" if ident.secondary_archetype else ""),
        f"Tagline: {ident.tagline or '—'}",
        "",
        "Voice attributes: " + ", ".join(
            f'{a.get("adj")} (sounds like: {a.get("sounds_like")}; not: {a.get("not")})'
            for a in (vi.get("attributes") or []) if isinstance(a, dict)
        ),
        f"Rhythm: {vi.get('rhythm', '—')}",
        f"Humor: {vi.get('humor', '—')}",
        f"First-line rule: {vi.get('first_line_rule', '—')}",
        "Use these words: " + ", ".join(lex.get("use") or []),
        "Never use: " + ", ".join(lex.get("ban") or []),
        "Non-negotiables: " + " | ".join(ident.identity_consistency_rules or []),
        "",
        "Write every asset in this voice. {input}",
    ]
    return "\n".join(lines)


def build_plan(ident: BrandIdentity) -> dict:
    assets: list[dict] = []
    if ident.manifesto:
        assets.append({"content_type": "manifesto", "content": ident.manifesto})
    if ident.tagline:
        alts = " · ".join(ident.taglines_alt or [])
        assets.append({"content_type": "tagline", "content": ident.tagline + (f"\n\nAlternates: {alts}" if alts else "")})
    for sr in (ident.sample_rewrites or []):
        if isinstance(sr, dict) and sr.get("text"):
            assets.append({"content_type": f"copy:{sr.get('context', 'snippet')}", "content": sr["text"]})
    if ident.story_spine:
        assets.append({"content_type": "story_spine", "content": json.dumps(ident.story_spine, ensure_ascii=False, indent=2)})
    if ident.visual_brief:
        vb = ident.visual_brief
        terms = ", ".join(vb.get("moodboard_search_terms") or []) if isinstance(vb, dict) else ""
        assets.append({
            "content_type": "visual_brief",
            "content": json.dumps(vb, ensure_ascii=False, indent=2) + (f"\n\nMoodboard search: {terms}" if terms else ""),
        })
    return {
        "identity_id": str(ident.id),
        "voice_template": {"template_name": f"[BT] Brand Voice — {ident.primary_archetype or 'v1'}", "template_type": "brand_voice"},
        "assets": assets,
        "consistency_rules": ident.identity_consistency_rules or [],
        "note": "Voice template + draft copy assets land in the content library; visual brief is a designer handoff.",
    }


class IdentityBridge:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def preview(self, ident: BrandIdentity) -> dict:
        return build_plan(ident)

    async def deploy(self, ident: BrandIdentity, dry_run: bool = False) -> dict:
        plan = build_plan(ident)
        if dry_run:
            plan["dry_run"] = True
            return plan

        try:
            from app.domains.ai_content_generation.service import AIContentService
        except Exception as e:  # noqa: BLE001
            return {**plan, "deployed": [], "error": f"content domain unavailable: {str(e)[:160]}"}

        deployed: list[dict] = []
        try:
            tpl = await AIContentService.create_template(
                self.db,
                business_id=ident.business_id,
                template_name=plan["voice_template"]["template_name"],
                template_type="brand_voice",
                template_prompt=_voice_template_prompt(ident),
            )
            deployed.append({"kind": "voice_template", "template_id": str(tpl.id)})
        except Exception as e:  # noqa: BLE001
            deployed.append({"kind": "voice_template", "error": str(e)[:160]})

        for a in plan["assets"]:
            try:
                row = await AIContentService.save_generated_content(
                    self.db,
                    business_id=ident.business_id,
                    content_type=a["content_type"][:50],
                    generated_content=a["content"],
                )
                deployed.append({"kind": a["content_type"], "content_id": str(row.id)})
            except Exception as e:  # noqa: BLE001
                deployed.append({"kind": a["content_type"], "error": str(e)[:160]})

        try:
            ident.deployed_assets = (ident.deployed_assets or []) + deployed
            await self.db.commit()
        except Exception as e:  # noqa: BLE001
            await self.db.rollback()
            plan["writeback_error"] = str(e)[:160]

        plan["deployed"] = deployed
        plan["created_count"] = sum(1 for d in deployed if d.get("content_id") or d.get("template_id"))
        return plan
