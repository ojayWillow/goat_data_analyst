"""IsolationForest - Isolation Forest anomaly detection.

This worker implements Isolation Forest algorithm which isolates anomalies by randomly
selecting features and split values. Works well with high-dimensional data and is
efficient for large datasets.

All methods follow A+ quality standards with comprehensive error handling and quality tracking.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest as SKIsolationForest
from typing import Any, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

# ===== CONSTANTS =====
DEFAULT_CONTAMINATION: float = 0.1
DEFAULT_N_ESTIMATORS: int = 100
MIN_REQUIRED_SAMPLES: int = 2

logger = get_logger(__name__)


class IsolationForest(BaseWorker):
    """Worker that detects anomalies using Isolation Forest algorithm.
    
    Isolation Forest algorithm is based on the concept that anomalies are few and different,
    and therefore they are easier to isolate. The algorithm works by randomly selecting
    features and thresholds, which results in different trees in the forest. The anomaly
    score for each data point is computed as the average path length in the trees.
    
    Advantages:
    - Efficient for high-dimensional data
    - Works well with large datasets
    - Does not require distance calculations
    - Handles mixed data types better than distance-based methods
    
    Example:
        >>> worker = IsolationForest()
        >>> df = pd.DataFrame({'value': [1, 2, 3, 100, 4, 5]})
        >>> result = worker.execute(df=df, contamination=0.1, n_estimators=100)
        >>> print(f"Anomalies: {result.data['anomalies_detected']}")
        Anomalies: 1
    """
    
    def __init__(self) -> None:
        """Initialize IsolationForest worker with error intelligence."""
        super().__init__("IsolationForest")
        self.error_intelligence: ErrorIntelligence = ErrorIntelligence()
        self.logger = get_logger("IsolationForest")
    
    def execute(
        self,
        df: Optional[pd.DataFrame] = None,
        contamination: float = DEFAULT_CONTAMINATION,
        n_estimators: int = DEFAULT_N_ESTIMATORS,
        **kwargs: Any
    ) -> WorkerResult:
        """Detect anomalies using Isolation Forest.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            contamination (float): Proportion of anomalies (0.0 to 0.5). Default 0.1.
            n_estimators (int): Number of isolation trees. Default 100.
            **kwargs: Additional arguments
        
        Returns:
            WorkerResult: Detection results with:
                - anomalies_detected: Number of anomalies found
                - normal_count: Number of normal samples
                - anomaly_scores_mean: Mean anomaly score
                - anomaly_scores_std: Std dev of anomaly scores
        
        Example:
            >>> df = pd.DataFrame({'a': [1, 2, 3, 100], 'b': [10, 20, 30, 1000]})
            >>> result = worker.execute(df=df, contamination=0.25)
            >>> assert result.success
            >>> assert result.data['anomalies_detected'] == 1
        """
        try:
            result: WorkerResult = self._run_isolation_forest(df, contamination, n_estimators, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="IsolationForest",
                operation="isolation_forest_detection",
                context={
                    "contamination": contamination,
                    "n_estimators": n_estimators
                }
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="IsolationForest",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "contamination": contamination,
                    "n_estimators": n_estimators
                }
            )
            raise
    
    def _run_isolation_forest(
        self,
        df: Optional[pd.DataFrame],
        contamination: float,
        n_estimators: int,
        **kwargs: Any
    ) -> WorkerResult:
        """Perform Isolation Forest detection.
        
        Args:
            df: Input DataFrame
            contamination: Expected contamination rate
            n_estimators: Number of trees
            **kwargs: Additional parameters
        
        Returns:
            WorkerResult with anomaly detection results
        """
        result: WorkerResult = self._create_result(
            task_type="isolation_forest_detection",
            quality_score=1.0
        )
        
        # ===== VALIDATE INPUTS =====
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
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
        
        # Validate n_estimators parameter
        if not isinstance(n_estimators, int) or n_estimators < 1:
            self._add_error(
                result,
                ErrorType.INVALID_PARAMETER,
                f"n_estimators must be positive integer, got {n_estimators}"
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
            
            # Run Isolation Forest
            iso_forest: SKIsolationForest = SKIsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                random_state=42,
                n_jobs=-1
            )
            
            predictions: np.ndarray = iso_forest.fit_predict(numeric_df)
            anomaly_scores: np.ndarray = iso_forest.score_samples(numeric_df)
            
            # Normalize scores to 0-1 range (higher = more anomalous)
            min_score: np.floating = anomaly_scores.min()
            max_score: np.floating = anomaly_scores.max()
            score_range: np.floating = max_score - min_score
            
            if score_range > 1e-10:
                normalized_scores: np.ndarray = (anomaly_scores - min_score) / score_range
            else:
                normalized_scores: np.ndarray = np.zeros_like(anomaly_scores)
            
            # Calculate statistics
            anomaly_count: int = int((predictions == -1).sum())
            normal_count: int = int((predictions == 1).sum())
            anomaly_pct: float = (anomaly_count / len(predictions) * 100) if len(predictions) > 0 else 0
            
            # Calculate quality score
            rows_failed: int = null_count + anomaly_count
            total_rows: int = len(df)
            quality_score: float = max(
                0.0,
                1.0 - (rows_failed / total_rows) if total_rows > 0 else 0.0
            )
            result.quality_score = quality_score
            
            result.data = {
                "method": "Isolation Forest",
                "contamination": contamination,
                "n_estimators": n_estimators,
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
                f"Isolation Forest: {anomaly_count} anomalies ({anomaly_pct:.2f}%) detected"
            )
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"Isolation Forest failed: {str(e)}")
            result.success = False
            self.logger.error(f"Error in Isolation Forest: {str(e)}")
            return result
