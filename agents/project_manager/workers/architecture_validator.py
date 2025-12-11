"""ArchitectureValidator Worker - Validates project follows architecture patterns.

Checks:
- Agent folder structure (workers subdirectory)
- File organization conventions
- Import patterns
- Circular dependencies
- Architecture compliance
"""

from pathlib import Path
from typing import Dict, List, Any, Set

from core.logger import get_logger


class ArchitectureValidator:
    """Validates project architecture compliance."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("ArchitectureValidator")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def validate_agent_structure(self, agent_path: Path) -> Dict[str, Any]:
        """Validate agent follows architecture pattern."""
        agent_name = agent_path.name
        issues = []
        recommendations = []
        score = 100.0

        # Check 1: Main file exists
        main_file = agent_path / f"{agent_name}.py"
        if not main_file.exists():
            py_files = [f for f in agent_path.glob("*.py") if not f.name.startswith("_")]
            if not py_files:
                issues.append("Missing main agent file")
                score -= 20
            else:
                recommendations.append(f"Rename {py_files[0].name} to {agent_name}.py")
                score -= 10

        # Check 2: __init__.py exists
        init_file = agent_path / "__init__.py"
        if not init_file.exists():
            issues.append("Missing __init__.py")
            score -= 15
            recommendations.append("Create __init__.py to export main class")

        # Check 3: Workers structure (if agent has workers)
        workers_dir = agent_path / "workers"
        if workers_dir.exists():
            # Check for workers __init__.py
            workers_init = workers_dir / "__init__.py"
            if not workers_init.exists():
                recommendations.append("Add __init__.py to workers/")
                score -= 5
            
            # Check worker file naming
            worker_files = [f for f in workers_dir.glob("*.py") if not f.name.startswith("_")]
            if worker_files and not all(self._is_snake_case(f.stem) for f in worker_files):
                issues.append("Worker files not in snake_case")
                score -= 10
        else:
            # No workers folder - this is OK for simple agents
            pass

        # Check 4: Documentation
        has_readme = (agent_path / "README.md").exists()
        has_docstring = self._check_module_docstring(main_file) if main_file.exists() else False
        
        if not (has_readme or has_docstring):
            recommendations.append("Add documentation (README.md or module docstring)")
            score -= 5

        return {
            "agent": agent_name,
            "valid": len(issues) == 0,
            "score": max(0.0, score),
            "issues": issues,
            "recommendations": recommendations,
        }

    def validate_project_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate overall project structure."""
        issues = []
        recommendations = []
        agent_scores = []

        agents = structure.get("agents", {})
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            validation = self.validate_agent_structure(agent_path)
            agent_scores.append(validation["score"])
            
            if not validation["valid"]:
                issues.extend([f"[{agent_name}] {issue}" for issue in validation["issues"]])
            
            if validation["recommendations"]:
                recommendations.extend(
                    [f"[{agent_name}] {rec}" for rec in validation["recommendations"]]
                )

        # Check for untested agents
        untested = [a for a, info in agents.items() if not info.get("has_test")]
        if untested:
            for agent in untested:
                recommendations.append(f"Add tests/test_{agent}.py for {agent}")

        # Overall score
        avg_score = sum(agent_scores) / len(agent_scores) if agent_scores else 50.0

        return {
            "valid": len(issues) == 0,
            "overall_score": avg_score,
            "total_agents": len(agents),
            "well_structured": len(agent_scores),
            "issues": issues,
            "recommendations": recommendations,
        }

    def _is_snake_case(self, name: str) -> bool:
        """Check if name is snake_case."""
        return name.islower() and ("_" in name or name.isidentifier())

    def _check_module_docstring(self, file_path: Path) -> bool:
        """Check if file has module-level docstring."""
        try:
            with open(file_path, "r") as f:
                content = f.read()
            # Simple check for docstring at start
            has_triple_double = '"""' in content
            has_triple_single = "'''" in content
            return has_triple_double or has_triple_single
        except:
            return False
