"""Planning Agent for complex multi-step tasks.

Breaks down high-level tasks into sub-tasks and executes each one
via the ReAct orchestrator.
"""

import json
import uuid
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.logger import get_logger
from app.domains.agents.llm_provider import generate_with_fallback
from app.domains.agents.react_orchestrator import ReActOrchestrator
from app.domains.consumo.service import log_ai_call

logger = get_logger(__name__)


PLANNER_SYSTEM_PROMPT = """You are a task planner. Break down the user's request into a list of sub-tasks.
Each sub-task must have:
- id: a short string identifier (e.g., "step_1")
- description: what needs to be done
- required_tools: list of tool names that might be needed from the available set:
  search_products, get_customer_history, check_inventory, retrieve_knowledge, retrieve_documents, search_memory, schedule_meeting
- dependencies: list of step_ids that must be completed before this one (can be empty)

Respond ONLY with a JSON object in this exact format:
{
  "sub_tasks": [
    {
      "id": "step_1",
      "description": "...",
      "required_tools": ["tool_name"],
      "dependencies": []
    }
  ]
}

Do not add markdown or explanations outside the JSON."""


class PlanStep(BaseModel):
    id: str
    description: str
    required_tools: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


class Plan(BaseModel):
    sub_tasks: List[PlanStep]


class PlanningAgent:
    """Agent that creates and executes plans using ReAct."""

    def __init__(
        self,
        db,
        user_id: uuid.UUID,
        business_id: Optional[uuid.UUID] = None,
    ):
        self.db = db
        self.user_id = user_id
        self.business_id = business_id

    async def create_plan(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Plan:
        """Create a plan from a high-level task description."""
        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Task: {task_description}\nContext: {json.dumps(context or {}, ensure_ascii=False)}"
            ),
        ]

        response = await generate_with_fallback(
            db=self.db,
            business_id=self.business_id,
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
            use_semantic_cache=False,
            use_smart_router=True,
        )

        if not response:
            raise RuntimeError("No LLM provider available for planning")

        text = response.content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            plan = Plan.model_validate(data)
        except Exception as exc:
            logger.warning(f"Failed to parse plan JSON: {exc}. Text: {text[:500]}")
            # Fallback single-step plan
            plan = Plan(
                sub_tasks=[
                    PlanStep(
                        id="step_1",
                        description=task_description,
                        required_tools=[],
                        dependencies=[],
                    )
                ]
            )

        try:
            await log_ai_call(
                db=self.db,
                user_id=self.user_id,
                business_id=self.business_id,
                provider=response.provider,
                model=response.model,
                task_type="planning",
                tokens_input=0,
                tokens_output=response.tokens_used or 0,
                cost_usd=0.0,
                metadata={"task": task_description, "plan": plan.model_dump()},
            )
        except Exception as exc:
            logger.warning(f"Failed to log planning call: {exc}")

        return plan

    async def execute_plan(
        self,
        plan: Plan,
        react_orchestrator: ReActOrchestrator,
    ) -> Dict[str, Any]:
        """Execute each sub-task in the plan using ReAct."""
        completed_steps: Dict[str, Any] = {}
        results = []

        for step in plan.sub_tasks:
            missing = [d for d in step.dependencies if d not in completed_steps]
            if missing:
                results.append({
                    "step_id": step.id,
                    "status": "skipped",
                    "reason": f"Missing dependencies: {missing}",
                })
                continue

            step_prompt = (
                f"Execute this sub-task: {step.description}\n"
                f"Required tools: {', '.join(step.required_tools) if step.required_tools else 'none'}\n"
                f"Previous results: {json.dumps(completed_steps, ensure_ascii=False)}"
            )

            try:
                step_result = await react_orchestrator.process(
                    user_input=step_prompt,
                    business_context={"step_id": step.id, "required_tools": step.required_tools},
                )
                completed_steps[step.id] = step_result
                results.append({
                    "step_id": step.id,
                    "status": "completed",
                    "result": step_result,
                })
            except Exception as exc:
                logger.exception(f"Plan step {step.id} failed: {exc}")
                results.append({
                    "step_id": step.id,
                    "status": "failed",
                    "error": str(exc),
                })

        return {
            "plan": plan.model_dump(),
            "results": results,
            "completed_steps": len([r for r in results if r["status"] == "completed"]),
            "failed_steps": len([r for r in results if r["status"] == "failed"]),
        }
