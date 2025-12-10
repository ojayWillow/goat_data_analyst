"""Isolation Forest Anomaly Detection Worker."""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

from agents.anomaly_detector.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class IsolationForestAnomalyDetector(BaseWorker):
    """Worker that detects anomalies using Isolation Forest algorithm."""
    
    def __init__(self):
        """Initialize IsolationForestAnomalyDetector."""
        super().__init__("IsolationForestAnomalyDetector")
    
    def execute(self, df: pd.DataFrame = None, contamination: float = 0.1, n_estimators: int = 100, **kwargs) -> WorkerResult:
        """Detect anomalies using Isolation Forest algorithm.
        
        Args:
            df: DataFrame to analyze
            contamination: Expected proportion of anomalies
            n_estimators: Number of base estimators
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with anomaly scores and labels
        """
        result = self._create_result(task_type="isolation_forest_anomaly_detection")
        
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
            
            # Apply Isolation Forest
            iso_forest = IsolationForest(contamination=contamination, n_estimators=n_estimators, random_state=42)
            anomaly_labels = iso_forest.fit_predict(numeric_df)
            anomaly_scores = -iso_forest.score_samples(numeric_df)
            
            # Normalize scores to 0-1 range
            min_score = anomaly_scores.min()
            max_score = anomaly_scores.max()
            if max_score > min_score:
                normalized_scores = (anomaly_scores - min_score) / (max_score - min_score)
            else:
                normalized_scores = np.zeros_like(anomaly_scores)
            
            result.data = {
                "algorithm": "IsolationForest",
                "contamination": contamination,
                "n_estimators": n_estimators,
                "anomaly_count": int(np.sum(anomaly_labels == -1)),
                "anomaly_percentage": round(np.sum(anomaly_labels == -1) / len(anomaly_labels) * 100, 2),
                "scores_min": round(float(np.min(normalized_scores)), 6),
                "scores_max": round(float(np.max(normalized_scores)), 6),
                "scores_mean": round(float(np.mean(normalized_scores)), 6),
                "rows_analyzed": len(numeric_df)
            }
            
            logger.info(f"Isolation Forest: {np.sum(anomaly_labels == -1)} anomalies detected in {len(numeric_df)} rows")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Isolation Forest detection failed: {e}")
            result.success = False
            return result
