"""NumericAnalyzer - Worker for analyzing numeric columns.

Analyzes numeric data and computes descriptive statistics.
Provides comprehensive statistical summary for all numeric columns.
"""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# Constants
MIN_SAMPLES_FOR_STATS = 1  # Minimum samples needed for statistics
QUALITY_THRESHOLD = 0.8  # Threshold for good quality


class NumericAnalyzer(BaseWorker):
    """Worker that analyzes numeric columns in data.
    
    Analyzes all numeric columns in a DataFrame and computes
    comprehensive descriptive statistics including:
    - Central tendency: mean, median
    - Dispersion: std, variance, range, IQR
    - Distribution: quartiles, skewness, kurtosis
    - Extremes: min, max
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame to analyze (required)
    
    Output Format:
        result.data contains:
            numeric_columns: List of numeric column names
            statistics: Dict mapping column names to statistics dicts
            columns_analyzed: Count of successfully analyzed columns
    
    Quality Score:
        Calculated as:
        - 1.0: All columns analyzed successfully
        - 1.0 - (warnings * 0.1) - (errors * 0.2): Reduced by warnings/errors
        - Minimum: 0.0
    
    Example:
        >>> analyzer = NumericAnalyzer()
        >>> result = analyzer.safe_execute(df=df)
        >>> if result.success:
        ...     stats = result.data['statistics']
        ...     print(f"Mean: {stats['column_name']['mean']}")
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize NumericAnalyzer worker."""
        super().__init__("NumericAnalyzer")
        self.error_intelligence = ErrorIntelligence()
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters.
        
        Args:
            **kwargs: Must contain 'df' key with DataFrame value
            
        Returns:
            WorkerError if validation fails, None if valid
        """
        df = kwargs.get('df')
        
        if df is None:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="No DataFrame provided (df=None)",
                severity="error",
                suggestion="Call with df parameter: analyzer.safe_execute(df=your_dataframe)"
            )
        
        if not isinstance(df, pd.DataFrame):
            return WorkerError(
                error_type=ErrorType.TYPE_ERROR,
                message=f"Expected DataFrame, got {type(df).__name__}",
                severity="error",
                details={"received_type": str(type(df))},
                suggestion="Pass a pandas DataFrame as the df parameter"
            )
        
        if df.empty:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="DataFrame is empty (0 rows)",
                severity="error",
                details={"shape": str(df.shape)},
                suggestion="Ensure DataFrame has data before analysis"
            )
        
        return None
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Analyze numeric columns in DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            WorkerResult with numeric statistics
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        # Note: validate_input() already checked in safe_execute()
        df = kwargs.get('df')
        
        result = self._create_result(
            task_type="numeric_analysis",
            quality_score=1.0
        )
        
        try:
            self.logger.info(f"Analyzing numeric columns from {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Select numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                self.logger.warning("No numeric columns found")
                self._add_warning(result, "No numeric columns found in data")
                result.data = {
                    "numeric_columns": [],
                    "statistics": {},
                    "columns_analyzed": 0,
                }
                result.quality_score = 0.5
                return result
            
            # Analyze each numeric column
            stats: Dict[str, Any] = {}
            errors_found: list = []
            warnings_found: list = []
            
            for col in numeric_cols:
                try:
                    series = df[col].dropna()
                    
                    if len(series) < MIN_SAMPLES_FOR_STATS:
                        warnings_found.append(f"Column '{col}' has fewer than {MIN_SAMPLES_FOR_STATS} non-null values")
                        continue
                    
                    # Compute statistics
                    col_stats = self._compute_statistics(col, series)
                    stats[col] = col_stats
                    
                except Exception as e:
                    errors_found.append(f"Error analyzing column '{col}': {str(e)}")
                    self.logger.error(f"Error analyzing column {col}: {e}", exc_info=True)
            
            # Add warnings to result
            for warning in warnings_found:
                self._add_warning(result, warning)
            
            # Add errors to result
            if errors_found:
                for error_msg in errors_found:
                    self._add_error(
                        result,
                        ErrorType.COMPUTATION_ERROR,
                        error_msg,
                        severity="warning",
                        suggestion="Check data types and column values"
                    )
            
            result.data = {
                "numeric_columns": numeric_cols,
                "statistics": stats,
                "columns_analyzed": len(stats),
            }
            
            # Calculate quality score: 1.0 - (warnings * 0.1) - (errors * 0.2)
            quality_score = 1.0
            quality_score -= (len(warnings_found) * 0.1)
            quality_score -= (len(errors_found) * 0.2)
            quality_score = max(0, min(1, quality_score))
            result.quality_score = quality_score
            
            # Set success based on whether we analyzed any columns
            result.success = len(stats) > 0
            
            self.logger.info(
                f"Analyzed {len(stats)}/{len(numeric_cols)} numeric columns "
                f"(quality: {quality_score:.2f})"
            )
            
            return result
        
        except Exception as e:
            """Catch unexpected exceptions.
            
            Should not happen if code is correct, but safety net ensures
            WorkerResult is always returned.
            """
            self.logger.error(f"NumericAnalyzer execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.UNKNOWN_ERROR,
                str(e),
                severity="critical",
                details={
                    "error_type": type(e).__name__,
                    "shape": str(df.shape)
                },
                suggestion="Check DataFrame structure and data types"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
    
    def _compute_statistics(self, col_name: str, series: pd.Series) -> Dict[str, Any]:
        """Compute statistics for a numeric column.
        
        Args:
            col_name: Column name (for logging)
            series: Series data (NaN already removed)
            
        Returns:
            Dictionary of statistics
            
        Raises:
            Exception: If computation fails (caller handles)
        """
        try:
            return {
                "count": int(len(series)),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "var": float(series.var()),
                "min": float(series.min()),
                "max": float(series.max()),
                "q25": float(series.quantile(0.25)),
                "q50": float(series.quantile(0.50)),
                "q75": float(series.quantile(0.75)),
                "iqr": float(series.quantile(0.75) - series.quantile(0.25)),
                "range": float(series.max() - series.min()),
                "skewness": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
            }
        except Exception as e:
            self.logger.error(f"Error computing statistics for '{col_name}': {e}", exc_info=True)
            raise
