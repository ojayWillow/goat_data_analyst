"""WindowFunction - Rolling window operations.

Rolling window operations with full validation and quality scoring
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
DEFAULT_WINDOW = 3
VALID_OPERATIONS = ['mean', 'sum', 'std', 'min', 'max', 'count', 'median']
DEFAULT_OPERATIONS = ['mean']


class WindowFunction(BaseWorker):
    """Worker that calculates rolling window functions on data.
    
    Calculates window functions including:
    - Multiple operation types (mean, sum, std, min, max)
    - Configurable window sizes
    - Null value tracking
    - Quality scoring
    """
    
    def __init__(self) -> None:
        """Initialize WindowFunction."""
        super().__init__("WindowFunction")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.operations_applied: int = 0
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - window_size is valid integer
        - operations are valid
        - DataFrame has numeric columns
        
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
        
        # Check operations
        operations = kwargs.get('operations', DEFAULT_OPERATIONS)
        if operations:
            if isinstance(operations, str):
                operations = [operations]
            elif not isinstance(operations, list):
                return WorkerError(
                    ErrorType.TYPE_ERROR,
                    f"operations must be string or list, got {type(operations).__name__}",
                    severity="error",
                    suggestion="Provide operations as string or list of strings"
                )
            
            invalid_ops = [op for op in operations if op not in VALID_OPERATIONS]
            if invalid_ops:
                return WorkerError(
                    ErrorType.INVALID_PARAMETER,
                    f"Invalid operations: {invalid_ops}",
                    severity="error",
                    details={"valid_operations": VALID_OPERATIONS},
                    suggestion=f"Use: {', '.join(VALID_OPERATIONS)}"
                )
        
        # Check numeric columns
        numeric_error = ValidationUtils.validate_numeric_columns(df)
        if numeric_error:
            return numeric_error
        
        return None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Calculate rolling window operations.
        
        Args:
            df: DataFrame to process
            window_size: Size of rolling window (default: 3)
            operations: List of operations (default: ['mean'])
            
        Returns:
            WorkerResult with windowed data
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_window(**kwargs)
            
            # Track success with error intelligence
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="WindowFunction",
                operation="window_functions",
                context={
                    "window_size": kwargs.get('window_size', DEFAULT_WINDOW),
                    "operations": len(kwargs.get('operations', DEFAULT_OPERATIONS)),
                    "success": result.success,
                    "quality_score": result.quality_score
                }
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="WindowFunction",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "window_size": kwargs.get('window_size', DEFAULT_WINDOW),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed
                }
            )
            raise
    
    def _run_window(self, **kwargs) -> WorkerResult:
        """Perform window function calculation.
        
        Returns:
            WorkerResult with window results or errors
        """
        df = kwargs.get('df')
        window_size = kwargs.get('window_size', DEFAULT_WINDOW)
        operations = kwargs.get('operations', DEFAULT_OPERATIONS)
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.operations_applied = 0
        
        result = self._create_result(
            task_type="window_functions",
            quality_score=1.0
        )
        
        # Normalize operations
        if operations is None:
            operations = DEFAULT_OPERATIONS
        elif isinstance(operations, str):
            operations = [operations]
        
        self.logger.info(
            f"Computing window functions: window_size={window_size}, operations={operations}"
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
            
            # Check for null values
            null_count = numeric_df.isnull().sum().sum()
            if null_count > 0:
                self._add_warning(
                    result,
                    f"Found {null_count} null values. "
                    f"Window operations will produce NaN for incomplete windows."
                )
            
            # Apply window functions
            windowed_results: Dict[str, pd.DataFrame] = {}
            total_nan_count = 0
            
            for operation in operations:
                try:
                    if operation == 'mean':
                        windowed = numeric_df.rolling(window=window_size, min_periods=1).mean()
                    elif operation == 'sum':
                        windowed = numeric_df.rolling(window=window_size, min_periods=1).sum()
                    elif operation == 'std':
                        windowed = numeric_df.rolling(window=window_size, min_periods=1).std()
                    elif operation == 'min':
                        windowed = numeric_df.rolling(window=window_size, min_periods=1).min()
                    elif operation == 'max':
                        windowed = numeric_df.rolling(window=window_size, min_periods=1).max()
                    elif operation == 'count':
                        windowed = numeric_df.rolling(window=window_size, min_periods=1).count()
                    elif operation == 'median':
                        windowed = numeric_df.rolling(window=window_size, min_periods=1).median()
                    else:
                        self.logger.warning(f"Unknown operation: {operation}")
                        continue
                    
                    windowed_results[f'rolling_{operation}'] = windowed
                    total_nan_count += windowed.isna().sum().sum()
                    self.operations_applied += 1
                    
                except Exception as e:
                    self.logger.warning(f"Operation '{operation}' failed: {e}")
                    self._add_warning(result, f"Operation '{operation}' skipped due to error: {str(e)}")
                    self.rows_failed += 1
            
            if not windowed_results:
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "No window operations were successfully applied",
                    severity="error",
                    suggestion="Check operation names and data types"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            # Build result data
            result.data = {
                "window_size": window_size,
                "operations_applied": list(windowed_results.keys()),
                "operations_requested": operations,
                "operations_successful": self.operations_applied,
                "numeric_columns": numeric_df.columns.tolist(),
                "columns_count": len(numeric_df.columns),
                "rows_processed": len(numeric_df),
                "input_null_values": int(null_count),
                "output_null_values_from_windowing": int(total_nan_count),
                "output_shape_per_operation": [list(df.shape) for df in windowed_results.values()],
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                operations_requested=len(operations),
                operations_successful=self.operations_applied,
                nan_count=total_nan_count
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Window functions completed: {self.operations_applied}/{len(operations)} operations, "
                f"{len(numeric_df)} rows, quality score: {quality_score:.3f}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Window functions failed: {e}")
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
                suggestion="Check window_size and operation validity"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        operations_requested: int = 0,
        operations_successful: int = 0,
        nan_count: int = 0
    ) -> float:
        """Calculate quality score based on window operation success.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed
            operations_requested: Number of operations requested
            operations_successful: Number of operations that succeeded
            nan_count: NaN values in output
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from processing
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            return 1.0
        
        base_quality = rows_processed / total_rows
        
        # Penalty for failed operations
        op_penalty = 0.0
        if operations_requested > 0:
            success_rate = operations_successful / operations_requested
            if success_rate < 1.0:
                op_penalty = (1.0 - success_rate) * 0.2  # Up to 20% penalty
        
        # Minimal penalty for NaN (expected behavior)
        nan_penalty = 0.0
        if rows_processed > 0:
            nan_ratio = nan_count / (rows_processed * max(1, operations_successful))
            nan_penalty = min(0.1, nan_ratio * 0.05)
        
        quality_score = max(0.0, base_quality - op_penalty - nan_penalty)
        
        return min(1.0, quality_score)
