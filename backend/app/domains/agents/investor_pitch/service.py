import uuid
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger
from app.domains.agents.investor_pitch.models import PitchDeck, PitchSlide
from app.domains.businesses.models import Business
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)


class InvestorPitchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_pitch_deck(self, business_id: uuid.UUID) -> PitchDeck:
        business = await self.db.get(Business, business_id)
        if not business:
            raise ValueError("Business not found")

        metrics = await self._extract_metrics(business)

        deck = PitchDeck(
            business_id=business_id,
            title=f"{business.name} — Pitch Deck",
            metrics=metrics,
            status="generated",
        )
        self.db.add(deck)
        await self.db.commit()
        await self.db.refresh(deck)

        slides = await self._generate_slides(business, deck, metrics)
        for slide in slides:
            self.db.add(slide)
        await self.db.commit()

        html_path = await self._generate_html_deck(deck, slides)
        deck.html_url = html_path
        await self.db.commit()

        logger.info(f"Pitch deck {deck.id} generated with {len(slides)} slides")
        return deck

    async def _extract_metrics(self, business: Business) -> Dict[str, Any]:
        config = business.config or {}
        return {
            "mrr": config.get("mrr", 15000),
            "growth_rate": config.get("growth_rate", 25),
            "tam": config.get("tam", 5000000),
            "team_size": config.get("team_size", 4),
            "traction": config.get("traction", "500+ clientes activos"),
            "cac": config.get("cac", 45),
            "ltv": config.get("ltv", 320),
        }

    async def _generate_slides(
        self,
        business: Business,
        deck: PitchDeck,
        metrics: Dict[str, Any],
    ) -> List[PitchSlide]:
        ctx = await get_agent_prompt_context(self.db, business.id)
        context_block = format_business_context_for_prompt(ctx)

        slide_definitions = [
            {"number": 1, "title": "Problem", "prompt": f"Describe el problema principal que resuelve {business.name} en 2-3 oraciones."},
            {"number": 2, "title": "Solution", "prompt": f"Describe la solución de {business.name}. {business.description or ''}"},
            {"number": 3, "title": "Product", "prompt": f"Describe el producto/servicio principal de {business.name}."},
            {"number": 4, "title": "Market", "prompt": f"TAM: ${metrics['tam']:,}. Describe el tamaño de mercado y oportunidad."},
            {"number": 5, "title": "Traction", "prompt": f"Traction: {metrics['traction']}. Resume métricas clave de crecimiento."},
            {"number": 6, "title": "Business Model", "prompt": f"MRR: ${metrics['mrr']:,}. CAC: ${metrics['cac']}. LTV: ${metrics['ltv']}. Explica el modelo de negocio."},
            {"number": 7, "title": "Competition", "prompt": f"Analiza 2-3 competidores y la ventaja diferencial de {business.name}."},
            {"number": 8, "title": "Go-to-Market", "prompt": f"Estrategia de adquisición y canales principales de {business.name}."},
            {"number": 9, "title": "Team", "prompt": f"Equipo de {metrics['team_size']} personas. Describe el equipo fundador."},
            {"number": 10, "title": "Financials", "prompt": f"Crecimiento: {metrics['growth_rate']}% MoM. Proyecta ingresos 3 años."},
            {"number": 11, "title": "The Ask", "prompt": f"Define la ronda de inversión buscada y uso de fondos para {business.name}."},
            {"number": 12, "title": "Contact", "prompt": f"Información de contacto para invertir en {business.name}."},
        ]

        slides = []
        for sd in slide_definitions:
            user_prompt = sd["prompt"]
            if context_block:
                user_prompt = f"{context_block}\n\n{user_prompt}"
            content = await generate_raw_ai_response(
                db=self.db,
                business_id=business.id,
                system_prompt="Eres un experto en creación de pitch decks para inversores. Genera contenido claro, conciso y convincente.",
                user_prompt=user_prompt,
                max_tokens=600,
                temperature=0.7,
            ) or "Contenido pendiente."

            chart_data = {}
            if sd["title"] == "Financials":
                chart_data = {
                    "type": "bar",
                    "labels": ["Año 1", "Año 2", "Año 3"],
                    "datasets": [
                        {
                            "label": "Ingresos proyectados ($)",
                            "data": [
                                int(metrics["mrr"] * 12),
                                int(metrics["mrr"] * 12 * 1.5),
                                int(metrics["mrr"] * 12 * 2.5),
                            ],
                        }
                    ],
                }
            elif sd["title"] == "Traction":
                chart_data = {
                    "type": "line",
                    "labels": ["M1", "M3", "M6", "M9", "M12"],
                    "datasets": [
                        {
                            "label": "Clientes",
                            "data": [50, 120, 250, 380, 500],
                        }
                    ],
                }

            slides.append(
                PitchSlide(
                    deck_id=deck.id,
                    slide_number=sd["number"],
                    title=sd["title"],
                    content=content,
                    chart_data=chart_data,
                    notes="",
                )
            )
        return slides

    async def _generate_html_deck(self, deck: PitchDeck, slides: List[PitchSlide]) -> str:
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="es">',
            "<head>",
            '<meta charset="UTF-8">',
            "<title>" + deck.title + "</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #0f172a; color: #f8fafc; }",
            ".slide { min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 60px; box-sizing: border-box; border-bottom: 1px solid #334155; }",
            "h1 { font-size: 48px; margin-bottom: 24px; }",
            "h2 { font-size: 36px; margin-bottom: 16px; color: #38bdf8; }",
            "p { font-size: 24px; line-height: 1.6; max-width: 800px; }",
            ".chart { margin-top: 24px; font-size: 18px; color: #94a3b8; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        for slide in sorted(slides, key=lambda s: s.slide_number):
            html_parts.append('<div class="slide">')
            html_parts.append(f"<h2>{slide.slide_number}. {slide.title}</h2>")
            html_parts.append(f"<p>{slide.content.replace(chr(10), '<br>')}</p>")
            if slide.chart_data:
                html_parts.append(f'<pre class="chart">{json.dumps(slide.chart_data, ensure_ascii=False, indent=2)}</pre>')
            html_parts.append("</div>")

        html_parts.extend(["</body>", "</html>"])

        storage_dir = os.path.join(os.getcwd(), "storage", "exports", "pitch_decks")
        os.makedirs(storage_dir, exist_ok=True)
        html_path = os.path.join(storage_dir, f"deck_{deck.id}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))

        return html_path

    async def export_pdf(self, deck_id: uuid.UUID, business_id: uuid.UUID) -> str:
        deck = await self.db.get(PitchDeck, deck_id)
        if not deck or deck.business_id != business_id:
            raise ValueError("Deck not found")

        slides_result = await self.db.execute(
            select(PitchSlide).where(PitchSlide.deck_id == deck_id).order_by(PitchSlide.slide_number)
        )
        slides = slides_result.scalars().all()

        html_content = await self._build_html_for_pdf(deck, slides)
        storage_dir = os.path.join(os.getcwd(), "storage", "exports", "pitch_decks")
        os.makedirs(storage_dir, exist_ok=True)
        pdf_path = os.path.join(storage_dir, f"deck_{deck_id}.pdf")

        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(html_content)
            await page.pdf(
                path=pdf_path,
                format="A4",
                margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"},
                print_background=True,
            )
            await browser.close()

        deck.pdf_url = pdf_path
        await self.db.commit()
        logger.info(f"PDF exported: {pdf_path}")
        return pdf_path

    async def _build_html_for_pdf(self, deck: PitchDeck, slides: List[PitchSlide]) -> str:
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="es">',
            "<head>",
            '<meta charset="UTF-8">',
            "<title>" + deck.title + "</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #fff; color: #1e293b; }",
            ".slide { page-break-after: always; padding: 40px; }",
            "h2 { font-size: 28px; color: #1e40af; }",
            "p { font-size: 18px; line-height: 1.5; }",
            ".chart { margin-top: 16px; font-size: 14px; color: #475569; }",
            "</style>",
            "</head>",
            "<body>",
        ]
        for slide in slides:
            html_parts.append('<div class="slide">')
            html_parts.append(f"<h2>{slide.slide_number}. {slide.title}</h2>")
            html_parts.append(f"<p>{slide.content.replace(chr(10), '<br>')}</p>")
            if slide.chart_data:
                html_parts.append(f'<pre class="chart">{json.dumps(slide.chart_data, ensure_ascii=False, indent=2)}</pre>')
            html_parts.append("</div>")
        html_parts.extend(["</body>", "</html>"])
        return "\n".join(html_parts)

    async def list_decks(self, business_id: uuid.UUID, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        result = await self.db.execute(
            select(PitchDeck).where(PitchDeck.business_id == business_id)
        )
        decks = result.scalars().all()
        return {"total": len(decks), "decks": decks[offset:offset + limit]}

    async def get_deck(self, deck_id: uuid.UUID, business_id: uuid.UUID) -> Optional[PitchDeck]:
        deck = await self.db.get(PitchDeck, deck_id)
        if not deck or deck.business_id != business_id:
            return None
        return deck

    async def get_deck_with_slides(self, deck_id: uuid.UUID, business_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        deck = await self.get_deck(deck_id, business_id)
        if not deck:
            return None
        result = await self.db.execute(
            select(PitchSlide).where(PitchSlide.deck_id == deck_id).order_by(PitchSlide.slide_number)
        )
        slides = result.scalars().all()
        return {"deck": deck, "slides": slides}
