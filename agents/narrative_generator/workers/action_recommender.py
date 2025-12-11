"""ActionRecommender Worker - Day 3 Implementation.

Generates actionable recommendations for each problem:
- For each problem, suggest specific actions
- Rank by priority and impact
- Explain why action matters
- Provide next steps

Recommendations are specific, not generic:
- NOT: "Fix your data"
- YES: "Remove 23 anomalies from North region (rows 145-167)"
"""

from typing import Any, Dict, List, Optional
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from agents.error_intelligence.main import ErrorIntelligence


class ActionRecommender:
    """Generates specific, actionable recommendations for data problems.
    
    Takes problems identified by ProblemIdentifier and generates:
    - Specific actions (not generic)
    - Priority ranking
    - Impact explanation
    - Next steps
    """

    def __init__(self) -> None:
        """Initialize the ActionRecommender worker."""
        self.name = "ActionRecommender"
        self.logger = get_logger("ActionRecommender")
        self.structured_logger = get_structured_logger("ActionRecommender")
        self.error_intelligence = ErrorIntelligence()
        self.logger.info("ActionRecommender worker initialized")

    def recommend_for_anomalies(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for anomaly problems.
        
        Args:
            problem: Problem dict from ProblemIdentifier.identify_anomaly_problems()
        
        Returns:
            Recommendation dict with:
            - action: What to do
            - detail: How to do it
            - impact: Why it matters
            - effort: low/medium/high
            - priority: 1-5 (5 = highest)
        """
        try:
            if not problem or problem.get('type') != 'anomalies':
                return None

            severity = problem.get('severity', 'low')
            count = problem.get('count', 0)
            percentage = problem.get('percentage', 0)
            location = problem.get('location', 'Unknown')

            # Determine action based on severity
            if severity == 'critical':
                action = "Immediately investigate and handle anomalies"
                detail = f"Found {count} anomalies ({percentage:.1f}% of data) at {location}. "\
                        f"Manually review each anomaly to determine if it's: "\
                        f"(1) Data entry error - correct it, "\
                        f"(2) Real outlier - document why, "\
                        f"(3) System error - remove it."
                effort = "medium"
                priority = 5
                impact = "Prevents skewed statistics and improves model accuracy by ~10%"
            elif severity == 'high':
                action = "Review and handle significant anomalies"
                detail = f"Found {count} anomalies ({percentage:.1f}% of data). "\
                        f"Prioritize reviewing the most extreme {int(count/2)} anomalies first."
                effort = "medium"
                priority = 4
                impact = "Improves model accuracy by ~5-7%"
            elif severity == 'medium':
                action = "Document anomalies and update processing rules"
                detail = f"Found {count} anomalies ({percentage:.1f}%). "\
                        f"Document patterns and add validation rules to catch future anomalies."
                effort = "low"
                priority = 3
                impact = "Improves future data quality by ~3-5%"
            else:  # low
                action = "Monitor anomalies in future batches"
                detail = f"Found {count} anomalies ({percentage:.1f}%). "\
                        f"Continue monitoring. Add to anomaly tracking dashboard."
                effort = "low"
                priority = 1
                impact = "Maintains data quality awareness"

            recommendation = {
                'action': action,
                'detail': detail,
                'impact': impact,
                'effort': effort,
                'priority': priority,
                'time_estimate': self._estimate_time(effort, count)
            }

            self.logger.info(f"Anomaly recommendation generated: {action} (priority {priority})")
            return recommendation

        except Exception as e:
            self.logger.error(f"Error generating anomaly recommendation: {e}")
            return None

    def recommend_for_missing_data(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for missing data problems.
        
        Args:
            problem: Problem dict from ProblemIdentifier.identify_missing_data_problems()
        
        Returns:
            Recommendation dict
        """
        try:
            if not problem or problem.get('type') != 'missing_data':
                return None

            severity = problem.get('severity', 'low')
            percentage = problem.get('percentage', 0)
            completeness = problem.get('completeness', 100)

            # Determine action based on severity
            if severity == 'critical':
                action = "Implement missing data handling strategy"
                detail = f"Missing {percentage:.1f}% of data (completeness: {completeness:.1f}%). "\
                        f"Choose strategy: (1) Remove incomplete rows, "\
                        f"(2) Impute with mean/median, (3) Use advanced imputation (KNN/MICE)."
                effort = "high"
                priority = 5
                impact = "Makes data usable for reliable model training"
            elif severity == 'high':
                action = "Address missing data in critical columns"
                detail = f"Missing {percentage:.1f}% of data. "\
                        f"Identify columns with most missing values and impute or remove."
                effort = "medium"
                priority = 4
                impact = "Improves data completeness from {:.1f}% to 95%+".format(completeness)
            elif severity == 'medium':
                action = "Impute remaining missing values"
                detail = f"Missing {percentage:.1f}% of data. "\
                        f"Use simple imputation (mean/median) for numeric columns."
                effort = "low"
                priority = 2
                impact = "Achieves {:.1f}% data completeness".format(100 - percentage/2)
            else:  # low
                action = "Document missing data patterns"
                detail = f"Missing {percentage:.1f}% of data. "\
                        f"Document which columns have missing values for future reference."
                effort = "low"
                priority = 1
                impact = "Improves data understanding"

            recommendation = {
                'action': action,
                'detail': detail,
                'impact': impact,
                'effort': effort,
                'priority': priority,
                'time_estimate': self._estimate_time(effort, percentage)
            }

            self.logger.info(f"Missing data recommendation generated: {action} (priority {priority})")
            return recommendation

        except Exception as e:
            self.logger.error(f"Error generating missing data recommendation: {e}")
            return None

    def recommend_for_prediction(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for low prediction confidence.
        
        Args:
            problem: Problem dict from ProblemIdentifier.identify_prediction_problems()
        
        Returns:
            Recommendation dict
        """
        try:
            if not problem or problem.get('type') != 'low_prediction_confidence':
                return None

            severity = problem.get('severity', 'low')
            confidence = problem.get('confidence', 0)
            accuracy = problem.get('accuracy', 0)

            # Determine action based on confidence
            if severity == 'critical':
                action = "Retrain model with improved data or features"
                detail = f"Model confidence: {confidence:.1%}, accuracy: {accuracy:.1f}%. "\
                        f"(1) Collect more training data, "\
                        f"(2) Engineer new features, "\
                        f"(3) Use different algorithm, "\
                        f"(4) Address data quality issues first."
                effort = "high"
                priority = 5
                impact = "Increases confidence from {:.1%} to 85%+ for reliable predictions".format(confidence)
            elif severity == 'high':
                action = "Improve model with feature engineering"
                detail = f"Confidence: {confidence:.1%}. "\
                        f"Engineer new features that better capture patterns. "\
                        f"Consider polynomial/interaction features."
                effort = "medium"
                priority = 4
                impact = "Improves confidence by ~10-15%"
            elif severity == 'medium':
                action = "Fine-tune model hyperparameters"
                detail = f"Confidence: {confidence:.1%}. "\
                        f"Try hyperparameter optimization (grid/random search)."
                effort = "medium"
                priority = 3
                impact = "Improves confidence by ~5-10%"
            else:  # low
                action = "Monitor model performance"
                detail = f"Confidence: {confidence:.1%}. Model is borderline. "\
                        f"Continue monitoring on new data."
                effort = "low"
                priority = 1
                impact = "Maintains awareness of model reliability"

            recommendation = {
                'action': action,
                'detail': detail,
                'impact': impact,
                'effort': effort,
                'priority': priority,
                'time_estimate': self._estimate_time(effort, (1 - confidence) * 100)
            }

            self.logger.info(f"Prediction recommendation generated: {action} (priority {priority})")
            return recommendation

        except Exception as e:
            self.logger.error(f"Error generating prediction recommendation: {e}")
            return None

    def recommend_for_distribution(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for skewed distribution.
        
        Args:
            problem: Problem dict from ProblemIdentifier.identify_distribution_problems()
        
        Returns:
            Recommendation dict
        """
        try:
            if not problem or problem.get('type') != 'skewed_distribution':
                return None

            severity = problem.get('severity', 'low')
            cv = problem.get('coefficient_of_variation', 0)

            # Determine action based on CV (coefficient of variation)
            if severity == 'critical':
                action = "Apply data transformation to normalize distribution"
                detail = f"High variability (CV: {cv:.2f}). "\
                        f"Try: (1) Log transformation, (2) Box-Cox transformation, "\
                        f"(3) Remove extreme outliers, (4) Use robust scaling."
                effort = "medium"
                priority = 5
                impact = "Stabilizes model predictions and reduces variance by ~30%"
            elif severity == 'high':
                action = "Normalize numeric features"
                detail = f"Variability (CV: {cv:.2f}). "\
                        f"Apply StandardScaler or MinMaxScaler to normalize features."
                effort = "low"
                priority = 4
                impact = "Improves model convergence and accuracy by ~5-10%"
            elif severity == 'medium':
                action = "Consider feature scaling"
                detail = f"Variability (CV: {cv:.2f}). "\
                        f"Scaling may help some models (neural nets, SVM, KNN)."
                effort = "low"
                priority = 2
                impact = "Improves training speed and accuracy"
            else:  # low
                action = "Monitor distribution in future data"
                detail = f"Variability (CV: {cv:.2f}). Distribution is reasonable."
                effort = "low"
                priority = 1
                impact = "Maintains distribution awareness"

            recommendation = {
                'action': action,
                'detail': detail,
                'impact': impact,
                'effort': effort,
                'priority': priority,
                'time_estimate': self._estimate_time(effort, cv * 10)
            }

            self.logger.info(f"Distribution recommendation generated: {action} (priority {priority})")
            return recommendation

        except Exception as e:
            self.logger.error(f"Error generating distribution recommendation: {e}")
            return None

    def recommend_for_all_problems(self, problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations for all problems.
        
        Args:
            problems: List of problem dicts from ProblemIdentifier.identify_all_problems()
        
        Returns:
            List of recommendation dicts, sorted by priority (highest first)
        """
        try:
            self.logger.info(f"Generating recommendations for {len(problems)} problems")

            recommendations = []

            for problem in problems:
                problem_type = problem.get('type')

                if problem_type == 'anomalies':
                    rec = self.recommend_for_anomalies(problem)
                elif problem_type == 'missing_data':
                    rec = self.recommend_for_missing_data(problem)
                elif problem_type == 'low_prediction_confidence':
                    rec = self.recommend_for_prediction(problem)
                elif problem_type == 'skewed_distribution':
                    rec = self.recommend_for_distribution(problem)
                else:
                    rec = None

                if rec:
                    rec['problem_type'] = problem_type
                    recommendations.append(rec)

            # Sort by priority (highest first)
            recommendations.sort(key=lambda x: x['priority'], reverse=True)

            self.logger.info(f"Generated {len(recommendations)} recommendations")
            self.structured_logger.info("Recommendations generated", {
                'total': len(recommendations),
                'by_priority': {
                    5: sum(1 for r in recommendations if r['priority'] == 5),
                    4: sum(1 for r in recommendations if r['priority'] == 4),
                    3: sum(1 for r in recommendations if r['priority'] == 3),
                    2: sum(1 for r in recommendations if r['priority'] == 2),
                    1: sum(1 for r in recommendations if r['priority'] == 1)
                }
            })
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="narrative_generator",
                worker_name="ActionRecommender",
                operation="recommend_for_all_problems",
                context={"total_recommendations": len(recommendations)}
            )

            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error in recommend_for_all_problems: {e}")
            self.error_intelligence.track_error(
                agent_name="narrative_generator",
                worker_name="ActionRecommender",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "recommend_for_all_problems"}
            )
            raise

    # === HELPER METHODS ===

    def _estimate_time(self, effort: str, magnitude: float) -> str:
        """Estimate time to complete action.
        
        Args:
            effort: low/medium/high
            magnitude: Severity metric (percentage, count, etc.)
        
        Returns:
            Time estimate string
        """
        if effort == 'low':
            return "< 1 hour"
        elif effort == 'medium':
            if magnitude > 20:
                return "2-4 hours"
            else:
                return "1-2 hours"
        else:  # high
            if magnitude > 30:
                return "1-2 days"
            else:
                return "4-8 hours"
