"""LOF - Local Outlier Factor anomaly detection.

This worker implements the Local Outlier Factor algorithm which computes local density
deviation of a data point relative to its neighbors. Points with low density relative
to their neighbors are anomalies.

All methods follow A+ quality standards with comprehensive error handling and quality tracking.
"""

import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor as SKLocalOutlierFactor
from typing import Any, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

# ===== CONSTANTS =====
DEFAULT_N_NEIGHBORS: int = 20
DEFAULT_CONTAMINATION: float = 0.1
MIN_REQUIRED_SAMPLES: int = 2

logger = get_logger(__name__)


class LOF(BaseWorker):
    """Worker that detects anomalies using Local Outlier Factor algorithm.
    
    Local Outlier Factor (LOF) is a density-based anomaly detection algorithm that
    computes the local density of each point and compares it with that of its neighbors.
    Points with significantly lower local density than their neighbors are flagged as anomalies.
    
    Advantages:
    - Good for detecting local and global outliers
    - Works with arbitrary data distributions
    - Efficient with appropriate k parameter
    
    Example:
        >>> worker = LOF()
        >>> df = pd.DataFrame({'value': [1, 2, 3, 100, 4, 5]})
        >>> result = worker.execute(df=df, n_neighbors=2, contamination=0.1)
        >>> print(f"Anomalies: {result.data['anomalies_detected']}")
        Anomalies: 1
    """
    
    def __init__(self) -> None:
        """Initialize LOF worker with error intelligence."""
        super().__init__("LOF")
        self.error_intelligence: ErrorIntelligence = ErrorIntelligence()
        self.logger = get_logger("LOF")
    
    def execute(
        self,
        df: Optional[pd.DataFrame] = None,
        n_neighbors: int = DEFAULT_N_NEIGHBORS,
        contamination: float = DEFAULT_CONTAMINATION,
        **kwargs: Any
    ) -> WorkerResult:
        """Detect anomalies using Local Outlier Factor.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            n_neighbors (int): Number of neighbors to use. Default 20.
            contamination (float): Proportion of anomalies (0.0 to 0.5). Default 0.1.
            **kwargs: Additional arguments
        
        Returns:
            WorkerResult: Detection results with:
                - anomalies_detected: Number of anomalies found
                - normal_count: Number of normal samples
                - anomaly_scores_mean: Mean LOF score
                - anomaly_scores_std: Std dev of LOF scores
        
        Example:
            >>> df = pd.DataFrame({'a': [1, 2, 3, 100], 'b': [10, 20, 30, 1000]})
            >>> result = worker.execute(df=df, n_neighbors=2, contamination=0.25)
            >>> assert result.success
        """
        try:
            result: WorkerResult = self._run_lof(df, n_neighbors, contamination, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="LOF",
                operation="lof_detection",
                context={
                    "n_neighbors": n_neighbors,
                    "contamination": contamination
                }
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="LOF",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "n_neighbors": n_neighbors,
                    "contamination": contamination
                }
            )
            raise
    
    def _run_lof(
        self,
        df: Optional[pd.DataFrame],
        n_neighbors: int,
        contamination: float,
        **kwargs: Any
    ) -> WorkerResult:
        """Perform LOF anomaly detection.
        
        Args:
            df: Input DataFrame
            n_neighbors: Number of neighbors
            contamination: Expected contamination rate
            **kwargs: Additional parameters
        
        Returns:
            WorkerResult with anomaly detection results
        """
        result: WorkerResult = self._create_result(
            task_type="lof_detection",
            quality_score=1.0
        )
        
        # ===== VALIDATE INPUTS =====
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        # Validate n_neighbors parameter
        if not isinstance(n_neighbors, int) or n_neighbors < 1:
            self._add_error(
                result,
                ErrorType.INVALID_PARAMETER,
                f"n_neighbors must be positive integer, got {n_neighbors}"
            )
            result.success = False
            return result
        
        # Validate contamination parameter
        if not (0.0 < contamination < 0.5):
            self._add_error(
                result,
                ErrorType.INVALID_PARAMETER,
                f"Contamination must be between 0 and 0.5, got {contamination}"
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
            
            # Adjust n_neighbors if needed
            actual_n_neighbors: int = min(n_neighbors, len(numeric_df) - 1)
            if actual_n_neighbors < n_neighbors:
                self._add_warning(
                    result,
                    f"Reduced n_neighbors from {n_neighbors} to {actual_n_neighbors} (data size)"
                )
            
            # Handle missing values
            null_count: int = numeric_df.isnull().sum().sum()
            if null_count > 0:
                numeric_df = numeric_df.dropna()
                self._add_warning(
                    result,
                    f"Found {null_count} null values - removed rows with NaNs"
                )
            
            # Run LOF
            lof: SKLocalOutlierFactor = SKLocalOutlierFactor(
                n_neighbors=actual_n_neighbors,
                contamination=contamination,
                n_jobs=-1
            )
            
            anomaly_labels: np.ndarray = lof.fit_predict(numeric_df)
            anomaly_scores: np.ndarray = -lof.negative_outlier_factor_
            
            # Normalize scores to 0-1 range (higher = more anomalous)
            min_score: np.floating = anomaly_scores.min()
            max_score: np.floating = anomaly_scores.max()
            score_range: np.floating = max_score - min_score
            
            if score_range > 1e-10:
                normalized_scores: np.ndarray = (anomaly_scores - min_score) / score_range
            else:
                normalized_scores: np.ndarray = np.zeros_like(anomaly_scores)
            
            # Calculate statistics
            anomaly_count: int = int((anomaly_labels == -1).sum())
            normal_count: int = int((anomaly_labels == 1).sum())
            anomaly_pct: float = (anomaly_count / len(anomaly_labels) * 100) if len(anomaly_labels) > 0 else 0
            
            # Calculate quality score
            rows_failed: int = null_count + anomaly_count
            total_rows: int = len(df)
            quality_score: float = max(
                0.0,
                1.0 - (rows_failed / total_rows) if total_rows > 0 else 0.0
            )
            result.quality_score = quality_score
            
            result.data = {
                "method": "Local Outlier Factor",
                "n_neighbors": actual_n_neighbors,
                "contamination": contamination,
                "sample_count": len(numeric_df),
                "null_count": null_count,
                "anomalies_detected": anomaly_count,
                "anomalies_percentage": round(anomaly_pct, 2),
                "normal_count": normal_count,
                "anomaly_scores": {
                    "mean": float(normalized_scores.mean()),
                    "std": float(normalized_scores.std()),
                    "min": float(normalized_scores.min()),
                    "max": float(normalized_scores.max()),
                },
            }
            
            self.logger.info(
                f"LOF: {anomaly_count} anomalies ({anomaly_pct:.2f}%) detected"
            )
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"LOF failed: {str(e)}")
            result.success = False
            self.logger.error(f"Error in LOF: {str(e)}")
            return result
