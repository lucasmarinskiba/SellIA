"""ReAct Orchestrator for SellIA.

Implements the Reasoning + Acting loop:
  1. THOUGHT: LLM analyzes what it knows and what it needs
  2. ACTION: LLM chooses a tool from the Tool Registry (or outputs final answer)
  3. OBSERVATION: Execute the tool, get result
  4. If more info needed, repeat
  5. FINAL_ANSWER: Generate response to user

Supports both JSON-mode (universal, works with Ollama) and native
function calling for OpenAI/Anthropic when available.
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.core.logger import get_logger
from app.domains.agents.tool_registry import ToolRegistry
from app.domains.agents.llm_provider import generate_with_fallback, resolve_api_keys
from app.domains.agents.business_type_registry import BusinessTypeRegistry
from app.domains.consumo.service import log_ai_call

logger = get_logger(__name__)

# Map BusinessTypeRegistry tool names → ToolRegistry tool names
_TOOL_NAME_MAP = {
    "SearchProducts": "search_products",
    "GetCustomerHistory": "get_customer_history",
    "CheckInventory": "check_inventory",
    "RetrieveKnowledge": "retrieve_knowledge",
    "RetrieveDocuments": "retrieve_documents",
    "SearchMemory": "search_memory",
    "ScheduleMeeting": "schedule_meeting",
}


REACT_SYSTEM_PROMPT = """You are SellIA, an intelligent AI assistant for businesses.
Your job is to help users by thinking step by step and using tools when needed.

You have access to the following tools:
{tool_descriptions}

You must respond with a single valid JSON object and NOTHING else. No markdown, no code blocks, no extra text.
The JSON must have this exact structure:
{{
  "thought": "Your reasoning about what you know and what you need",
  "action": "tool_name or final_answer",
  "action_input": {{}},
  "final_answer": null
}}

Rules:
- If you need more information, set "action" to a tool name and "action_input" to the tool parameters.
- If you have enough information to answer the user, set "action" to "final_answer" and put your response in "final_answer".
- Always think step by step in the "thought" field.
- NEVER make up information. Use tools to verify facts.
- Respond in the SAME LANGUAGE as the user.
- Be concise but complete.

