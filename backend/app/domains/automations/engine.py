"""Workflow Execution Engine

Processes triggers and executes workflow actions sequentially.
Supports persistent delays via WorkflowExecution state.
"""

import uuid
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.automations.models import (
    Workflow, WorkflowExecution, WorkflowTriggerType, WorkflowActionType,
    WorkflowStatus, WorkflowVariant,
)
from app.domains.channels.models import Conversation, Message, MessageDirection, MessageStatus, ChannelPlatform
from app.domains.agents.models import AgentConversation, AgentMessage
from app.domains.agents.services import AgentService
from app.domains.agents.prompts import get_system_prompt, compose_system_prompt
from app.domains.agents.context_builder import BusinessContextBuilder
from app.domains.subscriptions.models import UserAPIKey
from app.core.encryption import decrypt_value
from app.core.events import (
    emit_workflow_completed,
    emit_deal_created,
    emit_human_handoff_required,
)

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class WorkflowEngine:
    """Motor de ejecución de workflows de ventas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_trigger(
        self,
        trigger_type: WorkflowTriggerType,
        business_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID] = None,
        trigger_data: Optional[Dict[str, Any]] = None,
    ) -> List[WorkflowExecution]:
        """Process a trigger and execute matching workflows."""
        # Find active workflows for this trigger and business
        result = await self.db.execute(
            select(Workflow).where(
                Workflow.business_id == business_id,
                Workflow.trigger_type == trigger_type,
                Workflow.status == WorkflowStatus.ACTIVE,
                Workflow.is_active == True,
            )
        )
        workflows = result.scalars().all()

        executions = []
        for workflow in workflows:
            # Check trigger_config filters
            if not self._check_trigger_config(workflow.trigger_config, trigger_data or {}):
                continue

            # A/B Test: select variant deterministically
            variant_id, selected_actions = await self._select_variant(workflow, conversation_id)

            # Create execution record
            execution = WorkflowExecution(
                workflow_id=workflow.id,
                variant_id=variant_id,
                conversation_id=conversation_id,
                trigger_data=trigger_data or {},
                actions_executed=[],
                status="running",
            )
            self.db.add(execution)
            await self.db.flush()
            executions.append(execution)

            # Execute via Celery task if available, otherwise fallback to asyncio
            try:
                from app.tasks.workflow_tasks import execute_workflow_task
                execute_workflow_task.delay(str(execution.id), str(business_id), selected_actions)
            except Exception as e:
                from app.core.logger import get_logger
                get_logger(__name__).warning(f"Celery not available, using asyncio fallback: {e}")
                asyncio.create_task(self._run_execution(execution.id, business_id, selected_actions))

        await self.db.commit()
        return executions

    async def _select_variant(
        self,
        workflow: Workflow,
        conversation_id: Optional[uuid.UUID],
    ) -> tuple[Optional[uuid.UUID], Optional[List[Dict[str, Any]]]]:
        """Select A/B test variant using deterministic hash-based routing.
        
        Returns (variant_id, actions_override) or (None, None) if no variants.
        """
        result = await self.db.execute(
            select(WorkflowVariant).where(
                WorkflowVariant.workflow_id == workflow.id,
                WorkflowVariant.is_active == True,
            ).order_by(WorkflowVariant.is_control.desc(), WorkflowVariant.created_at)
        )
        variants = result.scalars().all()
        if not variants:
            return None, None

        # Build cumulative split ranges
        cumulative = []
        total = 0
        for v in variants:
            total += v.traffic_split
            cumulative.append(total)

        # Normalize to 100 if total != 100
        if total > 0 and total != 100:
            cumulative = [int(c * 100 / total) for c in cumulative]

        # Deterministic hash: hash(str(conversation_id) + str(workflow.id)) % 100
        hash_input = f"{conversation_id or 'anonymous'}:{workflow.id}"
        bucket = hash(hash_input) % 100
        if bucket < 0:
            bucket += 100  # Ensure positive

        for idx, v in enumerate(variants):
            upper = cumulative[idx] if idx < len(cumulative) else 100
            if bucket < upper:
                v.execution_count = (v.execution_count or 0) + 1
                self.db.add(v)
                return v.id, v.actions if v.actions else None

        # Fallback to last variant
        v = variants[-1]
        v.execution_count = (v.execution_count or 0) + 1
        self.db.add(v)
        return v.id, v.actions if v.actions else None

    def _check_trigger_config(self, config: Dict[str, Any], trigger_data: Dict[str, Any]) -> bool:
        """Check if trigger data matches workflow trigger_config filters."""
        if not config:
            return True

        # Keyword matching
        if "keywords" in config and trigger_data.get("content"):
            content = trigger_data["content"].lower()
            if not any(kw.lower() in content for kw in config["keywords"]):
                return False

        # Channel filter
        if "channels" in config and trigger_data.get("channel"):
            if trigger_data["channel"] not in config["channels"]:
                return False

        # Minimum delay check
        if "delay_minutes" in config:
            # Delay is handled by scheduling, not filtering
            pass

        return True

    async def _run_execution(self, execution_id: uuid.UUID, business_id: uuid.UUID, selected_actions: Optional[List[Dict[str, Any]]] = None):
        """Run a workflow execution in background."""
        async with AsyncSessionLocal() as db:
            engine = WorkflowEngine(db)
            await engine.execute_workflow(execution_id, business_id, selected_actions)

    async def execute_workflow(self, execution_id: uuid.UUID, business_id: uuid.UUID, selected_actions: Optional[List[Dict[str, Any]]] = None):
        """Execute workflow actions sequentially."""
        result = await self.db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if not execution or execution.status in ("completed", "failed"):
            return

        result = await self.db.execute(
            select(Workflow).where(Workflow.id == execution.workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            execution.status = "failed"
            execution.error_message = "Workflow not found"
            await self.db.commit()
            return

        # Use pre-selected variant actions from process_trigger, or fallback to workflow actions
        if selected_actions is not None:
            actions = selected_actions
        else:
            actions = workflow.actions or []

        executed_count = len(execution.actions_executed or [])

        for i in range(executed_count, len(actions)):
            action = actions[i]
            try:
                should_continue = await self._execute_action(
                    action, workflow, execution, business_id
                )
                if not should_continue:
                    break
            except Exception as e:
                execution.status = "failed"
                execution.error_message = str(e)
                await self.db.commit()
                return

        # Mark completed if all actions done
        if execution.status == "running":
            execution.status = "completed"
            workflow.execution_count += 1
            await self.db.commit()

            # Emit completion event
            try:
                await emit_workflow_completed(
                    business_id=str(business_id),
                    workflow_id=str(workflow.id),
                    execution_id=str(execution.id),
                    status="completed",
                    conversation_id=str(execution.conversation_id) if execution.conversation_id else None,
                )
            except Exception as e:
                from app.core.logger import get_logger
                get_logger(__name__).error(f"Event emit error: {e}")

    async def _execute_action(
        self,
        action: Dict[str, Any],
        workflow: Workflow,
        execution: WorkflowExecution,
        business_id: uuid.UUID,
    ) -> bool:
        """Execute a single action. Returns True to continue, False to pause."""
        action_type = action.get("type")
        config = action.get("config", {})

        action_record = {
            "type": action_type,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }

        if action_type == WorkflowActionType.SEND_MESSAGE:
            await self._action_send_message(config, execution, business_id)

        elif action_type == WorkflowActionType.SEND_EMAIL:
            await self._action_send_email(config, execution, business_id)

        elif action_type == WorkflowActionType.AI_REPLY:
            await self._action_ai_reply(config, execution, business_id)

        elif action_type == WorkflowActionType.ADD_TAG:
            await self._action_add_tag(config, execution)

        elif action_type == WorkflowActionType.WAIT:
            delay = self._parse_delay(config)
            if delay > 0:
                action_record["status"] = "waiting"
                action_record["resume_at"] = (datetime.now(timezone.utc) + delay).isoformat()
                execution.actions_executed = execution.actions_executed + [action_record]
                await self.db.commit()
                # Schedule resume
                asyncio.create_task(self._schedule_resume(execution.id, business_id, delay.total_seconds()))
                return False  # Pause execution

        elif action_type == WorkflowActionType.WEBHOOK:
            await self._action_webhook(config, execution)

        elif action_type == WorkflowActionType.MOVE_STAGE:
            await self._action_move_stage(config, execution)

        elif action_type == WorkflowActionType.UPDATE_STAGE:
            await self._action_update_stage(config, execution)

        elif action_type == WorkflowActionType.UPDATE_SCORE:
            await self._action_update_score(config, execution)

        elif action_type == WorkflowActionType.CREATE_DEAL:
            await self._action_create_deal(config, execution, business_id)

        elif action_type == WorkflowActionType.SET_DEAL_VALUE:
            await self._action_set_deal_value(config, execution)

        elif action_type == WorkflowActionType.SEND_NOTIFICATION:
            await self._action_send_notification(config, execution, business_id)

        elif action_type == WorkflowActionType.AI_WAIT:
            delay = await self._action_ai_wait(config, execution, business_id)
            if delay > 0:
                action_record["status"] = "waiting"
                action_record["resume_at"] = (datetime.now(timezone.utc) + delay).isoformat()
                execution.actions_executed = execution.actions_executed + [action_record]
                await self.db.commit()
                asyncio.create_task(self._schedule_resume(execution.id, business_id, delay.total_seconds()))
                return False

        elif action_type == WorkflowActionType.START_SEQUENCE:
            await self._action_start_sequence(config, execution, business_id)

        elif action_type == WorkflowActionType.ASSIGN_AGENT:
            await self._action_assign_human(config, execution, business_id)

        elif action_type == WorkflowActionType.CREATE_SHIPMENT:
            await self._action_create_shipment(config, execution, business_id)

        elif action_type == WorkflowActionType.CREATE_APPOINTMENT:
            await self._action_create_appointment(config, execution, business_id)

        elif action_type == WorkflowActionType.SEND_REMINDER:
            await self._action_send_reminder(config, execution, business_id)

        elif action_type == WorkflowActionType.REQUEST_CONFIRMATION:
            await self._action_request_confirmation(config, execution, business_id)

        elif action_type == WorkflowActionType.REQUEST_FEEDBACK:
            await self._action_request_feedback(config, execution, business_id)

        elif action_type == WorkflowActionType.UPDATE_SERVICE_STATUS:
            await self._action_update_service_status(config, execution, business_id)

        else:
            action_record["status"] = "skipped"
            action_record["reason"] = f"Unknown action type: {action_type}"

        execution.actions_executed = execution.actions_executed + [action_record]
        await self.db.commit()
        return True

    async def _schedule_resume(self, execution_id: uuid.UUID, business_id: uuid.UUID, delay_seconds: float):
        """Schedule workflow resume after delay."""
        await asyncio.sleep(delay_seconds)
        async with AsyncSessionLocal() as db:
            engine = WorkflowEngine(db)
            await engine.execute_workflow(execution_id, business_id)

    async def _action_send_message(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Send a message via the conversation's channel, or cross-channel if target_channel is specified."""
        if not execution.conversation_id:
            return

        content = config.get("content", "")
        template = config.get("template", "")
        target_channel = config.get("target_channel")

        # If template reference, resolve content (simplified)
        if template and not content:
            content = f"[Template: {template}]"

        if not content:
            return

        # Get conversation for contact info
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return

        try:
            if target_channel:
                # Cross-channel outreach
                from app.domains.channels.models import ChannelPlatform
                from app.domains.channels.connectors import get_connector

                platform = ChannelPlatform(target_channel)
                result = await self.db.execute(
                    select(ChannelConnection).where(
                        ChannelConnection.business_id == business_id,
                        ChannelConnection.platform == platform,
                        ChannelConnection.is_active == True,
                    )
                )
                target_conn = result.scalar_one_or_none()
                if not target_conn:
                    from app.core.logger import get_logger
                    get_logger(__name__).warning(f"No active {target_channel} connection for cross-channel send")
                    return

                connector = get_connector(platform, target_conn.credentials, target_conn.settings)

                # Determine recipient based on platform
                recipient = None
                if platform == ChannelPlatform.WHATSAPP and conversation.lead_phone:
                    recipient = conversation.lead_phone
                elif platform == ChannelPlatform.EMAIL and conversation.lead_email:
                    recipient = conversation.lead_email
                elif platform in (ChannelPlatform.INSTAGRAM, ChannelPlatform.MESSENGER, ChannelPlatform.TELEGRAM, ChannelPlatform.TIKTOK):
                    recipient = conversation.external_id
                else:
                    recipient = conversation.lead_phone or conversation.lead_email or conversation.external_id

                if recipient:
                    await connector.send_message(recipient, content)
                else:
                    from app.core.logger import get_logger
                    get_logger(__name__).warning(f"No recipient found for cross-channel send to {target_channel}")
            else:
                from app.domains.channels.services import send_outbound_message
                await send_outbound_message(self.db, execution.conversation_id, content)
        except Exception as e:
            # Log but don't fail workflow
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Failed to send message: {e}")

    async def _action_send_email(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Send an email using the email connector."""
        if not execution.conversation_id:
            return

        # Get conversation to find email
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation or not conversation.lead_email:
            return

        # Find email channel
        result = await self.db.execute(
            select(Conversation.channel).where(Conversation.id == execution.conversation_id)
        )
        # Simplified: use email connector directly
        from app.domains.channels.connectors.email import EmailConnector
        connector = EmailConnector({}, {})

        subject = config.get("subject", "Mensaje de {business_name}")
        body = config.get("body", config.get("template", ""))

        try:
            await connector.send_message(conversation.lead_email, body, "text")
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Failed to send email: {e}")

    async def _action_ai_reply(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Generate an AI response using a specific agent personality and send it."""
        if not execution.conversation_id:
            return

        personality_slug = config.get("personality", "captador")
        custom_prompt = config.get("message", "")

        # Get conversation
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return

        # Build rich business context (includes voice_personality_slug if configured)
        voice_slug = None
        try:
            ctx_builder = BusinessContextBuilder(self.db)
            business_context = await ctx_builder.build_system_prompt_context(
                business_id=business_id,
                personality_slug=personality_slug,
            )
            voice_slug = business_context.pop("voice_personality_slug", None)
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Context builder error: {e}")

        # Use centralized AI reply generator with voice composition
        from app.domains.agents.ai_reply import generate_ai_response
        response_text = await generate_ai_response(
            db=self.db,
            conversation=conversation,
            personality_slug=personality_slug,
            business_id=business_id,
            custom_prompt=custom_prompt,
            voice_slug=voice_slug,
        )

        if response_text:
            from app.domains.channels.services import send_outbound_message
            await send_outbound_message(self.db, execution.conversation_id, response_text)

    async def _action_add_tag(self, config: Dict[str, Any], execution: WorkflowExecution):
        """Add a tag to the conversation."""
        if not execution.conversation_id:
            return
        tag = config.get("tag", "")
        if not tag:
            return

        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            tags = conversation.extra_data.get("tags", [])
            if tag not in tags:
                tags.append(tag)
                conversation.extra_data["tags"] = tags
                await self.db.commit()

    async def _action_webhook(self, config: Dict[str, Any], execution: WorkflowExecution):
        """Call external webhook."""
        import aiohttp
        url = config.get("url", "")
        if not url:
            return
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "execution_id": str(execution.id),
                    "workflow_id": str(execution.workflow_id),
                    "conversation_id": str(execution.conversation_id) if execution.conversation_id else None,
                    "trigger_data": execution.trigger_data,
                    "actions_executed": execution.actions_executed,
                }
                async with session.post(url, json=payload, timeout=10) as resp:
                    from app.core.logger import get_logger
                    get_logger(__name__).info(f"Webhook {url} status: {resp.status}")
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Webhook failed: {e}")

    async def _action_move_stage(self, config: Dict[str, Any], execution: WorkflowExecution):
        """Move conversation to a different stage."""
        if not execution.conversation_id:
            return
        stage = config.get("stage", "")
        if not stage:
            return

        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.extra_data["stage"] = stage
            await self.db.commit()

    async def _action_update_stage(self, config: Dict[str, Any], execution: WorkflowExecution):
        """Update conversation stage in CRM."""
        if not execution.conversation_id:
            return
        stage = config.get("stage", "")
        if not stage:
            return
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            if not conversation.extra_data:
                conversation.extra_data = {}
            conversation.extra_data["stage"] = stage
            await self.db.commit()

    async def _action_update_score(self, config: Dict[str, Any], execution: WorkflowExecution):
        """Add/subtract lead score points."""
        if not execution.conversation_id:
            return
        points = config.get("points", 0)
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            if not conversation.extra_data:
                conversation.extra_data = {}
            current_score = conversation.extra_data.get("lead_score", 0) or 0
            conversation.extra_data["lead_score"] = max(0, min(100, current_score + points))
            await self.db.commit()

    async def _action_create_deal(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Create a new deal in the CRM."""
        from app.domains.crm.models import Deal
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return
        deal = Deal(
            business_id=business_id,
            conversation_id=conversation.id,
            title=config.get("title", f"Deal: {conversation.lead_name or 'Sin nombre'}"),
            contact_name=conversation.lead_name,
            contact_email=conversation.lead_email,
            contact_phone=conversation.lead_phone,
            value=config.get("value"),
            currency=config.get("currency", "ARS"),
            stage=config.get("stage", "new_lead"),
            source_channel=conversation.lead_source if conversation.lead_source else None,
        )
        self.db.add(deal)
        await self.db.commit()
        await self.db.refresh(deal)

        # Emit event
        try:
            await emit_deal_created(
                business_id=str(business_id),
                deal_id=str(deal.id),
                conversation_id=str(conversation.id) if conversation.id else None,
                value=float(deal.value) if deal.value else None,
                stage=deal.stage.value if deal.stage else "new_lead",
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Deal event error: {e}")

    async def _action_create_shipment(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Create a shipment for the order associated with this conversation/execution."""
        if not execution.conversation_id:
            return

        # Find the most recent paid order for this conversation
        from app.domains.orders.models import Order, OrderStatus
        result = await self.db.execute(
            select(Order).where(
                Order.conversation_id == execution.conversation_id,
                Order.status.in_([OrderStatus.PAID, OrderStatus.PENDING]),
                Order.is_active == True,
            ).order_by(desc(Order.created_at)).limit(1)
        )
        order = result.scalar_one_or_none()
        if not order:
            return

        from app.domains.shipments import services as shipment_services
        try:
            shipment_data = {
                "order_id": order.id,
                "config_id": config.get("config_id"),
                "carrier": config.get("carrier", "local"),
                "service_type": config.get("service_type", "standard"),
                "package": config.get("package", {"weight_kg": 1.0}),
                "shipping_cost": config.get("shipping_cost"),
                "auto_generate_label": config.get("auto_generate_label", False),
                "notify_customer": config.get("notify_customer", True),
                "notification_channel": config.get("notification_channel"),
            }
            await shipment_services.create_shipment(self.db, business_id, shipment_data)
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Shipment creation error: {e}")

    async def _action_create_appointment(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Create an appointment for a service order."""
        if not execution.conversation_id:
            return
        from app.domains.orders.models import Order, OrderStatus
        result = await self.db.execute(
            select(Order).where(
                Order.conversation_id == execution.conversation_id,
                Order.status.in_([OrderStatus.PAID, OrderStatus.PENDING]),
                Order.is_active == True,
            ).order_by(desc(Order.created_at)).limit(1)
        )
        order = result.scalar_one_or_none()
        if not order:
            return

        from app.domains.services import services as svc_services
        try:
            # Create service delivery first
            delivery_data = {
                "order_id": order.id,
                "catalog_item_id": config.get("catalog_item_id"),
                "conversation_id": execution.conversation_id,
                "scheduled_at": config.get("scheduled_at"),
                "modality": config.get("modality"),
                "solution_type": config.get("solution_type"),
                "estimated_duration_minutes": config.get("duration_minutes", 60),
            }
            delivery = await svc_services.create_service_delivery(self.db, business_id, delivery_data)

            # Create appointment linked to delivery
            from datetime import timedelta
            start = config.get("scheduled_at")
            if start:
                end = start + timedelta(minutes=config.get("duration_minutes", 60))
                appt_data = {
                    "service_delivery_id": delivery.id,
                    "order_id": order.id,
                    "conversation_id": execution.conversation_id,
                    "client_name": order.customer_name,
                    "client_email": order.customer_email,
                    "client_phone": order.customer_phone,
                    "start_time": start,
                    "end_time": end,
                    "modality": config.get("modality"),
                    "solution_type": config.get("solution_type"),
                    "service_name": config.get("service_name"),
                    "meeting_url": config.get("meeting_url"),
                }
                await svc_services.create_appointment(self.db, business_id, appt_data)
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Appointment creation error: {e}")

    async def _action_send_reminder(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Send reminder for an upcoming appointment."""
        appt_id = config.get("appointment_id")
        if not appt_id:
            return
        from app.domains.services import services as svc_services
        try:
            appt = await svc_services.get_appointment(self.db, appt_id)
            if appt:
                await svc_services.send_appointment_reminder(self.db, appt, config.get("channel", "whatsapp"))
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Send reminder error: {e}")

    async def _action_request_confirmation(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Request appointment confirmation from client."""
        appt_id = config.get("appointment_id")
        if not appt_id:
            return
        from app.domains.services import services as svc_services
        try:
            appt = await svc_services.get_appointment(self.db, appt_id)
            if appt:
                await svc_services.request_confirmation(self.db, appt, config.get("channel", "whatsapp"))
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Request confirmation error: {e}")

    async def _action_request_feedback(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Request feedback after service completion."""
        appt_id = config.get("appointment_id")
        if not appt_id:
            return
        from app.domains.services import services as svc_services
        try:
            appt = await svc_services.get_appointment(self.db, appt_id)
            if appt:
                await svc_services.request_feedback(self.db, appt, config.get("channel", "whatsapp"))
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Request feedback error: {e}")

    async def _action_update_service_status(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Update service delivery status."""
        delivery_id = config.get("delivery_id")
        if not delivery_id:
            return
        from app.domains.services import services as svc_services
        try:
            delivery = await svc_services.get_service_delivery(self.db, delivery_id)
            if delivery and config.get("status"):
                delivery.status = config["status"]
                await self.db.commit()
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Update service status error: {e}")

    async def _action_set_deal_value(self, config: Dict[str, Any], execution: WorkflowExecution):
        """Set deal value on the conversation."""
        if not execution.conversation_id:
            return
        value = config.get("value")
        if value is None:
            return
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            if not conversation.extra_data:
                conversation.extra_data = {}
            conversation.extra_data["deal_value"] = value
            await self.db.commit()

    async def _action_send_notification(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Send a notification to the business owner with expert voice."""
        from app.domains.users.models import User
        from app.domains.businesses.models import Business
        from app.domains.agents.ai_reply import generate_raw_ai_response
        from app.domains.channels.connectors.email import EmailConnector

        result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        if not business:
            return

        result = await self.db.execute(
            select(User).where(User.id == business.user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.email:
            from app.core.logger import get_logger
            get_logger(__name__).warning(f"No user/email for business {business_id}")
            return

        raw_message = config.get("message", "Evento importante en tu pipeline de ventas")
        voice_slug = config.get("voice_personality_slug", "hormozi")

        # Generate notification with expert voice
        try:
            system_prompt = compose_system_prompt(
                base_slug="sales-manager",
                voice_slug=voice_slug,
                business_context={"business_name": business.name},
            )
            user_prompt = f"""Escribe una notificación corta y accionable para el dueño de negocio.

EVENTO: {raw_message}

Instrucciones:
- Máximo 3 oraciones.
- Tono directo, sin fluff.
- Incluye 1 acción concreta si aplica.
- Responde SOLO el texto de la notificación."""

            notification_text = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=200,
                temperature=0.6,
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).warning(f"AI generation failed, using raw: {e}")
            notification_text = raw_message

        notification_text = notification_text or raw_message

        # Send email notification
        try:
            connector = EmailConnector({}, {})
            subject = config.get("subject", f"🔔 {business.name} — Alerta de Ventas")
            await connector.send_message(user.email, notification_text, "text")
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Notification sent to user: {notification_text[:80]}...")
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Email send failed: {e}")

        # Also store in conversation extra_data if applicable
        if execution.conversation_id:
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == execution.conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                if not conversation.extra_data:
                    conversation.extra_data = {}
                notifications = conversation.extra_data.get("owner_notifications", [])
                notifications.append({
                    "message": notification_text,
                    "raw_message": raw_message,
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                })
                conversation.extra_data["owner_notifications"] = notifications
                await self.db.commit()

    async def _action_start_sequence(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Start an email sequence for the conversation's lead."""
        from app.domains.automations.models import EmailSequence, SequenceSubscription
        sequence_id = config.get("sequence_id")
        if not sequence_id:
            return

        result = await self.db.execute(
            select(EmailSequence).where(
                EmailSequence.id == sequence_id,
                EmailSequence.business_id == business_id,
                EmailSequence.is_active == True,
            )
        )
        sequence = result.scalar_one_or_none()
        if not sequence:
            from app.core.logger import get_logger
            get_logger(__name__).warning(f"Sequence not found: {sequence_id}")
            return

        if execution.conversation_id:
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == execution.conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation or not conversation.lead_email:
                from app.core.logger import get_logger
                get_logger(__name__).warning(f"Conversation {execution.conversation_id} has no email, skipping sequence")
                return

            # Check if already subscribed
            existing = await self.db.execute(
                select(SequenceSubscription).where(
                    SequenceSubscription.sequence_id == sequence_id,
                    SequenceSubscription.conversation_id == execution.conversation_id,
                )
            )
            if existing.scalar_one_or_none():
                from app.core.logger import get_logger
                get_logger(__name__).info(f"Conversation already subscribed to sequence {sequence_id}")
                return

            sub = SequenceSubscription(
                sequence_id=sequence_id,
                conversation_id=execution.conversation_id,
                business_id=business_id,
                current_step_index=0,
                status="active",
            )
            self.db.add(sub)
            await self.db.commit()
            from app.core.logger import get_logger
            get_logger(__name__).info(f"Sequence {sequence_id} started for conversation {execution.conversation_id}")

    async def _action_assign_human(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID):
        """Assign conversation to human agent (handoff)."""
        if not execution.conversation_id:
            return

        result = await self.db.execute(
            select(Conversation).where(Conversation.id == execution.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return

        reason = config.get("reason", "Asignación manual desde workflow")
        if not conversation.extra_data:
            conversation.extra_data = {}
        conversation.extra_data["awaiting_human"] = True
        conversation.extra_data["handoff_reason"] = reason
        conversation.extra_data["handoff_at"] = datetime.now(timezone.utc).isoformat()
        await self.db.commit()

        # Find channel platform
        platform = conversation.platform.value if hasattr(conversation, 'platform') and conversation.platform else "unknown"
        if not platform and conversation.channel_connection_id:
            from app.domains.channels.models import ChannelConnection
            ch_result = await self.db.execute(
                select(ChannelConnection).where(ChannelConnection.id == conversation.channel_connection_id)
            )
            ch = ch_result.scalar_one_or_none()
            if ch:
                platform = ch.platform.value if ch.platform else "unknown"

        try:
            await emit_human_handoff_required(
                business_id=str(business_id),
                conversation_id=str(conversation.id),
                platform=platform,
                reason=reason,
                lead_name=conversation.lead_name,
            )
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Handoff emit error: {e}")

    async def _action_ai_wait(self, config: Dict[str, Any], execution: WorkflowExecution, business_id: uuid.UUID) -> timedelta:
        """Use AI to determine optimal follow-up timing.

        Analyzes conversation context to recommend the best delay before next contact.
        Falls back to config defaults if AI fails.
        """
        default_delay = self._parse_delay(config)
        if default_delay.total_seconds() > 0 and not config.get("ai_optimize", False):
            return default_delay

        if not execution.conversation_id:
            return default_delay if default_delay.total_seconds() > 0 else timedelta(hours=24)

        try:
            from app.domains.agents.ai_reply import generate_raw_ai_response

            result = await self.db.execute(
                select(Conversation).where(Conversation.id == execution.conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                return default_delay if default_delay.total_seconds() > 0 else timedelta(hours=24)

            result = await self.db.execute(
                select(Message).where(
                    Message.conversation_id == conversation.id
                ).order_by(Message.created_at.desc()).limit(10)
            )
            messages = list(reversed(result.scalars().all()))
            msg_summary = "\n".join([
                f"{'Lead' if m.direction.value == 'inbound' else 'Agent'}: {m.content[:200]}"
                for m in messages
            ])

            system_prompt = """You are a sales timing optimization AI.
Your job is to analyze conversation context and recommend the optimal delay before the next follow-up.

RULES:
- Respond with ONLY a JSON object: {"hours": <number>, "reason": "<brief reason>"}
- Consider: lead responsiveness, urgency signals, day of week, time of day, previous delays.
- Minimum 1 hour, maximum 168 hours (7 days).
- Be concise."""

            user_prompt = f"""Analyze this conversation and recommend the optimal follow-up delay:

{msg_summary}

Respond with JSON only: {{"hours": <number>, "reason": "<brief reason>"}}"""

            ai_response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=100,
                temperature=0.3,
            )

            if ai_response:
                import json
                try:
                    data = json.loads(ai_response.strip())
                    hours = float(data.get("hours", 24))
                    hours = max(1, min(168, hours))
                    from app.core.logger import get_logger
                    get_logger(__name__).info(f"Optimized delay: {hours}h — {data.get('reason', '')}")
                    return timedelta(hours=hours)
                except (json.JSONDecodeError, ValueError) as e:
                    from app.core.logger import get_logger
                    get_logger(__name__).error(f"JSON parse failed: {e}")
        except Exception as e:
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Optimization failed: {e}")

        return default_delay if default_delay.total_seconds() > 0 else timedelta(hours=24)

    def _parse_delay(self, config: Dict[str, Any]) -> timedelta:
        """Parse delay config into timedelta."""
        if "days" in config:
            return timedelta(days=config["days"])
        if "hours" in config:
            return timedelta(hours=config["hours"])
        if "minutes" in config:
            return timedelta(minutes=config["minutes"])
        if "seconds" in config:
            return timedelta(seconds=config["seconds"])
        return timedelta(0)


# Global engine instance for background processing
_engine_instance: Optional[WorkflowEngine] = None


def get_engine_instance() -> Optional[WorkflowEngine]:
    return _engine_instance


async def set_engine_instance(engine: WorkflowEngine):
    global _engine_instance
    _engine_instance = engine


class WorkflowScheduler:
    """Background scheduler that periodically checks for pending workflow executions."""

    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the scheduler loop."""
        self._running = True
        self._task = asyncio.create_task(self._loop())
        from app.core.logger import get_logger
        get_logger(__name__).info("Workflow scheduler started")

    async def stop(self):
        """Stop the scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        from app.core.logger import get_logger
        get_logger(__name__).info("Workflow scheduler stopped")

    async def _loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_pending_executions()
            except Exception as e:
                from app.core.logger import get_logger
                get_logger(__name__).error(f"Error in check loop: {e}")
            await asyncio.sleep(self.check_interval)

    async def _check_pending_executions(self):
        """Check for executions that are waiting and ready to resume."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.status == "running",
                ).order_by(WorkflowExecution.executed_at)
            )
            executions = result.scalars().all()

            now = datetime.now(timezone.utc)
            for execution in executions:
                # Check if last action was a wait that's now expired
                actions = execution.actions_executed or []
                if not actions:
                    continue

                last_action = actions[-1]
                if last_action.get("status") == "waiting":
                    resume_at_str = last_action.get("resume_at")
                    if resume_at_str:
                        resume_at = datetime.fromisoformat(resume_at_str.replace("Z", "+00:00"))
                        if now >= resume_at:
                            # Resume execution via Celery
                            wf_result = await db.execute(
                                select(Workflow).where(Workflow.id == execution.workflow_id)
                            )
                            workflow = wf_result.scalar_one_or_none()
                            if workflow:
                                try:
                                    from app.tasks.workflow_tasks import execute_workflow_task
                                    execute_workflow_task.delay(str(execution.id), str(workflow.business_id))
                                except Exception as e:
                                    from app.core.logger import get_logger
                                    get_logger(__name__).warning(f"Celery fallback: {e}")
                                    engine = WorkflowEngine(db)
                                    asyncio.create_task(engine._run_execution(execution.id, workflow.business_id))
