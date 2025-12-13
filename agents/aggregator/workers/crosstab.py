"""CrossTab Worker - Handles cross-tabulation operations.

Creates cross-tabulations for categorical data analysis with full validation,
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
VALID_AGGFUNCS = ['count', 'sum', 'mean', 'min', 'max', 'median', 'std']
DEFAULT_AGGFUNC = 'count'


class CrossTabWorker(BaseWorker):
    """Worker that creates cross-tabulations.
    
    Creates cross-tabulations for categorical data analysis including:
    - Row and column variable specification
    - Optional value aggregation
    - Advanced error handling (memory, empty results, infinity/NaN)
    - Multiple aggregation functions
    - Null value handling
    - Quality tracking
    """
    
    def __init__(self) -> None:
        """Initialize CrossTabWorker."""
        super().__init__("CrossTabWorker")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.null_values_found: int = 0
        self.advanced_errors: List[str] = []
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - rows and columns are provided and exist
        - values (if provided) exists
        - aggfunc is valid
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check rows
        rows = kwargs.get('rows')
        if not rows:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "rows parameter is required",
                severity="error",
                suggestion="Provide rows parameter (str)"
            )
        
        # Check columns
        columns = kwargs.get('columns')
        if not columns:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "columns parameter is required",
                severity="error",
                suggestion="Provide columns parameter (str)"
            )
        
        # Check columns exist
        required_cols = [rows, columns]
        values = kwargs.get('values')
        if values:
            required_cols.append(values)
        
        col_error = ValidationUtils.validate_columns_exist(
            df, required_cols, "crosstab columns"
        )
        if col_error:
            return col_error
        
        # Check aggfunc if values provided
        if values:
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
        """Create cross-tabulation.
        
        Args:
            df: DataFrame to analyze
            rows: Column for rows (str)
            columns: Column for columns (str)
            values: Column to aggregate (str, optional)
            aggfunc: Aggregation function (default: 'count')
            
        Returns:
            WorkerResult with cross-tabulation
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_crosstab(**kwargs)
            
            # Track success with error intelligence
            context = {
                "rows": str(kwargs.get('rows')),
                "columns": str(kwargs.get('columns')),
                "success": result.success,
                "quality_score": result.quality_score,
                "advanced_errors": len(self.advanced_errors),
            }
            
            if self.advanced_errors:
                context["error_types"] = list(set(self.advanced_errors))
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="CrossTabWorker",
                operation="crosstab",
                context=context
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="CrossTabWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "rows": str(kwargs.get('rows')),
                    "columns": str(kwargs.get('columns')),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed,
                    "advanced_errors": len(self.advanced_errors),
                }
            )
            raise
    
    def _run_crosstab(self, **kwargs) -> WorkerResult:
        """Perform cross-tabulation operation.
        
        Returns:
            WorkerResult with crosstab or errors
        """
        df = kwargs.get('df')
        rows = kwargs.get('rows')
        columns = kwargs.get('columns')
        values = kwargs.get('values')
        aggfunc = kwargs.get('aggfunc', DEFAULT_AGGFUNC)
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.null_values_found = 0
        self.advanced_errors = []
        
        result = self._create_result(
            task_type="crosstab",
            quality_score=1.0
        )
        
        self.logger.info(
            f"Creating crosstab: rows={rows}, columns={columns}, values={values}, aggfunc={aggfunc}"
        )
        
        try:
            # Check for null values
            crosstab_cols = [rows, columns]
            if values:
                crosstab_cols.append(values)
            
            null_count = df[crosstab_cols].isnull().sum().sum()
            self.null_values_found = null_count
            
            if null_count > 0:
                self._add_warning(
                    result,
                    f"Found {null_count} null values in crosstab columns. "
                    f"They will be excluded from the analysis."
                )
            
            # Create crosstab with error handling
            try:
                if values:
                    # Validate that values column is numeric if provided
                    if aggfunc in ['sum', 'mean', 'min', 'max', 'median', 'std']:
                        numeric_check = ValidationUtils.validate_numeric_columns(df, [values])
                        if numeric_check:
                            self._add_warning(
                                result,
                                f"Column '{values}' is not numeric. Attempting {aggfunc} anyway."
                            )
                    
                    ct = pd.crosstab(
                        df[rows],
                        df[columns],
                        values=df[values],
                        aggfunc=aggfunc
                    )
                else:
                    ct = pd.crosstab(
                        df[rows],
                        df[columns]
                    )
            except ValueError as ve:
                self.logger.error(f"Crosstab value error: {ve}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    f"Crosstab failed: {str(ve)}",
                    severity="error",
                    suggestion="Check that values column matches aggfunc"
                )
                self.advanced_errors.append("crosstab_value_error")
                result.success = False
                result.quality_score = 0
                return result
            except MemoryError:
                self.logger.error("Memory error during crosstab")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "Insufficient memory for crosstab (too many unique combinations)",
                    severity="critical",
                    suggestion="Reduce data size or filter categories"
                )
                self.advanced_errors.append("memory_error")
                result.success = False
                result.quality_score = 0
                return result
            except Exception as ct_error:
                self.logger.error(f"Unexpected crosstab error: {ct_error}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    str(ct_error),
                    severity="critical"
                )
                self.advanced_errors.append(type(ct_error).__name__.lower())
                result.success = False
                result.quality_score = 0
                return result
            
            # Handle single row/column result (becomes Series)
            try:
                if isinstance(ct, pd.Series):
                    ct = ct.to_frame()
                    self.advanced_errors.append("series_conversion")
                
                ct = ct.reset_index()
            except Exception as e:
                self.logger.warning(f"Error converting crosstab: {e}")
                self.advanced_errors.append("conversion_error")
            
            # Check if empty
            if ct.empty:
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "Crosstab resulted in empty DataFrame",
                    severity="error",
                    suggestion="Check that data exists for row-column combinations"
                )
                self.advanced_errors.append("empty_result")
                result.success = False
                result.quality_score = 0
                return result
            
            # Check for infinity/NaN in numeric columns
            numeric_cols = ct.select_dtypes(include=[np.number]).columns
            inf_count = np.isinf(ct[numeric_cols]).sum().sum() if len(numeric_cols) > 0 else 0
            nan_count = ct[numeric_cols].isna().sum().sum() if len(numeric_cols) > 0 else 0
            
            if inf_count > 0:
                self._add_warning(result, f"Crosstab contains {inf_count} infinity values")
                self.advanced_errors.append("infinity_in_result")
            
            if nan_count > 0:
                self._add_warning(result, f"Crosstab contains {nan_count} NaN values")
                self.advanced_errors.append("nan_in_result")
            
            # Build result data
            result.data = {
                "crosstab_data": ct.to_dict(orient='records'),
                "shape": list(ct.shape),
                "rows": ct.shape[0],
                "columns": ct.shape[1],
                "row_field": rows,
                "column_field": columns,
                "values_field": values if values else None,
                "aggregation_function": aggfunc if values else "count",
                "null_values_found": null_count,
                "advanced_errors_encountered": len(self.advanced_errors),
                "advanced_error_types": list(set(self.advanced_errors)) if self.advanced_errors else [],
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                null_values_found=null_count,
                advanced_errors=len(self.advanced_errors)
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Crosstab created: {ct.shape[0]} rows x {ct.shape[1]} columns, "
                f"quality score: {quality_score:.3f}"
            )
            
            return result
        
        except MemoryError:
            self.logger.error("Memory error during crosstab operation")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                "Insufficient memory",
                severity="critical"
            )
            self.advanced_errors.append("memory_error")
            result.success = False
            result.quality_score = 0
            return result
        
        except Exception as e:
            self.logger.error(f"Crosstab creation failed: {e}")
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
                suggestion="Check column names and data types"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        null_values_found: int = 0,
        advanced_errors: int = 0
    ) -> float:
        """Calculate quality score based on data quality.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed
            null_values_found: Number of null values found
            advanced_errors: Count of advanced error types
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            base_quality = 1.0
        else:
            base_quality = rows_processed / total_rows
        
        # Penalty for nulls (minimal since they're excluded)
        null_penalty = min(0.05, null_values_found * 0.001)
        
        # Penalty for advanced errors
        error_penalty = min(0.2, advanced_errors * 0.05)
        
        quality_score = max(0.0, base_quality - null_penalty - error_penalty)
        
        return min(1.0, quality_score)
