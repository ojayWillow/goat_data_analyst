"""LOF - Local Outlier Factor anomaly detection."""

import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from agents.anomaly_detector.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class LOF(BaseWorker):
    """Worker that detects anomalies using Local Outlier Factor algorithm."""
    
    def __init__(self):
        """Initialize LOF."""
        super().__init__("LOF")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(
        self,
        df: pd.DataFrame = None,
        n_neighbors: int = 20,
        contamination: float = 0.1,
        **kwargs
    ) -> WorkerResult:
        """Detect anomalies using Local Outlier Factor.
        
        Args:
            df: DataFrame to analyze
            n_neighbors: Number of neighbors
            contamination: Proportion of anomalies
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with anomaly scores
        """
        try:
            result = self._run_lof(df, n_neighbors, contamination, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="LOF",
                operation="lof_detection",
                context={"n_neighbors": n_neighbors, "contamination": contamination}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="LOF",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"n_neighbors": n_neighbors, "contamination": contamination}
            )
            raise
    
    def _run_lof(self, df, n_neighbors, contamination, **kwargs) -> WorkerResult:
        """Perform LOF anomaly detection."""
        result = self._create_result(task_type="lof_detection")
        
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
            
            # Local Outlier Factor
            lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
            anomaly_labels = lof.fit_predict(numeric_df)
            anomaly_scores = -lof.negative_outlier_factor_
            
            # Normalize scores to 0-1
            normalized_scores = (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min() + 1e-10)
            
            result.data = {
                "method": "Local Outlier Factor",
                "n_neighbors": n_neighbors,
                "contamination": contamination,
                "anomalies_detected": int((anomaly_labels == -1).sum()),
                "normal_count": int((anomaly_labels == 1).sum()),
                "anomaly_scores_mean": float(normalized_scores.mean()),
                "anomaly_scores_std": float(normalized_scores.std())
            }
            
            logger.info(f"LOF: {result.data['anomalies_detected']} anomalies detected")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"LOF failed: {e}")
            result.success = False
            return result
