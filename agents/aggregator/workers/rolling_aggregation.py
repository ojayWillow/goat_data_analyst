"""RollingAggregation - Multi-column rolling aggregations.

Rolling aggregations with full validation and quality scoring
per A+ worker guidance.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any

from .base_worker import BaseWorker, WorkerResult, ErrorType, WorkerError
from .validation_utils import ValidationUtils
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
MIN_WINDOW = 1
MAX_WINDOW = 1000
DEFAULT_WINDOW = 5
VALID_AGG_OPS = ['mean', 'sum', 'min', 'max', 'std', 'count', 'median']


class RollingAggregation(BaseWorker):
    """Worker that performs rolling aggregations on multiple columns.
    
    Performs rolling window aggregations including:
    - Configurable window sizes
    - Multiple aggregation operations per column
    - Null value tracking
    - Quality scoring
    """
    
    def __init__(self) -> None:
        """Initialize RollingAggregation."""
        super().__init__("RollingAggregation")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.columns_processed: int = 0
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - window_size is valid
        - columns (if provided) exist and are numeric
        - agg_dict (if provided) has valid operations
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check window_size
        window_size = kwargs.get('window_size', DEFAULT_WINDOW)
        if not isinstance(window_size, int):
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"window_size must be integer, got {type(window_size).__name__}",
                severity="error",
                suggestion="Provide window_size as positive integer"
            )
        
        if window_size < MIN_WINDOW or window_size > MAX_WINDOW:
            return WorkerError(
                ErrorType.VALUE_ERROR,
                f"window_size must be between {MIN_WINDOW} and {MAX_WINDOW}, got {window_size}",
                severity="error",
                suggestion=f"Use value between {MIN_WINDOW} and {MAX_WINDOW}"
            )
        
        # Check numeric columns exist
        numeric_error = ValidationUtils.validate_numeric_columns(df)
        if numeric_error:
            return numeric_error
        
        # Check columns if provided
        columns = kwargs.get('columns')
        if columns:
            if isinstance(columns, str):
                columns = [columns]
            
            col_error = ValidationUtils.validate_columns_exist(
                df, columns, "rolling aggregation columns"
            )
            if col_error:
                return col_error
            
            numeric_error = ValidationUtils.validate_numeric_columns(df, columns)
            if numeric_error:
                return numeric_error
        
        # Check agg_dict if provided
        agg_dict = kwargs.get('agg_dict')
        if agg_dict:
            if not isinstance(agg_dict, dict):
                return WorkerError(
                    ErrorType.TYPE_ERROR,
                    f"agg_dict must be dict, got {type(agg_dict).__name__}",
                    severity="error",
                    suggestion="Provide agg_dict as dict mapping columns to operations"
                )
        
        return None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Perform rolling aggregations on specified columns.
        
        Args:
            df: DataFrame to process
            window_size: Size of rolling window (default: 5)
            columns: Columns to aggregate (default: all numeric)
            agg_dict: Dict mapping columns to operations
            
        Returns:
            WorkerResult with aggregation results
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_rolling_agg(**kwargs)
            
            # Track success with error intelligence
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="RollingAggregation",
                operation="rolling_aggregation",
                context={
                    "window_size": kwargs.get('window_size', DEFAULT_WINDOW),
                    "success": result.success,
                    "quality_score": result.quality_score,
                    "columns_processed": self.columns_processed
                }
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="RollingAggregation",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "window_size": kwargs.get('window_size', DEFAULT_WINDOW),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed
                }
            )
            raise
    
    def _run_rolling_agg(self, **kwargs) -> WorkerResult:
        """Perform rolling aggregation.
        
        Returns:
            WorkerResult with aggregation results or errors
        """
        df = kwargs.get('df')
        window_size = kwargs.get('window_size', DEFAULT_WINDOW)
        columns = kwargs.get('columns')
        agg_dict = kwargs.get('agg_dict')
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.columns_processed = 0
        
        result = self._create_result(
            task_type="rolling_aggregation",
            quality_score=1.0
        )
        
        self.logger.info(
            f"Performing rolling aggregation: window_size={window_size}"
        )
        
        try:
            # Get numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(
                    result,
                    ErrorType.MISSING_DATA,
                    "No numeric columns found in DataFrame",
                    severity="error",
                    suggestion="DataFrame must contain numeric columns"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            # Filter to specified columns if provided
            if columns:
                if isinstance(columns, str):
                    columns = [columns]
                numeric_df = numeric_df[[col for col in columns if col in numeric_df.columns]]
            
            # Set default aggregation dict if not provided
            if agg_dict is None:
                agg_dict = {col: ['mean', 'sum'] for col in numeric_df.columns}
            else:
                # Filter to specified columns
                agg_dict = {k: v for k, v in agg_dict.items() if k in numeric_df.columns}
            
            if not agg_dict:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "No valid columns to aggregate",
                    severity="error",
                    suggestion="Ensure agg_dict contains valid numeric columns"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            self.columns_processed = len(agg_dict)
            
            # Perform rolling aggregation
            rolling_obj = numeric_df.rolling(window=window_size, min_periods=1)
            agg_results = rolling_obj.agg(agg_dict)
            
            # Count null values created by window
            nan_count = agg_results.isna().sum().sum()
            
            if nan_count > 0:
                self._add_warning(
                    result,
                    f"Rolling aggregation created {nan_count} NaN values. "
                    f"First {window_size - 1} rows may have partial windows."
                )
            
            # Build result data
            result.data = {
                "window_size": window_size,
                "columns_aggregated": list(agg_dict.keys()),
                "operations_per_column": {k: v if isinstance(v, list) else [v] for k, v in agg_dict.items()},
                "rows_processed": len(numeric_df),
                "columns_count": len(agg_dict),
                "output_shape": list(agg_results.shape),
                "null_values_in_output": int(nan_count),
                "total_operations": sum(len(v) if isinstance(v, list) else 1 for v in agg_dict.values()),
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                nan_values=nan_count,
                window_size=window_size
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Rolling aggregation completed: window={window_size}, "
                f"{len(agg_dict)} columns, {self.columns_processed} processed, "
                f"quality score: {quality_score:.3f}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Rolling aggregation failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                details={
                    "exception_type": type(e).__name__,
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed
                },
                suggestion="Check window_size and aggregation function validity"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        nan_values: int = 0,
        window_size: int = DEFAULT_WINDOW
    ) -> float:
        """Calculate quality score based on rolling operation quality.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed
            nan_values: NaN values created by window
            window_size: Size of rolling window
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from processing
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            return 1.0
        
        base_quality = rows_processed / total_rows
        
        # Minimal penalty for NaN (expected behavior of rolling window)
        nan_penalty = min(0.1, (nan_values / (rows_processed * window_size)) * 0.1) if rows_processed > 0 else 0
        
        quality_score = max(0.0, base_quality - nan_penalty)
        
        return min(1.0, quality_score)
