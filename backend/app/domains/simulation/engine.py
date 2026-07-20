"""Simulation / Training Engine

Orchestrates sales simulations between an AI agent and a simulated customer persona,
evaluates performance, and maintains leaderboards.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.simulation.models import SimulationScenario, SimulationRun, SimulationLeaderboard
from app.core.logger import get_logger

logger = get_logger(__name__)


class SimulationEngine:
    """Runs sales simulations and evaluates agent performance."""

    MAX_TURNS = 20
    _CLOSING_KEYWORDS = [
        "adiós", "adios", "chau", "nos vemos", "hasta luego",
        "compra confirmada", "pedido realizado", "orden confirmada",
        "listo, te envío", "gracias por tu compra", "quedamos así",
        "perfecto, pasame los datos", "te paso el link de pago",
    ]

    async def create_scenario(
        self,
        db: AsyncSession,
        business_id: Optional[uuid.UUID],
        name: str,
        description: str,
        difficulty: str,
        objective: str,
        customer_persona: Dict[str, Any],
        agent_type: str,
        success_criteria: Dict[str, Any],
    ) -> SimulationScenario:
        scenario = SimulationScenario(
            business_id=business_id,
            name=name,
            description=description,
            difficulty=difficulty,
            objective=objective,
            customer_persona=customer_persona,
            agent_type=agent_type,
            success_criteria=success_criteria or {},
        )
        db.add(scenario)
        await db.commit()
        await db.refresh(scenario)
        return scenario

    async def run_simulation(
        self,
        db: AsyncSession,
        scenario_id: uuid.UUID,
        user_id: uuid.UUID,
        agent_config: Optional[Dict[str, Any]] = None,
    ) -> SimulationRun:
        result = await db.execute(
            select(SimulationScenario).where(
                SimulationScenario.id == scenario_id,
                SimulationScenario.is_active == True,
            )
        )
        scenario = result.scalar_one_or_none()
        if not scenario:
            raise ValueError("Scenario not found")

        run = SimulationRun(
            scenario_id=scenario_id,
            user_id=user_id,
            agent_config=agent_config or {},
            status="running",
            messages=[],
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        started = datetime.now(timezone.utc)
        messages_history: List[Dict[str, str]] = []

        try:
            # Initial customer message (ice breaker)
            initial_customer = await self._generate_customer_message(db, scenario, messages_history)
            if initial_customer:
                messages_history.append({"role": "customer", "content": initial_customer})

            for turn in range(self.MAX_TURNS):
                # Agent turn
                agent_msg = await self._generate_agent_message(db, scenario, messages_history)
                if not agent_msg:
                    break
                messages_history.append({"role": "agent", "content": agent_msg})

                # Check if agent closed / ended
                if self._check_conversation_ended(agent_msg):
                    break

                # Customer turn
                customer_msg = await self._generate_customer_message(db, scenario, messages_history)
                if not customer_msg:
                    break
                messages_history.append({"role": "customer", "content": customer_msg})

                # Check if customer ended
                if self._check_conversation_ended(customer_msg):
                    break

                # Periodic objective check after turn 8 to avoid premature exits
                if turn >= 8 and turn % 2 == 0:
                    status = await self._check_objective_status(db, scenario, messages_history)
                    if status == "COMPLETE":
                        break

            # Evaluate
            score, outcome, skills, feedback = await self._evaluate_run(db, scenario, messages_history)

            duration = int((datetime.now(timezone.utc) - started).total_seconds())

            run.status = "completed"
            run.messages = messages_history
            run.score = score
            run.outcome = outcome
            run.skills_tested = skills
            run.feedback = feedback
            run.duration_seconds = duration
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(run)

            # Update leaderboard
            await self._update_leaderboard(db, user_id, scenario.agent_type)

        except Exception as e:
            logger.exception(f"Simulation run failed: {e}")
            run.status = "failed"
            run.messages = messages_history
            run.duration_seconds = int((datetime.now(timezone.utc) - started).total_seconds())
            await db.commit()
            await db.refresh(run)

        return run

    async def _generate_agent_message(
        self,
        db: AsyncSession,
        scenario: SimulationScenario,
        messages_history: List[Dict[str, str]],
    ) -> Optional[str]:
        from app.domains.agents.prompts import get_system_prompt
        from app.domains.agents.ai_reply import generate_raw_ai_response

        system_prompt = get_system_prompt(scenario.agent_type)
        system_prompt += (
            f"\n\nSIMULATION CONTEXT: Estás en una simulación de entrenamiento. "
            f"Tu objetivo es: {scenario.objective}. "
            f"El cliente se llama {scenario.customer_persona.get('name', 'Cliente')} y tiene "
            f"estilo de comunicación: {scenario.customer_persona.get('communication_style', 'neutral')}."
        )

        transcript = self._build_transcript(messages_history)
        user_prompt = f"Conversación hasta ahora:\n{transcript}\n\nTu turno como agente de ventas:"

        return await generate_raw_ai_response(
            db=db,
            business_id=scenario.business_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=800,
            temperature=0.7,
        )

    async def _generate_customer_message(
        self,
        db: AsyncSession,
        scenario: SimulationScenario,
        messages_history: List[Dict[str, str]],
    ) -> Optional[str]:
        from app.domains.agents.ai_reply import generate_raw_ai_response

        persona = scenario.customer_persona
        system_prompt = (
            f"Eres {persona.get('name', 'un cliente')}. "
            f"Personalidad: {persona.get('personality', 'neutral')}. "
            f"Presupuesto: {persona.get('budget', 'no especificado')}. "
            f"Puntos de dolor: {', '.join(persona.get('pain_points', []))}. "
            f"Objeciones: {', '.join(persona.get('objections', []))}. "
            f"Estilo de comunicación: {persona.get('communication_style', 'neutral')}. "
            "Responde de forma natural y realista como este cliente. No seas demasiado fácil de convencer."
        )

        transcript = self._build_transcript(messages_history)
        user_prompt = f"Conversación hasta ahora:\n{transcript}\n\nTu turno como cliente:"

        return await generate_raw_ai_response(
            db=db,
            business_id=scenario.business_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=800,
            temperature=0.8,
        )

    def _build_transcript(self, messages_history: List[Dict[str, str]]) -> str:
        lines = []
        for m in messages_history:
            speaker = "Agente" if m["role"] == "agent" else "Cliente"
            lines.append(f"{speaker}: {m['content']}")
        return "\n".join(lines)

    def _check_conversation_ended(self, message: str) -> bool:
        text = message.lower()
        return any(kw in text for kw in self._CLOSING_KEYWORDS)

    async def _check_objective_status(
        self,
        db: AsyncSession,
        scenario: SimulationScenario,
        messages_history: List[Dict[str, str]],
    ) -> str:
        from app.domains.agents.ai_reply import generate_raw_ai_response

        transcript = self._build_transcript(messages_history)
        system_prompt = (
            f"Evalúa si el agente de ventas ya cumplió el objetivo '{scenario.objective}' "
            "en esta conversación. Responde SOLO con una palabra: COMPLETE, PARTIAL o INCOMPLETE."
        )
        user_prompt = f"Conversación:\n{transcript}\n\nEstado del objetivo:"

        result = await generate_raw_ai_response(
            db=db,
            business_id=scenario.business_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=20,
            temperature=0.1,
        )
        if not result:
            return "INCOMPLETE"
        text = result.upper()
        if "COMPLETE" in text and "INCOMPLETE" not in text:
            return "COMPLETE"
        if "PARTIAL" in text:
            return "PARTIAL"
        return "INCOMPLETE"

    async def _evaluate_run(
        self,
        db: AsyncSession,
        scenario: SimulationScenario,
        messages_history: List[Dict[str, str]],
    ) -> tuple:
        from app.domains.agents.ai_reply import generate_raw_ai_response

        transcript = self._build_transcript(messages_history)

        # Score
        score_prompt = (
            "Evalúa esta conversación de ventas del 1 al 100 considerando: "
            "cumplimiento del objetivo, tono apropiado, eficiencia (menos turnos = mejor), creatividad. "
            "Responde SOLO con un número del 1 al 100."
        )
        score_raw = await generate_raw_ai_response(
            db=db,
            business_id=scenario.business_id,
            system_prompt=score_prompt,
            user_prompt=f"Conversación:\n{transcript}\n\nPuntuación:",
            max_tokens=20,
            temperature=0.1,
        )
        score = self._extract_number(score_raw, default=50, max_val=100)

        # Outcome
        status = await self._check_objective_status(db, scenario, messages_history)
        outcome_map = {"COMPLETE": "success", "PARTIAL": "partial", "INCOMPLETE": "failure"}
        outcome = outcome_map.get(status, "failure")

        # Skills
        skills_prompt = (
            "Analiza esta conversación de ventas y evalúa estas habilidades del 1 al 100. "
            'Responde SOLO con JSON válido: {"closing": 85, "empathy": 70, "objection_handling": 60, "efficiency": 80}'
        )
        skills_raw = await generate_raw_ai_response(
            db=db,
            business_id=scenario.business_id,
            system_prompt=skills_prompt,
            user_prompt=f"Conversación:\n{transcript}\n\nJSON de habilidades:",
            max_tokens=200,
            temperature=0.1,
        )
        skills = self._extract_json(skills_raw, default={})

        # Feedback
        feedback_prompt = (
            "Eres un coach de ventas experto. Analiza esta conversación y da feedback constructivo en español. "
            "Indica qué se hizo bien y qué se puede mejorar. Sé específico y conciso (máximo 300 palabras)."
        )
        feedback = await generate_raw_ai_response(
            db=db,
            business_id=scenario.business_id,
            system_prompt=feedback_prompt,
            user_prompt=f"Conversación:\n{transcript}\n\nFeedback:",
            max_tokens=600,
            temperature=0.7,
        )
        if not feedback:
            feedback = "No se pudo generar feedback automático."

        return score, outcome, skills, feedback

    def _extract_number(self, text: Optional[str], default: int = 0, max_val: int = 100) -> int:
        if not text:
            return default
        digits = "".join(c for c in text if c.isdigit())
        try:
            val = int(digits[:3])
            return max(0, min(max_val, val))
        except ValueError:
            return default

    def _extract_json(self, text: Optional[str], default: Dict[str, Any]) -> Dict[str, Any]:
        if not text:
            return default
        try:
            cleaned = text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            return json.loads(cleaned)
        except Exception:
            return default

    async def _update_leaderboard(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        agent_type: str,
    ) -> None:
        result = await db.execute(
            select(SimulationLeaderboard).where(
                SimulationLeaderboard.user_id == user_id,
                SimulationLeaderboard.agent_type == agent_type,
            )
        )
        lb = result.scalar_one_or_none()

        # Aggregate from all runs for this user + agent_type
        agg_result = await db.execute(
            select(
                func.count(SimulationRun.id),
                func.avg(SimulationRun.score),
                func.max(SimulationRun.score),
            ).where(
                SimulationRun.user_id == user_id,
                SimulationRun.agent_type == agent_type,
                SimulationRun.status == "completed",
            )
        )
        total_runs, avg_score, best_score = agg_result.one()
        total_runs = total_runs or 0
        avg_score = float(avg_score or 0.0)
        best_score = best_score or 0

        success_result = await db.execute(
            select(func.count(SimulationRun.id)).where(
                SimulationRun.user_id == user_id,
                SimulationRun.agent_type == agent_type,
                SimulationRun.status == "completed",
                SimulationRun.outcome == "success",
            )
        )
        success_count = success_result.scalar() or 0
        success_rate = success_count / total_runs if total_runs > 0 else 0.0

        if not lb:
            lb = SimulationLeaderboard(
                user_id=user_id,
                agent_type=agent_type,
            )
            db.add(lb)

        lb.total_runs = total_runs
        lb.avg_score = avg_score
        lb.best_score = best_score
        lb.success_rate = success_rate
        lb.updated_at = datetime.now(timezone.utc)
        await db.commit()

    async def get_leaderboard(
        self,
        db: AsyncSession,
        agent_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[SimulationLeaderboard]:
        query = select(SimulationLeaderboard).order_by(
            desc(SimulationLeaderboard.avg_score)
        ).limit(limit)
        if agent_type:
            query = query.where(SimulationLeaderboard.agent_type == agent_type)
        result = await db.execute(query)
        return list(result.scalars().all())
