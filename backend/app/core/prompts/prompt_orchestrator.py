"""Prompt Orchestrator — Execute prompts with context injection and result parsing."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PromptExecution:
    """Track a single prompt execution."""
    prompt_id: str
    execution_id: str
    context_vars: Dict[str, Any]
    executed_prompt_text: str
    result: str
    execution_timestamp: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None


class PromptOrchestrator:
    """Execute prompts with context injection, result parsing, and effectiveness tracking."""

    def __init__(self, registry=None):
        """Initialize orchestrator with registry."""
        self.registry = registry
        self.execution_history: List[PromptExecution] = []
        self.llm_client = None  # Inject your LLM client (Claude API, etc.)

    def set_llm_client(self, client):
        """Set the LLM client for prompt execution."""
        self.llm_client = client

    def prepare_prompt(self, prompt: Any, context_vars: Dict[str, Any]) -> str:
        """Inject context variables into prompt template."""
        prompt_text = prompt.prompt_text

        # Replace all variables with context values
        for var_name in prompt.variables:
            placeholder = "{" + var_name + "}"
            value = context_vars.get(var_name, f"[MISSING: {var_name}]")

            # Handle nested variables
            if isinstance(value, dict):
                value = json.dumps(value)
            elif isinstance(value, list):
                value = ", ".join(str(v) for v in value)

            prompt_text = prompt_text.replace(placeholder, str(value))

        return prompt_text

    def validate_context(self, prompt: Any, context_vars: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate that all required context variables are provided."""
        missing_vars = []

        for var_name in prompt.variables:
            if var_name not in context_vars or context_vars[var_name] is None:
                missing_vars.append(var_name)

        is_valid = len(missing_vars) == 0
        return is_valid, missing_vars

    def execute(self, prompt: Any, context_vars: Dict[str, Any], execution_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a prompt with context injection."""
        import uuid
        import time

        if execution_id is None:
            execution_id = str(uuid.uuid4())

        start_time = time.time()
        result_text = ""
        error_message = None
        success = False

        try:
            # Validate context
            is_valid, missing_vars = self.validate_context(prompt, context_vars)
            if not is_valid:
                error_message = f"Missing context variables: {', '.join(missing_vars)}"
                logger.error(error_message)
                raise ValueError(error_message)

            # Prepare prompt with injected context
            executed_prompt_text = self.prepare_prompt(prompt, context_vars)

            # Execute via LLM (if client available)
            if self.llm_client:
                result_text = self._call_llm(executed_prompt_text)
                success = True
            else:
                # Fallback: return prompt text with markers
                result_text = f"[PROMPT READY FOR EXECUTION]\n\n{executed_prompt_text}"
                success = True

            logger.info(f"Executed prompt: {prompt.id} ({execution_id})")

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error executing prompt: {error_message}")
            success = False

        # Record execution
        duration_ms = (time.time() - start_time) * 1000
        execution = PromptExecution(
            prompt_id=getattr(prompt, 'id', 'unknown'),
            execution_id=execution_id,
            context_vars=context_vars,
            executed_prompt_text=executed_prompt_text if success else "",
            result=result_text,
            execution_timestamp=datetime.utcnow().isoformat(),
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        self.execution_history.append(execution)

        return {
            'execution_id': execution_id,
            'prompt_id': getattr(prompt, 'id', 'unknown'),
            'success': success,
            'result': result_text,
            'error': error_message,
            'duration_ms': duration_ms,
            'timestamp': execution.execution_timestamp
        }

    def _call_llm(self, prompt_text: str) -> str:
        """Call LLM API to execute prompt."""
        if not self.llm_client:
            return "[LLM client not configured]"

        try:
            # This is a placeholder — implement with your LLM client
            # Example: Claude API, OpenAI, etc.
            response = self.llm_client.generate(
                prompt=prompt_text,
                max_tokens=2000,
                temperature=0.7
            )
            return response.get('text', '')
        except Exception as e:
            logger.error(f"LLM execution error: {e}")
            raise

    def batch_execute(self, prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple prompts in sequence."""
        results = []

        for prompt_config in prompts:
            prompt = prompt_config.get('prompt')
            context_vars = prompt_config.get('context_vars', {})
            execution_id = prompt_config.get('execution_id')

            result = self.execute(prompt, context_vars, execution_id)
            results.append(result)

        logger.info(f"Batch executed {len(results)} prompts")
        return results

    def get_execution_history(self, prompt_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve execution history."""
        history = self.execution_history

        if prompt_id:
            history = [e for e in history if e.prompt_id == prompt_id]

        # Return most recent first
        history = sorted(history, key=lambda x: x.execution_timestamp, reverse=True)[:limit]

        return [
            {
                'execution_id': e.execution_id,
                'prompt_id': e.prompt_id,
                'timestamp': e.execution_timestamp,
                'duration_ms': e.duration_ms,
                'success': e.success,
                'context_vars': e.context_vars,
                'result_preview': e.result[:500] if e.result else ""
            }
            for e in history
        ]

    def record_effectiveness(self, execution_id: str, effectiveness_score: float) -> bool:
        """Record effectiveness of an execution."""
        execution = next((e for e in self.execution_history if e.execution_id == execution_id), None)

        if not execution:
            return False

        if self.registry:
            self.registry.record_effectiveness(execution.prompt_id, effectiveness_score)

        logger.info(f"Recorded effectiveness: {execution_id} = {effectiveness_score}")
        return True

    def get_suggested_prompts(self, use_case: str) -> List[Dict[str, Any]]:
        """Get suggested prompts for a use case."""
        if not self.registry:
            return []

        return self.registry.get_recommended_prompts(use_case)

    def search_prompts(self, query: str, search_type: str = 'tag') -> List[str]:
        """Search for prompts."""
        if not self.registry:
            return []

        return self.registry.search(query, search_type)

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get statistics on prompt executions."""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_duration_ms': 0,
                'unique_prompts_executed': 0
            }

        successful = [e for e in self.execution_history if e.success]
        failed = [e for e in self.execution_history if not e.success]

        avg_duration = sum(e.duration_ms for e in self.execution_history) / len(self.execution_history)
        unique_prompts = len(set(e.prompt_id for e in self.execution_history))

        return {
            'total_executions': len(self.execution_history),
            'successful_executions': len(successful),
            'failed_executions': len(failed),
            'success_rate': len(successful) / len(self.execution_history) if self.execution_history else 0,
            'average_duration_ms': avg_duration,
            'unique_prompts_executed': unique_prompts,
            'execution_timeline': {
                'oldest': self.execution_history[-1].execution_timestamp if self.execution_history else None,
                'newest': self.execution_history[0].execution_timestamp if self.execution_history else None
            }
        }

    def export_execution_logs(self, filename: str) -> bool:
        """Export execution history to JSON file."""
        try:
            export_data = [
                {
                    'execution_id': e.execution_id,
                    'prompt_id': e.prompt_id,
                    'timestamp': e.execution_timestamp,
                    'success': e.success,
                    'duration_ms': e.duration_ms,
                    'context_vars': e.context_vars,
                    'result': e.result,
                    'error': e.error_message
                }
                for e in self.execution_history
            ]

            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported execution logs to: {filename}")
            return True

        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return False
