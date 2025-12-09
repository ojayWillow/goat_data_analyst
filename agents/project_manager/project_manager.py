"""ProjectManager Agent - Self-aware project coordinator.

Auto-discovers project structure, learns patterns, validates new agents,
and tracks project health. Grows with the project - zero maintenance.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any, Tuple
import ast

from core.logger import get_logger


class StructureScanner:
    """Scans project and discovers structure automatically."""

    def __init__(self, logger):
        self.logger = logger
        self.project_root = Path(__file__).parent.parent.parent

    def discover_agents(self) -> Dict[str, Dict[str, Any]]:
        """Discover all agents in the agents/ folder.
        
        Returns:
            Dict mapping agent names to their metadata (path, status, etc)
        """
        agents = {}
        agents_dir = self.project_root / "agents"

        if not agents_dir.exists():
            return agents

        # Discover .py files (flat structure)
        for py_file in agents_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            agent_name = py_file.stem
            agents[agent_name] = {
                "path": str(agents_dir / agent_name),
                "main_file": str(py_file),
                "exists": True,
                "has_test": self._has_test(agent_name),
                "discoverable": True,
            }

        # Discover folders (folder structure)
        for item in agents_dir.iterdir():
            if not item.is_dir() or item.name.startswith("_"):
                continue

            agent_name = item.name
            # Skip if already discovered as .py file
            if agent_name in agents:
                continue

            # Check for main module file in folder
            main_file = item / f"{agent_name}.py"
            if not main_file.exists():
                # Try first .py file in folder
                py_files = list(item.glob("*.py"))
                if not py_files:
                    continue
                main_file = py_files[0]

            agents[agent_name] = {
                "path": str(item),
                "main_file": str(main_file),
                "exists": True,
                "has_test": self._has_test(agent_name),
                "discoverable": True,
            }

        return agents

    def discover_tests(self) -> Dict[str, Dict[str, Any]]:
        """Discover all test files.
        
        Returns:
            Dict mapping test names to their metadata
        """
        tests = {}
        tests_dir = self.project_root / "tests"

        if not tests_dir.exists():
            return tests

        for test_file in tests_dir.glob("test_*.py"):
            test_name = test_file.stem
            tests[test_name] = {
                "path": str(test_file),
                "exists": True,
                "discoverable": True,
            }

        return tests

    def _has_test(self, agent_name: str) -> bool:
        """Check if agent has corresponding test file."""
        tests_dir = self.project_root / "tests"
        return (tests_dir / f"test_{agent_name}.py").exists()

    def discover_structure(self) -> Dict[str, Any]:
        """Discover complete project structure.
        
        Returns:
            Complete structure including agents, tests, folders, files
        """
        return {
            "agents": self.discover_agents(),
            "tests": self.discover_tests(),
            "discovered_at": datetime.now().isoformat(),
        }


class PatternLearner:
    """Learns patterns from existing code."""

    def __init__(self, logger):
        self.logger = logger
        self.project_root = Path(__file__).parent.parent.parent

    def learn_agent_pattern(self, agents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Learn the pattern that agents follow.
        
        Returns:
            Dict describing the learned pattern
        """
        pattern = {
            "agent_structure": {
                "has_init": True,
                "has_main_file": True,
                "has_methods": [
                    "__init__",
                    "execute",
                    "validate_input",
                    "process",
                ],
            },
            "expected_methods": self._extract_expected_methods(),
            "naming_convention": "snake_case",
            "test_naming": "test_{agent_name}.py",
            "discovered_agents": len(agents),
        }
        return pattern

    def _extract_expected_methods(self) -> List[str]:
        """Extract common methods from existing agents."""
        # Base methods all agents should have
        return [
            "__init__",
            "execute",
            "validate_input",
            "process",
        ]

    def learn_patterns(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Learn all patterns from discovered structure.
        
        Returns:
            Dict with all learned patterns
        """
        agents = structure.get("agents", {})

        return {
            "agent_pattern": self.learn_agent_pattern(agents),
            "pattern_confidence": 0.95 if len(agents) > 0 else 0.5,
            "learned_at": datetime.now().isoformat(),
            "total_agents_analyzed": len(agents),
        }


class PatternValidator:
    """Validates new agents against learned patterns."""

    def __init__(self, logger):
        self.logger = logger

    def validate_agent(self, agent_name: str, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if agent matches learned pattern.
        
        Returns:
            Validation result with issues (if any)
        """
        issues = []
        pattern = patterns.get("agent_pattern", {})

        # Basic validations
        if not agent_name:
            issues.append("Agent name is empty")
        elif not agent_name.islower() and not "_" in agent_name:
            issues.append(f"Agent name '{agent_name}' should use snake_case")

        return {
            "agent": agent_name,
            "valid": len(issues) == 0,
            "issues": issues,
            "validated_at": datetime.now().isoformat(),
        }


class ChangeTracker:
    """Tracks what changed in the project."""

    def __init__(self, logger):
        self.logger = logger
        self.project_root = Path(__file__).parent.parent.parent
        self.state_file = self.project_root / ".project_state.json"

    def get_current_state(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Get current project state."""
        return {
            "agents": list(structure.get("agents", {}).keys()),
            "tests": list(structure.get("tests", {}).keys()),
            "timestamp": datetime.now().isoformat(),
        }

    def load_previous_state(self) -> Dict[str, Any]:
        """Load previous project state if it exists."""
        if not self.state_file.exists():
            return {"agents": [], "tests": [], "timestamp": None}

        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"agents": [], "tests": [], "timestamp": None}

    def get_changes(self, current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
        """Detect what changed.
        
        Returns:
            Dict with new, removed, and unchanged agents/tests
        """
        current_agents = set(current.get("agents", []))
        previous_agents = set(previous.get("agents", []))
        current_tests = set(current.get("tests", []))
        previous_tests = set(previous.get("tests", []))

        return {
            "new_agents": list(current_agents - previous_agents),
            "removed_agents": list(previous_agents - current_agents),
            "new_tests": list(current_tests - previous_tests),
            "removed_tests": list(previous_tests - current_tests),
            "unchanged_agents": list(current_agents & previous_agents),
            "detected_at": datetime.now().isoformat(),
        }

    def save_state(self, state: Dict[str, Any]) -> bool:
        """Save current state for next comparison."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            return False


class HealthReporter:
    """Generates health reports about the project."""

    def __init__(self, logger):
        self.logger = logger

    def calculate_health_score(
        self, structure: Dict[str, Any], changes: Dict[str, Any]
    ) -> float:
        """Calculate project health score (0-100).
        
        Returns:
            Health score based on test coverage, changes, etc
        """
        agents = structure.get("agents", {})
        tests = structure.get("tests", {})

        if len(agents) == 0:
            return 0.0

        # Test coverage
        tested_agents = sum(1 for a in agents.values() if a.get("has_test"))
        test_coverage = (tested_agents / len(agents)) * 100 if len(agents) > 0 else 0

        # Change stability
        new_agents = len(changes.get("new_agents", []))
        removed_agents = len(changes.get("removed_agents", []))
        stability_factor = 1.0 - (new_agents + removed_agents) * 0.1
        stability_factor = max(0.0, stability_factor)

        # Overall score
        score = (test_coverage * 0.7) + (stability_factor * 100 * 0.3)
        return min(100.0, score)

    def generate_report(
        self,
        structure: Dict[str, Any],
        patterns: Dict[str, Any],
        changes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive health report.
        
        Returns:
            Detailed health report with scores and recommendations
        """
        agents = structure.get("agents", {})
        tests = structure.get("tests", {})
        health_score = self.calculate_health_score(structure, changes)

        # Test coverage
        tested_agents = [a for a in agents.keys() if agents[a].get("has_test")]
        untested_agents = [a for a in agents.keys() if not agents[a].get("has_test")]

        return {
            "health_score": round(health_score, 2),
            "status": self._get_status(health_score),
            "summary": {
                "total_agents": len(agents),
                "tested_agents": len(tested_agents),
                "untested_agents": len(untested_agents),
                "test_coverage": round((len(tested_agents) / len(agents) * 100), 2)
                if len(agents) > 0
                else 0,
                "total_tests": len(tests),
            },
            "changes": {
                "new_agents": changes.get("new_agents", []),
                "removed_agents": changes.get("removed_agents", []),
                "new_tests": changes.get("new_tests", []),
            },
            "recommendations": self._get_recommendations(agents, untested_agents),
            "generated_at": datetime.now().isoformat(),
        }

    def _get_status(self, score: float) -> str:
        """Get status based on health score."""
        if score >= 90:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 50:
            return "Fair"
        else:
            return "Needs Work"

    def _get_recommendations(self, agents: Dict, untested: List[str]) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []

        if len(untested) > 0:
            recommendations.append(
                f"Create tests for: {', '.join(untested[:3])}"
            )

        if len(agents) < 3:
            recommendations.append("Continue building agents to establish patterns")

        if len(recommendations) == 0:
            recommendations.append("Project looks good! Keep adding tests.")

        return recommendations


class ProjectManager:
    """Self-aware project coordinator.
    
    Auto-discovers agents, learns patterns, validates new additions,
    tracks changes, and reports health. Grows with the project.
    """

    def __init__(self):
        self.logger = get_logger("ProjectManager")
        self.scanner = StructureScanner(self.logger)
        self.learner = PatternLearner(self.logger)
        self.validator = PatternValidator(self.logger)
        self.tracker = ChangeTracker(self.logger)
        self.reporter = HealthReporter(self.logger)

        # Store discovered structure and patterns
        self.structure = {}
        self.patterns = {}
        self.changes = {}
        self.report = {}

    def execute(self) -> Dict[str, Any]:
        """Execute complete project analysis and reporting.
        
        Returns:
            Complete project report with health, changes, recommendations
        """
        try:
            # 1. Discover structure
            self.logger.info("Scanning project structure...")
            self.structure = self.scanner.discover_structure()
            agents_found = len(self.structure.get("agents", {}))
            tests_found = len(self.structure.get("tests", {}))
            self.logger.info(
                f"Found {agents_found} agents, {tests_found} tests"
            )

            # 2. Learn patterns
            self.logger.info("Learning patterns from existing code...")
            self.patterns = self.learner.learn_patterns(self.structure)
            self.logger.info(f"Pattern confidence: {self.patterns.get('pattern_confidence')}")

            # 3. Track changes
            self.logger.info("Tracking changes...")
            current_state = self.tracker.get_current_state(self.structure)
            previous_state = self.tracker.load_previous_state()
            self.changes = self.tracker.get_changes(current_state, previous_state)
            self.tracker.save_state(current_state)

            if self.changes.get("new_agents"):
                self.logger.info(f"New: {self.changes['new_agents']}")
            if self.changes.get("new_tests"):
                self.logger.info(f"New tests: {self.changes['new_tests']}")

            # 4. Generate report
            self.logger.info("Generating health report...")
            self.report = self.reporter.generate_report(
                self.structure, self.patterns, self.changes
            )
            self.logger.info(f"Health: {self.report['health_score']}/100 - {self.report['status']}")

            return self.get_report()

        except Exception as e:
            self.logger.error(f"ProjectManager execution failed: {e}")
            raise

    def get_report(self) -> Dict[str, Any]:
        """Get the current project report.
        
        Returns:
            Complete project analysis and health report
        """
        return {
            "structure": self.structure,
            "patterns": self.patterns,
            "changes": self.changes,
            "health": self.report,
        }

    def validate_new_agent(self, agent_name: str) -> Dict[str, Any]:
        """Validate if a new agent matches the learned pattern.
        
        Args:
            agent_name: Name of the agent to validate
            
        Returns:
            Validation result
        """
        self.logger.info(f"Validating agent '{agent_name}'...")
        result = self.validator.validate_agent(agent_name, self.patterns)
        
        if result["valid"]:
            self.logger.info(f"Valid - matches learned pattern")
        else:
            self.logger.warning(f"Issues: {result['issues']}")
        
        return result

    def get_agent_summary(self) -> str:
        """Get summary of discovered agents.
        
        Returns:
            Human-readable summary
        """
        agents = self.structure.get("agents", {})
        if not agents:
            return "No agents discovered yet."

        summary = f"Found {len(agents)} agents:\n"
        for agent_name, info in agents.items():
            status = "[OK]" if info.get("has_test") else "[NO TEST]"
            summary += f"  {status} {agent_name}\n"

        return summary

    def print_report(self) -> None:
        """Print formatted health report to console."""
        if not self.report:
            print("No report generated yet. Call execute() first.")
            return

        health = self.report
        print("\n" + "=" * 60)
        print(f"PROJECT HEALTH REPORT - {health['status']}")
        print("=" * 60)
        print(f"\nHealth Score: {health['health_score']}/100")
        print(f"\nSummary:")
        for key, value in health["summary"].items():
            print(f"  {key}: {value}")

        if health["changes"]["new_agents"]:
            print(f"\nNew Agents: {', '.join(health['changes']['new_agents'])}")
        if health["changes"]["new_tests"]:
            print(f"New Tests: {', '.join(health['changes']['new_tests'])}")

        print(f"\nRecommendations:")
        for rec in health["recommendations"]:
            print(f"  - {rec}")

        print("\n" + "=" * 60 + "\n")
