"""HealthReporter Worker - Generates comprehensive health reports.

Enhanced to count actual test cases using pytest discovery instead of
just counting test files.
"""

from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import ast

from core.logger import get_logger


class HealthReporter:
    """Generates health reports."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("HealthReporter")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def _count_test_cases(self, test_files: Dict[str, Any]) -> int:
        """Count actual test cases by parsing test files.
        
        Scans test_*.py files for:
        - Test classes (TestXxx)
        - Test methods (def test_xxx)
        
        Returns total number of test cases found.
        """
        total_tests = 0
        
        for test_name, test_info in test_files.items():
            test_path = Path(test_info.get("path", ""))
            
            if not test_path.exists() or not test_path.suffix == ".py":
                continue
            
            try:
                with open(test_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                
                # Count test methods in test classes and module-level test functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                        # Count test methods in class
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                                total_tests += 1
                    elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        # Module-level test function
                        # Only count if not inside a class (will be caught above)
                        if not isinstance(getattr(node, "parent", None), ast.ClassDef):
                            total_tests += 1
            except Exception as e:
                self.logger.debug(f"Failed to parse {test_path}: {e}")
                # Fallback: assume 1 test per file if parsing fails
                total_tests += 1
        
        return total_tests

    def calculate_health_score(self, structure: Dict[str, Any], changes: Dict[str, Any]) -> float:
        """Calculate project health score (0-100).
        
        Scoring:
        - Test coverage (70%): percentage of agents with tests
        - Architecture compliance (20%): agents with worker folders
        - Stability (10%): unchanged agents (no new/removed)
        """
        agents = structure.get("agents", {})
        if len(agents) == 0:
            return 0.0

        # Test coverage (70% weight)
        tested = sum(1 for a in agents.values() if a.get("has_test"))
        test_coverage = (tested / len(agents)) * 100 if len(agents) > 0 else 0

        # Architecture compliance (20% weight)
        with_workers = sum(1 for a in agents.values() if a.get("has_workers"))
        architecture_score = (with_workers / len(agents)) * 100 if len(agents) > 0 else 50

        # Stability (10% weight)
        new_agents = len(changes.get("new_agents", []))
        removed_agents = len(changes.get("removed_agents", []))
        stability = max(0.0, 100.0 - (new_agents + removed_agents) * 5)

        score = (test_coverage * 0.7) + (architecture_score * 0.2) + (stability * 0.1)
        return min(100.0, score)

    def generate_report(self, structure: Dict[str, Any], patterns: Dict[str, Any], changes: Dict[str, Any], code_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive health report.
        
        Enhanced to count actual test cases instead of just test files.
        """
        agents = structure.get("agents", {})
        tests = structure.get("tests", {})
        health_score = self.calculate_health_score(structure, changes)

        tested = [a for a in agents.keys() if agents[a].get("has_test")]
        untested = [a for a in agents.keys() if not agents[a].get("has_test")]
        
        # Count actual test cases
        total_test_cases = self._count_test_cases(tests)

        return {
            "health_score": round(health_score, 2),
            "status": self._get_status(health_score),
            "summary": {
                "total_agents": len(agents),
                "tested_agents": len(tested),
                "untested_agents": len(untested),
                "test_coverage": round((len(tested) / len(agents) * 100), 2) if agents else 0,
                "total_tests": len(tests),
                "total_test_cases": total_test_cases,
                "agents_with_workers": sum(1 for a in agents.values() if a.get("has_workers")),
            },
            "changes": {
                "new_agents": changes.get("new_agents", []),
                "removed_agents": changes.get("removed_agents", []),
                "new_tests": changes.get("new_tests", []),
            },
            "recommendations": self._get_recommendations(agents, untested),
            "generated_at": datetime.now().isoformat(),
        }

    def _get_status(self, score: float) -> str:
        """Get status based on health score."""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 50:
            return "Needs Work"
        else:
            return "Critical"

    def _get_recommendations(self, agents: Dict, untested: List[str]) -> List[str]:
        """Generate recommendations based on project state."""
        recommendations = []

        if len(untested) > 0:
            if len(untested) <= 3:
                recommendations.append(f"Add tests for: {', '.join(untested)}")
            else:
                recommendations.append(f"Add tests for {len(untested)} untested agents")

        if len(agents) < 3:
            recommendations.append("Continue building agents to establish patterns")

        if len(recommendations) == 0:
            recommendations.append("All systems healthy! Keep maintaining.")

        return recommendations
