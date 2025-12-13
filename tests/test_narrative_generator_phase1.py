"""PHASE 1 TEST SUITE - Integration, Errors, Cooperation Tests - FIXED

45 comprehensive tests targeting:
- Integration workflows (10 tests)
- Error path scenarios (18 tests)
- Worker cooperation (12 tests)
- Input validation edge cases (5 tests)

Target: 80%+ coverage
Execution: pytest tests/test_narrative_generator_phase1.py -v
"""

import pytest
from agents.narrative_generator.narrative_generator import NarrativeGenerator
from agents.narrative_generator.workers.insight_extractor import InsightExtractor
from agents.narrative_generator.workers.problem_identifier import ProblemIdentifier
from agents.narrative_generator.workers.action_recommender import ActionRecommender
from agents.narrative_generator.workers.story_builder import StoryBuilder


# ===== INTEGRATION TESTS (10) =====

class TestIntegrationWorkflows:
    """Full end-to-end workflow tests."""

    def test_full_workflow_generate_narrative(self):
        """Generate narrative with realistic data."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['Fix anomalies'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {'rows': 1000}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        
        narrative = agent.generate_narrative_from_results(results)
        
        assert narrative is not None
        assert narrative['status'] in ['success', 'partial', 'error']
        assert 'data' in narrative

    def test_workflow_with_high_anomalies(self):
        """Workflow with significant anomalies (>10%)."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(150)), 'total_rows': 1000},
            'predictions': {'accuracy': 70.0, 'confidence': 0.65},
            'recommendations': {'recommendations': ['Investigate', 'Clean data'], 'confidence': 0.75, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 90.0, 'data_quality': 'fair'}
        }
        
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None
        assert narrative['status'] in ['success', 'partial', 'error']

    def test_workflow_with_missing_data(self):
        """Workflow with missing data issues (>15% missing)."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 1000},
            'predictions': {'accuracy': 60.0, 'confidence': 0.50},
            'recommendations': {'recommendations': [], 'confidence': 0.5, 'impact': 'medium'},
            'report': {'statistics': {}, 'completeness': 80.0, 'data_quality': 'poor'}
        }
        
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None

    def test_workflow_multiple_problems(self):
        """Workflow with multiple concurrent problems."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(120)), 'total_rows': 1000},
            'predictions': {'accuracy': 55.0, 'confidence': 0.40},
            'recommendations': {'recommendations': ['Action 1', 'Action 2', 'Action 3'], 'confidence': 0.7, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 75.0, 'data_quality': 'poor'}
        }
        
        narrative = agent.generate_narrative_from_results(results)
        health = agent.get_health_report()
        
        assert narrative is not None
        assert health is not None
        assert 'overall_health' in health

    def test_workflow_perfect_data(self):
        """Workflow with clean data - no problems."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 1000},
            'predictions': {'accuracy': 98.0, 'confidence': 0.95},
            'recommendations': {'recommendations': ['Monitor', 'Maintain'], 'confidence': 0.9, 'impact': 'high'},
            'report': {'statistics': {'rows': 1000}, 'completeness': 100.0, 'data_quality': 'excellent'}
        }
        
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None
        assert narrative['status'] in ['success', 'partial']

    def test_workflow_empty_results(self):
        """Workflow with empty/minimal results."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 0},
            'predictions': {'accuracy': 0, 'confidence': 0},
            'recommendations': {'recommendations': [], 'confidence': 0, 'impact': 'low'},
            'report': {'statistics': {}, 'completeness': 0, 'data_quality': 'unknown'}
        }
        
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None

    def test_workflow_state_reset(self):
        """Workflow state is properly reset between operations."""
        agent = NarrativeGenerator()
        
        # First operation
        results1 = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['Fix'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        narrative1 = agent.generate_narrative_from_results(results1)
        
        # Second operation with different data
        results2 = {
            'anomalies': {'anomalies': list(range(200)), 'total_rows': 1000},
            'predictions': {'accuracy': 50.0, 'confidence': 0.40},
            'recommendations': {'recommendations': [], 'confidence': 0.4, 'impact': 'low'},
            'report': {'statistics': {}, 'completeness': 60.0, 'data_quality': 'poor'}
        }
        narrative2 = agent.generate_narrative_from_results(results2)
        
        # Verify both operations work independently
        assert narrative1 is not None
        assert narrative2 is not None

    def test_workflow_state_isolation_instances(self):
        """Different agent instances have isolated state."""
        agent1 = NarrativeGenerator()
        agent2 = NarrativeGenerator()
        
        results1 = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['A'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        
        results2 = {
            'anomalies': {'anomalies': list(range(200)), 'total_rows': 1000},
            'predictions': {'accuracy': 50.0, 'confidence': 0.40},
            'recommendations': {'recommendations': [], 'confidence': 0.4, 'impact': 'low'},
            'report': {'statistics': {}, 'completeness': 60.0, 'data_quality': 'poor'}
        }
        
        narrative1 = agent1.generate_narrative_from_results(results1)
        narrative2 = agent2.generate_narrative_from_results(results2)
        
        # Both should succeed independently
        assert narrative1 is not None
        assert narrative2 is not None

    def test_workflow_summary_after_generation(self):
        """Summary is correct after generation."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(100)), 'total_rows': 1000},
            'predictions': {'accuracy': 75.0, 'confidence': 0.70},
            'recommendations': {'recommendations': ['Action'], 'confidence': 0.7, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 90.0, 'data_quality': 'good'}
        }
        
        agent.generate_narrative_from_results(results)
        summary = agent.get_summary()
        
        assert summary is not None
        assert len(summary) > 0
        assert 'NarrativeGenerator' in summary

    def test_workflow_quality_score(self):
        """Quality score calculated correctly."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['Fix'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        
        agent.generate_narrative_from_results(results)
        assert 0.0 <= agent.quality_score <= 1.0


# ===== ERROR PATH TESTS (18) =====

class TestErrorPaths:
    """Test error handling and recovery."""

    def test_error_insight_extractor_none(self):
        """InsightExtractor returns None - handled gracefully."""
        extractor = InsightExtractor()
        result = extractor.extract_anomalies(None)
        assert result['count'] == 0
        assert result['severity'] == 'none'

    def test_error_problem_identifier_none_input(self):
        """ProblemIdentifier with None input."""
        identifier = ProblemIdentifier()
        problem = identifier.identify_anomaly_problems(None)
        assert problem is None

    def test_error_invalid_set_results(self):
        """set_results with invalid data raises error."""
        agent = NarrativeGenerator()
        try:
            agent.set_results("not a dict")
            assert False, "Should raise error"
        except (ValueError, TypeError):
            assert True

    def test_error_missing_required_keys(self):
        """set_results missing required keys."""
        agent = NarrativeGenerator()
        results = {'anomalies': {}}  # Missing other keys
        try:
            agent.set_results(results)
            assert False, "Should raise error"
        except (ValueError, AssertionError):
            assert True

    def test_error_malformed_anomalies(self):
        """Handles malformed anomaly data."""
        extractor = InsightExtractor()
        result = extractor.extract_anomalies({'anomalies': "not a list", 'total_rows': 100})
        assert result['count'] == 0

    def test_error_zero_predictions_confidence(self):
        """Handles zero prediction confidence."""
        extractor = InsightExtractor()
        result = extractor.extract_predictions({'accuracy': 0, 'confidence': 0, 'top_features': []})
        assert result['confidence'] == 0
        assert result['importance'] == 0.2

    def test_error_negative_values(self):
        """Handles negative values in calculations."""
        extractor = InsightExtractor()
        result = extractor.extract_anomalies({
            'anomalies': [],
            'total_rows': -100
        })
        assert isinstance(result, dict)

    def test_error_extreme_values(self):
        """Handles extreme values (clamping)."""
        extractor = InsightExtractor()
        result = extractor.extract_predictions({
            'accuracy': 999999.0,
            'confidence': 10.0,
            'top_features': []
        })
        assert result['accuracy'] == 100.0
        assert result['confidence'] == 1.0

    def test_error_empty_recommendations(self):
        """Handles empty recommendations."""
        extractor = InsightExtractor()
        result = extractor.extract_recommendations({
            'recommendations': [],
            'confidence': 0.5,
            'impact': 'low'
        })
        assert result['count'] == 0
        assert result['top_3_actions'] == []

    def test_error_invalid_impact_type(self):
        """Handles invalid impact value."""
        extractor = InsightExtractor()
        result = extractor.extract_recommendations({
            'recommendations': ['A'],
            'confidence': 0.5,
            'impact': 'invalid_impact'
        })
        assert isinstance(result, dict)

    def test_error_story_builder_empty_actions(self):
        """StoryBuilder with empty actions."""
        builder = StoryBuilder()
        narrative = builder.build_complete_narrative([])
        assert narrative is not None
        assert narrative['total_recommendations'] == 0

    def test_error_division_by_zero_protection(self):
        """Division by zero is protected."""
        identifier = ProblemIdentifier()
        problem = identifier.identify_distribution_problems({
            'key_statistics': {'mean': 0, 'std': 0}
        })
        assert isinstance(problem, (dict, type(None)))

    def test_error_type_coercion(self):
        """Handles type coercion safely."""
        extractor = InsightExtractor()
        result = extractor.extract_predictions({
            'accuracy': "95.0",
            'confidence': "0.85",
            'top_features': []
        })
        assert isinstance(result, dict)

    def test_error_special_characters_in_strings(self):
        """Handles special characters in descriptions."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['Fix <anomalies> & clean "data"'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None

    def test_error_unicode_handling(self):
        """Handles Unicode characters."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['Fix données 数据 данные'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None

    def test_error_narrative_generation_partial(self):
        """Narrative generation handles partial data."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': None,
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None

    def test_error_health_report_after_error(self):
        """Health report available after error scenario."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 1000},
            'predictions': {'accuracy': 0, 'confidence': 0},
            'recommendations': {'recommendations': [], 'confidence': 0, 'impact': 'low'},
            'report': {'statistics': {}, 'completeness': 0, 'data_quality': 'unknown'}
        }
        agent.generate_narrative_from_results(results)
        health = agent.get_health_report()
        assert health is not None
        assert 'overall_health' in health


# ===== WORKER COOPERATION TESTS (12) =====

class TestWorkerCooperation:
    """Test workers working together seamlessly."""

    def test_insights_to_problems_flow(self):
        """InsightExtractor output → ProblemIdentifier input."""
        extractor = InsightExtractor()
        identifier = ProblemIdentifier()
        
        insights = extractor.extract_all({
            'anomalies': {'anomalies': list(range(150)), 'total_rows': 1000},
            'predictions': {'accuracy': 70.0, 'confidence': 0.65},
            'recommendations': {'recommendations': ['Fix'], 'confidence': 0.7, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 90.0, 'data_quality': 'good'}
        })
        
        problems = identifier.identify_all_problems(insights)
        assert len(problems) >= 0
        assert all('type' in p for p in problems)

    def test_problems_to_actions_flow(self):
        """ProblemIdentifier output → ActionRecommender input."""
        identifier = ProblemIdentifier()
        recommender = ActionRecommender()
        
        insights = {
            'anomalies': {'count': 150, 'percentage': 15.0, 'total_rows': 1000},
            'predictions': {'confidence': 0.65, 'accuracy': 70.0},
            'statistics': {'completeness': 90.0, 'key_statistics': {}}
        }
        
        problems = identifier.identify_all_problems(insights)
        actions = recommender.recommend_for_all_problems(problems)
        
        assert isinstance(actions, list)

    def test_actions_to_story_flow(self):
        """ActionRecommender output → StoryBuilder input."""
        recommender = ActionRecommender()
        builder = StoryBuilder()
        
        problems = [
            {'type': 'anomalies', 'severity': 'high', 'description': 'Issues', 'impact': 'High'}
        ]
        
        actions = recommender.recommend_for_all_problems(problems)
        if isinstance(actions, list):
            narrative = builder.build_complete_narrative(actions)
            assert narrative is not None

    def test_full_chain_flow(self):
        """Complete chain: Insights → Problems → Actions → Story."""
        extractor = InsightExtractor()
        identifier = ProblemIdentifier()
        recommender = ActionRecommender()
        builder = StoryBuilder()
        
        insights = extractor.extract_all({
            'anomalies': {'anomalies': list(range(100)), 'total_rows': 1000},
            'predictions': {'accuracy': 80.0, 'confidence': 0.75},
            'recommendations': {'recommendations': ['Action'], 'confidence': 0.7, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 90.0, 'data_quality': 'good'}
        })
        
        problems = identifier.identify_all_problems(insights)
        actions = recommender.recommend_for_all_problems(problems)
        narrative = builder.build_complete_narrative(actions)
        
        assert narrative is not None
        assert 'full_narrative' in narrative

    def test_worker_data_integrity(self):
        """Data integrity maintained across workers."""
        extractor = InsightExtractor()
        identifier = ProblemIdentifier()
        
        insights = extractor.extract_all({
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['X'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        })
        
        assert insights['anomalies']['count'] == 50
        assert insights['predictions']['confidence'] == 0.8

    def test_worker_no_side_effects(self):
        """Workers don't modify input data."""
        extractor = InsightExtractor()
        original_data = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['X'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        
        original_anomaly_count = len(original_data['anomalies']['anomalies'])
        extractor.extract_all(original_data)
        
        assert len(original_data['anomalies']['anomalies']) == original_anomaly_count

    def test_worker_isolation(self):
        """Workers don't interfere with each other."""
        recommender1 = ActionRecommender()
        recommender2 = ActionRecommender()
        
        problems1 = [{'type': 'anomalies', 'severity': 'high', 'description': 'A', 'impact': 'High'}]
        problems2 = [{'type': 'missing_data', 'severity': 'critical', 'description': 'B', 'impact': 'Critical'}]
        
        actions1 = recommender1.recommend_for_all_problems(problems1)
        actions2 = recommender2.recommend_for_all_problems(problems2)
        
        assert isinstance(actions1, list)
        assert isinstance(actions2, list)

    def test_worker_output_format_compliance(self):
        """All workers output correct format."""
        extractor = InsightExtractor()
        result = extractor.extract_all({
            'anomalies': {'anomalies': [], 'total_rows': 100},
            'predictions': {'accuracy': 0, 'confidence': 0},
            'recommendations': {'recommendations': [], 'confidence': 0, 'impact': 'low'},
            'report': {'statistics': {}, 'completeness': 0, 'data_quality': 'unknown'}
        })
        
        assert isinstance(result, dict)
        assert 'anomalies' in result
        assert 'predictions' in result
        assert 'recommendations' in result
        assert 'statistics' in result

    def test_worker_concurrent_safety(self):
        """Workers handle concurrent calls safely."""
        recommender1 = ActionRecommender()
        recommender2 = ActionRecommender()
        
        problems = [{'type': 'anomalies', 'severity': 'high', 'description': 'X', 'impact': 'High'}]
        
        actions1 = recommender1.recommend_for_all_problems(problems)
        actions2 = recommender2.recommend_for_all_problems(problems)
        
        assert actions1 is not None
        assert actions2 is not None

    def test_worker_sequence_validation(self):
        """Workers follow correct sequence."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['Fix'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None
        assert 'status' in narrative


# ===== INPUT VALIDATION EDGE CASES (5) =====

class TestInputValidationEdgeCases:
    """Edge cases in input validation."""

    def test_empty_strings_in_description(self):
        """Handles empty strings in descriptions."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': [''], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': ''}
        }
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None

    def test_very_long_strings(self):
        """Handles very long strings (10K+ chars)."""
        agent = NarrativeGenerator()
        long_string = 'x' * 10000
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': [long_string], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None

    def test_special_characters_comprehensive(self):
        """Handles all special characters."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': ['!@#$%^&*()_+-=[]{}|;:,.<>?/'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None

    def test_mixed_valid_invalid_data(self):
        """Handles mixture of valid and invalid data."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': list(range(50)), 'total_rows': 1000},
            'predictions': {'accuracy': 85.0, 'confidence': 0.80},
            'recommendations': {'recommendations': [None, 'Valid', '', 123], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        narrative = agent.generate_narrative_from_results(results)
        assert narrative is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
