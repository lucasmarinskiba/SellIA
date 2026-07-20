"""
Improvement Generator

Usa LLM para analizar el System Health Report y generar propuestas de mejora
concretas para el sistema.
"""

import uuid
import json
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.intelligence.system_analyzer import SystemHealthReport
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.feedback.models import SystemImprovement
from app.core.logger import get_logger

logger = get_logger(__name__)


async def generate_improvements(
    db: AsyncSession,
    report: SystemHealthReport,
    business_id: uuid.UUID,
) -> List[SystemImprovement]:
    """
    Genera propuestas de mejora basadas en el health report.

    Returns:
        Lista de SystemImprovement creados en la BD.
    """
    system_prompt = """You are a Senior Software Architect AI responsible for improving a SaaS platform.
Analyze the system health report and generate improvement proposals.

Respond with ONLY a JSON array of objects:
[
  {
    "title": "Short title",
    "description": "Detailed description of the problem and solution",
    "affected_modules": ["auth", "api", "frontend"],
    "difficulty": "easy|medium|hard",
    "estimated_hours": number,
    "target_plan": "free|starter|pro|enterprise",
    "implementation_details": "Specific code/config changes suggested"
  }
]

Rules:
- Generate 2-4 concrete improvements
- Target plan: free (bugfixes/security), starter (small UX), pro (features), enterprise (custom/advanced)
- Be specific: mention exact endpoints, components, or configurations
- Consider user feedback themes from the report
- Respond ONLY with valid JSON array, no markdown."""

    user_prompt = f"""System Health Report:
{json.dumps(report.to_dict(), indent=2, default=str)}

Generate improvement proposals based on this data."""

    try:
        response = await generate_raw_ai_response(
            db=db,
            business_id=business_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1500,
            temperature=0.3,
        )
        if not response:
            return []

        proposals = json.loads(response.strip())
        if not isinstance(proposals, list):
            proposals = [proposals]

        improvements = []
        for p in proposals:
            improvement = SystemImprovement(
                title=p.get("title", "Untitled Improvement"),
                description=p.get("description", ""),
                affected_modules=p.get("affected_modules", []),
                implementation_details=p.get("implementation_details", ""),
                difficulty=p.get("difficulty", "medium"),
                estimated_hours=p.get("estimated_hours"),
                target_plan=p.get("target_plan", "starter"),
                status="proposed",
                source_health_report_id=report.id,
            )
            db.add(improvement)
            improvements.append(improvement)

        await db.commit()
        for imp in improvements:
            await db.refresh(imp)

        logger.info(f"Generated {len(improvements)} system improvements from health report")
        return improvements

    except Exception as e:
        logger.error(f"Failed to generate improvements: {e}")
        return []


async def create_feature_flag_for_improvement(
    db: AsyncSession,
    improvement: SystemImprovement,
) -> Optional[str]:
    """
    Crea un feature flag para una mejora aprobada.

    Returns:
        Nombre del feature flag creado.
    """
    from app.domains.feedback.models import FeatureFlag

    flag_name = f"improvement_{improvement.id.hex[:8]}"

    flag = FeatureFlag(
        name=flag_name,
        description=improvement.title,
        enabled_plans=[improvement.target_plan],
        rollout_percentage=10,  # Start with 10%
        created_by_improvement_id=improvement.id,
    )
    db.add(flag)
    await db.commit()
    await db.refresh(flag)

    improvement.feature_flag_name = flag_name
    improvement.status = "in_progress"
    await db.commit()

    logger.info(f"Created feature flag {flag_name} for improvement {improvement.id}")
    return flag_name
