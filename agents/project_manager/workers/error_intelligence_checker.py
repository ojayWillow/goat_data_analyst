"""ErrorIntelligenceChecker Worker - Audit Error Intelligence coverage across agents.

Checks:
- Which agents have Error Intelligence integration
- Which agents are missing Error Intelligence
- Error Intelligence initialization patterns
- Error tracking coverage
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Set

from core.logger import get_logger


class ErrorIntelligenceChecker:
    """Audits Error Intelligence coverage across all agents."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("ErrorIntelligenceChecker")
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.ei_module = "error_intelligence"
        self.ei_class = "ErrorIntelligence"

    def audit_agents(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Audit all agents for Error Intelligence integration."""
        agents = structure.get("agents", {})
        
        with_ei = {}
        without_ei = {}
        partial_ei = {}
        
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            result = self._check_agent_ei(agent_path, agent_name)
            
            if result["has_ei"]:
                with_ei[agent_name] = result
            elif result["has_partial"]:
                partial_ei[agent_name] = result
            else:
                without_ei[agent_name] = result
        
        coverage_percentage = (
            len(with_ei) / len(agents) * 100 if agents else 0
        )
        
        return {
            "total_agents": len(agents),
            "with_error_intelligence": len(with_ei),
            "without_error_intelligence": len(without_ei),
            "partial_error_intelligence": len(partial_ei),
            "coverage_percentage": round(coverage_percentage, 2),
            "agents_with_ei": with_ei,
            "agents_without_ei": without_ei,
            "agents_partial_ei": partial_ei,
            "priority_fixes": self._get_priority_fixes(without_ei, partial_ei),
            "status": self._get_status(coverage_percentage),
        }

    def _check_agent_ei(self, agent_path: Path, agent_name: str) -> Dict[str, Any]:
        """Check if agent has Error Intelligence integration."""
        main_file = agent_path / f"{agent_name}.py"
        if not main_file.exists():
            py_files = [f for f in agent_path.glob("*.py") if not f.name.startswith("_")]
            if not py_files:
                return {
                    "agent": agent_name,
                    "has_ei": False,
                    "has_partial": False,
                    "reason": "No main file found",
                    "ei_imports": [],
                    "ei_usage": [],
                }
            main_file = py_files[0]

        try:
            with open(main_file, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            ei_imports = self._find_ei_imports(tree)
            ei_usage = self._find_ei_usage(tree)
            
            has_ei = len(ei_imports) > 0 and len(ei_usage) > 0
            has_partial = len(ei_imports) > 0 and len(ei_usage) == 0
            
            return {
                "agent": agent_name,
                "has_ei": has_ei,
                "has_partial": has_partial,
                "file": str(main_file),
                "ei_imports": ei_imports,
                "ei_usage": ei_usage,
                "usage_count": len(ei_usage),
                "reason": self._get_reason(has_ei, has_partial, ei_imports, ei_usage),
            }
        except Exception as e:
            self.logger.error(f"Failed to check {agent_name}: {e}")
            return {
                "agent": agent_name,
                "has_ei": False,
                "has_partial": False,
                "reason": f"Analysis failed: {str(e)}",
                "ei_imports": [],
                "ei_usage": [],
            }

    def _find_ei_imports(self, tree: ast.AST) -> List[str]:
        """Find ErrorIntelligence imports in AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "error_intelligence" in node.module:
                    for alias in node.names:
                        if self.ei_class in alias.name:
                            imports.append(f"from {node.module} import {alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "error_intelligence" in alias.name:
                        imports.append(f"import {alias.name}")
        return imports

    def _find_ei_usage(self, tree: ast.AST) -> List[str]:
        """Find ErrorIntelligence usage in AST."""
        usage = []
        for node in ast.walk(tree):
            # Check for instantiation: ErrorIntelligence()
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if self.ei_class in node.func.id:
                        usage.append(f"Instantiation: {node.func.id}()")
            # Check for attribute access: self.error_intelligence.track_error()
            if isinstance(node, ast.Attribute):
                if "error_intelligence" in node.attr:
                    usage.append(f"Usage: error_intelligence.{node.attr}")
        return list(set(usage))

    def _get_reason(self, has_ei: bool, has_partial: bool, imports: List[str], usage: List[str]) -> str:
        """Get human-readable reason for status."""
        if has_ei:
            return "✅ Error Intelligence fully integrated"
        elif has_partial:
            return f"⚠️  Imported but not used ({len(imports)} imports, {len(usage)} usage)"
        elif imports:
            return f"⚠️  Imported but not integrated (1 import, no usage)"
        else:
            return "❌ Error Intelligence not integrated"

    def _get_priority_fixes(self, without_ei: Dict, partial_ei: Dict) -> List[Dict[str, Any]]:
        """Get prioritized list of agents needing Error Intelligence."""
        fixes = []
        
        # High priority: no Error Intelligence at all
        for agent_name, info in without_ei.items():
            fixes.append({
                "agent": agent_name,
                "priority": "HIGH",
                "action": "Add Error Intelligence integration",
                "complexity": "Medium",
                "effort_hours": 1,
                "reason": "No monitoring at all",
            })
        
        # Medium priority: imported but not used
        for agent_name, info in partial_ei.items():
            fixes.append({
                "agent": agent_name,
                "priority": "MEDIUM",
                "action": "Integrate imported Error Intelligence",
                "complexity": "Low",
                "effort_hours": 0.5,
                "reason": f"Imported {len(info.get('ei_imports', []))} times but not used",
            })
        
        # Sort by priority then by agent name
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        fixes.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["agent"]))
        
        return fixes

    def _get_status(self, coverage: float) -> str:
        """Get status based on Error Intelligence coverage."""
        if coverage >= 90:
            return "✅ Excellent"
        elif coverage >= 75:
            return "🟡 Good"
        elif coverage >= 50:
            return "🟠 Fair"
        else:
            return "🔴 Critical"
