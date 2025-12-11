"""PatternValidator Worker - Validates new agents match learned patterns."""

from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from core.logger import get_logger


class PatternValidator:
    """Validates agents against learned patterns."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("PatternValidator")

    def validate_agent(self, agent_name: str, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if agent matches learned pattern."""
        issues = []
        
        if not agent_name:
            issues.append("Agent name is empty")
        elif not self._is_snake_case(agent_name):
            issues.append(f"Agent name '{agent_name}' should use snake_case")
        
        return {
            "agent": agent_name,
            "valid": len(issues) == 0,
            "issues": issues,
            "validated_at": datetime.now().isoformat(),
        }

    def _is_snake_case(self, name: str) -> bool:
        """Check if name is snake_case."""
        return name.islower() and ("_" in name or name.isidentifier())
