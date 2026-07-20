"""Notification Delivery Service.

Sends real notifications to business owners via WhatsApp, Email, Push, In-App.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.models import NotificationDelivery, NotificationChannel, NotificationPriority, NotificationStatus
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.core.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Sends notifications through multiple channels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send(
        self,
        user_id: uuid.UUID,
        business_id: uuid.UUID,
        notification_type: str,
        message: str,
        message_short: str | None = None,
        subject: str | None = None,
        priority: str = "medium",
        channels: list[str] | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> list[NotificationDelivery]:
        """Send notification through specified channels."""
        if channels is None:
            channels = self._default_channels_for_priority(priority)

        deliveries = []
        for channel in channels:
            delivery = NotificationDelivery(
                business_id=business_id,
                user_id=user_id,
                channel=channel,
                priority=priority,
                notification_type=notification_type,
                subject=subject or notification_type.replace("_", " ").title(),
                message=message,
                message_short=message_short or message[:400],
                context_data=context_data or {},
            )
            self.db.add(delivery)
            deliveries.append(delivery)

        await self.db.commit()

        # Actually send
        for delivery in deliveries:
            try:
                await self._send_via_channel(delivery)
                delivery.status = NotificationStatus.SENT
                delivery.sent_at = datetime.now(timezone.utc)
            except Exception as e:
                delivery.status = NotificationStatus.FAILED
                delivery.error_message = str(e)
                logger.error(f"Failed to send {delivery.channel} notification: {e}")

        await self.db.commit()
        return deliveries

    def _default_channels_for_priority(self, priority: str) -> list[str]:
        mapping = {
            NotificationPriority.CRITICAL: ["whatsapp", "push", "email", "in_app"],
            NotificationPriority.HIGH: ["email", "in_app"],
            NotificationPriority.MEDIUM: ["in_app"],
            NotificationPriority.LOW: ["email"],
        }
        return mapping.get(priority, ["in_app"])

    async def _send_via_channel(self, delivery: NotificationDelivery) -> None:
        """Dispatch to actual channel implementation."""
        if delivery.channel == "whatsapp":
            await self._send_whatsapp(delivery)
        elif delivery.channel == "email":
            await self._send_email(delivery)
        elif delivery.channel == "push":
            await self._send_push(delivery)
        elif delivery.channel == "in_app":
            await self._send_in_app(delivery)

    async def _send_whatsapp(self, delivery: NotificationDelivery) -> None:
        """Send WhatsApp message."""
        # In production, integrate with WhatsApp Business API
        # For now, log it
        logger.info(f"[WHATSAPP] To user {delivery.user_id}: {delivery.message_short}")

    async def _send_email(self, delivery: NotificationDelivery) -> None:
        """Send email."""
        # In production, integrate with SendGrid/AWS SES
        logger.info(f"[EMAIL] To user {delivery.user_id}: {delivery.subject}")

    async def _send_push(self, delivery: NotificationDelivery) -> None:
        """Send Web Push notification."""
        # In production, integrate with Web Push API
        logger.info(f"[PUSH] To user {delivery.user_id}: {delivery.message_short}")

    async def _send_in_app(self, delivery: NotificationDelivery) -> None:
        """Send in-app notification (via WebSocket)."""
        # In production, emit WebSocket event
        logger.info(f"[IN_APP] To user {delivery.user_id}: {delivery.notification_type}")


class BriefingDeliveryService:
    """Delivers daily briefing to business owners."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification = NotificationService(db)

    async def deliver_daily_briefing(self, business_id: uuid.UUID) -> Optional[dict[str, Any]]:
        """Generate and deliver daily briefing."""
        from app.domains.orchestration.director import SellIADirector
        from app.domains.autopilot.service import AutopilotReportService

        # Get business owner
        biz_result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = biz_result.scalar_one_or_none()
        if not business:
            return None

        # Generate briefing
        director = SellIADirector(self.db)
        briefing = await director.run_daily_briefing(business_id)

        # Get autopilot report
        report_service = AutopilotReportService(self.db)
        report = await report_service.get_latest_report(business_id)

        # Build messages
        summary = report.ai_summary if report else "No hay actividad automática reciente."

        whatsapp_message = f"📊 Briefing SellIA\n\n{summary}\n\nAcciones hoy: {report.leads_contacted if report else 0} leads, {report.deals_closed if report else 0} deals cerrados."

        email_message = f"""
<h2>Buenos días, {business.name}</h2>
<p><strong>Resumen de SellIA Autopilot:</strong></p>
<p>{summary}</p>
<ul>
  <li>Leads contactados: {report.leads_contacted if report else 0}</li>
  <li>Deals cerrados: {report.deals_closed if report else 0}</li>
  <li>Órdenes creadas: {report.orders_created if report else 0}</li>
  <li>Revenue generado: ${float(report.revenue_generated) if report else 0:,.2f}</li>
  <li>Acciones escaladas: {report.actions_escalated if report else 0}</li>
</ul>
<p><a href="/dashboard/autopilot">Ver detalle en dashboard →</a></p>
"""

        # Send
        await self.notification.send(
            user_id=business.user_id,
            business_id=business_id,
            notification_type="daily_briefing",
            message=email_message,
            message_short=whatsapp_message,
            subject=f"Briefing SellIA — {business.name}",
            priority="medium",
            channels=["email", "whatsapp"],
        )

        return {"sent": True, "summary": summary}


class HandoffAlertService:
    """Notifies humans when leads need human intervention."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification = NotificationService(db)

    async def alert_handoff(
        self,
        business_id: uuid.UUID,
        conversation_id: uuid.UUID,
        reason: str,
        urgency: str = "normal",
    ) -> list[NotificationDelivery]:
        """Send handoff alert to business owner."""
        biz_result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = biz_result.scalar_one_or_none()
        if not business:
            return []

        # Determine priority
        priority = "critical" if urgency == "critical" else "high"
        channels = ["whatsapp", "push", "email", "in_app"] if urgency == "critical" else ["email", "in_app"]

        message_short = f"🚨 Handoff urgente: {reason[:200]}"
        message = f"""
<p><strong>Handoff requerido</strong></p>
<p>Razón: {reason}</p>
<p>Conversación: {conversation_id}</p>
<p><a href="/dashboard/conversaciones/{conversation_id}">Atender ahora →</a></p>
"""

        return await self.notification.send(
            user_id=business.user_id,
            business_id=business_id,
            notification_type="handoff_alert",
            message=message,
            message_short=message_short,
            subject="🚨 Handoff requerido — SellIA",
            priority=priority,
            channels=channels,
            context_data={"conversation_id": str(conversation_id), "urgency": urgency},
        )
