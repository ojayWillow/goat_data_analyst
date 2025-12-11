"""ProjectManager Agent - Enterprise-grade project coordinator.

Auto-discovers agents, learns patterns, validates architecture,
monitors health, analyzes code, and generates actionable insights.

V2 Enhancements:
- Worker-based architecture
- Deep code analysis (AST)
- Architecture validation
- Dependency mapping
- Advanced health reporting
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
    """

    def __init__(self):
        self.logger = get_logger("ProjectManager")
        self.project_root = Path(__file__).parent.parent.parent

        # Initialize workers
        self.scanner = StructureScanner(self.logger)
        self.learner = PatternLearner(self.logger)
        self.validator = PatternValidator(self.logger)
        self.tracker = ChangeTracker(self.logger)
        self.reporter = HealthReporter(self.logger)
        self.analyzer = CodeAnalyzer(self.logger)
        self.arch_validator = ArchitectureValidator(self.logger)
        self.dep_mapper = DependencyMapper(self.logger)

        # Storage
        self.structure = {}
        self.patterns = {}
        self.changes = {}
        self.report = {}
        self.code_analysis = {}
        self.architecture = {}
        self.dependencies = {}

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

            # 7. Generate health report
            self.logger.info("[HEALTH] Generating health report...")
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
        
        # Changes
        if self.changes["new_agents"] or self.changes["new_tests"]:
            print(f"\n[CHANGES]")
            if self.changes["new_agents"]:
                print(f"   New agents: {', '.join(self.changes['new_agents'])}")
            if self.changes["new_tests"]:
                print(f"   New tests: {len(self.changes['new_tests'])} added")
        
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
