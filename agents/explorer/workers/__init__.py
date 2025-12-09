"""Explorer Workers - Specialized workers for data analysis.

Each worker handles a specific analysis task.
All workers inherit from BaseWorker and use standardized communication.
"""

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from .numeric_analyzer import NumericAnalyzer
from .categorical_analyzer import CategoricalAnalyzer
from .correlation_analyzer import CorrelationAnalyzer
from .quality_assessor import QualityAssessor

__all__ = [
    'BaseWorker',
    'WorkerResult',
    'WorkerError',
    'ErrorType',
    'NumericAnalyzer',
    'CategoricalAnalyzer',
    'CorrelationAnalyzer',
    'QualityAssessor',
]
