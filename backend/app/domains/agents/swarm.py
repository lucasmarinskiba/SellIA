"""Multi-Agent Swarm System for SellIA.

Coordinates multiple agent personas to collaborate on a task through
structured rounds of discussion, critique, and consensus building.
"""

import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.agents.prompts import AGENT_PROMPTS, get_system_prompt
from app.domains.agents.llm_provider import generate_with_fallback
from app.domains.agents.swarm_memory import SwarmSession, SwarmMessage

logger = get_logger(__name__)


SWARM_SYSTEM_PROMPT = """You are participating in a multi-agent expert panel. Your role is: {role}.

YOUR PERSONA:
{persona}

SHARED TASK:
{task}

SHARED CONTEXT:
{context}

PREVIOUS MESSAGES THIS ROUND:
{previous_messages}

DISCUSSION HISTORY:
{history}

INSTRUCTIONS:
- Analyze the task from your role's perspective.
- You may: contribute an idea, critique another agent's point, agree/disagree, or propose a specific action.
- Be concise but substantive (3-5 sentences).
- If you agree with the emerging consensus, say so explicitly.
- If you disagree, explain why and offer an alternative.
- Always think step by step before responding.

Respond with a single valid JSON object and NOTHING else:
{{
  "thought": "Your brief reasoning",
  "message_type": "idea|critic|agreement|disagreement|action",
  "content": "Your actual response text",
  "target_agent": null or "agent-slug" if critiquing
}}
"""


ROLE_TO_PERSONA_MAP: Dict[str, List[str]] = {
    "researcher": ["alex-hormozi", "market-researcher", "data-analyst", "neil-rackham"],
    "copywriter": ["ad-copywriter", "copywriter-pro", "russell-brunson", "ryan-holiday"],
    "closer": ["jordan-belfort", "b2b-closer", "grant-cardone", "ryan-serhant"],
    "objection_handler": ["chris-voss", "objection-crusher", "jordan-belfort", "robert-cialdini"],
    "strategist": ["alex-hormozi", "russell-brunson", "grant-cardone", "steve-jobs"],
}


def _build_agent_prompt(
    agent_slug: str,
    role: str,
    task: str,
    shared_context: Dict[str, Any],
    history: List[Dict[str, Any]],
    previous_messages: List[Dict[str, Any]],
) -> str:
    """Build the swarm prompt for a single agent."""
    persona = AGENT_PROMPTS.get(agent_slug, AGENT_PROMPTS.get("alex-hormozi", ""))

    context_str = json.dumps(shared_context, ensure_ascii=False, indent=2) if shared_context else "No additional context."

    history_lines = []
    for msg in history[-20:]:  # Keep last 20 messages for context window
        history_lines.append(f"[{msg['round']}] {msg['agent_id']} ({msg['role']}): {msg['content']}")
    history_str = "\n".join(history_lines) if history_lines else "No previous messages."

    prev_lines = []
    for msg in previous_messages:
        prev_lines.append(f"{msg['agent_id']} ({msg['role']}): {msg['content']}")
    prev_str = "\n".join(prev_lines) if prev_lines else "No messages yet this round."

    return SWARM_SYSTEM_PROMPT.format(
        role=role,
        persona=persona[:2000],  # Truncate very long personas
        task=task,
        context=context_str,
        previous_messages=prev_str,
        history=history_str,
    )


