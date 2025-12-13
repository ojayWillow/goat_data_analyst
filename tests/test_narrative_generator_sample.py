"""Sample Test File for NarrativeGenerator.

Demonstrates test structure and patterns for all test categories.
Copy and adapt this for your complete test suite.

Usage:
  pytest tests/test_narrative_generator_sample.py -v
  pytest tests/test_narrative_generator_sample.py::test_agent_init -v
"""

import pytest
import sys
from typing import Dict, Any
from datetime import datetime
import time

# Import agent and workers
from agents.narrative_generator.narrative_generator import NarrativeGenerator
from agents.narrative_generator.workers.insight_extractor import InsightExtractor
from agents.narrative_generator.workers.problem_identifier import ProblemIdentifier
from agents.narrative_generator.workers.action_recommender import ActionRecommender
from agents.narrative_generator.workers.story_builder import StoryBuilder
from core.error_recovery import RecoveryError


# ===== CATEGORY 1: INITIALIZATION TESTS =====

class TestInitialization:
    """Test agent and worker initialization."""

    def test_agent_init(self):
        """Agent initializes with correct attributes."""
        agent = NarrativeGenerator()
        
        assert agent.name == "NarrativeGenerator"
        assert agent.version == "2.0-worker-integrated"
        assert agent.logger is not None
        assert agent.structured_logger is not None
        assert agent.error_intelligence is not None

    def test_workers_init(self):
        """All workers are properly initialized."""
        agent = NarrativeGenerator()
        
        # Check all workers exist and have correct names
        assert isinstance(agent.insight_extractor, InsightExtractor)
        assert agent.insight_extractor.name == "InsightExtractor"
        
        assert isinstance(agent.problem_identifier, ProblemIdentifier)
        assert agent.problem_identifier.name == "ProblemIdentifier"
        
        assert isinstance(agent.action_recommender, ActionRecommender)
        assert agent.action_recommender.name == "ActionRecommender"
        
        assert isinstance(agent.story_builder, StoryBuilder)
        assert agent.story_builder.name == "StoryBuilder"

    def test_state_init(self):
        """State is initialized correctly."""
        agent = NarrativeGenerator()
        
        assert agent.agent_results == {}
        assert agent.insights == {}
        assert agent.problems == []
        assert agent.actions == []
        assert agent.narrative is None
        assert agent.quality_score == 0.0
        assert agent.last_error is None


# ===== CATEGORY 2: INPUT VALIDATION TESTS =====

class TestInputValidation:
    """Test input validation methods."""

    def test_validate_agent_results_invalid_type(self):
        """Reject non-dict input."""
        agent = NarrativeGenerator()
        
        is_valid, error = agent._validate_agent_results([1, 2, 3])
        
        assert not is_valid
        assert error is not None
        assert "dict" in error.lower() or "type" in error.lower()

    def test_validate_agent_results_empty_dict(self):
        """Reject empty dict."""
        agent = NarrativeGenerator()
        
        is_valid, error = agent._validate_agent_results({})
        
        assert not is_valid
        assert error is not None
        assert "empty" in error.lower() or "key" in error.lower()

    def test_validate_agent_results_all_empty_values(self):
        """Reject dict with all empty values."""
        agent = NarrativeGenerator()
        
        is_valid, error = agent._validate_agent_results({
            'anomalies': {},
            'predictions': [],
            'report': None
        })
        
        assert not is_valid
        assert error is not None
        assert "empty" in error.lower()

    def test_validate_agent_results_valid(self):
        """Accept valid results."""
        agent = NarrativeGenerator()
        
        is_valid, error = agent._validate_agent_results({
            'anomalies': {'count': 5},
            'predictions': {'accuracy': 0.85}
        })
        
        assert is_valid
        assert error is None

    def test_validate_workflow_results_valid(self):
        """Accept valid workflow results."""
        agent = NarrativeGenerator()
        
        is_valid, error = agent._validate_workflow_results({
            'results': {'anomalies': {'count': 5}},
            'tasks': ['task1']
        })
        
        assert is_valid
        assert error is None

    def test_validate_workflow_results_missing_results_key(self):
        """Reject workflow without 'results' key."""
        agent = NarrativeGenerator()
        
        is_valid, error = agent._validate_workflow_results({
            'tasks': [],
            'execution_time': 1.5
        })
        
        assert not is_valid
        assert "results" in error.lower()

    def test_validate_workflow_results_invalid_results_type(self):
        """Reject workflow with non-dict 'results'."""
        agent = NarrativeGenerator()
        
        is_valid, error = agent._validate_workflow_results({
            'results': [1, 2, 3]  # Should be dict
        })
        
        assert not is_valid
        assert "dict" in error.lower() or "type" in error.lower()


# ===== CATEGORY 3: QUALITY SCORING TESTS =====

