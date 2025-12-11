"""RetryErrorRecoveryChecker Worker - Audit @retry_on_error coverage across agents.

Checks:
- Which agents use @retry_on_error decorator on their public methods
- Which agents are missing retry protection
- Coverage percentage across all agents

Key: Complements ErrorIntelligenceChecker to give complete resilience picture
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Set

from core.logger import get_logger


class RetryErrorRecoveryChecker:
    """Audits @retry_on_error coverage across all agents."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("RetryErrorRecoveryChecker")
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.retry_decorator = "retry_on_error"

    def audit_agents(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Audit all agents for @retry_on_error usage."""
        agents = structure.get("agents", {})
        
        with_retry = {}
        without_retry = {}
        partial_retry = {}
        
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            result = self._check_agent_retry(agent_path, agent_name)
            
            if result["has_full_retry"]:
                with_retry[agent_name] = result
            elif result["has_partial_retry"]:
                partial_retry[agent_name] = result
            else:
                without_retry[agent_name] = result
        
        coverage_percentage = (
            len(with_retry) / len(agents) * 100 if agents else 0
        )
        
        return {
            "total_agents": len(agents),
            "with_retry_error_recovery": len(with_retry),
            "without_retry_error_recovery": len(without_retry),
            "partial_retry_error_recovery": len(partial_retry),
            "coverage_percentage": round(coverage_percentage, 2),
            "agents_with_retry": with_retry,
            "agents_without_retry": without_retry,
            "agents_partial_retry": partial_retry,
            "priority_fixes": self._get_priority_fixes(without_retry, partial_retry),
            "status": self._get_status(coverage_percentage),
        }

    def _check_agent_retry(self, agent_path: Path, agent_name: str) -> Dict[str, Any]:
        """Check if agent uses @retry_on_error on public methods."""
        # Find main agent file
        main_file = agent_path / f"{agent_name}.py"
        if not main_file.exists():
            py_files = [f for f in agent_path.glob("*.py") if not f.name.startswith("_")]
            if not py_files:
                return {
                    "agent": agent_name,
                    "has_full_retry": False,
                    "has_partial_retry": False,
                    "reason": "No main file found",
                    "retry_imports": [],
                    "decorated_methods": [],
                    "public_methods_count": 0,
                    "decorated_count": 0,
                }
            main_file = py_files[0]

        retry_imports = self._find_retry_imports(main_file)
        decorated_methods = self._find_decorated_methods(main_file)
        public_methods = self._find_public_methods(main_file)
        
        has_import = len(retry_imports) > 0
        has_decorators = len(decorated_methods) > 0
        all_decorated = len(public_methods) > 0 and len(decorated_methods) >= len(public_methods)
        
        has_full = has_import and all_decorated
        has_partial = has_import and has_decorators and not all_decorated
        
        return {
            "agent": agent_name,
            "has_full_retry": has_full,
            "has_partial_retry": has_partial,
            "main_file": str(main_file),
            "retry_imports": retry_imports,
            "decorated_methods": decorated_methods,
            "public_methods": public_methods,
            "public_methods_count": len(public_methods),
            "decorated_count": len(decorated_methods),
            "coverage": (
                round(len(decorated_methods) / len(public_methods) * 100, 1)
                if public_methods else 0
            ),
            "reason": self._get_reason(has_full, has_partial, has_import, len(decorated_methods), len(public_methods)),
        }

    def _find_retry_imports(self, file_path: Path) -> List[str]:
        """Find @retry_on_error imports in a file."""
        imports = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "error_recovery" in node.module:
                        for alias in node.names:
                            if self.retry_decorator in alias.name:
                                imports.append(f"from {node.module} import {alias.name}")
        except Exception as e:
            self.logger.debug(f"Error parsing {file_path}: {e}")
        
        return imports

    def _find_decorated_methods(self, file_path: Path) -> List[str]:
        """Find methods decorated with @retry_on_error."""
        methods = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if method has @retry_on_error decorator
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name):
                                if self.retry_decorator in decorator.func.id:
                                    methods.append(node.name)
                        elif isinstance(decorator, ast.Name):
                            if self.retry_decorator in decorator.id:
                                methods.append(node.name)
        except Exception as e:
            self.logger.debug(f"Error parsing {file_path}: {e}")
        
        return list(set(methods))  # Remove duplicates

    def _find_public_methods(self, file_path: Path) -> List[str]:
        """Find public methods (excluding private/magic methods)."""
        methods = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            
            in_class = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    in_class = True
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # Exclude private/magic methods and simple getters/setters
                            if not item.name.startswith("_") and item.name not in ["__init__"]:
                                # Only count methods with substantive docstrings (not just getters)
                                if not item.name.startswith("get_") or len(item.name) > 4:
                                    methods.append(item.name)
        except Exception as e:
            self.logger.debug(f"Error parsing {file_path}: {e}")
        
        return list(set(methods))  # Remove duplicates

    def _get_reason(self, has_full: bool, has_partial: bool, has_import: bool, decorated_count: int, public_count: int) -> str:
        """Get human-readable reason for status."""
        if has_full:
            return "✅ @retry_on_error on all public methods"
        elif has_partial:
            return f"🟡 Partial (@retry_on_error on {decorated_count}/{public_count} methods)"
        elif has_import:
            return "⚠️  Imported but not used"
        else:
            return "❌ Missing @retry_on_error"

    def _get_priority_fixes(self, without_retry: Dict, partial_retry: Dict) -> List[Dict[str, Any]]:
        """Get prioritized list of agents needing retry protection."""
        fixes = []
        
        # High priority: no retry at all
        for agent_name, info in without_retry.items():
            fixes.append({
                "agent": agent_name,
                "priority": "CRITICAL",
                "action": "Add @retry_on_error to public methods",
                "methods_to_fix": info.get("public_methods", []),
                "complexity": "Low",
                "effort_hours": 0.25 * len(info.get("public_methods", [])),
                "reason": f"No retry protection ({len(info.get('public_methods', []))} methods)",
            })
        
        # Medium priority: partial retry
        for agent_name, info in partial_retry.items():
            missing = [
                m for m in info.get("public_methods", [])
                if m not in info.get("decorated_methods", [])
            ]
            fixes.append({
                "agent": agent_name,
                "priority": "HIGH",
                "action": "Complete @retry_on_error coverage",
                "methods_to_fix": missing,
                "complexity": "Low",
                "effort_hours": 0.25 * len(missing),
                "reason": f"Partial coverage ({info.get('decorated_count', 0)}/{info.get('public_methods_count', 0)} methods)",
            })
        
        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        fixes.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["agent"]))
        
        return fixes

    def _get_status(self, coverage: float) -> str:
        """Get status based on retry error recovery coverage."""
        if coverage >= 90:
            return "✅ Excellent"
        elif coverage >= 75:
            return "🟢 Good"
        elif coverage >= 50:
            return "🟡 Fair"
        else:
            return "🔴 Critical"
