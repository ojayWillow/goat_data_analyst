"""Error Intelligence Agent - Tracks, analyzes, and learns from worker/agent errors.

This agent monitors all errors across the system and provides:
- Error tracking and categorization
- Pattern analysis and detection
- Worker health scoring
- Fix recommendations
- Learning from successful fixes
"""

from agents.error_intelligence.main import ErrorIntelligence

__all__ = ['ErrorIntelligence']
