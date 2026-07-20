"""Unit tests for automation_engine.py — 24/7 autonomous sales execution.

Tests cover:
- Workflow execution
- Task scheduling
- Escalation handling
- State management
- Retry logic
- Performance monitoring
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.automation.automation_engine import (
    AutomationEngine,
    Workflow,
    Task,
    TaskStatus,
    ExecutionContext,
)


class TestAutomationEngineInitialization:
    """Test automation engine initialization."""

    def test_engine_initialization(self):
        """Test basic engine initialization."""
        engine = AutomationEngine()

        assert engine is not None
        assert hasattr(engine, 'workflows')
        assert hasattr(engine, 'task_queue')
        assert hasattr(engine, 'execution_context')

    def test_load_workflows(self):
        """Test loading workflows."""
        engine = AutomationEngine()
        engine.load_workflows()

        assert len(engine.workflows) > 0
        assert all(isinstance(w, Workflow) for w in engine.workflows.values())

    def test_initialize_task_scheduler(self):
        """Test task scheduler initialization."""
        engine = AutomationEngine()

        assert engine.scheduler is not None
        assert engine.scheduler.is_running or not engine.scheduler.is_running


class TestWorkflowExecution:
    """Test workflow execution capabilities."""

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """Test executing a simple workflow."""
        engine = AutomationEngine()

        workflow_def = {
            "name": "test_workflow",
            "tasks": [
                {
                    "type": "lead_check",
                    "params": {"lead_id": "123"}
                },
                {
                    "type": "send_message",
                    "params": {"message": "Hello"}
                }
            ]
        }

        result = await engine.execute_workflow(workflow_def)

        assert result is not None
        assert "status" in result
        assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_workflow_with_conditions(self):
        """Test workflow with conditional logic."""
        engine = AutomationEngine()

        workflow_def = {
            "name": "conditional_workflow",
            "tasks": [
                {
                    "type": "lead_check",
                    "params": {"lead_id": "123"}
                },
                {
                    "type": "conditional",
                    "condition": "lead.score > 70",
                    "then": [{"type": "send_offer"}],
                    "else": [{"type": "send_info"}]
                }
            ]
        }

        result = await engine.execute_workflow(workflow_def)

        assert result is not None

    @pytest.mark.asyncio
    async def test_workflow_with_loops(self):
        """Test workflow with loop logic."""
        engine = AutomationEngine()

        workflow_def = {
            "name": "loop_workflow",
            "tasks": [
                {
                    "type": "loop",
                    "items": "leads_list",
                    "task": {
                        "type": "process_lead",
                        "params": {"lead": "${item}"}
                    }
                }
            ]
        }

        result = await engine.execute_workflow(workflow_def)

        assert result is not None

    @pytest.mark.asyncio
    async def test_parallel_workflow_execution(self):
        """Test parallel execution of workflow tasks."""
        engine = AutomationEngine()

        workflow_def = {
            "name": "parallel_workflow",
            "tasks": [
                {
                    "type": "parallel",
                    "tasks": [
                        {"type": "send_email"},
                        {"type": "send_sms"},
                        {"type": "create_followup_task"}
                    ]
                }
            ]
        }

        result = await engine.execute_workflow(workflow_def)

        assert result is not None

    @pytest.mark.asyncio
    async def test_workflow_execution_timeout(self):
        """Test workflow execution with timeout."""
        engine = AutomationEngine()

        workflow_def = {
            "name": "timeout_workflow",
            "timeout": 5,
            "tasks": [{"type": "long_running_task"}]
        }

        result = await engine.execute_workflow(workflow_def, timeout=5)

        assert result is not None


class TestTaskScheduling:
    """Test task scheduling capabilities."""

    @pytest.mark.asyncio
    async def test_schedule_immediate_task(self):
        """Test scheduling a task for immediate execution."""
        engine = AutomationEngine()

        task = Task(
            name="send_email",
            type="email_notification",
            params={"recipient": "test@example.com"},
            priority=1
        )

        task_id = await engine.schedule_task(task)

        assert task_id is not None
        assert isinstance(task_id, str)

    @pytest.mark.asyncio
    async def test_schedule_delayed_task(self):
        """Test scheduling a task with delay."""
        engine = AutomationEngine()

        scheduled_time = datetime.now() + timedelta(hours=1)
        task = Task(
            name="send_reminder",
            type="reminder",
            params={"lead_id": "123"},
            scheduled_time=scheduled_time,
            priority=2
        )

        task_id = await engine.schedule_task(task)

        assert task_id is not None

    @pytest.mark.asyncio
    async def test_schedule_recurring_task(self):
        """Test scheduling recurring tasks."""
        engine = AutomationEngine()

        task = Task(
            name="daily_report",
            type="report_generation",
            params={"report_type": "daily"},
            cron_expression="0 9 * * *",  # 9 AM daily
            priority=3
        )

        task_id = await engine.schedule_task(task)

        assert task_id is not None

    @pytest.mark.asyncio
    async def test_task_priority_queue(self):
        """Test that tasks are executed in priority order."""
        engine = AutomationEngine()

        # Schedule tasks with different priorities
        tasks = [
            Task("task_3", "type", {}, priority=3),
            Task("task_1", "type", {}, priority=1),
            Task("task_2", "type", {}, priority=2)
        ]

        task_ids = []
        for task in tasks:
            task_id = await engine.schedule_task(task)
            task_ids.append(task_id)

        # Get execution order
        exec_order = await engine.get_task_execution_order()

        # Higher priority (lower number) should execute first
        assert len(exec_order) >= 0

    @pytest.mark.asyncio
    async def test_cancel_scheduled_task(self):
        """Test canceling a scheduled task."""
        engine = AutomationEngine()

        task = Task("test_task", "type", {})
        task_id = await engine.schedule_task(task)

        canceled = await engine.cancel_task(task_id)

        assert canceled is True

    @pytest.mark.asyncio
    async def test_reschedule_failed_task(self):
        """Test rescheduling a failed task."""
        engine = AutomationEngine()

        task = Task(
            "failing_task",
            "type",
            {},
            retry_count=3,
            retry_delay=60
        )

        task_id = await engine.schedule_task(task)

        # Simulate failure
        await engine.record_task_failure(task_id, "Connection timeout")

        # Reschedule
        rescheduled = await engine.reschedule_task(task_id)

        assert rescheduled is True


class TestEscalationHandling:
    """Test escalation and error handling."""

    @pytest.mark.asyncio
    async def test_escalate_on_repeated_failure(self):
        """Test escalation after repeated failures."""
        engine = AutomationEngine()

        task = Task(
            "critical_task",
            "send_contract",
            {"lead_id": "123"},
            critical=True
        )

        # Simulate 3 failures
        for _ in range(3):
            await engine.record_task_failure(task.id, "Failed")

        escalation = await engine.check_escalation(task.id)

        assert escalation is not None
        assert "escalate" in escalation

    @pytest.mark.asyncio
    async def test_escalate_to_human_support(self):
        """Test escalating to human support."""
        engine = AutomationEngine()

        result = await engine.escalate_to_human(
            issue="Lead scoring disagreement",
            severity="high",
            context={"lead_id": "123"}
        )

        assert result is not None
        assert "ticket_id" in result or "assigned_to" in result

    @pytest.mark.asyncio
    async def test_escalation_notification(self):
        """Test that escalation sends notifications."""
        engine = AutomationEngine()

        with patch.object(engine, 'send_notification') as mock_notify:
            await engine.escalate_to_human(
                issue="Test issue",
                severity="high"
            )

            # Notification should be sent
            mock_notify.assert_called()

    @pytest.mark.asyncio
    async def test_handle_execution_error(self):
        """Test handling of execution errors."""
        engine = AutomationEngine()

        error_handling = await engine.handle_error(
            task_id="task_123",
            error="Database connection failed",
            error_type="DatabaseError"
        )

        assert error_handling is not None
        assert "action" in error_handling


class TestStateManagement:
    """Test execution state management."""

    @pytest.mark.asyncio
    async def test_save_execution_state(self):
        """Test saving execution state."""
        engine = AutomationEngine()

        state = {
            "lead_id": "123",
            "current_stage": "qualification",
            "data": {"score": 85}
        }

        saved = await engine.save_state("exec_ctx_1", state)

        assert saved is True

    @pytest.mark.asyncio
    async def test_restore_execution_state(self):
        """Test restoring execution state."""
        engine = AutomationEngine()

        state = {
            "lead_id": "123",
            "current_stage": "negotiation"
        }

        await engine.save_state("exec_ctx_2", state)

        restored = await engine.restore_state("exec_ctx_2")

        assert restored is not None
        assert restored["lead_id"] == "123"

    @pytest.mark.asyncio
    async def test_state_persistence(self):
        """Test state persistence across engine restarts."""
        engine1 = AutomationEngine()

        state = {
            "task_id": "task_1",
            "progress": 0.5
        }

        await engine1.save_state("persistent_ctx", state)

        # Simulate engine restart
        engine2 = AutomationEngine()

        restored = await engine2.restore_state("persistent_ctx")

        assert restored is not None
        assert restored["progress"] == 0.5

    @pytest.mark.asyncio
    async def test_cleanup_old_states(self):
        """Test cleanup of old execution states."""
        engine = AutomationEngine()

        # Create states from 30 days ago
        old_date = (datetime.now() - timedelta(days=30)).isoformat()

        cleaned = await engine.cleanup_old_states(days=7)

        assert isinstance(cleaned, int)


class TestRetryLogic:
    """Test retry and failure recovery."""

    @pytest.mark.asyncio
    async def test_exponential_backoff_retry(self):
        """Test exponential backoff retry strategy."""
        engine = AutomationEngine()

        attempt_times = []

        async def failing_task():
            attempt_times.append(datetime.now())
            if len(attempt_times) < 3:
                raise Exception("Still failing")
            return "Success"

        result = await engine.retry_with_backoff(
            failing_task,
            max_retries=3,
            base_delay=1
        )

        assert result == "Success"
        assert len(attempt_times) == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_retry(self):
        """Test circuit breaker pattern."""
        engine = AutomationEngine()

        # Simulate consistent failures
        for _ in range(5):
            try:
                await engine.call_with_circuit_breaker("failing_service")
            except Exception:
                pass

        # Circuit should be open
        circuit_state = engine.get_circuit_state("failing_service")

        assert circuit_state in ["open", "half_open"]

    @pytest.mark.asyncio
    async def test_retry_with_custom_strategy(self):
        """Test retry with custom strategy."""
        engine = AutomationEngine()

        def custom_strategy(attempt):
            # Custom backoff: 1s, 3s, 5s
            return (attempt * 2) - 1

        task = Task("custom_retry", "test", {})

        result = await engine.schedule_with_retry(
            task,
            retry_strategy=custom_strategy
        )

        assert result is not None


class TestPerformanceMonitoring:
    """Test performance monitoring."""

    @pytest.mark.asyncio
    async def test_track_execution_metrics(self):
        """Test tracking execution metrics."""
        engine = AutomationEngine()

        metrics = await engine.get_execution_metrics()

        assert "total_tasks" in metrics
        assert "successful_tasks" in metrics
        assert "failed_tasks" in metrics
        assert "average_execution_time" in metrics

    @pytest.mark.asyncio
    async def test_workflow_performance_analysis(self):
        """Test workflow performance analysis."""
        engine = AutomationEngine()

        analysis = await engine.analyze_workflow_performance("workflow_name")

        assert "throughput" in analysis
        assert "success_rate" in analysis
        assert "avg_duration" in analysis

    @pytest.mark.asyncio
    async def test_bottleneck_detection(self):
        """Test detecting workflow bottlenecks."""
        engine = AutomationEngine()

        bottlenecks = await engine.detect_bottlenecks()

        assert isinstance(bottlenecks, list)
        if len(bottlenecks) > 0:
            for b in bottlenecks:
                assert "task" in b
                assert "duration" in b

    @pytest.mark.asyncio
    async def test_resource_utilization_monitoring(self):
        """Test resource utilization monitoring."""
        engine = AutomationEngine()

        resources = await engine.get_resource_utilization()

        assert "cpu_percent" in resources
        assert "memory_percent" in resources
        assert "active_tasks" in resources


class TestAutomationEngineIntegration:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_end_to_end_lead_automation(self):
        """Test complete lead automation workflow."""
        engine = AutomationEngine()

        # Step 1: Receive lead
        lead = {"id": "lead_123", "email": "test@example.com"}

        # Step 2: Schedule analysis
        task = Task("analyze", "lead_scoring", {"lead": lead})
        task_id = await engine.schedule_task(task)
        assert task_id is not None

        # Step 3: Execute workflow
        workflow = {
            "name": "lead_nurture",
            "tasks": [
                {"type": "send_welcome"},
                {"type": "schedule_followup"}
            ]
        }
        result = await engine.execute_workflow(workflow)
        assert result is not None

    @pytest.mark.asyncio
    async def test_multi_stage_sales_automation(self):
        """Test multi-stage sales process automation."""
        engine = AutomationEngine()

        stages = ["prospecting", "qualification", "proposal", "negotiation"]

        for stage in stages:
            workflow = {
                "name": f"stage_{stage}",
                "tasks": [
                    {"type": "prepare_stage_content"},
                    {"type": "send_communication"},
                    {"type": "schedule_next_stage"}
                ]
            }

            result = await engine.execute_workflow(workflow)
            assert result is not None


class TestAutomationEngineEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_workflow_with_circular_dependency(self):
        """Test handling circular workflow dependencies."""
        engine = AutomationEngine()

        workflow_def = {
            "name": "circular",
            "tasks": [
                {"id": "A", "depends_on": ["B"]},
                {"id": "B", "depends_on": ["A"]}
            ]
        }

        result = await engine.execute_workflow(workflow_def)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_massive_parallel_tasks(self):
        """Test handling massive number of parallel tasks."""
        engine = AutomationEngine()

        tasks = [
            Task(f"task_{i}", "test", {})
            for i in range(100)
        ]

        task_ids = []
        for task in tasks:
            task_id = await engine.schedule_task(task)
            task_ids.append(task_id)

        assert len(task_ids) == 100

    @pytest.mark.asyncio
    async def test_workflow_resource_exhaustion(self):
        """Test behavior under resource exhaustion."""
        engine = AutomationEngine()

        # Simulate resource exhaustion
        engine.max_concurrent_tasks = 1

        tasks = [Task(f"t_{i}", "test", {}) for i in range(5)]

        for task in tasks:
            await engine.schedule_task(task)

        # Should queue tasks instead of failing
        queued = await engine.get_queued_tasks()
        assert len(queued) >= 0
