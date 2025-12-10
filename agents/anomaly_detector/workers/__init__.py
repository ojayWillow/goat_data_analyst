"""Anomaly Detector Workers - Specialized workers for anomaly detection.

Week 1 Day 3 Workers (4):
- LOFAnomalyDetector: Local Outlier Factor algorithm
- OneClassSVMAnomalyDetector: One-Class SVM algorithm
- IsolationForestAnomalyDetector: Isolation Forest algorithm
- EnsembleAnomalyDetector: Ensemble voting method
"""

from .base_worker import BaseWorker, WorkerResult, ErrorType
from .lof_anomaly_detector import LOFAnomalyDetector
from .ocsvm_anomaly_detector import OneClassSVMAnomalyDetector
from .isolation_forest_anomaly_detector import IsolationForestAnomalyDetector
from .ensemble_anomaly_detector import EnsembleAnomalyDetector

__all__ = [
    "BaseWorker",
    "WorkerResult",
    "ErrorType",
    "LOFAnomalyDetector",
    "OneClassSVMAnomalyDetector",
    "IsolationForestAnomalyDetector",
    "EnsembleAnomalyDetector",
]
