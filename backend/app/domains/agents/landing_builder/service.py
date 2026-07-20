"""Landing Page Builder Service"""

import uuid
import json
import os
import zipfile
import io
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.logger import get_logger
from app.core.config import get_settings
from app.domains.agents.landing_builder.models import LandingPageJob
from app.domains.agents.llm_provider import generate_with_fallback
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)
settings = get_settings()


def _get_storage_dir() -> str:
    base = os.path.join(os.getcwd(), "storage", "exports", "landing_pages")
    os.makedirs(base, exist_ok=True)
    return base


async def _fetch_product_data(db: AsyncSession, product_id: Optional[uuid.UUID]) -> Dict[str, Any]:
    if not product_id:
        return {}
    from app.domains.catalogs.models import CatalogItem
    result = await db.execute(select(CatalogItem).where(CatalogItem.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return {}
    return {
        "name": product.name,
        "description": product.description,
        "price": str(product.price) if product.price else None,
        "currency": product.currency,
        "images": product.images,
        "tags": product.tags,
    }


async def _generate_copy_with_llm(
    db: AsyncSession,
    business_id: uuid.UUID,
    product_data: Dict[str, Any],
    style: str,
    variant_name: str,
) -> Dict[str, Any]:
    ctx = await get_agent_prompt_context(db, business_id)
    context_block = format_business_context_for_prompt(ctx)

    system = SystemMessage(
        content=(
            "Eres un copywriter de conversiones y un desarrollador frontend senior. "
            "Genera copy persuasivo y código React/Next.js + Tailwind CSS en español "
            "personalizado para el negocio del cliente. "
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{"headline": "...", "subheadline": "...", "cta_text": "...", '
            '"features": [{"title": "...", "description": "..."}], '
            '"testimonials": [{"quote": "...", "author": "..."}], '
            '"faq": [{"question": "...", "answer": "..."}], '
            '"pricing_section": {"headline": "...", "plans": [{"name": "...", "price": "...", "features": ["..."]}]}, '
            '"color_scheme": {"primary": "#3B82F6", "secondary": "#10B981", "background": "#F9FAFB", "text": "#111827"}}'
        )
    )
    human_content = (
        f"Estilo: {style}\nVariante: {variant_name}\n"
        f"Producto: {json.dumps(product_data, ensure_ascii=False, indent=2)}\n"
        "Genera el copy y el esquema de colores para una landing page de alto rendimiento."
    )
    if context_block:
        human_content = f"{context_block}\n\n{human_content}"
    human = HumanMessage(content=human_content)
    response = await generate_with_fallback(
        db=db,
        business_id=business_id,
        messages=[system, human],
        temperature=0.6,
        max_tokens=2500,
    )
    if not response:
        return {
            "headline": "Bienvenido",
            "subheadline": "Descubre nuestra solución",
            "cta_text": "Comenzar ahora",
            "features": [],
            "testimonials": [],
            "faq": [],
            "pricing_section": {},
            "color_scheme": {"primary": "#3B82F6", "secondary": "#10B981", "background": "#F9FAFB", "text": "#111827"},
        }
    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        logger.warning(f"Failed to parse landing copy LLM output: {e}")
        return {
            "headline": "Bienvenido",
            "subheadline": "Descubre nuestra solución",
            "cta_text": "Comenzar ahora",
            "features": [],
            "testimonials": [],
            "faq": [],
            "pricing_section": {},
            "color_scheme": {"primary": "#3B82F6", "secondary": "#10B981", "background": "#F9FAFB", "text": "#111827"},
        }


def _build_nextjs_page(copy: Dict[str, Any], product_data: Dict[str, Any], variant_name: str) -> str:
    """Construye una página Next.js + Tailwind básica a partir del copy."""
    cs = copy.get("color_scheme", {})
    primary = cs.get("primary", "#3B82F6")
    secondary = cs.get("secondary", "#10B981")
    bg = cs.get("background", "#F9FAFB")
    text = cs.get("text", "#111827")

    features = copy.get("features", [])
    testimonials = copy.get("testimonials", [])
    faq = copy.get("faq", [])
    pricing = copy.get("pricing_section", {})
    plans = pricing.get("plans", [])

    features_html = "\n".join(
        f"""      <div className=\"p-6 bg-white rounded-2xl shadow-sm\">
        <h3 className=\"text-lg font-semibold mb-2\" style={{{{color: '{primary}'}}}}>{f.get('title', '')}</h3>
        <p className=\"text-gray-600\">{f.get('description', '')}</p>
      </div>"""
        for f in features
    ) or '<p className="text-gray-600">Próximamente más información.</p>'

    testimonials_html = "\n".join(
        f"""      <blockquote className=\"p-6 bg-white rounded-2xl shadow-sm\">
        <p className=\"italic text-gray-700 mb-4\">&quot;{t.get('quote', '')}&quot;</p>
        <footer className=\"text-sm font-semibold\" style={{{{color: '{primary}'}}}}>— {t.get('author', '')}</footer>
      </blockquote>"""
        for t in testimonials
    ) or ''

    faq_html = "\n".join(
        f"""      <details className=\"group bg-white rounded-xl p-4 shadow-sm\">
        <summary className=\"font-semibold cursor-pointer\" style={{{{color: '{primary}'}}}}>{q.get('question', '')}</summary>
        <p className=\"mt-2 text-gray-600\">{q.get('answer', '')}</p>
      </details>"""
        for q in faq
    ) or ''

    plans_html = "\n".join(
        f"""      <div className=\"p-6 bg-white rounded-2xl shadow-sm border-t-4\" style={{{{borderColor: '{primary}'}}}}>
        <h3 className=\"text-xl font-bold mb-2\">{p.get('name', '')}</h3>
        <p className=\"text-2xl font-extrabold mb-4\" style={{{{color: '{primary}'}}}}>{p.get('price', '')}</p>
        <ul className=\"space-y-2 text-gray-600\">
          {' '.join(f'<li>• {feat}</li>' for feat in p.get('features', []))}
        </ul>
      </div>"""
        for p in plans
    ) or ''

    return f"""'use client';
import React from 'react';

export default function LandingPage() {{
  return (
    <main className="min-h-screen" style={{{{backgroundColor: '{bg}', color: '{text}'}}}}>
      {{/* Hero */}}
      <section className="relative px-6 py-20 md:py-32 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-6">
            {copy.get('headline', 'Bienvenido')}
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            {copy.get('subheadline', 'Descubre nuestra solución')}
          </p>
          <button
            className="inline-flex items-center px-8 py-4 rounded-full text-white font-semibold shadow-lg transition-transform hover:scale-105"
            style={{{{backgroundColor: primary}}}}
          >
            {copy.get('cta_text', 'Comenzar ahora')}
          </button>
        </div>
      </section>

      {{/* Features */}}
      <section className="px-6 py-16">
        <div className="max-w-6xl mx-auto grid gap-6 md:grid-cols-3">
{features_html}
        </div>
      </section>

      {{/* Social Proof */}}
      {testimonials_html and f"""<section className="px-6 py-16">
        <div className="max-w-6xl mx-auto grid gap-6 md:grid-cols-2">
{testimonials_html}
        </div>
      </section>"""}

      {{/* Pricing */}}
      {plans_html and f"""<section className="px-6 py-16">
        <div className="max-w-4xl mx-auto text-center mb-10">
          <h2 className="text-3xl font-bold">{pricing.get('headline', 'Precios')}</h2>
        </div>
        <div className="max-w-6xl mx-auto grid gap-6 md:grid-cols-3">
{plans_html}
        </div>
      </section>"""}

      {{/* FAQ */}}
      {faq_html and f"""<section className="px-6 py-16">
        <div className="max-w-3xl mx-auto space-y-4">
{faq_html}
        </div>
      </section>"""}

      {{/* CTA */}}
      <section className="px-6 py-20 text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            ¿Listo para empezar?
          </h2>
          <button
            className="inline-flex items-center px-8 py-4 rounded-full text-white font-semibold shadow-lg transition-transform hover:scale-105"
            style={{{{backgroundColor: secondary}}}}
          >
            {copy.get('cta_text', 'Comenzar ahora')}
          </button>
        </div>
      </section>
    </main>
  );
}}
"""


async def generate_landing_page(
    db: AsyncSession,
    business_id: uuid.UUID,
    product_id: Optional[uuid.UUID],
    style: str = "modern",
) -> LandingPageJob:
    """Genera una landing page con variantes A/B."""
    job = LandingPageJob(
        business_id=business_id,
        status="running",
        product_id=product_id,
        template_used=style,
        variants=[],
        generated_code={},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    try:
        product_data = await _fetch_product_data(db, product_id)

        variants: List[Dict[str, Any]] = []
        files: Dict[str, str] = {}

        variant_names = ["Variante A (Directa)", "Variante B (Emocional)", "Variante C (Social Proof)"]
        for variant_name in variant_names:
            copy = await _generate_copy_with_llm(db, business_id, product_data, style, variant_name)
            code = _build_nextjs_page(copy, product_data, variant_name)
            safe_name = variant_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
            files[f"pages/{safe_name}/page.tsx"] = code
            variants.append({
                "variant_name": variant_name,
                "headline": copy.get("headline", ""),
                "subheadline": copy.get("subheadline", ""),
                "cta_text": copy.get("cta_text", ""),
                "color_scheme": copy.get("color_scheme", {}),
                "conversion_rate": None,
            })

        # Guardar en storage
        storage_dir = _get_storage_dir()
        job_dir = os.path.join(storage_dir, str(job.id))
        os.makedirs(job_dir, exist_ok=True)

        for path, content in files.items():
            full_path = os.path.join(job_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        # ZIP
        zip_path = os.path.join(storage_dir, f"{job.id}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in files.items():
                zf.writestr(path, content)

        job.variants = variants
        job.generated_code = {"files": files}
        job.generated_code_url = f"/storage/exports/landing_pages/{job.id}.zip"
        job.preview_url = f"/storage/exports/landing_pages/{job.id}/pages/variante_a_directa/page.tsx"
        job.status = "completed"
        await db.commit()
        await db.refresh(job)

    except Exception as e:
        logger.error(f"Landing page generation failed for job {job.id}: {e}")
        job.status = "failed"
        job.generated_code = {"error": str(e)}
        await db.commit()
        await db.refresh(job)

    return job


async def get_landing_code(db: AsyncSession, job_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    result = await db.execute(select(LandingPageJob).where(LandingPageJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        return None
    return {
        "job_id": job.id,
        "files": job.generated_code.get("files", {}),
        "variants": job.variants,
    }


async def get_landing_zip(job_id: uuid.UUID) -> Optional[bytes]:
    storage_dir = _get_storage_dir()
    zip_path = os.path.join(storage_dir, f"{job_id}.zip")
    if not os.path.exists(zip_path):
        return None
    with open(zip_path, "rb") as f:
        return f.read()


async def list_jobs(db: AsyncSession, business_id: uuid.UUID) -> List[LandingPageJob]:
    result = await db.execute(
        select(LandingPageJob)
        .where(LandingPageJob.business_id == business_id)
        .order_by(desc(LandingPageJob.created_at))
    )
    return result.scalars().all()
