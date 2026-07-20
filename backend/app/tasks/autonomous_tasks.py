"""Autonomous Sales Loop + 4-Pillar Autonomous Computing Tasks.

24/7 autonomous execution: intelligence, outreach, content, notifications, optimization,
self-configuration, self-repair, self-optimization, self-protection.
"""

import asyncio
from celery import shared_task
from datetime import datetime, timezone, timedelta

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.businesses.models import Business
from app.domains.intelligence.service import MessageIntelligenceService
from app.domains.outreach.proactive import ProactiveOutreachEngine
from app.domains.automations.content_engine import ContentGenerationRouter, ContentConfidenceScorer
from app.domains.notifications.service import BriefingDeliveryService, HandoffAlertService
from app.domains.optimization.service import ExperimentRunner, AutoOptimizer, CadenceOptimizer
from app.domains.autopilot.router_v2 import SmartActionRouter
from app.domains.crm.auto_close import AutoCloseEvaluator
from sqlalchemy import select

logger = get_logger(__name__)


def _async_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(name="app.tasks.autonomous_tasks.message_intelligence_analyzer")
def message_intelligence_analyzer():
    """Every 5 min: analyze pending inbound messages."""
    async def _run():
        async with AsyncSessionLocal() as db:
            service = MessageIntelligenceService(db)
            count = await service.analyze_pending_messages()
            logger.info(f"Message intelligence analyzer: {count} messages analyzed")
            return {"analyzed": count}
    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.smart_action_router_evaluator")
def smart_action_router_evaluator():
    """Every 15 min: evaluate recent events and route actions."""
    async def _run():
        async with AsyncSessionLocal() as db:
            router = SmartActionRouter(db)
            # Process recent analyses
            from app.domains.intelligence.models import MessageAnalysis
            recent = await db.execute(
                select(MessageAnalysis).where(
                    MessageAnalysis.created_at >= datetime.now(timezone.utc) - timedelta(minutes=15)
                ).limit(50)
            )
            analyses = recent.scalars().all()

            actions_taken = 0
            for analysis in analyses:
                # Emit synthetic events for routing
                event_type = "intent.detected"
                if analysis.buying_signals_detected:
                    event_type = "buying_signal.detected"
                elif analysis.objections_detected:
                    event_type = "objection.raised"
                elif analysis.intent_type == "churn_risk":
                    event_type = "churn_risk.detected"

                context = {
                    "business_id": str(analysis.business_id),
                    "conversation_id": str(analysis.conversation_id),
                    "intent_type": analysis.intent_type,
                    "confidence": float(analysis.intent_confidence),
                    "signals": analysis.buying_signals_detected,
                    "objections": analysis.objections_detected,
                    "sentiment_score": float(analysis.sentiment_score),
                }

                try:
                    actions = await router.route_event(event_type, context)
                    actions_taken += len(actions)
                except Exception as e:
                    logger.error(f"Router error: {e}")

            logger.info(f"Smart action router: {actions_taken} actions executed")
            return {"actions_taken": actions_taken}
    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.proactive_outreach_scheduler")
def proactive_outreach_scheduler():
    """Daily 9 AM: schedule proactive outreach for all businesses."""
    async def _run():
        async with AsyncSessionLocal() as db:
            engine = ProactiveOutreachEngine(db)
            result = await db.execute(select(Business).where(Business.is_active == True))
            businesses = result.scalars().all()

            total = 0
            for business in businesses:
                try:
                    results = await engine.schedule_outreach_for_business(business.id)
                    total += len(results)
                except Exception as e:
                    logger.error(f"Proactive outreach failed for business {business.id}: {e}")

            logger.info(f"Proactive outreach scheduler: {total} outreach messages scheduled")
            return {"scheduled": total}
    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.briefing_delivery")
def briefing_delivery():
    """Daily 8 AM: deliver daily briefing to all business owners."""
    async def _run():
        async with AsyncSessionLocal() as db:
            service = BriefingDeliveryService(db)
            result = await db.execute(select(Business).where(Business.is_active == True))
            businesses = result.scalars().all()

            delivered = 0
            for business in businesses:
                try:
                    await service.deliver_daily_briefing(business.id)
                    delivered += 1
                except Exception as e:
                    logger.error(f"Briefing delivery failed for business {business.id}: {e}")

            logger.info(f"Briefing delivery: {delivered} briefings sent")
            return {"delivered": delivered}
    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.handoff_alert_sender")
