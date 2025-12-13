"""GroupBy Worker - Handles grouping and aggregation operations.

Performs single and multiple column grouping with various aggregation functions,
with full validation, error intelligence, and advanced error handling per A+ guidance.
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
VALID_AGG_SPECS = ['sum', 'mean', 'count', 'min', 'max', 'median', 'std', 'first', 'last']
MIN_GROUPS = 1
MAX_GROUPS = 1000000


class GroupByWorker(BaseWorker):
    """Worker that performs groupby operations.
    
    Performs single and multiple column grouping with various aggregation
    functions including:
    - String or list aggregation specs
    - Dictionary-based specs for column-specific functions
    - Advanced error handling (memory, overflow, empty results)
    - Quality tracking
    - Null value handling
    """
    
    def __init__(self) -> None:
        """Initialize GroupByWorker."""
        super().__init__("GroupByWorker")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.groups_created: int = 0
        self.advanced_errors: List[str] = []
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - group_cols is provided and exists
        - agg_specs is provided and valid format
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check group_cols
        group_cols = kwargs.get('group_cols')
        if not group_cols:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "group_cols parameter is required",
                severity="error",
                suggestion="Provide group_cols parameter (str or list[str])"
            )
        
        # Normalize to list
        if isinstance(group_cols, str):
            cols_to_check = [group_cols]
        elif isinstance(group_cols, list):
            cols_to_check = group_cols
        else:
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"group_cols must be str or list[str], got {type(group_cols).__name__}",
                severity="error",
                suggestion="Provide group_cols as string or list of strings"
            )
        
        # Check columns exist
        col_error = ValidationUtils.validate_columns_exist(
            df, cols_to_check, "group_cols"
        )
        if col_error:
            return col_error
        
        # Check agg_specs
        agg_specs = kwargs.get('agg_specs')
        if not agg_specs:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "agg_specs parameter is required",
                severity="error",
                suggestion="Provide agg_specs as string or dict"
            )
        
        # Validate agg_specs format and columns
        if isinstance(agg_specs, str):
            # Verify it's a valid aggregation function
            if agg_specs not in VALID_AGG_SPECS:
                return WorkerError(
                    ErrorType.INVALID_PARAMETER,
                    f"Invalid aggregation spec: {agg_specs}",
                    severity="error",
                    details={"valid_specs": VALID_AGG_SPECS},
                    suggestion=f"Use one of: {', '.join(VALID_AGG_SPECS)}"
                )
        elif isinstance(agg_specs, dict):
            # Check that all columns in dict exist
            missing_cols = [col for col in agg_specs.keys() if col not in df.columns]
            if missing_cols:
                return WorkerError(
                    ErrorType.VALUE_ERROR,
                    f"Aggregation columns not found: {missing_cols}",
                    severity="error",
                    suggestion=f"Available columns: {list(df.columns)}"
                )
        else:
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"agg_specs must be string or dict, got {type(agg_specs).__name__}",
                severity="error",
                suggestion="Provide agg_specs as string or dict"
            )
        
        return None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Perform groupby operation.
        
        Args:
            df: DataFrame to group
            group_cols: Column(s) to group by (str or list[str])
            agg_specs: Aggregation specs (str or dict)
            
        Returns:
            WorkerResult with grouped data
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_groupby(**kwargs)
            
            # Track success with error intelligence
            context = {
                "group_cols": str(kwargs.get('group_cols')),
                "success": result.success,
                "quality_score": result.quality_score,
                "groups_created": self.groups_created,
                "advanced_errors": len(self.advanced_errors),
            }
            
            if self.advanced_errors:
                context["error_types"] = list(set(self.advanced_errors))
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="GroupByWorker",
                operation="groupby_aggregation",
                context=context
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="GroupByWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "group_cols": str(kwargs.get('group_cols')),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed,
                    "advanced_errors": len(self.advanced_errors),
                }
            )
            raise
    
    def _run_groupby(self, **kwargs) -> WorkerResult:
        """Perform groupby aggregation.
        
        Returns:
            WorkerResult with aggregated data or errors
        """
        df = kwargs.get('df')
        group_cols = kwargs.get('group_cols')
        agg_specs = kwargs.get('agg_specs')
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.groups_created = 0
        self.advanced_errors = []
        
        result = self._create_result(
            task_type="groupby_aggregation",
            quality_score=1.0
        )
        
        self.logger.info(
            f"Performing groupby operation: group_cols={group_cols}, agg_specs={agg_specs}"
        )
        
        try:
            # Normalize group_cols to list
            if isinstance(group_cols, str):
                group_cols = [group_cols]
            
            # Check for null values in group columns
            null_count = df[group_cols].isnull().sum().sum()
            if null_count > 0:
                self._add_warning(
                    result,
                    f"Found {null_count} null values in group columns. Rows with nulls will be excluded."
                )
            
            # Perform groupby with error handling
            try:
                grouped = df.groupby(group_cols)
            except Exception as gb_error:
                self.logger.error(f"Groupby operation failed: {gb_error}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    f"Groupby failed: {str(gb_error)}",
                    severity="critical",
                    suggestion="Check group column types and values"
                )
                self.advanced_errors.append(type(gb_error).__name__.lower())
                result.success = False
                result.quality_score = 0
                return result
            
            # Apply aggregation with error handling
            try:
                if isinstance(agg_specs, str):
                    aggregated = grouped.agg(agg_specs).reset_index()
                elif isinstance(agg_specs, dict):
                    aggregated = grouped.agg(agg_specs).reset_index()
                else:
                    self._add_error(
                        result,
                        ErrorType.INVALID_PARAMETER,
                        "agg_specs must be string or dict",
                        severity="error"
                    )
                    self.advanced_errors.append("invalid_agg_specs")
                    result.success = False
                    result.quality_score = 0
                    return result
            except ValueError as ve:
                self.logger.error(f"Aggregation failed: {ve}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    f"Aggregation error: {str(ve)}",
                    severity="error",
                    suggestion="Check that columns match aggregation specs"
                )
                self.advanced_errors.append("aggregation_value_error")
                result.success = False
                result.quality_score = 0
                return result
            except MemoryError:
                self.logger.error("Memory error during groupby aggregation")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "Insufficient memory for groupby aggregation",
                    severity="critical",
                    suggestion="Reduce number of groups or data size"
                )
                self.advanced_errors.append("memory_error")
                result.success = False
                result.quality_score = 0
                return result
            except Exception as agg_error:
                self.logger.error(f"Unexpected aggregation error: {agg_error}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    str(agg_error),
                    severity="critical"
                )
                self.advanced_errors.append(type(agg_error).__name__.lower())
                result.success = False
                result.quality_score = 0
                return result
            
            # Check if empty
            if aggregated.empty:
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "Groupby resulted in empty DataFrame",
                    severity="error",
                    suggestion="Check that data exists in all groups"
                )
                self.advanced_errors.append("empty_result")
                result.success = False
                result.quality_score = 0
                return result
            
            self.groups_created = len(aggregated)
            
            # Check for infinity/NaN in result
            numeric_cols = aggregated.select_dtypes(include=[np.number]).columns
            inf_count = np.isinf(aggregated[numeric_cols]).sum().sum() if len(numeric_cols) > 0 else 0
            nan_count = aggregated[numeric_cols].isna().sum().sum() if len(numeric_cols) > 0 else 0
            
            if inf_count > 0:
                self._add_warning(result, f"Result contains {inf_count} infinity values")
                self.advanced_errors.append("infinity_in_result")
            
            if nan_count > 0:
                self._add_warning(result, f"Result contains {nan_count} NaN values")
                self.advanced_errors.append("nan_in_result")
            
            # Build result data
            result.data = {
                "grouped_data": aggregated.to_dict(orient='records'),
                "groups_count": len(aggregated),
                "group_columns": group_cols,
                "aggregation_specs": str(agg_specs),
                "null_values_in_groups": int(null_count),
                "rows_in_result": len(aggregated),
                "advanced_errors_encountered": len(self.advanced_errors),
                "advanced_error_types": list(set(self.advanced_errors)) if self.advanced_errors else [],
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                groups_created=self.groups_created,
                advanced_errors=len(self.advanced_errors)
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Grouped into {len(aggregated)} groups, quality score: {quality_score:.3f}"
            )
            
            return result
        
        except MemoryError:
            self.logger.error("Memory error during groupby operation")
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
            self.logger.error(f"GroupBy failed: {e}")
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
                suggestion="Check column names and aggregation function validity"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        groups_created: int = 0,
        advanced_errors: int = 0
    ) -> float:
        """Calculate quality score based on aggregation quality.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed
            groups_created: Number of groups created
            advanced_errors: Count of advanced error types
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from processing
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            base_quality = 1.0
        else:
            base_quality = rows_processed / total_rows
        
        # Ensure minimum groups
        if groups_created < MIN_GROUPS:
            return 0.0
        
        # Apply penalty for advanced errors
        error_penalty = 0.0
        if advanced_errors > 0:
            error_penalty = min(0.2, advanced_errors * 0.05)
        
        quality_score = max(0.0, base_quality - error_penalty)
        
        return min(1.0, quality_score)
