"""One-Class SVM Anomaly Detection Worker."""

import pandas as pd
import numpy as np
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

from agents.anomaly_detector.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class OneClassSVMAnomalyDetector(BaseWorker):
    """Worker that detects anomalies using One-Class SVM algorithm."""
    
    def __init__(self):
        """Initialize OneClassSVMAnomalyDetector."""
        super().__init__("OneClassSVMAnomalyDetector")
    
    def execute(self, df: pd.DataFrame = None, nu: float = 0.05, kernel: str = 'rbf', **kwargs) -> WorkerResult:
        """Detect anomalies using One-Class SVM algorithm.
        
        Args:
            df: DataFrame to analyze
            nu: Upper bound on fraction of anomalies
            kernel: Kernel type ('rbf', 'linear', 'poly')
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with anomaly scores and labels
        """
        result = self._create_result(task_type="ocsvm_anomaly_detection")
        
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
            
            # Standardize features
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(numeric_df)
            
            # Apply One-Class SVM
            oc_svm = OneClassSVM(kernel=kernel, nu=nu, gamma='auto')
            anomaly_labels = oc_svm.fit_predict(scaled_data)
            
            # Get decision function scores (distance from hyperplane)
            decision_scores = oc_svm.decision_function(scaled_data)
            
            # Normalize scores to 0-1 range
            min_score = decision_scores.min()
            max_score = decision_scores.max()
            if max_score > min_score:
                normalized_scores = (decision_scores - min_score) / (max_score - min_score)
            else:
                normalized_scores = np.zeros_like(decision_scores)
            
            result.data = {
                "algorithm": "OneClassSVM",
                "kernel": kernel,
                "nu": nu,
                "anomaly_count": int(np.sum(anomaly_labels == -1)),
                "anomaly_percentage": round(np.sum(anomaly_labels == -1) / len(anomaly_labels) * 100, 2),
                "scores_min": round(float(np.min(normalized_scores)), 6),
                "scores_max": round(float(np.max(normalized_scores)), 6),
                "scores_mean": round(float(np.mean(normalized_scores)), 6),
                "rows_analyzed": len(numeric_df)
            }
            
            logger.info(f"One-Class SVM: {np.sum(anomaly_labels == -1)} anomalies detected in {len(numeric_df)} rows")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"One-Class SVM detection failed: {e}")
            result.success = False
            return result
