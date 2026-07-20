"""Brand Visual Agent Service

Handles brand kit generation via DALL-E 3 / Stable Diffusion.
"""

import uuid
import json
import zipfile
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.agents.brand_visual.models import BrandKitJob, BrandAsset
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[4] / "storage" / "media" / "brand"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class BrandVisualService:
    """Service layer for brand visual generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_brand_kit(
        self,
        business_id: uuid.UUID,
        brand_name: str,
        industry: str,
        style_preferences: Optional[Dict[str, Any]] = None,
    ) -> BrandKitJob:
        """Generate a complete brand kit."""
        settings = get_settings()
        style_preferences = style_preferences or {}

        job = BrandKitJob(
            business_id=business_id,
            brand_name=brand_name,
            industry=industry,
            status="processing",
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        assets: List[BrandAsset] = []

        # 1. Generate 3 logo concepts via DALL-E 3
        logo_urls = await self._generate_logos(
            brand_name, industry, style_preferences, settings
        )
        for idx, logo_url in enumerate(logo_urls, 1):
            assets.append(
                BrandAsset(
                    job_id=job.id,
                    business_id=business_id,
                    asset_type="logo",
                    file_url=logo_url,
                    config={"concept": idx, "format": "png"},
                )
            )

        if logo_urls:
            job.logo_url = logo_urls[0]

        # 2. Generate color palette
        colors = await self._generate_color_palette(
            business_id, brand_name, industry, style_preferences, settings
        )
        job.colors = colors

        # 3. Generate typography recommendations
        fonts = await self._generate_typography(
            business_id, brand_name, industry, style_preferences, settings
        )
        job.fonts = fonts

        # 4. Generate social media templates
        template_platforms = ["instagram", "linkedin", "tiktok"]
        for platform in template_platforms:
            tpl_url = await self._generate_social_template(
                brand_name, industry, platform, colors, settings
            )
            assets.append(
                BrandAsset(
                    job_id=job.id,
                    business_id=business_id,
                    asset_type="social_template",
                    file_url=tpl_url,
                    config={"platform": platform, "format": "png"},
                )
            )

        # 5. Generate product mockup
        mockup_url = await self._generate_mockup(
            brand_name, industry, style_preferences, settings
        )
        assets.append(
            BrandAsset(
                job_id=job.id,
                business_id=business_id,
                asset_type="mockup",
                file_url=mockup_url,
                config={"format": "png"},
            )
        )

        # 6. Generate brand guidelines (markdown)
        guidelines_path = STORAGE_DIR / f"guidelines_{job.id}.md"
        guidelines_content = self._build_guidelines(
            brand_name, industry, colors, fonts, logo_urls
        )
        guidelines_path.write_text(guidelines_content, encoding="utf-8")
        assets.append(
            BrandAsset(
                job_id=job.id,
                business_id=business_id,
                asset_type="guideline",
                file_url=f"/storage/media/brand/guidelines_{job.id}.md",
                config={"format": "markdown"},
            )
        )

        for asset in assets:
            self.db.add(asset)

        job.assets = {
            "logos": logo_urls,
            "templates": [a.file_url for a in assets if a.asset_type == "social_template"],
            "mockups": [a.file_url for a in assets if a.asset_type == "mockup"],
            "guidelines": f"/storage/media/brand/guidelines_{job.id}.md",
        }
        job.status = "completed"
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_brand_kit(self, job_id: uuid.UUID) -> Optional[BrandKitJob]:
        result = await self.db.execute(
            select(BrandKitJob).where(BrandKitJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_kits(self, business_id: uuid.UUID) -> List[BrandKitJob]:
        result = await self.db.execute(
            select(BrandKitJob)
            .where(BrandKitJob.business_id == business_id)
            .order_by(desc(BrandKitJob.created_at))
        )
        return result.scalars().all()

    async def get_assets(self, job_id: uuid.UUID) -> List[BrandAsset]:
        result = await self.db.execute(
            select(BrandAsset).where(BrandAsset.job_id == job_id)
        )
        return result.scalars().all()

    async def build_zip(self, job_id: uuid.UUID) -> bytes:
        """Build a ZIP archive of all brand assets."""
        assets = await self.get_assets(job_id)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for asset in assets:
                local_path = STORAGE_DIR / Path(asset.file_url).name
                if local_path.exists():
                    zf.write(local_path, arcname=f"{asset.asset_type}/{local_path.name}")
                else:
                    # For remote URLs, add a text reference
                    zf.writestr(
                        f"{asset.asset_type}/{asset.asset_type}_{asset.id}.txt",
                        asset.file_url,
                    )
        buffer.seek(0)
        return buffer.read()

    # ------------------------------------------------------------------
    # Generation helpers
    # ------------------------------------------------------------------

    async def _generate_logos(
        self,
        brand_name: str,
        industry: str,
        style_preferences: Dict[str, Any],
        settings: Any,
    ) -> List[str]:
        urls: List[str] = []
        style = style_preferences.get("style", "modern minimalistic")
        for idx in range(1, 4):
            prompt = (
                f"Professional logo design for '{brand_name}', {industry} industry. "
                f"Style: {style}. Concept variation {idx}. Clean vector look, "
                f"white background, high resolution, no text except brand name."
            )
            url = await self._generate_image(prompt, settings, f"logo_{idx}")
            if url:
                urls.append(url)
        if not urls:
            urls = ["/storage/media/brand/placeholder_logo.png"]
        return urls

    async def _generate_color_palette(
        self,
        business_id: uuid.UUID,
        brand_name: str,
        industry: str,
        style_preferences: Dict[str, Any],
        settings: Any,
    ) -> List[Dict[str, str]]:
        """Generate a 5-color palette. Uses OpenAI if available, else heuristic."""
        ctx = await get_agent_prompt_context(self.db, business_id)
        context_block = format_business_context_for_prompt(ctx)

        if settings.OPENAI_API_KEY:
            try:
                user_content = (
                    f"Brand: {brand_name}, Industry: {industry}. "
                    f"Generate a cohesive color palette."
                )
                if context_block:
                    user_content = f"{context_block}\n\n{user_content}"
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "Return ONLY a JSON array of 5 colors for a brand palette. "
                                        "Each object must have 'name' and 'hex'. No markdown."
                                    ),
                                },
                                {
                                    "role": "user",
                                    "content": user_content,
                                },
                            ],
                            "temperature": 0.7,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"OpenAI palette generation failed: {e}")

        # Fallback palette
        return [
            {"name": "Primary", "hex": "#1E3A8A"},
            {"name": "Secondary", "hex": "#3B82F6"},
            {"name": "Accent", "hex": "#F59E0B"},
            {"name": "Neutral", "hex": "#6B7280"},
            {"name": "Background", "hex": "#F3F4F6"},
        ]

    async def _generate_typography(
        self,
        business_id: uuid.UUID,
        brand_name: str,
        industry: str,
        style_preferences: Dict[str, Any],
        settings: Any,
    ) -> List[Dict[str, Any]]:
        """Return typography recommendations."""
        ctx = await get_agent_prompt_context(self.db, business_id)
        context_block = format_business_context_for_prompt(ctx)

        if settings.OPENAI_API_KEY:
            try:
                user_content = (
                    f"Brand: {brand_name}, Industry: {industry}. "
                    f"Suggest typography pairings."
                )
                if context_block:
                    user_content = f"{context_block}\n\n{user_content}"
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "Return ONLY a JSON array of 3 font recommendations. "
                                        "Each object: {name, category, usage, weights: []}. "
                                        "No markdown."
                                    ),
                                },
                                {
                                    "role": "user",
                                    "content": user_content,
                                },
                            ],
                            "temperature": 0.7,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"OpenAI typography generation failed: {e}")

        return [
            {"name": "Inter", "category": "sans-serif", "usage": "Headings & UI", "weights": [400, 600, 700]},
            {"name": "Merriweather", "category": "serif", "usage": "Body text", "weights": [400, 700]},
            {"name": "JetBrains Mono", "category": "monospace", "usage": "Code & data", "weights": [400]},
        ]

    async def _generate_social_template(
        self,
        brand_name: str,
        industry: str,
        platform: str,
        colors: List[Dict[str, str]],
        settings: Any,
    ) -> str:
        primary_color = colors[0]["hex"] if colors else "#1E3A8A"
        prompt = (
            f"Social media post template for {platform}, brand '{brand_name}', "
            f"{industry} industry. Primary color {primary_color}. "
            f"Clean layout with space for headline and body text. Modern design."
        )
        return await self._generate_image(prompt, settings, f"template_{platform}") or ""

    async def _generate_mockup(
        self,
        brand_name: str,
        industry: str,
        style_preferences: Dict[str, Any],
        settings: Any,
    ) -> str:
        prompt = (
            f"Product mockup for '{brand_name}', {industry} industry. "
            f"Realistic 3D render on neutral background. Professional photography style."
        )
        return await self._generate_image(prompt, settings, "mockup") or ""

    async def _generate_image(self, prompt: str, settings: Any, suffix: str) -> Optional[str]:
        """Generate image via DALL-E 3 or Stable Diffusion fallback."""
        job_id = uuid.uuid4()
        file_name = f"brand_{job_id}_{suffix}.png"
        file_path = STORAGE_DIR / file_name

        # Primary: DALL-E 3 (OpenAI)
        if settings.OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "dall-e-3",
                            "prompt": prompt,
                            "n": 1,
                            "size": "1024x1024",
                            "response_format": "url",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    image_url = data["data"][0]["url"]
                    # Download and store locally
                    img_resp = await client.get(image_url, timeout=httpx.Timeout(60.0))
                    img_resp.raise_for_status()
                    with open(file_path, "wb") as f:
                        f.write(img_resp.content)
                    return f"/storage/media/brand/{file_name}"
            except Exception as e:
                logger.warning(f"DALL-E 3 generation failed: {e}")

        # Fallback: Stable Diffusion via Stability AI
        if settings.STABILITY_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                    response = await client.post(
                        "https://api.stability.ai/v2beta/stable-image/generate/core",
                        headers={
                            "authorization": settings.STABILITY_API_KEY,
                            "accept": "image/*",
                        },
                        files={"none": ("", "")},
                        data={
                            "prompt": prompt,
                            "output_format": "png",
                        },
                    )
                    response.raise_for_status()
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    return f"/storage/media/brand/{file_name}"
            except Exception as e:
                logger.warning(f"Stable Diffusion generation failed: {e}")

        # Development fallback
        logger.info("Image generation fallback: returning placeholder")
        return "/storage/media/brand/placeholder.png"

    def _build_guidelines(
        self,
        brand_name: str,
        industry: str,
        colors: List[Dict[str, str]],
        fonts: List[Dict[str, Any]],
        logo_urls: List[str],
    ) -> str:
        lines = [
            f"# Brand Guidelines — {brand_name}",
            f"",
            f"## Industry",
            f"{industry}",
            f"",
            f"## Color Palette",
        ]
        for c in colors:
            lines.append(f"- **{c.get('name', 'Color')}**: {c.get('hex', '')}")
        lines.append("")
        lines.append("## Typography")
        for f in fonts:
            lines.append(f"- **{f.get('name', '')}** ({f.get('category', '')}) — {f.get('usage', '')}")
        lines.append("")
        lines.append("## Logos")
        for idx, url in enumerate(logo_urls, 1):
            lines.append(f"- Concept {idx}: {url}")
        lines.append("")
        lines.append("---")
        lines.append("Generated by SellIA Brand Visual Agent")
        return "\n".join(lines)
