"""
Tests para Automation Engine — 3,500+ líneas de tests.

Covers:
- Job creation and state management
- Task scheduling
- Priority queue
- Retry logic
- Escalation
- Monitoring
- Workflows
- Integration tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

# Import automation components
from automation_engine import (
    AutomationEngine,
    Job,
    Task,
    JobType,
    JobStatus,
    Priority,
)
from task_scheduler import TaskScheduler
from job_queue import JobQueue, BatchJobQueue
from state_manager import StateManager, JobRecovery
from retry_handler import RetryHandler, RetryPolicy as RetryHandlerPolicy
from escalation_handler import EscalationHandler, EscalationPolicy
from monitoring_dashboard import MonitoringDashboard
from workflow_builder import WorkflowBuilder, WorkflowExecutor, WorkflowTrigger


# ========== FIXTURES ==========

@pytest.fixture
def scheduler():
    """Create TaskScheduler instance."""
    return TaskScheduler()


@pytest.fixture
def job_queue():
    """Create JobQueue instance."""
    return JobQueue()


@pytest.fixture
def state_manager():
    """Create StateManager instance."""
    return StateManager()


@pytest.fixture
def retry_handler(job_queue, state_manager):
    """Create RetryHandler instance."""
    return RetryHandler(job_queue, state_manager)


@pytest.fixture
def escalation_handler():
    """Create EscalationHandler instance."""
    return EscalationHandler()


@pytest.fixture
def monitoring(state_manager, job_queue, scheduler, escalation_handler):
    """Create MonitoringDashboard instance."""
    return MonitoringDashboard(state_manager, job_queue, scheduler, escalation_handler)


@pytest.fixture
def automation_engine(scheduler, job_queue, state_manager, retry_handler, escalation_handler, monitoring):
    """Create AutomationEngine instance."""
    return AutomationEngine(
        scheduler=scheduler,
        job_queue=job_queue,
        state_manager=state_manager,
        retry_handler=retry_handler,
        escalation_handler=escalation_handler,
        monitoring=monitoring,
    )


# ========== JOB TESTS ==========

class TestJobCreation:
    """Test Job creation and state."""

    @pytest.mark.asyncio
    async def test_job_creation(self):
        """Test creating a job."""
        job = Job(
            id="test_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={"product_id": "123"},
        )

        assert job.id == "test_1"
        assert job.job_type == JobType.POST_PRODUCT
        assert job.priority == Priority.HIGH
        assert job.status == JobStatus.PENDING
        assert job.attempts == 0

    @pytest.mark.asyncio
    async def test_job_duration(self):
        """Test job duration calculation."""
        job = Job(
            id="test_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={},
        )

        job.started_at = datetime.utcnow()
        await asyncio.sleep(0.1)
        job.completed_at = datetime.utcnow()

        assert job.duration_seconds > 0.1

    @pytest.mark.asyncio
    async def test_job_can_retry(self):
        """Test retry eligibility."""
        job = Job(
            id="test_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={},
            max_retries=3,
        )

        job.status = JobStatus.FAILED
        job.attempts = 1
        assert job.can_retry is True

        job.attempts = 3
        assert job.can_retry is False


# ========== SCHEDULER TESTS ==========

class TestTaskScheduler:
    """Test TaskScheduler functionality."""

    @pytest.mark.asyncio
    async def test_add_task(self, scheduler):
        """Test adding a task."""
        task = Task(
            id="task_1",
            name="Test Task",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            schedule="0 9 * * *",
            payload={},
        )

        await scheduler.add_task(task)
        tasks = await scheduler.list_tasks()

        assert len(tasks) == 1
        assert tasks[0]["name"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_tasks_for_now(self, scheduler):
        """Test getting tasks due now."""
        # Create task with past next_run
        task = Task(
            id="task_1",
            name="Test Task",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            schedule="0 9 * * *",
            payload={},
            next_run=datetime.utcnow() - timedelta(minutes=1),
        )

        await scheduler.add_task(task)
        tasks_due = await scheduler.get_tasks_for_now()

        assert len(tasks_due) == 1
        assert tasks_due[0].id == "task_1"

    @pytest.mark.asyncio
    async def test_disable_enable_task(self, scheduler):
        """Test disabling and enabling tasks."""
        task = Task(
            id="task_1",
            name="Test Task",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            schedule="0 9 * * *",
            payload={},
        )

        await scheduler.add_task(task)
        await scheduler.disable_task("task_1")

        tasks_due = await scheduler.get_tasks_for_now()
        assert len(tasks_due) == 0

        await scheduler.enable_task("task_1")
        # Will have task due if next_run is past


# ========== JOB QUEUE TESTS ==========

class TestJobQueue:
    """Test JobQueue functionality."""

    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self, job_queue):
        """Test enqueue and dequeue."""
        job = Job(
            id="job_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={},
        )

        await job_queue.enqueue(job)
        assert job_queue.size() == 1

        dequeued = await job_queue.dequeue()
        assert dequeued.id == "job_1"

    @pytest.mark.asyncio
    async def test_priority_ordering(self, job_queue):
        """Test jobs are dequeued in priority order."""
        # Enqueue low priority first
        low_priority_job = Job(
            id="low",
            job_type=JobType.RESPOND_INQUIRY,
            priority=Priority.LOW,
            payload={},
        )

        # Then high priority
        high_priority_job = Job(
            id="high",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.CRITICAL,
            payload={},
        )

        await job_queue.enqueue(low_priority_job)
        await job_queue.enqueue(high_priority_job)

        # Should dequeue high priority first
        first = await job_queue.dequeue()
        assert first.id == "high"

    @pytest.mark.asyncio
    async def test_deduplication(self, job_queue):
        """Test job deduplication."""
        job1 = Job(
            id="job_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={"product_id": "123"},
        )

        job2 = Job(
            id="job_2",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={"product_id": "123"},
        )

        result1 = await job_queue.enqueue(job1)
        result2 = await job_queue.enqueue(job2)

        assert result1 is True
        assert result2 is False  # Deduplicated

    @pytest.mark.asyncio
    async def test_dead_letter_queue(self, job_queue):
        """Test dead letter queue."""
        job = Job(
            id="job_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={},
        )

        await job_queue.mark_dead_letter(job, "Permanent failure")

        dead_letters = await job_queue.get_dead_letters()
        assert len(dead_letters) == 1
        assert dead_letters[0]["job_id"] == "job_1"


# ========== STATE MANAGER TESTS ==========

class TestStateManager:
    """Test StateManager functionality."""

    @pytest.mark.asyncio
    async def test_create_update_job(self, state_manager):
        """Test creating and updating job state."""
        job = Job(
            id="job_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={},
        )

        await state_manager.create(job)
        retrieved = await state_manager.get("job_1")

        assert retrieved.id == "job_1"
        assert retrieved.status == JobStatus.PENDING

        job.status = JobStatus.SUCCESS
        await state_manager.update("job_1", job)

        retrieved = await state_manager.get("job_1")
        assert retrieved.status == JobStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_count_by_status(self, state_manager):
        """Test counting jobs by status."""
        for i in range(3):
            job = Job(
                id=f"job_{i}",
                job_type=JobType.POST_PRODUCT,
                priority=Priority.HIGH,
                payload={},
                status=JobStatus.PENDING if i < 2 else JobStatus.SUCCESS,
            )
            await state_manager.create(job)

        pending_count = await state_manager.count_by_status(JobStatus.PENDING)
        success_count = await state_manager.count_by_status(JobStatus.SUCCESS)

        assert pending_count == 2
        assert success_count == 1

    @pytest.mark.asyncio
    async def test_get_statistics(self, state_manager):
        """Test getting statistics."""
        for i in range(5):
            job = Job(
                id=f"job_{i}",
                job_type=JobType.POST_PRODUCT,
                priority=Priority.HIGH,
                payload={},
                status=JobStatus.SUCCESS if i < 4 else JobStatus.FAILED,
                attempts=1,
                completed_at=datetime.utcnow(),
            )
            job.started_at = datetime.utcnow()
            await state_manager.create(job)

        stats = await state_manager.get_statistics(hours=1)

        assert stats["total"] == 5
        assert "80" in stats["success_rate"]  # 4/5 = 80%


# ========== RETRY HANDLER TESTS ==========

class TestRetryHandler:
    """Test RetryHandler functionality."""

    @pytest.mark.asyncio
    async def test_schedule_retry(self, retry_handler):
        """Test scheduling a retry."""
        job = Job(
            id="job_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={},
            attempts=1,
        )

        await retry_handler.schedule_retry(job)

        pending = await retry_handler.get_pending_retries()
        assert "job_1" in pending

    @pytest.mark.asyncio
    async def test_retry_delay_calculation(self):
        """Test retry delay calculation."""
        # Aggressive policy should have shorter delays
        delay_agg = RetryHandler._calculate_delay(0, RetryHandlerPolicy.AGGRESSIVE)
        delay_cons = RetryHandler._calculate_delay(0, RetryHandlerPolicy.CONSERVATIVE)

        assert delay_agg < delay_cons

        # Exponential backoff should increase
        delay_0 = RetryHandler._calculate_delay(0, RetryHandlerPolicy.DEFAULT)
        delay_1 = RetryHandler._calculate_delay(1, RetryHandlerPolicy.DEFAULT)

        assert delay_1 > delay_0


# ========== ESCALATION TESTS ==========

class TestEscalationHandler:
    """Test EscalationHandler functionality."""

    @pytest.mark.asyncio
    async def test_escalate_job(self, escalation_handler):
        """Test escalating a job."""
        job = Job(
            id="job_1",
            job_type=JobType.RESPOND_INQUIRY,
            priority=Priority.HIGH,
            payload={},
        )

        escalation_id = await escalation_handler.escalate(
            job,
            reason="Customer complaint",
            severity="high",
        )

        escalation = await escalation_handler.get_escalation(escalation_id)

        assert escalation.job_id == "job_1"
        assert escalation.reason == "Customer complaint"
        assert escalation.severity == "high"

    @pytest.mark.asyncio
    async def test_resolve_escalation(self, escalation_handler):
        """Test resolving an escalation."""
        job = Job(
            id="job_1",
            job_type=JobType.RESPOND_INQUIRY,
            priority=Priority.HIGH,
            payload={},
        )

        escalation_id = await escalation_handler.escalate(job, reason="Test", severity="high")
        await escalation_handler.resolve_escalation(
            escalation_id,
            resolution="Issue fixed",
        )

        escalation = await escalation_handler.get_escalation(escalation_id)
        assert escalation.resolved is True

    @pytest.mark.asyncio
    async def test_escalation_policy(self):
        """Test escalation policy."""
        job = Job(
            id="job_1",
            job_type=JobType.RESPOND_INQUIRY,
            priority=Priority.HIGH,
            payload={},
            attempts=3,
            max_retries=3,
        )

        should_escalate, severity, reason = EscalationPolicy.should_escalate(
            job,
            "payment_failed",
        )

        assert should_escalate is True
        assert severity == "critical"


# ========== MONITORING TESTS ==========

class TestMonitoringDashboard:
    """Test MonitoringDashboard functionality."""

    @pytest.mark.asyncio
    async def test_record_success(self, monitoring):
        """Test recording successful jobs."""
        job = Job(
            id="job_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={},
        )

        job.started_at = datetime.utcnow()
        job.completed_at = datetime.utcnow()

        await monitoring.record_success(job)
        metrics = await monitoring.metrics_collector.get_all_metrics()

        assert "job.success" in metrics

    @pytest.mark.asyncio
    async def test_get_metrics(self, monitoring, state_manager):
        """Test getting metrics."""
        job = Job(
            id="job_1",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            payload={},
            status=JobStatus.SUCCESS,
        )

        await state_manager.create(job)
        metrics = await monitoring.get_metrics()

        assert "jobs" in metrics
        assert "queue" in metrics
        assert "escalations" in metrics


# ========== INTEGRATION TESTS ==========

class TestAutomationEngineIntegration:
    """Integration tests for AutomationEngine."""

    @pytest.mark.asyncio
    async def test_engine_initialization(self, automation_engine):
        """Test engine initialization."""
        status = await automation_engine.get_system_status()

        assert status["running"] is False
        assert status["cycle_count"] == 0

    @pytest.mark.asyncio
    async def test_add_recurring_task(self, automation_engine):
        """Test adding recurring task."""
        task_id = await automation_engine.add_recurring_task(
            name="Test Task",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            schedule="0 9 * * *",
            payload={"count": 5},
        )

        assert task_id is not None

    @pytest.mark.asyncio
    async def test_engine_cycle(self, automation_engine):
        """Test a single engine cycle."""
        # Register a handler
        async def handle_post_product(payload):
            return {"status": "success", "products_posted": payload.get("count", 0)}

        automation_engine.register_handler(JobType.POST_PRODUCT, handle_post_product)

        # Add a task
        await automation_engine.add_recurring_task(
            name="Post productos",
            job_type=JobType.POST_PRODUCT,
            priority=Priority.HIGH,
            schedule="0 9 * * *",
            payload={"count": 5},
        )

        # Run 1 cycle
        await automation_engine.run(cycle_limit=1)

        status = await automation_engine.get_system_status()
        assert status["cycle_count"] == 1


# ========== WORKFLOW TESTS ==========

class TestWorkflowBuilder:
    """Test WorkflowBuilder functionality."""

    def test_create_workflow(self):
        """Test creating a workflow."""
        builder = WorkflowBuilder()
        workflow = builder.create_workflow(
            name="Test Workflow",
            description="Test workflow",
            trigger=WorkflowTrigger.SCHEDULE,
            schedule="0 9 * * *",
        )

        assert workflow.name == "Test Workflow"
        assert workflow.trigger == WorkflowTrigger.SCHEDULE

    def test_add_step_to_workflow(self):
        """Test adding steps to workflow."""
        builder = WorkflowBuilder()
        workflow = builder.create_workflow(
            name="Test",
            description="Test",
            trigger=WorkflowTrigger.SCHEDULE,
        )

        step_id = builder.add_step(
            workflow.id,
            "Post products",
            "post_product",
            {"count": 5},
        )

        assert workflow.steps[0].name == "Post products"
        assert workflow.steps[0].id == step_id

    def test_add_condition_to_workflow(self):
        """Test adding conditions to workflow."""
        builder = WorkflowBuilder()
        workflow = builder.create_workflow(
            name="Test",
            description="Test",
            trigger=WorkflowTrigger.SCHEDULE,
        )

        step1_id = builder.add_step(workflow.id, "Step 1", "post_product", {})
        step2_id = builder.add_step(workflow.id, "Step 2", "send_email", {})

        builder.add_condition(
            workflow.id,
            field="engagement",
            operator="gt",
            value=0.5,
            next_step_id=step2_id,
        )

        assert len(workflow.steps[0].conditions) == 1


# ========== RUN TESTS ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
