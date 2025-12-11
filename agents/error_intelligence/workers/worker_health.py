"""WorkerHealth Worker - Calculates health scores for workers/agents."""

from typing import Dict, Any
from core.logger import get_logger

logger = get_logger(__name__)


class WorkerHealth:
    """Calculates health and reliability scores for agents/workers."""

    def __init__(self):
        """Initialize worker health calculator."""
        logger.info("WorkerHealth worker initialized")

    def calculate(self, error_patterns: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculate health scores for all workers.
        
        Args:
            error_patterns: Dictionary of tracked errors
            
        Returns:
            Dictionary of health scores by agent and worker
        """
        health_scores = {}
        
        for agent_name, agent_data in error_patterns.items():
            if not isinstance(agent_data, dict) or 'workers' not in agent_data:
                continue
            
            health_scores[agent_name] = {
                'agent_health': self._calculate_agent_health(agent_data),
                'workers': {},
            }
            
            for worker_name, worker_data in agent_data['workers'].items():
                if isinstance(worker_data, dict):
                    health_scores[agent_name]['workers'][worker_name] = self._calculate_worker_health(worker_data)
        
        logger.info(f"Calculated health scores for {len(health_scores)} agents")
        return health_scores

    def _calculate_agent_health(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate health for an agent.
        
        Args:
            agent_data: Agent error data
            
        Returns:
            Agent health metrics
        """
        total_runs = agent_data.get('total_runs', 1)
        failures = agent_data.get('failures', 0)
        successes = agent_data.get('successes', 0)
        
        # Use successes if available (from new tracking system)
        if successes > 0:
            success_rate = (successes / total_runs * 100) if total_runs > 0 else 0
        else:
            # Fallback to old calculation
            success_rate = (
                ((total_runs - failures) / total_runs * 100)
                if total_runs > 0 else 0
            )
        
        return {
            'total_runs': total_runs,
            'failures': failures,
            'successes': successes,
            'success_rate': round(success_rate, 2),
            'status': 'HEALTHY' if success_rate >= 90 else 'DEGRADED' if success_rate >= 70 else 'BROKEN',
        }

    def _calculate_worker_health(self, worker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate health for a worker.
        
        Args:
            worker_data: Worker error data
            
        Returns:
            Worker health metrics
        """
        failures = worker_data.get('failures', 0)
        successes = worker_data.get('successes', 0)
        errors = worker_data.get('errors', [])
        
        # Use actual successes and failures if available (from new tracking system)
        total_runs = successes + failures if (successes > 0 or failures > 0) else 1
        
        if total_runs > 0:
            success_rate = (successes / total_runs * 100)
        else:
            success_rate = 0
        
        # Get most common error
        common_error = errors[0].get('error_type', 'Unknown') if errors else 'None'
        
        return {
            'failures': failures,
            'successes': successes,
            'total_runs': total_runs,
            'total_errors': len(errors),
            'success_rate': round(success_rate, 2),
            'status': 'HEALTHY' if success_rate >= 90 else 'DEGRADED' if success_rate >= 70 else 'BROKEN',
            'most_common_error': common_error,
        }

    def rank_workers(self, error_patterns: Dict[str, Any]) -> list:
        """Rank workers by health (worst to best).
        
        Args:
            error_patterns: Dictionary of tracked errors
            
        Returns:
            List of workers ranked by health
        """
        worker_list = []
        
        for agent_name, agent_data in error_patterns.items():
            if 'workers' not in agent_data:
                continue
                
            for worker_name, worker_data in agent_data['workers'].items():
                failures = worker_data.get('failures', 0)
                worker_list.append({
                    'agent': agent_name,
                    'worker': worker_name,
                    'failures': failures,
                    'priority': 'CRITICAL' if failures > 5 else 'HIGH' if failures > 2 else 'MEDIUM',
                })
        
        # Sort by failures (highest first)
        return sorted(worker_list, key=lambda x: x['failures'], reverse=True)
