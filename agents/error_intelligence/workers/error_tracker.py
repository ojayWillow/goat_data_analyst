"""ErrorTracker Worker - Captures and stores errors from agents/workers."""

from typing import Dict, Any, Optional
from datetime import datetime
from core.logger import get_logger

logger = get_logger(__name__)


class ErrorTracker:
    """Tracks errors from all agents and workers."""

    def __init__(self):
        """Initialize error tracker."""
        self.errors = {}
        logger.info("ErrorTracker worker initialized")

    def track(
        self,
        agent_name: str,
        worker_name: str,
        error_type: str,
        error_message: str,
        data_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track an error.
        
        Args:
            agent_name: Name of agent
            worker_name: Name of worker
            error_type: Type of error
            error_message: Error message
            data_type: Data type that caused error
            context: Additional context
        """
        if agent_name not in self.errors:
            self.errors[agent_name] = {
                'total_runs': 0,
                'failures': 0,
                'workers': {},
            }
        
        if worker_name not in self.errors[agent_name]['workers']:
            self.errors[agent_name]['workers'][worker_name] = {
                'failures': 0,
                'errors': [],
            }
        
        # Increment counters
        self.errors[agent_name]['failures'] += 1
        self.errors[agent_name]['workers'][worker_name]['failures'] += 1
        
        # Store error details
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'data_type': data_type,
            'context': context or {},
        }
        
        self.errors[agent_name]['workers'][worker_name]['errors'].append(error_record)
        
        logger.debug(f"Tracked error: {agent_name}.{worker_name} - {error_type}")

    def record_run(self, agent_name: str) -> None:
        """Record a run attempt for an agent.
        
        Args:
            agent_name: Name of agent that ran
        """
        if agent_name not in self.errors:
            self.errors[agent_name] = {
                'total_runs': 0,
                'failures': 0,
                'workers': {},
            }
        
        self.errors[agent_name]['total_runs'] += 1

    def get_patterns(self) -> Dict[str, Any]:
        """Get current error patterns.
        
        Returns:
            Dictionary of error patterns by agent
        """
        return self.errors

    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get stats for specific agent.
        
        Args:
            agent_name: Name of agent
            
        Returns:
            Agent statistics
        """
        if agent_name not in self.errors:
            return {}
        
        stats = self.errors[agent_name].copy()
        total = stats.get('total_runs', 1)  # Avoid divide by zero
        stats['success_rate'] = (
            (total - stats['failures']) / total * 100
            if total > 0 else 0
        )
        return stats

    def clear(self) -> None:
        """Clear all tracked errors."""
        self.errors = {}
        logger.info("Error tracker cleared")
