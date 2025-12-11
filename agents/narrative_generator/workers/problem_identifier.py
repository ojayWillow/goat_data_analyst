"""ProblemIdentifier Worker - Day 2 Implementation.

Identifies and ranks problems in the data:
- Anomalies: unusual values detected
- Missing Data: incomplete information
- Low Predictions: poor model confidence
- Bad Distributions: skewed or outlier-heavy data

Problems ranked by severity:
- critical: >15% affected
- high: 10-15% affected
- medium: 5-10% affected
- low: <5% affected
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from agents.error_intelligence.main import ErrorIntelligence


class Severity(Enum):
    """Problem severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ProblemIdentifier:
    """Identifies and ranks problems in data.
    
    Takes insights and identifies:
    - Anomalies as a problem
    - Missing data as a problem
    - Low prediction confidence as a problem
    - Outlier-heavy distributions as a problem
    
    Ranks by severity and suggests priority for fixing.
    """

    def __init__(self) -> None:
        """Initialize the ProblemIdentifier worker."""
        self.name = "ProblemIdentifier"
        self.logger = get_logger("ProblemIdentifier")
        self.structured_logger = get_structured_logger("ProblemIdentifier")
        self.error_intelligence = ErrorIntelligence()
        self.logger.info("ProblemIdentifier worker initialized")
        
        # Severity thresholds
        self.severity_thresholds = {
            'critical': 15,   # >15% affected
            'high': 10,       # 10-15% affected
            'medium': 5,      # 5-10% affected
            'low': 0          # <5% affected
        }

    def _get_severity(self, percentage: float) -> str:
        """Determine severity from percentage.
        
        Args:
            percentage: Percentage of data affected (0-100)
        
        Returns:
            Severity level string
        """
        if percentage > self.severity_thresholds['critical']:
            return Severity.CRITICAL.value
        elif percentage > self.severity_thresholds['high']:
            return Severity.HIGH.value
        elif percentage > self.severity_thresholds['medium']:
            return Severity.MEDIUM.value
        elif percentage > self.severity_thresholds['low']:
            return Severity.LOW.value
        else:
            return Severity.NONE.value

    def _severity_score(self, severity: str) -> int:
        """Convert severity to numeric score for sorting.
        
        Args:
            severity: Severity level string
        
        Returns:
            Numeric score (higher = more severe)
        """
        scores = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1,
            'none': 0
        }
        return scores.get(severity, 0)

    def identify_anomaly_problems(self, anomaly_insights: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Identify problems from anomaly insights.
        
        Args:
            anomaly_insights: Insights from InsightExtractor.extract_anomalies()
        
        Returns:
            Problem dictionary or None if no problem
        """
        try:
            if not anomaly_insights or not isinstance(anomaly_insights, dict):
                return None

            percentage = anomaly_insights.get('percentage', 0)
            count = anomaly_insights.get('count', 0)
            top_anomalies = anomaly_insights.get('top_anomalies', [])

            # No anomalies = no problem
            if percentage == 0 or count == 0:
                return None

            severity = self._get_severity(percentage)
            if severity == 'none':
                return None

            problem = {
                'type': 'anomalies',
                'severity': severity,
                'percentage': percentage,
                'count': count,
                'description': f"{count} unusual values detected ({percentage:.1f}% of data)",
                'impact': self._describe_anomaly_impact(percentage, count),
                'location': f"Rows: {', '.join(str(a) for a in top_anomalies[:3])}" if top_anomalies else "Unknown",
                'fix_priority': self._severity_score(severity)
            }

            self.logger.info(f"Anomaly problem identified: {severity} ({percentage:.1f}%)")
            return problem

        except Exception as e:
            self.logger.error(f"Error identifying anomaly problems: {e}")
            return None

    def identify_missing_data_problems(self, statistics_insights: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Identify problems from missing data.
        
        Args:
            statistics_insights: Insights from InsightExtractor.extract_statistics()
        
        Returns:
            Problem dictionary or None if no problem
        """
        try:
            if not statistics_insights or not isinstance(statistics_insights, dict):
                return None

            # Calculate missing percentage
            completeness = statistics_insights.get('completeness', 100)
            missing_percentage = 100 - completeness

            # No missing data = no problem
            if missing_percentage == 0:
                return None

            severity = self._get_severity(missing_percentage)
            if severity == 'none':
                return None

            problem = {
                'type': 'missing_data',
                'severity': severity,
                'percentage': missing_percentage,
                'completeness': completeness,
                'description': f"Missing data in {missing_percentage:.1f}% of records",
                'impact': self._describe_missing_data_impact(missing_percentage),
                'location': "Multiple columns (missing values)",
                'fix_priority': self._severity_score(severity)
            }

            self.logger.info(f"Missing data problem identified: {severity} ({missing_percentage:.1f}%)")
            return problem

        except Exception as e:
            self.logger.error(f"Error identifying missing data problems: {e}")
            return None

    def identify_prediction_problems(self, prediction_insights: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Identify problems from low prediction confidence.
        
        Args:
            prediction_insights: Insights from InsightExtractor.extract_predictions()
        
        Returns:
            Problem dictionary or None if no problem
        """
        try:
            if not prediction_insights or not isinstance(prediction_insights, dict):
                return None

            confidence = prediction_insights.get('confidence', 0)
            accuracy = prediction_insights.get('accuracy', 0)

            # Good confidence = no problem
            if confidence >= 0.75:  # 75% confidence threshold
                return None

            # Calculate how far below threshold
            confidence_deficit = 75 - (confidence * 100)  # Convert 0-1 to 0-100
            severity = self._get_severity(confidence_deficit)

            problem = {
                'type': 'low_prediction_confidence',
                'severity': severity,
                'confidence': confidence,
                'accuracy': accuracy,
                'description': f"Model confidence is {confidence:.1%} (below 75% threshold)",
                'impact': self._describe_prediction_impact(confidence, accuracy),
                'location': "Model predictions",
                'fix_priority': self._severity_score(severity)
            }

            self.logger.info(f"Prediction problem identified: {severity} (confidence: {confidence:.1%})")
            return problem

        except Exception as e:
            self.logger.error(f"Error identifying prediction problems: {e}")
            return None

    def identify_distribution_problems(self, statistics_insights: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Identify problems from bad distributions.
        
        Args:
            statistics_insights: Insights from InsightExtractor.extract_statistics()
        
        Returns:
            Problem dictionary or None if no problem
        """
        try:
            if not statistics_insights or not isinstance(statistics_insights, dict):
                return None

            key_stats = statistics_insights.get('key_statistics', {})
            if not key_stats:
                return None

            # Check for high standard deviation relative to mean
            mean = key_stats.get('mean', 0)
            std = key_stats.get('std', 0)

            if mean == 0 or std == 0:
                return None

            # Coefficient of variation (std/mean)
            cv = abs(std / mean) if mean != 0 else 0
            
            # High CV (>1.0) indicates high variability
            if cv > 1.0:
                percentage = min(cv * 20, 100)  # Scale CV to percentage
                severity = self._get_severity(percentage)
                
                if severity == 'none':
                    return None

                problem = {
                    'type': 'skewed_distribution',
                    'severity': severity,
                    'coefficient_of_variation': round(cv, 2),
                    'description': f"Data has high variability (CV: {cv:.2f})",
                    'impact': self._describe_distribution_impact(cv),
                    'location': "Multiple numeric columns",
                    'fix_priority': self._severity_score(severity)
                }

                self.logger.info(f"Distribution problem identified: {severity} (CV: {cv:.2f})")
                return problem

            return None

        except Exception as e:
            self.logger.error(f"Error identifying distribution problems: {e}")
            return None

    def identify_all_problems(self, all_insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify all problems from complete insights.
        
        Args:
            all_insights: Complete insights from InsightExtractor.extract_all()
        
        Returns:
            List of problems sorted by severity (highest first)
        """
        try:
            self.logger.info("Starting comprehensive problem identification")

            problems = []

            # Identify anomaly problems
            anomaly_problem = self.identify_anomaly_problems(
                all_insights.get('anomalies', {})
            )
            if anomaly_problem:
                problems.append(anomaly_problem)

            # Identify missing data problems
            missing_problem = self.identify_missing_data_problems(
                all_insights.get('statistics', {})
            )
            if missing_problem:
                problems.append(missing_problem)

            # Identify prediction problems
            prediction_problem = self.identify_prediction_problems(
                all_insights.get('predictions', {})
            )
            if prediction_problem:
                problems.append(prediction_problem)

            # Identify distribution problems
            distribution_problem = self.identify_distribution_problems(
                all_insights.get('statistics', {})
            )
            if distribution_problem:
                problems.append(distribution_problem)

            # Sort by severity (fix_priority descending)
            problems.sort(key=lambda x: x['fix_priority'], reverse=True)

            self.logger.info(f"Problem identification complete. Found {len(problems)} problems")
            self.structured_logger.info("Problem identification complete", {
                'total_problems': len(problems),
                'by_severity': {
                    'critical': sum(1 for p in problems if p['severity'] == 'critical'),
                    'high': sum(1 for p in problems if p['severity'] == 'high'),
                    'medium': sum(1 for p in problems if p['severity'] == 'medium'),
                    'low': sum(1 for p in problems if p['severity'] == 'low')
                }
            })
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="narrative_generator",
                worker_name="ProblemIdentifier",
                operation="identify_all_problems",
                context={"total_problems": len(problems)}
            )

            return problems
            
        except Exception as e:
            self.logger.error(f"Error in identify_all_problems: {e}")
            self.error_intelligence.track_error(
                agent_name="narrative_generator",
                worker_name="ProblemIdentifier",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "identify_all_problems"}
            )
            raise

    # === IMPACT DESCRIPTIONS ===

    def _describe_anomaly_impact(self, percentage: float, count: int) -> str:
        """Describe impact of anomalies.
        
        Args:
            percentage: Percentage of data with anomalies
            count: Number of anomalies
        
        Returns:
            Impact description string
        """
        if percentage > 15:
            return "Severely skews statistical measures and model predictions"
        elif percentage > 10:
            return "Significantly affects averages and model accuracy"
        elif percentage > 5:
            return "Moderately affects data quality and predictions"
        else:
            return "Slightly impacts statistical measures"

    def _describe_missing_data_impact(self, missing_percentage: float) -> str:
        """Describe impact of missing data.
        
        Args:
            missing_percentage: Percentage of missing data
        
        Returns:
            Impact description string
        """
        if missing_percentage > 15:
            return "Cannot train reliable models; requires handling strategy"
        elif missing_percentage > 10:
            return "Significantly impacts model training and predictions"
        elif missing_percentage > 5:
            return "Moderately reduces data quality and model performance"
        else:
            return "Minor impact on overall data completeness"

    def _describe_prediction_impact(self, confidence: float, accuracy: float) -> str:
        """Describe impact of low prediction confidence.
        
        Args:
            confidence: Model confidence (0-1)
            accuracy: Model accuracy (0-100)
        
        Returns:
            Impact description string
        """
        if confidence < 0.5:
            return "Model predictions are unreliable; significant retraining needed"
        elif confidence < 0.65:
            return "Model has low confidence; needs improvement before deployment"
        elif confidence < 0.75:
            return "Model confidence below ideal threshold; consider refinement"
        else:
            return "Model confidence is acceptable"

    def _describe_distribution_impact(self, cv: float) -> str:
        """Describe impact of skewed distribution.
        
        Args:
            cv: Coefficient of variation (std/mean)
        
        Returns:
            Impact description string
        """
        if cv > 2.0:
            return "Extreme variability; may need data transformation or scaling"
        elif cv > 1.5:
            return "High variability; consider normalization or feature engineering"
        elif cv > 1.0:
            return "Moderate variability; may benefit from standardization"
        else:
            return "Reasonable distribution variability"
