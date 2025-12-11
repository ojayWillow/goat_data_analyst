"""Tests for ProblemIdentifier Worker - Day 2 Implementation.

Tests:
1. Detect anomalies as problem
2. Detect missing data as problem
3. Detect low prediction confidence as problem
4. Severity scoring: critical > high > medium > low
5. Multiple problems identified and ranked
6. Impact descriptions are helpful
7. Handle clean datasets (no problems)
8. Validate problem structure
9. Detect skewed distribution
10. Problem ranking by priority
"""

import pytest
from agents.narrative_generator.workers.problem_identifier import ProblemIdentifier, Severity


class TestProblemIdentifier:
    """Test suite for ProblemIdentifier worker."""

    @pytest.fixture
    def identifier(self):
        """Create ProblemIdentifier instance."""
        return ProblemIdentifier()

    # === ANOMALY PROBLEM TESTS ===

    def test_detect_anomalies_as_problem(self, identifier):
        """Test detecting anomalies as a problem."""
        anomaly_insights = {
            'count': 5,
            'percentage': 5.0,
            'severity': 'medium',
            'top_anomalies': ['row_1', 'row_5', 'row_10']
        }

        problem = identifier.identify_anomaly_problems(anomaly_insights)

        assert problem is not None
        assert problem['type'] == 'anomalies'
        assert problem['severity'] == 'medium'
        assert problem['count'] == 5
        assert problem['percentage'] == 5.0

    def test_no_anomaly_problem(self, identifier):
        """Test no problem when no anomalies."""
        anomaly_insights = {
            'count': 0,
            'percentage': 0,
            'severity': 'none',
            'top_anomalies': []
        }

        problem = identifier.identify_anomaly_problems(anomaly_insights)

        assert problem is None

    def test_anomaly_severity_critical(self, identifier):
        """Test critical severity for high anomaly percentage."""
        anomaly_insights = {
            'count': 20,
            'percentage': 20.0,
            'severity': 'high',
            'top_anomalies': []
        }

        problem = identifier.identify_anomaly_problems(anomaly_insights)

        assert problem is not None
        assert problem['severity'] == 'critical'
        assert problem['fix_priority'] == 4  # Highest priority

    # === MISSING DATA PROBLEM TESTS ===

    def test_detect_missing_data_as_problem(self, identifier):
        """Test detecting missing data as a problem."""
        statistics_insights = {
            'completeness': 90.0,
            'key_statistics': {},
            'data_quality': 'fair'
        }

        problem = identifier.identify_missing_data_problems(statistics_insights)

        assert problem is not None
        assert problem['type'] == 'missing_data'
        assert problem['percentage'] == 10.0  # 100 - 90
        assert problem['completeness'] == 90.0

    def test_no_missing_data_problem(self, identifier):
        """Test no problem when data is complete."""
        statistics_insights = {
            'completeness': 100.0,
            'key_statistics': {},
            'data_quality': 'excellent'
        }

        problem = identifier.identify_missing_data_problems(statistics_insights)

        assert problem is None

    def test_missing_data_severity_high(self, identifier):
        """Test high severity for significant missing data."""
        statistics_insights = {
            'completeness': 85.0,  # 15% missing
            'key_statistics': {},
            'data_quality': 'poor'
        }

        problem = identifier.identify_missing_data_problems(statistics_insights)

        assert problem is not None
        assert problem['severity'] == 'critical'  # >15%
        assert problem['percentage'] == 15.0

    # === PREDICTION PROBLEM TESTS ===

    def test_detect_low_prediction_confidence(self, identifier):
        """Test detecting low prediction confidence as problem."""
        prediction_insights = {
            'accuracy': 60,
            'confidence': 0.65,
            'top_features': [],
            'trend': 'declining'
        }

        problem = identifier.identify_prediction_problems(prediction_insights)

        assert problem is not None
        assert problem['type'] == 'low_prediction_confidence'
        assert problem['confidence'] == 0.65
        assert problem['severity'] in ['medium', 'high']

    def test_no_prediction_problem_high_confidence(self, identifier):
        """Test no problem when confidence is high."""
        prediction_insights = {
            'accuracy': 95,
            'confidence': 0.92,
            'top_features': [],
            'trend': 'stable'
        }

        problem = identifier.identify_prediction_problems(prediction_insights)

        assert problem is None

    def test_prediction_severity_critical_very_low(self, identifier):
        """Test critical severity for very low confidence."""
        prediction_insights = {
            'accuracy': 40,
            'confidence': 0.35,
            'top_features': [],
            'trend': 'declining'
        }

        problem = identifier.identify_prediction_problems(prediction_insights)

        assert problem is not None
        assert problem['severity'] == 'critical'
        assert problem['confidence'] == 0.35

    # === DISTRIBUTION PROBLEM TESTS ===

    def test_detect_skewed_distribution(self, identifier):
        """Test detecting skewed distribution as problem."""
        statistics_insights = {
            'key_statistics': {
                'mean': 100,
                'std': 150,  # High std relative to mean
                'median': 95
            },
            'completeness': 95
        }

        problem = identifier.identify_distribution_problems(statistics_insights)

        assert problem is not None
        assert problem['type'] == 'skewed_distribution'
        assert problem['coefficient_of_variation'] == 1.5

    def test_no_distribution_problem_normal(self, identifier):
        """Test no problem for normal distribution."""
        statistics_insights = {
            'key_statistics': {
                'mean': 100,
                'std': 15,  # Normal std relative to mean
                'median': 99
            },
            'completeness': 100
        }

        problem = identifier.identify_distribution_problems(statistics_insights)

        assert problem is None

    def test_extreme_distribution_problem(self, identifier):
        """Test critical severity for extreme skew."""
        statistics_insights = {
            'key_statistics': {
                'mean': 50,
                'std': 200,  # CV = 4.0 (extreme)
                'median': 30
            },
            'completeness': 90
        }

        problem = identifier.identify_distribution_problems(statistics_insights)

        assert problem is not None
        assert problem['severity'] == 'critical'
        assert problem['coefficient_of_variation'] == 4.0

    # === SEVERITY TESTS ===

    def test_severity_thresholds(self, identifier):
        """Test severity thresholds at boundaries."""
        # Test critical threshold (>15%)
        assert identifier._get_severity(16) == 'critical'
        assert identifier._get_severity(15) == 'high'
        
        # Test high threshold (>10%)
        assert identifier._get_severity(11) == 'high'
        assert identifier._get_severity(10) == 'medium'
        
        # Test medium threshold (>5%)
        assert identifier._get_severity(6) == 'medium'
        assert identifier._get_severity(5) == 'low'
        
        # Test low threshold (>0%)
        assert identifier._get_severity(1) == 'low'
        assert identifier._get_severity(0) == 'none'

    def test_severity_score(self, identifier):
        """Test severity scoring for ranking."""
        assert identifier._severity_score('critical') == 4
        assert identifier._severity_score('high') == 3
        assert identifier._severity_score('medium') == 2
        assert identifier._severity_score('low') == 1
        assert identifier._severity_score('none') == 0

    # === INTEGRATION TESTS ===

    def test_identify_multiple_problems(self, identifier):
        """Test identifying multiple problems at once."""
        all_insights = {
            'anomalies': {
                'count': 10,
                'percentage': 10.0,
                'severity': 'high',
                'top_anomalies': []
            },
            'statistics': {
                'completeness': 90.0,
                'key_statistics': {
                    'mean': 100,
                    'std': 80
                }
            },
            'predictions': {
                'accuracy': 70,
                'confidence': 0.70,
                'top_features': []
            }
        }

        problems = identifier.identify_all_problems(all_insights)

        # Should find multiple problems
        assert len(problems) > 1
        problem_types = {p['type'] for p in problems}
        assert 'anomalies' in problem_types
        assert 'missing_data' in problem_types or 'low_prediction_confidence' in problem_types

    def test_problems_ranked_by_severity(self, identifier):
        """Test that problems are ranked by severity."""
        all_insights = {
            'anomalies': {
                'count': 3,
                'percentage': 3.0,  # low
                'severity': 'low',
                'top_anomalies': []
            },
            'statistics': {
                'completeness': 80.0,  # high (20% missing)
                'key_statistics': {
                    'mean': 100,
                    'std': 50
                }
            },
            'predictions': {
                'accuracy': 50,
                'confidence': 0.50,  # high (50% confidence)
                'top_features': []
            }
        }

        problems = identifier.identify_all_problems(all_insights)

        # Problems should be sorted by fix_priority (descending)
        priorities = [p['fix_priority'] for p in problems]
        assert priorities == sorted(priorities, reverse=True)

    def test_clean_dataset_no_problems(self, identifier):
        """Test that clean dataset produces no problems."""
        all_insights = {
            'anomalies': {
                'count': 0,
                'percentage': 0,
                'severity': 'none',
                'top_anomalies': []
            },
            'statistics': {
                'completeness': 100.0,
                'key_statistics': {
                    'mean': 100,
                    'std': 15
                }
            },
            'predictions': {
                'accuracy': 95,
                'confidence': 0.95,
                'top_features': []
            }
        }

        problems = identifier.identify_all_problems(all_insights)

        assert len(problems) == 0

    def test_problem_structure_validation(self, identifier):
        """Test that problems have correct structure."""
        anomaly_insights = {
            'count': 5,
            'percentage': 5.0,
            'severity': 'medium',
            'top_anomalies': []
        }

        problem = identifier.identify_anomaly_problems(anomaly_insights)

        # Check required fields
        assert 'type' in problem
        assert 'severity' in problem
        assert 'description' in problem
        assert 'impact' in problem
        assert 'location' in problem
        assert 'fix_priority' in problem

    # === ERROR HANDLING TESTS ===

    def test_handle_empty_insights(self, identifier):
        """Test handling empty insights gracefully."""
        problem = identifier.identify_anomaly_problems({})
        assert problem is None

        problem = identifier.identify_missing_data_problems(None)
        assert problem is None

        problem = identifier.identify_prediction_problems("not a dict")
        assert problem is None

    def test_impact_descriptions_vary(self, identifier):
        """Test that impact descriptions vary by severity."""
        high_impact = identifier._describe_anomaly_impact(20, 20)
        low_impact = identifier._describe_anomaly_impact(1, 1)

        # Different severity should have different descriptions
        assert high_impact != low_impact
        assert len(high_impact) > 0
        assert len(low_impact) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
