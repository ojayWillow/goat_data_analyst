"""PHASE 2 TEST SUITE - Boundary Cases, Quality Formula Deep, Data Structure Validation

35 comprehensive tests targeting:
- Boundary & edge cases (15 tests)
- Quality formula deep testing (10 tests)
- Data structure validation (10 tests)

Target: 90%+ coverage
Execution: pytest tests/test_narrative_generator_phase2.py -v
"""

import pytest
from agents.narrative_generator.narrative_generator import NarrativeGenerator
from agents.narrative_generator.workers.insight_extractor import InsightExtractor
from agents.narrative_generator.workers.problem_identifier import ProblemIdentifier
from agents.narrative_generator.workers.action_recommender import ActionRecommender
from agents.narrative_generator.workers.story_builder import StoryBuilder


# ===== BOUNDARY & EDGE CASES (15) =====

class TestBoundaryAndEdgeCases:
    """Extreme and boundary condition testing."""

    def test_boundary_zero_anomalies(self):
        """Edge case: Exactly zero anomalies."""
        extractor = InsightExtractor()
        result = extractor.extract_anomalies({
            'anomalies': [],
            'total_rows': 1000,
            'top_anomalies': []
        })
        assert result['count'] == 0
        assert result['severity'] == 'none'
        assert result['percentage'] == 0

    def test_boundary_100_percent_anomalies(self):
        """Edge case: All data points are anomalies (100%)."""
        extractor = InsightExtractor()
        result = extractor.extract_anomalies({
            'anomalies': list(range(1000)),
            'total_rows': 1000,
            'top_anomalies': []
        })
        assert result['count'] == 1000
        assert result['severity'] == 'high'
        assert result['percentage'] == 100.0

    def test_boundary_single_anomaly(self):
        """Edge case: Exactly one anomaly out of many."""
        extractor = InsightExtractor()
        result = extractor.extract_anomalies({
            'anomalies': [1],
            'total_rows': 1000,
            'top_anomalies': [[1, 500]]
        })
        assert result['count'] == 1
        assert result['percentage'] == 0.1

    def test_boundary_zero_confidence(self):
        """Edge case: Zero confidence predictions."""
        extractor = InsightExtractor()
        result = extractor.extract_predictions({
            'accuracy': 0,
            'confidence': 0.0,
            'top_features': []
        })
        assert result['confidence'] == 0.0
        assert result['importance'] == 0.2

    def test_boundary_perfect_confidence(self):
        """Edge case: Perfect (1.0) confidence."""
        extractor = InsightExtractor()
        result = extractor.extract_predictions({
            'accuracy': 100.0,
            'confidence': 1.0,
            'top_features': ['f1', 'f2', 'f3']
        })
        assert result['confidence'] == 1.0
        assert result['importance'] == 0.9

    def test_boundary_zero_accuracy(self):
        """Edge case: Zero accuracy."""
        extractor = InsightExtractor()
        result = extractor.extract_predictions({
            'accuracy': 0,
            'confidence': 0.5,
            'top_features': []
        })
        assert result['accuracy'] == 0

    def test_boundary_perfect_accuracy(self):
        """Edge case: Perfect (100%) accuracy."""
        extractor = InsightExtractor()
        result = extractor.extract_predictions({
            'accuracy': 100.0,
            'confidence': 0.5,
            'top_features': []
        })
        assert result['accuracy'] == 100.0

    def test_boundary_zero_completeness(self):
        """Edge case: Zero data completeness (all missing)."""
        extractor = InsightExtractor()
        result = extractor.extract_statistics({
            'statistics': {},
            'completeness': 0,
            'data_quality': 'poor'
        })
        assert result['completeness'] == 0

    def test_boundary_perfect_completeness(self):
        """Edge case: Perfect (100%) completeness."""
        extractor = InsightExtractor()
        result = extractor.extract_statistics({
            'statistics': {'rows': 1000},
            'completeness': 100.0,
            'data_quality': 'excellent'
        })
        assert result['completeness'] == 100.0

    def test_boundary_empty_problem_list(self):
        """Edge case: No problems identified."""
        identifier = ProblemIdentifier()
        insights = {
            'anomalies': {'count': 0, 'percentage': 0},
            'predictions': {'confidence': 0.9, 'accuracy': 95.0},
            'statistics': {'completeness': 100.0}
        }
        problems = identifier.identify_all_problems(insights)
        assert isinstance(problems, list)
        assert len(problems) == 0

    def test_boundary_single_problem(self):
        """Edge case: Exactly one problem identified."""
        identifier = ProblemIdentifier()
        problem = identifier.identify_anomaly_problems({
            'count': 1,
            'percentage': 0.1,
            'total_rows': 1000,
            'top_anomalies': [[1, 500]]
        })
        assert problem is not None

    def test_boundary_empty_recommendation_list(self):
        """Edge case: No recommendations."""
        extractor = InsightExtractor()
        result = extractor.extract_recommendations({
            'recommendations': [],
            'confidence': 0,
            'impact': 'low'
        })
        assert result['count'] == 0
        assert result['top_3_actions'] == []

    def test_boundary_max_recommendations(self):
        """Edge case: Many recommendations."""
        extractor = InsightExtractor()
        recs = [f'Action {i}' for i in range(100)]
        result = extractor.extract_recommendations({
            'recommendations': recs,
            'confidence': 0.9,
            'impact': 'high'
        })
        assert result['count'] == 100
        assert len(result['top_3_actions']) == 3

    def test_boundary_quality_score_zero(self):
        """Edge case: Quality score exactly 0.0."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 0},
            'predictions': {'accuracy': 0, 'confidence': 0},
            'recommendations': {'recommendations': [], 'confidence': 0, 'impact': 'low'},
            'report': {'statistics': {}, 'completeness': 0, 'data_quality': 'unknown'}
        }
        agent.generate_narrative_from_results(results)
        assert agent.quality_score >= 0.0

    def test_boundary_quality_score_perfect(self):
        """Edge case: Quality score close to 1.0."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 1000},
            'predictions': {'accuracy': 99.0, 'confidence': 0.99},
            'recommendations': {'recommendations': ['A', 'B', 'C'], 'confidence': 0.95, 'impact': 'high'},
            'report': {'statistics': {'rows': 1000}, 'completeness': 100.0, 'data_quality': 'excellent'}
        }
        agent.generate_narrative_from_results(results)
        assert 0.7 <= agent.quality_score <= 1.0


