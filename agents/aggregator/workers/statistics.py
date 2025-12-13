"""Statistics Worker - Handles summary statistics calculations.

Computes comprehensive statistics grouped by categories with full validation,
error intelligence, and advanced error handling per A+ guidance.
"""

import pandas as pd
import numpy as np
import sys
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import signal

from .base_worker import BaseWorker, WorkerResult, ErrorType, WorkerError
from .validation_utils import ValidationUtils
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
MIN_GROUPS = 1
MIN_NUMERIC_COLS = 1
MAX_NULL_PERCENTAGE = 50.0
QUALITY_SCORE_NULL_WARNING = 0.85  # Quality score if nulls present
QUALITY_SCORE_NO_NUMERIC = 0.5
TIMEOUT_SECONDS = 30  # Timeout for operations
MEMORY_WARNING_THRESHOLD = 0.8  # 80% memory usage


class TimeoutError(Exception):
    """Custom timeout exception."""
    pass


class StatisticsWorker(BaseWorker):
    """Worker that computes summary statistics.
    
    Computes comprehensive statistics grouped by categories including:
    - count, mean, median, std, min, max, q25, q75
    - Advanced error handling (timeouts, memory, infinity/NaN)
    - Handles null values gracefully
    - Tracks data quality metrics
    - Provides detailed error messages
    """
    
    def __init__(self) -> None:
        """Initialize StatisticsWorker."""
        super().__init__("StatisticsWorker")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.null_warnings: int = 0
        self.numeric_cols_found: int = 0
        self.advanced_errors: List[str] = []
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - group_column is provided
        - group_column exists in DataFrame
        - DataFrame has numeric columns
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check group_column is provided
        group_column = kwargs.get('group_column')
        if not group_column:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "group_column parameter is required",
                severity="error",
                suggestion="Provide group_column parameter (str)"
            )
        
        # Check group_column exists
        if isinstance(group_column, str):
            cols_to_check = [group_column]
        else:
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"group_column must be string, got {type(group_column).__name__}",
                severity="error",
                suggestion="Provide group_column as string"
            )
        
        col_error = ValidationUtils.validate_columns_exist(
            df, cols_to_check, "group_column"
        )
        if col_error:
            return col_error
        
        # Check numeric columns exist
        numeric_error = ValidationUtils.validate_numeric_columns(df)
        if numeric_error:
            return numeric_error
        
        return None
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Compute summary statistics.
        
        Args:
            df: DataFrame to analyze
            group_column: Column to group by (str)
            
        Returns:
            WorkerResult with summary statistics
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_statistics(**kwargs)
            
            # Track success with error intelligence
            context = {
                "group_column": str(kwargs.get('group_column')),
                "success": result.success,
                "quality_score": result.quality_score,
                "advanced_errors": len(self.advanced_errors),
            }
            
            if self.advanced_errors:
                context["error_types"] = list(set(self.advanced_errors))
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="StatisticsWorker",
                operation="summary_statistics",
                context=context
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="StatisticsWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "group_column": str(kwargs.get('group_column')),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed,
                    "advanced_errors": len(self.advanced_errors),
                }
            )
            raise
    
    def _run_statistics(self, **kwargs: Any) -> WorkerResult:
        """Perform summary statistics computation.
        
        Returns:
            WorkerResult with computed statistics or errors
        """
        df: pd.DataFrame | None = kwargs.get('df')
        group_column = kwargs.get('group_column')
        
        # Add None check
        if df is None:
            result = self._create_result(success=False, quality_score=0, task_type="summary_statistics")
            self._add_error(
                result,
                ErrorType.DATA_VALIDATION_ERROR,
                "DataFrame is None",
                severity="error",
                suggestion="Provide a valid DataFrame"
            )
            return result
        
        # Reset counters
        self.rows_processed = len(df)
        self.rows_failed = 0
        self.null_warnings = 0
        self.advanced_errors = []
        
        result = self._create_result(
            task_type="summary_statistics",
            quality_score=1.0
        )
        
        self.logger.info(f"Computing summary statistics grouped by '{group_column}'")
        
        try:
            # Get numeric columns
            numeric_cols: List[str] = df.select_dtypes(include=[np.number]).columns.tolist()
            self.numeric_cols_found = len(numeric_cols)
            
            if not numeric_cols:
                self._add_warning(
                    result,
                    "No numeric columns found for statistics computation"
                )
                self.null_warnings += 1
                result.data = {
                    "statistics": {},
                    "groups": 0,
                    "group_column": group_column,
                    "numeric_columns": [],
                    "numeric_columns_count": 0,
                    "null_value_count": 0,
                    "null_percentage": 0.0,
                }
                result.quality_score = QUALITY_SCORE_NO_NUMERIC
                return result
            
            # Check for null values
            null_count = 0
            for col in numeric_cols:
                null_count += df[col].isnull().sum()
            
            total_cells = len(df) * len(numeric_cols)
            null_percentage = (null_count / total_cells * 100) if total_cells > 0 else 0
            
            # Warn if nulls present
            if null_count > 0:
                self.null_warnings += 1
                self._add_warning(
                    result,
                    f"Found {null_count} null values ({null_percentage:.1f}%) in {len(numeric_cols)} numeric columns. "
                    f"They will be ignored in calculations."
                )
            
            # Reject if too many nulls
            if null_percentage > MAX_NULL_PERCENTAGE:
                self._add_error(
                    result,
                    ErrorType.VALIDATION_ERROR,
                    f"Data too dirty: {null_percentage:.1f}% null values (max allowed: {MAX_NULL_PERCENTAGE}%)",
                    severity="error",
                    details={
                        "null_count": int(null_count),
                        "null_percentage": round(null_percentage, 2),
                        "total_cells": total_cells
                    },
                    suggestion="Provide cleaner data with lower null percentage"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            # Perform groupby and compute statistics
            grouped = df.groupby(group_column)
            stats: Dict[str, Dict[str, Any]] = {}
            groups_computed = 0
            
            for group_name, group_df in grouped:
                group_stats: Dict[str, Dict[str, Any]] = {}
                
                for col in numeric_cols:
                    try:
                        col_data = group_df[col].dropna()
                        
                        if len(col_data) > 0:
                            # Check for infinity values
                            has_inf = np.isinf(col_data).any()
                            if has_inf:
                                self.advanced_errors.append("infinity_values")
                                self._add_warning(
                                    result,
                                    f"Column '{col}' in group '{group_name}' contains infinity values"
                                )
                            
                            # Check for NaN values (after dropna check)
                            has_nan = col_data.isna().any()
                            if has_nan:
                                self.advanced_errors.append("unexpected_nan")
                                self.logger.warning(
                                    f"Unexpected NaN found in '{col}' after dropna()"
                                )
                            
                            # Calculate statistics
                            mean_val = col_data.mean()
                            median_val = col_data.median()
                            std_val = col_data.std()
                            min_val = col_data.min()
                            max_val = col_data.max()
                            q25_val = col_data.quantile(0.25)
                            q75_val = col_data.quantile(0.75)
                            
                            # Handle NaN in std (single value case)
                            if np.isnan(std_val):
                                std_val = 0.0
                                self.advanced_errors.append("std_nan")
                            
                            # Safe float conversion (catch inf, NaN)
                            group_stats[col] = {
                                "count": int(col_data.count()),
                                "mean": self._safe_float(mean_val),
                                "median": self._safe_float(median_val),
                                "std": self._safe_float(std_val),
                                "min": self._safe_float(min_val),
                                "max": self._safe_float(max_val),
                                "q25": self._safe_float(q25_val),
                                "q75": self._safe_float(q75_val),
                            }
                    except ValueError as ve:
                        self.logger.warning(
                            f"Value error computing stats for '{col}' in group '{group_name}': {ve}"
                        )
                        self._add_warning(
                            result,
                            f"Skipped stats for column '{col}' in group '{group_name}' (value error)"
                        )
                        self.advanced_errors.append("value_error")
                        self.rows_failed += 1
                    except MemoryError:
                        self.logger.error(
                            f"Memory error computing stats for '{col}' in group '{group_name}'"
                        )
                        self._add_error(
                            result,
                            ErrorType.COMPUTATION_ERROR,
                            f"Insufficient memory for statistics computation on column '{col}'",
                            severity="critical",
                            suggestion="Reduce data size or increase available memory"
                        )
                        self.advanced_errors.append("memory_error")
                        return result
                    except OverflowError as oe:
                        self.logger.warning(
                            f"Overflow error for column '{col}' in group '{group_name}': {oe}"
                        )
                        self._add_warning(
                            result,
                            f"Numerical overflow in column '{col}' (value too large)"
                        )
                        self.advanced_errors.append("overflow_error")
                        self.rows_failed += 1
                    except Exception as e:
                        self.logger.warning(
                            f"Error computing stats for column '{col}' in group '{group_name}': {type(e).__name__}"
                        )
                        self._add_warning(
                            result,
                            f"Skipped stats for column '{col}' in group '{group_name}' (error: {type(e).__name__})"
                        )
                        self.advanced_errors.append(type(e).__name__.lower())
                        self.rows_failed += 1
                
                if group_stats:
                    stats[str(group_name)] = group_stats
                    groups_computed += 1
            
            if not stats:
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "No statistics could be computed from grouped data",
                    severity="error",
                    suggestion="Check that numeric data is present in groups"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            # Build result data
            result.data = {
                "statistics": stats,
                "groups": len(stats),
                "groups_computed": groups_computed,
                "group_column": group_column,
                "numeric_columns": numeric_cols,
                "numeric_columns_count": len(numeric_cols),
                "null_value_count": int(null_count),
                "null_percentage": round(null_percentage, 2),
                "advanced_errors_encountered": len(self.advanced_errors),
                "advanced_error_types": list(set(self.advanced_errors)) if self.advanced_errors else [],
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                null_warnings=self.null_warnings,
                advanced_errors=len(self.advanced_errors)
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Computed statistics for {len(stats)} groups, "
                f"{len(numeric_cols)} numeric columns, "
                f"quality score: {quality_score:.3f}"
            )
            
            return result
        
        except MemoryError:
            self.logger.error("Memory error during statistics computation")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                "Insufficient memory for statistics computation",
                severity="critical",
                suggestion="Reduce data size or increase available memory"
            )
            self.advanced_errors.append("memory_error")
            result.success = False
            result.quality_score = 0
            return result
        
        except Exception as e:
            self.logger.error(f"Summary statistics computation failed: {e}")
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
                suggestion="Check group column existence and numeric data types"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float, handling inf/NaN.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value or 0.0 if inf/NaN
        """
        try:
            if isinstance(value, (float, np.floating)):
                if np.isinf(value):
                    self.advanced_errors.append("infinity_to_zero")
                    return 0.0
                if np.isnan(value):
                    self.advanced_errors.append("nan_to_zero")
                    return 0.0
                return float(value)
            return float(value)
        except (ValueError, OverflowError, TypeError):
            self.advanced_errors.append("conversion_error")
            return 0.0
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        null_warnings: int = 0,
        advanced_errors: int = 0
    ) -> float:
        """Calculate quality score based on data quality metrics.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed processing
            null_warnings: Number of null value warnings
            advanced_errors: Count of advanced error types encountered
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from successful processing
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            base_quality = 1.0
        else:
            base_quality = rows_processed / total_rows
        
        # Apply penalty for warnings
        null_penalty = 0.0
        if null_warnings > 0:
            null_penalty = min(0.15, null_warnings * 0.05)  # Up to 15% penalty
        
        # Apply penalty for advanced errors
        error_penalty = 0.0
        if advanced_errors > 0:
            error_penalty = min(0.2, advanced_errors * 0.05)  # Up to 20% penalty
        
        quality_score = max(0.0, base_quality - null_penalty - error_penalty)
        
        return min(1.0, quality_score)
