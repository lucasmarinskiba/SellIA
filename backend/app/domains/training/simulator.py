"""Simulation / Training Engine — Core Simulator

Uses the existing LLM router (`generate_with_fallback`) and ReAct orchestrator
patterns to run agent-vs-customer simulations without real customers.
"""

import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.core.logger import get_logger
from app.domains.agents.llm_provider import generate_with_fallback
from app.domains.training.models import TrainingScenario, TrainingRun
from app.domains.agents.models import AgentConfig, AgentPersonality

logger = get_logger(__name__)

CUSTOMER_TYPES = {
    "indeciso": {
        "description": "Cliente indeciso que necesita mucha información antes de decidir.",
        "common_objections": ["Necesito pensarlo", "Déjame consultar con mi pareje", "No estoy seguro/a"],
        "budget_range": "medio-bajo",
        "decision_speed": "lento",
    },
    "aggressive": {
        "description": "Cliente agresivo que presiona por descuentos y respuestas inmediatas.",
        "common_objections": ["Me lo dan más barato en otro lado", "No me interesa si no hay descuento", "Respondeme ya"],
        "budget_range": "variable",
        "decision_speed": "rápido",
    },
    "price-sensitive": {
        "description": "Cliente muy enfocado en el precio, compara constantemente.",
        "common_objections": ["Es muy caro", "¿No tienen algo más barato?", "¿Me pueden hacer un precio?"],
        "budget_range": "bajo",
        "decision_speed": "medio",
    },
    "feature-focused": {
        "description": "Cliente técnico que pregunta por características y especificaciones.",
        "common_objections": ["No tiene la función X", "Prefiero la versión Pro", "¿Soporta integración con Z?"],
        "budget_range": "alto",
        "decision_speed": "lento",
    },
    "rushed": {
        "description": "Cliente apurado que quiere resolver todo en 2 mensajes.",
        "common_objections": ["No tengo tiempo", "Resumime", "Solo dime sí o no"],
        "budget_range": "alto",
        "decision_speed": "muy rápido",
    },
    "friendly": {
        "description": "Cliente amable y colaborativo, fácil de tratar pero puede no comprar.",
        "common_objections": ["Me encanta pero no puedo ahora", "Quizás el mes que viene", "Gracias por la info"],
        "budget_range": "medio",
        "decision_speed": "medio",
    },
    "skeptical": {
        "description": "Cliente escéptico que desconfía de todo hasta ver pruebas.",
        "common_objections": ["¿Por qué debería confiar?", "Demostrame que funciona", "Suena demasiado bueno"],
        "budget_range": "medio",
        "decision_speed": "lento",
    },
}

AGENT_SYSTEM_PROMPT_TEMPLATE = """You are a professional sales AI agent for a business.
Your agent type / personality: {agent_type}
Your objective in this conversation: {objective}

Scenario context:
{scenario_description}

Instructions:
- Be professional, persuasive, and concise.
- Use the best sales techniques for the situation.
- Your goal is to achieve the objective above.
- Respond in the SAME LANGUAGE as the customer (Spanish by default).
- Do NOT use markdown formatting. Write plain text as if it were a chat message.
- Keep responses under 3 sentences when possible.
"""

CUSTOMER_SYSTEM_PROMPT_TEMPLATE = """You are a simulated customer interacting with a sales AI agent.

Your customer persona:
- Type: {customer_type}
- Personality: {personality_description}
- Common objections: {common_objections}
- Budget range: {budget_range}
- Decision speed: {decision_speed}

Objective of the sales agent: {agent_objective}

Instructions:
- Stay in character at ALL times.
- React naturally based on your persona.
- If the agent is pushy, resist. If helpful, warm up.
- Use the SAME LANGUAGE as the agent (Spanish by default).
- Do NOT use markdown. Write plain text chat messages.
- Keep responses under 3 sentences.
- If the agent successfully achieves the objective and you are satisfied, you may say a closing phrase like "LISTO_CIERRE" or "OK_AGENDADO" to end the conversation.
- If you are clearly not interested and the agent is not helping, you may say "FIN_CONVERSACION" to end.
"""