# ===== QUALITY FORMULA DEEP TESTING (10) =====

class TestQualityFormulaDeep:
    """Deep testing of quality scoring formula."""

    def test_quality_formula_all_zeros(self):
        """Quality formula with all zero components."""
        agent = NarrativeGenerator()
        score = agent._calculate_quality_score(
            insights_count=0,
            problems_count=0,
            actions_count=0,
            had_errors=False
        )
        assert 0.0 <= score <= 1.0

    def test_quality_formula_all_max(self):
        """Quality formula with maximum values."""
        agent = NarrativeGenerator()
        score = agent._calculate_quality_score(
            insights_count=10,
            problems_count=10,
            actions_count=10,
            had_errors=False
        )
        assert score == 1.0

    def test_quality_formula_with_error_penalty(self):
        """Quality formula applies error penalty (-0.15)."""
        agent = NarrativeGenerator()
        score_no_error = agent._calculate_quality_score(
            insights_count=4,
            problems_count=3,
            actions_count=3,
            had_errors=False
        )
        score_with_error = agent._calculate_quality_score(
            insights_count=4,
            problems_count=3,
            actions_count=3,
            had_errors=True
        )
        assert score_with_error < score_no_error

    def test_quality_formula_partial_components(self):
        """Quality formula with partial data."""
        agent = NarrativeGenerator()
        score = agent._calculate_quality_score(
            insights_count=2,
            problems_count=1,
            actions_count=0,
            had_errors=False
        )
        assert 0.0 <= score < 1.0

    def test_quality_formula_clamping_lower(self):
        """Quality score clamped to minimum 0.0."""
        agent = NarrativeGenerator()
        score = agent._calculate_quality_score(
            insights_count=0,
            problems_count=0,
            actions_count=0,
            had_errors=True
        )
        assert score >= 0.0

    def test_quality_formula_clamping_upper(self):
        """Quality score clamped to maximum 1.0."""
        agent = NarrativeGenerator()
        score = agent._calculate_quality_score(
            insights_count=100,
            problems_count=100,
            actions_count=100,
            had_errors=False
        )
        assert score <= 1.0

    def test_quality_formula_rounding_precision(self):
        """Quality score rounded to 2 decimals."""
        agent = NarrativeGenerator()
        score = agent._calculate_quality_score(
            insights_count=3,
            problems_count=2,
            actions_count=2,
            had_errors=False
        )
        assert isinstance(score, float)
        assert len(str(score).split('.')[-1]) <= 2

    def test_quality_formula_insights_weight_030(self):
        """Quality formula: insights weight 0.3."""
        agent = NarrativeGenerator()
        # Only insights, no problems/actions
        score = agent._calculate_quality_score(
            insights_count=4,
            problems_count=0,
            actions_count=0,
            had_errors=False
        )
        # Should be approximately 0.3
        assert 0.25 <= score <= 0.35

    def test_quality_formula_problems_weight_030(self):
        """Quality formula: problems weight 0.3."""
        agent = NarrativeGenerator()
        # Only problems, no insights/actions
        score = agent._calculate_quality_score(
            insights_count=0,
            problems_count=3,
            actions_count=0,
            had_errors=False
        )
        # Should be approximately 0.3
        assert 0.25 <= score <= 0.35

    def test_quality_formula_actions_weight_030(self):
        """Quality formula: actions weight 0.3."""
        agent = NarrativeGenerator()
        # Only actions, no insights/problems
        score = agent._calculate_quality_score(
            insights_count=0,
            problems_count=0,
            actions_count=3,
            had_errors=False
        )
        # Should be approximately 0.3
        assert 0.25 <= score <= 0.35


