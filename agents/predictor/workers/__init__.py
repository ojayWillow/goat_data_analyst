"""Predictor Workers - Machine learning specialists.

Each worker handles a specific ML task:
- LinearRegressionWorker: Simple linear regression predictions
- DecisionTreeWorker: Tree-based predictions (regression & classification)
- TimeSeriesWorker: Time series forecasting
- ModelValidatorWorker: Model validation and comparison

Note: These are the _worker versions that include full ErrorIntelligence integration.
"""

from .base_worker import BaseWorker, WorkerResult, ErrorType
from .linear_regression_worker import LinearRegressionWorker as LinearRegression
from .decision_tree_worker import DecisionTreeWorker as DecisionTree
from .time_series_worker import TimeSeriesWorker as TimeSeries
from .model_validator_worker import ModelValidatorWorker as ModelValidator

__all__ = [
    'BaseWorker',
    'WorkerResult',
    'ErrorType',
    'LinearRegression',
    'DecisionTree',
    'TimeSeries',
    'ModelValidator',
]
