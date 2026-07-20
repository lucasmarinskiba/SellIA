"""SellIA Assistant — Meta-Agent Orchestrator

El orchestrador recibe comandos en lenguaje natural del usuario,
entra al LLM con un meta-prompt que describe todos los agentes,
y devuelve una acción estructurada para que el frontend la ejecute.

Soporta:
- Procesamiento síncrono (process_intent)
- Streaming de respuestas (process_intent_stream)
- Ejecución de acciones reales del sistema (SellIAActionExecutor)
"""

import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.domains.agents.models import AgentPersonality, AgentConversation, AgentMessage
from app.domains.agents.services import AgentService
from app.domains.agents.prompts import AGENT_PROMPTS
from app.domains.agents.actions import SellIAActionExecutor
from app.api.v1.computer_use import create_computer_use_from_orchestrator
from app.domains.subscriptions.models import UserAPIKey
from app.core.encryption import decrypt_value
from app.core.config import get_settings


SELLIA_SYSTEM_PROMPT = """You are "SellIA", the intelligent assistant for an AI agent platform called SellIA.

Your mission: help users accomplish their goals by understanding their intent, asking clarifying questions when needed, and routing them to the right AI agents or actions.

## Available Agents (by category)

{agents_summary}

## Your Capabilities

You can perform these actions by returning a JSON response:

1. **ASK_CLARIFICATION** — Ask the user a follow-up question to better understand their need.
   ```json
   {"action": "ASK_CLARIFICATION", "response": "Your question here", "options": ["Option A", "Option B"]}
   ```

2. **SUGGEST_AGENTS** — Suggest 1-3 relevant agents from the list above.
   ```json
   {"action": "SUGGEST_AGENTS", "response": "Your helpful message", "suggested_agents": ["slug1", "slug2"]}
   ```

3. **CREATE_CONVERSATION** — Create a conversation with a specific agent, optionally with context.
   ```json
   {"action": "CREATE_CONVERSATION", "response": "Opening [Agent Name] for you...", "agent_slug": "agent-slug", "context_hint": "Brief context for the agent"}
   ```

4. **GENERATE_CONTENT** — Generate content directly using an agent's expertise.
   ```json
   {"action": "GENERATE_CONTENT", "response": "Generating content with [Agent Name]...", "agent_slug": "agent-slug", "content_request": "What to generate"}
   ```

5. **NAVIGATE** — Navigate the user to a dashboard section.
   ```json
   {"action": "NAVIGATE", "response": "Taking you to...", "target": "section_name"}
   ```

6. **CREATE_SEQUENCE** — Create an email or message sequence.
   ```json
   {"action": "CREATE_SEQUENCE", "response": "Creating email sequence for you...", "sequence_type": "email|whatsapp|sms", "sequence_name": "Name", "steps": [{"step": 1, "delay": "1d", "subject": "...", "content": "..."}]}
   ```

7. **SETUP_AUTOMATION** — Configure an automation workflow.
   ```json
   {"action": "SETUP_AUTOMATION", "response": "Setting up automation...", "automation_name": "Name", "trigger": "event", "actions": ["action1", "action2"]}
   ```

8. **GENERATE_PLAYBOOK** — Generate a sales or business playbook.
   ```json
   {"action": "GENERATE_PLAYBOOK", "response": "Generating playbook...", "playbook_type": "sales|onboarding|retention", "topic": "topic description"}
   ```

9. **ANALYZE_BUSINESS** — Analyze business performance or strategy.
   ```json
   {"action": "ANALYZE_BUSINESS", "response": "Analyzing your business...", "analysis_type": "general|sales|marketing|operations"}
   ```

10. **CREATE_CONTENT_CALENDAR** — Create a weekly/monthly content calendar.
    ```json
    {"action": "CREATE_CONTENT_CALENDAR", "response": "Creating content calendar...", "period": "weekly|monthly", "platforms": ["tiktok", "instagram", "email"], "topics": ["topic1", "topic2"]}
    ```

11. **MULTI_AGENT_PANEL** — Consult multiple experts at once.
    ```json
    {"action": "MULTI_AGENT_PANEL", "response": "Consulting 3 experts...", "agent_slugs": ["slug1", "slug2", "slug3"], "question": "The question to ask them"}
    ```

12. **ACTIVATE_PIPELINE_AGENT** — Activate a specialized pipeline-stage agent for a specific deal/lead.
    ```json
    {"action": "ACTIVATE_PIPELINE_AGENT", "response": "Activating [Stage] agent for this lead...", "stage": "prospecting|qualifying|nurturing|discovery|proposal|objection|closing|onboarding|retention", "deal_id": "uuid-or-null", "context": {"contact_name": "...", "product_name": "...", "pain_points": []}}
    ```
    Use when the user wants to:
    - Handle a specific lead at a specific sales stage
    - Get a script for prospecting, closing, handling objections, etc.
    - Coach on a specific part of the pipeline

13. **NEGOTIATE** — Activate a negotiation strategy agent (Chris Voss, Roger Fisher, Herb Cohen, etc.).
    ```json
    {"action": "NEGOTIATE", "response": "Applying [Expert] negotiation strategy...", "expert": "chris-voss|roger-fisher|herb-cohen|stuart-diamond|william-ury", "situation": "Description of the negotiation scenario"}
    ```

14. **BUILD_OFFER** — Build a Grand Slam Offer using Hormozi's Value Equation.
    ```json
    {"action": "BUILD_OFFER", "response": "Building your Grand Slam Offer...", "product_name": "...", "target_audience": "...", "price_point": 0, "pain_points": []}
    ```

15. **SYSTEM_HEALTH** — Get the current autonomous system health status.
    ```json
    {"action": "SYSTEM_HEALTH", "response": "Checking system health...", "include_recommendations": true}
    ```

16. **COMPUTER_USE** — Use the visual browser automation agent to perform tasks on websites (Canva, Google Docs, social media, etc.).
    ```json
    {"action": "COMPUTER_USE", "response": "I'll open the browser and help you with that...", "task": "Describe what to do", "url": "https://example.com"}
    ```
    Use COMPUTER_USE when the user wants to:
    - Create or edit designs in Canva
    - Fill forms on websites
    - Search for information on the web
    - Navigate tools like Google Docs, Notion, etc.
    - Any task that requires interacting with a web interface visually.

## Pipeline Stage Agents (use ACTIVATE_PIPELINE_AGENT)
- prospecting — Captación de prospectos (Gary Vee methodology)
- qualifying — Calificación BANT+MEDDIC
- nurturing — Nutrición de leads fríos/tibios
- discovery — Diagnóstico de necesidades (SPIN Selling)
- proposal — Construcción de oferta (Hormozi Grand Slam)
- objection — Manejo de objeciones (Belfort + Cialdini)
- closing — Cierre (Ziglar + Cardone + Serhant)
- onboarding — Bienvenida y primera victoria (Bezos Customer Obsession)
- retention — Retención y upsell (RFM + Hormozi LTV)

## Negotiation Experts (use NEGOTIATE)
- chris-voss — FBI negotiation, Never Split the Difference
- roger-fisher — Harvard Negotiation Project, Getting to Yes
- herb-cohen — Power of time/information/perceived power
- stuart-diamond — Wharton emotional negotiation
- william-ury — Getting Past No, Golden Bridge

## Sales Methodology Experts
- brian-tracy — Psychology of Selling, 7-step system
- zig-ziglar — Heart-based selling, Feel-Felt-Found
- neil-rackham — SPIN Selling for complex sales
- sandler-selling — Anti-salesperson, upfront contracts
- meddic-framework — Enterprise deal qualification

## System Sections for Navigation
- agentes — Agent dashboard
- pipeline — Sales pipeline agents
- negocios — Business management
- catalogo — Product catalog
- analytics — Analytics & reports
- conversaciones — Conversations
- automatizaciones — Automation builder
- canales — Channel connections
- planes — Subscription plans
- configuracion — Settings
- autonomo — Sistema autónomo y salud del sistema

## Routing Rules

- ALWAYS respond in the SAME LANGUAGE as the user (Spanish, English, Portuguese, etc.).
- If the user's intent is CLEAR and matches a specific agent, CREATE_CONVERSATION.
- If the intent is VAGUE or could match multiple agents, ASK_CLARIFICATION or SUGGEST_AGENTS.
- Be CONCISE. 1-2 sentences max for the response text.
- Use the agents' EXPERTISE to match them to user needs.
- For SALES PIPELINE tasks (prospecting, qualifying, closing, objections): use ACTIVATE_PIPELINE_AGENT.
- For NEGOTIATION scenarios (price, contracts, disputes): use NEGOTIATE with the right expert.
- For OFFER CREATION (pricing, value stacks, guarantees): use BUILD_OFFER with Hormozi's framework.
- For SYSTEM STATUS (health, security, faults): use SYSTEM_HEALTH.
- For content creation: suggest the best agent based on platform (TikTok → TikTok specialist, Instagram → Instagram specialist).
- For legal/medical/financial advice: suggest the appropriate professional agent.
- For business strategy: suggest Hormozi, Brunson, or business consultants.
- For PR/communications: suggest Ryan Holiday, Tim Ferriss, or David Meerman Scott.
- For entrepreneurship questions: suggest Elon Musk, Daymond John, or Barbara Corcoran agents.
- NEVER make up agents that don't exist in the list.
- ALWAYS return valid JSON."""


