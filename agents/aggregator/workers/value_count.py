"""ValueCount Worker - Handles value counting operations.

Counts occurrences of unique values in columns with full validation,
error intelligence, and advanced error handling per A+ guidance.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType, WorkerError
from .validation_utils import ValidationUtils
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
DEFAULT_TOP_N = 10
MIN_TOP_N = 1
MAX_TOP_N = 1000


class ValueCountWorker(BaseWorker):
    """Worker that counts unique values.
    
    Counts occurrences of unique values in columns including:
    - Top N value filtering
    - Advanced error handling (empty results, type errors)
    - Percentage calculation
    - Null value tracking
    - Quality scoring
    """
    
    def __init__(self) -> None:
        """Initialize ValueCountWorker."""
        super().__init__("ValueCountWorker")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.unique_count: int = 0
        self.advanced_errors: List[str] = []
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - column is provided and exists
        - top_n is valid integer
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check column
        column = kwargs.get('column')
        if not column:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "column parameter is required",
                severity="error",
                suggestion="Provide column parameter (str)"
            )
        
        # Check column exists
        col_error = ValidationUtils.validate_columns_exist(
            df, [column], "column"
        )
        if col_error:
            return col_error
        
        # Check top_n if provided
        top_n = kwargs.get('top_n', DEFAULT_TOP_N)
        if not isinstance(top_n, int):
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"top_n must be integer, got {type(top_n).__name__}",
                severity="error",
                suggestion="Provide top_n as positive integer"
            )
        
        if top_n < MIN_TOP_N or top_n > MAX_TOP_N:
            return WorkerError(
                ErrorType.VALUE_ERROR,
                f"top_n must be between {MIN_TOP_N} and {MAX_TOP_N}, got {top_n}",
                severity="error",
                suggestion=f"Use value between {MIN_TOP_N} and {MAX_TOP_N}"
            )
        
        return None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Count values in a column.
        
        Args:
            df: DataFrame to analyze
            column: Column to count values (str)
            top_n: Number of top values to return (default: 10)
            
        Returns:
            WorkerResult with value counts
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_count_values(**kwargs)
            
            # Track success with error intelligence
            context = {
                "column": str(kwargs.get('column')),
                "success": result.success,
                "quality_score": result.quality_score,
                "unique_count": self.unique_count,
                "advanced_errors": len(self.advanced_errors),
            }
            
            if self.advanced_errors:
                context["error_types"] = list(set(self.advanced_errors))
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="ValueCountWorker",
                operation="value_count",
                context=context
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="ValueCountWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "column": str(kwargs.get('column')),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed,
                    "advanced_errors": len(self.advanced_errors),
                }
            )
            raise
    
    def _run_count_values(self, **kwargs) -> WorkerResult:
        """Perform value counting operation.
        
        Returns:
            WorkerResult with value counts or errors
        """
        df = kwargs.get('df')
        column = kwargs.get('column')
        top_n = kwargs.get('top_n', DEFAULT_TOP_N)
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.unique_count = 0
        self.advanced_errors = []
        
        result = self._create_result(
            task_type="value_count",
            quality_score=1.0
        )
        
        self.logger.info(f"Computing value counts for column '{column}', top {top_n}")
        
        try:
            # Get null count before dropping
            null_count = df[column].isna().sum()
            null_percentage = (null_count / len(df) * 100) if len(df) > 0 else 0
            
            if null_count > 0:
                self._add_warning(
                    result,
                    f"Found {null_count} null values ({null_percentage:.1f}%). "
                    f"They are excluded from value counts."
                )
            
            # Count values with error handling
            try:
                vc = df[column].value_counts().head(top_n)
            except TypeError as te:
                self.logger.error(f"Type error in value_count: {te}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    f"Cannot count values (type error): {str(te)}",
                    severity="error",
                    suggestion="Check column data types"
                )
                self.advanced_errors.append("value_count_type_error")
                result.success = False
                result.quality_score = 0
                return result
            except Exception as vc_error:
                self.logger.error(f"Value count error: {vc_error}")
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    str(vc_error),
                    severity="critical"
                )
                self.advanced_errors.append(type(vc_error).__name__.lower())
                result.success = False
                result.quality_score = 0
                return result
            
            # Check if empty
            if vc.empty:
                self._add_error(
                    result,
                    ErrorType.MISSING_DATA,
                    "No non-null values found in column",
                    severity="error",
                    suggestion="Ensure column contains non-null values"
                )
                self.advanced_errors.append("empty_result")
                result.success = False
                result.quality_score = 0
                return result
            
            # Build result list with error handling
            result_list: List[Dict[str, Any]] = []
            try:
                for value, count in vc.items():
                    try:
                        pct = (count / len(df)) * 100
                        result_list.append({
                            "value": str(value),
                            "count": int(count),
                            "percentage": round(pct, 2),
                        })
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Error processing value {value}: {e}")
                        self.advanced_errors.append("value_conversion_error")
                        self.rows_failed += 1
                        continue
            except Exception as e:
                self.logger.error(f"Error building result list: {e}")
                self.advanced_errors.append("result_building_error")
            
            # Calculate unique count
            try:
                self.unique_count = df[column].nunique()
            except Exception as e:
                self.logger.warning(f"Error computing nunique: {e}")
                self.advanced_errors.append("nunique_error")
                self.unique_count = len(result_list)
            
            # Build result data
            result.data = {
                "value_counts": result_list,
                "column": column,
                "total_unique_values": self.unique_count,
                "top_n_requested": top_n,
                "results_returned": len(result_list),
                "total_rows": len(df),
                "null_count": int(null_count),
                "null_percentage": round(null_percentage, 2),
                "coverage_percentage": round((len(df) - null_count) / len(df) * 100, 2) if len(df) > 0 else 0,
                "advanced_errors_encountered": len(self.advanced_errors),
                "advanced_error_types": list(set(self.advanced_errors)) if self.advanced_errors else [],
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                null_count=null_count,
                total_rows=len(df),
                advanced_errors=len(self.advanced_errors)
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Value counts completed: {len(result_list)} values from {self.unique_count} unique, "
                f"quality score: {quality_score:.3f}"
            )
            
            return result
        
        except MemoryError:
            self.logger.error("Memory error during value count")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                "Insufficient memory for value counting",
                severity="critical"
            )
            self.advanced_errors.append("memory_error")
            result.success = False
            result.quality_score = 0
            return result
        
        except Exception as e:
            self.logger.error(f"Value count failed: {e}")
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
                suggestion="Check column name and data types"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        null_count: int = 0,
        total_rows: int = 0,
        advanced_errors: int = 0
    ) -> float:
        """Calculate quality score based on data completeness.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed
            null_count: Number of null values in column
            total_rows: Total rows in DataFrame
            advanced_errors: Count of advanced error types
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from processing
        total = rows_processed + rows_failed
        if total == 0:
            return 1.0
        
        base_quality = rows_processed / total
        
        # Penalty for nulls
        null_penalty = 0.0
        if total_rows > 0:
            null_percentage = (null_count / total_rows) * 100
            null_penalty = min(0.2, null_percentage * 0.002)  # Up to 20% penalty
        
        # Penalty for advanced errors
        error_penalty = min(0.15, advanced_errors * 0.05)
        
        quality_score = max(0.0, base_quality - null_penalty - error_penalty)
        
        return min(1.0, quality_score)
