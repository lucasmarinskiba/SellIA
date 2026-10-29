"""The placeholder engine (domains/workflows) must not claim success for actions it does not perform."""

import uuid

from app.domains.workflows.workflow_engine import WorkflowEngine
from app.domains.workflows.workflow_models import ActionType


def _run(action_type: str) -> dict:
    return WorkflowEngine._execute_action(action_type, {}, uuid.uuid4(), {})


def test_unimplemented_actions_report_not_implemented_instead_of_success():
    for action in (ActionType.SEND_EMAIL, ActionType.SEND_SMS, ActionType.ADD_TO_SEGMENT, ActionType.CREATE_TASK):
        result = _run(action.value)
        assert result["status"] == "not_implemented" and result["action_type"] == action.value
        assert "automatizaciones" in result["detail"]


def test_an_unknown_action_is_still_reported_as_unknown():
    assert _run("teleport")["status"] == "unknown_action"


def test_neither_status_counts_as_a_successful_action():
    # execute_workflow counts only status == "success" as executed; anything else is a failed action.
    assert _run(ActionType.SEND_EMAIL.value)["status"] != "success" and _run("teleport")["status"] != "success"
