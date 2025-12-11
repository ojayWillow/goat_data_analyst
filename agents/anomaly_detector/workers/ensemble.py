"""Ensemble - Ensemble anomaly detection using voting."""

import pandas as pd
import numpy as np
from agents.anomaly_detector.workers.lof import LOF
from agents.anomaly_detector.workers.ocsvm import OneClassSVM
from agents.anomaly_detector.workers.isolation_forest import IsolationForest
from agents.anomaly_detector.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class Ensemble(BaseWorker):
    """Worker that detects anomalies using ensemble voting."""
    
    def __init__(self):
        """Initialize Ensemble."""
        super().__init__("Ensemble")
        self.error_intelligence = ErrorIntelligence()
        self.lof = LOF()
        self.ocsvm = OneClassSVM()
        self.iso_forest = IsolationForest()
    
    def execute(
        self,
        df: pd.DataFrame = None,
        threshold: float = 0.5,
        **kwargs
    ) -> WorkerResult:
        """Detect anomalies using ensemble voting.
        
        Args:
            df: DataFrame to analyze
            threshold: Voting threshold (0-1)
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with ensemble anomaly predictions
        """
        try:
            result = self._run_ensemble(df, threshold, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="Ensemble",
                operation="ensemble_detection",
                context={"threshold": threshold}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="Ensemble",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"threshold": threshold}
            )
            raise
    
    def _run_ensemble(self, df, threshold, **kwargs) -> WorkerResult:
        """Perform ensemble detection."""
        result = self._create_result(task_type="ensemble_detection")
        
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
            
            votes = np.zeros(len(numeric_df))
            successful_algos = 0
            
            # LOF
            try:
                lof_result = self.lof.safe_execute(df=df)
                if lof_result.success:
                    votes += 1
                    successful_algos += 1
            except Exception as e:
                logger.warning(f"LOF failed in ensemble: {e}")
            
            # One-Class SVM
            try:
                ocsvm_result = self.ocsvm.safe_execute(df=df)
                if ocsvm_result.success:
                    votes += 1
                    successful_algos += 1
            except Exception as e:
                logger.warning(f"One-Class SVM failed in ensemble: {e}")
            
            # Isolation Forest
            try:
                iso_result = self.iso_forest.safe_execute(df=df)
                if iso_result.success:
                    votes += 1
                    successful_algos += 1
            except Exception as e:
                logger.warning(f"Isolation Forest failed in ensemble: {e}")
            
            if successful_algos == 0:
                self._add_error(result, ErrorType.LOAD_ERROR, "All algorithms failed")
                result.success = False
                return result
            
            # Calculate voting threshold
            vote_threshold = max(1, threshold * successful_algos)
            ensemble_predictions = votes >= vote_threshold
            
            result.data = {
                "method": "Ensemble Voting",
                "threshold": threshold,
                "successful_algorithms": successful_algos,
                "anomalies_detected": int(ensemble_predictions.sum()),
                "normal_count": int((~ensemble_predictions).sum()),
                "voting_threshold": vote_threshold,
                "algorithms": ["LOF", "OneClassSVM", "IsolationForest"]
            }
            
            logger.info(f"Ensemble: {result.data['anomalies_detected']} anomalies detected")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Ensemble failed: {e}")
            result.success = False
            return result
