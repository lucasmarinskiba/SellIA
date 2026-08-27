"""
FOMO Workflow Actions - Integration with Workflow Engine
Triggers FOMO campaigns from workflow events
"""

from typing import Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.fomo.service import fomo_service
from app.domains.fomo.models import FOMOCampaign


class FOMOWorkflowActions:
    """Workflow action definitions for FOMO campaigns."""

    @staticmethod
    async def trigger_scarcity_message(
        db: AsyncSession,
        campaign_id: UUID,
        customer_id: UUID,
        product_id: UUID,
        stock_available: int,
        stock_total: int,
        **kwargs: Any,
    ) -> dict:
        """
        Trigger scarcity message workflow action.
        Used when: low stock, limited time, limited spots
        """
        campaign = await fomo_service.get_campaign(db, campaign_id)
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        # Log event
        event = await fomo_service.log_event(
            db,
            campaign_id=campaign_id,
            event_type='view',
            customer_id=customer_id,
            product_id=product_id,
            metadata={
                'stock_available': stock_available,
                'stock_total': stock_total,
                'urgency_level': 'high' if stock_available < stock_total * 0.2 else 'medium',
            },
        )

        await fomo_service.record_metric(db, campaign_id, 'impression')
        await db.commit()

        return {
            "success": True,
            "event_id": str(event.id),
            "message": f"Solo {stock_available}/{stock_total} disponibles",
            "urgency": "high" if stock_available < stock_total * 0.2 else "medium",
        }

    @staticmethod
    async def trigger_cart_recovery(
        db: AsyncSession,
        campaign_id: UUID,
        customer_id: UUID,
        product_id: UUID,
        cart_value: float,
        items_count: int,
        **kwargs: Any,
    ) -> dict:
        """
        Trigger cart abandonment recovery.
        Send urgency message + optional discount.
        """
        campaign = await fomo_service.get_campaign(db, campaign_id)
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        config = campaign.config or {}
        discount_percent = config.get('discountPercent', 0)

        event = await fomo_service.log_event(
            db,
            campaign_id=campaign_id,
            event_type='abandoned',
            customer_id=customer_id,
            product_id=product_id,
            metadata={
                'cart_value': cart_value,
                'items_count': items_count,
                'recovery_offer': f"{discount_percent}% OFF" if discount_percent > 0 else None,
            },
        )

        await db.commit()

        return {
            "success": True,
            "event_id": str(event.id),
            "offer": f"{discount_percent}% OFF" if discount_percent > 0 else None,
            "urgency_message": "No dejes pasar esto. Tu carrito expira pronto.",
        }

    @staticmethod
    async def trigger_social_proof(
        db: AsyncSession,
        campaign_id: UUID,
        customer_id: UUID,
        product_id: UUID,
        event_type: str = 'purchase',
        customer_name: Optional[str] = None,
        product_name: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        """
        Trigger social proof display.
        Shows real-time activity: 'User X just bought Y'
        """
        campaign = await fomo_service.get_campaign(db, campaign_id)
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        event = await fomo_service.log_event(
            db,
            campaign_id=campaign_id,
            event_type=event_type,
            customer_id=customer_id,
            product_id=product_id,
            metadata={
                'customer_name': customer_name or 'Usuario',
                'product_name': product_name or 'Producto',
            },
        )

        if event_type == 'purchase':
            await fomo_service.record_metric(db, campaign_id, 'conversion')

        await db.commit()

        return {
            "success": True,
            "event_id": str(event.id),
            "activity_text": f"{customer_name or 'User'} compró {product_name or 'this item'}",
        }

    @staticmethod
    async def trigger_countdown_urgency(
        db: AsyncSession,
        campaign_id: UUID,
        customer_id: UUID,
        countdown_hours: int = 48,
        **kwargs: Any,
    ) -> dict:
        """
        Trigger countdown timer urgency.
        Flash sale or limited-time offer.
        """
        campaign = await fomo_service.get_campaign(db, campaign_id)
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        event = await fomo_service.log_event(
            db,
            campaign_id=campaign_id,
            event_type='view',
            customer_id=customer_id,
            metadata={
                'countdown_hours': countdown_hours,
                'deadline': (datetime.now(timezone.utc).isoformat()),
            },
        )

        await fomo_service.record_metric(db, campaign_id, 'impression')
        await db.commit()

        return {
            "success": True,
            "event_id": str(event.id),
            "countdown_hours": countdown_hours,
            "message": f"Oferta válida por {countdown_hours} horas",
        }

    @staticmethod
    async def trigger_exclusivity(
        db: AsyncSession,
        campaign_id: UUID,
        customer_id: UUID,
        customer_segment: str = 'vip',
        **kwargs: Any,
    ) -> dict:
        """
        Trigger exclusivity messaging.
        'Early access for VIP customers' / 'Limited to first 100'
        """
        campaign = await fomo_service.get_campaign(db, campaign_id)
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        event = await fomo_service.log_event(
            db,
            campaign_id=campaign_id,
            event_type='view',
            customer_id=customer_id,
            metadata={
                'segment': customer_segment,
                'exclusive': True,
            },
        )

        await fomo_service.record_metric(db, campaign_id, 'impression')
        await db.commit()

        segment_labels = {
            'vip': 'Acceso exclusivo VIP',
            'early_adopter': 'Early access para clientes destacados',
            'high_value': 'Oferta especial para ti',
        }

        return {
            "success": True,
            "event_id": str(event.id),
            "message": segment_labels.get(customer_segment, 'Acceso exclusivo'),
        }


# Workflow trigger mapping
FOMO_WORKFLOW_TRIGGERS = {
    'cart_abandon': {
        'action': FOMOWorkflowActions.trigger_cart_recovery,
        'description': 'Cart abandonment recovery with urgency',
    },
    'page_view': {
        'action': FOMOWorkflowActions.trigger_scarcity_message,
        'description': 'Show scarcity on product view',
    },
    'purchase': {
        'action': FOMOWorkflowActions.trigger_social_proof,
        'description': 'Display purchase in social proof feed',
    },
    'low_engagement': {
        'action': FOMOWorkflowActions.trigger_countdown_urgency,
        'description': 'Re-engage with countdown offer',
    },
    'vip_access': {
        'action': FOMOWorkflowActions.trigger_exclusivity,
        'description': 'Exclusive offer for VIP segment',
    },
}
