"""
Integration Example — Cómo integrar Automation Engine en FastAPI app.

Este archivo muestra cómo:
1. Setup en startup
2. Register handlers
3. Add API endpoints
4. Monitor en tiempo real
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging
from typing import Dict, Any, Optional

from app.core.automation import (
    setup_automation_engine,
    JobType,
    Priority,
    DashboardAPI,
    WorkflowBuilder,
    WorkflowTrigger,
)

logger = logging.getLogger(__name__)

# Global engine instance
automation_engine = None


# ========== HANDLERS ==========

async def handle_post_product(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler para post_product jobs.

    Usa Computer Use para postear productos en plataformas.
    """
    logger.info(f"Posting {payload.get('count', 5)} products")

    try:
        count = payload.get("count", 5)
        platform = payload.get("platform", "mercadolibre")

        # TODO: Implementar Computer Use para postear
        # browser_agent = get_browser_agent()
        # for i in range(count):
        #     result = await browser_agent.post_product(...)

        return {
            "status": "success",
            "products_posted": count,
            "platform": platform,
        }
    except Exception as e:
        logger.error(f"Failed to post products: {str(e)}")
        raise


async def handle_respond_inquiry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler para respond_inquiry jobs.

    Usa AI para responder preguntas de clientes en tiempo real.
    """
    logger.info("Responding to customer inquiries")

    try:
        # TODO: Query inquiries from DB
        # inquiries = await db.query("SELECT * FROM inquiries WHERE responded = false LIMIT 10")

        # TODO: Use AI to generate responses
        # for inquiry in inquiries:
        #     response = await ai_service.generate_response(inquiry.text)
        #     await send_response(inquiry.id, response)

        return {
            "status": "success",
            "inquiries_responded": 5,  # placeholder
        }
    except Exception as e:
        logger.error(f"Failed to respond to inquiries: {str(e)}")
        raise


async def handle_send_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler para send_email jobs.

    Envía emails de campañas de nurturing.
    """
    logger.info(f"Sending emails: {payload.get('template')}")

    try:
        template = payload.get("template", "welcome")
        batch = payload.get("batch", True)

        # TODO: Query pending emails
        # emails = await db.query("SELECT * FROM email_queue WHERE template = %s AND sent = false", [template])

        # TODO: Send emails
        # for email in emails:
        #     await email_service.send(email)

        return {
            "status": "success",
            "emails_sent": 10,  # placeholder
            "template": template,
        }
    except Exception as e:
        logger.error(f"Failed to send emails: {str(e)}")
        raise


