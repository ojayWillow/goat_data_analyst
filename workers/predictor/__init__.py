"""Predictor Workers - Machine learning specialists.

Each worker handles a specific ML task:
- LinearRegression: Simple linear regression predictions
- DecisionTree: Tree-based predictions (regression & classification)
- TimeSeries: Time series forecasting
- ModelValidator: Model validation and comparison
"""

from .linear_regression import LinearRegressionWorker
from .decision_tree import DecisionTreeWorker
from .time_series import TimeSeriesWorker
from .model_validator import ModelValidatorWorker

__all__ = [
    'LinearRegressionWorker',
    'DecisionTreeWorker',
    'TimeSeriesWorker',
    'ModelValidatorWorker',
]