EVALUATION_SYSTEM_PROMPT = """You are an expert sales coach evaluating an AI agent's performance in a simulated sales conversation.

Scenario Objective: {objective}
Success Criteria: {success_criteria}
Conversation:
{conversation_text}

Evaluate the agent and return ONLY a valid JSON object with this exact structure:
{{
  "objective_achieved": true|false,
  "score": 0-100,
  "customer_satisfaction": 0.0-5.0,
  "time_to_close_turns": number,
  "skills_tested": {{
    "rapport_building": 0-100,
    "objection_handling": 0-100,
    "closing": 0-100,
    "empathy": 0-100,
    "product_knowledge": 0-100
  }},
  "feedback": "Detailed qualitative feedback in Spanish. What did the agent do well? What could improve?"
}}

Rules:
- Be strict but fair. A mediocre agent should get 50-60.
- Only give 90+ for truly excellent performance.
- Return ONLY the JSON object, no markdown, no extra text.
"""

PERSONA_GENERATION_PROMPT = """Generate a detailed synthetic customer persona for a sales training simulation.

Difficulty: {difficulty}

Return ONLY a valid JSON object:
{{
  "customer_type": "one of: indeciso, aggressive, price-sensitive, feature-focused, rushed, friendly, skeptical",
  "personality_description": "2-3 sentences describing this person's attitude and background",
  "common_objections": ["objeción 1", "objeción 2", "objeción 3"],
  "budget_range": "bajo|medio-bajo|medio|alto|muy alto",
  "decision_speed": "muy lento|lento|medio|rápido|muy rápido",
  "urgency": "low|medium|high",
  "extra_traits": {{"key": "value"}}
}}

No markdown, no extra text. Only the JSON.
"""


