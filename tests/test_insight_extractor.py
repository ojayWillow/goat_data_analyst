"""Tests for InsightExtractor Worker - Day 1 Implementation.

Tests:
1. Extract key anomalies from results
2. Calculate anomaly percentage
3. Extract prediction accuracy
4. Extract feature importance
5. Extract top 3 recommendations
6. Score insight importance
7. Handle missing results gracefully
8. Validate scores on 0-1 scale
9. Extract all insights together
10. Handle malformed input
"""

import pytest
from agents.narrative_generator.workers.insight_extractor import InsightExtractor
from core.exceptions import AgentError


class TestInsightExtractor:
    """Test suite for InsightExtractor worker."""

    @pytest.fixture
    def extractor(self):
        """Create InsightExtractor instance."""
        return InsightExtractor()

    # === ANOMALY TESTS ===

    def test_extract_key_anomalies(self, extractor):
        """Test extracting key anomalies from results."""
        anomaly_results = {
            'anomalies': ['row_5', 'row_12', 'row_23'],
            'total_rows': 100,
            'top_anomalies': ['row_5', 'row_12', 'row_23']
        }

        insights = extractor.extract_anomalies(anomaly_results)

        assert insights['count'] == 3
        assert insights['percentage'] == 3.0
        assert insights['severity'] == 'low'
        assert len(insights['top_anomalies']) <= 3

    def test_calculate_anomaly_percentage(self, extractor):
        """Test anomaly percentage calculation."""
        # 10 anomalies out of 100 rows = 10%
        anomaly_results = {
            'anomalies': ['row_' + str(i) for i in range(10)],
            'total_rows': 100,
            'top_anomalies': ['row_0', 'row_1', 'row_2']
        }

        insights = extractor.extract_anomalies(anomaly_results)

        assert insights['percentage'] == 10.0
        assert insights['severity'] == 'medium'
        assert insights['importance'] == 0.6

    def test_anomaly_severity_high(self, extractor):
        """Test high severity anomalies (>10%)."""
        anomaly_results = {
            'anomalies': ['row_' + str(i) for i in range(15)],
            'total_rows': 100,
            'top_anomalies': []
        }

        insights = extractor.extract_anomalies(anomaly_results)

        assert insights['severity'] == 'high'
        assert insights['importance'] == 0.9

    def test_no_anomalies(self, extractor):
        """Test handling when no anomalies found."""
        anomaly_results = {
            'anomalies': [],
            'total_rows': 100
        }

        insights = extractor.extract_anomalies(anomaly_results)

        assert insights['count'] == 0
        assert insights['severity'] == 'none'
        assert insights['importance'] == 0

    # === PREDICTION TESTS ===

    def test_extract_prediction_accuracy(self, extractor):
        """Test extracting prediction accuracy."""
        prediction_results = {
            'accuracy': 87.5,
            'confidence': 0.92,
            'top_features': ['feature_1', 'feature_2', 'feature_3'],
            'trend': 'increasing'
        }

        insights = extractor.extract_predictions(prediction_results)

        assert insights['accuracy'] == 87.5
        assert insights['confidence'] == 0.92
        assert len(insights['top_features']) == 3

    def test_extract_feature_importance(self, extractor):
        """Test extracting top features."""
        prediction_results = {
            'accuracy': 85,
            'confidence': 0.85,
            'top_features': ['age', 'income', 'score', 'rating', 'level'],
            'trend': 'stable'
        }

        insights = extractor.extract_predictions(prediction_results)

        assert len(insights['top_features']) == 3
        assert insights['top_features'][0] == 'age'
        assert insights['top_features'][2] == 'score'

    def test_prediction_importance_scoring(self, extractor):
        """Test importance scoring based on confidence."""
        # High confidence
        high_conf = extractor.extract_predictions({
            'accuracy': 90,
            'confidence': 0.95
        })
        assert high_conf['importance'] == 0.9

        # Medium confidence
        med_conf = extractor.extract_predictions({
            'accuracy': 75,
            'confidence': 0.75
        })
        assert med_conf['importance'] == 0.7

        # Low confidence
        low_conf = extractor.extract_predictions({
            'accuracy': 50,
            'confidence': 0.40
        })
        assert low_conf['importance'] == 0.2

    def test_confidence_clamping(self, extractor):
        """Test that confidence is clamped to 0-1."""
        prediction_results = {
            'accuracy': 120,  # Over 100
            'confidence': 1.5  # Over 1.0
        }

        insights = extractor.extract_predictions(prediction_results)

        assert insights['accuracy'] == 100  # Clamped to 100
        assert insights['confidence'] == 1.0  # Clamped to 1.0

    # === RECOMMENDATION TESTS ===

    def test_extract_top_3_recommendations(self, extractor):
        """Test extracting top 3 recommendations."""
        rec_results = {
            'recommendations': [
                'Fix missing data',
                'Remove outliers',
                'Scale features',
                'Engineer features',
                'Handle imbalance'
            ],
            'confidence': 0.85,
            'impact': 'high'
        }

        insights = extractor.extract_recommendations(rec_results)

        assert len(insights['top_3_actions']) == 3
        assert insights['top_3_actions'][0] == 'Fix missing data'
        assert insights['count'] == 5

    def test_recommendation_importance_from_impact(self, extractor):
        """Test importance scoring from impact level."""
        # High impact
        high = extractor.extract_recommendations({
            'recommendations': ['action'],
            'confidence': 0.8,
            'impact': 'high'
        })
        assert high['importance'] == 0.9

        # Medium impact
        med = extractor.extract_recommendations({
            'recommendations': ['action'],
            'confidence': 0.8,
            'impact': 'medium'
        })
        assert med['importance'] == 0.6

        # Low impact
        low = extractor.extract_recommendations({
            'recommendations': ['action'],
            'confidence': 0.8,
            'impact': 'low'
        })
        assert low['importance'] == 0.3

    # === STATISTICS TESTS ===

    def test_extract_statistics(self, extractor):
        """Test extracting key statistics."""
        report_results = {
            'statistics': {
                'rows': 10000,
                'columns': 25,
                'missing_percentage': 3.2,
                'mean': 45.5,
                'median': 42.0,
                'std': 12.3
            },
            'completeness': 96.8,
            'data_quality': 'good'
        }

        insights = extractor.extract_statistics(report_results)

        assert len(insights['key_statistics']) > 0
        assert insights['completeness'] == 96.8
        assert insights['data_quality'] == 'good'

    # === INTEGRATION TESTS ===

    def test_extract_all_insights(self, extractor):
        """Test extracting all insights together."""
        agent_results = {
            'anomalies': {
                'anomalies': ['row_1', 'row_2'],
                'total_rows': 100
            },
            'predictions': {
                'accuracy': 85,
                'confidence': 0.85,
                'top_features': ['f1', 'f2']
            },
            'recommendations': {
                'recommendations': ['action1', 'action2'],
                'confidence': 0.8,
                'impact': 'high'
            },
            'report': {
                'statistics': {'rows': 100},
                'completeness': 95
            }
        }

        all_insights = extractor.extract_all(agent_results)

        assert 'anomalies' in all_insights
        assert 'predictions' in all_insights
        assert 'recommendations' in all_insights
        assert 'statistics' in all_insights
        assert 'overall_importance' in all_insights

    def test_overall_importance_calculation(self, extractor):
        """Test overall importance is average of all insights."""
        agent_results = {
            'anomalies': {'anomalies': [], 'total_rows': 100},
            'predictions': {'accuracy': 90, 'confidence': 0.9},
            'recommendations': {'recommendations': [], 'confidence': 0.8, 'impact': 'high'},
            'report': {'statistics': {}}
        }

        all_insights = extractor.extract_all(agent_results)

        # Overall should be average of 4 insights
        assert 'overall_importance' in all_insights
        assert 0 <= all_insights['overall_importance'] <= 1

    # === ERROR HANDLING TESTS ===

    def test_handle_missing_results_gracefully(self, extractor):
        """Test graceful handling of missing result types."""
        # Empty results
        insights = extractor.extract_anomalies({})
        assert insights['count'] == 0
        assert insights['severity'] == 'none'

        # None results
        insights = extractor.extract_predictions(None)
        assert insights['accuracy'] == 0
        assert insights['confidence'] == 0

        # Malformed results
        insights = extractor.extract_recommendations("not a dict")
        assert insights['top_3_actions'] == []
        assert insights['count'] == 0

    def test_validate_importance_scale(self, extractor):
        """Test that all importance scores are 0-1."""
        agent_results = {
            'anomalies': {'anomalies': ['a', 'b'], 'total_rows': 50},
            'predictions': {'accuracy': 95, 'confidence': 0.99},
            'recommendations': {'recommendations': ['x'], 'confidence': 0.7, 'impact': 'high'},
            'report': {'statistics': {'rows': 100}, 'completeness': 99}
        }

        all_insights = extractor.extract_all(agent_results)

        # Check all importance scores are 0-1
        for key, insight in all_insights.items():
            if isinstance(insight, dict) and 'importance' in insight:
                assert 0 <= insight['importance'] <= 1, f"Invalid importance in {key}: {insight['importance']}"

    def test_handle_zero_rows(self, extractor):
        """Test handling edge case of zero total rows."""
        anomaly_results = {
            'anomalies': ['row_1'],
            'total_rows': 0
        }

        insights = extractor.extract_anomalies(anomaly_results)

        # Should handle gracefully
        assert 'percentage' in insights
        assert insights['percentage'] >= 0

    def test_empty_agent_results(self, extractor):
        """Test handling completely empty agent results."""
        all_insights = extractor.extract_all({})

        assert 'anomalies' in all_insights
        assert 'predictions' in all_insights
        assert 'recommendations' in all_insights
        assert 'statistics' in all_insights
        assert 'overall_importance' in all_insights


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
