"""ContractValidator Worker - Validate API contracts and data formats between agents.

Checks:
- Method signatures and return types
- Documented input/output contracts
- Data format consistency
- Breaking changes detection
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Tuple

from core.logger import get_logger


class ContractValidator:
    """Validates contracts between agents."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("ContractValidator")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def validate_contracts(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API contracts for all agents."""
        agents = structure.get("agents", {})
        
        contract_results = {}
        issues = []
        
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            contracts = self._extract_agent_contracts(agent_path, agent_name)
            contract_results[agent_name] = contracts
            
            # Check for contract issues
            if not contracts.get("main_class"):
                issues.append({
                    "agent": agent_name,
                    "severity": "HIGH",
                    "issue": "No identifiable main class found",
                })
            
            if not contracts.get("execute_method"):
                issues.append({
                    "agent": agent_name,
                    "severity": "HIGH",
                    "issue": "No execute() method found",
                })
            
            execute_sig = contracts.get("execute_method", {})
            if execute_sig and not execute_sig.get("return_type"):
                issues.append({
                    "agent": agent_name,
                    "severity": "MEDIUM",
                    "issue": "execute() method missing return type annotation",
                })
        
        # Check consistency across agents
        consistency_issues = self._check_consistency(contract_results)
        issues.extend(consistency_issues)
        
        contract_compliance = self._calculate_compliance(contract_results)
        
        return {
            "total_agents": len(agents),
            "agents_with_valid_contracts": len([c for c in contract_results.values() if c.get("valid")]),
            "contract_issues": len(issues),
            "contract_compliance": round(contract_compliance, 2),
            "contract_results": contract_results,
            "issues": issues,
            "priority_fixes": self._get_priority_fixes(issues),
            "status": self._get_status(contract_compliance),
        }

    def _extract_agent_contracts(self, agent_path: Path, agent_name: str) -> Dict[str, Any]:
        """Extract API contract information from agent."""
        main_file = agent_path / f"{agent_name}.py"
        if not main_file.exists():
            py_files = [f for f in agent_path.glob("*.py") if not f.name.startswith("_")]
            if not py_files:
                return {"valid": False, "reason": "No main file found"}
            main_file = py_files[0]
        
        try:
            with open(main_file, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            main_class = self._find_main_class(tree)
            execute_method = self._find_method(tree, "execute") if main_class else None
            
            contracts = {
                "agent": agent_name,
                "file": str(main_file),
                "main_class": main_class,
                "public_methods": self._find_public_methods(tree),
                "execute_method": execute_method,
                "valid": main_class is not None and execute_method is not None,
            }
            
            return contracts
        except Exception as e:
            self.logger.error(f"Failed to extract contracts for {agent_name}: {e}")
            return {"valid": False, "reason": f"Analysis failed: {str(e)}"}

    def _find_main_class(self, tree: ast.AST) -> Dict[str, Any]:
        """Find the main class and its details."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                return {
                    "name": node.name,
                    "has_init": any(isinstance(n, ast.FunctionDef) and n.name == "__init__" for n in node.body),
                    "docstring": ast.get_docstring(node),
                }
        return None

    def _find_method(self, tree: ast.AST, method_name: str) -> Dict[str, Any]:
        """Find a specific method and its signature."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == method_name:
                        return {
                            "name": method_name,
                            "args": [arg.arg for arg in item.args.args if arg.arg != "self"],
                            "return_type": self._get_return_type(item),
                            "docstring": ast.get_docstring(item),
                            "has_type_hints": item.returns is not None,
                        }
        return None

    def _find_public_methods(self, tree: ast.AST) -> List[str]:
        """Find all public methods in classes."""
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                        methods.append(item.name)
        return methods

    def _get_return_type(self, func_node: ast.FunctionDef) -> str:
        """Get return type annotation as string."""
        if func_node.returns:
            if isinstance(func_node.returns, ast.Name):
                return func_node.returns.id
            elif isinstance(func_node.returns, ast.Constant):
                return str(func_node.returns.value)
            else:
                return "Annotated"
        return None

    def _check_consistency(self, contract_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
        """Check consistency of contracts across agents."""
        issues = []
        
        # Check if all agents have execute method
        agents_without_execute = [
            name for name, contracts in contract_results.items()
            if not contracts.get("execute_method")
        ]
        
        if agents_without_execute:
            for agent in agents_without_execute:
                issues.append({
                    "agent": agent,
                    "severity": "HIGH",
                    "issue": "Missing standard execute() method",
                    "impact": "Cannot be used in orchestration",
                })
        
        # Check return type consistency
        execute_return_types = {}
        for name, contracts in contract_results.items():
            if contracts.get("execute_method"):
                ret_type = contracts["execute_method"].get("return_type")
                if ret_type:
                    execute_return_types.setdefault(ret_type, []).append(name)
        
        if len(execute_return_types) > 1:
            issues.append({
                "severity": "MEDIUM",
                "issue": "Inconsistent return types for execute() across agents",
                "details": execute_return_types,
            })
        
        return issues

    def _calculate_compliance(self, contract_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall contract compliance percentage."""
        if not contract_results:
            return 0.0
        
        total = 0.0
        for contracts in contract_results.values():
            score = 0.0
            
            # Has main class (40%)
            if contracts.get("main_class"):
                score += 40
            
            # Has execute method (40%)
            if contracts.get("execute_method"):
                score += 40
                # With type hints (20% bonus)
                if contracts.get("execute_method", {}).get("has_type_hints"):
                    score += 20
            
            # Has docstring (20%)
            if contracts.get("main_class", {}).get("docstring"):
                score += 20
            
            total += min(100, score)
        
        return total / len(contract_results) if contract_results else 0.0

    def _get_priority_fixes(self, issues: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Get prioritized list of contract issues to fix."""
        fixes = []
        
        for issue in issues:
            if issue.get("severity") == "HIGH":
                effort = 2
            elif issue.get("severity") == "MEDIUM":
                effort = 1
            else:
                effort = 0.5
            
            fixes.append({
                "agent": issue.get("agent", "System"),
                "priority": issue.get("severity", "LOW"),
                "issue": issue.get("issue"),
                "impact": issue.get("impact", "Consistency"),
                "effort_hours": effort,
            })
        
        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        fixes.sort(key=lambda x: severity_order.get(x["priority"], 4))
        
        return fixes

    def _get_status(self, compliance: float) -> str:
        """Get status based on contract compliance."""
        if compliance >= 90:
            return "✅ Excellent"
        elif compliance >= 75:
            return "🟡 Good"
        elif compliance >= 60:
            return "🟠 Fair"
        else:
            return "🔴 Critical"
