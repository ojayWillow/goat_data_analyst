"""ProjectManager Agent - Enterprise-grade project coordinator.

Auto-discovers agents, learns patterns, validates architecture,
monitors health, analyzes code, and generates actionable insights.

V3 Enhancements (Honest Health Reporting):
- ErrorIntelligenceChecker: Detect which agents have EI
- ErrorHandlingAuditor: Audit error patterns
- IntegrationTester: Test agent integration
- ContractValidator: Validate API contracts
- DependencyConsistencyChecker: Check import consistency

Result: Honest health scores that show ACTUAL gaps A-Z
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from core.logger import get_logger
from .workers import (
    StructureScanner,
    PatternLearner,
    PatternValidator,
    ChangeTracker,
    HealthReporter,
    CodeAnalyzer,
    ArchitectureValidator,
    DependencyMapper,
    ErrorIntelligenceChecker,
    ErrorHandlingAuditor,
    IntegrationTester,
    ContractValidator,
    DependencyConsistencyChecker,
)


class ProjectManager:
    """Enterprise-grade project coordinator.
    
    Auto-discovers agents, learns patterns, validates architecture,
    monitors health, and generates actionable insights.
    
    Workers (SRP):
    - StructureScanner: Discovers project structure
    - PatternLearner: Learns patterns from code
    - PatternValidator: Validates new additions
    - ChangeTracker: Tracks evolution
    - HealthReporter: Generates health metrics
    - CodeAnalyzer: Deep code inspection
    - ArchitectureValidator: Validates architecture
    - DependencyMapper: Maps dependencies
    - ErrorIntelligenceChecker: Audits Error Intelligence coverage
    - ErrorHandlingAuditor: Audits error handling patterns
    - IntegrationTester: Tests agent integrations
    - ContractValidator: Validates API contracts
    - DependencyConsistencyChecker: Checks import consistency
    """

    def __init__(self):
        self.logger = get_logger("ProjectManager")
        self.project_root = Path(__file__).parent.parent.parent

        # Initialize workers (8 original + 5 new)
        self.scanner = StructureScanner(self.logger)
        self.learner = PatternLearner(self.logger)
        self.validator = PatternValidator(self.logger)
        self.tracker = ChangeTracker(self.logger)
        self.reporter = HealthReporter(self.logger)
        self.analyzer = CodeAnalyzer(self.logger)
        self.arch_validator = ArchitectureValidator(self.logger)
        self.dep_mapper = DependencyMapper(self.logger)
        
        # New workers for honest health reporting
        self.ei_checker = ErrorIntelligenceChecker(self.logger)
        self.error_auditor = ErrorHandlingAuditor(self.logger)
        self.integration_tester = IntegrationTester(self.logger)
        self.contract_validator = ContractValidator(self.logger)
        self.dep_consistency = DependencyConsistencyChecker(self.logger)

        # Storage
        self.structure = {}
        self.patterns = {}
        self.changes = {}
        self.report = {}
        self.code_analysis = {}
        self.architecture = {}
        self.dependencies = {}
        self.error_intelligence = {}
        self.error_handling = {}
        self.integrations = {}
        self.contracts = {}
        self.dependency_consistency = {}

    def execute(self) -> Dict[str, Any]:
        """Execute complete project analysis."""
        try:
            # 1. Discover
            self.logger.info("[SCAN] Scanning project structure...")
            self.structure = self.scanner.discover_structure()
            agents_found = len(self.structure.get("agents", {}))
            tests_found = len(self.structure.get("tests", {}))
            self.logger.info(f"   Found {agents_found} agents, {tests_found} tests")

            # 2. Learn patterns
            self.logger.info("[LEARN] Learning patterns from code...")
            self.patterns = self.learner.learn_patterns(self.structure)
            self.logger.info(f"   Pattern confidence: {self.patterns.get('pattern_confidence')}")

            # 3. Analyze code
            self.logger.info("[ANALYZE] Analyzing code structure...")
            self.code_analysis = self._analyze_all_agents()
            self.logger.info(f"   Analyzed {len(self.code_analysis)} agents")

            # 4. Validate architecture
            self.logger.info("[ARCH] Validating architecture...")
            self.architecture = self.arch_validator.validate_project_structure(self.structure)
            self.logger.info(f"   Architecture score: {self.architecture.get('overall_score'):.1f}/100")

            # 5. Map dependencies
            self.logger.info("[DEPS] Mapping dependencies...")
            self.dependencies = self.dep_mapper.map_dependencies(self.structure)
            self.logger.info(f"   Found {self.dependencies.get('total_external')} external deps")

            # 6. Track changes
            self.logger.info("[TRACK] Tracking changes...")
            current_state = self.tracker.get_current_state(self.structure)
            previous_state = self.tracker.load_previous_state()
            self.changes = self.tracker.get_changes(current_state, previous_state)
            self.tracker.save_state(current_state)
            
            if self.changes.get("new_agents"):
                self.logger.info(f"   New: {self.changes['new_agents']}")
            if self.changes.get("new_tests"):
                self.logger.info(f"   New tests: {self.changes['new_tests']}")

            # ===== NEW ANALYSIS =====
            
            # 7. Check Error Intelligence Coverage
            self.logger.info("[EI] Checking Error Intelligence coverage...")
            self.error_intelligence = self.ei_checker.audit_agents(self.structure)
            ei_coverage = self.error_intelligence.get("coverage_percentage", 0)
            self.logger.info(f"   Error Intelligence coverage: {ei_coverage}%")

            # 8. Audit Error Handling
            self.logger.info("[ERROR] Auditing error handling patterns...")
            self.error_handling = self.error_auditor.audit_agents(self.structure)
            error_score = self.error_handling.get("average_score", 0)
            self.logger.info(f"   Error handling score: {error_score:.1f}/100")

            # 9. Test Integrations
            self.logger.info("[INTEGRATION] Testing agent integrations...")
            self.integrations = self.integration_tester.test_integrations(self.structure)
            integration_health = self.integrations.get("health_score", 0)
            self.logger.info(f"   Integration health: {integration_health:.1f}%")

            # 10. Validate Contracts
            self.logger.info("[CONTRACT] Validating API contracts...")
            self.contracts = self.contract_validator.validate_contracts(self.structure)
            contract_compliance = self.contracts.get("contract_compliance", 0)
            self.logger.info(f"   Contract compliance: {contract_compliance:.1f}%")

            # 11. Check Dependency Consistency
            self.logger.info("[CONSISTENCY] Checking dependency consistency...")
            self.dependency_consistency = self.dep_consistency.check_consistency(self.structure)
            dep_consistency_score = self.dependency_consistency.get("consistency_score", 0)
            self.logger.info(f"   Dependency consistency: {dep_consistency_score:.1f}/100")

            # 12. Generate health report
            self.logger.info("[HEALTH] Generating honest health report...")
            self.report = self.reporter.generate_report(
                self.structure, self.patterns, self.changes, self.code_analysis
            )
            self.logger.info(f"   Health: {self.report['health_score']}/100 {self.report['status']}")

            return self.get_report()

        except Exception as e:
            self.logger.error(f"ProjectManager execution failed: {e}")
            raise

    def get_report(self) -> Dict[str, Any]:
        """Get complete project analysis report."""
        return {
            "structure": self.structure,
            "patterns": self.patterns,
            "code_analysis": self.code_analysis,
            "architecture": self.architecture,
            "dependencies": self.dependencies,
            "changes": self.changes,
            "error_intelligence": self.error_intelligence,
            "error_handling": self.error_handling,
            "integrations": self.integrations,
            "contracts": self.contracts,
            "dependency_consistency": self.dependency_consistency,
            "health": self.report,
            "timestamp": datetime.now().isoformat(),
        }

    def validate_new_agent(self, agent_name: str) -> Dict[str, Any]:
        """Validate if new agent matches patterns."""
        self.logger.info(f"Validating agent '{agent_name}'...")
        return self.validator.validate_agent(agent_name, self.patterns)

    def get_agent_summary(self) -> str:
        """Get summary of all agents."""
        agents = self.structure.get("agents", {})
        if not agents:
            return "No agents discovered."

        summary = f"Found {len(agents)} agents:\n"
        for agent_name, info in agents.items():
            status = "OK" if info.get("has_test") else "NO-TEST"
            workers = f" [{info.get('worker_count', 0)} workers]" if info.get("has_workers") else ""
            summary += f"  [{status}] {agent_name}{workers}\n"

        return summary

    def print_report(self) -> None:
        """Print formatted report to console."""
        if not self.report:
            print("No report generated. Call execute() first.")
            return

        print("\n" + "="*70)
        print(f"PROJECT HEALTH REPORT - {self.report['status']}")
        print("="*70)
        
        # Health Score
        print(f"\n[HEALTH] Score: {self.report['health_score']}/100")
        
        # Summary
        print(f"\n[SUMMARY]")
        for key, value in self.report["summary"].items():
            print(f"   {key}: {value}")
        
        # Error Intelligence Coverage
        if self.error_intelligence:
            print(f"\n[ERROR INTELLIGENCE]")
            ei_cov = self.error_intelligence.get("coverage_percentage", 0)
            print(f"   Coverage: {ei_cov}% ({self.error_intelligence.get('with_error_intelligence', 0)}/{self.error_intelligence.get('total_agents', 0)} agents)")
            print(f"   Status: {self.error_intelligence.get('status')}")
        
        # Error Handling
        if self.error_handling:
            print(f"\n[ERROR HANDLING]")
            avg_score = self.error_handling.get("average_score", 0)
            print(f"   Average Score: {avg_score:.1f}/100")
            print(f"   Strong: {self.error_handling.get('strong_error_handling', 0)} agents")
            print(f"   Weak: {self.error_handling.get('weak_error_handling', 0)} agents")
            print(f"   Critical Gaps: {self.error_handling.get('critical_gaps', 0)} agents")
        
        # Integration Health
        if self.integrations:
            print(f"\n[INTEGRATIONS]")
            int_health = self.integrations.get("health_score", 0)
            print(f"   Health: {int_health:.1f}%")
            print(f"   Working: {self.integrations.get('working_integrations', 0)} points")
            print(f"   Broken: {self.integrations.get('broken_integrations', 0)} points")
        
        # Contracts
        if self.contracts:
            print(f"\n[CONTRACTS]")
            compliance = self.contracts.get("contract_compliance", 0)
            print(f"   Compliance: {compliance:.1f}%")
            print(f"   Valid: {self.contracts.get('agents_with_valid_contracts', 0)} agents")
            print(f"   Issues: {self.contracts.get('contract_issues', 0)}")
        
        # Dependency Consistency
        if self.dependency_consistency:
            print(f"\n[DEPENDENCY CONSISTENCY]")
            dep_score = self.dependency_consistency.get("consistency_score", 0)
            print(f"   Score: {dep_score:.1f}/100")
            print(f"   Missing Imports: {len(self.dependency_consistency.get('missing_standard_imports', []))}")
            print(f"   Inconsistencies: {len(self.dependency_consistency.get('inconsistent_imports', []))}")
        
        # Architecture
        if self.architecture:
            print(f"\n[ARCH] Architecture Score: {self.architecture.get('overall_score', 0):.1f}/100")
            if self.architecture.get("issues"):
                print(f"   Issues: {len(self.architecture['issues'])}")
                for issue in self.architecture["issues"][:3]:
                    print(f"   - {issue}")
        
        # Code Quality
        if self.code_analysis:
            print(f"\n[CODE]")
            avg_type_hints = sum(
                a.get("type_hints_coverage", 0) for a in self.code_analysis.values()
            ) / len(self.code_analysis) if self.code_analysis else 0
            avg_docstrings = sum(
                a.get("docstring_coverage", 0) for a in self.code_analysis.values()
            ) / len(self.code_analysis) if self.code_analysis else 0
            print(f"   Type Hints: {avg_type_hints:.0f}%")
            print(f"   Docstrings: {avg_docstrings:.0f}%")
        
        # Recommendations
        if self.report["recommendations"]:
            print(f"\n[RECOMMENDATIONS]")
            for rec in self.report["recommendations"]:
                print(f"   - {rec}")
        
        print("\n" + "="*70 + "\n")

    def _analyze_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Analyze code for all agents."""
        analysis = {}
        agents = self.structure.get("agents", {})
        
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            analysis[agent_name] = self.analyzer.analyze_agent(agent_path)
            # Also analyze workers if present
            if info.get("has_workers"):
                analysis[agent_name]["workers"] = self.analyzer.analyze_workers(agent_path)
        
        return analysis
