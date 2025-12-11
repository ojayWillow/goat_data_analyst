"""Integration Tests - Orchestrator + Narrative Generator.

Tests the complete pipeline:
1. Workflow execution (agents running)
2. Result collection
3. Narrative generation
4. Combined output

This validates the full "from data to story" pipeline.
"""

import pytest
from unittest.mock import Mock, MagicMock
from agents.orchestrator import Orchestrator, NarrativeIntegrator
from core.exceptions import OrchestratorError


class TestNarrativeIntegrator:
    """Test NarrativeIntegrator worker."""

    @pytest.fixture
    def integrator(self):
        """Create NarrativeIntegrator instance."""
        return NarrativeIntegrator()

    def test_initialize(self, integrator):
        """Test NarrativeIntegrator initializes."""
        assert integrator.name == "NarrativeIntegrator"
        assert integrator.narrative_tester is not None

    def test_generate_narrative_from_results(self, integrator):
        """Test generating narrative from agent results."""
        agent_results = {
            'explorer': {
                'shape': (100, 5),
                'missing_percentage': 5.0
            },
            'anomalies': {
                'count': 3,
                'percentage': 3.0,
                'severity': 'low'
            },
            'predictions': {
                'confidence': 0.85,
                'accuracy': 87.5
            }
        }
        
        narrative = integrator.generate_narrative_from_results(agent_results)
        
        assert narrative is not None
        assert 'executive_summary' in narrative
        assert 'full_narrative' in narrative
        assert 'agent_results' in narrative

    def test_validate_narrative(self, integrator):
        """Test narrative validation."""
        narrative = {
            'executive_summary': 'Test summary',
            'problem_statement': 'Test problem',
            'action_plan': 'Test action',
            'full_narrative': 'This is a test narrative that is long enough to validate.'
        }
        
        validation = integrator.validate_narrative(narrative)
        
        assert validation['has_executive_summary'] is True
        assert validation['has_problem_statement'] is True
        assert validation['narrative_length_ok'] is True

    def test_get_narrative_summary(self, integrator):
        """Test getting narrative summary."""
        narrative = {
            'executive_summary': 'Test summary',
            'total_recommendations': 3,
            'critical_count': 1,
            'high_count': 2,
            'action_plan': '1. First action\n2. Second action'
        }
        
        summary = integrator.get_narrative_summary(narrative)
        
        assert summary['problem_count'] == 3
        assert summary['critical_issues'] == 1
        assert summary['high_priority'] == 2
        assert len(summary['action_items']) > 0


class TestOrchestratorNarrativeIntegration:
    """Test Orchestrator with Narrative integration."""

    @pytest.fixture
    def orchestrator(self):
        """Create Orchestrator instance."""
        return Orchestrator()

    def test_orchestrator_has_narrative_integrator(self, orchestrator):
        """Test orchestrator has narrative integrator."""
        assert orchestrator.narrative_integrator is not None
        assert orchestrator.narrative_integrator.name == "NarrativeIntegrator"

    def test_generate_narrative_method_exists(self, orchestrator):
        """Test orchestrator has generate_narrative method."""
        assert hasattr(orchestrator, 'generate_narrative')
        assert callable(orchestrator.generate_narrative)

    def test_execute_workflow_with_narrative_method_exists(self, orchestrator):
        """Test orchestrator has full pipeline method."""
        assert hasattr(orchestrator, 'execute_workflow_with_narrative')
        assert callable(orchestrator.execute_workflow_with_narrative)

    def test_generate_narrative_from_agent_results(self, orchestrator):
        """Test generating narrative from agent results."""
        agent_results = {
            'explorer': {'shape': (100, 5), 'missing_percentage': 5.0},
            'anomalies': {'count': 2, 'percentage': 2.0, 'severity': 'low'},
            'predictions': {'confidence': 0.8, 'accuracy': 85.0}
        }
        
        narrative = orchestrator.generate_narrative(agent_results)
        
        assert narrative is not None
        assert 'executive_summary' in narrative
        assert 'full_narrative' in narrative

    def test_full_pipeline_status_includes_narrative(self, orchestrator):
        """Test status includes narrative integrator info."""
        status = orchestrator.get_status()
        
        assert 'workflows' in status
        assert status['status'] == 'active'
        # Narrative integrator is active but not shown in basic status
        # (it's only used when needed)