def _parse_swarm_response(text: str) -> Dict[str, Any]:
    """Parse JSON response from swarm agent."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract from markdown code block
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

    # Try to find JSON between braces
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    # Fallback: treat entire text as content
    return {
        "thought": "Parsed as plain text",
        "message_type": "idea",
        "content": text[:800],
        "target_agent": None,
    }


def _check_consensus(messages: List[Dict[str, Any]]) -> bool:
    """Check if all agents have reached agreement.

    Consensus requires:
    - At least one 'agreement' message type
    - No 'disagreement' messages
    - Or explicit 'consensus reached' in content
    """
    if not messages:
        return False

    has_agreement = False
    for msg in messages:
        mtype = msg.get("message_type", "").lower()
        content = msg.get("content", "").lower()
        if mtype == "disagreement":
            return False
        if mtype == "agreement":
            has_agreement = True
        if "consensus" in content and ("reached" in content or "alcanzado" in content):
            has_agreement = True

    return has_agreement


class SwarmCoordinator:
    """Assigns roles and selects agent personas for swarm tasks."""

    ROLE_DESCRIPTIONS: Dict[str, str] = {
        "researcher": "Gathers information, analyzes data, and provides evidence-based insights.",
        "copywriter": "Crafts compelling messaging, hooks, and persuasive copy.",
        "closer": "Focuses on closing deals, overcoming final resistance, and sealing agreements.",
        "objection_handler": "Anticipates and neutralizes objections before they block the sale.",
        "strategist": "Plans the overall approach, sequences tactics, and aligns the team.",
    }

    def assign_roles(self, task: str) -> List[Dict[str, str]]:
        """Suggest which agents to involve for a given task.

        Returns a list of dicts with keys: role, agent_slug, description.
        """
        task_lower = task.lower()
        selected_roles: List[str] = []

        # Heuristic role selection based on task keywords
        if any(kw in task_lower for kw in ["precio", "price", "cerrar", "close", "deal", "contrato", "contract"]):
            selected_roles.extend(["closer", "objection_handler"])

        if any(kw in task_lower for kw in ["mensaje", "message", "copy", "texto", "text", "email", "anuncio", "ad", "hook"]):
            selected_roles.append("copywriter")

        if any(kw in task_lower for kw in ["estrategia", "strategy", "plan", "enfoque", "approach", "tactica", "tactic"]):
            selected_roles.append("strategist")

        if any(kw in task_lower for kw in ["investigar", "research", "dato", "data", "analisis", "analysis", "mercado", "market"]):
            selected_roles.append("researcher")

        # Default panel if no strong signals
        if not selected_roles:
            selected_roles = ["strategist", "copywriter", "closer"]

        # Deduplicate while preserving order
        seen = set()
        unique_roles = []
        for r in selected_roles:
            if r not in seen:
                seen.add(r)
                unique_roles.append(r)

        # Map roles to available personas
        result = []
        for role in unique_roles:
            candidates = ROLE_TO_PERSONA_MAP.get(role, ["alex-hormozi"])
            # Pick first candidate that exists in AGENT_PROMPTS
            agent_slug = next((s for s in candidates if s in AGENT_PROMPTS), candidates[0])
            result.append({
                "role": role,
                "agent_slug": agent_slug,
                "description": self.ROLE_DESCRIPTIONS.get(role, ""),
            })

        return result


class AgentSwarm:
    """Executes multi-agent collaborative tasks with shared memory and consensus."""

    def __init__(self, db: AsyncSession, business_id: Optional[uuid.UUID] = None):
        self.db = db
        self.business_id = business_id
        self.coordinator = SwarmCoordinator()

    async def execute_swarm(
        self,
        task: str,
        agents: List[str],
        context: Dict[str, Any],
        consensus_required: bool = True,
        max_rounds: int = 5,
    ) -> Dict[str, Any]:
        """Execute a swarm task with the given agents.

        Args:
            task: The task description.
            agents: List of agent slugs to involve.
            context: Shared context dict visible to all agents.
            consensus_required: Whether to stop only when consensus is reached.
            max_rounds: Maximum discussion rounds.

        Returns:
            Dict with final_response, agent_contributions, reasoning, consensus_reached, rounds.
        """
        # Create persistent session
        session = SwarmSession(
            task=task,
            business_id=self.business_id or uuid.uuid4(),
            agents_involved=agents,
            shared_context=context,
            round_count=0,
            consensus_reached=False,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # Assign roles
        role_assignments = self._assign_roles_to_agents(agents)

        shared_memory = dict(context)
        history: List[Dict[str, Any]] = []
        final_response: Optional[str] = None
        consensus_reached = False

        for round_num in range(1, max_rounds + 1):
            session.round_count = round_num
            round_messages: List[Dict[str, Any]] = []

            for agent_slug in agents:
                role = role_assignments.get(agent_slug, "contributor")

                prompt = _build_agent_prompt(
                    agent_slug=agent_slug,
                    role=role,
                    task=task,
                    shared_context=shared_memory,
                    history=history,
                    previous_messages=round_messages,
                )

                messages = [SystemMessage(content=prompt)]

                try:
                    response = await generate_with_fallback(
                        db=self.db,
                        business_id=self.business_id or uuid.uuid4(),
                        messages=messages,
                        model="gpt-4o-mini",
                        temperature=0.7,
                        max_tokens=800,
                        use_semantic_cache=False,
                        use_smart_router=True,
                    )
                    raw_text = response.content if response else "{}"
                except Exception as e:
                    logger.error(f"Swarm LLM call failed for {agent_slug}: {e}")
                    raw_text = "{}"

                parsed = _parse_swarm_response(raw_text)

                msg_record = {
                    "agent_id": agent_slug,
                    "role": role,
                    "content": parsed.get("content", raw_text[:500]),
                    "message_type": parsed.get("message_type", "idea"),
                    "target_agent": parsed.get("target_agent"),
                    "thought": parsed.get("thought", ""),
                    "round": round_num,
                }
                round_messages.append(msg_record)
                history.append(msg_record)

                # Persist message
                db_msg = SwarmMessage(
                    session_id=session.id,
                    agent_id=agent_slug,
                    role=role,
                    content=msg_record["content"],
                    message_type=msg_record["message_type"],
                    round=round_num,
                )
                self.db.add(db_msg)

            await self.db.commit()

            # Update shared memory with round summaries
            shared_memory[f"round_{round_num}_summary"] = [
                {"agent": m["agent_id"], "type": m["message_type"], "content": m["content"]} for m in round_messages
            ]

            # Check consensus
            if consensus_required and _check_consensus(round_messages):
                consensus_reached = True
                # Build final response from the converged ideas
                final_response = self._synthesize_final_response(history, task)
                session.consensus_reached = True
                session.final_response = final_response
                await self.db.commit()
                break

        if not consensus_reached and not final_response:
            # Synthesize best response from history
            final_response = self._synthesize_final_response(history, task)
            session.final_response = final_response
            await self.db.commit()

        return {
            "session_id": str(session.id),
            "final_response": final_response,
            "agent_contributions": history,
            "reasoning": self._build_reasoning(history),
            "consensus_reached": consensus_reached,
            "rounds": round_num if consensus_reached else max_rounds,
            "shared_memory": shared_memory,
        }

    def _assign_roles_to_agents(self, agents: List[str]) -> Dict[str, str]:
        """Map agent slugs to functional roles."""
        assignments: Dict[str, str] = {}
        used_roles: set = set()

        for slug in agents:
            role = None
            for r, candidates in ROLE_TO_PERSONA_MAP.items():
                if slug in candidates:
                    role = r
                    break

            # Fallback: heuristic based on slug keywords
            if not role:
                if any(kw in slug for kw in ["copy", "writer", "creative"]):
                    role = "copywriter"
                elif any(kw in slug for kw in ["close", "closer", "belfort", "cardone", "serhant"]):
                    role = "closer"
                elif any(kw in slug for kw in ["research", "analyst", "data", "rackham"]):
                    role = "researcher"
                elif any(kw in slug for kw in ["objection", "voss", "cialdini"]):
                    role = "objection_handler"
                elif any(kw in slug for kw in ["strateg", "hormozi", "brunson", "jobs"]):
                    role = "strategist"
                else:
                    role = "contributor"

            # Deduplicate roles if possible
            if role in used_roles and role != "contributor":
                role = "contributor"
            used_roles.add(role)
            assignments[slug] = role

        return assignments

    def _synthesize_final_response(self, history: List[Dict[str, Any]], task: str) -> str:
        """Synthesize a final consensus response from agent contributions."""
        # Gather action proposals and key ideas from last round
        last_round = max((m["round"] for m in history), default=1)
        last_messages = [m for m in history if m["round"] == last_round]

        parts: List[str] = []
        parts.append(f"## Swarm Consensus: {task}\n")

        for msg in last_messages:
            if msg["message_type"] == "action":
                parts.append(f"**Proposed Action** ({msg['agent_id']}): {msg['content']}\n")
            elif msg["message_type"] == "idea":
                parts.append(f"**Insight** ({msg['agent_id']}): {msg['content']}\n")
            elif msg["message_type"] == "agreement":
                parts.append(f"**Agreement** ({msg['agent_id']}): {msg['content']}\n")

        if len(parts) == 1:
            # No structured messages found; concatenate all last-round messages
            parts.append("\n".join(f"- {m['agent_id']}: {m['content']}" for m in last_messages))

        return "\n".join(parts)

    def _build_reasoning(self, history: List[Dict[str, Any]]) -> str:
        """Build a reasoning trace from the swarm discussion."""
        lines: List[str] = []
        rounds = sorted(set(m["round"] for m in history))
        for r in rounds:
            lines.append(f"Round {r}:")
            for m in history:
                if m["round"] == r:
                    lines.append(f"  [{m['role']}] {m['agent_id']} ({m['message_type']}): {m['content'][:120]}...")
        return "\n".join(lines)