Current date: {current_date}
Business context: {business_context}
"""


class ReActStep(BaseModel):
    thought: str
    action: str
    action_input: Dict[str, Any] = Field(default_factory=dict)
    final_answer: Optional[str] = None


class ReActResult(BaseModel):
    final_answer: str
    iterations: int
    tool_calls: List[Dict[str, Any]]
    tokens_used: int
    model: str
    provider: str
    error: Optional[str] = None


class ReActOrchestrator:
    """Meta-agent that runs a ReAct loop with tool use."""

    def __init__(
        self,
        db,
        user_id: uuid.UUID,
        business_id: Optional[uuid.UUID] = None,
        max_iterations: int = 5,
        business_type: Optional[str] = None,
    ):
        self.db = db
        self.user_id = user_id
        self.business_id = business_id
        self.max_iterations = max_iterations
        self._raw_business_type = business_type
        self.registry = ToolRegistry()
        self._total_tokens = 0
        self._tool_calls: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_system_prompt(self, business_context: Optional[Dict] = None) -> str:
        # Determine allowed tools based on business type
        allowed_tool_names = None
        if self._raw_business_type:
            try:
                from app.domains.business_context.models import BusinessType
                bt = BusinessType(self._raw_business_type)
                relevant = BusinessTypeRegistry.get_relevant_tools(bt, min_priority=30)
                allowed_tool_names = [_TOOL_NAME_MAP.get(t, t.lower()) for t in relevant if t in _TOOL_NAME_MAP]
            except (ValueError, KeyError):
                pass

        tool_desc = self.registry.get_tool_descriptions(allowed_names=allowed_tool_names)

        # Add business-type adaptation if available
        adaptation = ""
        if self._raw_business_type:
            try:
                from app.domains.business_context.models import BusinessType
                bt = BusinessType(self._raw_business_type)
                adaptation = BusinessTypeRegistry.get_prompt_adaptation(bt)
            except (ValueError, KeyError):
                pass

        ctx = dict(business_context or {})
        if adaptation:
            ctx["_type_adaptation"] = adaptation

        return REACT_SYSTEM_PROMPT.format(
            tool_descriptions=tool_desc,
            current_date=datetime.now(timezone.utc).isoformat(),
            business_context=json.dumps(ctx, ensure_ascii=False),
        )

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_step(self, text: str) -> Optional[ReActStep]:
        text = text.strip()

        # Direct JSON parse
        try:
            data = json.loads(text)
            return ReActStep.model_validate(data)
        except Exception:
            pass

        # Markdown code block ```json
        if "```json" in text:
            try:
                start = text.index("```json") + 7
                end = text.index("```", start)
                data = json.loads(text[start:end].strip())
                return ReActStep.model_validate(data)
            except Exception:
                pass

        # Any code block ```
        if "```" in text:
            try:
                start = text.index("```") + 3
                end = text.index("```", start)
                data = json.loads(text[start:end].strip())
                return ReActStep.model_validate(data)
            except Exception:
                pass

        # JSON between braces
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])
            return ReActStep.model_validate(data)
        except Exception:
            pass

        return None

    # ------------------------------------------------------------------
    # LLM invocation
    # ------------------------------------------------------------------

    async def _call_llm(
        self,
        messages: List,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Optional[Any]:
        """Call LLM via the existing fallback infrastructure."""
        response = await generate_with_fallback(
            db=self.db,
            business_id=self.business_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            use_semantic_cache=False,
            use_smart_router=True,
        )
        if response:
            self._total_tokens += response.tokens_used or 0
        return response

    async def _call_llm_with_native_tools(
        self,
        messages: List,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Optional[Any]:
        """Try native tool calling for OpenAI / Anthropic."""
        if not self.business_id:
            return None

        keys = await resolve_api_keys(self.db, self.business_id)
        provider = None
        api_key = None
        model = "gpt-4o-mini"

        if keys.get("openai"):
            provider = "openai"
            api_key = keys["openai"]
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif keys.get("anthropic"):
            provider = "anthropic"
            api_key = keys["anthropic"]
            model = "claude-3-5-sonnet-20241022"
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            return None

        try:
            from langchain_core.tools import StructuredTool
            tools = [
                StructuredTool.from_function(
                    name=t.name,
                    description=t.description,
                    func=lambda **kw: {},  # sync placeholder
                    coroutine=t.execute,
                    args_schema=t.input_schema,
                )
                for t in self.registry.list_tools()
            ]
            llm_with_tools = llm.bind_tools(tools)
            response = await llm_with_tools.ainvoke(messages)

            # If the model made tool calls, we need to return a synthetic text
            # representation so the rest of the loop can handle it uniformly.
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_call = response.tool_calls[0]
                synthetic = {
                    "thought": f"Using native tool calling for {tool_call.get('name', 'unknown')}",
                    "action": tool_call.get("name", ""),
                    "action_input": tool_call.get("args", {}),
                    "final_answer": None,
                }
                from app.domains.agents.llm_provider import LLMResponse
                return LLMResponse(
                    content=json.dumps(synthetic),
                    model=model,
                    provider=provider,
                    tokens_used=response.response_metadata.get("token_usage", {}).get("total_tokens") if hasattr(response, "response_metadata") else None,
                )
            else:
                # Model answered directly
                synthetic = {
                    "thought": "The model provided a direct answer via native tool calling.",
                    "action": "final_answer",
                    "action_input": {},
                    "final_answer": response.content,
                }
                from app.domains.agents.llm_provider import LLMResponse
                return LLMResponse(
                    content=json.dumps(synthetic),
                    model=model,
                    provider=provider,
                    tokens_used=response.response_metadata.get("token_usage", {}).get("total_tokens") if hasattr(response, "response_metadata") else None,
                )
        except Exception as exc:
            logger.warning(f"Native tool calling failed: {exc}. Falling back to JSON mode.")
            return None

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    async def _log_iteration(
        self,
        iteration: int,
        step: ReActStep,
        observation: Optional[str],
        model: str,
        provider: str,
    ):
        try:
            await log_ai_call(
                db=self.db,
                user_id=self.user_id,
                business_id=self.business_id,
                provider=provider,
                model=model,
                task_type="react_iteration",
                tokens_input=0,
                tokens_output=0,
                cost_usd=0.0,
                metadata={
                    "iteration": iteration,
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "observation": observation,
                },
            )
        except Exception as exc:
            logger.warning(f"Failed to log AI call: {exc}")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _load_business_type(self) -> Optional[str]:
        """Lazy-load business_type from BusinessContext if business_id is set."""
        if self._raw_business_type:
            return self._raw_business_type
        if not self.business_id:
            return None
        try:
            from sqlalchemy import select
            from app.domains.business_context.models import BusinessContext
            result = await self.db.execute(
                select(BusinessContext.business_type).where(
                    BusinessContext.business_id == self.business_id,
                    BusinessContext.is_active == True,
                )
            )
            btype = result.scalar_one_or_none()
            if btype:
                self._raw_business_type = btype.value
                return self._raw_business_type
        except Exception as exc:
            logger.debug(f"Could not load business_type: {exc}")
        return None

    async def process(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        business_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self._load_business_type()
        system_prompt = self._build_system_prompt(business_context)
        messages = [SystemMessage(content=system_prompt)]

        if conversation_history:
            for msg in conversation_history[-6:]:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_input))

        iterations = 0
        model_name = "unknown"
        provider_name = "unknown"

        while iterations < self.max_iterations:
            iterations += 1

            # Try native tool calling first for OpenAI/Anthropic
            response = await self._call_llm_with_native_tools(messages)
            if not response:
                response = await self._call_llm(messages, temperature=0.3, max_tokens=2000)

            if not response:
                return {
                    "final_answer": "No se pudo contactar con el proveedor de IA. Verificá que Ollama esté corriendo o que tengas una API key configurada.",
                    "iterations": iterations,
                    "tool_calls": self._tool_calls,
                    "tokens_used": self._total_tokens,
                    "model": model_name,
                    "provider": provider_name,
                    "error": "llm_unavailable",
                }

            model_name = response.model
            provider_name = response.provider

            step = self._parse_step(response.content)
            if not step:
                # If we can't parse, treat raw response as final answer
                step = ReActStep(
                    thought="El modelo no siguió el formato ReAct. Se devuelve la respuesta cruda.",
                    action="final_answer",
                    final_answer=response.content[:2000],
                )

            if step.action == "final_answer" or step.final_answer is not None:
                final = step.final_answer or "No se proporcionó respuesta final."
                await self._log_iteration(iterations, step, None, model_name, provider_name)
                return {
                    "final_answer": final,
                    "iterations": iterations,
                    "tool_calls": self._tool_calls,
                    "tokens_used": self._total_tokens,
                    "model": model_name,
                    "provider": provider_name,
                    "error": None,
                }

            # Execute tool
            observation = await self.registry.execute_tool(
                name=step.action,
                db=self.db,
                business_id=self.business_id,
                **(step.action_input or {}),
            )
            self._tool_calls.append({
                "iteration": iterations,
                "tool": step.action,
                "input": step.action_input,
                "output": observation,
            })

            await self._log_iteration(
                iterations,
                step,
                json.dumps(observation, ensure_ascii=False),
                model_name,
                provider_name,
            )

            # Append to conversation context
            observation_msg = (
                f"Observation from tool '{step.action}':\n"
                f"{json.dumps(observation, ensure_ascii=False)}"
            )
            messages.append(AIMessage(content=response.content))
            messages.append(HumanMessage(content=observation_msg))

        # Max iterations reached
        return {
            "final_answer": "Alcancé el límite de iteraciones sin obtener una respuesta final. Intentá reformular tu pregunta.",
            "iterations": iterations,
            "tool_calls": self._tool_calls,
            "tokens_used": self._total_tokens,
            "model": model_name,
            "provider": provider_name,
            "error": "max_iterations",
        }