async def handle_sync_inventory(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler para sync_inventory jobs.

    Sincroniza stock entre DB y plataformas.
    """
    logger.info("Syncing inventory")

    try:
        # TODO: Get master inventory from DB
        # master_inventory = await db.query("SELECT sku, quantity FROM inventory")

        # TODO: Sync to each platform
        # for platform in ["mercadolibre", "shopify", "amazon"]:
        #     await sync_platform_inventory(platform, master_inventory)

        return {
            "status": "success",
            "skus_synced": 50,  # placeholder
        }
    except Exception as e:
        logger.error(f"Failed to sync inventory: {str(e)}")
        raise


async def handle_extract_analytics(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler para extract_analytics jobs.

    Extrae métricas de dashboards de plataformas.
    """
    logger.info("Extracting analytics")

    try:
        platforms = ["mercadolibre", "amazon", "shopify", "tiktok_shop"]

        # TODO: Use Computer Use to extract metrics
        # browser_agent = get_browser_agent()
        # for platform in platforms:
        #     metrics = await browser_agent.extract_dashboard_metrics(platform)
        #     await db.save_metrics(platform, metrics)

        return {
            "status": "success",
            "platforms_extracted": len(platforms),
        }
    except Exception as e:
        logger.error(f"Failed to extract analytics: {str(e)}")
        raise


# ========== STARTUP / SHUTDOWN ==========

async def setup_automation():
    """Setup automation engine on app startup."""
    global automation_engine

    logger.info("Setting up Automation Engine...")

    # Create engine
    automation_engine = await setup_automation_engine()

    # Register handlers
    automation_engine.register_handler(JobType.POST_PRODUCT, handle_post_product)
    automation_engine.register_handler(JobType.RESPOND_INQUIRY, handle_respond_inquiry)
    automation_engine.register_handler(JobType.SEND_EMAIL, handle_send_email)
    automation_engine.register_handler(JobType.SYNC_INVENTORY, handle_sync_inventory)
    automation_engine.register_handler(JobType.EXTRACT_ANALYTICS, handle_extract_analytics)

    logger.info("✓ Automation Engine ready")

    # Start engine in background
    asyncio.create_task(automation_engine.run())


async def shutdown_automation():
    """Graceful shutdown on app termination."""
    global automation_engine

    if automation_engine:
        logger.info("Shutting down Automation Engine...")
        await automation_engine.graceful_shutdown()
        logger.info("✓ Automation Engine shutdown complete")


# ========== API ROUTES ==========

def setup_automation_routes(app: FastAPI):
    """Setup automation API routes."""

    @app.on_event("startup")
    async def startup():
        await setup_automation()

    @app.on_event("shutdown")
    async def shutdown():
        await shutdown_automation()

    # Status endpoint
    @app.get("/api/automation/status")
    async def get_automation_status():
        """Get current automation engine status."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        status = await automation_engine.get_system_status()
        return JSONResponse(status)

    # Dashboard endpoint
    @app.get("/api/automation/dashboard")
    async def get_dashboard():
        """Get full dashboard data."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        dashboard = DashboardAPI(automation_engine.monitoring)
        data = await dashboard.get_dashboard_data()
        return JSONResponse(data)

    # Jobs endpoint
    @app.get("/api/automation/jobs")
    async def get_jobs(status: Optional[str] = None, limit: int = 50):
        """Get jobs (optionally filtered by status)."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        if status:
            # Filter by status
            jobs = await automation_engine.state_manager.get_by_status(status, limit=limit)
            jobs_data = [
                {
                    "id": j.id,
                    "type": j.job_type.value,
                    "status": j.status.value,
                    "created_at": j.created_at.isoformat(),
                    "duration": f"{j.duration_seconds:.2f}s" if j.duration_seconds else "—",
                }
                for j in jobs
            ]
        else:
            # Get recent jobs
            jobs = await automation_engine.state_manager.get_recent(hours=1, limit=limit)
            jobs_data = [
                {
                    "id": j.id,
                    "type": j.job_type.value,
                    "status": j.status.value,
                    "created_at": j.created_at.isoformat(),
                    "duration": f"{j.duration_seconds:.2f}s" if j.duration_seconds else "—",
                }
                for j in jobs
            ]

        return JSONResponse({"jobs": jobs_data})

    # Job details endpoint
    @app.get("/api/automation/jobs/{job_id}")
    async def get_job_details(job_id: str):
        """Get detailed job history."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        history = await automation_engine.state_manager.get_history(job_id)
        if not history:
            raise HTTPException(status_code=404, detail="Job not found")

        return JSONResponse(history)

    # Escalations endpoint
    @app.get("/api/automation/escalations")
    async def get_escalations(limit: int = 50):
        """Get pending escalations."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        escalations = await automation_engine.escalation_handler.get_pending_escalations(limit=limit)
        escalations_data = [
            {
                "id": e.id,
                "job_id": e.job_id,
                "severity": e.severity,
                "reason": e.reason,
                "created_at": e.created_at.isoformat(),
                "resolved": e.resolved,
            }
            for e in escalations
        ]

        return JSONResponse({"escalations": escalations_data})

    # Resolve escalation endpoint
    @app.post("/api/automation/escalations/{escalation_id}/resolve")
    async def resolve_escalation(escalation_id: str, resolution: str):
        """Resolve an escalation."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        success = await automation_engine.escalation_handler.resolve_escalation(
            escalation_id,
            resolution=resolution,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Escalation not found")

        return JSONResponse({"status": "resolved"})

    # Add task endpoint
    @app.post("/api/automation/tasks")
    async def add_task(
        name: str,
        job_type: str,
        priority: str,
        schedule: str,
        payload: Dict[str, Any],
    ):
        """Add a new recurring task."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        try:
            task_id = await automation_engine.add_recurring_task(
                name=name,
                job_type=JobType[job_type.upper()],
                priority=Priority[priority.upper()],
                schedule=schedule,
                payload=payload,
            )
            return JSONResponse({"task_id": task_id, "status": "created"})
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")

    # List tasks endpoint
    @app.get("/api/automation/tasks")
    async def list_tasks():
        """List all tasks."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        tasks = await automation_engine.scheduler.list_tasks()
        return JSONResponse({"tasks": tasks})

    # Metrics endpoint (Prometheus format)
    @app.get("/metrics/automation")
    async def get_prometheus_metrics():
        """Export Prometheus metrics."""
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        metrics = await automation_engine.monitoring.export_prometheus_metrics()
        return metrics

    logger.info("✓ Automation API routes registered")


# ========== INITIALIZATION IN FASTAPI APP ==========

def create_app() -> FastAPI:
    """Create FastAPI app with automation engine."""
    app = FastAPI(title="Automation Engine API")

    # Setup automation
    setup_automation_routes(app)

    return app


# ========== USAGE ==========

if __name__ == "__main__":
    import uvicorn

    app = create_app()

    # Run
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

    # Endpoints:
    # GET  /api/automation/status
    # GET  /api/automation/dashboard
    # GET  /api/automation/jobs
    # GET  /api/automation/jobs/{job_id}
    # GET  /api/automation/escalations
    # POST /api/automation/escalations/{id}/resolve
    # POST /api/automation/tasks
    # GET  /api/automation/tasks
    # GET  /metrics/automation