class SellIAOrchestrator:
    """Meta-agent that routes user intents to the right agents and actions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_service = AgentService(db)

    def _build_agents_summary(self, personalities: List[AgentPersonality]) -> str:
        """Build a compact summary of all available agents."""
        lines = []
        for p in personalities:
            expertise = ", ".join(p.expertise[:3]) if p.expertise else "General"
            lines.append(f"- {p.slug}: {p.name} ({expertise})")
        return "\n".join(lines)

    async def _resolve_api_key(self, user_id: Any) -> Optional[str]:
        """Resolve OpenAI API key for the user."""
        result = await self.db.execute(
            select(UserAPIKey).where(
                UserAPIKey.user_id == user_id,
                UserAPIKey.provider == "openai",
                UserAPIKey.is_active == True,
            )
        )
        key_record = result.scalar_one_or_none()
        if not key_record or not key_record.api_key_fernet:
            return None
        return decrypt_value(key_record.api_key_fernet)

    def _build_llm_messages(
        self,
        user_input: str,
        agents_summary: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> List:
        """Build LangChain messages for LLM invocation."""
        system_prompt = SELLIA_SYSTEM_PROMPT.format(agents_summary=agents_summary)
        messages = [SystemMessage(content=system_prompt)]

        if conversation_history:
            for msg in conversation_history[-6:]:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_input))
        return messages

    async def process_intent(
        self,
        user_input: str,
        user_id: Any,
        business_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Process a user intent and return an action (sync)."""

        personalities = await self.agent_service.get_personalities(active_only=True)
        agents_summary = self._build_agents_summary(personalities)

        messages = self._build_llm_messages(user_input, agents_summary, conversation_history)

        try:
            from app.domains.agents.llm_provider import generate_with_fallback
            response = await generate_with_fallback(
                db=self.db,
                business_id=business_id,
                messages=messages,
                model="llama3.1",
                temperature=0.3,
                max_tokens=1500,
                use_semantic_cache=False,
                use_smart_router=False,
            )
            if not response:
                return {
                    "action": "ASK_CLARIFICATION",
                    "response": "No se encontró un proveedor de IA disponible. Asegurate de que Ollama esté corriendo o agregá una API key en Configuración.",
                    "options": [],
                }
            action = self._parse_action(response.content)
            action = await self._run_react_if_needed(
                action, user_input, user_id, business_id, conversation_history
            )
            action = await self._execute_action_if_needed(action, user_id, business_id)
            return action
        except Exception as e:
            return {
                "action": "ASK_CLARIFICATION",
                "response": f"Perdón, tuve un problema procesando tu solicitud. ¿Podés reformularla? (Error: {str(e)[:100]})",
                "options": [],
            }

    async def process_intent_stream(
        self,
        user_input: str,
        user_id: Any,
        business_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Process a user intent and yield streaming tokens (SSE format).

        Yields JSON strings with fields:
        - {"type": "token", "content": "..."} — streaming text tokens
        - {"type": "action", "data": {...}} — final parsed action
        - {"type": "error", "message": "..."} — error occurred
        """

        personalities = await self.agent_service.get_personalities(active_only=True)
        agents_summary = self._build_agents_summary(personalities)

        messages = self._build_llm_messages(user_input, agents_summary, conversation_history)

        api_key = await self._resolve_api_key(user_id)

        try:
            if api_key:
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=api_key,
                    temperature=0.3,
                    max_tokens=1500,
                    streaming=True,
                )
            else:
                from langchain_ollama import ChatOllama
                from app.core.config import get_settings
                settings = get_settings()
                llm = ChatOllama(
                    model="llama3.1",
                    base_url=settings.OLLAMA_BASE_URL,
                    temperature=0.3,
                )

            full_text = ""
            async for chunk in llm.astream(messages):
                token = chunk.content
                if token:
                    full_text += token
                    yield json.dumps({"type": "token", "content": token})

            # Parse final action from accumulated text
            action = self._parse_action(full_text)
            action = await self._run_react_if_needed(
                action, user_input, user_id, business_id, conversation_history
            )
            action = await self._execute_action_if_needed(action, user_id, business_id)
            yield json.dumps({"type": "action", "data": action})

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": f"Error: {str(e)[:200]}",
            })

    async def _execute_action_if_needed(
        self,
        action: Dict[str, Any],
        user_id: Any,
        business_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute complex system actions if detected."""
        executable_actions = {
            "CREATE_SEQUENCE",
            "SETUP_AUTOMATION",
            "GENERATE_PLAYBOOK",
            "ANALYZE_BUSINESS",
            # Pipeline + Autonomous actions
            "ACTIVATE_PIPELINE_AGENT",
            "NEGOTIATE",
            "BUILD_OFFER",
            "SYSTEM_HEALTH",
            "CREATE_CONTENT_CALENDAR",
            "MULTI_AGENT_PANEL",
            "COMPUTER_USE",
        }

        action_type = action.get("action", "")
        if action_type in executable_actions:
            executor = SellIAActionExecutor(self.db, user_id, business_id)
            execution_result = await executor.execute(action_type, action)

            if execution_result.get("success"):
                # Merge execution result into action response
                action["execution_result"] = execution_result
                # Update response text if execution provided one
                if "message" in execution_result:
                    action["response"] = execution_result["message"]
            else:
                action["execution_error"] = execution_result.get("error", "Error desconocido")

        return action

    def _should_use_react(self, action_type: str) -> bool:
        """Determine if a complex action should use the ReAct loop."""
        settings = get_settings()
        if not settings.USE_REACT_ORCHESTRATOR:
            return False

        simple_actions = {
            "ASK_CLARIFICATION",
            "SUGGEST_AGENTS",
            "NAVIGATE",
            "CREATE_CONVERSATION",
            "GENERATE_CONTENT",
        }
        return action_type not in simple_actions

    async def _run_react_if_needed(
        self,
        action: Dict[str, Any],
        user_input: str,
        user_id: Any,
        business_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Delegate complex actions to the ReAct orchestrator when enabled."""
        action_type = action.get("action", "")
        if not self._should_use_react(action_type):
            return action

        from app.domains.agents.react_orchestrator import ReActOrchestrator

        react = ReActOrchestrator(
            db=self.db,
            user_id=user_id,
            business_id=business_id,
        )
        react_result = await react.process(
            user_input=user_input,
            conversation_history=conversation_history,
            business_context={"original_action": action},
        )

        # Merge ReAct result into the original action shape
        merged = dict(action)
        merged["response"] = react_result["final_answer"]
        merged["react_metadata"] = {
            "iterations": react_result["iterations"],
            "tool_calls": react_result["tool_calls"],
            "tokens_used": react_result["tokens_used"],
            "model": react_result["model"],
            "provider": react_result["provider"],
        }
        if react_result.get("error"):
            merged["react_metadata"]["error"] = react_result["error"]
        return merged

    def _parse_action(self, text: str) -> Dict[str, Any]:
        """Parse JSON action from LLM response."""
        text = text.strip()

        # Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        if "```json" in text:
            try:
                start = text.index("```json") + 7
                end = text.index("```", start)
                return json.loads(text[start:end].strip())
            except (ValueError, json.JSONDecodeError):
                pass

        # Try to extract JSON from any code block
        if "```" in text:
            try:
                start = text.index("```") + 3
                end = text.index("```", start)
                return json.loads(text[start:end].strip())
            except (ValueError, json.JSONDecodeError):
                pass

        # Try to find JSON between braces
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            pass

        # Fallback: treat as ASK_CLARIFICATION with the raw text
        return {
            "action": "ASK_CLARIFICATION",
            "response": text[:500],
            "options": [],
        }
