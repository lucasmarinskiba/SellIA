"""Sales Funnel API — REST endpoints para pipeline completo."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.database import get_db
from app.domains.computer_use.services.sales_funnel_orchestrator import get_sales_funnel_orchestrator
from app.domains.computer_use.services.lead_generator import get_lead_generator, LeadQuality
from app.domains.computer_use.services.outreach_orchestrator import get_outreach_orchestrator, OutreachChannel
from app.domains.computer_use.services.customer_loyalty import get_customer_loyalty_engine

router = APIRouter(prefix="/sales-funnel", tags=["Sales Funnel"])


@router.post("/run-pipeline")
async def run_complete_pipeline(
    leads: List[Dict[str, Any]],
    product_info: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Ejecuta pipeline completo: Find → Contact → Respond → Close → Pay → Grow → Loyalty

    ```
    POST /sales-funnel/run-pipeline
    {
      "leads": [
        {"name": "John", "email": "john@company.com", "company": "Acme", ...},
        ...
      ],
      "product_info": {"name": "SellIA Pro", "price": 499, "niche": "sales"}
    }
    ```
    """
    try:
        orchestrator = get_sales_funnel_orchestrator(db)

        result = await orchestrator.run_complete_pipeline(
            leads_data=leads,
            product_info=product_info,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import-leads")
async def import_leads(
    leads: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Importa + enriquece leads (Fase 11).

    ```
    POST /sales-funnel/import-leads
    {
      "leads": [
        {"name": "John", "email": "john@company.com", "company": "Acme", "title": "CTO"},
        ...
      ]
    }
    ```
    """
    try:
        lead_gen = get_lead_generator()

        imported = await lead_gen.import_leads(leads)

        # Enrich
        for lead in imported:
            lead = await lead_gen.enrich_lead(lead)
            lead = await lead_gen.score_lead(lead)

        # Agrupar por quality
        hot = [l for l in imported if l.quality == LeadQuality.HOT]
        warm = [l for l in imported if l.quality == LeadQuality.WARM]
        cold = [l for l in imported if l.quality == LeadQuality.COLD]

        return {
            "imported": len(imported),
            "hot": len(hot),
            "warm": len(warm),
            "cold": len(cold),
            "leads": [l.to_dict() for l in imported[:10]],  # Primeros 10
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-outreach")
async def send_outreach(
    leads: List[Dict[str, Any]],
    channel: str = "email",  # email, whatsapp, linkedin
) -> Dict[str, Any]:
    """
    Envía outreach a leads (Fase 11).

    ```
    POST /sales-funnel/send-outreach
    {
      "leads": [...],
      "channel": "email"
    }
    ```
    """
    try:
        lead_gen = get_lead_generator()
        outreach = get_outreach_orchestrator()

        # Importar
        imported = await lead_gen.import_leads(leads)

        # Enrich + score
        for lead in imported:
            lead = await lead_gen.enrich_lead(lead)
            lead = await lead_gen.score_lead(lead)

        # Crear campaign
        campaign = await outreach.create_campaign(
            name=f"Outreach {datetime.utcnow().strftime('%Y%m%d%H%M')}",
            target_quality="hot",
            channel=OutreachChannel(channel),
        )

        # Enviar a HOT leads
        contacted = 0
        for lead in imported:
            if lead.quality.value == "hot":
                success, msg_id = await outreach.send_outreach(
                    campaign=campaign,
                    lead=lead,
                    sender_name="SellIA Bot",
                    sender_email="bot@sellía.ai",
                )

                if success:
                    contacted += 1

        return {
            "campaign_id": campaign.campaign_id,
            "total_leads": len(imported),
            "contacted": contacted,
            "hot": len([l for l in imported if l.quality.value == "hot"]),
            "warm": len([l for l in imported if l.quality.value == "warm"]),
            "cold": len([l for l in imported if l.quality.value == "cold"]),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-email-sequence")
async def send_email_sequence(
    customers: List[Dict[str, Any]],
    sequence_type: str = "welcome",  # welcome, upsell, win_back
) -> Dict[str, Any]:
    """
    Envía secuencias de email (Fase 12).

    ```
    POST /sales-funnel/send-email-sequence
    {
      "customers": [
        {"name": "John", "email": "john@company.com", "product": "SellIA Pro"},
        ...
      ],
      "sequence_type": "welcome"
    }
    ```
    """
    try:
        loyalty = get_customer_loyalty_engine()

        # Crear sequence
        sequence = await loyalty.create_email_sequence(
            name=f"Sequence {sequence_type}",
            sequence_type=sequence_type,
        )

        # Enviar a customers
        sent = 0
        for customer in customers:
            if sequence_type == "welcome":
                success, seq_id = await loyalty.trigger_welcome_sequence(
                    customer_id=customer.get("id", ""),
                    customer_name=customer.get("name", ""),
                    customer_email=customer.get("email", ""),
                    product=customer.get("product", ""),
                )
            elif sequence_type == "upsell":
                opportunity = await loyalty.create_upsell_offer(
                    customer_id=customer.get("id", ""),
                    product_purchased=customer.get("product", ""),
                    upsell_product="Premium",
                )

                success = await loyalty.send_upsell_email(
                    opportunity=opportunity,
                    customer_email=customer.get("email", ""),
                    customer_name=customer.get("name", ""),
                )
            else:
                success = False

            if success:
                sent += 1

        return {
            "sequence_id": sequence.sequence_id,
            "sequence_type": sequence_type,
            "total_customers": len(customers),
            "sent": sent,
            "stats": sequence.stats,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pipeline-status/{campaign_id}")
async def get_pipeline_status(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Obtiene status de campaign."""
    try:
        orchestrator = get_sales_funnel_orchestrator(db)
        orchestrator.campaign_id = campaign_id

        return await orchestrator.get_pipeline_status()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_metrics() -> Dict[str, Any]:
    """
    Dashboard metrics: leads, conversions, revenue, growth.

    ```
    GET /sales-funnel/dashboard
    ```
    """
    try:
        # Mock data (en prod: consultar DB)
        return {
            "summary": {
                "leads_imported": 1250,
                "leads_contacted": 450,
                "leads_responded": 135,
                "sales_closed": 67,
                "payments_processed": 65,
                "revenue": 32500,
                "avg_deal_size": 500,
            },
            "funnel": {
                "awareness": {"leads": 1250, "conversion": "100%"},
                "engagement": {"leads": 450, "conversion": "36%"},
                "interest": {"leads": 135, "conversion": "30%"},
                "decision": {"leads": 67, "conversion": "50%"},
                "purchase": {"leads": 65, "conversion": "97%"},
            },
            "performance": {
                "outreach_efficiency": "36%",  # contacted / imported
                "response_rate": "30%",  # responded / contacted
                "close_rate": "50%",  # closed / interested
                "conversion_rate": "5.2%",  # closed / imported
            },
            "growth": {
                "followers_gain": 4500,
                "engagement_rate": "6.8%",
                "reach": 125000,
                "content_posts": 21,
                "best_performing": "Educational tips (8.5% engagement)",
            },
            "loyalty": {
                "upsells_sent": 65,
                "upsell_rate": "25%",
                "email_sequences_active": 3,
                "at_risk_customers": 12,
                "ltv_avg": 1250,
            },
            "roi": {
                "marketing_spend": 2500,
                "revenue_generated": 32500,
                "roi_percentage": 1200,
                "profit": 30000,
            },
            "status": "production_ready",
            "next_actions": [
                "5 leads ready to close (hot tier)",
                "12 customers at-risk (send win-back)",
                "3 upsell opportunities ready",
                "Trending topic detected: #sidehustle (+35%)",
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Importar datetime
from datetime import datetime
