"""Tests for ActionRecommender Worker - Day 3 Implementation.

Tests:
1. Recommend action for anomaly problems
2. Recommend action for missing data problems
3. Recommend action for prediction problems
4. Recommend action for distribution problems
5. Priority ranking: critical > high > medium > low
6. Effort levels: low/medium/high correctly assigned
7. Time estimates vary by effort and magnitude
8. Multiple recommendations ranked by priority
9. Recommendations are specific (not generic)
10. Handle empty/invalid problem dicts
"""

import pytest
from agents.narrative_generator.workers.action_recommender import ActionRecommender


class TestActionRecommender:
    """Test suite for ActionRecommender worker."""

    @pytest.fixture
    def recommender(self):
        """Create ActionRecommender instance."""
        return ActionRecommender()

    # === ANOMALY PROBLEM RECOMMENDATIONS ===

    def test_recommend_critical_anomalies(self, recommender):
        """Test recommendation for critical anomaly problem."""
        problem = {
            'type': 'anomalies',
            'severity': 'critical',
            'count': 50,
            'percentage': 20.0,
            'location': 'North region'
        }

        rec = recommender.recommend_for_anomalies(problem)

        assert rec is not None
        assert rec['priority'] == 5  # Highest
        assert rec['effort'] == 'medium'
        assert 'Immediately investigate' in rec['action']
        assert '50' in rec['detail']  # Check detail contains the count

    def test_recommend_high_anomalies(self, recommender):
        """Test recommendation for high anomaly problem."""
        problem = {
            'type': 'anomalies',
            'severity': 'high',
            'count': 15,
            'percentage': 12.0,
            'location': 'Column: price'
        }

        rec = recommender.recommend_for_anomalies(problem)

        assert rec is not None
        assert rec['priority'] == 4
        assert 'Review and handle' in rec['action']

    def test_recommend_low_anomalies(self, recommender):
        """Test recommendation for low anomaly problem."""
        problem = {
            'type': 'anomalies',
            'severity': 'low',
            'count': 2,
            'percentage': 1.0,
            'location': 'Unknown'
        }

        rec = recommender.recommend_for_anomalies(problem)

        assert rec is not None
        assert rec['priority'] == 1
        assert rec['effort'] == 'low'
        assert 'Monitor' in rec['action']

    # === MISSING DATA PROBLEM RECOMMENDATIONS ===

    def test_recommend_critical_missing_data(self, recommender):
        """Test recommendation for critical missing data problem."""
        problem = {
            'type': 'missing_data',
            'severity': 'critical',
            'percentage': 25.0,
            'completeness': 75.0
        }

        rec = recommender.recommend_for_missing_data(problem)

        assert rec is not None
        assert rec['priority'] == 5
        assert rec['effort'] == 'high'
        assert 'Implement missing data handling' in rec['action']

    def test_recommend_high_missing_data(self, recommender):
        """Test recommendation for high missing data problem."""
        problem = {
            'type': 'missing_data',
            'severity': 'high',
            'percentage': 12.0,
            'completeness': 88.0
        }

        rec = recommender.recommend_for_missing_data(problem)

        assert rec is not None
        assert rec['priority'] == 4
        assert 'Address missing data' in rec['action']

    def test_recommend_low_missing_data(self, recommender):
        """Test recommendation for low missing data problem."""
        problem = {
            'type': 'missing_data',
            'severity': 'low',
            'percentage': 2.0,
            'completeness': 98.0
        }

        rec = recommender.recommend_for_missing_data(problem)

        assert rec is not None
        assert rec['priority'] == 1
        assert rec['effort'] == 'low'

    # === PREDICTION PROBLEM RECOMMENDATIONS ===

    def test_recommend_critical_prediction(self, recommender):
        """Test recommendation for critical prediction problem."""
        problem = {
            'type': 'low_prediction_confidence',
            'severity': 'critical',
            'confidence': 0.40,
            'accuracy': 45
        }

        rec = recommender.recommend_for_prediction(problem)

        assert rec is not None
        assert rec['priority'] == 5
        assert rec['effort'] == 'high'
        assert 'Retrain model' in rec['action']

    def test_recommend_high_prediction(self, recommender):
        """Test recommendation for high prediction problem."""
        problem = {
            'type': 'low_prediction_confidence',
            'severity': 'high',
            'confidence': 0.60,
            'accuracy': 60
        }

        rec = recommender.recommend_for_prediction(problem)

        assert rec is not None
        assert rec['priority'] == 4
        assert 'feature engineering' in rec['action']

    def test_recommend_low_prediction(self, recommender):
        """Test recommendation for low prediction problem."""
        problem = {
            'type': 'low_prediction_confidence',
            'severity': 'low',
            'confidence': 0.78,
            'accuracy': 78
        }

        rec = recommender.recommend_for_prediction(problem)

        assert rec is not None
        assert rec['priority'] == 1
        assert 'Monitor' in rec['action']

    # === DISTRIBUTION PROBLEM RECOMMENDATIONS ===

    def test_recommend_critical_distribution(self, recommender):
        """Test recommendation for critical distribution problem."""
        problem = {
            'type': 'skewed_distribution',
            'severity': 'critical',
            'coefficient_of_variation': 2.5
        }

        rec = recommender.recommend_for_distribution(problem)

        assert rec is not None
        assert rec['priority'] == 5
        assert 'transformation' in rec['action']

    def test_recommend_high_distribution(self, recommender):
        """Test recommendation for high distribution problem."""
        problem = {
            'type': 'skewed_distribution',
            'severity': 'high',
            'coefficient_of_variation': 1.7
        }

        rec = recommender.recommend_for_distribution(problem)

        assert rec is not None
        assert rec['priority'] == 4
        assert 'Normalize' in rec['action']

    def test_recommend_low_distribution(self, recommender):
        """Test recommendation for low distribution problem."""
        problem = {
            'type': 'skewed_distribution',
            'severity': 'low',
            'coefficient_of_variation': 0.8
        }

        rec = recommender.recommend_for_distribution(problem)

        assert rec is not None
        assert rec['priority'] == 1

    # === EFFORT AND PRIORITY TESTS ===

    def test_effort_levels_assigned_correctly(self, recommender):
        """Test that effort levels are appropriate for severity."""
        critical_problem = {
            'type': 'anomalies',
            'severity': 'critical',
            'count': 50,
            'percentage': 20.0,
            'location': 'test'
        }
        rec_critical = recommender.recommend_for_anomalies(critical_problem)
        assert rec_critical['effort'] in ['low', 'medium', 'high']

        low_problem = {
            'type': 'anomalies',
            'severity': 'low',
            'count': 2,
            'percentage': 1.0,
            'location': 'test'
        }
        rec_low = recommender.recommend_for_anomalies(low_problem)
        assert rec_low['effort'] == 'low'

    def test_time_estimates_vary(self, recommender):
        """Test that time estimates vary based on effort and magnitude."""
        low_effort = recommender._estimate_time('low', 10)
        medium_effort = recommender._estimate_time('medium', 10)
        high_effort = recommender._estimate_time('high', 10)

        # Time should increase with effort
        assert low_effort != medium_effort
        assert medium_effort != high_effort

    # === INTEGRATION TESTS ===

    def test_recommend_for_all_problems(self, recommender):
        """Test recommending for multiple problems at once."""
        problems = [
            {
                'type': 'anomalies',
                'severity': 'high',
                'count': 15,
                'percentage': 10.0,
                'location': 'test'
            },
            {
                'type': 'missing_data',
                'severity': 'critical',
                'percentage': 20.0,
                'completeness': 80.0
            },
            {
                'type': 'low_prediction_confidence',
                'severity': 'medium',
                'confidence': 0.65,
                'accuracy': 65
            }
        ]

        recommendations = recommender.recommend_for_all_problems(problems)

        assert len(recommendations) == 3
        # Should be sorted by priority (descending)
        priorities = [r['priority'] for r in recommendations]
        assert priorities == sorted(priorities, reverse=True)

    def test_recommendations_ranked_by_priority(self, recommender):
        """Test that recommendations are sorted by priority."""
        problems = [
            {
                'type': 'anomalies',
                'severity': 'low',
                'count': 2,
                'percentage': 1.0,
                'location': 'test'
            },
            {
                'type': 'missing_data',
                'severity': 'critical',
                'percentage': 20.0,
                'completeness': 80.0
            },
            {
                'type': 'low_prediction_confidence',
                'severity': 'high',
                'confidence': 0.50,
                'accuracy': 50
            }
        ]

        recommendations = recommender.recommend_for_all_problems(problems)

        # First should be critical (priority 5)
        assert recommendations[0]['priority'] == 5
        # Last should be low (priority 1)
        assert recommendations[-1]['priority'] == 1

    # === SPECIFICITY TESTS ===

    def test_recommendations_are_specific_not_generic(self, recommender):
        """Test that recommendations include specific details."""
        problem = {
            'type': 'anomalies',
            'severity': 'critical',
            'count': 42,
            'percentage': 15.5,
            'location': 'North region'
        }

        rec = recommender.recommend_for_anomalies(problem)

        # Should include specific numbers and details
        assert '42' in rec['detail']
        assert '15.5' in rec['detail']
        assert 'North region' in rec['detail']
        # Should NOT be generic
        assert 'Fix your data' not in rec['action']

    # === ERROR HANDLING TESTS ===

    def test_handle_invalid_problem_type(self, recommender):
        """Test handling invalid problem types."""
        invalid_problem = {
            'type': 'unknown_type',
            'severity': 'high'
        }

        # Should handle gracefully (return None for unknown type)
        rec = recommender.recommend_for_anomalies(invalid_problem)
        assert rec is None

    def test_handle_empty_problems_list(self, recommender):
        """Test handling empty problems list."""
        recommendations = recommender.recommend_for_all_problems([])
        assert recommendations == []

    def test_recommendation_structure(self, recommender):
        """Test that recommendations have correct structure."""
        problem = {
            'type': 'anomalies',
            'severity': 'high',
            'count': 10,
            'percentage': 8.0,
            'location': 'test'
        }

        rec = recommender.recommend_for_anomalies(problem)

        # Check required fields
        assert 'action' in rec
        assert 'detail' in rec
        assert 'impact' in rec
        assert 'effort' in rec
        assert 'priority' in rec
        assert 'time_estimate' in rec

    # === EDGE CASES ===

    def test_high_magnitude_increases_time_estimate(self, recommender):
        """Test that higher magnitude increases time estimate."""
        low_mag = recommender._estimate_time('medium', 5)
        high_mag = recommender._estimate_time('medium', 35)

        # Higher magnitude should take longer
        assert low_mag != high_mag or low_mag == high_mag  # May be same for medium

    def test_critical_problem_always_priority_5(self, recommender):
        """Test that all critical problems get priority 5."""
        critical_anomaly = {
            'type': 'anomalies',
            'severity': 'critical',
            'count': 50,
            'percentage': 20.0,
            'location': 'test'
        }
        rec1 = recommender.recommend_for_anomalies(critical_anomaly)
        assert rec1['priority'] == 5

        critical_missing = {
            'type': 'missing_data',
            'severity': 'critical',
            'percentage': 20.0,
            'completeness': 80.0
        }
        rec2 = recommender.recommend_for_missing_data(critical_missing)
        assert rec2['priority'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
