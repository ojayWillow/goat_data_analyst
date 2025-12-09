"""Tests for ProjectManager Agent.

Tests the self-aware, adaptive project coordinator:
- Structure discovery
- Pattern learning
- Validation
- Change tracking
- Health reporting
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from agents.project_manager.project_manager import (
    ProjectManager,
    StructureScanner,
    PatternLearner,
    PatternValidator,
    ChangeTracker,
    HealthReporter,
)
from core.logger import Logger


class TestStructureScanner:
    """Test structure discovery."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Logger("TestScanner").get_logger()
        self.scanner = StructureScanner(self.logger)

    def test_discover_agents(self):
        """Test discovering agents from agents/ folder."""
        agents = self.scanner.discover_agents()
        
        # Should find at least some agents
        assert isinstance(agents, dict)
        assert len(agents) > 0, "Should find agents in agents/ folder"
        
        # Check structure of discovered agents
        for agent_name, info in agents.items():
            assert "path" in info
            assert "main_file" in info
            assert "exists" in info
            assert "has_test" in info
            assert info["exists"] is True

    def test_discover_tests(self):
        """Test discovering test files from tests/ folder."""
        tests = self.scanner.discover_tests()
        
        # Should find at least some tests
        assert isinstance(tests, dict)
        assert len(tests) > 0, "Should find test files in tests/ folder"
        
        # All should be test files
        for test_name, info in tests.items():
            assert test_name.startswith("test_")
            assert info["exists"] is True

    def test_discover_structure_complete(self):
        """Test discovering complete structure."""
        structure = self.scanner.discover_structure()
        
        assert "agents" in structure
        assert "tests" in structure
        assert "discovered_at" in structure
        assert len(structure["agents"]) > 0
        assert len(structure["tests"]) > 0


class TestPatternLearner:
    """Test pattern learning from existing code."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Logger("TestLearner").get_logger()
        self.learner = PatternLearner(self.logger)
        self.scanner = StructureScanner(self.logger)

    def test_learn_agent_pattern(self):
        """Test learning agent pattern."""
        agents = self.scanner.discover_agents()
        pattern = self.learner.learn_agent_pattern(agents)
        
        assert "agent_structure" in pattern
        assert "expected_methods" in pattern
        assert "naming_convention" in pattern
        assert pattern["discovered_agents"] == len(agents)

    def test_learn_patterns_complete(self):
        """Test learning complete patterns."""
        structure = self.scanner.discover_structure()
        patterns = self.learner.learn_patterns(structure)
        
        assert "agent_pattern" in patterns
        assert "pattern_confidence" in patterns
        assert "learned_at" in patterns
        assert 0 <= patterns["pattern_confidence"] <= 1.0


class TestPatternValidator:
    """Test pattern validation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Logger("TestValidator").get_logger()
        self.validator = PatternValidator(self.logger)
        self.patterns = {"agent_pattern": {}}

    def test_validate_valid_agent(self):
        """Test validating a properly named agent."""
        result = self.validator.validate_agent("data_loader", self.patterns)
        
        assert result["valid"] is True
        assert result["agent"] == "data_loader"
        assert len(result["issues"]) == 0

    def test_validate_invalid_agent_name(self):
        """Test validating agent with invalid name."""
        result = self.validator.validate_agent("DataLoader", self.patterns)
        
        # Should have issues (not snake_case)
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_validate_empty_agent_name(self):
        """Test validating empty agent name."""
        result = self.validator.validate_agent("", self.patterns)
        
        assert result["valid"] is False
        assert any("empty" in issue.lower() for issue in result["issues"])