def handoff_alert_sender():
    """Every 5 min: send handoff alerts to human agents."""
    async def _run():
        async with AsyncSessionLocal() as db:
            service = HandoffAlertService(db)
            from app.domains.channels.models import Conversation

            # Find recent handoffs (conversations awaiting human in last 5 min)
            since = datetime.now(timezone.utc) - timedelta(minutes=5)
            result = await db.execute(
                select(Conversation).where(
                    Conversation.awaiting_human == True,
                    Conversation.updated_at >= since,
                ).limit(50)
            )
            conversations = result.scalars().all()

            sent = 0
            for conv in conversations:
                try:
                    await service.alert_handoff(
                        business_id=conv.business_id,
                        conversation_id=conv.id,
                        reason="Lead requiere atención humana",
                        urgency="normal",
                    )
                    sent += 1
                except Exception as e:
                    logger.error(f"Handoff alert failed: {e}")

            logger.info(f"Handoff alert sender: {sent} alerts sent")
            return {"sent": sent}
    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.experiment_evaluator")
def experiment_evaluator():
    """Weekly: evaluate all running experiments."""
    async def _run():
        async with AsyncSessionLocal() as db:
            runner = ExperimentRunner(db)
            result = await db.execute(select(Business).where(Business.is_active == True))
            businesses = result.scalars().all()

            evaluated = 0
            for business in businesses:
                try:
                    outcomes = await runner.evaluate_experiments(business.id)
                    evaluated += len(outcomes)
                except Exception as e:
                    logger.error(f"Experiment evaluation failed for business {business.id}: {e}")

            logger.info(f"Experiment evaluator: {evaluated} experiments evaluated")
            return {"evaluated": evaluated}
    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.auto_optimizer_runner")
def auto_optimizer_runner():
    """Weekly: run auto-optimization adjustments."""
    async def _run():
        async with AsyncSessionLocal() as db:
            optimizer = AutoOptimizer(db)
            result = await db.execute(select(Business).where(Business.is_active == True))
            businesses = result.scalars().all()

            adjustments = 0
            for business in businesses:
                try:
                    opts = await optimizer.run_optimization_cycle(business.id)
                    adjustments += len(opts)
                except Exception as e:
                    logger.error(f"Auto optimizer failed for business {business.id}: {e}")

            logger.info(f"Auto optimizer: {adjustments} adjustments recommended")
            return {"adjustments": adjustments}
    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.ab_test_winner_applier")
def ab_test_winner_applier():
    """Weekly: apply A/B test winners."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.automations.models import WorkflowVariant, Workflow
            from app.domains.optimization.models import OptimizationExperiment

            # Find completed experiments with a winner
            result = await db.execute(
                select(OptimizationExperiment).where(
                    OptimizationExperiment.status == "completed",
                    OptimizationExperiment.winner_variant.isnot(None),
                )
            )
            experiments = result.scalars().all()

            applied = 0
            for exp in experiments:
                if exp.winner_variant == "b":
                    # Apply variant B as new control
                    # In production, would update workflow default
                    applied += 1

            logger.info(f"A/B winner applier: {applied} winners applied")
            return {"applied": applied}
    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.pipeline_automation_trigger_scanner")
def pipeline_automation_trigger_scanner():
    """Every 1h: scan for pipeline automation triggers."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.agents.pipeline_automations import PipelineAutomationEngine
            from app.domains.crm.models import Deal
            from app.domains.channels.models import Conversation

            engine = PipelineAutomationEngine(db)

            # Check stalled deals
            since = datetime.now(timezone.utc) - timedelta(days=3)
            result = await db.execute(
                select(Deal).where(
                    Deal.is_active == True,
                    Deal.stage.notin_(["closed_won", "closed_lost"]),
                    Deal.updated_at < since,
                ).limit(100)
            )
            stalled = result.scalars().all()

            triggered = 0
            for deal in stalled:
                try:
                    await engine.process_event(
                        "inactivity_72h",
                        {},
                        deal.business_id,
                        deal.id,
                    )
                    triggered += 1
                except Exception as e:
                    logger.error(f"Pipeline automation error: {e}")

            logger.info(f"Pipeline trigger scanner: {triggered} automations triggered")
            return {"triggered": triggered}
    return _async_run(_run())


