"""ErrorHandlingAuditor Worker - Audit error handling patterns across agents.

Checks:
- Which agents have try/except blocks
- Which agents have error recovery logic
- Which agents log errors properly
- Error handling consistency patterns
"""

import ast
from pathlib import Path
from typing import Dict, List, Any

from core.logger import get_logger


class ErrorHandlingAuditor:
    """Audits error handling patterns across all agents."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("ErrorHandlingAuditor")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def audit_agents(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Audit error handling in all agents."""
        agents = structure.get("agents", {})
        
        audit_results = {}
        strong_handlers = []
        weak_handlers = []
        critical_gaps = []
        
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            result = self._audit_agent_error_handling(agent_path, agent_name)
            audit_results[agent_name] = result
            
            if result["score"] >= 80:
                strong_handlers.append(agent_name)
            elif result["score"] >= 50:
                weak_handlers.append(agent_name)
            else:
                critical_gaps.append(agent_name)
        
        avg_score = (
            sum(r["score"] for r in audit_results.values()) / len(audit_results)
            if audit_results else 0
        )
        
        return {
            "total_agents": len(agents),
            "strong_error_handling": len(strong_handlers),
            "weak_error_handling": len(weak_handlers),
            "critical_gaps": len(critical_gaps),
            "average_score": round(avg_score, 2),
            "agents_audit": audit_results,
            "strong_handlers": strong_handlers,
            "weak_handlers": weak_handlers,
            "critical_gaps": critical_gaps,
            "priority_fixes": self._get_priority_fixes(audit_results),
            "status": self._get_status(avg_score),
        }

    def _audit_agent_error_handling(self, agent_path: Path, agent_name: str) -> Dict[str, Any]:
        """Audit error handling in a single agent."""
        main_file = agent_path / f"{agent_name}.py"
        if not main_file.exists():
            py_files = [f for f in agent_path.glob("*.py") if not f.name.startswith("_")]
            if not py_files:
                return self._empty_audit(agent_name, "No main file found")
            main_file = py_files[0]

        try:
            with open(main_file, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            try_excepts = self._count_try_except_blocks(tree)
            error_logs = self._find_error_logging(tree)
            raise_statements = self._find_raise_statements(tree)
            recovery_logic = self._find_recovery_logic(tree)
            total_functions = self._count_functions(tree)
            
            # Calculate coverage
            try_except_coverage = (
                (try_excepts / total_functions * 100) if total_functions > 0 else 0
            )
            logging_coverage = (
                (error_logs / try_excepts * 100) if try_excepts > 0 else 0
            )
            recovery_coverage = (
                (recovery_logic / try_excepts * 100) if try_excepts > 0 else 0
            )
            
            # Weighted score: try/except (40%), logging (35%), recovery (25%)
            score = (
                (try_except_coverage * 0.4) +
                (min(100, logging_coverage) * 0.35) +
                (recovery_coverage * 0.25)
            ) / 100 * 100
            
            return {
                "agent": agent_name,
                "file": str(main_file),
                "try_except_blocks": try_excepts,
                "total_functions": total_functions,
                "try_except_coverage": round(try_except_coverage, 2),
                "error_logging_calls": error_logs,
                "logging_coverage": round(min(100, logging_coverage), 2),
                "raise_statements": raise_statements,
                "recovery_logic_patterns": recovery_logic,
                "recovery_coverage": round(recovery_coverage, 2),
                "score": round(score, 2),
                "issues": self._identify_issues(try_excepts, error_logs, recovery_logic, total_functions),
            }
        except Exception as e:
            self.logger.error(f"Failed to audit {agent_name}: {e}")
            return self._empty_audit(agent_name, f"Analysis failed: {str(e)}")

    def _count_try_except_blocks(self, tree: ast.AST) -> int:
        """Count try/except blocks in AST."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                count += 1
        return count

    def _count_functions(self, tree: ast.AST) -> int:
        """Count total functions (methods and functions)."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                count += 1
        return count

    def _find_error_logging(self, tree: ast.AST) -> int:
        """Find error logging calls (logger.error, print, etc)."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for logger.error() calls
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["error", "exception", "critical"]:
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id in ["logger", "self.logger"]:
                                count += 1
                # Check for raise statements
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["raise"]:
                        count += 1
        return count

    def _find_raise_statements(self, tree: ast.AST) -> int:
        """Find raise statements."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                count += 1
        return count

    def _find_recovery_logic(self, tree: ast.AST) -> int:
        """Find recovery patterns (return, continue, break after except)."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check if except handlers have recovery logic
                for handler in node.handlers:
                    if len(handler.body) > 0:
                        last_stmt = handler.body[-1]
                        # Recovery: return, continue, break, or assignment
                        if isinstance(last_stmt, (ast.Return, ast.Continue, ast.Break)):
                            count += 1
                        elif isinstance(last_stmt, ast.Assign):
                            count += 1
        return count

    def _identify_issues(self, try_except: int, logging: int, recovery: int, functions: int) -> List[str]:
        """Identify specific error handling issues."""
        issues = []
        
        if try_except == 0 and functions > 0:
            issues.append("No try/except blocks found")
        elif try_except > 0 and functions > 0:
            coverage = try_except / functions * 100
            if coverage < 50:
                issues.append(f"Low error handling coverage ({coverage:.0f}%)")
        
        if try_except > 0 and logging == 0:
            issues.append("Error blocks found but no error logging")
        
        if try_except > 0 and recovery == 0:
            issues.append("Error blocks found but no recovery logic")
        
        return issues

    def _get_priority_fixes(self, audit_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get prioritized list of agents needing error handling improvements."""
        fixes = []
        
        for agent_name, result in audit_results.items():
            if result["score"] < 80:
                priority = "HIGH" if result["score"] < 50 else "MEDIUM"
                
                fixes.append({
                    "agent": agent_name,
                    "priority": priority,
                    "current_score": result["score"],
                    "try_except_coverage": result["try_except_coverage"],
                    "logging_coverage": result["logging_coverage"],
                    "recovery_coverage": result["recovery_coverage"],
                    "issues": result["issues"],
                    "action": "Improve error handling patterns",
                    "effort_hours": 2 if priority == "HIGH" else 1,
                })
        
        # Sort by priority and score
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        fixes.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["current_score"]))
        
        return fixes

    def _get_status(self, avg_score: float) -> str:
        """Get status based on average error handling score."""
        if avg_score >= 80:
            return "✅ Excellent"
        elif avg_score >= 60:
            return "🟡 Good"
        elif avg_score >= 40:
            return "🟠 Fair"
        else:
            return "🔴 Critical"

    def _empty_audit(self, agent_name: str, reason: str) -> Dict[str, Any]:
        """Return empty audit result."""
        return {
            "agent": agent_name,
            "try_except_blocks": 0,
            "total_functions": 0,
            "try_except_coverage": 0.0,
            "error_logging_calls": 0,
            "logging_coverage": 0.0,
            "raise_statements": 0,
            "recovery_logic_patterns": 0,
            "recovery_coverage": 0.0,
            "score": 0.0,
            "issues": [reason],
        }
