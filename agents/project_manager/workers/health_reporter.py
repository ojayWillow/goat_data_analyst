"""HealthReporter Worker - Generates comprehensive, HONEST health reports.

V3 Enhancement: Composite health that shows ACTUAL gaps
- Test coverage
- Error Intelligence coverage
- Error handling quality
- Integration health
- Contract compliance
- Dependency consistency

Result: Honest score reflecting ALL aspects, not just testing
"""

from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import ast

from core.logger import get_logger


class HealthReporter:
    """Generates honest, comprehensive health reports."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("HealthReporter")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def _count_test_cases(self, test_files: Dict[str, Any]) -> int:
        """Count actual test cases by parsing test files."""
        total_tests = 0
        
        for test_name, test_info in test_files.items():
            test_path = Path(test_info.get("path", ""))
            
            if not test_path.exists() or not test_path.suffix == ".py":
                continue
            
            try:
                with open(test_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                                total_tests += 1
                    elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        if not isinstance(getattr(node, "parent", None), ast.ClassDef):
                            total_tests += 1
            except Exception as e:
                self.logger.debug(f"Failed to parse {test_path}: {e}")
                total_tests += 1
        
        return total_tests

    def calculate_health_score_legacy(self, structure: Dict[str, Any], changes: Dict[str, Any]) -> float:
        """Legacy health score (test-focused only)."""
        agents = structure.get("agents", {})
        if len(agents) == 0:
            return 0.0

        tested = sum(1 for a in agents.values() if a.get("has_test"))
        test_coverage = (tested / len(agents)) * 100 if len(agents) > 0 else 0

        with_workers = sum(1 for a in agents.values() if a.get("has_workers"))
        architecture_score = (with_workers / len(agents)) * 100 if len(agents) > 0 else 50

        new_agents = len(changes.get("new_agents", []))
        removed_agents = len(changes.get("removed_agents", []))
        stability = max(0.0, 100.0 - (new_agents + removed_agents) * 5)

        score = (test_coverage * 0.7) + (architecture_score * 0.2) + (stability * 0.1)
        return min(100.0, score)

    def calculate_honest_health_score(self, all_results: Dict[str, Any]) -> float:
        """Calculate HONEST composite health score using ALL checks.
        
        Weights:
        - Test Coverage: 20% (we know this is good)
        - Error Intelligence: 20% (CRITICAL - monitoring)
        - Error Handling: 15% (CRITICAL - resilience)
        - Integration: 15% (CRITICAL - system cohesion)
        - Contract Compliance: 15% (IMPORTANT - stability)
        - Dependency Consistency: 10% (IMPORTANT - maintainability)
        - Code Quality: 5% (nice to have)
        """
        
        # Extract scores from all results
        test_cov = all_results.get("health", {}).get("summary", {}).get("test_coverage", 0)
        ei_cov = all_results.get("error_intelligence", {}).get("coverage_percentage", 0)
        error_score = all_results.get("error_handling", {}).get("average_score", 0)
        int_health = all_results.get("integrations", {}).get("health_score", 0)
        contract_comp = all_results.get("contracts", {}).get("contract_compliance", 0)
        dep_consist = all_results.get("dependency_consistency", {}).get("consistency_score", 0)
        
        # Code quality (average of type hints and docstrings)
        code_analysis = all_results.get("code_analysis", {})
        if code_analysis:
            avg_hints = sum(a.get("type_hints_coverage", 0) for a in code_analysis.values()) / len(code_analysis)
            avg_docs = sum(a.get("docstring_coverage", 0) for a in code_analysis.values()) / len(code_analysis)
            code_quality = (avg_hints + avg_docs) / 2
        else:
            code_quality = 0
        
        # Weighted composite score
        honest_score = (
            (test_cov * 0.20) +
            (ei_cov * 0.20) +
            (error_score * 0.15) +
            (int_health * 0.15) +
            (contract_comp * 0.15) +
            (dep_consist * 0.10) +
            (code_quality * 0.05)
        )
        
        return round(honest_score, 2)

    def generate_report(self, structure: Dict[str, Any], patterns: Dict[str, Any], changes: Dict[str, Any], code_analysis: Dict[str, Any] = None, all_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive health report.
        
        NEW: Uses all_results to generate honest composite health score.
        """
        agents = structure.get("agents", {})
        tests = structure.get("tests", {})
        
        # Calculate honest health score if all_results provided
        if all_results:
            health_score = self.calculate_honest_health_score(all_results)
            status = self._get_honest_status(health_score)
        else:
            # Fallback to legacy calculation
            health_score = self.calculate_health_score_legacy(structure, changes)
            status = self._get_legacy_status(health_score)
        
        tested = [a for a in agents.keys() if agents[a].get("has_test")]
        untested = [a for a in agents.keys() if not agents[a].get("has_test")]
        
        total_test_cases = self._count_test_cases(tests)

        return {
            "health_score": round(health_score, 2),
            "status": status,
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
            "recommendations": self._get_recommendations(all_results if all_results else {}),
            "generated_at": datetime.now().isoformat(),
        }

    def _get_honest_status(self, score: float) -> str:
        """Get status based on HONEST composite health score."""
        if score >= 80:
            return "Excellent ✅"
        elif score >= 70:
            return "Good 🟢"
        elif score >= 60:
            return "Fair 🟡"
        elif score >= 50:
            return "Poor 🟠"
        else:
            return "Critical 🔴"

    def _get_legacy_status(self, score: float) -> str:
        """Get status based on legacy test-only score."""
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

    def _get_recommendations(self, all_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on ALL health metrics."""
        recommendations = []
        
        # Error Intelligence
        ei_cov = all_results.get("error_intelligence", {}).get("coverage_percentage", 0)
        if ei_cov < 50:
            ei_without = all_results.get("error_intelligence", {}).get("agents_without_ei", {})
            count = len(ei_without)
            recommendations.append(f"🔴 URGENT: Add Error Intelligence to {count} agents (0% coverage)")
        elif ei_cov < 100:
            recommendations.append(f"🟠 Add Error Intelligence to remaining agents ({ei_cov}% coverage)")
        
        # Error Handling
        error_score = all_results.get("error_handling", {}).get("average_score", 0)
        if error_score < 50:
            gaps = all_results.get("error_handling", {}).get("critical_gaps", [])
            recommendations.append(f"🔴 URGENT: Improve error handling in {len(gaps)} agents (avg {error_score:.0f}/100)")
        elif error_score < 80:
            recommendations.append(f"🟠 Improve error handling across agents (avg {error_score:.0f}/100)")
        
        # Integration
        int_health = all_results.get("integrations", {}).get("health_score", 0)
        if int_health < 50:
            broken = all_results.get("integrations", {}).get("broken_integrations", 0)
            recommendations.append(f"🔴 URGENT: Fix {broken} broken integration points")
        elif int_health < 90:
            recommendations.append(f"🟠 Test and validate integration points ({int_health:.0f}% health)")
        
        # Contracts
        contract_comp = all_results.get("contracts", {}).get("contract_compliance", 0)
        if contract_comp < 75:
            issues = all_results.get("contracts", {}).get("contract_issues", 0)
            recommendations.append(f"🟠 Fix {issues} contract/signature mismatches ({contract_comp:.0f}% compliance)")
        
        # Dependencies
        dep_consist = all_results.get("dependency_consistency", {}).get("consistency_score", 0)
        if dep_consist < 85:
            missing = len(all_results.get("dependency_consistency", {}).get("missing_standard_imports", []))
            recommendations.append(f"🟡 Standardize imports across agents ({missing} missing, {dep_consist:.0f}/100)")
        
        # If everything is good
        if not recommendations:
            recommendations.append("✅ All systems healthy! Continue hardening in Week 2.")
        
        return recommendations

    def get_priority_roadmap(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Week 2+ roadmap based on health metrics."""
        return {
            "phase": "Week 2: Hardening & Consistency",
            "priority_1_critical": self._get_critical_fixes(all_results),
            "priority_2_high": self._get_high_priority_fixes(all_results),
            "priority_3_medium": self._get_medium_priority_fixes(all_results),
            "estimated_total_effort_hours": self._estimate_effort(all_results),
        }

    def _get_critical_fixes(self, all_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get CRITICAL priority fixes."""
        fixes = []
        
        # Error Intelligence
        ei_cov = all_results.get("error_intelligence", {}).get("coverage_percentage", 0)
        if ei_cov < 50:
            fixes.append({
                "issue": "Error Intelligence coverage",
                "current": f"{ei_cov}%",
                "target": "100%",
                "effort_hours": 13,  # 1 hour per agent
                "impact": "Monitoring, observability",
            })
        
        # Error Handling
        error_score = all_results.get("error_handling", {}).get("average_score", 0)
        if error_score < 50:
            fixes.append({
                "issue": "Error handling patterns",
                "current": f"{error_score:.0f}/100",
                "target": "80/100",
                "effort_hours": 12,  # 1-2 hours per agent
                "impact": "Resilience, failure recovery",
            })
        
        return fixes

    def _get_high_priority_fixes(self, all_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get HIGH priority fixes."""
        fixes = []
        
        # Integration
        int_health = all_results.get("integrations", {}).get("health_score", 0)
        if int_health < 90:
            fixes.append({
                "issue": "Integration points",
                "current": f"{int_health:.0f}%",
                "target": "95%",
                "effort_hours": 8,
                "impact": "System cohesion, end-to-end flow",
            })
        
        # Contracts
        contract_comp = all_results.get("contracts", {}).get("contract_compliance", 0)
        if contract_comp < 85:
            fixes.append({
                "issue": "API contracts & signatures",
                "current": f"{contract_comp:.0f}%",
                "target": "95%",
                "effort_hours": 6,
                "impact": "Stability, breaking changes prevention",
            })
        
        return fixes

    def _get_medium_priority_fixes(self, all_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get MEDIUM priority fixes."""
        fixes = []
        
        # Dependency Consistency
        dep_consist = all_results.get("dependency_consistency", {}).get("consistency_score", 0)
        if dep_consist < 90:
            fixes.append({
                "issue": "Import consistency",
                "current": f"{dep_consist:.0f}/100",
                "target": "95/100",
                "effort_hours": 4,
                "impact": "Maintainability, standardization",
            })
        
        return fixes

    def _estimate_effort(self, all_results: Dict[str, Any]) -> float:
        """Estimate total effort hours needed."""
        total = 0
        total += len(self._get_critical_fixes(all_results)) * 13
        total += len(self._get_high_priority_fixes(all_results)) * 7
        total += len(self._get_medium_priority_fixes(all_results)) * 4
        return total
