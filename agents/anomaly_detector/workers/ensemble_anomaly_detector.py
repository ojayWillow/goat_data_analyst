"""Ensemble Anomaly Detection Worker - Combines multiple algorithms."""

import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from agents.anomaly_detector.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class EnsembleAnomalyDetector(BaseWorker):
    """Worker that detects anomalies using ensemble of multiple algorithms."""
    
    def __init__(self):
        """Initialize EnsembleAnomalyDetector."""
        super().__init__("EnsembleAnomalyDetector")
    
    def execute(self, df: pd.DataFrame = None, threshold: float = 0.5, **kwargs) -> WorkerResult:
        """Detect anomalies using ensemble method.
        
        Args:
            df: DataFrame to analyze
            threshold: Voting threshold (0-1)
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with ensemble anomaly scores and labels
        """
        result = self._create_result(task_type="ensemble_anomaly_detection")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        try:
            # Select numeric columns only
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(result, ErrorType.LOAD_ERROR, "No numeric columns found")
                result.success = False
                return result
            
            # Handle missing values
            numeric_df = numeric_df.fillna(numeric_df.mean())
            
            # Initialize voting array
            n_samples = len(numeric_df)
            votes = np.zeros(n_samples)
            scores_list = []
            
            # 1. LOF
            try:
                lof = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
                lof_labels = lof.fit_predict(numeric_df)
                lof_scores = -lof.negative_outlier_factor_
                lof_norm = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min() + 1e-10)
                votes += (lof_labels == -1).astype(int)
                scores_list.append(lof_norm)
            except Exception as e:
                logger.warning(f"LOF failed in ensemble: {e}")
            
            # 2. One-Class SVM
            try:
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(numeric_df)
                oc_svm = OneClassSVM(kernel='rbf', nu=0.05, gamma='auto')
                svm_labels = oc_svm.fit_predict(scaled_data)
                svm_scores = oc_svm.decision_function(scaled_data)
                svm_norm = (svm_scores - svm_scores.min()) / (svm_scores.max() - svm_scores.min() + 1e-10)
                votes += (svm_labels == -1).astype(int)
                scores_list.append(svm_norm)
            except Exception as e:
                logger.warning(f"One-Class SVM failed in ensemble: {e}")
            
            # 3. Isolation Forest
            try:
                iso_forest = IsolationForest(contamination=0.1, n_estimators=100, random_state=42)
                if_labels = iso_forest.fit_predict(numeric_df)
                if_scores = -iso_forest.score_samples(numeric_df)
                if_norm = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min() + 1e-10)
                votes += (if_labels == -1).astype(int)
                scores_list.append(if_norm)
            except Exception as e:
                logger.warning(f"Isolation Forest failed in ensemble: {e}")
            
            # Calculate ensemble score (average of normalized scores)
            if scores_list:
                ensemble_scores = np.mean(scores_list, axis=0)
            else:
                ensemble_scores = np.zeros(n_samples)
            
            # Determine anomalies by voting threshold
            # threshold * 3 algorithms = minimum votes needed
            min_votes = max(1, int(np.ceil(threshold * len(scores_list))))
            anomaly_labels = (votes >= min_votes).astype(int)
            anomaly_labels[anomaly_labels == 0] = 1  # Normal: 1
            anomaly_labels[anomaly_labels == 1] = -1  # Keep anomalies as -1
            anomaly_labels[votes >= min_votes] = -1
            
            result.data = {
                "algorithm": "EnsembleAnomalyDetector",
                "algorithms_used": len(scores_list),
                "threshold": threshold,
                "min_votes": min_votes,
                "anomaly_count": int(np.sum(anomaly_labels == -1)),
                "anomaly_percentage": round(np.sum(anomaly_labels == -1) / len(anomaly_labels) * 100, 2),
                "scores_min": round(float(np.min(ensemble_scores)), 6),
                "scores_max": round(float(np.max(ensemble_scores)), 6),
                "scores_mean": round(float(np.mean(ensemble_scores)), 6),
                "rows_analyzed": len(numeric_df)
            }
            
            logger.info(f"Ensemble: {np.sum(anomaly_labels == -1)} anomalies detected using {len(scores_list)} algorithms")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Ensemble detection failed: {e}")
            result.success = False
            return result
