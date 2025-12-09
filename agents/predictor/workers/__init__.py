"""Predictor Workers - Machine learning specialists.

Each worker handles a specific ML task:
- Linear Regression: Simple linear regression predictions
- DecisionTree: Tree-based predictions (regression & classification)
- TimeSeries: Time series forecasting
- ModelValidator: Model validation and comparison
"""

from .base import Base, WorkerResult, ErrorType
from .linear_regression import LinearRegression
from .decision_tree import DecisionTree
from .time_series import TimeSeries
from .model_validator import ModelValidator

__all__ = [
    'Base',
    'WorkerResult',
    'ErrorType',
    'LinearRegression',
    'DecisionTree',
    'TimeSeries',
    'ModelValidator',
]
