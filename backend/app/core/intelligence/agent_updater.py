"""
Agent Updater

Actualiza automáticamente los agentes IA cuando los modelos ML mejoran.
Guarda versiones anteriores para rollback.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.agents.models import AgentPersonality
from app.core.logger import get_logger

logger = get_logger(__name__)


async def check_and_deploy_model_updates(db: AsyncSession) -> Dict[str, Any]:
    """
    Verifica si un modelo ML mejoró significativamente y actualiza los agentes.

    Returns:
        Dict con las actualizaciones realizadas.
    """
    from app.core.intelligence.ml_trainer import get_model_status, MODELS_DIR
    import os

    updates = {"deployed": [], "skipped": []}

    # Check intent classifier
    model_path = f"{MODELS_DIR}/intent_classifier.pkl"
    if os.path.exists(model_path):
        import pickle
        try:
            with open(model_path, "rb") as f:
                data = pickle.load(f)
            new_accuracy = data.get("accuracy", 0.0)
            new_version = data.get("version", "unknown")

            # Get current deployed version
            result = await db.execute(
                select(AgentPersonality).where(AgentPersonality.slug == "captador")
            )
            agent = result.scalar_one_or_none()

            if agent and agent.extra_data:
                current_accuracy = agent.extra_data.get("ml_model_accuracy", 0.0)
                if new_accuracy > current_accuracy + 0.05:  # 5% improvement threshold
                    # Backup current prompt
                    _backup_agent_prompt(agent)

                    # Update agent with new model info
                    if not agent.extra_data:
                        agent.extra_data = {}
                    agent.extra_data["ml_model_version"] = new_version
                    agent.extra_data["ml_model_accuracy"] = new_accuracy
                    agent.extra_data["last_model_update"] = datetime.now(timezone.utc).isoformat()

                    await db.commit()
                    updates["deployed"].append({
                        "agent": agent.slug,
                        "model": "intent_classifier",
                        "old_accuracy": current_accuracy,
                        "new_accuracy": new_accuracy,
                    })
                    logger.info(f"Deployed model update to {agent.slug}: accuracy {current_accuracy:.3f} -> {new_accuracy:.3f}")
                else:
                    updates["skipped"].append({
                        "model": "intent_classifier",
                        "reason": f"Improvement {new_accuracy - current_accuracy:.3f} below threshold",
                    })
        except Exception as e:
            logger.error(f"Failed to deploy model update: {e}")

    return updates


def _backup_agent_prompt(agent: AgentPersonality) -> None:
    """Guarda una copia del prompt actual antes de actualizarlo."""
    import json
    backup_dir = "data/agent_backups"
    os.makedirs(backup_dir, exist_ok=True)

    backup = {
        "agent_id": str(agent.id),
        "slug": agent.slug,
        "description": agent.description,
        "extra_data": agent.extra_data,
        "backed_up_at": datetime.now(timezone.utc).isoformat(),
    }

    filename = f"{backup_dir}/{agent.slug}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(backup, f, indent=2)

    logger.info(f"Backed up agent {agent.slug} to {filename}")