class SimulationEngine:
    """Runs agent-vs-simulated-customer conversations and evaluates them."""

    def __init__(self, db: AsyncSession, business_id: Optional[uuid.UUID] = None):
        self.db = db
        self.business_id = business_id
        self.max_turns = 20

    # ------------------------------------------------------------------
    # Persona generation
    # ------------------------------------------------------------------

    async def create_customer_persona(self, difficulty: str = "medium") -> Dict[str, Any]:
        """Generate a synthetic customer profile using the LLM."""
        if not self.business_id:
            # Fallback to deterministic persona based on difficulty
            return self._fallback_persona(difficulty)

        messages = [
            SystemMessage(content="You generate realistic customer personas for sales training."),
            HumanMessage(content=PERSONA_GENERATION_PROMPT.format(difficulty=difficulty)),
        ]

        response = await generate_with_fallback(
            db=self.db,
            business_id=self.business_id,
            messages=messages,
            model="llama3.1",
            temperature=0.8,
            max_tokens=800,
            use_semantic_cache=False,
            use_smart_router=False,
        )

        if response and response.content:
            try:
                persona = json.loads(response.content.strip())
                # Validate required keys
                required = {"customer_type", "personality_description", "common_objections", "budget_range", "decision_speed"}
                if required.issubset(persona.keys()):
                    return persona
            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON for persona generation, using fallback.")

        return self._fallback_persona(difficulty)

    def _fallback_persona(self, difficulty: str) -> Dict[str, Any]:
        """Deterministic fallback persona when LLM is unavailable."""
        mapping = {
            "easy": "friendly",
            "medium": "indeciso",
            "hard": "price-sensitive",
            "expert": "skeptical",
        }
        ctype = mapping.get(difficulty, "friendly")
        base = CUSTOMER_TYPES[ctype].copy()
        base["customer_type"] = ctype
        base["urgency"] = "medium"
        base["extra_traits"] = {}
        return base

    # ------------------------------------------------------------------
    # Simulation loop
    # ------------------------------------------------------------------

    async def run_simulation(
        self,
        scenario_id: uuid.UUID,
        agent_type: str,
        run_id: Optional[uuid.UUID] = None,
    ) -> TrainingRun:
        """Run a full simulation: load scenario, converse, evaluate, save results."""
        start_time = time.monotonic()

        # Load scenario
        result = await self.db.execute(
            select(TrainingScenario).where(TrainingScenario.id == scenario_id)
        )
        scenario = result.scalar_one_or_none()
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        self.business_id = scenario.business_id

        # Resolve agent_id from agent_type if possible
        agent_id = await self._resolve_agent_id(agent_type)

        # Create or reuse run record
        if run_id:
            result = await self.db.execute(
                select(TrainingRun).where(TrainingRun.id == run_id)
            )
            run = result.scalar_one_or_none()
            if not run:
                raise ValueError(f"Run {run_id} not found")
            run.status = "running"
            run.agent_id = agent_id
            run.messages = []
        else:
            run = TrainingRun(
                scenario_id=scenario_id,
                agent_id=agent_id,
                status="running",
                messages=[],
            )
            self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)

        try:
            # Build or use customer persona
            persona = scenario.customer_persona or {}
            if not persona:
                persona = await self.create_customer_persona(scenario.difficulty)

            # Run conversation loop
            messages_log: List[Dict[str, Any]] = []
            conversation_turns = 0
            objective_achieved = False
            conversation_ended = False

            # Initial customer message
            customer_msg = await self._generate_customer_message(
                persona=persona,
                agent_objective=scenario.objective,
                conversation_history=messages_log,
            )
            messages_log.append({"role": "customer", "content": customer_msg, "turn": 0, "timestamp": datetime.now(timezone.utc).isoformat()})

            for turn in range(1, self.max_turns + 1):
                conversation_turns = turn

                # Agent responds
                agent_msg = await self._generate_agent_message(
                    agent_type=agent_type,
                    objective=scenario.objective,
                    scenario_description=scenario.description or "",
                    conversation_history=messages_log,
                )
                messages_log.append({"role": "agent", "content": agent_msg, "turn": turn, "timestamp": datetime.now(timezone.utc).isoformat()})

                # Check for objective achievement signals from agent message
                if self._check_agent_objective_achievement(agent_msg, scenario.objective):
                    objective_achieved = True

                # Customer responds
                customer_msg = await self._generate_customer_message(
                    persona=persona,
                    agent_objective=scenario.objective,
                    conversation_history=messages_log,
                )
                messages_log.append({"role": "customer", "content": customer_msg, "turn": turn, "timestamp": datetime.now(timezone.utc).isoformat()})

                # Check for conversation end signals
                if self._check_conversation_end(customer_msg):
                    conversation_ended = True
                    break

                # If objective achieved and customer seems satisfied, end early
                if objective_achieved and self._check_customer_satisfaction(customer_msg):
                    break

            # Update run with conversation
            run.messages = messages_log
            run.time_to_close_seconds = int(time.monotonic() - start_time)
            await self.db.commit()

            # Evaluate
            await self.evaluate_simulation(run.id, scenario=scenario)

            # Reload and return
            await self.db.refresh(run)
            return run

        except Exception as exc:
            logger.exception(f"Simulation run {run.id} failed: {exc}")
            run.status = "failed"
            run.feedback = f"Simulation failed: {str(exc)[:500]}"
            run.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            raise

    async def _resolve_agent_id(self, agent_type: str) -> Optional[uuid.UUID]:
        """Try to resolve agent_type string to an AgentConfig UUID."""
        # If it looks like a UUID, use it directly
        try:
            return uuid.UUID(agent_type)
        except ValueError:
            pass

        # Try to find an AgentConfig whose personality slug matches agent_type
        try:
            result = await self.db.execute(
                select(AgentConfig.id)
                .join(AgentPersonality, AgentConfig.personality_id == AgentPersonality.id)
                .where(AgentPersonality.slug == agent_type)
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                return row
        except Exception:
            pass

        return None

    async def _generate_agent_message(
        self,
        agent_type: str,
        objective: str,
        scenario_description: str,
        conversation_history: List[Dict[str, Any]],
    ) -> str:
        """Generate the AI agent's next message using the existing LLM router."""
        system_prompt = AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            agent_type=agent_type,
            objective=objective,
            scenario_description=scenario_description or "No additional context.",
        )
        messages = [SystemMessage(content=system_prompt)]

        for msg in conversation_history[-10:]:
            if msg["role"] == "customer":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "agent":
                messages.append(AIMessage(content=msg["content"]))

        response = await generate_with_fallback(
            db=self.db,
            business_id=self.business_id,
            messages=messages,
            model="llama3.1",
            temperature=0.7,
            max_tokens=400,
            use_semantic_cache=False,
            use_smart_router=True,
        )

        if response and response.content:
            return response.content.strip()
        return "Disculpe, ¿podría repetirme?"

    async def _generate_customer_message(
        self,
        persona: Dict[str, Any],
        agent_objective: str,
        conversation_history: List[Dict[str, Any]],
    ) -> str:
        """Generate the simulated customer's next message using the LLM."""
        system_prompt = CUSTOMER_SYSTEM_PROMPT_TEMPLATE.format(
            customer_type=persona.get("customer_type", "friendly"),
            personality_description=persona.get("personality_description", "Cliente genérico."),
            common_objections=", ".join(persona.get("common_objections", [])),
            budget_range=persona.get("budget_range", "medio"),
            decision_speed=persona.get("decision_speed", "medio"),
            agent_objective=agent_objective,
        )
        messages = [SystemMessage(content=system_prompt)]

        for msg in conversation_history[-10:]:
            if msg["role"] == "agent":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "customer":
                messages.append(AIMessage(content=msg["content"]))

        response = await generate_with_fallback(
            db=self.db,
            business_id=self.business_id,
            messages=messages,
            model="llama3.1",
            temperature=0.8,
            max_tokens=400,
            use_semantic_cache=False,
            use_smart_router=False,
        )

        if response and response.content:
            return response.content.strip()
        return "Mmm, no sé..."

    def _check_agent_objective_achievement(self, agent_msg: str, objective: str) -> bool:
        """Quick heuristic to detect if the agent claims to have achieved the objective."""
        msg_lower = agent_msg.lower()
        signals = {
            "close_sale": ["comprar", "compra", "pedido", "orden", "pag", "cerramos", "listo", "envío"],
            "set_appointment": ["agendar", "cita", "reunión", "calendario", "horario", "disponible"],
            "gather_info": ["datos", "información", "email", "teléfono", "contacto", "nombre"],
            "handle_complaint": ["solución", "resolver", "reembolso", "disculpa", "ayudar", "arreglar"],
        }
        keywords = signals.get(objective, [])
        return any(k in msg_lower for k in keywords)

    def _check_conversation_end(self, customer_msg: str) -> bool:
        """Detect explicit conversation end signals from customer."""
        signals = ["fin_conversacion", "listo_cierre", "ok_agendado", "no me interesa", "adiós", "hasta luego"]
        return any(s in customer_msg.lower() for s in signals)

    def _check_customer_satisfaction(self, customer_msg: str) -> bool:
        """Heuristic: customer seems satisfied and ready to wrap up."""
        positive = ["gracias", "perfecto", "genial", "excelente", "me sirve", "ok", "dale", "hagámoslo", "confirmo"]
        return any(p in customer_msg.lower() for p in positive)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    async def evaluate_simulation(
        self,
        run_id: uuid.UUID,
        scenario: Optional[TrainingScenario] = None,
    ) -> Dict[str, Any]:
        """Use LLM to evaluate a completed simulation run."""
        result = await self.db.execute(
            select(TrainingRun).where(TrainingRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        if not scenario:
            scenario = run.scenario

        # Build conversation text for evaluator
        conversation_text = "\n".join(
            f"{'Agent' if m['role'] == 'agent' else 'Customer'}: {m['content']}"
            for m in run.messages
        )

        success_criteria = json.dumps(scenario.success_criteria or {}, ensure_ascii=False)

        eval_prompt = EVALUATION_SYSTEM_PROMPT.format(
            objective=scenario.objective,
            success_criteria=success_criteria,
            conversation_text=conversation_text,
        )

        messages = [
            SystemMessage(content="You are an expert sales coach evaluator."),
            HumanMessage(content=eval_prompt),
        ]

        response = await generate_with_fallback(
            db=self.db,
            business_id=self.business_id,
            messages=messages,
            model="llama3.1",
            temperature=0.3,
            max_tokens=1200,
            use_semantic_cache=False,
            use_smart_router=False,
        )

        eval_data = self._parse_evaluation(response.content if response else "")

        # Update run
        run.score = eval_data.get("score")
        run.objective_achieved = eval_data.get("objective_achieved")
        run.customer_satisfaction = eval_data.get("customer_satisfaction")
        run.skills_tested = eval_data.get("skills_tested", {})
        run.feedback = eval_data.get("feedback")
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(run)

        return eval_data

    def _parse_evaluation(self, text: str) -> Dict[str, Any]:
        """Parse evaluation JSON from LLM response."""
        text = (text or "").strip()
        try:
            # Try direct JSON
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try markdown code block
        if "```json" in text:
            try:
                start = text.index("```json") + 7
                end = text.index("```", start)
                return json.loads(text[start:end].strip())
            except (ValueError, json.JSONDecodeError):
                pass

        if "```" in text:
            try:
                start = text.index("```") + 3
                end = text.index("```", start)
                return json.loads(text[start:end].strip())
            except (ValueError, json.JSONDecodeError):
                pass

        # Try finding JSON between braces
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            pass

        logger.warning("Failed to parse evaluation JSON, returning defaults.")
        return {
            "objective_achieved": False,
            "score": 0,
            "customer_satisfaction": 0.0,
            "time_to_close_turns": 0,
            "skills_tested": {},
            "feedback": "No se pudo evaluar la simulación automáticamente.",
        }
