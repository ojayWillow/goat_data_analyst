"""PatternLearner Worker - Learns patterns from existing code."""

from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from core.logger import get_logger


class PatternLearner:
    """Learns patterns from existing agents."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("PatternLearner")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def learn_patterns(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Learn all patterns from discovered structure."""
        agents = structure.get("agents", {})

        return {
            "agent_pattern": self._learn_agent_pattern(agents),
            "folder_structure_pattern": self._learn_folder_pattern(agents),
            "naming_conventions": self._learn_naming(agents),
            "pattern_confidence": 0.95 if len(agents) >= 5 else 0.7 if len(agents) >= 3 else 0.5,
            "learned_at": datetime.now().isoformat(),
            "total_agents_analyzed": len(agents),
        }

    def _learn_agent_pattern(self, agents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Learn the pattern agents follow."""
        return {
            "agent_structure": {
                "has_init": True,
                "has_main_file": True,
                "has_workers_folder": any(a.get("has_workers") for a in agents.values()),
                "expected_methods": [
                    "__init__",
                    "execute",
                    "validate_input",
                    "process",
                ],
            },
            "expected_methods": [
                "__init__",
                "execute",
                "validate_input",
                "process",
            ],
            "naming_convention": "snake_case",
            "test_naming": "test_{agent_name}.py",
            "discovered_agents": len(agents),
        }

    def _learn_folder_pattern(self, agents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Learn folder structure pattern."""
        with_workers = sum(1 for a in agents.values() if a.get("has_workers"))
        
        return {
            "folder_based_agents": len(agents),
            "with_workers_subfolder": with_workers,
            "average_workers_per_agent": sum(
                a.get("worker_count", 0) for a in agents.values()
            ) / len(agents) if agents else 0,
            "preferred_structure": "folder_with_workers",
        }

    def _learn_naming(self, agents: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Learn naming conventions."""
        return {
            "agents": "snake_case",
            "classes": "PascalCase",
            "functions": "snake_case",
            "constants": "UPPER_SNAKE_CASE",
            "workers": "snake_case",
            "tests": "test_{name}.py",
        }
