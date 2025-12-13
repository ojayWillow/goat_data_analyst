"""Pivot Worker - Handles pivot table creation.

Reshapes data into pivot tables for cross-tabular analysis with full validation,
error intelligence, and advanced error handling per A+ guidance.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union

from .base_worker import BaseWorker, WorkerResult, ErrorType, WorkerError
from .validation_utils import ValidationUtils
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
VALID_AGGFUNCS = ['sum', 'mean', 'count', 'min', 'max', 'median', 'std']
DEFAULT_AGGFUNC = 'sum'
MAX_PIVOT_SIZE = 10000000  # ~10M cells
QUALITY_SCORE_DUPLICATES = 0.7  # Reduced if duplicates found and handled


class PivotWorker(BaseWorker):
    """Worker that creates pivot tables.
    
    Creates pivot tables for cross-tabular analysis with:
    - Flexible index/column/value specifications
    - Multiple aggregation functions
    - Advanced error handling (memory, overflow, empty results)
    - Duplicate detection and handling
    - Null value awareness
    - Quality scoring
    """
    
    def __init__(self) -> None:
        """Initialize PivotWorker."""
        super().__init__("PivotWorker")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.duplicates_found: int = 0
        self.advanced_errors: List[str] = []
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - index, columns, values are provided
        - All required columns exist
        - aggfunc is valid
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check required parameters
        index = kwargs.get('index')
        columns = kwargs.get('columns')
        values = kwargs.get('values')
        
        if not index:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "index parameter is required",
                severity="error",
                suggestion="Provide index parameter (str)"
            )
        
        if not columns:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "columns parameter is required",
                severity="error",
                suggestion="Provide columns parameter (str)"
            )
        
        if not values:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "values parameter is required",
                severity="error",
                suggestion="Provide values parameter (str)"
            )
        
        # Check columns exist
        required_cols = []
        for param in [index, columns, values]:
            if isinstance(param, str):
                required_cols.append(param)
            elif isinstance(param, list):
                required_cols.extend(param)
            else:
                return WorkerError(
                    ErrorType.TYPE_ERROR,
                    f"Parameters must be str or list[str], got {type(param).__name__}",
                    severity="error",
                    suggestion="Use string or list of strings for index, columns, values"
                )
        
        col_error = ValidationUtils.validate_columns_exist(
            df, required_cols, "pivot columns"
        )
        if col_error:
            return col_error
        
        # Check aggfunc is valid
        aggfunc = kwargs.get('aggfunc', DEFAULT_AGGFUNC)
        if aggfunc not in VALID_AGGFUNCS:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                f"Invalid aggfunc: {aggfunc}",
                severity="error",
                details={"valid_aggfuncs": VALID_AGGFUNCS},
                suggestion=f"Use one of: {', '.join(VALID_AGGFUNCS)}"
            )
        
        return None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Create pivot table.
        
        Args:
            df: DataFrame to pivot
            index: Column(s) for rows (str or list[str])
            columns: Column(s) for columns (str or list[str])
            values: Column to aggregate (str)
            aggfunc: Aggregation function (default: 'sum')
            
        Returns:
            WorkerResult with pivot table
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_pivot(**kwargs)
            
            # Track success with error intelligence
            context = {
                "index": str(kwargs.get('index')),
                "columns": str(kwargs.get('columns')),
                "success": result.success,
                "quality_score": result.quality_score,
                "advanced_errors": len(self.advanced_errors),
            }
            
            if self.advanced_errors:
                context["error_types"] = list(set(self.advanced_errors))
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="PivotWorker",
                operation="pivot_table",
                context=context
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="PivotWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "index": str(kwargs.get('index')),
                    "columns": str(kwargs.get('columns')),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed,
                    "advanced_errors": len(self.advanced_errors),
                }
            )
            raise
    
    def _run_pivot(self, **kwargs) -> WorkerResult:
        """Perform pivot table operation.
        
        Returns:
            WorkerResult with pivot table or errors
        """
        df = kwargs.get('df')
        index = kwargs.get('index')
        columns = kwargs.get('columns')
        values = kwargs.get('values')
        aggfunc = kwargs.get('aggfunc', DEFAULT_AGGFUNC)
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.duplicates_found = 0
        self.advanced_errors = []
        
        result = self._create_result(
            task_type="pivot_table",
            quality_score=1.0
        )
        
        self.logger.info(
            f"Creating pivot table: index={index}, columns={columns}, values={values}, aggfunc={aggfunc}"
        )
        
        try:
            # Check for null values in pivot columns
            pivot_cols = []
            for param in [index, columns, values]:
                if isinstance(param, str):
                    pivot_cols.append(param)
                elif isinstance(param, list):
                    pivot_cols.extend(param)
            
            null_count = df[pivot_cols].isnull().sum().sum()
            if null_count > 0:
                self._add_warning(
                    result,
                    f"Found {null_count} null values in pivot columns. "
                    f"They will be excluded from the pivot operation."
                )
            
            # Check for duplicate key combinations
            key_cols = []
            if isinstance(index, str):
                key_cols.append(index)
            elif isinstance(index, list):
                key_cols.extend(index)
            
            if isinstance(columns, str):
                key_cols.append(columns)
            elif isinstance(columns, list):
                key_cols.extend(columns)
            
            key_combination = df[key_cols].dropna()
            duplicates = key_combination.duplicated().sum()
            self.duplicates_found = duplicates
            
            if duplicates > 0:
                self._add_warning(
                    result,
                    f"Found {duplicates} duplicate (index, column) key combinations. "
                    f"Using aggfunc='{aggfunc}' to combine duplicate values."
                )
                if aggfunc == 'sum':
                    quality_reduction = min(0.15, duplicates * 0.01)
                else:
                    quality_reduction = min(0.1, duplicates * 0.005)
            else:
                quality_reduction = 0
            
            # Create pivot table with error handling
            try:
                pivot = pd.pivot_table(
                    df,
                    index=index,
                    columns=columns,
                    values=values,
                    aggfunc=aggfunc
                )
            except ValueError as ve:
                self.logger.error(f"Value error during pivot: {ve}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    f"Pivot computation failed: {str(ve)}",
                    severity="error",
                    suggestion="Check that values column is numeric for numeric aggfuncs"
                )
                self.advanced_errors.append("pivot_value_error")
                result.success = False
                result.quality_score = 0
                return result
            except MemoryError:
                self.logger.error("Memory error during pivot table creation")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "Insufficient memory for pivot table (result too large)",
                    severity="critical",
                    details={"max_size": MAX_PIVOT_SIZE},
                    suggestion="Reduce data size or filter columns/rows"
                )
                self.advanced_errors.append("memory_error")
                result.success = False
                result.quality_score = 0
                return result
            except Exception as piv_error:
                self.logger.error(f"Unexpected error during pivot: {piv_error}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    str(piv_error),
                    severity="critical",
                    suggestion="Check data types and pivot parameters"
                )
                self.advanced_errors.append(type(piv_error).__name__.lower())
                result.success = False
                result.quality_score = 0
                return result
            
            # Handle case where pivot returns Series instead of DataFrame
            if isinstance(pivot, pd.Series):
                try:
                    pivot = pivot.to_frame().reset_index()
                except Exception as e:
                    self.logger.warning(f"Error converting Series to DataFrame: {e}")
                    self.advanced_errors.append("series_conversion_error")
                    pivot = pivot.reset_index()
            else:
                try:
                    pivot = pivot.reset_index()
                except Exception as e:
                    self.logger.warning(f"Error resetting pivot index: {e}")
                    self.advanced_errors.append("reset_index_error")
            
            # Check if pivot is empty
            if pivot.empty:
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "Pivot table resulted in empty DataFrame",
                    severity="error",
                    suggestion="Check that values exist in all index-column combinations"
                )
                self.advanced_errors.append("empty_pivot")
                result.success = False
                result.quality_score = 0
                return result
            
            # Check for infinity/NaN in pivot result
            inf_count = np.isinf(pivot.select_dtypes(include=[np.number])).sum().sum()
            nan_count_pivot = pivot.select_dtypes(include=[np.number]).isna().sum().sum()
            
            if inf_count > 0:
                self._add_warning(
                    result,
                    f"Pivot result contains {inf_count} infinity values (from division by zero?)"
                )
                self.advanced_errors.append("infinity_in_result")
            
            if nan_count_pivot > 0:
                self._add_warning(
                    result,
                    f"Pivot result contains {nan_count_pivot} NaN values (missing combinations?)"
                )
                self.advanced_errors.append("nan_in_result")
            
            # Build result data
            result.data = {
                "pivot_data": pivot.to_dict(orient='records'),
                "shape": list(pivot.shape),
                "rows": pivot.shape[0],
                "columns": pivot.shape[1],
                "index_column": str(index),
                "column_field": str(columns),
                "values_column": values,
                "aggregation_function": aggfunc,
                "null_values_found": int(null_count),
                "duplicate_combinations": duplicates,
                "infinity_values_in_result": int(inf_count),
                "nan_values_in_result": int(nan_count_pivot),
                "advanced_errors_encountered": len(self.advanced_errors),
                "advanced_error_types": list(set(self.advanced_errors)) if self.advanced_errors else [],
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                duplicates_found=duplicates,
                quality_reduction=quality_reduction,
                advanced_errors=len(self.advanced_errors)
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Pivot table created: {pivot.shape[0]} rows x {pivot.shape[1]} columns, "
                f"quality score: {quality_score:.3f}"
            )
            
            return result
        
        except MemoryError:
            self.logger.error("Memory error during pivot operation")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                "Insufficient memory for pivot operation",
                severity="critical",
                suggestion="Reduce data size or number of unique combinations"
            )
            self.advanced_errors.append("memory_error")
            result.success = False
            result.quality_score = 0
            return result
        
        except Exception as e:
            self.logger.error(f"Pivot table creation failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                details={
                    "exception_type": type(e).__name__,
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed,
                    "duplicates_found": self.duplicates_found
                },
                suggestion="Check column names and aggregation function validity"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        duplicates_found: int = 0,
        quality_reduction: float = 0.0,
        advanced_errors: int = 0
    ) -> float:
        """Calculate quality score based on data quality metrics.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed processing
            duplicates_found: Number of duplicate key combinations
            quality_reduction: Penalty for duplicates
            advanced_errors: Count of advanced error types
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from successful processing
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            base_quality = 1.0
        else:
            base_quality = rows_processed / total_rows
        
        # Apply reduction for duplicates
        dup_penalty = quality_reduction
        
        # Apply penalty for advanced errors
        error_penalty = 0.0
        if advanced_errors > 0:
            error_penalty = min(0.2, advanced_errors * 0.05)
        
        quality_score = max(0.0, base_quality - dup_penalty - error_penalty)
        
        return min(1.0, quality_score)
