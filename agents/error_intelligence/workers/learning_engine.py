"""LearningEngine Worker - Learns from successful fixes and tracks effectiveness."""

from typing import Dict, Any, List
from datetime import datetime
from core.logger import get_logger

logger = get_logger(__name__)


class LearningEngine:
    """Learns from fixes and tracks their effectiveness."""

    def __init__(self):
        """Initialize learning engine."""
        self.learned_fixes = []
        self.error_intelligence = None  # Lazy load to avoid circular dependency
        logger.info("LearningEngine worker initialized")

    def _get_error_intelligence(self):
        """Lazy load ErrorIntelligence to avoid circular dependency."""
        if self.error_intelligence is None:
            try:
                from agents.error_intelligence.main import ErrorIntelligence
                self.error_intelligence = ErrorIntelligence()
            except ImportError:
                pass
        return self.error_intelligence

    def record_fix(
        self,
        agent_name: str,
        worker_name: str,
        error_type: str,
        fix_applied: str,
        success: bool,
    ) -> None:
        """Record a fix attempt.
        
        Args:
            agent_name: Agent with issue
            worker_name: Worker with issue
            error_type: Type of error fixed
            fix_applied: Description of fix
            success: Whether fix worked
        """
        try:
            fix_record = {
                'timestamp': datetime.now().isoformat(),
                'agent': agent_name,
                'worker': worker_name,
                'error_type': error_type,
                'fix_applied': fix_applied,
                'success': success,
            }
            
            self.learned_fixes.append(fix_record)
            logger.info(f"Recorded fix: {agent_name}.{worker_name} - {error_type} - {'SUCCESS' if success else 'FAILED'}")
        
        except Exception as e:
            logger.error(f"LearningEngine.record_fix failed: {e}")

    def get_learned_fixes(self, success_only: bool = True) -> List[Dict[str, Any]]:
        """Get learned fixes.
        
        Args:
            success_only: Only return successful fixes
            
        Returns:
            List of learned fixes
        """
        try:
            result = []
            if success_only:
                result = [f for f in self.learned_fixes if f['success']]
            else:
                result = self.learned_fixes
            
            return result
        
        except Exception as e:
            logger.error(f"LearningEngine.get_learned_fixes failed: {e}")
            return []

    def get_fix_effectiveness(
        self,
        agent_name: str,
        worker_name: str,
        error_type: str,
    ) -> Dict[str, Any]:
        """Get effectiveness of fixes for specific error.
        
        Args:
            agent_name: Agent name
            worker_name: Worker name
            error_type: Error type
            
        Returns:
            Effectiveness metrics
        """
        try:
            relevant_fixes = [
                f for f in self.learned_fixes
                if f['agent'] == agent_name
                and f['worker'] == worker_name
                and f['error_type'] == error_type
            ]
            
            if not relevant_fixes:
                result = {
                    'no_fixes_recorded': True,
                    'agent': agent_name,
                    'worker': worker_name,
                    'error_type': error_type,
                }
            else:
                successful = sum(1 for f in relevant_fixes if f['success'])
                total = len(relevant_fixes)
                
                result = {
                    'agent': agent_name,
                    'worker': worker_name,
                    'error_type': error_type,
                    'total_attempts': total,
                    'successful': successful,
                    'failed': total - successful,
                    'success_rate': round(successful / total * 100, 2),
                    'last_fix': relevant_fixes[-1]['fix_applied'],
                    'last_timestamp': relevant_fixes[-1]['timestamp'],
                }
            
            return result
        
        except Exception as e:
            logger.error(f"LearningEngine.get_fix_effectiveness failed: {e}")
            return {}

    def get_best_practices(self) -> List[str]:
        """Get best practices learned from fixes.
        
        Returns:
            List of best practices
        """
        try:
            successful_fixes = self.get_learned_fixes(success_only=True)
            
            if not successful_fixes:
                return []
            
            # Extract unique successful fixes
            practices = list(set(f['fix_applied'] for f in successful_fixes))
            
            logger.info(f"Identified {len(practices)} best practices")
            return practices
        
        except Exception as e:
            logger.error(f"LearningEngine.get_best_practices failed: {e}")
            return []

    def suggest_fix_for_error(self, error_type: str) -> str:
        """Suggest a fix for an error type based on what worked before.
        
        Args:
            error_type: Type of error
            
        Returns:
            Suggested fix or message if none found
        """
        try:
            successful_fixes = self.get_learned_fixes(success_only=True)
            
            for fix in successful_fixes:
                if fix['error_type'] == error_type:
                    return fix['fix_applied']
            
            return f"No learned fixes for {error_type}. Suggest: Add error handling for {error_type}"
        
        except Exception as e:
            logger.error(f"LearningEngine.suggest_fix_for_error failed: {e}")
            return f"Error suggesting fix: {str(e)}"

    def clear_history(self) -> None:
        """Clear learning history."""
        try:
            self.learned_fixes = []
            logger.info("Learning history cleared")
        
        except Exception as e:
            logger.error(f"LearningEngine.clear_history failed: {e}")
