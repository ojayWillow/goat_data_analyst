"""ContractValidator Worker - Validate API contracts and data formats between agents.

Checks:
- AgentInterface compliance (set_data, get_data, get_summary)
- Method signatures and return types consistency
- Documented input/output contracts
- Data format consistency
- Breaking changes detection
- Standardized response format
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
        
        # Required methods from AgentInterface
        self.required_interface_methods = {'set_data', 'get_data', 'get_summary'}
        
        # Expected return types for common methods
        self.expected_returns = {
            'execute': 'Dict',
            'get_data': 'Optional',
            'get_summary': 'str',
            'analyze': 'Dict',
        }

    def validate_contracts(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API contracts for all agents (UPDATED with real checks)."""
        agents = structure.get("agents", {})
        
        contract_results = {}
        issues = []
        signature_mismatches = []
        return_type_issues = []
        interface_issues = []
        
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            contracts = self._extract_agent_contracts(agent_path, agent_name)
            contract_results[agent_name] = contracts
            
            # 1. Check AgentInterface implementation
            interface_check = self._check_agent_interface(contracts, agent_name)
            if interface_check['issues']:
                interface_issues.extend(interface_check['issues'])
            
            # 2. Check for standard structure
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
            
            # 3. Check return type annotations
            return_issues = self._check_return_types(contracts, agent_name)
            if return_issues:
                return_type_issues.extend(return_issues)
        
        # 4. Check consistency across agents
        consistency_issues = self._check_consistency(contract_results)
        
        # 5. Check method signature mismatches
        signature_issues = self._check_signature_mismatches(contract_results)
        signature_mismatches.extend(signature_issues)
        
        # Combine all issues
        all_issues = issues + interface_issues + return_type_issues + consistency_issues + signature_mismatches
        
        # Calculate compliance
        contract_compliance = self._calculate_compliance(contract_results, all_issues)
        
        return {
            "total_agents": len(agents),
            "agents_with_valid_contracts": len([c for c in contract_results.values() if c.get("valid")]),
            "contract_issues": len(all_issues),
            "contract_compliance": round(contract_compliance, 2),
            "contract_results": contract_results,
            "issues": all_issues,
            "interface_issues": interface_issues,
            "return_type_issues": return_type_issues,
            "signature_mismatches": signature_mismatches,
            "priority_fixes": self._get_priority_fixes(all_issues),
            "status": self._get_status(contract_compliance),
        }

    def _check_agent_interface(self, contracts: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Check if agent implements AgentInterface methods."""
        issues = []
        public_methods = set(contracts.get("public_methods", []))
        
        # Check for required interface methods
        for required_method in self.required_interface_methods:
            if required_method not in public_methods:
                issues.append({
                    "agent": agent_name,
                    "severity": "MEDIUM",
                    "issue": f"Missing AgentInterface method: {required_method}()",
                    "type": "interface_compliance",
                })
        
        return {"issues": issues, "compliant": len(issues) == 0}

    def _check_return_types(self, contracts: Dict[str, Any], agent_name: str) -> List[Dict[str, Any]]:
        """Check return type consistency."""
        issues = []
        
        # Check execute method return type
        execute_method = contracts.get("execute_method", {})
        if execute_method and not execute_method.get("has_type_hints"):
            issues.append({
                "agent": agent_name,
                "severity": "MEDIUM",
                "issue": "execute() method missing return type annotation",
                "type": "return_type",
            })
        
        # Check for common methods with wrong return types
        all_methods = contracts.get("methods", {})
        for method_name, method_info in all_methods.items():
            # correlation_matrix should return Dict, not DataFrame
            if method_name == "correlation_matrix":
                if method_info.get("return_type") == "DataFrame":
                    issues.append({
                        "agent": agent_name,
                        "severity": "HIGH",
                        "issue": f"{method_name}() returns DataFrame but should return Dict",
                        "type": "return_type_mismatch",
                        "fix": "Convert return value to Dict[str, Any]",
                    })
        
        return issues

    def _check_signature_mismatches(self, contract_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for method signature mismatches across agents."""
        issues = []
        
        # Build map of methods by name
        methods_by_name = {}
        for agent_name, contracts in contract_results.items():
            for method_name, method_info in contracts.get("methods", {}).items():
                if method_name not in methods_by_name:
                    methods_by_name[method_name] = []
                methods_by_name[method_name].append((agent_name, method_info))
        
        # Check for conflicting signatures
        for method_name, occurrences in methods_by_name.items():
            if len(occurrences) > 1:
                signatures = []
                agents_with_method = []
                
                for agent_name, method_info in occurrences:
                    sig = {
                        'agent': agent_name,
                        'args': method_info.get('args', []),
                        'return_type': method_info.get('return_type', 'Unknown')
                    }
                    signatures.append(sig)
                    agents_with_method.append(agent_name)
                
                # Check if signatures differ
                first_sig = signatures[0]
                for sig in signatures[1:]:
                    if sig['args'] != first_sig['args'] or sig['return_type'] != first_sig['return_type']:
                        issues.append({
                            "severity": "HIGH",
                            "issue": f"Method {method_name}() has conflicting signatures",
                            "type": "signature_mismatch",
                            "agents": agents_with_method,
                            "signatures": signatures,
                            "impact": "Agents cannot be used interchangeably",
                        })
                        break
        
        return issues

    def _extract_agent_contracts(self, agent_path: Path, agent_name: str) -> Dict[str, Any]:
        """Extract API contract information from agent (UPDATED)."""
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
            
            # Extract ALL public methods with signatures
            all_methods = self._find_all_methods(tree)
            
            # Check AgentInterface inheritance
            implements_interface = self._check_interface_inheritance(tree)
            
            contracts = {
                "agent": agent_name,
                "file": str(main_file),
                "main_class": main_class,
                "public_methods": list(all_methods.keys()),
                "methods": all_methods,  # NEW: Include all method signatures
                "execute_method": execute_method,
                "implements_agent_interface": implements_interface,
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

    def _find_all_methods(self, tree: ast.AST) -> Dict[str, Dict[str, Any]]:
        """Find all public methods with their signatures (NEW)."""
        methods = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                        methods[item.name] = {
                            "name": item.name,
                            "args": [arg.arg for arg in item.args.args if arg.arg != "self"],
                            "return_type": self._get_return_type(item),
                            "has_type_hints": item.returns is not None,
                            "docstring": ast.get_docstring(item),
                        }
        return methods

    def _check_interface_inheritance(self, tree: ast.AST) -> bool:
        """Check if class inherits from AgentInterface."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "AgentInterface":
                        return True
        return False

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
            elif isinstance(func_node.returns, ast.Subscript):
                # Handle Dict[str, Any], List[str], etc.
                if isinstance(func_node.returns.value, ast.Name):
                    return func_node.returns.value.id
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
                    "type": "missing_execute",
                })
        
        # Check return type consistency for execute()
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
                "type": "inconsistent_returns",
            })
        
        return issues

    def _calculate_compliance(self, contract_results: Dict[str, Dict[str, Any]], all_issues: List[Dict]) -> float:
        """Calculate overall contract compliance percentage (UPDATED)."""
        if not contract_results:
            return 0.0
        
        total = 0.0
        issues_by_agent = {}
        for issue in all_issues:
            agent = issue.get('agent')
            if agent:
                issues_by_agent[agent] = issues_by_agent.get(agent, 0) + 1
        
        for agent_name, contracts in contract_results.items():
            score = 100.0  # Start with perfect
            
            # Deduct for missing components
            if not contracts.get("main_class"):
                score -= 20
            if not contracts.get("execute_method"):
                score -= 30
            if not contracts.get("implements_agent_interface"):
                score -= 15
            
            # Deduct for missing type hints
            if contracts.get("execute_method") and not contracts["execute_method"].get("has_type_hints"):
                score -= 10
            
            # Deduct for issues in this agent
            agent_issues = issues_by_agent.get(agent_name, 0)
            score -= agent_issues * 5  # 5 points per issue
            
            total += max(0, score)
        
        return (total / len(contract_results)) if contract_results else 0.0

    def _get_priority_fixes(self, issues: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Get prioritized list of contract issues to fix."""
        fixes = []
        
        for issue in issues:
            severity = issue.get("severity", "LOW")
            if severity == "CRITICAL":
                effort = 3
            elif severity == "HIGH":
                effort = 2
            elif severity == "MEDIUM":
                effort = 1
            else:
                effort = 0.5
            
            fixes.append({
                "agent": issue.get("agent", "System"),
                "priority": severity,
                "issue": issue.get("issue"),
                "type": issue.get("type", "unknown"),
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
