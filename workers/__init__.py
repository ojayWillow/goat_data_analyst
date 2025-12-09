"""Workers module - Specialized workers for agents.

Each worker handles a specific task with quality validation.
Workers communicate in a common language (same interface/protocol).

Worker Packages:
- base_worker: Shared BaseWorker and WorkerResult
- predictor: ML prediction workers (LinearRegression, DecisionTree, TimeSeries, ModelValidator)
"""

from .base_worker import BaseWorker, WorkerResult, ErrorType
from .validation import ValidationResult, QualityValidator
from . import predictor

__all__ = [
    'BaseWorker',
    'WorkerResult',
    'ErrorType',
    'ValidationResult',
    'QualityValidator',
    'predictor',
]
