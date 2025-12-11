"""Multivariate Worker - Mahalanobis distance-based anomaly detection."""

import pandas as pd
import numpy as np
from typing import Any, Dict, List

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = get_logger(__name__)


class MultivariateWorker(BaseWorker):
    """Worker that performs multivariate anomaly detection using Mahalanobis distance.
    
    Mahalanobis distance accounts for correlations between variables and
    different scales, making it suitable for multivariate outlier detection.
    """
    
    def __init__(self):
        """Initialize MultivariateWorker."""
        super().__init__("MultivariateWorker")
        self.error_intelligence = ErrorIntelligence()
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available - Multivariate detection disabled")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute multivariate anomaly detection.
        
        Args:
            df: DataFrame to analyze
            feature_cols: List of columns to use for detection
            percentile: Percentile threshold for outliers (default 95)
            
        Returns:
            WorkerResult with multivariate anomaly results
        """
        try:
            result = self._run_multivariate(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="MultivariateWorker",
                operation="multivariate_detection",
                context={"feature_cols": str(kwargs.get('feature_cols', []))}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="MultivariateWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"feature_cols": str(kwargs.get('feature_cols', []))}
            )
            raise
    
    def _run_multivariate(self, **kwargs) -> WorkerResult:
        """Perform multivariate detection."""
        df = kwargs.get('df')
        feature_cols = kwargs.get('feature_cols', [])
        percentile = kwargs.get('percentile', 95)
        
        # Create empty result
        result = self._create_result(
            task_type="multivariate_detection",
            quality_score=1.0
        )
        
        # Validate sklearn availability
        if not SKLEARN_AVAILABLE:
            self._add_error(result, ErrorType.SKLEARN_UNAVAILABLE, "scikit-learn not installed")
            result.success = False
            return result
        
        # Validate inputs
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        if not feature_cols:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "No feature columns specified")
            result.success = False
            return result
        
        # Validate feature columns exist
        missing_cols = [col for col in feature_cols if col not in df.columns]
        if missing_cols:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Columns not found: {missing_cols}")
            result.success = False
            return result
        
        # Validate percentile
        if not (0 < percentile < 100):
            self._add_error(result, ErrorType.INVALID_PARAMETER, "percentile must be between 0 and 100")
            result.success = False
            return result
        
        try:
            # Extract features and drop NaNs
            df_clean = df[feature_cols].dropna()
            
            if len(df_clean) < len(feature_cols) + 1:
                self._add_error(
                    result,
                    ErrorType.INSUFFICIENT_DATA,
                    f"Insufficient samples ({len(df_clean)}) for features ({len(feature_cols)})"
                )
                result.success = False
                return result
            
            # Standardize data
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df_clean)
            
            # Calculate covariance matrix
            cov_matrix = np.cov(scaled_data.T)
            mean = scaled_data.mean(axis=0)
            
            # Calculate inverse covariance matrix
            try:
                inv_cov = np.linalg.inv(cov_matrix)
            except np.linalg.LinAlgError:
                # Use pseudo-inverse if singular
                inv_cov = np.linalg.pinv(cov_matrix)
                self._add_warning(result, "Singular covariance matrix - using pseudo-inverse")
            
            # Calculate Mahalanobis distance for each point
            distances = []
            for point in scaled_data:
                diff = point - mean
                distance = np.sqrt(np.clip(diff.dot(inv_cov).dot(diff.T), 0, None))
                distances.append(distance)
            
            distances = np.array(distances)
            threshold = np.percentile(distances, percentile)
            
            # Identify outliers
            outlier_mask = distances > threshold
            outlier_count = outlier_mask.sum()
            outlier_pct = (outlier_count / len(df_clean) * 100) if len(df_clean) > 0 else 0
            outlier_indices = df_clean[outlier_mask].index.tolist()
            
            # Create outlier dataframe with distances
            outlier_df = pd.DataFrame({
                'index': df_clean.index,
                'mahalanobis_distance': distances,
                'is_outlier': outlier_mask
            }).sort_values('mahalanobis_distance', ascending=False)
            
            top_outliers = outlier_df[outlier_df['is_outlier']].head(20).to_dict(orient="records")
            
            result.data = {
                "method": "Mahalanobis Distance",
                "features": feature_cols,
                "total_samples": len(df_clean),
                "distance_threshold": float(threshold),
                "percentile": percentile,
                "outliers_count": int(outlier_count),
                "outliers_percentage": round(outlier_pct, 2),
                "distance_statistics": {
                    "mean": float(distances.mean()),
                    "std": float(distances.std()),
                    "min": float(distances.min()),
                    "max": float(distances.max()),
                    "median": float(np.median(distances)),
                },
                "top_outliers": top_outliers,
            }
            
            logger.info(f"Mahalanobis: {outlier_count} multivariate outliers ({outlier_pct:.2f}%)")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, str(e))
            result.success = False
            return result
