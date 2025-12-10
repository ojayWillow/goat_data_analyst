"""IsolationForest - Isolation Forest anomaly detection."""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from agents.anomaly_detector.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class IsolationForest(BaseWorker):
    """Worker that detects anomalies using Isolation Forest."""
    
    def __init__(self):
        """Initialize IsolationForest."""
        super().__init__("IsolationForest")
    
    def execute(
        self,
        df: pd.DataFrame = None,
        contamination: float = 0.1,
        n_estimators: int = 100,
        **kwargs
    ) -> WorkerResult:
        """Detect anomalies using Isolation Forest.
        
        Args:
            df: DataFrame to analyze
            contamination: Proportion of anomalies
            n_estimators: Number of trees
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with anomaly predictions
        """
        result = self._create_result(task_type="isolation_forest_detection")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(result, ErrorType.LOAD_ERROR, "No numeric columns")
                result.success = False
                return result
            
            # Isolation Forest
            iso_forest = IsolationForest(contamination=contamination, n_estimators=n_estimators, random_state=42)
            predictions = iso_forest.fit_predict(numeric_df)
            anomaly_scores = iso_forest.score_samples(numeric_df)
            
            # Normalize scores to 0-1
            normalized_scores = (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min() + 1e-10)
            
            result.data = {
                "method": "Isolation Forest",
                "contamination": contamination,
                "n_estimators": n_estimators,
                "anomalies_detected": int((predictions == -1).sum()),
                "normal_count": int((predictions == 1).sum()),
                "anomaly_scores_mean": float(normalized_scores.mean()),
                "anomaly_scores_std": float(normalized_scores.std())
            }
            
            logger.info(f"Isolation Forest: {result.data['anomalies_detected']} anomalies detected")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Isolation Forest failed: {e}")
            result.success = False
            return result
