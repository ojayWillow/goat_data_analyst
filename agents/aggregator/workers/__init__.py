"""Aggregator Workers - Collection of specialized aggregation workers.

Week 1 Day 4 Workers (4):
- WindowFunctionWorker: Rolling window operations
- RollingAggregationWorker: Multi-column rolling aggregations
- ExponentialWeightedWorker: EWMA and exponential std
- LagLeadFunctionWorker: Lag/lead time shifts

Note: If you get ImportError, clear __pycache__ and restart interpreter.
"""

from .base_worker import BaseWorker, WorkerResult, ErrorType
from .window_function_worker import WindowFunctionWorker
from .rolling_aggregation_worker import RollingAggregationWorker
from .exponential_weighted_worker import ExponentialWeightedWorker
from .lag_lead_function_worker import LagLeadFunctionWorker

__all__ = [
    "BaseWorker",
    "WorkerResult",
    "ErrorType",
    "WindowFunctionWorker",
    "RollingAggregationWorker",
    "ExponentialWeightedWorker",
    "LagLeadFunctionWorker",
]
