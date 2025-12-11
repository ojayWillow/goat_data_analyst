"""InsightExtractor Worker - Day 1 Implementation.

Extracts key insights from raw agent results:
- Anomaly detection insights (count, severity, %)
- Prediction insights (accuracy, confidence, features)
- Recommendation insights (top 3 actions)
- Report insights (statistics)

Scores importance of each insight (0-1 scale).
"""

from typing import Any, Dict, Optional, List
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError


class InsightExtractor:
    """Extracts key findings from agent results.
    
    Takes raw results and pulls:
    - Anomalies: count, severity, percentage
    - Predictions: accuracy, confidence, top features
    - Recommendations: top 3 actions
    - Statistics: key metrics
    
    All insights scored 0-1 for importance.
    """

    def __init__(self) -> None:
        """Initialize the InsightExtractor worker."""
        self.name = "InsightExtractor"
        self.logger = get_logger("InsightExtractor")
        self.structured_logger = get_structured_logger("InsightExtractor")
        self.logger.info("InsightExtractor worker initialized")

    def extract_anomalies(self, anomaly_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key anomaly insights.
        
        Args:
            anomaly_results: Results from AnomalyDetector agent
                           Expected keys: anomalies, ensemble_method, etc.
        
        Returns:
            Dictionary with:
            - count: Number of anomalies found
            - severity: low/medium/high based on percentage
            - percentage: % of data that are anomalies
            - importance: 0-1 score
            - top_anomalies: Top 3 anomalies by severity
        
        Raises:
            AgentError: If anomaly_results malformed
        """
        try:
            if not anomaly_results or not isinstance(anomaly_results, dict):
                return self._no_anomaly_insights()

            # Extract anomaly count
            anomalies = anomaly_results.get('anomalies', [])
            if isinstance(anomalies, list):
                count = len(anomalies)
            elif isinstance(anomalies, dict):
                count = anomalies.get('count', 0)
            else:
                count = 0

            # Extract total rows to calculate percentage
            total_rows = anomaly_results.get('total_rows', 1)
            if total_rows == 0:
                total_rows = 1

            percentage = (count / total_rows) * 100 if total_rows > 0 else 0

            # Determine severity
            if percentage > 10:
                severity = "high"
                importance = 0.9
            elif percentage > 5:
                severity = "medium"
                importance = 0.6
            elif percentage > 0:
                severity = "low"
                importance = 0.3
            else:
                return self._no_anomaly_insights()

            # Top anomalies
            top_anomalies = anomaly_results.get('top_anomalies', [])[:3]

            insight = {
                'count': count,
                'severity': severity,
                'percentage': round(percentage, 2),
                'importance': importance,
                'top_anomalies': top_anomalies,
                'total_rows': total_rows
            }

            self.logger.info(f"Anomaly insights extracted: {count} anomalies ({percentage:.2f}%)")
            self.structured_logger.info("Anomaly insights extracted", insight)

            return insight

        except Exception as e:
            self.logger.error(f"Error extracting anomaly insights: {e}")
            raise AgentError(f"Failed to extract anomaly insights: {e}")

    def extract_predictions(self, prediction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key prediction insights.
        
        Args:
            prediction_results: Results from Predictor agent
                              Expected keys: accuracy, confidence, features, etc.
        
        Returns:
            Dictionary with:
            - accuracy: Model accuracy (0-100)
            - confidence: Confidence in predictions (0-1)
            - top_features: Top 3 important features
            - trend: Trend in predictions
            - importance: 0-1 score
        
        Raises:
            AgentError: If prediction_results malformed
        """
        try:
            if not prediction_results or not isinstance(prediction_results, dict):
                return self._no_prediction_insights()

            # Extract accuracy
            accuracy = prediction_results.get('accuracy', 0)
            if isinstance(accuracy, (int, float)):
                accuracy = min(max(accuracy, 0), 100)  # Clamp 0-100
            else:
                accuracy = 0

            # Extract confidence
            confidence = prediction_results.get('confidence', 0)
            if isinstance(confidence, (int, float)):
                confidence = min(max(confidence, 0), 1)  # Clamp 0-1
            else:
                confidence = 0

            # Determine importance based on confidence
            if confidence >= 0.85:
                importance = 0.9
            elif confidence >= 0.70:
                importance = 0.7
            elif confidence >= 0.50:
                importance = 0.5
            else:
                importance = 0.2

            # Extract features
            features = prediction_results.get('top_features', [])
            top_features = features[:3] if isinstance(features, list) else []

            # Extract trend
            trend = prediction_results.get('trend', 'stable')

            insight = {
                'accuracy': round(accuracy, 2),
                'confidence': round(confidence, 2),
                'top_features': top_features,
                'trend': trend,
                'importance': importance,
                'model_type': prediction_results.get('model_type', 'unknown')
            }

            self.logger.info(f"Prediction insights extracted: {accuracy:.1f}% accuracy, {confidence:.1f} confidence")
            self.structured_logger.info("Prediction insights extracted", insight)

            return insight

        except Exception as e:
            self.logger.error(f"Error extracting prediction insights: {e}")
            raise AgentError(f"Failed to extract prediction insights: {e}")

    def extract_recommendations(self, recommendation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key recommendation insights.
        
        Args:
            recommendation_results: Results from Recommender agent
                                  Expected keys: recommendations, confidence, etc.
        
        Returns:
            Dictionary with:
            - top_3_actions: Top 3 recommendations
            - confidence: Confidence in recommendations (0-1)
            - impact: Expected impact level
            - importance: 0-1 score
        
        Raises:
            AgentError: If recommendation_results malformed
        """
        try:
            if not recommendation_results or not isinstance(recommendation_results, dict):
                return self._no_recommendation_insights()

            # Extract recommendations
            recommendations = recommendation_results.get('recommendations', [])
            if not isinstance(recommendations, list):
                recommendations = []

            top_3_actions = recommendations[:3]

            # Extract confidence
            confidence = recommendation_results.get('confidence', 0.5)
            if isinstance(confidence, (int, float)):
                confidence = min(max(confidence, 0), 1)
            else:
                confidence = 0.5

            # Extract impact
            impact = recommendation_results.get('impact', 'medium')
            impact_score = {
                'high': 0.9,
                'medium': 0.6,
                'low': 0.3
            }.get(str(impact).lower(), 0.5)

            insight = {
                'top_3_actions': top_3_actions,
                'confidence': round(confidence, 2),
                'impact': impact,
                'importance': impact_score,
                'count': len(recommendations)
            }

            self.logger.info(f"Recommendation insights extracted: {len(top_3_actions)} top actions")
            self.structured_logger.info("Recommendation insights extracted", insight)

            return insight

        except Exception as e:
            self.logger.error(f"Error extracting recommendation insights: {e}")
            raise AgentError(f"Failed to extract recommendation insights: {e}")

    def extract_statistics(self, report_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key statistics from report.
        
        Args:
            report_results: Results from Reporter agent
                          Expected keys: statistics, metrics, etc.
        
        Returns:
            Dictionary with key statistics and importance score
        
        Raises:
            AgentError: If report_results malformed
        """
        try:
            if not report_results or not isinstance(report_results, dict):
                return self._no_statistics_insights()

            # Extract key statistics
            statistics = report_results.get('statistics', {})
            if not isinstance(statistics, dict):
                statistics = {}

            # Key metrics to extract
            key_stats = {}
            for key in ['rows', 'columns', 'missing_percentage', 'mean', 'median', 'std']:
                if key in statistics:
                    key_stats[key] = statistics[key]

            insight = {
                'key_statistics': key_stats,
                'completeness': statistics.get('completeness', 100),
                'data_quality': statistics.get('data_quality', 'unknown'),
                'importance': 0.5  # Statistics are context
            }

            self.logger.info(f"Statistics extracted: {len(key_stats)} key metrics")
            self.structured_logger.info("Statistics extracted", insight)

            return insight

        except Exception as e:
            self.logger.error(f"Error extracting statistics: {e}")
            raise AgentError(f"Failed to extract statistics: {e}")

    def extract_all(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all insights from complete agent results.
        
        Args:
            agent_results: Dictionary with all agent results
                         Expected keys: anomalies, predictions, recommendations, report
        
        Returns:
            Dictionary with all insights organized by type
        """
        self.logger.info("Starting comprehensive insight extraction")

        all_insights = {
            'anomalies': self.extract_anomalies(agent_results.get('anomalies', {})),
            'predictions': self.extract_predictions(agent_results.get('predictions', {})),
            'recommendations': self.extract_recommendations(agent_results.get('recommendations', {})),
            'statistics': self.extract_statistics(agent_results.get('report', {}))
        }

        # Calculate overall importance
        total_importance = sum(
            v.get('importance', 0) for v in all_insights.values()
            if isinstance(v, dict)
        )
        avg_importance = total_importance / len(all_insights) if all_insights else 0
        all_insights['overall_importance'] = round(avg_importance, 2)

        self.logger.info(f"Insight extraction complete. Overall importance: {avg_importance:.2f}")
        self.structured_logger.info("Insight extraction complete", {
            'insight_types': len(all_insights),
            'overall_importance': round(avg_importance, 2)
        })

        return all_insights

    # === HELPER METHODS ===

    def _no_anomaly_insights(self) -> Dict[str, Any]:
        """Return empty anomaly insights."""
        return {
            'count': 0,
            'severity': 'none',
            'percentage': 0,
            'importance': 0,
            'top_anomalies': [],
            'total_rows': 0
        }

    def _no_prediction_insights(self) -> Dict[str, Any]:
        """Return empty prediction insights."""
        return {
            'accuracy': 0,
            'confidence': 0,
            'top_features': [],
            'trend': 'unknown',
            'importance': 0,
            'model_type': 'unknown'
        }

    def _no_recommendation_insights(self) -> Dict[str, Any]:
        """Return empty recommendation insights."""
        return {
            'top_3_actions': [],
            'confidence': 0,
            'impact': 'unknown',
            'importance': 0,
            'count': 0
        }

    def _no_statistics_insights(self) -> Dict[str, Any]:
        """Return empty statistics insights."""
        return {
            'key_statistics': {},
            'completeness': 0,
            'data_quality': 'unknown',
            'importance': 0
        }
