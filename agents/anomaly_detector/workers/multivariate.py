"""Multivariate Worker - Mahalanobis distance-based anomaly detection.

This worker implements multivariate anomaly detection using Mahalanobis distance.
Mahalanobis distance accounts for correlations between variables and different scales,
making it suitable for multivariate outlier detection.

All methods follow A+ quality standards with comprehensive error handling and quality tracking.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# ===== CONSTANTS =====
DEFAULT_PERCENTILE: float = 95.0
MIN_REQUIRED_SAMPLES: int = 2

logger = get_logger(__name__)


class MultivariateWorker(BaseWorker):
    """Worker that performs multivariate anomaly detection using Mahalanobis distance.
    
    Mahalanobis distance is a measure of distance between a point P and a distribution D.
    It accounts for correlations between variables and different scales. This makes it
    ideal for detecting multivariate outliers where anomalies may not be evident in
    individual dimensions.
    
    Formula: D = sqrt((x-m)^T * Σ^-1 * (x-m))
    where x is the data point, m is the mean, and Σ is the covariance matrix.
    
    Advantages:
    - Handles correlations between variables
    - Accounts for different scales
    - Detects points that are far from the centroid in the scaled/rotated space
    
    Example:
        >>> worker = MultivariateWorker()
        >>> df = pd.DataFrame({'x': [1, 2, 3, 100], 'y': [10, 20, 30, 1000]})
        >>> result = worker.execute(df=df, feature_cols=['x', 'y'], percentile=95)
        >>> print(f"Outliers: {result.data['outliers_count']}")
        Outliers: 1
    """
    
    def __init__(self) -> None:
        """Initialize MultivariateWorker with error intelligence."""
        super().__init__("MultivariateWorker")
        self.error_intelligence: ErrorIntelligence = ErrorIntelligence()
        self.logger = get_logger("MultivariateWorker")
        if not SKLEARN_AVAILABLE:
            self.logger.warning("scikit-learn not available - Multivariate detection disabled")
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute multivariate anomaly detection.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            feature_cols (List[str]): List of columns to use for detection
            percentile (float, optional): Percentile threshold for outliers (default 95)
            **kwargs: Additional arguments
        
        Returns:
            WorkerResult: Multivariate anomaly results with:
                - outliers_count: Number of outliers found
                - outliers_percentage: Percentage of outliers
                - distance_threshold: Mahalanobis distance threshold
                - top_outliers: List of most anomalous points
        
        Example:
            >>> df = pd.DataFrame({
            ...     'feature1': [1, 2, 3, 4, 5, 100],
            ...     'feature2': [10, 20, 30, 40, 50, 1000]
            ... })
            >>> result = worker.execute(
            ...     df=df,
            ...     feature_cols=['feature1', 'feature2'],
            ...     percentile=90
            ... )
            >>> assert result.success
        """
        try:
            result: WorkerResult = self._run_multivariate(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="MultivariateWorker",
                operation="multivariate_detection",
                context={
                    "feature_cols": str(kwargs.get('feature_cols', [])),
                    "percentile": kwargs.get('percentile', DEFAULT_PERCENTILE)
                }
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="MultivariateWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "feature_cols": str(kwargs.get('feature_cols', [])),
                    "percentile": kwargs.get('percentile', DEFAULT_PERCENTILE)
                }
            )
            raise
    
    def _run_multivariate(self, **kwargs: Any) -> WorkerResult:
        """Perform multivariate detection.
        
        Args:
            **kwargs: Parameters including df, feature_cols, percentile
        
        Returns:
            WorkerResult with detection results
        """
        df: Optional[pd.DataFrame] = kwargs.get('df')
        feature_cols: List[str] = kwargs.get('feature_cols', [])
        percentile: float = kwargs.get('percentile', DEFAULT_PERCENTILE)
        
        result: WorkerResult = self._create_result(
            task_type="multivariate_detection",
            quality_score=1.0
        )
        
        # ===== VALIDATE SKLEARN AVAILABILITY =====
        if not SKLEARN_AVAILABLE:
            self._add_error(result, ErrorType.LOAD_ERROR, "scikit-learn not installed")
            result.success = False
            return result
        
        # ===== VALIDATE INPUTS =====
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        if not feature_cols:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "No feature columns specified")
            result.success = False
            return result
        
        # Validate feature columns exist
        missing_cols: List[str] = [col for col in feature_cols if col not in df.columns]
        if missing_cols:
            self._add_error(
                result,
                ErrorType.INVALID_COLUMN,
                f"Columns not found: {missing_cols}"
            )
            result.success = False
            return result
        
        # Validate percentile
        if not (0 < percentile < 100):
            self._add_error(
                result,
                ErrorType.INVALID_PARAMETER,
                f"Percentile must be between 0 and 100, got {percentile}"
            )
            result.success = False
            return result
        
        try:
            # Extract features and drop NaNs
            df_clean: pd.DataFrame = df[feature_cols].dropna()
            null_count: int = len(df[feature_cols]) - len(df_clean)
            
            if null_count > 0:
                self._add_warning(result, f"Found {null_count} null values - removed rows with NaNs")
            
            # Validate minimum samples
            min_samples: int = len(feature_cols) + 1
            if len(df_clean) < min_samples:
                self._add_error(
                    result,
                    ErrorType.INSUFFICIENT_DATA,
                    f"Insufficient samples ({len(df_clean)}) for features ({len(feature_cols)}), need {min_samples}"
                )
                result.success = False
                return result
            
            # Standardize data
            from sklearn.preprocessing import StandardScaler
            scaler: StandardScaler = StandardScaler()
            scaled_data: np.ndarray = scaler.fit_transform(df_clean)
            
            # Calculate covariance matrix
            cov_matrix: np.ndarray = np.cov(scaled_data.T)
            mean: np.ndarray = scaled_data.mean(axis=0)
            
            # Calculate inverse covariance matrix
            try:
                inv_cov: np.ndarray = np.linalg.inv(cov_matrix)
            except np.linalg.LinAlgError:
                # Use pseudo-inverse if singular
                inv_cov: np.ndarray = np.linalg.pinv(cov_matrix)
                self._add_warning(result, "Singular covariance matrix - using pseudo-inverse")
            
            # Calculate Mahalanobis distance for each point
            distances: List[float] = []
            for point in scaled_data:
                diff: np.ndarray = point - mean
                distance: float = np.sqrt(np.clip(diff.dot(inv_cov).dot(diff.T), 0, None))
                distances.append(distance)
            
            distances_array: np.ndarray = np.array(distances)
            threshold: np.floating = np.percentile(distances_array, percentile)
            
            # Identify outliers
            outlier_mask: np.ndarray = distances_array > threshold
            outlier_count: int = int(outlier_mask.sum())
            outlier_pct: float = (outlier_count / len(df_clean) * 100) if len(df_clean) > 0 else 0
            outlier_indices: list = df_clean[outlier_mask].index.tolist()
            
            # Create outlier dataframe with distances
            outlier_df: pd.DataFrame = pd.DataFrame({
                'index': df_clean.index,
                'mahalanobis_distance': distances_array,
                'is_outlier': outlier_mask
            }).sort_values('mahalanobis_distance', ascending=False)
            
            top_outliers: List[Dict[str, Any]] = outlier_df[outlier_df['is_outlier']].head(20).to_dict(orient="records")
            
            # Calculate quality score
            rows_failed: int = null_count + outlier_count
            total_rows: int = len(df[feature_cols])
            quality_score: float = max(
                0.0,
                1.0 - (rows_failed / total_rows) if total_rows > 0 else 0.0
            )
            result.quality_score = quality_score
            
            result.data = {
                "method": "Mahalanobis Distance",
                "features": feature_cols,
                "total_samples": len(df_clean),
                "null_count": null_count,
                "distance_threshold": float(threshold),
                "percentile": percentile,
                "outliers_count": outlier_count,
                "outliers_percentage": round(outlier_pct, 2),
                "distance_statistics": {
                    "mean": float(distances_array.mean()),
                    "std": float(distances_array.std()),
                    "min": float(distances_array.min()),
                    "max": float(distances_array.max()),
                    "median": float(np.median(distances_array)),
                },
                "top_outliers": top_outliers,
            }
            
            self.logger.info(
                f"Mahalanobis: {outlier_count} multivariate outliers ({outlier_pct:.2f}%)"
            )
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"Mahalanobis detection failed: {str(e)}")
            result.success = False
            self.logger.error(f"Error in Mahalanobis detection: {str(e)}")
            return result
