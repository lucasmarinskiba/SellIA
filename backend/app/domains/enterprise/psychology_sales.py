"""Phase 31 - Psychology Sales System (Jordan Belfort Method), in Spanish.

The engines here store what the prospect said and build the scripts. The moves that depend on a
business fact (scarcity, deadlines, customer proof, guarantees) are gated in psychology_intelligence:
without the fact they are not produced.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.enterprise.psychology_intelligence import (
    PAIN_RX,
    TIMELINE_RX,
    annual_amounts,
    classify_objection,
    is_positive_reply,
    urgency_triggers,
)
from app.models.psychology_sales import (
    DiscoveryResponse,
    NeedNarrative,
)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)

# The Claude path is only taken when a key is passed in; the routes do not pass one.
CLAUDE_MODEL = "claude-opus-5"


@dataclass
class DiscoveryQuestion:
    """Discovery question with psychology framework."""

    question: str
    category: str  # rapport, problem, impact, status_quo, desired, authority
    psychology: str
    expected_response_type: str


@dataclass
class NeedNarrativeResult:
    """Need creation narrative."""

    narrative: str
    financial_impact: float
    pain_points: List[str]
    urgency_level: float  # 1-10


class DiscoveryQuestionsEngine:
    """Generate contextual discovery questions."""

    QUESTION_HIERARCHY = {
        "rapport": [
            "Cuéntame sobre {company_name} y a qué se dedican.",
            "¿Cuánto tiempo llevas en tu puesto actual?",
            "¿Cuántas personas hay en tu equipo?",
        ],
        "problem": [
            "¿Cuál es tu mayor desafío en este momento?",
            "¿Dónde sientes que se pierde más tiempo o dinero?",
            "¿Qué es lo que más te preocupa de tu negocio?",
        ],
        "impact": [
            "¿Cuánto les cuesta eso al año, más o menos?",
            "¿Qué pasa con tu equipo cuando eso ocurre?",
            "Si esto sigue 12 meses igual, ¿qué pasa con el negocio?",
        ],
        "status_quo": [
            "¿Cómo lo resuelven hoy?",
            "¿Qué soluciones ya probaron?",
            "¿Por qué no terminaron de funcionar?",
        ],
        "desired": [
            "¿Cómo se vería la situación ideal para ti?",
            "Si pudieras cambiar una sola cosa, ¿cuál sería?",
            "¿Qué harías con el tiempo o el dinero que se ahorre?",
        ],
        "authority": [
            "¿Quién más tiene que dar el visto bueno para esta decisión?",
            "¿Cómo es el proceso para decidir algo así?",
            "¿Cuándo podríamos sumar a esa persona a una conversación?",
        ],
    }

    def __init__(self, db: AsyncSession, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    def generate_questions(self, prospect: Dict, deal_stage: str) -> List[DiscoveryQuestion]:
        """Generate discovery questions for prospect."""

        stage_to_hierarchy = {
            "initial_contact": "rapport",
            "discovery": "problem",
            "qualification": "impact",
            "needs_analysis": "status_quo",
            "proposal": "desired",
            "negotiation": "authority",
        }

        hierarchy_type = stage_to_hierarchy.get(deal_stage, "problem")
        company = prospect.get("company_name") or "tu empresa"
        base_questions = [q.format(company_name=company) for q in self.QUESTION_HIERARCHY.get(hierarchy_type, [])]

        if not self.claude:
            return [
                DiscoveryQuestion(
                    question=q,
                    category=hierarchy_type,
                    psychology=self._get_psychology(hierarchy_type),
                    expected_response_type=self._get_response_type(hierarchy_type),
                )
                for q in base_questions
            ]

        # Personalize with Claude
        prompt = f"""
        Genera 3 preguntas de descubrimiento en español para:
        Empresa: {prospect.get('company_name')}
        Industria: {prospect.get('industry')}
        Rol: {prospect.get('role')}
        Etapa: {deal_stage}

        Categoría: {hierarchy_type}

        Preguntas base:
        {json.dumps(base_questions, ensure_ascii=False)}

        Personaliza para este prospecto. Que hable ÉL, no que vendas tú.
        Responde solo un array JSON con los campos: question, psychology, expected_response_type
        """

        try:
            message = self.claude.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            questions_json = json.loads(message.content[0].text)
            return [
                DiscoveryQuestion(
                    question=q["question"],
                    category=hierarchy_type,
                    psychology=q.get("psychology", ""),
                    expected_response_type=q.get("expected_response_type", "open"),
                )
                for q in questions_json
            ]
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return [
                DiscoveryQuestion(
                    question=q,
                    category=hierarchy_type,
                    psychology=self._get_psychology(hierarchy_type),
                    expected_response_type=self._get_response_type(hierarchy_type),
                )
                for q in base_questions
            ]

    async def record_response(self, deal_id: str, question: str, response: str) -> DiscoveryResponse:
        """Record discovery response and analyze."""

        # Extract pain points, needs, urgency
        analysis = self._analyze_response(response)

        db_response = DiscoveryResponse(
            deal_id=deal_id,
            question=question,
            response_text=response,
            pain_points=analysis.get("pain_points", []),
            needs_identified=analysis.get("needs", []),
            urgency_level=analysis.get("urgency", 5),
            sentiment=analysis.get("sentiment", "neutral"),
        )

        self.db.add(db_response)
        # Awaited: the session is async, and an un-awaited commit() never runs, so the row was lost.
        await self.db.commit()

        return db_response

    def _analyze_response(self, response: str) -> Dict[str, Any]:
        """Analyze response for pain points, needs, urgency."""

        pain_points = [response] if PAIN_RX.search(response) else []
        urgency = 8 if TIMELINE_RX.search(response) else 5

        return {
            "pain_points": pain_points,
            "needs": [response[:50]],  # Placeholder
            "urgency": urgency,
            "sentiment": "neutral",
        }

    def _get_psychology(self, hierarchy_type: str) -> str:
        """Get psychology principle for question type."""

        psychology_map = {
            "rapport": "Generar confianza y que se sienta cómodo hablando",
            "problem": "Que identifique él mismo el problema",
            "impact": "Que él mismo cuantifique el costo",
            "status_quo": "Ayudarlo a ver que la solución actual falla",
            "desired": "Que describa la necesidad que se está creando",
            "authority": "Quitar objeciones de decisión antes de la propuesta",
        }
        return psychology_map.get(hierarchy_type, "Construir la conversación")

    def _get_response_type(self, hierarchy_type: str) -> str:
        """Get expected response type."""

        return "open" if hierarchy_type in ["problem", "desired"] else "specific"


class NeedCreationEngine:
    """Create awareness of buyer need through pain amplification."""

    def __init__(self, db: AsyncSession, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    async def create_need_narrative(self, deal_id: str, discovery_responses: List[str]) -> NeedNarrativeResult:
        """Build narrative that creates urgency and need."""

        # Extract pain points
        pain_points = self._extract_pain_points(discovery_responses)
        financial_impact = self._calculate_financial_impact(pain_points)

        if not self.claude:
            narrative = self._get_template_narrative(pain_points, financial_impact)
        else:
            narrative = self._generate_claude_narrative(pain_points, financial_impact)

        # Save to DB
        db_narrative = NeedNarrative(
            deal_id=deal_id,
            narrative=narrative,
            financial_impact_calculated=financial_impact,
            pain_points=pain_points,
        )
        self.db.add(db_narrative)
        await self.db.commit()

        urgency = min(financial_impact / 100000, 10)  # 1-10 scale

        return NeedNarrativeResult(
            narrative=narrative,
            financial_impact=financial_impact,
            pain_points=pain_points,
            urgency_level=urgency,
        )

    def _extract_pain_points(self, responses: List[str]) -> List[str]:
        """Extract pain points from discovery responses."""

        pain_points = [response for response in responses if PAIN_RX.search(response)]

        return pain_points[:3]  # Top 3

    def _calculate_financial_impact(self, pain_points: List[str]) -> float:
        """Yearly cost the prospect named in their own words. 0.0 when they named none."""

        return max((sum(annual_amounts(pain)) for pain in pain_points), default=0.0)

    def _generate_claude_narrative(self, pain_points: List[str], impact: float) -> str:
        """Generate need narrative using Claude."""

        prompt = f"""
        Escribe en español una narrativa que haga ver al comprador que NECESITA actuar:

        Dolores (en sus palabras): {json.dumps(pain_points, ensure_ascii=False)}
        Costo anual que él mencionó: {f"${impact:,.0f}" if impact > 0 else "no lo mencionó"}

        Estructura:
        1. Validar el problema (no está solo)
        2. Cuantificar el costo, solo con sus números
        3. Mostrar la tendencia ("si sigue igual...")
        4. Positionar la esperanza ("sí hay una forma de resolverlo...")

        Tono: conversacional, empático, real. NADA de frases de venta. No inventes cifras ni clientes.
        """

        try:
            message = self.claude.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error generating narrative: {e}")
            return self._get_template_narrative(pain_points, impact)

    def _get_template_narrative(self, pain_points: List[str], impact: float) -> str:
        """Template narrative. It states a cost only when the prospect named one."""

        parts = []
        if pain_points:
            parts.append(f'Lo que describiste: "{pain_points[0]}".')
        else:
            parts.append("Hoy hay un problema que vale la pena resolver.")
        if impact > 0:
            parts.append(f"Según tus propios números, eso equivale a unos ${impact:,.0f} al año.")
        parts.append("Si sigue igual, ese costo no baja solo.")
        return " ".join(parts)


class UrgencyTriggerEngine:
    """Urgency lines backed by facts the business supplies. No facts, no urgency."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_urgency_triggers(self, evidence: Optional[Mapping[str, Any]] = None) -> List[Dict[str, Any]]:
        """Urgency lines the business can back. Nothing is invented: a missing fact drops the line."""

        return urgency_triggers(evidence or {})

    def weave_into_narrative(self, triggers: List[Dict], conversation: str) -> str:
        """Weave urgency into conversation naturally."""

        # Don't say "Limited spots available!" (cringe)
        # DO say "Our next cohort starts April 1st" (natural)

        result = conversation
        for trigger in triggers[:2]:  # Use top 2 triggers
            result += f"\n\n[Punto natural para decirlo: {trigger['messaging']}]"

        return result


