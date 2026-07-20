"""Market Analyst Service"""

import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.logger import get_logger
from app.domains.agents.market_analyst.models import MarketAnalysisJob, CompetitorSnapshot
from app.domains.agents.llm_provider import generate_with_fallback
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)


async def _scrape_with_httpx(url: str) -> Dict[str, Any]:
    """Scrapeo rápido con httpx (sin JS)."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9",
            }
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            text = resp.text
            return {
                "url": url,
                "status": resp.status_code,
                "title": _extract_title(text),
                "text_preview": text[:8000],
                "method": "httpx",
            }
    except Exception as e:
        logger.warning(f"httpx scrape failed for {url}: {e}")
        return {"url": url, "error": str(e), "method": "httpx"}


def _extract_title(html: str) -> Optional[str]:
    import re
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


async def _scrape_with_browser(url: str) -> Dict[str, Any]:
    """Scrapeo con BrowserService (Playwright) para JS-heavy sites."""
    try:
        from app.domains.computer_use.browser_service import BrowserService
        browser = BrowserService()
        await browser.start(headless=True)
        await browser.navigate(url)
        # Esperar carga básica
        await browser._page.wait_for_load_state("networkidle", timeout=10000)
        title = await browser._page.title()
        text = await browser._page.inner_text("body")
        await browser.stop()
        return {
            "url": url,
            "title": title,
            "text_preview": text[:12000],
            "method": "browser",
        }
    except Exception as e:
        logger.warning(f"Browser scrape failed for {url}: {e}")
        return {"url": url, "error": str(e), "method": "browser"}


async def _analyze_competitor_with_llm(
    db: AsyncSession,
    business_id: uuid.UUID,
    competitor: Dict[str, Any],
    scrape_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Usa LLM para extraer pricing, features, strengths, weaknesses."""
    ctx = await get_agent_prompt_context(db, business_id)
    context_block = format_business_context_for_prompt(ctx)

    system = SystemMessage(
        content=(
            "Eres un analista de mercado senior. Analiza el siguiente competidor "
            "desde la perspectiva del negocio del cliente. "
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{"price_range": "...", "key_features": ["..."], "strengths": ["..."], '
            '"weaknesses": ["..."], "sentiment_score": 0.0}\n'
            "sentiment_score debe estar entre -1.0 y 1.0."
        )
    )
    human = HumanMessage(
        content=(
            f"{context_block}\n\n"
            f"Competidor a analizar: {competitor.get('name')}\n"
            f"URL: {competitor.get('url', 'N/A')}\n"
            f"Título página: {scrape_data.get('title', 'N/A')}\n"
            f"Contenido preview:\n{scrape_data.get('text_preview', '')[:6000]}"
        )
    )
    response = await generate_with_fallback(
        db=db,
        business_id=business_id,
        messages=[system, human],
        temperature=0.3,
        max_tokens=2000,
    )
    if not response:
        return {
            "price_range": None,
            "key_features": [],
            "strengths": [],
            "weaknesses": [],
            "sentiment_score": 0.0,
        }
    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        logger.warning(f"Failed to parse LLM competitor analysis: {e}")
        return {
            "price_range": None,
            "key_features": [],
            "strengths": [],
            "weaknesses": [],
            "sentiment_score": 0.0,
        }


async def _generate_market_report_with_llm(
    db: AsyncSession,
    business_id: uuid.UUID,
    target_market: str,
    snapshots_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Genera reporte estructurado con gaps, oportunidades y trends."""
    ctx = await get_agent_prompt_context(db, business_id)
    context_block = format_business_context_for_prompt(ctx)

    system = SystemMessage(
        content=(
            "Eres un estratega de mercado. Genera un análisis en español "
            "personalizado para el negocio del cliente. "
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{"trends": [{"name": "...", "description": "...", "impact": "high|medium|low"}], '
            '"gaps": [{"area": "...", "description": "...", "opportunity_size": "..."}], '
            '"opportunities": [{"title": "...", "description": "...", "recommended_action": "..."}], '
            '"charts_data": {"sentiment_distribution": [...], "feature_comparison": [...]}}'
        )
    )
    human = HumanMessage(
        content=(
            f"{context_block}\n\n"
            f"Mercado objetivo: {target_market}\n"
            f"Competidores analizados ({len(snapshots_data)}):\n"
            f"{json.dumps(snapshots_data, ensure_ascii=False, indent=2)[:8000]}"
        )
    )
    response = await generate_with_fallback(
        db=db,
        business_id=business_id,
        messages=[system, human],
        temperature=0.4,
        max_tokens=2500,
    )
    if not response:
        return {
            "trends": [],
            "gaps": [],
            "opportunities": [],
            "charts_data": {},
        }
    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        logger.warning(f"Failed to parse LLM market report: {e}")
        return {
            "trends": [],
            "gaps": [],
            "opportunities": [],
            "charts_data": {},
        }


async def run_market_analysis(
    db: AsyncSession,
    business_id: uuid.UUID,
    target_market: str,
    competitors_list: List[Dict[str, Any]],
) -> MarketAnalysisJob:
    """Orquesta el análisis completo de mercado."""
    job = MarketAnalysisJob(
        business_id=business_id,
        status="running",
        target_market=target_market,
        competitors_analyzed=0,
        trends_found=0,
        report_data={},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    snapshots_data: List[Dict[str, Any]] = []
    try:
        for competitor in competitors_list:
            url = competitor.get("url")
            name = competitor.get("name", "Unknown")
            # 1. Scrapeo
            if url:
                scrape_data = await _scrape_with_httpx(url)
                if "error" in scrape_data:
                    scrape_data = await _scrape_with_browser(url)
            else:
                scrape_data = {"url": None, "title": name, "text_preview": "", "method": "none"}

            # 2. Análisis LLM
            llm_analysis = await _analyze_competitor_with_llm(db, business_id, competitor, scrape_data)

            snapshot = CompetitorSnapshot(
                job_id=job.id,
                name=name,
                url=url,
                price_range=llm_analysis.get("price_range"),
                key_features=llm_analysis.get("key_features", []),
                strengths=llm_analysis.get("strengths", []),
                weaknesses=llm_analysis.get("weaknesses", []),
                sentiment_score=llm_analysis.get("sentiment_score"),
                raw_data=scrape_data,
            )
            db.add(snapshot)
            snapshots_data.append({
                "name": name,
                "price_range": llm_analysis.get("price_range"),
                "key_features": llm_analysis.get("key_features", []),
                "strengths": llm_analysis.get("strengths", []),
                "weaknesses": llm_analysis.get("weaknesses", []),
                "sentiment_score": llm_analysis.get("sentiment_score"),
            })

        job.competitors_analyzed = len(competitors_list)
        await db.commit()

        # 3. Reporte consolidado
        report = await _generate_market_report_with_llm(db, business_id, target_market, snapshots_data)
        job.report_data = report
        job.trends_found = len(report.get("trends", []))
        job.status = "completed"
        await db.commit()
        await db.refresh(job)

    except Exception as e:
        logger.error(f"Market analysis failed for job {job.id}: {e}")
        job.status = "failed"
        job.report_data = {"error": str(e)}
        await db.commit()
        await db.refresh(job)

    return job


async def get_market_report(db: AsyncSession, job_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Retorna el reporte completo con snapshots y charts data."""
    result = await db.execute(
        select(MarketAnalysisJob).where(MarketAnalysisJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return None

    result_snaps = await db.execute(
        select(CompetitorSnapshot).where(CompetitorSnapshot.job_id == job_id)
    )
    snapshots = result_snaps.scalars().all()

    return {
        "job_id": job.id,
        "target_market": job.target_market,
        "status": job.status,
        "competitors": [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "price_range": s.price_range,
                "key_features": s.key_features,
                "strengths": s.strengths,
                "weaknesses": s.weaknesses,
                "sentiment_score": float(s.sentiment_score) if s.sentiment_score is not None else None,
                "created_at": s.created_at,
            }
            for s in snapshots
        ],
        "trends": job.report_data.get("trends", []),
        "gaps": job.report_data.get("gaps", []),
        "opportunities": job.report_data.get("opportunities", []),
        "charts_data": job.report_data.get("charts_data", {}),
        "generated_at": job.updated_at,
    }


async def list_jobs(db: AsyncSession, business_id: uuid.UUID) -> List[MarketAnalysisJob]:
    result = await db.execute(
        select(MarketAnalysisJob)
        .where(MarketAnalysisJob.business_id == business_id)
        .order_by(desc(MarketAnalysisJob.created_at))
    )
    return result.scalars().all()