class TestQualityScoring:
    """Test quality score calculation."""

    def test_quality_score_no_components(self):
        """Minimal quality score when nothing extracted."""
        agent = NarrativeGenerator()
        
        score = agent._calculate_quality_score(
            insights_count=0,
            problems_count=0,
            actions_count=0,
            had_errors=False
        )
        
        assert 0 <= score <= 1
        assert score < 0.2  # Should be minimal

    def test_quality_score_full_components(self):
        """High quality score with full components."""
        agent = NarrativeGenerator()
        
        score = agent._calculate_quality_score(
            insights_count=5,  # More than 4
            problems_count=4,  # More than 3
            actions_count=4,   # More than 3
            had_errors=False
        )
        
        assert 0.9 <= score <= 1.0

    def test_quality_score_with_errors(self):
        """Quality score reduced with errors."""
        agent = NarrativeGenerator()
        
        score_no_error = agent._calculate_quality_score(
            insights_count=3,
            problems_count=2,
            actions_count=2,
            had_errors=False
        )
        
        score_with_error = agent._calculate_quality_score(
            insights_count=3,
            problems_count=2,
            actions_count=2,
            had_errors=True
        )
        
        assert score_with_error < score_no_error
        assert score_with_error >= 0  # Not negative

    def test_quality_score_clamped_to_range(self):
        """Quality score clamped to [0, 1]."""
        agent = NarrativeGenerator()
        
        # Extreme values
        score = agent._calculate_quality_score(
            insights_count=1000,
            problems_count=1000,
            actions_count=1000,
            had_errors=False
        )
        
        assert score == 1.0  # Clamped to 1.0

    def test_quality_score_always_valid_range(self):
        """Quality score always in [0, 1] range."""
        agent = NarrativeGenerator()
        
        for insights in [0, 1, 5, 100]:
            for problems in [0, 1, 5, 100]:
                for actions in [0, 1, 5, 100]:
                    for has_error in [True, False]:
                        score = agent._calculate_quality_score(
                            insights_count=insights,
                            problems_count=problems,
                            actions_count=actions,
                            had_errors=has_error
                        )
                        assert 0 <= score <= 1, f"Invalid score: {score}"


# ===== CATEGORY 4: RETRY LOGIC TESTS =====

class TestRetryLogic:
    """Test exponential backoff retry mechanism."""

    def test_retry_success_first_attempt(self):
        """Succeed on first attempt without retry."""
        agent = NarrativeGenerator()
        call_count = [0]
        
        def successful_func():
            call_count[0] += 1
            return "success"
        
        result = agent._retry_with_backoff("test_op", successful_func)
        
        assert result == "success"
        assert call_count[0] == 1

    def test_retry_success_second_attempt(self):
        """Succeed on second attempt after one failure."""
        agent = NarrativeGenerator()
        call_count = [0]
        
        def sometimes_fails():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("First attempt fails")
            return "success"
        
        result = agent._retry_with_backoff("test_op", sometimes_fails)
        
        assert result == "success"
        assert call_count[0] == 2

    def test_retry_exhausted(self):
        """Raise RuntimeError after max retries."""
        agent = NarrativeGenerator()
        
        def always_fails():
            raise ValueError("Always fails")
        
        with pytest.raises(RuntimeError) as exc_info:
            agent._retry_with_backoff("test_op", always_fails)
        
        assert "failed after" in str(exc_info.value).lower()

    def test_retry_backoff_timing(self):
        """Verify exponential backoff delay."""
        agent = NarrativeGenerator()
        call_times = []
        
        def track_calls():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Retry")
            return "success"
        
        start = time.time()
        result = agent._retry_with_backoff("test_op", track_calls)
        total_time = time.time() - start
        
        # Should have delays: 1.0s + 2.0s = 3.0s minimum
        assert total_time >= 2.9  # Allow small timing variance
        assert result == "success"


# ===== CATEGORY 5: SET RESULTS TESTS =====