class PsychologyObjectionHandler:
    """Handle objections using psychology, not logic."""

    def __init__(self, db: AsyncSession, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    OBJECTION_FRAMEWORKS = {
        "price": {
            "validate": "Entiendo que el presupuesto importa.",
            "reframe": "Comparar el costo de resolverlo con el costo de seguir igual.",
            "question": "¿Cuánto les cuesta hoy no resolverlo?",
        },
        "time": {
            "validate": "Tiene sentido, el tiempo es escaso.",
            "reframe": "Pensar cuánto tiempo devuelve, no solo cuánto pide.",
            "question": "¿Cuánto vale una hora de tu tiempo hoy?",
        },
        "need": {
            "validate": "Está bien no estar convencido todavía.",
            "reframe": "Lo importante es si el problema va a mejorar o a empeorar.",
            "question": "¿Qué pasa en 12 meses si nada cambia?",
        },
        "authority": {
            "validate": "Es buena idea consultarlo con quien decide.",
            "reframe": "Conviene que esa persona vea el problema con tus números.",
            "question": "¿Quién se beneficiaría más si esto se resuelve?",
        },
    }

    def handle_objection(self, objection: str, prospect: Dict) -> str:
        """Generate psychology-based objection response."""

        objection_type = self._classify_objection(objection)
        framework = self.OBJECTION_FRAMEWORKS.get(objection_type, self.OBJECTION_FRAMEWORKS["need"])

        if not self.claude:
            return f"{framework['validate']} {framework['question']}"

        prompt = f"""
        Escribe en español una respuesta con psicología a esta objeción:

        Objeción: "{objection}"
        Tipo: {objection_type}
        Marco: {json.dumps(framework, ensure_ascii=False)}

        La respuesta debe:
        1. Validar (nunca descartar): "{framework['validate']}"
        2. Reencuadrar la perspectiva: "{framework['reframe']}"
        3. Hacer una pregunta: "{framework['question']}"

        Conversacional, no de vendedor. 2-3 frases como máximo. No inventes cifras ni clientes.
        """

        try:
            message = self.claude.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error handling objection: {e}")
            return f"{framework['validate']} {framework['question']}"

    def _classify_objection(self, objection: str) -> str:
        """Classify objection type."""

        return classify_objection(objection)


class AssumptiveCloseEngine:
    """Jordan Belfort's 5-step closing sequence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    CLOSE_SEQUENCE = [
        {
            "step": 1,
            "commitment": "¿Agendamos una llamada de 30 minutos con tu equipo?",
            "psychology": "Un sí pequeño, con poco compromiso",
            "expected": "Sí, ¿cuándo?",
        },
        {
            "step": 2,
            "commitment": "¿Te conviene más el plan anual o el mensual?",
            "psychology": "Elegir asume que va a comprar",
            "expected": "Probablemente anual",
        },
        {
            "step": 3,
            "commitment": "¿Probamos un piloto de 30 días para medir el resultado?",
            "psychology": "Quita riesgo y facilita el compromiso",
            "expected": "Dale, probemos",
        },
        {
            "step": 4,
            "commitment": "¿Te interesa sumar alguna función avanzada desde el inicio?",
            "psychology": "Un upsell pequeño después del compromiso principal",
            "expected": "Quizás más adelante",
        },
        {
            "step": 5,
            "commitment": "Perfecto. Te envío el contrato hoy. ¿Lo revisamos juntos?",
            "psychology": "Impulso + suposición = un sí casi automático",
            "expected": "Sí, mándalo",
        },
    ]

    def get_close(self, step: int) -> str:
        """Get close for current step."""

        if step < len(self.CLOSE_SEQUENCE):
            return self.CLOSE_SEQUENCE[step]["commitment"]

        return "¿Entonces estás listo para avanzar?"

    def get_next_close(self, current_response: str) -> tuple:
        """Get next close based on their response."""

        is_positive = self._is_positive_response(current_response)

        if not is_positive:
            # Handle objection, stay on current step
            return ("objection", current_response)

        # Move to next step
        return ("advance", self.CLOSE_SEQUENCE)

    def _is_positive_response(self, response: str) -> bool:
        """Determine if response is positive."""

        return is_positive_reply(response)
