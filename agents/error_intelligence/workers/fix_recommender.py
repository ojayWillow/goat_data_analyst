"""FixRecommender Worker - Recommends fixes for identified error patterns."""

from typing import Dict, Any, List
from core.logger import get_logger

logger = get_logger(__name__)

# Fix recommendation mappings
FIX_RECOMMENDATIONS = {
    'DateFormatError': {
        'description': 'Add date format converter/normalizer',
        'priority': 'HIGH',
        'action': 'Add date validation and conversion before worker execution',
    },
    'NullValueError': {
        'description': 'Add null/empty value checking',
        'priority': 'HIGH',
        'action': 'Add null checks and filtering before processing',
    },
    'DataTypeError': {
        'description': 'Add type validation',
        'priority': 'HIGH',
        'action': 'Validate data types before processing',
    },
    'IndexError': {
        'description': 'Add bounds checking',
        'priority': 'MEDIUM',
        'action': 'Add length validation and safe indexing',
    },
    'ValueError': {
        'description': 'Add value validation',
        'priority': 'MEDIUM',
        'action': 'Validate input values and ranges',
    },
    'KeyError': {
        'description': 'Add key existence checking',
        'priority': 'MEDIUM',
        'action': 'Check for key existence before access',
    },
}


class FixRecommender:
    """Recommends fixes based on error patterns."""

    def __init__(self):
        """Initialize fix recommender."""
        # Import here to avoid circular dependency
        try:
            from agents.error_intelligence.main import ErrorIntelligence
            self.error_intelligence = ErrorIntelligence()
        except ImportError:
            self.error_intelligence = None
        
        logger.info("FixRecommender worker initialized")

    def recommend(self, patterns: Dict[str, int]) -> List[Dict[str, Any]]:
        """Recommend fixes for identified patterns.
        
        Args:
            patterns: Dictionary of error patterns with frequencies
            
        Returns:
            List of recommended fixes
        """
        try:
            recommendations = []
            
            for pattern, frequency in patterns.items():
                # Extract error type from pattern
                parts = pattern.split(':')
                if len(parts) < 2:
                    continue
                
                error_type = parts[1].split('[')[0]  # Remove data type if present
                
                # Look up recommendation
                if error_type in FIX_RECOMMENDATIONS:
                    fix = FIX_RECOMMENDATIONS[error_type].copy()
                    fix['pattern'] = pattern
                    fix['frequency'] = frequency
                    recommendations.append(fix)
                else:
                    # Generic recommendation
                    recommendations.append({
                        'pattern': pattern,
                        'frequency': frequency,
                        'description': f'Investigate and handle {error_type}',
                        'priority': 'MEDIUM' if frequency > 2 else 'LOW',
                        'action': f'Add error handling for {error_type}',
                    })
            
            # Sort by priority and frequency
            priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            recommendations.sort(
                key=lambda x: (priority_order.get(x.get('priority', 'LOW'), 4), -x['frequency'])
            )
            
            logger.info(f"Generated {len(recommendations)} fix recommendations")
            
            # Track success
            if self.error_intelligence:
                self.error_intelligence.track_success(
                    agent_name="error_intelligence",
                    worker_name="FixRecommender",
                    operation="recommend_fixes",
                    context={"recommendations_generated": len(recommendations)}
                )
            
            return recommendations
        
        except Exception as e:
            logger.error(f"FixRecommender.recommend failed: {e}")
            
            if self.error_intelligence:
                self.error_intelligence.track_error(
                    agent_name="error_intelligence",
                    worker_name="FixRecommender",
                    error_type="recommend_error",
                    error_message=str(e),
                )
            
            return []

    def get_top_recommendations(self, patterns: Dict[str, int], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top recommended fixes.
        
        Args:
            patterns: Dictionary of error patterns
            limit: Maximum recommendations to return
            
        Returns:
            Top recommendations
        """
        try:
            all_recs = self.recommend(patterns)
            return all_recs[:limit]
        
        except Exception as e:
            logger.error(f"FixRecommender.get_top_recommendations failed: {e}")
            
            if self.error_intelligence:
                self.error_intelligence.track_error(
                    agent_name="error_intelligence",
                    worker_name="FixRecommender",
                    error_type="get_top_recommendations_error",
                    error_message=str(e),
                )
            
            return []

    def recommend_for_worker(self, agent: str, worker: str, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get recommendations for specific worker.
        
        Args:
            agent: Agent name
            worker: Worker name
            errors: List of errors for worker
            
        Returns:
            Recommendations for that worker
        """
        try:
            recommendations = []
            error_types = set()
            
            # Collect all error types
            for error in errors:
                error_type = error.get('error_type', 'Unknown')
                error_types.add(error_type)
            
            # Get recommendations for each error type
            for error_type in error_types:
                if error_type in FIX_RECOMMENDATIONS:
                    fix = FIX_RECOMMENDATIONS[error_type].copy()
                    fix['error_type'] = error_type
                    recommendations.append(fix)
            
            # Track success
            if self.error_intelligence:
                self.error_intelligence.track_success(
                    agent_name="error_intelligence",
                    worker_name="FixRecommender",
                    operation="recommend_for_worker",
                    context={"agent": agent, "worker": worker, "recommendations": len(recommendations)}
                )
            
            return recommendations
        
        except Exception as e:
            logger.error(f"FixRecommender.recommend_for_worker failed: {e}")
            
            if self.error_intelligence:
                self.error_intelligence.track_error(
                    agent_name="error_intelligence",
                    worker_name="FixRecommender",
                    error_type="recommend_for_worker_error",
                    error_message=str(e),
                )
            
            return []
