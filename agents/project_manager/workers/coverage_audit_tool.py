"""Coverage Audit Tool - Audit Retry Error Recovery & Error Intelligence Coverage.

Scans all agents and their workers to identify:
1. Which agents are NOT covered with @retry_on_error
2. Which agent workers are NOT integrated with Error Intelligence
3. Provides detailed reports with exact methods needing coverage
4. Generates actionable remediation steps

Usage:
    tool = CoverageAuditTool(logger)
    
    # Audit retry coverage
    retry_report = tool.audit_retry_coverage(structure)
    print(retry_report['summary'])
    
    # Audit error intelligence coverage
    ei_report = tool.audit_error_intelligence_coverage(structure)
    print(ei_report['summary'])
    
    # Combined audit
    combined = tool.audit_combined(structure)
    tool.print_audit_report(combined)
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict


class CoverageAuditTool:
    """Audit tool for retry error recovery and error intelligence coverage."""

    def __init__(self, logger):
        self.logger = logger
        self.project_root = Path(__file__).parent.parent.parent.parent

    def audit_retry_coverage(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Audit @retry_on_error coverage across all agents.
        
        Returns:
            Dict with:
            - coverage_percentage: float (0-100)
            - total_agents: int
            - covered_agents: int
            - uncovered_agents: List[str]
            - agents_detail: Dict[agent_name -> coverage_info]
            - missing_methods: Dict[agent_name -> methods_list]
            - summary: str (human-readable)
        """
        agents = structure.get("agents", {})
        covered = 0
        uncovered_agents = []
        agents_detail = {}
        missing_methods = {}

        for agent_name, agent_info in agents.items():
            agent_path = Path(agent_info["path"])
            
            # Check agent main file
            main_file = agent_path / f"{agent_name}.py"
            if not main_file.exists():
                # Try alternative naming
                py_files = list(agent_path.glob("*.py"))
                main_file = next((f for f in py_files if f.name != "__init__.py"), None)
            
            if not main_file:
                uncovered_agents.append(agent_name)
                agents_detail[agent_name] = {
                    "covered": False,
                    "percentage": 0,
                    "reason": "No main file found"
                }
                continue
            
            # Check for @retry_on_error in main file
            retry_count, total_methods = self._count_retry_decorators(main_file)
            workers_retry = {}
            
            # Check workers if they exist
            if agent_info.get("has_workers"):
                workers_dir = agent_path / "workers"
                if workers_dir.exists():
                    for worker_file in workers_dir.glob("*.py"):
                        if worker_file.name != "__init__.py":
                            w_retry, w_total = self._count_retry_decorators(worker_file)
                            worker_name = worker_file.stem
                            workers_retry[worker_name] = {
                                "retry_count": w_retry,
                                "total_methods": w_total,
                                "percentage": (w_retry / w_total * 100) if w_total > 0 else 0
                            }
            
            has_coverage = retry_count > 0 or any(w["retry_count"] > 0 for w in workers_retry.values())
            
            if has_coverage:
                covered += 1
                agents_detail[agent_name] = {
                    "covered": True,
                    "percentage": (retry_count / total_methods * 100) if total_methods > 0 else 0,
                    "main_file_retry_count": retry_count,
                    "main_file_total_methods": total_methods,
                    "workers_retry": workers_retry
                }
            else:
                uncovered_agents.append(agent_name)
                agents_detail[agent_name] = {
                    "covered": False,
                    "percentage": 0,
                    "main_file_total_methods": total_methods,
                    "workers_count": len(workers_retry)
                }
                missing_methods[agent_name] = self._extract_public_methods(main_file)
        
        coverage_pct = (covered / len(agents) * 100) if agents else 0
        status = self._get_coverage_status(coverage_pct)
        
        summary = f"""RETRY ERROR RECOVERY COVERAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Coverage: {coverage_pct:.2f}% ({covered}/{len(agents)} agents)
Status: {status}

Covered Agents: {covered}
Uncovered Agents: {len(uncovered_agents)}

Uncovered List:
{chr(10).join(f"  • {a}" for a in uncovered_agents) if uncovered_agents else "  (None)"}"""
        
        return {
            "coverage_percentage": coverage_pct,
            "total_agents": len(agents),
            "covered_agents": covered,
            "uncovered_agents": uncovered_agents,
            "agents_detail": agents_detail,
            "missing_methods": missing_methods,
            "summary": summary,
            "status": status
        }

    def audit_error_intelligence_coverage(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Audit Error Intelligence coverage across all agents.
        
        Returns:
            Dict with:
            - coverage_percentage: float (0-100)
            - total_agents: int
            - covered_agents: int
            - uncovered_agents: List[str]
            - agents_detail: Dict[agent_name -> coverage_info]
            - missing_integrations: Dict[agent_name -> workers_needing_ei]
            - summary: str (human-readable)
        """
        agents = structure.get("agents", {})
        covered = 0
        uncovered_agents = []
        agents_detail = {}
        missing_integrations = {}

        for agent_name, agent_info in agents.items():
            agent_path = Path(agent_info["path"])
            
            # Check main file
            main_file = agent_path / f"{agent_name}.py"
            if not main_file.exists():
                py_files = list(agent_path.glob("*.py"))
                main_file = next((f for f in py_files if f.name != "__init__.py"), None)
            
            if not main_file:
                uncovered_agents.append(agent_name)
                agents_detail[agent_name] = {
                    "covered": False,
                    "percentage": 0,
                    "reason": "No main file found"
                }
                continue
            
            # Check for Error Intelligence integration
            ei_present = self._check_error_intelligence_integration(main_file)
            workers_ei = {}
            missing_workers = []
            
            # Check workers
            if agent_info.get("has_workers"):
                workers_dir = agent_path / "workers"
                if workers_dir.exists():
                    for worker_file in workers_dir.glob("*.py"):
                        if worker_file.name != "__init__.py":
                            has_ei = self._check_error_intelligence_integration(worker_file)
                            worker_name = worker_file.stem
                            if has_ei:
                                workers_ei[worker_name] = True
                            else:
                                missing_workers.append(worker_name)
            
            has_coverage = ei_present or len(workers_ei) > 0
            
            if has_coverage:
                covered += 1
                agents_detail[agent_name] = {
                    "covered": True,
                    "main_file_has_ei": ei_present,
                    "workers_with_ei": list(workers_ei.keys()),
                    "workers_without_ei": missing_workers
                }
            else:
                uncovered_agents.append(agent_name)
                agents_detail[agent_name] = {
                    "covered": False,
                    "main_file_has_ei": ei_present,
                    "workers_without_ei": missing_workers
                }
                if agent_info.get("has_workers"):
                    missing_integrations[agent_name] = missing_workers
        
        coverage_pct = (covered / len(agents) * 100) if agents else 0
        status = self._get_coverage_status(coverage_pct)
        
        summary = f"""ERROR INTELLIGENCE COVERAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Coverage: {coverage_pct:.2f}% ({covered}/{len(agents)} agents)
Status: {status}

Covered Agents: {covered}
Uncovered Agents: {len(uncovered_agents)}

Uncovered List:
{chr(10).join(f"  • {a}" for a in uncovered_agents) if uncovered_agents else "  (None)"}

Missing Worker Integrations:
{self._format_missing_integrations(missing_integrations)}"""
        
        return {
            "coverage_percentage": coverage_pct,
            "total_agents": len(agents),
            "covered_agents": covered,
            "uncovered_agents": uncovered_agents,
            "agents_detail": agents_detail,
            "missing_integrations": missing_integrations,
            "summary": summary,
            "status": status
        }

    def audit_combined(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Run both audits and combine results."""
        retry_audit = self.audit_retry_coverage(structure)
        ei_audit = self.audit_error_intelligence_coverage(structure)
        
        # Calculate combined health score
        combined_score = (retry_audit["coverage_percentage"] + ei_audit["coverage_percentage"]) / 2
        
        # Identify critical gaps (agents missing BOTH)
        critical_gaps = set(retry_audit["uncovered_agents"]) & set(ei_audit["uncovered_agents"])
        
        return {
            "retry_audit": retry_audit,
            "ei_audit": ei_audit,
            "combined_coverage": combined_score,
            "critical_gaps": list(critical_gaps),
            "remediation_plan": self._generate_remediation_plan(
                retry_audit["uncovered_agents"],
                ei_audit["uncovered_agents"],
                critical_gaps
            )
        }

    def print_audit_report(self, audit_result: Dict[str, Any]) -> None:
        """Print formatted audit report to console."""
        print("\n" + "="*70)
        print("COVERAGE AUDIT REPORT")
        print("="*70)
        
        # Retry coverage
        print("\n" + audit_result["retry_audit"]["summary"])
        
        # Error Intelligence coverage
        print("\n" + audit_result["ei_audit"]["summary"])
        
        # Combined score
        print(f"\nCOMBINED COVERAGE SCORE: {audit_result['combined_coverage']:.2f}%")
        
        # Critical gaps
        if audit_result["critical_gaps"]:
            print(f"\n🔴 CRITICAL GAPS (Missing BOTH Retry & EI):")
            for agent in audit_result["critical_gaps"]:
                print(f"   • {agent}")
        
        # Remediation plan
        print("\n" + "="*70)
        print("REMEDIATION PLAN")
        print("="*70)
        print(audit_result["remediation_plan"])
        
        print("\n" + "="*70 + "\n")

    def export_audit_json(self, audit_result: Dict[str, Any], output_path: Path) -> None:
        """Export audit results to JSON file."""
        with open(output_path, "w") as f:
            # Remove summary strings for cleaner JSON
            clean_result = {k: v for k, v in audit_result.items() if k != "remediation_plan"}
            json.dump(clean_result, f, indent=2)
        self.logger.info(f"Audit results exported to {output_path}")

    # Private helpers

    def _count_retry_decorators(self, file_path: Path) -> Tuple[int, int]:
        """Count @retry_on_error decorated methods in file.
        
        Returns: (retry_count, total_public_methods)
        """
        try:
            with open(file_path, "r") as f:
                tree = ast.parse(f.read())
        except Exception as e:
            self.logger.warning(f"Failed to parse {file_path}: {e}")
            return 0, 0
        
        retry_count = 0
        total_methods = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count public methods (not starting with _)
                if not node.name.startswith("_"):
                    total_methods += 1
                    
                    # Check for @retry_on_error decorator
                    for decorator in node.decorator_list:
                        decorator_name = self._get_decorator_name(decorator)
                        if "retry_on_error" in decorator_name or "retry" in decorator_name:
                            retry_count += 1
                            break
        
        return retry_count, total_methods

    def _check_error_intelligence_integration(self, file_path: Path) -> bool:
        """Check if Error Intelligence is integrated in file.
        
        Returns: True if ErrorIntelligence is used
        """
        try:
            with open(file_path, "r") as f:
                content = f.read()
        except Exception as e:
            self.logger.warning(f"Failed to read {file_path}: {e}")
            return False
        
        # Check for various error intelligence patterns
        patterns = [
            "ErrorIntelligence",
            "error_intelligence",
            "self.error_intelligence",
            "track_success",
            "track_error",
            "from agents.error_intelligence"
        ]
        
        return any(pattern in content for pattern in patterns)

    def _extract_public_methods(self, file_path: Path) -> List[str]:
        """Extract list of public methods from file."""
        try:
            with open(file_path, "r") as f:
                tree = ast.parse(f.read())
        except Exception as e:
            self.logger.warning(f"Failed to parse {file_path}: {e}")
            return []
        
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith("_"):
                    methods.append(node.name)
        
        return methods

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return ""

    def _get_coverage_status(self, percentage: float) -> str:
        """Get status emoji and text based on coverage percentage."""
        if percentage >= 90:
            return "🟢 Excellent"
        elif percentage >= 75:
            return "🟢 Good"
        elif percentage >= 50:
            return "🟡 Fair"
        elif percentage >= 25:
            return "🟠 Poor"
        else:
            return "🔴 Critical"

    def _format_missing_integrations(self, missing: Dict[str, List[str]]) -> str:
        """Format missing integrations for display."""
        if not missing:
            return "  (None)"
        
        lines = []
        for agent, workers in missing.items():
            lines.append(f"  {agent}:")
            for worker in workers:
                lines.append(f"    • {worker}")
        return "\n".join(lines)

    def _generate_remediation_plan(self, retry_uncovered: List[str], 
                                   ei_uncovered: List[str],
                                   critical_gaps: Set[str]) -> str:
        """Generate actionable remediation plan."""
        lines = []
        
        if critical_gaps:
            lines.append("🔴 PHASE 1: Critical (Both Missing)")
            lines.append("-" * 40)
            for agent in critical_gaps:
                lines.append(f"  {agent}:")
                lines.append(f"    1. Add @retry_on_error to public methods")
                lines.append(f"    2. Integrate ErrorIntelligence")
                lines.append(f"    3. Test both integrations")
            lines.append("")
        
        retry_only = set(retry_uncovered) - critical_gaps
        if retry_only:
            lines.append("🟡 PHASE 2: Retry Only (Missing)")
            lines.append("-" * 40)
            for agent in retry_only:
                lines.append(f"  {agent}: Add @retry_on_error decorator")
            lines.append("")
        
        ei_only = set(ei_uncovered) - critical_gaps
        if ei_only:
            lines.append("🟡 PHASE 3: Error Intelligence Only (Missing)")
            lines.append("-" * 40)
            for agent in ei_only:
                lines.append(f"  {agent}: Integrate ErrorIntelligence")
            lines.append("")
        
        if not (critical_gaps or retry_only or ei_only):
            lines.append("✅ All agents have full coverage!")
        
        return "\n".join(lines)
