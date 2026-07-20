"""Autopilot Engine Services.

AutopilotEngine — decides what to execute autonomously.
AutopilotExecutor — executes concrete actions.
"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.autopilot.models import (
    AutopilotConfig,
    AutopilotActionLog,
    AutopilotActionStatus,
    AutopilotActionType,
    AutopilotDailyReport,
)
from app.domains.autopilot.schemas import AutopilotConfigCreate, AutopilotConfigUpdate
from app.domains.alerts.models import Recommendation, RecommendationActionType, RecommendationStatus
from app.core.logger import get_logger

logger = get_logger(__name__)


class AutopilotEngine:
    """Decides whether an action should be auto-executed or escalated."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_config(self, business_id: uuid.UUID) -> AutopilotConfig:
        """Get config or create default (opt-in: everything requires approval)."""
        result = await self.db.execute(
            select(AutopilotConfig).where(AutopilotConfig.business_id == business_id)
        )
        config = result.scalar_one_or_none()
        if not config:
            config = AutopilotConfig(business_id=business_id)
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
            logger.info(f"Created default AutopilotConfig for business {business_id}")
        return config

    async def should_auto_execute(
        self,
        action_type: AutopilotActionType,
        business_id: uuid.UUID,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Returns (should_execute, reason)."""
        config = await self.get_or_create_config(business_id)
        context = context or {}

        # Master toggles
        if not config.is_active:
            return False, "Autopilot is not active for this business."
        if config.is_paused:
            return False, f"Autopilot is paused: {config.paused_reason or 'No reason given.'}"

        # Check daily limits
        can_execute, limit_reason = await self._check_daily_limits(config, action_type)
        if not can_execute:
            return False, limit_reason

        # Check action-specific toggle
        toggle_map = {
            AutopilotActionType.QUALIFY_LEAD: config.auto_qualify_leads,
            AutopilotActionType.MOVE_DEAL: config.auto_move_deals,
            AutopilotActionType.SEND_FOLLOWUP: config.auto_send_followups,
            AutopilotActionType.CLOSE_DEAL: config.auto_close_deals,
            AutopilotActionType.CREATE_ORDER: config.auto_create_orders,
            AutopilotActionType.REQUEST_REVIEW: config.auto_request_reviews,
            AutopilotActionType.ACTIVATE_RECOVERY_WORKFLOW: config.auto_activate_recovery_workflows,
            AutopilotActionType.ESCALATE_TO_HUMAN: config.auto_escalate_to_human,
            AutopilotActionType.SEND_PROPOSAL: config.auto_send_followups,
            AutopilotActionType.ASSIGN_AGENT: config.auto_escalate_to_human,
            AutopilotActionType.START_SEQUENCE: config.auto_send_followups,
            AutopilotActionType.CREATE_DEAL: config.auto_move_deals,
            AutopilotActionType.UPDATE_LEAD_SCORE: config.auto_qualify_leads,
            AutopilotActionType.APPLY_RECOMMENDATION: True,  # Checked per-recommendation
        }

        allowed = toggle_map.get(action_type, False)
        if not allowed:
            return False, f"Action '{action_type.value}' is not enabled for autopilot."

        # Check amount threshold for orders/deals
        amount = context.get("amount", Decimal("0"))
        if action_type in (AutopilotActionType.CREATE_ORDER, AutopilotActionType.CLOSE_DEAL):
            if amount > config.approval_threshold_amount:
                return False, (
                    f"Amount ${amount:,.2f} exceeds approval threshold "
                    f"${config.approval_threshold_amount:,.2f}. Requires manual approval."
                )

        return True, "Autopilot authorized this action."

    async def _check_daily_limits(
        self, config: AutopilotConfig, action_type: AutopilotActionType
    ) -> tuple[bool, str]:
        """Check if daily limits would be exceeded."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # Count today's executed actions
        result = await self.db.execute(
            select(func.count(AutopilotActionLog.id)).where(
                AutopilotActionLog.business_id == config.business_id,
                AutopilotActionLog.status == AutopilotActionStatus.EXECUTED,
                AutopilotActionLog.created_at >= today_start,
            )
        )
        total_today = result.scalar() or 0

        # Global message limit
        if action_type in (
            AutopilotActionType.SEND_FOLLOWUP,
            AutopilotActionType.SEND_PROPOSAL,
            AutopilotActionType.START_SEQUENCE,
        ):
            msg_result = await self.db.execute(
                select(func.count(AutopilotActionLog.id)).where(
                    AutopilotActionLog.business_id == config.business_id,
                    AutopilotActionLog.action_type.in_([
                        AutopilotActionType.SEND_FOLLOWUP,
                        AutopilotActionType.SEND_PROPOSAL,
                        AutopilotActionType.START_SEQUENCE,
                    ]),
                    AutopilotActionLog.status == AutopilotActionStatus.EXECUTED,
                    AutopilotActionLog.created_at >= today_start,
                )
            )
            msgs_today = msg_result.scalar() or 0
            if msgs_today >= config.max_daily_auto_messages:
                return False, f"Daily auto-message limit reached ({config.max_daily_auto_messages})."

        # Close limit
        if action_type == AutopilotActionType.CLOSE_DEAL:
            close_result = await self.db.execute(
                select(func.count(AutopilotActionLog.id)).where(
                    AutopilotActionLog.business_id == config.business_id,
                    AutopilotActionLog.action_type == AutopilotActionType.CLOSE_DEAL,
                    AutopilotActionLog.status == AutopilotActionStatus.EXECUTED,
                    AutopilotActionLog.created_at >= today_start,
                )
            )
            closes_today = close_result.scalar() or 0
            if closes_today >= config.max_daily_auto_closes:
                return False, f"Daily auto-close limit reached ({config.max_daily_auto_closes})."

        # Order limit
        if action_type == AutopilotActionType.CREATE_ORDER:
            order_result = await self.db.execute(
                select(func.count(AutopilotActionLog.id)).where(
                    AutopilotActionLog.business_id == config.business_id,
                    AutopilotActionLog.action_type == AutopilotActionType.CREATE_ORDER,
                    AutopilotActionLog.status == AutopilotActionStatus.EXECUTED,
                    AutopilotActionLog.created_at >= today_start,
                )
            )
            orders_today = order_result.scalar() or 0
            if orders_today >= config.max_daily_auto_orders:
                return False, f"Daily auto-order limit reached ({config.max_daily_auto_orders})."

        return True, "Within daily limits."

    async def log_action(
        self,
        business_id: uuid.UUID,
        action_type: AutopilotActionType,
        entity_type: str,
        entity_id: uuid.UUID,
        reason: str,
        status: AutopilotActionStatus,
        context_data: dict[str, Any] | None = None,
        ai_explanation: str | None = None,
        confidence_score: int = 0,
        revenue_impact: Decimal | None = None,
        error_message: str | None = None,
        requires_approval: bool = False,
    ) -> AutopilotActionLog:
        """Log every autopilot decision for audit."""
        log = AutopilotActionLog(
            business_id=business_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,
            ai_explanation=ai_explanation,
            confidence_score=confidence_score,
            context_data=context_data or {},
            status=status,
            error_message=error_message,
            requires_approval=requires_approval,
            revenue_impact=revenue_impact,
            executed_at=datetime.now(timezone.utc) if status == AutopilotActionStatus.EXECUTED else None,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        logger.info(
            f"Autopilot action logged: {action_type.value} for {entity_type} {entity_id} "
            f"→ {status.value}"
        )
        return log

    async def approve_action(self, action_log_id: uuid.UUID, user_id: uuid.UUID, reason: str | None = None) -> Optional[AutopilotActionLog]:
        """Manually approve a pending action."""
        result = await self.db.execute(
            select(AutopilotActionLog).where(AutopilotActionLog.id == action_log_id)
        )
        log = result.scalar_one_or_none()
        if not log or log.status != AutopilotActionStatus.PENDING_APPROVAL:
            return None

        log.status = AutopilotActionStatus.EXECUTED
        log.approved_at = datetime.now(timezone.utc)
        log.approved_by_user_id = user_id
        log.executed_at = datetime.now(timezone.utc)
        log.reason = f"{log.reason} | Approved by user: {reason or 'No reason given.'}"
        await self.db.commit()
        await self.db.refresh(log)

        # Execute the actual action via executor
        executor = AutopilotExecutor(self.db)
        await executor.execute_logged_action(log)

        return log

    async def reject_action(self, action_log_id: uuid.UUID, reason: str) -> Optional[AutopilotActionLog]:
        """Manually reject a pending action."""
        result = await self.db.execute(
            select(AutopilotActionLog).where(AutopilotActionLog.id == action_log_id)
        )
        log = result.scalar_one_or_none()
        if not log or log.status != AutopilotActionStatus.PENDING_APPROVAL:
            return None

        log.status = AutopilotActionStatus.REJECTED
        log.rejected_at = datetime.now(timezone.utc)
        log.rejected_reason = reason
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_today_counts(self, business_id: uuid.UUID) -> dict[str, int]:
        """Get today's action counts for a business."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(
                AutopilotActionLog.status,
                func.count(AutopilotActionLog.id),
            ).where(
                AutopilotActionLog.business_id == business_id,
                AutopilotActionLog.created_at >= today_start,
            ).group_by(AutopilotActionLog.status)
        )
        counts = {row[0].value: row[1] for row in result.all()}
        return {
            "executed": counts.get("executed", 0),
            "pending_approval": counts.get("pending_approval", 0),
            "escalated": counts.get("escalated", 0),
            "rejected": counts.get("rejected", 0),
            "failed": counts.get("failed", 0),
        }

    async def get_last_action(self, business_id: uuid.UUID) -> Optional[datetime]:
        result = await self.db.execute(
            select(AutopilotActionLog.created_at).where(
                AutopilotActionLog.business_id == business_id,
            ).order_by(desc(AutopilotActionLog.created_at)).limit(1)
        )
        row = result.scalar_one_or_none()
        return row


class AutopilotExecutor:
    """Executes concrete actions mapped from recommendations or triggers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_recommendation(self, recommendation: Recommendation) -> bool:
        """Execute a recommendation if autopilot allows it."""
        from app.domains.automations.engine import WorkflowEngine
        from app.domains.crm.models import Deal
        from app.domains.channels.models import Conversation

        engine = AutopilotEngine(self.db)
        rec_action = recommendation.action_type

        # Map recommendation action to autopilot action type
        action_type_map = {
            RecommendationActionType.SEND_MESSAGE: AutopilotActionType.SEND_FOLLOWUP,
            RecommendationActionType.MOVE_STAGE: AutopilotActionType.MOVE_DEAL,
            RecommendationActionType.ASSIGN_AGENT: AutopilotActionType.ASSIGN_AGENT,
            RecommendationActionType.CREATE_DEAL: AutopilotActionType.CREATE_DEAL,
            RecommendationActionType.WAIT: AutopilotActionType.SEND_FOLLOWUP,
            RecommendationActionType.DISMISS: None,
        }
        autopilot_action = action_type_map.get(rec_action)

        if autopilot_action is None:
            # Dismiss = mark as applied, no action needed
            recommendation.status = RecommendationStatus.APPLIED
            recommendation.applied_at = datetime.now(timezone.utc)
            await self.db.commit()
            return True

        can_execute, reason = await engine.should_auto_execute(
            autopilot_action, recommendation.business_id, recommendation.action_payload
        )

        if not can_execute:
            # Log as pending approval
            await engine.log_action(
                business_id=recommendation.business_id,
                action_type=autopilot_action,
                entity_type="recommendation",
                entity_id=recommendation.id,
                reason=reason,
                status=AutopilotActionStatus.PENDING_APPROVAL,
                context_data={"recommendation_id": str(recommendation.id), "payload": recommendation.action_payload},
                requires_approval=True,
            )
            return False

        # Execute
        try:
            success = await self._execute_mapped_action(recommendation)
            status = AutopilotActionStatus.EXECUTED if success else AutopilotActionStatus.FAILED
            await engine.log_action(
                business_id=recommendation.business_id,
                action_type=autopilot_action,
                entity_type="recommendation",
                entity_id=recommendation.id,
                reason=f"Auto-executed recommendation: {recommendation.title}",
                status=status,
                context_data={"recommendation_id": str(recommendation.id), "payload": recommendation.action_payload},
            )
            if success:
                recommendation.status = RecommendationStatus.APPLIED
                recommendation.applied_at = datetime.now(timezone.utc)
                await self.db.commit()
            return success
        except Exception as e:
            logger.exception(f"Autopilot execution failed for recommendation {recommendation.id}")
            await engine.log_action(
                business_id=recommendation.business_id,
                action_type=autopilot_action,
                entity_type="recommendation",
                entity_id=recommendation.id,
                reason=f"Execution failed: {str(e)}",
                status=AutopilotActionStatus.FAILED,
                error_message=str(e),
                context_data={"recommendation_id": str(recommendation.id)},
            )
            return False

    async def _execute_mapped_action(self, recommendation: Recommendation) -> bool:
        """Execute the concrete action based on recommendation type."""
        from app.domains.automations.engine import WorkflowEngine
        from app.domains.crm.models import Deal, Pipeline
        from app.domains.channels.models import Conversation
        from app.domains.agents.ai_reply import generate_ai_response

        payload = recommendation.action_payload or {}
        business_id = recommendation.business_id

        if recommendation.action_type == RecommendationActionType.SEND_MESSAGE:
            conversation_id = payload.get("conversation_id")
            if conversation_id:
                # Use AI to generate contextual follow-up
                await generate_ai_response(
                    db=self.db,
                    business_id=business_id,
                    conversation_id=uuid.UUID(conversation_id),
                    message_text=payload.get("template", "follow_up"),
                    personality_slug="vendedor",
                )
            return True

        elif recommendation.action_type == RecommendationActionType.CREATE_DEAL:
            conversation_id = payload.get("conversation_id")
            if conversation_id:
                conv_result = await self.db.execute(
                    select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
                )
                conv = conv_result.scalar_one_or_none()
                if conv:
                    deal = Deal(
                        business_id=business_id,
                        conversation_id=conv.id,
                        title=f"Deal from {conv.lead_name or 'Lead'}",
                        stage="new_lead",
                        source_channel=conv.lead_source,
                    )
                    self.db.add(deal)
                    await self.db.commit()
            return True

        elif recommendation.action_type == RecommendationActionType.MOVE_STAGE:
            deal_id = payload.get("deal_id")
            stage = payload.get("stage")
            if deal_id and stage:
                deal_result = await self.db.execute(
                    select(Deal).where(Deal.id == uuid.UUID(deal_id))
                )
                deal = deal_result.scalar_one_or_none()
                if deal:
                    deal.stage = stage
                    deal.updated_at = datetime.now(timezone.utc)
                    await self.db.commit()
            return True

        elif recommendation.action_type == RecommendationActionType.ASSIGN_AGENT:
            conversation_id = payload.get("conversation_id")
            if conversation_id:
                conv_result = await self.db.execute(
                    select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
                )
                conv = conv_result.scalar_one_or_none()
                if conv:
                    conv.awaiting_human = True
                    conv.updated_at = datetime.now(timezone.utc)
                    await self.db.commit()
            return True

        return True  # WAIT and others are no-ops

    async def execute_logged_action(self, log: AutopilotActionLog) -> bool:
        """Execute an action that was previously logged as pending."""
        # Reconstruct a pseudo-recommendation and execute
        from app.domains.alerts.models import Recommendation

        pseudo_rec = Recommendation(
            business_id=log.business_id,
            type="custom",
            title=f"Approved action: {log.action_type.value}",
            description=log.reason,
            action_type=RecommendationActionType.SEND_MESSAGE,  # Default
            action_payload=log.context_data.get("payload", {}),
            status=RecommendationStatus.PENDING,
        )
        return await self._execute_mapped_action(pseudo_rec)


class AutopilotReportService:
    """Generates daily reports and summaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_daily_report(self, business_id: uuid.UUID, report_date: datetime | None = None) -> AutopilotDailyReport:
        """Generate a daily report for a business."""
        if report_date is None:
            report_date = datetime.now(timezone.utc)

        day_start = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        # Query stats from action logs
        result = await self.db.execute(
            select(
                AutopilotActionLog.action_type,
                AutopilotActionLog.status,
                func.count(AutopilotActionLog.id),
                func.sum(AutopilotActionLog.revenue_impact),
            ).where(
                AutopilotActionLog.business_id == business_id,
                AutopilotActionLog.created_at >= day_start,
                AutopilotActionLog.created_at < day_end,
            ).group_by(AutopilotActionLog.action_type, AutopilotActionLog.status)
        )

        stats = {
            "leads_contacted": 0,
            "deals_moved": 0,
            "deals_closed": 0,
            "orders_created": 0,
            "messages_sent": 0,
            "sequences_started": 0,
            "workflows_activated": 0,
            "revenue_generated": Decimal("0"),
            "actions_escalated": 0,
            "actions_pending_approval": 0,
            "actions_rejected": 0,
        }

        for action_type, status, count, revenue in result.all():
            if status == AutopilotActionStatus.EXECUTED:
                if action_type in (AutopilotActionType.SEND_FOLLOWUP, AutopilotActionType.SEND_PROPOSAL):
                    stats["messages_sent"] += count
                elif action_type == AutopilotActionType.CLOSE_DEAL:
                    stats["deals_closed"] += count
                elif action_type == AutopilotActionType.MOVE_DEAL:
                    stats["deals_moved"] += count
                elif action_type == AutopilotActionType.CREATE_ORDER:
                    stats["orders_created"] += count
                elif action_type == AutopilotActionType.START_SEQUENCE:
                    stats["sequences_started"] += count
                elif action_type == AutopilotActionType.ACTIVATE_RECOVERY_WORKFLOW:
                    stats["workflows_activated"] += count
                elif action_type in (AutopilotActionType.QUALIFY_LEAD, AutopilotActionType.UPDATE_LEAD_SCORE):
                    stats["leads_contacted"] += count
                if revenue:
                    stats["revenue_generated"] += revenue
            elif status == AutopilotActionStatus.ESCALATED:
                stats["actions_escalated"] += count
            elif status == AutopilotActionStatus.PENDING_APPROVAL:
                stats["actions_pending_approval"] += count
            elif status == AutopilotActionStatus.REJECTED:
                stats["actions_rejected"] += count

        # Calculate deals value closed
        deals_value = Decimal("0")
        from app.domains.crm.models import Deal
        deals_result = await self.db.execute(
            select(func.sum(Deal.value)).where(
                Deal.business_id == business_id,
                Deal.stage == "closed_won",
                Deal.actual_close_date >= day_start,
                Deal.actual_close_date < day_end,
            )
        )
        deals_value = deals_result.scalar() or Decimal("0")

        report = AutopilotDailyReport(
            business_id=business_id,
            report_date=day_start,
            leads_contacted=stats["leads_contacted"],
            deals_moved=stats["deals_moved"],
            deals_closed=stats["deals_closed"],
            orders_created=stats["orders_created"],
            messages_sent=stats["messages_sent"],
            sequences_started=stats["sequences_started"],
            workflows_activated=stats["workflows_activated"],
            revenue_generated=stats["revenue_generated"],
            deals_value_closed=deals_value,
            actions_escalated=stats["actions_escalated"],
            actions_pending_approval=stats["actions_pending_approval"],
            actions_rejected=stats["actions_rejected"],
        )

        # Generate AI summary (simple for now)
        report.ai_summary = self._generate_summary(report)

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    def _generate_summary(self, report: AutopilotDailyReport) -> str:
        """Generate a human-readable summary."""
        parts = []
        if report.leads_contacted:
            parts.append(f"contactó {report.leads_contacted} leads")
        if report.deals_closed:
            parts.append(f"cerró {report.deals_closed} deals")
        if report.orders_created:
            parts.append(f"creó {report.orders_created} órdenes")
        if report.messages_sent:
            parts.append(f"envió {report.messages_sent} mensajes")
        if report.revenue_generated and report.revenue_generated > 0:
            parts.append(f"generó ${float(report.revenue_generated):,.2f} en revenue")
        if report.actions_escalated:
            parts.append(f"escaló {report.actions_escalated} acciones para revisión humana")

        if not parts:
            return "Hoy no hubo actividad automática. El sistema estuvo monitoreando."

        return "Hoy SellIA " + ", ".join(parts) + "."

    async def get_latest_report(self, business_id: uuid.UUID) -> Optional[AutopilotDailyReport]:
        result = await self.db.execute(
            select(AutopilotDailyReport).where(
                AutopilotDailyReport.business_id == business_id,
            ).order_by(desc(AutopilotDailyReport.report_date)).limit(1)
        )
        return result.scalar_one_or_none()
