import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger
from app.domains.agents.ad_copywriter.models import AdCampaign, AdVariant
from app.domains.catalogs.models import CatalogItem
from app.domains.businesses.models import Business
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)


class AdCopywriterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ad_campaign(
        self,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        platform: str,
        budget: float,
        campaign_name: Optional[str] = None,
    ) -> AdCampaign:
        product = await self.db.get(CatalogItem, product_id)
        if not product or product.business_id != business_id:
            raise ValueError("Product not found")

        business = await self.db.get(Business, business_id)
        if not business:
            raise ValueError("Business not found")

        target_audience = await self._analyze_audience(business, product)

        campaign = AdCampaign(
            business_id=business_id,
            campaign_name=campaign_name or f"{product.name} - {platform}",
            platform=platform,
            objective="conversions",
            target_audience=target_audience,
            budget=budget,
            status="generated",
        )
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)

        variants = await self._generate_variants(business, product, campaign, platform)
        for variant in variants:
            self.db.add(variant)
        await self.db.commit()

        logger.info(f"Ad campaign {campaign.id} created with {len(variants)} variants")
        return campaign

    async def _analyze_audience(self, business: Business, product: CatalogItem) -> Dict[str, Any]:
        ctx = await get_agent_prompt_context(self.db, business.id)
        context_block = format_business_context_for_prompt(ctx)

        prompt = (
            f"Analiza este producto/servicio y define la audiencia objetivo ideal para anuncios pagados.\n\n"
            f"Negocio: {business.name}\n"
            f"Tipo: {business.type.value}\n"
            f"Producto: {product.name}\n"
            f"Descripción: {product.description or 'N/A'}\n"
            f"Precio: {product.price} {product.currency}\n\n"
            f"Devuelve SOLO un JSON válido con esta estructura:\n"
            f'{{"age_range": "25-45", "gender": "all", "interests": ["..."], "locations": ["..."], "pain_points": ["..."], "fomo_trigger": "urgencia"}}'
        )
        if context_block:
            prompt = f"{context_block}\n\n{prompt}"
        response = await generate_raw_ai_response(
            db=self.db,
            business_id=business.id,
            system_prompt="Eres un experto en marketing digital y segmentación de audiencias. Responde SOLO con JSON válido.",
            user_prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )
        if response:
            try:
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                return json.loads(json_str.strip())
            except Exception as e:
                logger.warning(f"Failed to parse audience JSON: {e}")
        return {
            "age_range": "25-45",
            "gender": "all",
            "interests": ["tecnología", "productividad"],
            "locations": ["Argentina"],
            "pain_points": ["ahorrar tiempo", "mejorar resultados"],
            "fomo_trigger": "oferta limitada",
        }

    async def _generate_variants(
        self,
        business: Business,
        product: CatalogItem,
        campaign: AdCampaign,
        platform: str,
    ) -> List[AdVariant]:
        ctx = await get_agent_prompt_context(self.db, business.id)
        context_block = format_business_context_for_prompt(ctx)

        fomo_context = ""
        if campaign.target_audience and isinstance(campaign.target_audience, dict):
            fomo_trigger = campaign.target_audience.get("fomo_trigger", "oferta limitada")
            fomo_context = f" Integra urgencia/FOMO usando: {fomo_trigger}."

        prompt = (
            f"Genera 5 variantes de anuncio para {platform}.\n\n"
            f"Negocio: {business.name}\n"
            f"Producto: {product.name}\n"
            f"Descripción: {product.description or 'N/A'}\n"
            f"Precio: {product.price} {product.currency}\n"
            f"{fomo_context}\n\n"
            f"Para cada variante devuelve:\n"
            f"- headline (máx 60 chars)\n"
            f"- body (2-3 oraciones, persuasivo)\n"
            f"- cta (máx 20 chars)\n"
            f"- image_prompt (descripción para generar imagen/video)\n"
            f"- targeting tweaks (intereses o demográficos específicos)\n"
            f"- predicted_ctr (estimado 0.01-0.15)\n\n"
            f"Devuelve SOLO un JSON válido con un array 'variants'."
        )
        if context_block:
            prompt = f"{context_block}\n\n{prompt}"
        response = await generate_raw_ai_response(
            db=self.db,
            business_id=business.id,
            system_prompt="Eres un copywriter senior especializado en ads de alto rendimiento. Responde SOLO con JSON válido.",
            user_prompt=prompt,
            max_tokens=2000,
            temperature=0.8,
        )
        variants = []
        if response:
            try:
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                data = json.loads(json_str.strip())
                items = data.get("variants", data if isinstance(data, list) else [])
                for idx, item in enumerate(items[:5], start=1):
                    variants.append(
                        AdVariant(
                            campaign_id=campaign.id,
                            variant_name=item.get("variant_name") or f"Variante {idx}",
                            headline=item.get("headline", "Headline"),
                            body=item.get("body", "Body"),
                            cta=item.get("cta", "Comprar ahora"),
                            image_prompt=item.get("image_prompt"),
                            targeting=item.get("targeting", {}),
                            predicted_ctr=item.get("predicted_ctr"),
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to parse variants JSON: {e}")

        if not variants:
            for i in range(1, 6):
                variants.append(
                    AdVariant(
                        campaign_id=campaign.id,
                        variant_name=f"Variante {i}",
                        headline=f"Descubre {product.name}",
                        body=f"La solución que estabas buscando. {product.description or ''}",
                        cta="Comprar ahora",
                        image_prompt=f"Imagen profesional de {product.name}",
                        targeting={},
                        predicted_ctr=0.03,
                    )
                )
        return variants

    async def list_campaigns(
        self,
        business_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        total_result = await self.db.execute(
            select(AdCampaign).where(AdCampaign.business_id == business_id)
        )
        campaigns = total_result.scalars().all()
        total = len(campaigns)
        return {"total": total, "campaigns": campaigns[offset:offset + limit]}

    async def get_campaign(self, campaign_id: uuid.UUID, business_id: uuid.UUID) -> Optional[AdCampaign]:
        campaign = await self.db.get(AdCampaign, campaign_id)
        if not campaign or campaign.business_id != business_id:
            return None
        return campaign

    async def get_campaign_with_variants(self, campaign_id: uuid.UUID, business_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        campaign = await self.get_campaign(campaign_id, business_id)
        if not campaign:
            return None
        result = await self.db.execute(
            select(AdVariant).where(AdVariant.campaign_id == campaign_id)
        )
        variants = result.scalars().all()
        return {
            "campaign": campaign,
            "variants": variants,
        }

    async def export_campaign(self, campaign_id: uuid.UUID, platform: str, business_id: uuid.UUID) -> Dict[str, Any]:
        data = await self.get_campaign_with_variants(campaign_id, business_id)
        if not data:
            raise ValueError("Campaign not found")

        campaign = data["campaign"]
        variants = data["variants"]

        if platform == "meta":
            export = {
                "campaign_name": campaign.campaign_name,
                "objective": campaign.objective,
                "adsets": [
                    {
                        "name": v.variant_name,
                        "headline": v.headline,
                        "primary_text": v.body,
                        "cta": v.cta,
                        "image_prompt": v.image_prompt,
                        "targeting": v.targeting,
                    }
                    for v in variants
                ],
            }
        elif platform == "google":
            export = {
                "campaign_name": campaign.campaign_name,
                "ads": [
                    {
                        "headline_1": v.headline,
                        "description": v.body,
                        "cta": v.cta,
                        "final_url": "",
                    }
                    for v in variants
                ],
            }
        elif platform == "tiktok":
            export = {
                "campaign_name": campaign.campaign_name,
                "ads": [
                    {
                        "ad_name": v.variant_name,
                        "text": f"{v.headline} {v.body}",
                        "cta": v.cta,
                        "video_prompt": v.image_prompt,
                    }
                    for v in variants
                ],
            }
        else:
            export = {
                "campaign_name": campaign.campaign_name,
                "variants": [
                    {
                        "name": v.variant_name,
                        "headline": v.headline,
                        "body": v.body,
                        "cta": v.cta,
                    }
                    for v in variants
                ],
            }
        return export