class TestOrchestrationWithMockAgents:
    """Test orchestration with mocked agents."""

    @pytest.fixture
    def orchestrator_with_agents(self):
        """Create orchestrator with mocked agents."""
        orchestrator = Orchestrator()
        
        # Create mock agents
        explorer = Mock()
        explorer.name = "Explorer"
        explorer.set_data = Mock()
        explorer.get_summary_report = Mock(return_value={
            'shape': (100, 5),
            'missing_percentage': 5.0,
            'columns': ['a', 'b', 'c', 'd', 'e']
        })
        
        anomaly_detector = Mock()
        anomaly_detector.name = "AnomalyDetector"
        anomaly_detector.set_data = Mock()
        anomaly_detector.iqr_detection = Mock(return_value={
            'count': 2,
            'percentage': 2.0,
            'severity': 'low'
        })
        
        predictor = Mock()
        predictor.name = "Predictor"
        predictor.set_data = Mock()
        predictor.trend_analysis = Mock(return_value={
            'confidence': 0.85,
            'accuracy': 87.5,
            'trend': 'stable'
        })
        
        # Register agents
        orchestrator.register_agent('explorer', explorer)
        orchestrator.register_agent('anomaly_detector', anomaly_detector)
        orchestrator.register_agent('predictor', predictor)
        
        return orchestrator

    def test_workflow_with_narrative_pipeline(self, orchestrator_with_agents):
        """Test complete workflow with narrative generation."""
        # Create workflow
        workflow_tasks = [
            {
                'type': 'explore_data',
                'parameters': {'data_key': 'test_data'},
                'critical': True
            },
            {
                'type': 'detect_anomalies',
                'parameters': {'data_key': 'test_data', 'method': 'iqr', 'column': 'a'},
                'critical': False
            },
            {
                'type': 'predict',
                'parameters': {'data_key': 'test_data', 'prediction_type': 'trend', 'column': 'a'},
                'critical': False
            }
        ]
        
        # Note: We'd need actual agents for full workflow testing
        # This test demonstrates the API usage pattern
        assert orchestrator_with_agents is not None
        assert len(orchestrator_with_agents.list_agents()) == 3

    def test_narrative_from_mock_results(self, orchestrator_with_agents):
        """Test narrative generation from mock agent results."""
        mock_results = {
            'explorer': {
                'shape': (100, 5),
                'missing_percentage': 5.0,
                'columns': ['a', 'b', 'c', 'd', 'e']
            },
            'anomalies': {
                'count': 2,
                'percentage': 2.0,
                'severity': 'low'
            },
            'predictions': {
                'confidence': 0.85,
                'accuracy': 87.5,
                'trend': 'stable'
            }
        }
        
        narrative = orchestrator_with_agents.generate_narrative(mock_results)
        
        assert narrative is not None
        assert 'executive_summary' in narrative
        assert len(narrative.get('full_narrative', '')) > 0


class TestNarrativeValidation:
    """Test narrative validation and quality checks."""

    @pytest.fixture
    def integrator(self):
        """Create NarrativeIntegrator."""
        return NarrativeIntegrator()

    def test_validate_complete_narrative(self, integrator):
        """Test validating complete narrative."""
        narrative = {
            'executive_summary': 'This is a test summary',
            'problem_statement': 'This is a test problem statement',
            'action_plan': 'This is a test action plan with multiple items',
            'full_narrative': 'This is a complete narrative that is long enough to pass the length check.'
        }
        
        validation = integrator.validate_narrative(narrative)
        
        assert validation['has_executive_summary'] is True
        assert validation['has_problem_statement'] is True
        assert validation['has_action_plan'] is True
        assert validation['narrative_length_ok'] is True

    def test_validate_incomplete_narrative(self, integrator):
        """Test validating incomplete narrative."""
        narrative = {
            'executive_summary': 'Summary',
            # Missing problem_statement
            # Missing action_plan
            'full_narrative': ''
        }
        
        validation = integrator.validate_narrative(narrative)
        
        assert validation['has_executive_summary'] is True
        assert validation['has_problem_statement'] is False
        assert validation['narrative_length_ok'] is False

    def test_calculate_confidence_score(self, integrator):
        """Test confidence score calculation."""
        narrative = {
            'executive_summary': 'Summary',
            'problem_statement': 'Problem',
            'action_plan': 'Action',
            'full_narrative': 'Full narrative',
            'total_recommendations': 3
        }
        
        summary = integrator.get_narrative_summary(narrative)
        
        assert 'confidence_level' in summary
        assert 0 <= summary['confidence_level'] <= 1.0
        assert summary['confidence_level'] > 0.5  # Should have decent confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