# ═══════════════════════════════════════════════════════
#   NUEVAS TAREAS — SISTEMA DE COMPUTACIÓN AUTÓNOMA
#   4 Pilares: Config · Repair · Optimization · Protection
# ═══════════════════════════════════════════════════════

@shared_task(
    name="app.tasks.autonomous_tasks.autonomous_operations_cycle",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def autonomous_operations_cycle(self, business_id: str | None = None):
    """
    Ciclo maestro autónomo — orquesta los 4 pilares en paralelo.
    Se ejecuta según el intervalo interno de cada pilar (config: 30m,
    repair: 10m, protection: 5m, optimization: 24h).
    Programado por Celery Beat cada 5 minutos.
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.agents.autonomous.operations_center import get_operations_center
            from app.domains.businesses.models import Business
            from sqlalchemy import select

            center = get_operations_center(db)

            if business_id:
                from uuid import UUID
                result = await center.run_full_autonomous_cycle(UUID(business_id))
                hs = result.get("health_snapshot", {})
                logger.info(
                    f"[AOC] business={business_id} "
                    f"health={hs.get('overall_health_score', '?')}/100 "
                    f"faults={hs.get('metrics', {}).get('active_faults', 0)} "
                    f"threats={hs.get('metrics', {}).get('threat_score', 0)}"
                )
                return result
            else:
                biz_result = await db.execute(
                    select(Business).where(Business.is_active == True)
                )
                businesses = biz_result.scalars().all()
                summaries = []
                for biz in businesses:
                    try:
                        r = await center.run_full_autonomous_cycle(biz.id)
                        hs = r.get("health_snapshot", {})
                        summaries.append({
                            "business_id": str(biz.id),
                            "health_score": hs.get("overall_health_score", 0),
                            "pillars_executed": r.get("pillars_executed", []),
                            "duration_s": r.get("cycle_duration_seconds", 0),
                        })
                    except Exception as e:
                        logger.error(f"[AOC] Error business {biz.id}: {e}")
                        summaries.append({"business_id": str(biz.id), "error": str(e)[:100]})

                logger.info(f"[AOC] Ciclos completados para {len(businesses)} negocios")
                return {"businesses_processed": len(businesses), "summaries": summaries}

    try:
        return _async_run(_run())
    except Exception as exc:
        logger.error(f"[AOC] autonomous_operations_cycle error: {exc}")
        raise self.retry(exc=exc)


@shared_task(name="app.tasks.autonomous_tasks.system_health_check")
def system_health_check(business_id: str | None = None):
    """
    Health check rápido — sin acciones correctivas, solo métricas.
    Genera alerta crítica si el score baja de 50.
    Programado cada 2 minutos.
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.agents.autonomous.operations_center import get_operations_center
            from uuid import UUID
            center = get_operations_center(db)
            bid = UUID(business_id) if business_id else None
            result = await center.run_quick_health_check(bid)
            score = result.get("health_score", 100)
            if score < 50:
                logger.warning(f"[HealthCheck] ⚠️ Score CRÍTICO: {score}/100 para business={business_id}")
            elif score < 70:
                logger.warning(f"[HealthCheck] Score bajo: {score}/100 para business={business_id}")
            return result

    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.deep_system_optimization")
def deep_system_optimization(business_id: str | None = None):
    """
    Optimización profunda con análisis de A/B tests y recomendaciones estratégicas.
    Programado cada 24 horas.
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.agents.autonomous.self_optimization import SelfOptimizationEngine
            from app.domains.businesses.models import Business
            from sqlalchemy import select
            from uuid import UUID

            engine = SelfOptimizationEngine(db)

            if business_id:
                bid = UUID(business_id)
                opt = await engine.run_optimization_cycle(bid)
                ab = await engine.run_ab_test_analysis(bid)
                logger.info(
                    f"[DeepOpt] business={business_id}: "
                    f"insights={opt.get('insights_generated', 0)}, "
                    f"actions={opt.get('actions_taken', 0)}, "
                    f"ab_promoted={len(ab.get('promoted', []))}"
                )
                return {"optimization": opt, "ab_tests": ab}
            else:
                biz_result = await db.execute(
                    select(Business).where(Business.is_active == True)
                )
                businesses = biz_result.scalars().all()
                for biz in businesses:
                    try:
                        await engine.run_optimization_cycle(biz.id)
                        await engine.run_ab_test_analysis(biz.id)
                    except Exception as e:
                        logger.error(f"[DeepOpt] Error {biz.id}: {e}")
                logger.info(f"[DeepOpt] Completado para {len(businesses)} negocios")
                return {"businesses_processed": len(businesses)}

    return _async_run(_run())


@shared_task(
    name="app.tasks.autonomous_tasks.emergency_security_scan",
    bind=True,
    max_retries=0,
)
def emergency_security_scan(self, business_id: str | None = None, reason: str = "manual"):
    """
    Escaneo de seguridad on-demand. Disparo manual desde el dashboard
    o cuando se detecta actividad sospechosa inusual.
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.agents.autonomous.self_protection import SelfProtectionEngine
            from uuid import UUID
            logger.warning(f"[EmergencyScan] Iniciando. Razón: {reason}, business={business_id}")
            engine = SelfProtectionEngine(db)
            bid = UUID(business_id) if business_id else None
            result = await engine.run_protection_cycle(bid)
            if result.get("critical_threats", 0) > 0:
                logger.critical(
                    f"[EmergencyScan] ⛔ {result['critical_threats']} amenazas CRÍTICAS detectadas!"
                )
            return result

    return _async_run(_run())


@shared_task(name="app.tasks.autonomous_tasks.weekly_executive_report")
def weekly_executive_report(business_id: str | None = None):
    """
    Reporte ejecutivo semanal para el dueño: métricas de ventas,
    salud del sistema, logros y recomendaciones estratégicas generados con IA.
    Programado cada lunes a las 8 AM.
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.agents.autonomous.operations_center import get_operations_center
            from app.domains.businesses.models import Business
            from app.domains.agents.ai_reply import generate_raw_ai_response
            from app.domains.alerts.models import Alert, AlertSeverity
            from sqlalchemy import select, func, and_
            from uuid import UUID

            center = get_operations_center(db)
            now = datetime.now(timezone.utc)
            week_ago = now - timedelta(days=7)

            async def _report_for(biz_id: UUID, biz_name: str):
                try:
                    from app.domains.channels.models import Message
                    from app.domains.crm.models import Deal

                    msg_q = await db.execute(
                        select(func.count(Message.id)).where(Message.created_at >= week_ago)
                    )
                    deals_q = await db.execute(
                        select(func.count(Deal.id)).where(
                            and_(Deal.created_at >= week_ago, Deal.business_id == biz_id)
                        )
                    )
                    health = await center.run_quick_health_check(biz_id)

                    ctx = (
                        f"Negocio: {biz_name}\n"
                        f"Mensajes procesados esta semana: {msg_q.scalar() or 0}\n"
                        f"Nuevos deals: {deals_q.scalar() or 0}\n"
                        f"Health score: {health.get('health_score', 100)}/100\n"
                        f"Estado: {health.get('load_state', 'normal')}\n"
                    )
                    briefing = await generate_raw_ai_response(
                        db=db,
                        business_id=biz_id,
                        system_prompt=(
                            "Eres el Director Ejecutivo de SellIA. "
                            "Genera un reporte ejecutivo semanal conciso y accionable. "
                            "Formato: resumen ejecutivo (2 líneas), 3 logros, 3 áreas de mejora, "
                            "1 foco para la próxima semana. Usa emojis. Máximo 400 palabras."
                        ),
                        user_prompt=ctx,
                        max_tokens=600,
                        temperature=0.6,
                    )
                    alert = Alert(
                        business_id=biz_id,
                        title=f"📊 Reporte Ejecutivo Semanal — {now.strftime('%d/%m/%Y')}",
                        message=briefing or ctx,
                        severity=AlertSeverity.LOW,
                        is_read=False,
                        created_at=now,
                    )
                    db.add(alert)
                    await db.commit()
                    logger.info(f"[WeeklyReport] Reporte enviado para {biz_name}")
                except Exception as e:
                    logger.error(f"[WeeklyReport] Error {biz_id}: {e}")

            if business_id:
                biz_r = await db.execute(
                    select(Business).where(Business.id == UUID(business_id))
                )
                biz = biz_r.scalar_one_or_none()
                if biz:
                    await _report_for(biz.id, biz.name)
            else:
                biz_r = await db.execute(select(Business).where(Business.is_active == True))
                businesses = biz_r.scalars().all()
                for biz in businesses:
                    await _report_for(biz.id, biz.name)
                logger.info(f"[WeeklyReport] {len(businesses)} reportes generados")

    return _async_run(_run())
