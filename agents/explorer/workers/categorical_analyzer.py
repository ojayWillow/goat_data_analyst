"""CategoricalAnalyzer - Worker for analyzing categorical columns.

Analyzes categorical data and computes value counts and distributions.
Provides comprehensive categorical summary for all object/string columns.
"""

from typing import Any, Dict, Optional
import pandas as pd

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# Constants
TOP_VALUES_COUNT = 10  # Number of top values to include in result
QUALITY_THRESHOLD = 0.8  # Threshold for good quality


class CategoricalAnalyzer(BaseWorker):
    """Worker that analyzes categorical columns in data.
    
    Analyzes all object/string columns in a DataFrame and computes
    comprehensive categorical statistics including:
    - Value counts and frequencies
    - Unique value counts
    - Null/missing value analysis
    - Most/least common values
    - Top 10 values distribution
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame to analyze (required)
    
    Output Format:
        result.data contains:
            categorical_columns: List of categorical column names
            statistics: Dict mapping column names to statistics dicts
            columns_analyzed: Count of successfully analyzed columns
    
    Quality Score:
        Calculated as:
        - 1.0: All columns analyzed successfully
        - 1.0 - (warnings * 0.1) - (errors * 0.2): Reduced by warnings/errors
        - Minimum: 0.0
    
    Example:
        >>> analyzer = CategoricalAnalyzer()
        >>> result = analyzer.safe_execute(df=df)
        >>> if result.success:
        ...     stats = result.data['statistics']
        ...     print(f"Unique values: {stats['column_name']['unique_values']}")
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize CategoricalAnalyzer worker."""
        super().__init__("CategoricalAnalyzer")
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
        """Analyze categorical columns in DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            WorkerResult with categorical statistics
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        # Note: validate_input() already checked in safe_execute()
        df = kwargs.get('df')
        
        result = self._create_result(
            task_type="categorical_analysis",
            quality_score=1.0
        )
        
        try:
            self.logger.info(f"Analyzing categorical columns from {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Select categorical columns (object/string types)
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if not categorical_cols:
                self.logger.warning("No categorical columns found")
                self._add_warning(result, "No categorical columns found in data")
                result.data = {
                    "categorical_columns": [],
                    "statistics": {},
                    "columns_analyzed": 0,
                }
                result.quality_score = 0.5
                return result
            
            # Analyze each categorical column
            stats: Dict[str, Any] = {}
            errors_found: list = []
            warnings_found: list = []
            
            for col in categorical_cols:
                try:
                    value_counts = df[col].value_counts()
                    
                    col_stats = self._compute_statistics(col, df[col], value_counts)
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
                "categorical_columns": categorical_cols,
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
                f"Analyzed {len(stats)}/{len(categorical_cols)} categorical columns "
                f"(quality: {quality_score:.2f})"
            )
            
            return result
        
        except Exception as e:
            """Catch unexpected exceptions.
            
            Should not happen if code is correct, but safety net ensures
            WorkerResult is always returned.
            """
            self.logger.error(f"CategoricalAnalyzer execute() failed: {e}", exc_info=True)
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
    
    def _compute_statistics(self, col_name: str, series: pd.Series, value_counts: pd.Series) -> Dict[str, Any]:
        """Compute statistics for a categorical column.
        
        Args:
            col_name: Column name (for logging)
            series: Series data (all values including nulls)
            value_counts: Value counts series
            
        Returns:
            Dictionary of statistics
            
        Raises:
            Exception: If computation fails (caller handles)
        """
        try:
            null_count = series.isna().sum()
            null_pct = (null_count / len(series) * 100) if len(series) > 0 else 0
            
            return {
                "count": int(len(series)),
                "unique_values": int(series.nunique()),
                "null_count": int(null_count),
                "null_percentage": round(null_pct, 2),
                "most_common": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "most_common_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                "most_common_percentage": round(
                    (value_counts.iloc[0] / len(series) * 100) if len(value_counts) > 0 else 0,
                    2
                ),
                "least_common": str(value_counts.index[-1]) if len(value_counts) > 0 else None,
                "least_common_count": int(value_counts.iloc[-1]) if len(value_counts) > 0 else 0,
                "top_10_values": dict(value_counts.head(TOP_VALUES_COUNT).items()),
            }
        except Exception as e:
            self.logger.error(f"Error computing categorical statistics for '{col_name}': {e}", exc_info=True)
            raise