class TestSetResults:
    """Test set_results functionality."""

    def test_set_results_valid(self):
        """Set valid results successfully."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'count': 5},
            'predictions': {'accuracy': 85}
        }
        
        agent.set_results(results)
        
        assert agent.agent_results == results
        assert agent.insights == {}
        assert agent.problems == []
        assert agent.actions == []
        assert agent.quality_score == 0.0

    def test_set_results_invalid_raises_recovery_error(self):
        """Raise RecoveryError for invalid results (due to @retry_on_error decorator)."""
        agent = NarrativeGenerator()
        
        # @retry_on_error decorator wraps ValueError in RecoveryError after retries
        with pytest.raises(RecoveryError):
            agent.set_results(None)  # Invalid

    def test_set_results_resets_state(self):
        """set_results clears previous state."""
        agent = NarrativeGenerator()
        
        # Set initial state
        agent.insights = {'key': 'value'}
        agent.problems = ['problem1']
        agent.narrative = {'text': 'narrative'}
        agent.quality_score = 0.8
        
        # Set new results
        agent.set_results({'anomalies': {'count': 5}})
        
        # State should be reset
        assert agent.insights == {}
        assert agent.problems == []
        assert agent.narrative is None
        assert agent.quality_score == 0.0


# ===== CATEGORY 6: SUMMARY AND HEALTH TESTS =====

class TestSummaryAndHealth:
    """Test get_summary and get_health_report."""

    def test_get_summary_format(self):
        """get_summary returns formatted string."""
        agent = NarrativeGenerator()
        summary = agent.get_summary()
        
        assert isinstance(summary, str)
        assert "NarrativeGenerator" in summary
        assert "Summary" in summary
        assert "=" in summary  # Has separator lines
        assert "Workers" in summary

    def test_get_summary_shows_state(self):
        """get_summary includes current state."""
        agent = NarrativeGenerator()
        agent.agent_results = {'key': 'value'}
        agent.insights = {'insight': 'value'}
        agent.problems = [{'type': 'issue'}]
        agent.actions = [{'action': 'do something'}]
        agent.quality_score = 0.85
        
        summary = agent.get_summary()
        
        assert "Results loaded: True" in summary
        assert "Insights extracted: 1" in summary
        assert "Problems identified: 1" in summary
        assert "Actions recommended: 1" in summary
        assert "Quality score: 0.85" in summary

    def test_get_health_report_structure(self):
        """get_health_report returns complete dict."""
        agent = NarrativeGenerator()
        health = agent.get_health_report()
        
        assert isinstance(health, dict)
        assert 'overall_health' in health
        assert 'quality_score' in health
        assert 'components_healthy' in health
        assert 'total_components' in health
        assert 'problems_identified' in health
        assert 'actions_recommended' in health
        assert 'workers' in health
        assert 'last_error' in health

    def test_get_health_report_values(self):
        """get_health_report returns valid values."""
        agent = NarrativeGenerator()
        agent.quality_score = 0.75
        agent.problems = [1, 2]
        agent.actions = [1, 2, 3]
        agent.last_error = "Test error"
        
        health = agent.get_health_report()
        
        assert health['overall_health'] == 75.0
        assert health['quality_score'] == 0.75
        assert health['total_components'] == 4
        assert health['problems_identified'] == 2
        assert health['actions_recommended'] == 3
        assert health['last_error'] == "Test error"
        assert isinstance(health['workers'], dict)
        assert len(health['workers']) == 4


# ===== CATEGORY 7: FALLBACK NARRATIVE TESTS =====

class TestFallbackNarrative:
    """Test fallback narrative generation."""

    def test_fallback_narrative_structure(self):
        """Fallback narrative has all required fields."""
        agent = NarrativeGenerator()
        fallback = agent._build_fallback_narrative()
        
        assert isinstance(fallback, dict)
        assert 'full_narrative' in fallback
        assert 'sections' in fallback
        assert 'confidence' in fallback
        assert 'fallback_mode' in fallback

    def test_fallback_narrative_with_data(self):
        """Fallback narrative includes available data."""
        agent = NarrativeGenerator()
        agent.insights = {'key': 'insight value'}
        agent.problems = [{'type': 'issue_type', 'description': 'Issue description'}]
        agent.actions = [{'action': 'Take action'}]
        
        fallback = agent._build_fallback_narrative()
        narrative_text = fallback['full_narrative']
        
        assert 'Narrative' in narrative_text
        assert 'insight value' in narrative_text
        assert 'Issue description' in narrative_text
        assert 'Take action' in narrative_text


# ===== INTEGRATION TEST EXAMPLE =====

class TestIntegration:
    """Basic integration test."""

    def test_agent_workflow_valid_input(self):
        """Test basic workflow with valid input."""
        agent = NarrativeGenerator()
        
        valid_results = {
            'anomalies': {
                'anomalies': [1, 2],
                'count': 2,
                'percentage': 1.0,
                'total_rows': 200,
                'top_anomalies': []
            },
            'predictions': {
                'accuracy': 90,
                'confidence': 0.85,
                'top_features': ['f1', 'f2'],
                'trend': 'stable'
            },
            'recommendations': {
                'recommendations': ['action1'],
                'confidence': 0.8,
                'impact': 'medium'
            },
            'report': {
                'statistics': {'mean': 100},
                'completeness': 100,
                'data_quality': 'good'
            }
        }
        
        result = agent.generate_narrative_from_results(valid_results)
        
        assert result is not None
        assert 'status' in result
        assert result['status'] in ['success', 'partial']
        assert 'data' in result
        assert 'message' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