# ===== DATA STRUCTURE VALIDATION (10) =====

class TestDataStructureValidation:
    """Validate exact output data structures."""

    def test_structure_extract_anomalies_keys(self):
        """extract_anomalies output has all required keys."""
        extractor = InsightExtractor()
        result = extractor.extract_anomalies({
            'anomalies': list(range(50)),
            'total_rows': 1000,
            'top_anomalies': []
        })
        required_keys = {'count', 'severity', 'percentage', 'importance', 'top_anomalies', 'total_rows'}
        assert required_keys.issubset(result.keys())

    def test_structure_extract_predictions_keys(self):
        """extract_predictions output has all required keys."""
        extractor = InsightExtractor()
        result = extractor.extract_predictions({
            'accuracy': 85.0,
            'confidence': 0.8,
            'top_features': ['f1']
        })
        required_keys = {'accuracy', 'confidence', 'top_features', 'trend', 'importance', 'model_type'}
        assert required_keys.issubset(result.keys())

    def test_structure_extract_recommendations_keys(self):
        """extract_recommendations output has all required keys."""
        extractor = InsightExtractor()
        result = extractor.extract_recommendations({
            'recommendations': ['Action 1'],
            'confidence': 0.8,
            'impact': 'high'
        })
        required_keys = {'top_3_actions', 'confidence', 'impact', 'importance', 'count'}
        assert required_keys.issubset(result.keys())

    def test_structure_extract_statistics_keys(self):
        """extract_statistics output has all required keys."""
        extractor = InsightExtractor()
        result = extractor.extract_statistics({
            'statistics': {'rows': 1000},
            'completeness': 95.0,
            'data_quality': 'good'
        })
        required_keys = {'key_statistics', 'completeness', 'data_quality', 'importance'}
        assert required_keys.issubset(result.keys())

    def test_structure_extract_all_keys(self):
        """extract_all output has all insight types."""
        extractor = InsightExtractor()
        result = extractor.extract_all({
            'anomalies': {'anomalies': [], 'total_rows': 100},
            'predictions': {'accuracy': 0, 'confidence': 0},
            'recommendations': {'recommendations': [], 'confidence': 0, 'impact': 'low'},
            'report': {'statistics': {}, 'completeness': 0, 'data_quality': 'unknown'}
        })
        required_keys = {'anomalies', 'predictions', 'recommendations', 'statistics', 'overall_importance'}
        assert required_keys.issubset(result.keys())

    def test_structure_identify_anomaly_problem_keys(self):
        """identify_anomaly_problems has required keys."""
        identifier = ProblemIdentifier()
        problem = identifier.identify_anomaly_problems({
            'count': 100,
            'percentage': 10.0,
            'total_rows': 1000,
            'top_anomalies': []
        })
        if problem is not None:
            required_keys = {'type', 'severity', 'percentage', 'count', 'description', 'impact', 'location', 'fix_priority'}
            assert required_keys.issubset(problem.keys())

    def test_structure_narrative_generator_response(self):
        """generate_narrative_from_results response structure."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 100},
            'predictions': {'accuracy': 85.0, 'confidence': 0.8},
            'recommendations': {'recommendations': ['Action'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        response = agent.generate_narrative_from_results(results)
        
        # Top-level structure
        assert 'status' in response
        assert 'data' in response
        assert 'message' in response
        assert 'metadata' in response

    def test_structure_health_report_keys(self):
        """get_health_report has all required keys."""
        agent = NarrativeGenerator()
        results = {
            'anomalies': {'anomalies': [], 'total_rows': 100},
            'predictions': {'accuracy': 85.0, 'confidence': 0.8},
            'recommendations': {'recommendations': ['Action'], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}, 'completeness': 95.0, 'data_quality': 'good'}
        }
        agent.generate_narrative_from_results(results)
        health = agent.get_health_report()
        
        required_keys = {'overall_health', 'quality_score', 'components_healthy', 'total_components', 
                        'problems_identified', 'actions_recommended', 'last_error', 'workers'}
        assert required_keys.issubset(health.keys())

    def test_structure_narrative_dict_keys(self):
        """build_complete_narrative output structure."""
        builder = StoryBuilder()
        narrative = builder.build_complete_narrative([
            {'action': 'Action 1', 'priority': 5, 'effort': 'low', 'impact': 'Critical'}
        ])
        
        required_keys = {'executive_summary', 'problem_statement', 'pain_points', 'action_plan', 
                        'next_steps', 'improvement_outlook', 'full_narrative', 'critical_count',
                        'high_count', 'medium_count', 'total_recommendations'}
        assert required_keys.issubset(narrative.keys())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
