"""OneClassSVM - One-Class SVM anomaly detection."""

import pandas as pd
import numpy as np
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from agents.anomaly_detector.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class OneClassSVM(BaseWorker):
    """Worker that detects anomalies using One-Class SVM."""
    
    def __init__(self):
        """Initialize OneClassSVM."""
        super().__init__("OneClassSVM")
    
    def execute(
        self,
        df: pd.DataFrame = None,
        nu: float = 0.05,
        kernel: str = 'rbf',
        **kwargs
    ) -> WorkerResult:
        """Detect anomalies using One-Class SVM.
        
        Args:
            df: DataFrame to analyze
            nu: Upper bound on anomaly fraction
            kernel: Kernel type ('rbf', 'linear', 'poly')
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with anomaly predictions
        """
        result = self._create_result(task_type="ocsvm_detection")
        
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
            
            # Standardize features
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(numeric_df)
            
            # One-Class SVM
            ocsvm = OneClassSVM(kernel=kernel, nu=nu, gamma='auto')
            predictions = ocsvm.fit_predict(scaled_data)
            
            result.data = {
                "method": "One-Class SVM",
                "kernel": kernel,
                "nu": nu,
                "anomalies_detected": int((predictions == -1).sum()),
                "normal_count": int((predictions == 1).sum()),
                "anomaly_fraction": float((predictions == -1).sum() / len(predictions))
            }
            
            logger.info(f"One-Class SVM: {result.data['anomalies_detected']} anomalies detected")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"One-Class SVM failed: {e}")
            result.success = False
            return result
