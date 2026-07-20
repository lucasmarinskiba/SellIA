"""SellIA Pipeline Automations — Motor de automatizaciones inteligentes por etapa.

Cada trigger detecta eventos en el pipeline y dispara acciones coordinadas
entre múltiples agentes. El sistema opera 24/7 sin intervención humana.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.logger import get_logger
from app.domains.agents.pipeline_agents import PipelineStage, PipelineContext

logger = get_logger(__name__)


# ─────────────────────────────────────────────
# TIPOS DE TRIGGERS
# ─────────────────────────────────────────────

class TriggerType(str, Enum):
    # Eventos de tiempo
    INACTIVITY_24H = "inactivity_24h"
    INACTIVITY_72H = "inactivity_72h"
    INACTIVITY_7D = "inactivity_7d"
    INACTIVITY_30D = "inactivity_30d"

    # Eventos de conversación
    NEW_MESSAGE_RECEIVED = "new_message_received"
    KEYWORD_DETECTED = "keyword_detected"
    SENTIMENT_NEGATIVE = "sentiment_negative"
    BUYING_SIGNAL_DETECTED = "buying_signal_detected"
    OBJECTION_DETECTED = "objection_detected"

    # Eventos de CRM
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    LEAD_SCORE_THRESHOLD = "lead_score_threshold"
    DEAL_STALLED = "deal_stalled"
    NO_REPLY = "no_reply"

    # Eventos de tiempo de negocio
    PROPOSAL_SENT = "proposal_sent"
    PROPOSAL_24H_NO_RESPONSE = "proposal_24h_no_response"
    PROPOSAL_48H_NO_RESPONSE = "proposal_48h_no_response"
    CLOSE_ACHIEVED = "close_achieved"

    # Eventos de post-venta
    ONBOARDING_DAY_1 = "onboarding_day_1"
    ONBOARDING_DAY_3 = "onboarding_day_3"
    ONBOARDING_DAY_7 = "onboarding_day_7"
    ONBOARDING_DAY_30 = "onboarding_day_30"

    # Eventos de retención
    CHURN_RISK_DETECTED = "churn_risk_detected"
    NPS_LOW = "nps_low"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    REFERRAL_MOMENT = "referral_moment"


class ActionType(str, Enum):
    SEND_MESSAGE = "send_message"
    ASSIGN_AGENT = "assign_agent"
    UPDATE_CRM = "update_crm"
    ADVANCE_STAGE = "advance_stage"
    GENERATE_CONTENT = "generate_content"
    SEND_PROPOSAL = "send_proposal"
    SCHEDULE_FOLLOWUP = "schedule_followup"
    ALERT_OWNER = "alert_owner"
    ESCALATE_HUMAN = "escalate_human"
    ACTIVATE_WORKFLOW = "activate_workflow"
    SEND_NURTURE_CONTENT = "send_nurture_content"
    REQUEST_REFERRAL = "request_referral"
    SEND_NPS = "send_nps"


@dataclass
class AutomationRule:
    """Regla de automatización: si [trigger] entonces [acciones]."""
    id: str
    name: str
    trigger: TriggerType
    stage: PipelineStage
    conditions: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    cooldown_hours: int = 24
    is_active: bool = True
    priority: int = 5  # 1=crítico, 10=bajo

    def evaluate_conditions(self, context: dict[str, Any]) -> bool:
        """Evalúa si todas las condiciones se cumplen para disparar."""
        for condition in self.conditions:
            field_val = context.get(condition.get("field", ""))
            operator = condition.get("operator", "eq")
            expected = condition.get("value")

            if operator == "eq" and field_val != expected:
                return False
            elif operator == "gt" and not (isinstance(field_val, (int, float)) and field_val > expected):
                return False
            elif operator == "lt" and not (isinstance(field_val, (int, float)) and field_val < expected):
                return False
            elif operator == "contains" and expected not in str(field_val):
                return False
            elif operator == "not_null" and field_val is None:
                return False
        return True


# ─────────────────────────────────────────────
# REGLAS DE AUTOMATIZACIÓN PREDEFINIDAS
# ─────────────────────────────────────────────

PIPELINE_AUTOMATION_RULES: list[AutomationRule] = [

    # ───── ETAPA 1: PROSPECCIÓN ─────
    AutomationRule(
        id="capture-welcome-message",
        name="Bienvenida inmediata al nuevo lead",
        trigger=TriggerType.NEW_MESSAGE_RECEIVED,
        stage=PipelineStage.PROSPECTING,
        conditions=[{"field": "is_first_contact", "operator": "eq", "value": True}],
        actions=[
            {
                "type": ActionType.ASSIGN_AGENT,
                "agent_stage": PipelineStage.PROSPECTING,
                "reason": "primer contacto",
            },
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "welcome_first_contact",
                "delay_seconds": 0,
            },
            {
                "type": ActionType.UPDATE_CRM,
                "fields": {"status": "new_lead", "first_contact_at": "now"},
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    AutomationRule(
        id="prospect-no-reply-24h",
        name="Follow-up si no responde en 24h",
        trigger=TriggerType.INACTIVITY_24H,
        stage=PipelineStage.PROSPECTING,
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "followup_24h_soft",
                "delay_seconds": 0,
            },
        ],
        cooldown_hours=24,
        priority=3,
    ),

    AutomationRule(
        id="prospect-no-reply-72h",
        name="Follow-up 72h con oferta de valor",
        trigger=TriggerType.INACTIVITY_72H,
        stage=PipelineStage.PROSPECTING,
        actions=[
            {
                "type": ActionType.GENERATE_CONTENT,
                "content_type": "lead_magnet",
                "send_via": "channel",
            },
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "followup_72h_value",
                "delay_seconds": 300,
            },
        ],
        cooldown_hours=48,
        priority=3,
    ),

    # ───── ETAPA 2: CALIFICACIÓN ─────
    AutomationRule(
        id="qualify-buying-signal",
        name="Señal de compra detectada — calificar urgente",
        trigger=TriggerType.BUYING_SIGNAL_DETECTED,
        stage=PipelineStage.PROSPECTING,
        actions=[
            {
                "type": ActionType.ASSIGN_AGENT,
                "agent_stage": PipelineStage.QUALIFYING,
            },
            {
                "type": ActionType.ADVANCE_STAGE,
                "to_stage": PipelineStage.QUALIFYING,
            },
            {
                "type": ActionType.UPDATE_CRM,
                "fields": {"priority": "high", "buying_signal_at": "now"},
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    AutomationRule(
        id="qualify-high-score-advance",
        name="Score alto — avanzar a diagnóstico",
        trigger=TriggerType.LEAD_SCORE_THRESHOLD,
        stage=PipelineStage.QUALIFYING,
        conditions=[{"field": "qualification_score", "operator": "gt", "value": 69}],
        actions=[
            {
                "type": ActionType.ADVANCE_STAGE,
                "to_stage": PipelineStage.DISCOVERY,
            },
            {
                "type": ActionType.ASSIGN_AGENT,
                "agent_stage": PipelineStage.DISCOVERY,
            },
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "advance_to_discovery",
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    AutomationRule(
        id="qualify-low-score-nurture",
        name="Score bajo — iniciar nurturing",
        trigger=TriggerType.LEAD_SCORE_THRESHOLD,
        stage=PipelineStage.QUALIFYING,
        conditions=[{"field": "qualification_score", "operator": "lt", "value": 40}],
        actions=[
            {
                "type": ActionType.ADVANCE_STAGE,
                "to_stage": PipelineStage.NURTURING,
            },
            {
                "type": ActionType.ACTIVATE_WORKFLOW,
                "workflow_type": "nurture_sequence_30d",
            },
        ],
        cooldown_hours=0,
        priority=2,
    ),

    # ───── ETAPA 3: NURTURING ─────
    AutomationRule(
        id="nurture-week1-education",
        name="Contenido educativo semana 1",
        trigger=TriggerType.DEAL_STAGE_CHANGED,
        stage=PipelineStage.NURTURING,
        conditions=[{"field": "days_in_stage", "operator": "eq", "value": 1}],
        actions=[
            {
                "type": ActionType.SEND_NURTURE_CONTENT,
                "content_type": "educational",
                "day": 1,
            },
        ],
        cooldown_hours=168,
        priority=4,
    ),

    AutomationRule(
        id="nurture-case-study",
        name="Caso de éxito día 3",
        trigger=TriggerType.DEAL_STAGE_CHANGED,
        stage=PipelineStage.NURTURING,
        conditions=[{"field": "days_in_stage", "operator": "eq", "value": 3}],
        actions=[
            {
                "type": ActionType.SEND_NURTURE_CONTENT,
                "content_type": "case_study",
                "day": 3,
            },
        ],
        cooldown_hours=168,
        priority=4,
    ),

    AutomationRule(
        id="nurture-buying-signal",
        name="Lead tibio muestra señal de compra — escalar",
        trigger=TriggerType.BUYING_SIGNAL_DETECTED,
        stage=PipelineStage.NURTURING,
        actions=[
            {
                "type": ActionType.ASSIGN_AGENT,
                "agent_stage": PipelineStage.QUALIFYING,
                "reason": "buying signal en nurturing",
            },
            {
                "type": ActionType.ALERT_OWNER,
                "message": "Lead en nurturing mostró señal de compra — revisar urgente.",
                "priority": "high",
            },
            {
                "type": ActionType.UPDATE_CRM,
                "fields": {"status": "hot_lead", "reactivated_at": "now"},
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    # ───── ETAPA 4: DIAGNÓSTICO ─────
    AutomationRule(
        id="discovery-pain-identified",
        name="Dolor identificado — preparar propuesta",
        trigger=TriggerType.KEYWORD_DETECTED,
        stage=PipelineStage.DISCOVERY,
        conditions=[{"field": "pain_points_count", "operator": "gt", "value": 2}],
        actions=[
            {
                "type": ActionType.UPDATE_CRM,
                "fields": {"discovery_complete": True},
            },
            {
                "type": ActionType.GENERATE_CONTENT,
                "content_type": "proposal_draft",
                "based_on": "pain_points",
            },
        ],
        cooldown_hours=0,
        priority=2,
    ),

    AutomationRule(
        id="discovery-stalled-3d",
        name="Diagnóstico sin avance 3 días — intervención",
        trigger=TriggerType.DEAL_STALLED,
        stage=PipelineStage.DISCOVERY,
        conditions=[{"field": "days_in_stage", "operator": "gt", "value": 3}],
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "discovery_reactivation",
            },
            {
                "type": ActionType.ALERT_OWNER,
                "message": "Deal en diagnóstico lleva +3 días sin avance.",
            },
        ],
        cooldown_hours=72,
        priority=3,
    ),

    # ───── ETAPA 5: PROPUESTA ─────
    AutomationRule(
        id="proposal-sent-followup-24h",
        name="Follow-up 24h después de enviar propuesta",
        trigger=TriggerType.PROPOSAL_24H_NO_RESPONSE,
        stage=PipelineStage.PROPOSAL,
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "proposal_followup_24h",
            },
        ],
        cooldown_hours=24,
        priority=2,
    ),

    AutomationRule(
        id="proposal-followup-48h",
        name="Follow-up urgente 48h sin respuesta a propuesta",
        trigger=TriggerType.PROPOSAL_48H_NO_RESPONSE,
        stage=PipelineStage.PROPOSAL,
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "proposal_urgency_followup",
            },
            {
                "type": ActionType.ALERT_OWNER,
                "message": "Propuesta sin respuesta en 48h — revisar y contactar.",
            },
        ],
        cooldown_hours=24,
        priority=2,
    ),

    # ───── ETAPA 6: OBJECIONES ─────
    AutomationRule(
        id="objection-price-detected",
        name="Objeción de precio detectada",
        trigger=TriggerType.OBJECTION_DETECTED,
        stage=PipelineStage.OBJECTION,
        conditions=[{"field": "objection_type", "operator": "eq", "value": "price"}],
        actions=[
            {
                "type": ActionType.ASSIGN_AGENT,
                "agent_stage": PipelineStage.OBJECTION,
            },
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "objection_price_response",
                "delay_seconds": 60,
            },
            {
                "type": ActionType.UPDATE_CRM,
                "fields": {"objection_price": True},
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    AutomationRule(
        id="objection-think-about-it",
        name="Objeción 'necesito pensarlo' detectada",
        trigger=TriggerType.OBJECTION_DETECTED,
        stage=PipelineStage.OBJECTION,
        conditions=[{"field": "objection_type", "operator": "eq", "value": "think_about_it"}],
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "objection_think_isolate",
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    AutomationRule(
        id="objection-negative-sentiment",
        name="Sentimiento muy negativo — escalar a humano",
        trigger=TriggerType.SENTIMENT_NEGATIVE,
        stage=PipelineStage.OBJECTION,
        conditions=[{"field": "sentiment_score", "operator": "lt", "value": -0.7}],
        actions=[
            {
                "type": ActionType.ESCALATE_HUMAN,
                "reason": "Sentimiento extremadamente negativo detectado",
                "urgency": "high",
            },
            {
                "type": ActionType.ALERT_OWNER,
                "message": "⚠️ Lead con sentimiento muy negativo — intervención humana recomendada.",
                "priority": "critical",
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    # ───── ETAPA 7: CIERRE ─────
    AutomationRule(
        id="close-buying-signal-urgent",
        name="Señal de cierre detectada — actuar en 5 minutos",
        trigger=TriggerType.BUYING_SIGNAL_DETECTED,
        stage=PipelineStage.CLOSING,
        actions=[
            {
                "type": ActionType.ASSIGN_AGENT,
                "agent_stage": PipelineStage.CLOSING,
            },
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "close_buying_signal_response",
                "delay_seconds": 60,
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    AutomationRule(
        id="close-achieved-celebrate",
        name="¡Venta cerrada! — iniciar onboarding",
        trigger=TriggerType.CLOSE_ACHIEVED,
        stage=PipelineStage.CLOSING,
        actions=[
            {
                "type": ActionType.ADVANCE_STAGE,
                "to_stage": PipelineStage.ONBOARDING,
            },
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "welcome_new_client",
                "delay_seconds": 0,
            },
            {
                "type": ActionType.UPDATE_CRM,
                "fields": {"status": "client", "closed_at": "now"},
            },
            {
                "type": ActionType.ACTIVATE_WORKFLOW,
                "workflow_type": "onboarding_sequence_30d",
            },
            {
                "type": ActionType.ALERT_OWNER,
                "message": "🎉 ¡Nueva venta cerrada! Onboarding iniciado automáticamente.",
                "priority": "info",
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    # ───── ETAPA 8: ONBOARDING ─────
    AutomationRule(
        id="onboarding-day-1",
        name="Onboarding día 1 — bienvenida y quick win",
        trigger=TriggerType.ONBOARDING_DAY_1,
        stage=PipelineStage.ONBOARDING,
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "onboarding_day1_welcome",
            },
            {
                "type": ActionType.ASSIGN_AGENT,
                "agent_stage": PipelineStage.ONBOARDING,
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    AutomationRule(
        id="onboarding-day-3-checkin",
        name="Onboarding día 3 — check-in de primera victoria",
        trigger=TriggerType.ONBOARDING_DAY_3,
        stage=PipelineStage.ONBOARDING,
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "onboarding_day3_checkin",
            },
        ],
        cooldown_hours=0,
        priority=2,
    ),

    AutomationRule(
        id="onboarding-day-7-roadmap",
        name="Onboarding día 7 — roadmap de 30 días",
        trigger=TriggerType.ONBOARDING_DAY_7,
        stage=PipelineStage.ONBOARDING,
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "onboarding_day7_roadmap",
            },
        ],
        cooldown_hours=0,
        priority=2,
    ),

    AutomationRule(
        id="onboarding-day-30-results",
        name="Onboarding día 30 — revisión de resultados y testimonio",
        trigger=TriggerType.ONBOARDING_DAY_30,
        stage=PipelineStage.ONBOARDING,
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "onboarding_day30_review",
            },
            {
                "type": ActionType.ADVANCE_STAGE,
                "to_stage": PipelineStage.RETENTION,
            },
            {
                "type": ActionType.REQUEST_REFERRAL,
                "delay_days": 3,
            },
        ],
        cooldown_hours=0,
        priority=2,
    ),

    # ───── ETAPA 9: RETENCIÓN ─────
    AutomationRule(
        id="retention-churn-risk",
        name="Riesgo de churn detectado — intervención urgente",
        trigger=TriggerType.CHURN_RISK_DETECTED,
        stage=PipelineStage.RETENTION,
        actions=[
            {
                "type": ActionType.ALERT_OWNER,
                "message": "⚠️ Cliente en riesgo de churn — contactar en menos de 4 horas.",
                "priority": "critical",
            },
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "churn_risk_recovery",
                "delay_seconds": 1800,
            },
            {
                "type": ActionType.UPDATE_CRM,
                "fields": {"churn_risk": True, "churn_risk_at": "now"},
            },
        ],
        cooldown_hours=48,
        priority=1,
    ),

    AutomationRule(
        id="retention-nps-low",
        name="NPS bajo — recuperación inmediata",
        trigger=TriggerType.NPS_LOW,
        stage=PipelineStage.RETENTION,
        conditions=[{"field": "nps_score", "operator": "lt", "value": 7}],
        actions=[
            {
                "type": ActionType.ALERT_OWNER,
                "message": "📉 NPS bajo recibido — llamar al cliente hoy.",
                "priority": "high",
            },
            {
                "type": ActionType.ESCALATE_HUMAN,
                "reason": "NPS bajo requiere intervención personal",
                "urgency": "high",
            },
        ],
        cooldown_hours=0,
        priority=1,
    ),

    AutomationRule(
        id="retention-upsell-moment",
        name="Momento de upsell — cliente con éxito demostrado",
        trigger=TriggerType.UPSELL_OPPORTUNITY,
        stage=PipelineStage.RETENTION,
        actions=[
            {
                "type": ActionType.SEND_MESSAGE,
                "template": "upsell_opportunity_pitch",
                "delay_seconds": 3600,
            },
            {
                "type": ActionType.UPDATE_CRM,
                "fields": {"upsell_offered_at": "now"},
            },
        ],
        cooldown_hours=720,
        priority=3,
    ),

    AutomationRule(
        id="retention-referral-request",
        name="Solicitud de referido en momento de alta satisfacción",
        trigger=TriggerType.REFERRAL_MOMENT,
        stage=PipelineStage.RETENTION,
        actions=[
            {
                "type": ActionType.REQUEST_REFERRAL,
                "template": "referral_request_satisfied",
            },
            {
                "type": ActionType.SEND_NPS,
                "delay_days": 7,
            },
        ],
        cooldown_hours=2160,
        priority=3,
    ),
]


# ─────────────────────────────────────────────
# MOTOR DE EJECUCIÓN DE AUTOMATIZACIONES
# ─────────────────────────────────────────────

class PipelineAutomationEngine:
    """Motor autónomo que evalúa y ejecuta reglas de automatización del pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rules = PIPELINE_AUTOMATION_RULES

    async def process_event(
        self,
        trigger: TriggerType,
        context: dict[str, Any],
        business_id: str,
        deal_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Procesa un evento y ejecuta todas las reglas aplicables."""
        results = []
        current_stage = PipelineStage(context.get("current_stage", PipelineStage.PROSPECTING))

        applicable_rules = [
            rule for rule in self.rules
            if rule.trigger == trigger
            and (rule.stage == current_stage or trigger in {
                TriggerType.BUYING_SIGNAL_DETECTED,
                TriggerType.SENTIMENT_NEGATIVE,
                TriggerType.CHURN_RISK_DETECTED,
            })
            and rule.is_active
            and rule.evaluate_conditions(context)
        ]

        # Ordenar por prioridad (1=más urgente)
        applicable_rules.sort(key=lambda r: r.priority)

        for rule in applicable_rules:
            try:
                result = await self._execute_rule(rule, context, business_id, deal_id)
                results.append({"rule": rule.id, "status": "executed", "result": result})
                logger.info(f"[PipelineAuto] Rule '{rule.name}' executed for deal {deal_id}")
            except Exception as e:
                results.append({"rule": rule.id, "status": "error", "error": str(e)})
                logger.error(f"[PipelineAuto] Rule '{rule.name}' failed: {e}")

        return results

    async def _execute_rule(
        self,
        rule: AutomationRule,
        context: dict[str, Any],
        business_id: str,
        deal_id: Optional[str],
    ) -> dict[str, Any]:
        """Ejecuta las acciones de una regla."""
        executed_actions = []

        for action in rule.actions:
            action_type = ActionType(action["type"])
            delay = action.get("delay_seconds", 0)

            if delay > 0:
                await asyncio.sleep(min(delay, 5))

            action_result = await self._dispatch_action(
                action_type, action, context, business_id, deal_id
            )
            executed_actions.append({
                "action": action_type,
                "result": action_result,
            })

        return {"actions_executed": len(executed_actions), "details": executed_actions}

    async def _dispatch_action(
        self,
        action_type: ActionType,
        action: dict[str, Any],
        context: dict[str, Any],
        business_id: str,
        deal_id: Optional[str],
    ) -> dict[str, Any]:
        """Despacha una acción específica al sistema correspondiente."""

        if action_type == ActionType.SEND_MESSAGE:
            return await self._send_automated_message(action, context, business_id)

        elif action_type == ActionType.UPDATE_CRM:
            return await self._update_crm(action["fields"], deal_id, business_id)

        elif action_type == ActionType.ADVANCE_STAGE:
            to_stage = PipelineStage(action["to_stage"])
            return await self._advance_pipeline_stage(deal_id, to_stage, business_id)

        elif action_type == ActionType.ALERT_OWNER:
            return await self._send_owner_alert(action, business_id)

        elif action_type == ActionType.ACTIVATE_WORKFLOW:
            return await self._activate_workflow(action, business_id, context)

        elif action_type == ActionType.ESCALATE_HUMAN:
            return await self._escalate_to_human(action, context, business_id, deal_id)

        elif action_type == ActionType.GENERATE_CONTENT:
            return await self._generate_ai_content(action, context, business_id)

        elif action_type == ActionType.REQUEST_REFERRAL:
            return await self._send_referral_request(action, context, business_id)

        elif action_type == ActionType.SEND_NPS:
            return await self._schedule_nps(action, context, business_id)

        return {"status": "no_handler", "action": action_type}

    async def _send_automated_message(
        self, action: dict, context: dict, business_id: str
    ) -> dict:
        """Genera y envía mensaje automatizado vía canal del prospecto."""
        try:
            from app.domains.channels.services import send_outbound_message
            from app.domains.agents.ai_reply import generate_raw_ai_response

            conversation_id = context.get("conversation_id")
            if not conversation_id:
                return {"status": "skipped", "reason": "no_conversation_id"}

            template = action.get("template", "")
            message_content = self._get_message_template(template, context)

            await send_outbound_message(
                db=self.db,
                conversation_id=uuid.UUID(conversation_id),
                content=message_content,
                sender_type="agent",
            )

            return {"status": "sent", "template": template}
        except Exception as e:
            logger.error(f"[PipelineAuto] Message send error: {e}")
            return {"status": "error", "error": str(e)}

    async def _update_crm(self, fields: dict, deal_id: Optional[str], business_id: str) -> dict:
        """Actualiza campos del deal en el CRM."""
        try:
            if not deal_id:
                return {"status": "skipped", "reason": "no_deal_id"}

            from app.domains.crm.models import Deal
            now = datetime.now(timezone.utc)

            resolved_fields = {
                k: now if v == "now" else v
                for k, v in fields.items()
            }

            await self.db.execute(
                update(Deal)
                .where(Deal.id == uuid.UUID(deal_id))
                .values(**resolved_fields)
            )
            await self.db.commit()
            return {"status": "updated", "fields": list(resolved_fields.keys())}
        except Exception as e:
            logger.error(f"[PipelineAuto] CRM update error: {e}")
            return {"status": "error", "error": str(e)}

    async def _advance_pipeline_stage(
        self, deal_id: Optional[str], to_stage: PipelineStage, business_id: str
    ) -> dict:
        """Avanza el deal a la siguiente etapa del pipeline."""
        try:
            if not deal_id:
                return {"status": "skipped", "reason": "no_deal_id"}

            from app.domains.crm.models import Deal
            await self.db.execute(
                update(Deal)
                .where(Deal.id == uuid.UUID(deal_id))
                .values(
                    pipeline_stage=to_stage.value,
                    stage_changed_at=datetime.now(timezone.utc),
                )
            )
            await self.db.commit()
            logger.info(f"[PipelineAuto] Deal {deal_id} advanced to {to_stage}")
            return {"status": "advanced", "to_stage": to_stage.value}
        except Exception as e:
            logger.error(f"[PipelineAuto] Stage advance error: {e}")
            return {"status": "error", "error": str(e)}

    async def _send_owner_alert(self, action: dict, business_id: str) -> dict:
        """Envía alerta al dueño del negocio."""
        try:
            from app.domains.alerts.models import Alert, AlertSeverity
            alert = Alert(
                business_id=uuid.UUID(business_id),
                title=f"[SellIA Auto] {action.get('message', 'Alerta del pipeline')}",
                message=action.get("message", ""),
                severity=AlertSeverity.HIGH if action.get("priority") in ("critical", "high") else AlertSeverity.MEDIUM,
                is_read=False,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(alert)
            await self.db.commit()
            return {"status": "alert_created"}
        except Exception as e:
            logger.error(f"[PipelineAuto] Alert send error: {e}")
            return {"status": "error", "error": str(e)}

    async def _activate_workflow(self, action: dict, business_id: str, context: dict) -> dict:
        """Activa un workflow de automaciones existente."""
        try:
            from app.domains.automations.models import Workflow, WorkflowStatus
            workflow_type = action.get("workflow_type", "")

            result = await self.db.execute(
                select(Workflow).where(
                    Workflow.business_id == uuid.UUID(business_id),
                    Workflow.name.ilike(f"%{workflow_type.replace('_', ' ')}%"),
                    Workflow.is_active == True,
                )
            )
            workflow = result.scalar_one_or_none()

            if workflow and workflow.status == WorkflowStatus.PAUSED:
                workflow.status = WorkflowStatus.ACTIVE
                await self.db.commit()
                return {"status": "workflow_activated", "workflow_id": str(workflow.id)}

            return {"status": "workflow_not_found", "type": workflow_type}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _escalate_to_human(
        self, action: dict, context: dict, business_id: str, deal_id: Optional[str]
    ) -> dict:
        """Escala la conversación a un humano."""
        try:
            conversation_id = context.get("conversation_id")
            if not conversation_id:
                return {"status": "skipped"}

            from app.domains.channels.models import Conversation
            await self.db.execute(
                update(Conversation)
                .where(Conversation.id == uuid.UUID(conversation_id))
                .values(
                    needs_human=True,
                    human_requested_at=datetime.now(timezone.utc),
                    human_request_reason=action.get("reason", "Escalación automática"),
                )
            )
            await self.db.commit()

            await self._send_owner_alert(
                {"message": f"🙋 Conversación requiere atención humana: {action.get('reason', '')}", "priority": action.get("urgency", "high")},
                business_id,
            )

            return {"status": "escalated"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _generate_ai_content(self, action: dict, context: dict, business_id: str) -> dict:
        """Genera contenido de IA para el prospecto."""
        try:
            from app.domains.agents.ai_reply import generate_raw_ai_response
            content_type = action.get("content_type", "")

            prompts = {
                "proposal_draft": f"Genera un borrador de propuesta para cliente con dolores: {context.get('pain_points', [])}",
                "lead_magnet": f"Genera un recurso de valor gratuito relevante para: {context.get('product_name', 'el producto')}",
            }

            prompt = prompts.get(content_type, f"Genera contenido tipo {content_type}")
            content = await generate_raw_ai_response(
                db=self.db,
                business_id=uuid.UUID(business_id),
                system_prompt="Eres un experto generador de contenido de ventas. Genera contenido profesional y personalizado.",
                user_prompt=prompt,
                max_tokens=1000,
            )

            return {"status": "content_generated", "content_type": content_type, "length": len(content or "")}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _send_referral_request(self, action: dict, context: dict, business_id: str) -> dict:
        """Envía solicitud de referido al cliente satisfecho."""
        return await self._send_automated_message(
            {**action, "template": action.get("template", "referral_request")},
            context,
            business_id,
        )

    async def _schedule_nps(self, action: dict, context: dict, business_id: str) -> dict:
        """Programa envío de NPS para el futuro."""
        delay_days = action.get("delay_days", 7)
        return {"status": "nps_scheduled", "send_in_days": delay_days}

    def _get_message_template(self, template_name: str, context: dict) -> str:
        """Retorna el contenido del mensaje para una plantilla dada."""
        name = context.get("contact_name", "")
        product = context.get("product_name", "nuestro servicio")

        templates: dict[str, str] = {
            "welcome_first_contact": f"¡Hola{' ' + name if name else ''}! 👋 Gracias por tu interés. Soy el asistente de SellIA. ¿En qué puedo ayudarte hoy?",
            "followup_24h_soft": f"Hola{' ' + name if name else ''}! Solo quería saber si pudiste ver mi mensaje anterior. ¿Tienes alguna pregunta? 😊",
            "followup_72h_value": f"Hola{' ' + name if name else ''}! Te comparto algo que puede ser muy útil para ti sobre {product}. ¿Te parece si hablamos 10 minutos esta semana?",
            "advance_to_discovery": f"¡Genial{' ' + name if name else ''}! Me gustaría entender mejor tu situación para ver cómo podemos ayudarte mejor. ¿Podemos hablar unos minutos?",
            "objection_price_response": f"Entiendo completamente{', ' + name if name else ''} — es una inversión importante. Para ayudarte a evaluar si tiene sentido para ti, déjame preguntarte: ¿cuánto te está costando no tener esto resuelto ahora?",
            "objection_think_isolate": f"¡Claro{', ' + name if name else ''}! Es una decisión importante. Para que puedas pensar mejor — ¿cuál es la parte específica sobre la que tienes más dudas?",
            "close_buying_signal_response": f"¡Perfecto{', ' + name if name else ''}! El siguiente paso es muy simple. ¿Te envío el link para proceder ahora?",
            "welcome_new_client": f"🎉 ¡Bienvenido/a{', ' + name if name else ''} a la familia! Tomaste una excelente decisión. En los próximos minutos recibirás todo lo que necesitas para empezar. Estamos muy emocionados de trabajar contigo.",
            "onboarding_day1_welcome": f"¡Hola{' ' + name if name else ''}! ¿Pudiste acceder a todo sin problemas? El primer paso más importante que puedes hacer hoy es: [primer paso específico]. ¿Cuándo lo vas a hacer?",
            "onboarding_day3_checkin": f"Hola{' ' + name if name else ''}! 👋 ¿Cómo va todo? ¿Pudiste dar los primeros pasos? Me encantaría saber cómo te fue.",
            "onboarding_day7_roadmap": f"¡Hola{' ' + name if name else ''}! Primera semana completada. Te envío el mapa de los próximos 30 días para que veas exactamente hacia dónde vamos juntos. 🗺️",
            "onboarding_day30_review": f"¡{name or 'Hola'}! Ya pasó el primer mes juntos 🎂 Me encantaría hacer una revisión de tus resultados. ¿Cómo te fue? ¿Qué logros puedes destacar?",
            "churn_risk_recovery": f"Hola{' ' + name if name else ''}! Noté que no hemos hablado en un tiempo. ¿Cómo estás? ¿Estás obteniendo el valor que esperabas de {product}? Quiero asegurarme de que estés bien. 🙏",
            "upsell_opportunity_pitch": f"¡Hola{' ' + name if name else ''}! Vi que estás obteniendo excelentes resultados 🚀 Tengo algo que puede llevar eso al siguiente nivel. ¿Tienes 5 minutos para que te cuente?",
            "referral_request_satisfied": f"Hola{' ' + name if name else ''}! Estoy muy contento de ver tus resultados 😊 ¿Conoces a alguien que esté pasando por el mismo desafío que tú tenías? Me ayudaría muchísimo — y ellos también se beneficiarían.",
            "proposal_followup_24h": f"¡Hola{' ' + name if name else ''}! ¿Pudiste revisar la propuesta que te envié? ¿Tienes alguna pregunta?",
            "proposal_urgency_followup": f"Hola{' ' + name if name else ''}! Solo quería asegurarme de que todo esté bien. La propuesta tiene validez hasta fin de semana — ¿hay algo que necesites aclarar para avanzar?",
            "discovery_reactivation": f"Hola{' ' + name if name else ''}! Quería retomar nuestra conversación. ¿Sigues teniendo el desafío que me mencionaste? Me gustaría ayudarte a resolverlo. 🤝",
        }

        return templates.get(template_name, f"Hola{' ' + name if name else ''}! ¿En qué te puedo ayudar hoy?")


def get_pipeline_automation_engine(db: AsyncSession) -> PipelineAutomationEngine:
    return PipelineAutomationEngine(db)
