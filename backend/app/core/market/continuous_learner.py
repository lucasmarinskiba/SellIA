"""Continuous Learner — Watch external agent systems for updates."""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ContinuousLearner:
    """Monitor & learn from Real Estate & Commercial Advisor systems."""

    def __init__(self):
        self.realEstate_repo = "C:\\Users\\Usuario\\Pictures\\Somos paithon labs\\Agente IA - Agente Inmobiliario"
        self.comercial_repo = "C:\\Users\\Usuario\\Pictures\\Somos paithon labs\\Agente IA - Asesor Comercial"
        self.version_file = "backend/app/core/market/.versions.json"
        self.versions = self._load_versions()

    def monitor_external_systems(self) -> Dict[str, Any]:
        """Check for updates in external systems."""
        updates = {
            "realEstate": self._check_realEstate_updates(),
            "comercial": self._check_comercial_updates(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        return updates

    def _check_realEstate_updates(self) -> Dict[str, Any]:
        """Check Real Estate Agent system for new agents/rules."""
        if not os.path.exists(self.realEstate_repo):
            return {"status": "repo_not_found", "version": "0.0.0"}

        try:
            # Get latest commit hash
            result = subprocess.run(
                ["git", "-C", self.realEstate_repo, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            commit_hash = result.stdout.strip()[:8] if result.returncode == 0 else "unknown"

            # Check for new agent definitions
            agents_path = Path(self.realEstate_repo) / "agents"
            new_agents = []
            if agents_path.exists():
                new_agents = [f.stem for f in agents_path.glob("*.py") if f.is_file()]

            # Check for new tools
            tools_path = Path(self.realEstate_repo) / "tools"
            new_tools = []
            if tools_path.exists():
                new_tools = [f.stem for f in tools_path.glob("*.py") if f.is_file()]

            old_version = self.versions.get("realEstate", {}).get("commit", "")
            updated = commit_hash != old_version

            if updated:
                self.versions["realEstate"] = {
                    "commit": commit_hash,
                    "agents": new_agents,
                    "tools": new_tools,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                self._save_versions()
                logger.info(f"Real Estate system updated: {commit_hash}")

            return {
                "status": "ok",
                "commit": commit_hash,
                "updated": updated,
                "agents": new_agents,
                "tools": new_tools,
                "version": f"1.0.{len(new_agents)}",
            }
        except Exception as e:
            logger.error(f"Error checking Real Estate updates: {e}")
            return {"status": "error", "error": str(e)}

    def _check_comercial_updates(self) -> Dict[str, Any]:
        """Check Commercial Advisor system for new agents/rules."""
        if not os.path.exists(self.comercial_repo):
            return {"status": "repo_not_found", "version": "0.0.0"}

        try:
            # Get latest commit hash
            result = subprocess.run(
                ["git", "-C", self.comercial_repo, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            commit_hash = result.stdout.strip()[:8] if result.returncode == 0 else "unknown"

            # Check for specialized agents
            agents_path = Path(self.comercial_repo) / "core" / "agents"
            new_agents = []
            if agents_path.exists():
                new_agents = [f.stem for f in agents_path.glob("*.py") if f.is_file()]

            old_version = self.versions.get("comercial", {}).get("commit", "")
            updated = commit_hash != old_version

            if updated:
                self.versions["comercial"] = {
                    "commit": commit_hash,
                    "agents": new_agents,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                self._save_versions()
                logger.info(f"Commercial Advisor system updated: {commit_hash}")

            return {
                "status": "ok",
                "commit": commit_hash,
                "updated": updated,
                "agents": new_agents,
                "version": f"1.0.{len(new_agents)}",
            }
        except Exception as e:
            logger.error(f"Error checking Commercial Advisor updates: {e}")
            return {"status": "error", "error": str(e)}

    def sync_from_external_systems(self) -> Dict[str, Any]:
        """Sync new agents/tools from external systems."""
        updates = self.monitor_external_systems()

        sync_result = {
            "realEstate_synced": False,
            "comercial_synced": False,
            "new_agents": [],
            "errors": [],
        }

        if updates["realEstate"]["status"] == "ok" and updates["realEstate"]["updated"]:
            try:
                sync_result["realEstate_synced"] = True
                sync_result["new_agents"].extend(
                    [f"realEstate_{a}" for a in updates["realEstate"]["agents"]]
                )
                logger.info("Real Estate agents synced")
            except Exception as e:
                sync_result["errors"].append(f"Real Estate sync failed: {e}")

        if updates["comercial"]["status"] == "ok" and updates["comercial"]["updated"]:
            try:
                sync_result["comercial_synced"] = True
                sync_result["new_agents"].extend(
                    [f"commerce_{a}" for a in updates["comercial"]["agents"]]
                )
                logger.info("Commercial Advisor agents synced")
            except Exception as e:
                sync_result["errors"].append(f"Commercial Advisor sync failed: {e}")

        return sync_result

    def _load_versions(self) -> Dict[str, Any]:
        """Load version tracking file."""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading versions: {e}")
        return {}

    def _save_versions(self) -> None:
        """Save version tracking file."""
        try:
            os.makedirs(os.path.dirname(self.version_file), exist_ok=True)
            with open(self.version_file, "w") as f:
                json.dump(self.versions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving versions: {e}")

    def rollback_to_version(self, system: str, version: str) -> bool:
        """Rollback to previous version."""
        try:
            repo = self.realEstate_repo if system == "realEstate" else self.comercial_repo
            subprocess.run(
                ["git", "-C", repo, "checkout", version],
                timeout=10,
                check=True,
            )
            logger.info(f"Rolled back {system} to {version}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning/sync status."""
        return {
            "versions": self.versions,
            "last_check": datetime.utcnow().isoformat(),
            "realEstate_connected": os.path.exists(self.realEstate_repo),
            "comercial_connected": os.path.exists(self.comercial_repo),
        }
