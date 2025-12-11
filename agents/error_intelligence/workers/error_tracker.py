"""ErrorTracker Worker - Captures and stores errors from agents/workers."""

from typing import Dict, Any, Optional
from datetime import datetime
from core.logger import get_logger

logger = get_logger(__name__)


class ErrorTracker:
    """Tracks both successes and errors from all agents and workers.
    
    Implemented as a singleton to ensure all ErrorIntelligence instances
    share the same error tracking state.
    """
    
    _instance = None

    def __new__(cls):
        """Singleton pattern - always return same instance."""
        if cls._instance is None:
            cls._instance = super(ErrorTracker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize error tracker (only on first creation)."""
        if self._initialized:
            return
        
        self.errors = {}
        self._initialized = True
        
        # Import here to avoid circular dependency
        try:
            from agents.error_intelligence.main import ErrorIntelligence
            self.error_intelligence = ErrorIntelligence()
        except ImportError:
            # If ErrorIntelligence not available yet, skip
            self.error_intelligence = None
        
        logger.info("ErrorTracker worker initialized")

    def track_success(
        self,
        agent_name: str,
        worker_name: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a successful run.
        
        Args:
            agent_name: Name of agent
            worker_name: Name of worker
            operation: Operation that succeeded
            context: Additional context
        """
        try:
            if agent_name not in self.errors:
                self.errors[agent_name] = {
                    'total_runs': 0,
                    'successes': 0,
                    'failures': 0,
                    'workers': {},
                }
            
            if worker_name not in self.errors[agent_name]['workers']:
                self.errors[agent_name]['workers'][worker_name] = {
                    'successes': 0,
                    'failures': 0,
                    'errors': [],
                }
            
            # Increment success counters
            self.errors[agent_name]['total_runs'] += 1
            self.errors[agent_name]['successes'] += 1
            self.errors[agent_name]['workers'][worker_name]['successes'] += 1
            
            logger.debug(f"Tracked success: {agent_name}.{worker_name} - {operation}")
            
            # Track success in error intelligence
            if self.error_intelligence:
                self.error_intelligence.track_success(
                    agent_name=agent_name,
                    worker_name=worker_name,
                    operation=operation,
                    context=context,
                )
        
        except Exception as e:
            logger.error(f"ErrorTracker.track_success failed: {e}")
            # Don't raise - we don't want tracking to break the system

    def track_error(
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
        try:
            if agent_name not in self.errors:
                self.errors[agent_name] = {
                    'total_runs': 0,
                    'successes': 0,
                    'failures': 0,
                    'workers': {},
                }
            
            if worker_name not in self.errors[agent_name]['workers']:
                self.errors[agent_name]['workers'][worker_name] = {
                    'successes': 0,
                    'failures': 0,
                    'errors': [],
                }
            
            # Increment failure counters
            self.errors[agent_name]['total_runs'] += 1
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
            
            # Track error in error intelligence
            if self.error_intelligence:
                self.error_intelligence.track_error(
                    agent_name=agent_name,
                    worker_name=worker_name,
                    error_type=error_type,
                    error_message=error_message,
                    data_type=data_type,
                    context=context,
                )
        
        except Exception as e:
            logger.error(f"ErrorTracker.track_error failed: {e}")
            # Don't raise - we don't want tracking to break the system

    def record_run(self, agent_name: str) -> None:
        """Record a run attempt for an agent.
        
        Args:
            agent_name: Name of agent that ran
        """
        try:
            if agent_name not in self.errors:
                self.errors[agent_name] = {
                    'total_runs': 0,
                    'successes': 0,
                    'failures': 0,
                    'workers': {},
                }
            
            self.errors[agent_name]['total_runs'] += 1
        
        except Exception as e:
            logger.error(f"ErrorTracker.record_run failed: {e}")

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
        try:
            if agent_name not in self.errors:
                return {}
            
            stats = self.errors[agent_name].copy()
            total = stats.get('total_runs', 1)
            successes = stats.get('successes', 0)
            failures = stats.get('failures', 0)
            
            stats['success_rate'] = (
                (successes / total * 100)
                if total > 0 else 0
            )
            stats['failure_rate'] = (
                (failures / total * 100)
                if total > 0 else 0
            )
            
            return stats
        
        except Exception as e:
            logger.error(f"ErrorTracker.get_agent_stats failed: {e}")
            return {}

    def clear(self) -> None:
        """Clear all tracked errors."""
        try:
            self.errors = {}
            logger.info("Error tracker cleared")
        except Exception as e:
            logger.error(f"ErrorTracker.clear failed: {e}")
