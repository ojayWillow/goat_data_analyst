"""ErrorIntelligence Agent - Main Orchestrator

Coordinates all error intelligence workers to track, analyze, and learn from
errors across all agents and workers in the system.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.exceptions import AgentError
from agents.error_intelligence.workers.error_tracker import ErrorTracker
from agents.error_intelligence.workers.pattern_analyzer import PatternAnalyzer
from agents.error_intelligence.workers.worker_health import WorkerHealth
from agents.error_intelligence.workers.fix_recommender import FixRecommender
from agents.error_intelligence.workers.learning_engine import LearningEngine

logger = get_logger(__name__)


class ErrorIntelligence:
    """Error Intelligence Agent - Tracks successes and learns from system errors."""

    def __init__(self):
        """Initialize error intelligence agent with all workers."""
        self.error_tracker = ErrorTracker()
        self.pattern_analyzer = PatternAnalyzer()
        self.worker_health = WorkerHealth()
        self.fix_recommender = FixRecommender()
        self.learning_engine = LearningEngine()
        
        self.error_patterns_file = '.error_patterns.json'
        self.error_patterns = self._load_error_patterns()
        
        logger.info("ErrorIntelligence agent initialized")

    def _load_error_patterns(self) -> Dict[str, Any]:
        """Load error patterns from file or create empty structure."""
        if os.path.exists(self.error_patterns_file):
            try:
                with open(self.error_patterns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load error patterns: {e}")
                return {}
        return {}

    def _save_error_patterns(self) -> None:
        """Save error patterns to file."""
        try:
            with open(self.error_patterns_file, 'w') as f:
                json.dump(self.error_patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save error patterns: {e}")

    @retry_on_error(max_attempts=2, backoff=1)
    def track_success(
        self,
        agent_name: str,
        worker_name: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a successful operation.
        
        Args:
            agent_name: Name of agent that succeeded
            worker_name: Name of worker that succeeded
            operation: Operation that succeeded
            context: Additional context about the success
        """
        # Track the success
        self.error_tracker.track_success(
            agent_name=agent_name,
            worker_name=worker_name,
            operation=operation,
            context=context,
        )
        
        # Update error patterns
        self.error_patterns = self.error_tracker.get_patterns()
        self._save_error_patterns()
        
        logger.info(f"Success tracked: {agent_name}.{worker_name} - {operation}")

    @retry_on_error(max_attempts=2, backoff=1)
    def track_error(
        self,
        agent_name: str,
        worker_name: str,
        error_type: str,
        error_message: str,
        data_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track an error from an agent's worker.
        
        Args:
            agent_name: Name of agent that failed
            worker_name: Name of worker that failed
            error_type: Type of error (e.g., 'DateFormatError')
            error_message: Error message
            data_type: Type of data that caused error
            context: Additional context about the error
        """
        # Track the error
        self.error_tracker.track_error(
            agent_name=agent_name,
            worker_name=worker_name,
            error_type=error_type,
            error_message=error_message,
            data_type=data_type,
            context=context,
        )
        
        # Update error patterns
        self.error_patterns = self.error_tracker.get_patterns()
        self._save_error_patterns()
        
        logger.info(f"Error tracked: {agent_name}.{worker_name} - {error_type}")

    @retry_on_error(max_attempts=2, backoff=1)
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns across system.
        
        Returns:
            Dictionary with pattern analysis results
        """
        patterns = self.pattern_analyzer.analyze(self.error_patterns)
        logger.info(f"Identified {len(patterns)} error patterns")
        return patterns

    @retry_on_error(max_attempts=2, backoff=1)
    def get_worker_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health scores for all workers.
        
        Returns:
            Dictionary with worker health scores by agent
        """
        health = self.worker_health.calculate(self.error_patterns)
        logger.info("Calculated worker health scores")
        return health

    @retry_on_error(max_attempts=2, backoff=1)
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get fix recommendations based on error patterns.
        
        Returns:
            List of recommended fixes
        """
        patterns = self.analyze_patterns()
        recommendations = self.fix_recommender.recommend(patterns)
        logger.info(f"Generated {len(recommendations)} fix recommendations")
        return recommendations

    @retry_on_error(max_attempts=2, backoff=1)
    def record_fix_attempt(
        self,
        agent_name: str,
        worker_name: str,
        error_type: str,
        fix_applied: str,
        success: bool,
    ) -> None:
        """Record a fix attempt and whether it worked.
        
        Args:
            agent_name: Agent that had issue
            worker_name: Worker that had issue
            error_type: Type of error fixed
            fix_applied: Description of fix
            success: Whether fix worked
        """
        self.learning_engine.record_fix(
            agent_name=agent_name,
            worker_name=worker_name,
            error_type=error_type,
            fix_applied=fix_applied,
            success=success,
        )
        logger.info(f"Fix recorded: {agent_name}.{worker_name} - {success}")

    @retry_on_error(max_attempts=3, backoff=2)
    def execute(self) -> Dict[str, Any]:
        """Execute full error intelligence analysis.
        
        Returns:
            Comprehensive error analysis report
        """
        try:
            logger.info("Starting error intelligence analysis")
            
            # Get all metrics
            patterns = self.analyze_patterns()
            health = self.get_worker_health()
            recommendations = self.get_recommendations()
            learned_fixes = self.learning_engine.get_learned_fixes()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'error_patterns': patterns,
                'worker_health': health,
                'recommendations': recommendations,
                'learned_fixes': learned_fixes,
                'total_errors': len(self.error_patterns),
                'affected_agents': list(self.error_patterns.keys()),
            }
            
            logger.info("Error intelligence analysis complete")
            return report
            
        except Exception as e:
            logger.error(f"Error intelligence analysis failed: {e}")
            raise AgentError(f"ErrorIntelligence execution failed: {e}") from e

    @retry_on_error(max_attempts=2, backoff=1)
    def print_report(self) -> None:
        """Print human-readable error intelligence report."""
        report = self.execute()
        
        print("\n" + "="*70)
        print("ERROR INTELLIGENCE REPORT")
        print("="*70)
        
        print(f"\nTimestamp: {report['timestamp']}")
        print(f"Total Errors Tracked: {report['total_errors']}")
        print(f"Affected Agents: {', '.join(report['affected_agents'])}")
        
        if report['error_patterns']:
            print("\nTop Error Patterns:")
            for i, (pattern, count) in enumerate(report['error_patterns'].items(), 1):
                print(f"  {i}. {pattern} ({count} occurrences)")
        
        if report['recommendations']:
            print("\nFix Recommendations:")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                print(f"  {i}. {rec['description']}")
                print(f"     Priority: {rec.get('priority', 'MEDIUM')}")
        
        if report['learned_fixes']:
            print("\nLearned Fixes (Successful):")
            for fix in report['learned_fixes'][:5]:
                print(f"  ✓ {fix['fix_applied']}")
        
        print("\n" + "="*70 + "\n")
