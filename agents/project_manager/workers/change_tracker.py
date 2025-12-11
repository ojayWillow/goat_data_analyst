"""ChangeTracker Worker - Tracks project changes over time."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set

from core.logger import get_logger


class ChangeTracker:
    """Tracks what changed in the project."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("ChangeTracker")
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.state_file = self.project_root / ".project_state.json"

    def get_current_state(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Get current project state."""
        return {
            "agents": list(structure.get("agents", {}).keys()),
            "tests": list(structure.get("tests", {}).keys()),
            "core_systems": list(structure.get("core_systems", {}).keys()),
            "timestamp": datetime.now().isoformat(),
        }

    def load_previous_state(self) -> Dict[str, Any]:
        """Load previous project state."""
        if not self.state_file.exists():
            return {"agents": [], "tests": [], "core_systems": [], "timestamp": None}

        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"agents": [], "tests": [], "core_systems": [], "timestamp": None}

    def get_changes(self, current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
        """Detect what changed."""
        current_agents = set(current.get("agents", []))
        previous_agents = set(previous.get("agents", []))
        current_tests = set(current.get("tests", []))
        previous_tests = set(previous.get("tests", []))

        return {
            "new_agents": sorted(list(current_agents - previous_agents)),
            "removed_agents": sorted(list(previous_agents - current_agents)),
            "new_tests": sorted(list(current_tests - previous_tests)),
            "removed_tests": sorted(list(previous_tests - current_tests)),
            "unchanged_agents": sorted(list(current_agents & previous_agents)),
            "detected_at": datetime.now().isoformat(),
        }

    def save_state(self, state: Dict[str, Any]) -> bool:
        """Save current state."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            return False