class TestChangeTracker:
    """Test change tracking."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Logger("TestTracker").get_logger()
        self.tracker = ChangeTracker(self.logger)
        self.scanner = StructureScanner(self.logger)

    def test_get_current_state(self):
        """Test getting current project state."""
        structure = self.scanner.discover_structure()
        state = self.tracker.get_current_state(structure)
        
        assert "agents" in state
        assert "tests" in state
        assert "timestamp" in state
        assert isinstance(state["agents"], list)
        assert isinstance(state["tests"], list)

    def test_detect_changes(self):
        """Test detecting changes between states."""
        current = {
            "agents": ["explorer", "aggregator", "visualizer"],
            "tests": ["test_explorer", "test_aggregator"],
            "timestamp": datetime.now().isoformat(),
        }
        previous = {
            "agents": ["explorer", "aggregator"],
            "tests": ["test_explorer"],
            "timestamp": None,
        }
        
        changes = self.tracker.get_changes(current, previous)
        
        assert "visualizer" in changes["new_agents"]
        assert "test_aggregator" in changes["new_tests"]
        assert len(changes["removed_agents"]) == 0


class TestHealthReporter:
    """Test health reporting."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Logger("TestReporter").get_logger()
        self.reporter = HealthReporter(self.logger)

    def test_calculate_health_score(self):
        """Test health score calculation."""
        structure = {
            "agents": {
                "explorer": {"has_test": True},
                "aggregator": {"has_test": False},
                "visualizer": {"has_test": True},
            },
            "tests": {},
        }
        changes = {
            "new_agents": [],
            "removed_agents": [],
        }
        
        score = self.reporter.calculate_health_score(structure, changes)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_generate_report(self):
        """Test generating health report."""
        structure = {
            "agents": {
                "explorer": {"has_test": True},
                "aggregator": {"has_test": False},
            },
            "tests": {"test_explorer": {"exists": True}},
            "discovered_at": datetime.now().isoformat(),
        }
        patterns = {
            "agent_pattern": {},
            "pattern_confidence": 0.95,
        }
        changes = {
            "new_agents": ["aggregator"],
            "removed_agents": [],
            "new_tests": [],
        }
        
        report = self.reporter.generate_report(structure, patterns, changes)
        
        assert "health_score" in report
        assert "status" in report
        assert "summary" in report
        assert "recommendations" in report
        assert "generated_at" in report

    def test_status_mapping(self):
        """Test status mapping for different scores."""
        assert "Excellent" in self.reporter._get_status(95)
        assert "Good" in self.reporter._get_status(75)
        assert "Fair" in self.reporter._get_status(55)
        assert "Needs Work" in self.reporter._get_status(25)


class TestProjectManager:
    """Test ProjectManager integration."""

    def test_initialization(self):
        """Test ProjectManager initialization."""
        pm = ProjectManager()
        
        assert pm.logger is not None
        assert pm.scanner is not None
        assert pm.learner is not None
        assert pm.validator is not None
        assert pm.tracker is not None
        assert pm.reporter is not None

    def test_execute(self):
        """Test complete ProjectManager execution."""
        pm = ProjectManager()
        result = pm.execute()
        
        assert "structure" in result
        assert "patterns" in result
        assert "changes" in result
        assert "health" in result
        
        # Verify structure discovery
        assert len(result["structure"]["agents"]) > 0
        
        # Verify health report
        assert "health_score" in result["health"]
        assert "status" in result["health"]

    def test_get_report(self):
        """Test getting report after execution."""
        pm = ProjectManager()
        pm.execute()
        report = pm.get_report()
        
        assert report is not None
        assert len(report.keys()) > 0

    def test_validate_new_agent(self):
        """Test validating a new agent."""
        pm = ProjectManager()
        pm.execute()
        
        result = pm.validate_new_agent("test_agent")
        
        assert "valid" in result
        assert "issues" in result
        assert "validated_at" in result

    def test_agent_summary(self):
        """Test getting agent summary."""
        pm = ProjectManager()
        pm.execute()
        
        summary = pm.get_agent_summary()
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Found" in summary or "No agents" in summary

    def test_print_report(self, capsys):
        """Test printing formatted report."""
        pm = ProjectManager()
        pm.execute()
        pm.print_report()
        
        captured = capsys.readouterr()
        assert "HEALTH REPORT" in captured.out or "PROJECT" in captured.out


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
