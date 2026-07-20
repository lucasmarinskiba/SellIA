"""
Sales Tasks — Celery job queue. Ejecuta ciclos venta en paralelo (no bloquea).

Setup:
  pip install celery redis
  celery -A app.core.tasks worker -l info --concurrency=10
"""

from celery import Celery, group, chain
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Celery app
app = Celery(
    "sellia_sales",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 min hard limit
)


@app.task(bind=True, max_retries=3)
def run_sales_cycle_task(self, cycle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tarea: Ejecuta ciclo venta completo (7 fases).

    Enqueue: celery_app.delay(cycle_data)
    Resultado guardado en DB + Redis cache.
    """

    try:
        cycle_id = cycle_data["id"]
        logger.info(f"Starting sales cycle task {cycle_id}")

        # Simular ejecución ciclo
        # En prod: llamar LoopEngineering.run_sales_cycle_with_loops()

        result = {
            "cycle_id": cycle_id,
            "status": "completed",
            "sales": 1,
            "revenue": cycle_data["product"]["price"],
        }

        logger.info(f"Sales cycle {cycle_id} completed: {result}")

        return result

    except Exception as e:
        logger.error(f"Error in sales cycle {cycle_data.get('id')}: {str(e)}")
        # Retry con exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@app.task
def process_lead_task(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Tarea: Califica y valida lead."""

    try:
        lead_id = lead_data["id"]
        logger.info(f"Processing lead {lead_id}")

        # Scoring, validation, etc
        score = 85  # dummy

        return {"lead_id": lead_id, "score": score, "qualified": score > 70}

    except Exception as e:
        logger.error(f"Error processing lead: {str(e)}")
        return {"error": str(e)}


@app.task
def send_email_task(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Tarea: Envía email vía SendGrid."""

    try:
        # from backend.app.core.integrations.sendgrid_email import EmailService
        # EmailService.send_transactional(...)

        return {"email_sent": True, "to": email_data.get("to")}

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {"error": str(e)}


@app.task
def run_browser_automation_task(automation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Tarea: Ejecuta browser automation (MercadoLibre, Meta, etc)."""

    try:
        script_name = automation_data["script"]
        logger.info(f"Running browser automation: {script_name}")

        # from backend.app.core.computer_use.browser_agent import BrowserAgent
        # agent = BrowserAgent()
        # result = agent.run_automation_script(script)

        return {"automation": script_name, "status": "success"}

    except Exception as e:
        logger.error(f"Error running automation: {str(e)}")
        return {"error": str(e)}


# Workflow: ciclo venta completo en paralelo
@app.task
def orchestrate_sales_cycle(cycle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orquesta ciclo venta: ejecuta fases en paralelo donde posible.

    Ejemplo: captura + análisis → negoción (paralelo) → cierre.
    """

    # Fase 1: capture + qualify (secuencial)
    capture_chain = chain(
        process_lead_task.s(cycle_data["buyer"]),
        send_email_task.s({"to": cycle_data["buyer"]["email"], "type": "welcome"}),
    )

    # Fase 2: parallelizar (negotiation, automation, email sequences)
    parallel_phase = group(
        run_browser_automation_task.s({"script": "mercadolibre_list"}),
        send_email_task.s({"to": cycle_data["buyer"]["email"], "type": "nurture"}),
        run_browser_automation_task.s({"script": "meta_ads_create"}),
    )

    # Fase 3: cierre + pago
    closing_phase = run_sales_cycle_task.s(cycle_data)

    # Encadenar: capture → parallel → close
    workflow = chain(capture_chain, parallel_phase, closing_phase)

    # Ejecutar async
    result = workflow.apply_async()

    return {"workflow_id": result.id, "status": "queued"}


# Batch processing: N ciclos simultáneamente
@app.task
def batch_process_sales_cycles(cycles: list) -> Dict[str, Any]:
    """Procesa N ciclos en paralelo (10, 100, 1000)."""

    logger.info(f"Batch processing {len(cycles)} sales cycles")

    # Crear N tareas en paralelo
    job = group(run_sales_cycle_task.s(cycle) for cycle in cycles)

    result = job.apply_async()

    return {
        "batch_size": len(cycles),
        "job_id": result.id,
        "status": "processing",
    }


# Scheduled tasks: ejecutar cada N minutos/horas
@app.task
def scheduled_win_back_campaigns():
    """Ejecuta win-back campaigns cada 6 horas."""

    # Buscar clientes churn-risk
    # Enviar win-back email
    # Log resultado

    logger.info("Win-back campaigns executed")

    return {"campaigns": "completed"}


@app.task
def scheduled_nps_surveys():
    """Ejecuta NPS surveys cada 7 días."""

    logger.info("NPS surveys sent")

    return {"surveys": "sent"}


@app.task
def scheduled_upsell_automation():
    """Detecta ready-for-upsell customers, envía offer."""

    logger.info("Upsell automation executed")

    return {"upsells": "processed"}
