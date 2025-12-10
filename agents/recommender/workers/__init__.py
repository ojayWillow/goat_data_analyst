"""Recommender Workers - Specialized task processors for recommendation generation.

Each worker handles a specific recommendation task:
- MissingDataAnalyzer: Analyze missing data and recommend actions
- DuplicateAnalyzer: Analyze duplicates and recommend cleanup
- DistributionAnalyzer: Analyze distributions and recommend transformations
- CorrelationAnalyzer: Analyze correlations and recommend feature engineering
- ActionPlanGenerator: Consolidate all recommendations into action plan
"""

from .missing_data_analyzer import MissingDataAnalyzer
from .duplicate_analyzer import DuplicateAnalyzer
from .distribution_analyzer import DistributionAnalyzer
from .correlation_analyzer import CorrelationAnalyzer
from .action_plan_generator import ActionPlanGenerator

__all__ = [
    'MissingDataAnalyzer',
    'DuplicateAnalyzer',
    'DistributionAnalyzer',
    'CorrelationAnalyzer',
    'ActionPlanGenerator',
]
