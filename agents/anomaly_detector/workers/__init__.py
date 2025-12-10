"""Anomaly Detector Workers - Specialized workers for anomaly detection.

Week 1 Day 3 Workers (4):
- LOF: Local Outlier Factor algorithm
- OneClassSVM: One-Class SVM algorithm
- IsolationForest: Isolation Forest algorithm
- Ensemble: Ensemble voting method
"""

from .base_worker import BaseWorker, WorkerResult, ErrorType
from .lof import LOF
from .ocsvm import OneClassSVM
from .isolation_forest import IsolationForest
from .ensemble import Ensemble

__all__ = [
    "BaseWorker",
    "WorkerResult",
    "ErrorType",
    "LOF",
    "OneClassSVM",
    "IsolationForest",
    "Ensemble",
]
