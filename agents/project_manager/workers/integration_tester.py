"""IntegrationTester Worker - Test data flow and integration between agents.

Checks:
- Agent dependencies and data flow
- Import compatibility
- Method signatures that should match
- Orchestrator integration points
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

from core.logger import get_logger


class IntegrationTester:
    """Tests integration between agents."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("IntegrationTester")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def test_integrations(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Test all integration points between agents."""
        agents = structure.get("agents", {})
        
        # Find orchestrator
        orchestrator_info = agents.get("orchestrator")
        if not orchestrator_info:
            return self._no_orchestrator_result(agents)
        
        orchestrator_path = Path(orchestrator_info["path"])
        orchestrator_deps = self._find_agent_dependencies(orchestrator_path, "orchestrator")
        
        integration_results = {}
        broken_integrations = []
        
        for dep_agent in orchestrator_deps:
            if dep_agent not in agents:
                broken_integrations.append({
                    "orchestrator": "orchestrator",
                    "target": dep_agent,
                    "status": "MISSING",
                    "issue": f"Orchestrator imports {dep_agent} but agent doesn't exist",
                })
                continue
            
            target_path = Path(agents[dep_agent]["path"])
            integration_test = self._test_integration_point(
                orchestrator_path,
                target_path,
                "orchestrator",
                dep_agent
            )
            
            integration_results[dep_agent] = integration_test
            
            if not integration_test["status"] == "PASS":
                broken_integrations.append({
                    "orchestrator": "orchestrator",
                    "target": dep_agent,
                    "status": integration_test["status"],
                    "issue": integration_test.get("issue", "Unknown integration issue"),
                })
        
        working_integrations = len(
            [r for r in integration_results.values() if r["status"] == "PASS"]
        )
        total_integrations = len(integration_results)
        
        health_score = (
            (working_integrations / total_integrations * 100)
            if total_integrations > 0 else 0
        )
        
        return {
            "total_integration_points": total_integrations,
            "working_integrations": working_integrations,
            "broken_integrations": len(broken_integrations),
            "health_score": round(health_score, 2),
            "integration_results": integration_results,
            "issues": broken_integrations,
            "priority_fixes": self._get_priority_fixes(broken_integrations),
            "status": self._get_status(health_score),
        }

    def _test_integration_point(self, source_path: Path, target_path: Path, source_name: str, target_name: str) -> Dict[str, Any]:
        """Test integration between two agents."""
        try:
            # Check if target agent can be imported
            target_main = target_path / f"{target_name}.py"
            if not target_main.exists():
                py_files = [f for f in target_path.glob("*.py") if not f.name.startswith("_")]
                if not py_files:
                    return {
                        "source": source_name,
                        "target": target_name,
                        "status": "BROKEN",
                        "issue": f"{target_name} has no main file",
                    }
                target_main = py_files[0]
            
            # Check target has main class
            target_class = self._find_main_class(target_main)
            if not target_class:
                return {
                    "source": source_name,
                    "target": target_name,
                    "status": "WARNING",
                    "issue": f"{target_name} has no identifiable main class",
                }
            
            # Check if target has execute method
            has_execute = self._check_method_exists(target_main, "execute")
            if not has_execute:
                return {
                    "source": source_name,
                    "target": target_name,
                    "status": "WARNING",
                    "issue": f"{target_name} missing standard 'execute' method",
                }
            
            # All checks passed
            return {
                "source": source_name,
                "target": target_name,
                "status": "PASS",
                "target_class": target_class,
                "has_execute_method": True,
                "integration_type": "Class instantiation + execute()",
            }
        except Exception as e:
            self.logger.error(f"Integration test {source_name}->{target_name} failed: {e}")
            return {
                "source": source_name,
                "target": target_name,
                "status": "ERROR",
                "issue": f"Analysis failed: {str(e)}",
            }

    def _find_agent_dependencies(self, agent_path: Path, agent_name: str) -> Set[str]:
        """Find which agents are imported by this agent."""
        main_file = agent_path / f"{agent_name}.py"
        if not main_file.exists():
            py_files = [f for f in agent_path.glob("*.py") if not f.name.startswith("_")]
            if not py_files:
                return set()
            main_file = py_files[0]
        
        deps = set()
        try:
            with open(main_file, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "agents." in node.module:
                        # Extract agent name from "agents.loader" -> "loader"
                        parts = node.module.split(".")
                        if len(parts) >= 2:
                            agent = parts[1]
                            deps.add(agent)
        except Exception as e:
            self.logger.debug(f"Failed to find dependencies for {agent_name}: {e}")
        
        return deps

    def _find_main_class(self, file_path: Path) -> str:
        """Find the main class name in a file."""
        try:
            with open(file_path, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            # Look for classes that aren't private
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    return node.name
        except Exception as e:
            self.logger.debug(f"Failed to find main class in {file_path}: {e}")
        
        return None

    def _check_method_exists(self, file_path: Path, method_name: str) -> bool:
        """Check if a method exists in a file."""
        try:
            with open(file_path, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name == method_name:
                        return True
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name == method_name:
                                return True
        except Exception as e:
            self.logger.debug(f"Failed to check method {method_name}: {e}")
        
        return False

    def _get_priority_fixes(self, issues: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Get prioritized list of integration issues to fix."""
        fixes = []
        
        for issue in issues:
            if issue["status"] == "MISSING":
                priority = "CRITICAL"
                effort = 4
            elif issue["status"] == "BROKEN":
                priority = "HIGH"
                effort = 3
            else:  # WARNING
                priority = "MEDIUM"
                effort = 2
            
            fixes.append({
                "source": issue["orchestrator"],
                "target": issue["target"],
                "priority": priority,
                "issue": issue["issue"],
                "effort_hours": effort,
            })
        
        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        fixes.sort(key=lambda x: priority_order.get(x["priority"], 4))
        
        return fixes

    def _get_status(self, health_score: float) -> str:
        """Get status based on integration health."""
        if health_score >= 90:
            return "✅ Excellent"
        elif health_score >= 75:
            return "🟡 Good"
        elif health_score >= 50:
            return "🟠 Fair"
        else:
            return "🔴 Critical"

    def _no_orchestrator_result(self, agents: Dict) -> Dict[str, Any]:
        """Return result when no orchestrator found."""
        return {
            "total_integration_points": 0,
            "working_integrations": 0,
            "broken_integrations": 0,
            "health_score": 0.0,
            "integration_results": {},
            "issues": [{"status": "ERROR", "issue": "No orchestrator agent found"}],
            "priority_fixes": [],
            "status": "⚠️  Warning - No orchestrator to test",
        }
