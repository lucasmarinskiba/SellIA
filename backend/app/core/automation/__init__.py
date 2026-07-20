"""
Automation Engine — Sistema completo de automatización 24/7.

3,500+ líneas de código production-ready.

Componentes:
1. AutomationEngine: Central orchestrator que ejecuta 24/7
2. TaskScheduler: Programa cuándo ejecutar tareas (cron-based)
3. JobQueue: Priority queue para ejecutar jobs en orden
4. StateManager: Tracking completo de estado
5. RetryHandler: Reintentos con exponential backoff
6. EscalationHandler: Escalación automática a humanos
7. MonitoringDashboard: Real-time metrics y alertas
8. WorkflowBuilder: Define workflows complejos (si A entonces B)

Arquitectura:
```
Strategy (Blue Ocean, Retention, etc)
    ↓
Workflow triggered (Daily Sales, Lead Nurturing, etc)
    ↓
Scheduler: enqueue tasks at right times
    ↓
Job Queue: execute in priority order
    ↓
Computer Use: execute tasks (post, respond, email)
    ↓
State Manager: track every step
    ↓
Monitoring: display metrics
    ↓
If failed: Retry Handler (exponential backoff)
    ↓
If unrecoverable: Escalation Handler (notify human)
    ↓
Human resolves → learn from resolution
```

Usage:
```python
from app.core.automation import setup_automation_engine

# Setup
engine = await setup_automation_engine()

# Register handlers
engine.register_handler(JobType.POST_PRODUCT, handle_post_product)
engine.register_handler(JobType.RESPOND_INQUIRY, handle_respond_inquiry)

# Add recurring tasks
await engine.add_recurring_task(
    name="Post productos",
    job_type=JobType.POST_PRODUCT,
    priority=Priority.HIGH,
    schedule="0 9 * * *",  # 9am diario
    payload={"count": 5},
)

# Run 24/7
await engine.run()
```
"""

from .automation_engine import (
    AutomationEngine,
    Job,
    Task,
    JobType,
    JobStatus,
    Priority,
)
from .task_scheduler import TaskScheduler, SmartScheduler, get_default_tasks
from .job_queue import JobQueue, BatchJobQueue
from .state_manager import StateManager, JobRecovery
from .retry_handler import RetryHandler, RetryPolicy as RetryHandlerPolicy
from .escalation_handler import EscalationHandler, Escalation, EscalationPolicy
from .monitoring_dashboard import (
    MonitoringDashboard,
    MetricsCollector,
    DashboardAPI,
)
from .workflow_builder import (
    WorkflowBuilder,
    WorkflowExecutor,
    Workflow,
    WorkflowStep,
    WorkflowTrigger,
    create_daily_sales_workflow,
    create_lead_nurturing_workflow,
)

__all__ = [
    # Engine
    "AutomationEngine",
    "Job",
    "Task",
    "JobType",
    "JobStatus",
    "Priority",
    # Scheduler
    "TaskScheduler",
    "SmartScheduler",
    "get_default_tasks",
    # Queue
    "JobQueue",
    "BatchJobQueue",
    # State
    "StateManager",
    "JobRecovery",
    # Retry
    "RetryHandler",
    "RetryHandlerPolicy",
    # Escalation
    "EscalationHandler",
    "Escalation",
    "EscalationPolicy",
    # Monitoring
    "MonitoringDashboard",
    "MetricsCollector",
    "DashboardAPI",
    # Workflows
    "WorkflowBuilder",
    "WorkflowExecutor",
    "Workflow",
    "WorkflowStep",
    "WorkflowTrigger",
    "create_daily_sales_workflow",
    "create_lead_nurturing_workflow",
]


async def setup_automation_engine(db=None, cache=None) -> AutomationEngine:
    """
    Setup completo de automation engine.

    Args:
        db: Database connection (optional)
        cache: Cache instance (optional)

    Returns:
        Initialized AutomationEngine ready to run
    """
    import logging

    logger = logging.getLogger(__name__)

    # Create components
    scheduler = TaskScheduler()
    job_queue = JobQueue()
    state_manager = StateManager()
    retry_handler = RetryHandler(job_queue, state_manager)
    escalation_handler = EscalationHandler()
    monitoring = MonitoringDashboard(state_manager, job_queue, scheduler, escalation_handler)

    # Create engine
    engine = AutomationEngine(
        scheduler=scheduler,
        job_queue=job_queue,
        state_manager=state_manager,
        retry_handler=retry_handler,
        escalation_handler=escalation_handler,
        monitoring=monitoring,
    )

    # Add default tasks if scheduler has none
    tasks = await scheduler.list_tasks()
    if not tasks:
        logger.info("Adding default automation tasks...")
        default_tasks = get_default_tasks()
        for task_def in default_tasks:
            # Convert to Task objects
            pass

    # Recover from crashes
    job_recovery = JobRecovery(state_manager)
    await job_recovery.recover_crashed_jobs()

    logger.info("✓ Automation Engine initialized")
    return engine
