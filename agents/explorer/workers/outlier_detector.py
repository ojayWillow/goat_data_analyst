"""OutlierDetector - Worker for detecting outliers in data.

Detects outliers using the Z-score method and other statistical approaches.
"""

from typing import Any, Dict, Optional, List
import pandas as pd
import numpy as np
from scipy import stats

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_ZSCORE_THRESHOLD = 3.0  # Default Z-score threshold (3 = ~0.3% outliers in normal)
MIN_SAMPLES = 2  # Minimum samples for Z-score
IQR_MULTIPLIER = 1.5  # Standard multiplier for IQR method


class OutlierDetector(BaseWorker):
    """Worker that detects outliers using Z-score and IQR methods.
    
    Identifies statistical outliers using multiple approaches:
    - Z-score: Points that are 3+ standard deviations from mean
    - IQR: Points beyond 1.5 × IQR from quartiles
    
    Z-score interpretation:
        - |z| > 3: Extremely rare (< 0.3% in normal distribution)
        - |z| > 2: Unusual (< 5% in normal distribution)
        - |z| > 1: Somewhat unusual (< 32% in normal distribution)
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame containing data (required)
        column: str - Column name to analyze (required)
        threshold: float - Z-score threshold (default: 3.0)
    
    Output Format:
        result.data contains:
            column: Analyzed column name
            method: Detection method ('z-score', 'iqr', or 'both')
            threshold: Z-score threshold used
            outlier_count: Number of outliers detected
            outlier_percentage: Percentage of values that are outliers
            outlier_indices: List of outlier indices (first 100)
    
    Quality Score:
        - 1.0: Successfully detected outliers
        - 0.0: Failed or insufficient data
    
    Example:
        >>> detector = OutlierDetector()
        >>> result = detector.safe_execute(df=df, column='revenue', threshold=3.0)
        >>> if result.success:
        ...     print(f"Found {result.data['outlier_count']} outliers")
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize OutlierDetector worker."""
        super().__init__("OutlierDetector")
        self.error_intelligence = ErrorIntelligence()
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters.
        
        Args:
            **kwargs: Must contain 'df' and 'column' keys
            
        Returns:
            WorkerError if validation fails, None if valid
        """
        df = kwargs.get('df')
        column = kwargs.get('column')
        threshold = kwargs.get('threshold', DEFAULT_ZSCORE_THRESHOLD)
        
        if df is None:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="No DataFrame provided (df=None)",
                severity="error",
                suggestion="Provide df parameter"
            )
        
        if not isinstance(df, pd.DataFrame):
            return WorkerError(
                error_type=ErrorType.TYPE_ERROR,
                message=f"Expected DataFrame, got {type(df).__name__}",
                severity="error",
                suggestion="df must be a pandas DataFrame"
            )
        
        if column is None:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="No column specified",
                severity="error",
                suggestion="Provide column parameter"
            )
        
        if column not in df.columns:
            return WorkerError(
                error_type=ErrorType.INVALID_PARAMETER,
                message=f"Column '{column}' not found in DataFrame",
                severity="error",
                details={"available_columns": list(df.columns)},
                suggestion=f"Column must be one of: {list(df.columns)}"
            )
        
        if not isinstance(threshold, (int, float)):
            return WorkerError(
                error_type=ErrorType.INVALID_PARAMETER,
                message=f"Threshold must be numeric, got {type(threshold).__name__}",
                severity="error",
                suggestion="Provide threshold as number"
            )
        
        return None
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Detect outliers in specified column.
        
        Args:
            df: DataFrame containing data
            column: Column name to analyze
            threshold: Z-score threshold (default: 3.0)
            
        Returns:
            WorkerResult with outlier detection results
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        df = kwargs.get('df')
        column = kwargs.get('column')
        threshold = kwargs.get('threshold', DEFAULT_ZSCORE_THRESHOLD)
        
        result = self._create_result(task_type="outlier_detection")
        
        try:
            self.logger.info(f"Detecting outliers in column '{column}' (threshold: {threshold})")
            
            # Remove NaN values
            series = df[column].dropna()
            
            if len(series) < MIN_SAMPLES:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    f"Need at least {MIN_SAMPLES} samples, got {len(series)}",
                    severity="warning"
                )
                result.success = False
                result.quality_score = 0.0
                return result
            
            # Z-score method
            z_scores = np.abs(stats.zscore(series, nan_policy='omit'))
            outliers_zscore = z_scores > threshold
            
            # IQR method
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            outliers_iqr = (series < Q1 - IQR_MULTIPLIER * IQR) | (series > Q3 + IQR_MULTIPLIER * IQR)
            
            # Combined: outliers detected by either method
            outliers_combined = outliers_zscore | outliers_iqr
            
            # Get outlier indices and values (first 100)
            outlier_indices = np.where(outliers_combined)[0].tolist()[:100]
            outlier_values = series.iloc[outlier_indices].tolist() if outlier_indices else []
            
            result.data = {
                "column": column,
                "method": "z-score + IQR",
                "zscore_threshold": threshold,
                "iqr_multiplier": IQR_MULTIPLIER,
                "outlier_count": int(outliers_combined.sum()),
                "outlier_percentage": round(outliers_combined.sum() / len(series) * 100, 2),
                "zscore_outliers": int(outliers_zscore.sum()),
                "iqr_outliers": int(outliers_iqr.sum()),
                "sample_size": len(series),
                "Q1": float(Q1),
                "Q3": float(Q3),
                "IQR": float(IQR),
                "lower_bound": float(Q1 - IQR_MULTIPLIER * IQR),
                "upper_bound": float(Q3 + IQR_MULTIPLIER * IQR),
                "outlier_indices": outlier_indices,
            }
            
            result.success = True
            result.quality_score = 1.0
            
            self.logger.info(
                f"Outlier detection complete for '{column}': "
                f"found {int(outliers_combined.sum())} outliers ({result.data['outlier_percentage']}%)"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"OutlierDetector execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Outlier detection failed: {str(e)}",
                severity="critical",
                suggestion="Check column contains numeric data"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
