"""OneClassSVM - One-Class SVM anomaly detection.

This worker implements One-Class Support Vector Machine which finds a hyperplane that
encloses the maximum number of points in the training set. Points that fall outside
this hyperplane are classified as anomalies.

All methods follow A+ quality standards with comprehensive error handling and quality tracking.
"""

import pandas as pd
import numpy as np
from sklearn.svm import OneClassSVM as SKOneClassSVM
from sklearn.preprocessing import StandardScaler
from typing import Any, Optional, Literal

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

# ===== CONSTANTS =====
DEFAULT_NU: float = 0.05
DEFAULT_KERNEL: Literal['rbf', 'linear', 'poly'] = 'rbf'
MIN_REQUIRED_SAMPLES: int = 2

logger = get_logger(__name__)


class OneClassSVM(BaseWorker):
    """Worker that detects anomalies using One-Class SVM algorithm.
    
    One-Class SVM finds a decision boundary that encloses most of the training data.
    Points that fall outside this boundary are flagged as anomalies. This approach is
    effective when you only have normal examples for training.
    
    Advantages:
    - Works well with high-dimensional data
    - Flexible kernel choice for non-linear boundaries
    - Theoretically well-founded approach
    
    Parameters:
    - nu: Upper bound on anomaly fraction (0, 1)
    - kernel: 'rbf' (default), 'linear', or 'poly'
    
    Example:
        >>> worker = OneClassSVM()
        >>> df = pd.DataFrame({'value': [1, 2, 3, 100, 4, 5]})
        >>> result = worker.execute(df=df, nu=0.1, kernel='rbf')
        >>> print(f"Anomalies: {result.data['anomalies_detected']}")
        Anomalies: 1
    """
    
    def __init__(self) -> None:
        """Initialize OneClassSVM worker with error intelligence."""
        super().__init__("OneClassSVM")
        self.error_intelligence: ErrorIntelligence = ErrorIntelligence()
        self.logger = get_logger("OneClassSVM")
    
    def execute(
        self,
        df: Optional[pd.DataFrame] = None,
        nu: float = DEFAULT_NU,
        kernel: Literal['rbf', 'linear', 'poly'] = DEFAULT_KERNEL,
        **kwargs: Any
    ) -> WorkerResult:
        """Detect anomalies using One-Class SVM.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            nu (float): Upper bound on anomaly fraction (0 < nu < 1). Default 0.05.
            kernel (str): Kernel type: 'rbf', 'linear', or 'poly'. Default 'rbf'.
            **kwargs: Additional arguments
        
        Returns:
            WorkerResult: Detection results with:
                - anomalies_detected: Number of anomalies found
                - normal_count: Number of normal samples
                - anomaly_fraction: Fraction of anomalies
        
        Example:
            >>> df = pd.DataFrame({'a': [1, 2, 3, 100], 'b': [10, 20, 30, 1000]})
            >>> result = worker.execute(df=df, nu=0.25, kernel='rbf')
            >>> assert result.success
        """
        try:
            result: WorkerResult = self._run_ocsvm(df, nu, kernel, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="OneClassSVM",
                operation="ocsvm_detection",
                context={
                    "nu": nu,
                    "kernel": kernel
                }
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="OneClassSVM",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "nu": nu,
                    "kernel": kernel
                }
            )
            raise
    
    def _run_ocsvm(
        self,
        df: Optional[pd.DataFrame],
        nu: float,
        kernel: str,
        **kwargs: Any
    ) -> WorkerResult:
        """Perform One-Class SVM detection.
        
        Args:
            df: Input DataFrame
            nu: Anomaly upper bound
            kernel: Kernel type
            **kwargs: Additional parameters
        
        Returns:
            WorkerResult with anomaly detection results
        """
        result: WorkerResult = self._create_result(
            task_type="ocsvm_detection",
            quality_score=1.0
        )
        
        # ===== VALIDATE INPUTS =====
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        # Validate nu parameter
        if not (0.0 < nu < 1.0):
            self._add_error(
                result,
                ErrorType.INVALID_PARAMETER,
                f"nu must be between 0 and 1, got {nu}"
            )
            result.success = False
            return result
        
        # Validate kernel parameter
        valid_kernels: tuple = ('rbf', 'linear', 'poly')
        if kernel not in valid_kernels:
            self._add_error(
                result,
                ErrorType.INVALID_PARAMETER,
                f"kernel must be one of {valid_kernels}, got '{kernel}'"
            )
            result.success = False
            return result
        
        try:
            # Extract numeric columns only
            numeric_df: pd.DataFrame = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(result, ErrorType.LOAD_ERROR, "No numeric columns found")
                result.success = False
                return result
            
            # Check minimum samples
            if len(numeric_df) < MIN_REQUIRED_SAMPLES:
                self._add_error(
                    result,
                    ErrorType.INSUFFICIENT_DATA,
                    f"Insufficient samples: {len(numeric_df)} (need {MIN_REQUIRED_SAMPLES})"
                )
                result.success = False
                return result
            
            # Handle missing values
            null_count: int = numeric_df.isnull().sum().sum()
            if null_count > 0:
                numeric_df = numeric_df.dropna()
                self._add_warning(
                    result,
                    f"Found {null_count} null values - removed rows with NaNs"
                )
            
            # Standardize features (important for SVM)
            scaler: StandardScaler = StandardScaler()
            scaled_data: np.ndarray = scaler.fit_transform(numeric_df)
            
            # Run One-Class SVM
            ocsvm: SKOneClassSVM = SKOneClassSVM(
                kernel=kernel,
                nu=nu,
                gamma='auto'
            )
            
            predictions: np.ndarray = ocsvm.fit_predict(scaled_data)
            
            # Get decision function scores (distance from hyperplane)
            decision_scores: np.ndarray = ocsvm.decision_function(scaled_data)
            
            # Normalize scores to 0-1 range (higher = more anomalous, i.e., further from hyperplane)
            min_score: np.floating = decision_scores.min()
            max_score: np.floating = decision_scores.max()
            score_range: np.floating = max_score - min_score
            
            if score_range > 1e-10:
                normalized_scores: np.ndarray = (decision_scores - min_score) / score_range
            else:
                normalized_scores: np.ndarray = np.zeros_like(decision_scores)
            
            # Calculate statistics
            anomaly_count: int = int((predictions == -1).sum())
            normal_count: int = int((predictions == 1).sum())
            anomaly_pct: float = (anomaly_count / len(predictions) * 100) if len(predictions) > 0 else 0
            anomaly_fraction: float = anomaly_count / len(predictions) if len(predictions) > 0 else 0.0
            
            # Calculate quality score
            rows_failed: int = null_count + anomaly_count
            total_rows: int = len(df)
            quality_score: float = max(
                0.0,
                1.0 - (rows_failed / total_rows) if total_rows > 0 else 0.0
            )
            result.quality_score = quality_score
            
            result.data = {
                "method": "One-Class SVM",
                "kernel": kernel,
                "nu": nu,
                "sample_count": len(numeric_df),
                "null_count": null_count,
                "anomalies_detected": anomaly_count,
                "anomalies_percentage": round(anomaly_pct, 2),
                "normal_count": normal_count,
                "anomaly_fraction": round(anomaly_fraction, 4),
                "decision_scores": {
                    "mean": float(normalized_scores.mean()),
                    "std": float(normalized_scores.std()),
                    "min": float(normalized_scores.min()),
                    "max": float(normalized_scores.max()),
                },
            }
            
            self.logger.info(
                f"One-Class SVM ({kernel}): {anomaly_count} anomalies ({anomaly_pct:.2f}%) detected"
            )
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"One-Class SVM failed: {str(e)}")
            result.success = False
            self.logger.error(f"Error in One-Class SVM: {str(e)}")
            return result
