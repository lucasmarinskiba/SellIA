"""Phase 3: Channel Routing Service - Intelligent Message Delivery."""
from typing import List, Tuple
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domains.channel_routing.models import ChannelAffinityModel, MessageRouting, ChannelPerformanceMetrics


class ChannelRoutingService:
    @staticmethod
    async def route_message(
        db: AsyncSession,
        business_id: UUID,
        customer_id: UUID,
        message_template_id: UUID,
        force_channel: str = None,
    ) -> dict:
        """Route message to optimal channel based on customer affinity."""
        # Get customer affinity profile
        result = await db.execute(
            select(ChannelAffinityModel).where(
                (ChannelAffinityModel.business_id == business_id)
                & (ChannelAffinityModel.customer_id == customer_id)
            )
        )
        affinity = result.scalar()

        if not affinity:
            # Default routing
            routed_channel = force_channel or "email"
            confidence = 0.5
        else:
            # Rank channels by affinity (excluding opted-out)
            opted_out = affinity.opted_out_channels or []

            channels_scores = [
                ("email", affinity.email_score),
                ("sms", affinity.sms_score),
                ("whatsapp", affinity.whatsapp_score),
                ("phone", affinity.phone_score),
                ("in_app", affinity.in_app_score),
            ]

            # Filter out opted-out channels
            available = [(ch, sc) for ch, sc in channels_scores if ch not in opted_out]
            available.sort(key=lambda x: x[1], reverse=True)

            # Override with force_channel if specified
            if force_channel and force_channel not in opted_out:
                routed_channel = force_channel
            else:
                routed_channel = available[0][0] if available else "email"

            confidence = available[0][1] if available else 0.5

        # Calculate optimal send time
        if routed_channel == "email":
            send_hour = affinity.email_best_hour if affinity else 10
        elif routed_channel == "sms":
            send_hour = affinity.sms_best_hour if affinity else 14
        elif routed_channel == "whatsapp":
            send_hour = affinity.whatsapp_best_hour if affinity else 20
        elif routed_channel == "phone":
            send_hour = affinity.phone_best_hour if affinity else 15
        else:
            send_hour = 10

        # Create optimal send time (today or tomorrow)
        now = datetime.now(timezone.utc)
        target_time = now.replace(hour=send_hour, minute=0, second=0, microsecond=0)
        if target_time < now:
            target_time += timedelta(days=1)

        # Create routing record
        routing = MessageRouting(
            business_id=business_id,
            customer_id=customer_id,
            message_template_id=message_template_id,
            routed_to_channel=routed_channel,
            routed_reason="highest_affinity",
            confidence_score=confidence,
            fallback_channel_1="email",
            fallback_channel_2="sms",
            optimal_send_time=target_time,
        )
        db.add(routing)
        await db.commit()
        await db.refresh(routing)

        return {
            "routing_id": routing.id,
            "customer_id": customer_id,
            "routed_to_channel": routed_channel,
            "confidence": round(confidence, 2),
            "optimal_send_time": target_time.isoformat(),
            "fallback_channels": [routing.fallback_channel_1, routing.fallback_channel_2],
        }

    @staticmethod
    async def update_channel_affinity(
        db: AsyncSession,
        business_id: UUID,
        customer_id: UUID,
        channel: str,
        was_delivered: bool,
        was_opened: bool = False,
        was_clicked: bool = False,
        response_time_seconds: int = None,
    ) -> ChannelAffinityModel:
        """Update channel affinity based on message performance."""
        result = await db.execute(
            select(ChannelAffinityModel).where(
                (ChannelAffinityModel.business_id == business_id)
                & (ChannelAffinityModel.customer_id == customer_id)
            )
        )
        affinity = result.scalar()

        if not affinity:
            affinity = ChannelAffinityModel(
                business_id=business_id,
                customer_id=customer_id,
            )
            db.add(affinity)

        # Update response rates based on channel
        if channel == "email":
            affinity.email_response_rate = (affinity.email_response_rate * 0.7) + (0.3 if was_clicked else 0)
        elif channel == "sms":
            affinity.sms_response_rate = (affinity.sms_response_rate * 0.7) + (0.3 if was_clicked else 0)
        elif channel == "whatsapp":
            affinity.whatsapp_response_rate = (affinity.whatsapp_response_rate * 0.7) + (0.3 if was_clicked else 0)
        elif channel == "phone":
            affinity.phone_response_rate = (affinity.phone_response_rate * 0.7) + (0.3 if was_clicked else 0)

        # Recalculate affinity scores
        total_rate = (
            affinity.email_response_rate
            + affinity.sms_response_rate
            + affinity.whatsapp_response_rate
            + affinity.phone_response_rate
        )

        if total_rate > 0:
            affinity.email_score = affinity.email_response_rate / total_rate * 0.4 + 0.1
            affinity.sms_score = affinity.sms_response_rate / total_rate * 0.4 + 0.1
            affinity.whatsapp_score = affinity.whatsapp_response_rate / total_rate * 0.4 + 0.1
            affinity.phone_score = affinity.phone_response_rate / total_rate * 0.4 + 0.1

        await db.commit()
        await db.refresh(affinity)
        return affinity

    @staticmethod
    async def get_channel_performance(
        db: AsyncSession,
        business_id: UUID,
        channel: str,
    ) -> dict:
        """Get channel performance metrics."""
        result = await db.execute(
            select(ChannelPerformanceMetrics).where(
                (ChannelPerformanceMetrics.business_id == business_id)
                & (ChannelPerformanceMetrics.channel == channel)
            )
        )
        metrics = result.scalar()

        if not metrics:
            return {
                "channel": channel,
                "status": "no_data",
                "message": f"No data yet for channel {channel}",
            }

        return {
            "channel": channel,
            "total_sent": metrics.total_messages_sent,
            "delivery_rate": round(metrics.delivery_rate * 100, 2),
            "open_rate": round(metrics.open_rate * 100, 2),
            "click_rate": round(metrics.click_rate * 100, 2),
            "response_rate": round(metrics.response_rate * 100, 2),
            "avg_response_time_seconds": metrics.avg_response_time_seconds,
            "cost_per_response": round(metrics.cost_per_response, 2),
            "quality_score": round(metrics.quality_score, 2),
            "week_over_week_growth": round(metrics.week_over_week_growth * 100, 2),
        }

    @staticmethod
    async def recommend_channel_strategy(
        db: AsyncSession,
        business_id: UUID,
    ) -> dict:
        """Recommend optimal channel strategy for business."""
        # Get all channel performance
        result = await db.execute(
            select(ChannelPerformanceMetrics).where(
                ChannelPerformanceMetrics.business_id == business_id
            )
        )
        metrics_list = result.scalars().all()

        if not metrics_list:
            return {"recommendation": "collect_baseline_data", "channels": []}

        # Rank channels by performance
        channels_ranked = sorted(
            metrics_list,
            key=lambda m: (m.open_rate + m.click_rate + m.response_rate) / 3,
            reverse=True,
        )

        return {
            "primary_channel": channels_ranked[0].channel if channels_ranked else None,
            "secondary_channel": channels_ranked[1].channel if len(channels_ranked) > 1 else None,
            "channels_by_performance": [
                {
                    "channel": m.channel,
                    "quality_score": round(m.quality_score, 2),
                    "response_rate": round(m.response_rate * 100, 2),
                }
                for m in channels_ranked[:3]
            ],
        }
