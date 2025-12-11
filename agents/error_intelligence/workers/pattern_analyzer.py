"""PatternAnalyzer Worker - Identifies recurring error patterns."""

from typing import Dict, Any, List
from collections import Counter
from core.logger import get_logger

logger = get_logger(__name__)


class PatternAnalyzer:
    """Analyzes error patterns across system."""

    def __init__(self):
        """Initialize pattern analyzer."""
        self.error_intelligence = None  # Lazy load to avoid circular dependency
        logger.info("PatternAnalyzer worker initialized")

    def _get_error_intelligence(self):
        """Lazy load ErrorIntelligence to avoid circular dependency."""
        if self.error_intelligence is None:
            try:
                from agents.error_intelligence.main import ErrorIntelligence
                self.error_intelligence = ErrorIntelligence()
            except ImportError:
                pass
        return self.error_intelligence

    def analyze(self, error_patterns: Dict[str, Any]) -> Dict[str, int]:
        """Analyze error patterns from tracked errors.
        
        Args:
            error_patterns: Dictionary of tracked errors
            
        Returns:
            Dictionary of patterns with frequencies
        """
        try:
            patterns = Counter()
            
            for agent_name, agent_data in error_patterns.items():
                if not isinstance(agent_data, dict) or 'workers' not in agent_data:
                    continue
                    
                for worker_name, worker_data in agent_data['workers'].items():
                    if not isinstance(worker_data, dict) or 'errors' not in worker_data:
                        continue
                        
                    for error in worker_data['errors']:
                        error_type = error.get('error_type', 'Unknown')
                        data_type = error.get('data_type', 'Unknown')
                        
                        # Create pattern key
                        pattern = f"{agent_name}.{worker_name}:{error_type}"
                        patterns[pattern] += 1
                        
                        # Track by data type
                        if data_type:
                            pattern_by_type = f"{agent_name}.{worker_name}:{error_type}[{data_type}]"
                            patterns[pattern_by_type] += 1
            
            result = dict(patterns.most_common())
            logger.info(f"Identified {len(result)} error patterns")
            
            return result
        
        except Exception as e:
            logger.error(f"PatternAnalyzer.analyze failed: {e}")
            return {}

    def get_top_patterns(self, error_patterns: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top error patterns.
        
        Args:
            error_patterns: Dictionary of tracked errors
            limit: Maximum patterns to return
            
        Returns:
            List of top patterns with details
        """
        try:
            patterns = self.analyze(error_patterns)
            
            result = []
            for pattern, frequency in list(patterns.items())[:limit]:
                result.append({
                    'pattern': pattern,
                    'frequency': frequency,
                    'severity': 'HIGH' if frequency > 5 else 'MEDIUM' if frequency > 2 else 'LOW',
                })
            
            return result
        
        except Exception as e:
            logger.error(f"PatternAnalyzer.get_top_patterns failed: {e}")
            return []

    def find_patterns_by_worker(self, error_patterns: Dict[str, Any], agent: str, worker: str) -> List[Dict[str, Any]]:
        """Find all patterns for specific worker.
        
        Args:
            error_patterns: Dictionary of tracked errors
            agent: Agent name
            worker: Worker name
            
        Returns:
            List of patterns for that worker
        """
        try:
            if agent not in error_patterns:
                return []
            
            agent_data = error_patterns[agent]
            if 'workers' not in agent_data or worker not in agent_data['workers']:
                return []
            
            worker_data = agent_data['workers'][worker]
            error_types = Counter()
            
            for error in worker_data.get('errors', []):
                error_type = error.get('error_type', 'Unknown')
                error_types[error_type] += 1
            
            result = [
                {'error_type': err_type, 'frequency': count}
                for err_type, count in error_types.most_common()
            ]
            
            return result
        
        except Exception as e:
            logger.error(f"PatternAnalyzer.find_patterns_by_worker failed: {e}")
            return []
