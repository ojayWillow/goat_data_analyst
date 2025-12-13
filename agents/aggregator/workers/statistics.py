"""Statistics Worker - Handles summary statistics calculations.

Computes comprehensive statistics grouped by categories with full validation
and quality scoring per A+ worker guidance.
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
MIN_GROUPS = 1
MIN_NUMERIC_COLS = 1
MAX_NULL_PERCENTAGE = 50.0
QUALITY_SCORE_NULL_WARNING = 0.85  # Quality score if nulls present
QUALITY_SCORE_NO_NUMERIC = 0.5


class StatisticsWorker(BaseWorker):
    """Worker that computes summary statistics.
    
    Computes comprehensive statistics grouped by categories including:
    - count, mean, median, std, min, max, q25, q75
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
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
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
    
    def execute(self, **kwargs) -> WorkerResult:
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
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="StatisticsWorker",
                operation="summary_statistics",
                context={
                    "group_column": str(kwargs.get('group_column')),
                    "success": result.success,
                    "quality_score": result.quality_score
                }
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
                    "rows_failed": self.rows_failed
                }
            )
            raise
    
    def _run_statistics(self, **kwargs) -> WorkerResult:
        """Perform summary statistics computation.
        
        Returns:
            WorkerResult with computed statistics or errors
        """
        df = kwargs.get('df')
        group_column = kwargs.get('group_column')
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.null_warnings = 0
        
        result = self._create_result(
            task_type="summary_statistics",
            quality_score=1.0
        )
        
        self.logger.info(f"Computing summary statistics grouped by '{group_column}'")
        
        try:
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
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
                            group_stats[col] = {
                                "count": int(col_data.count()),
                                "mean": float(col_data.mean()),
                                "median": float(col_data.median()),
                                "std": float(col_data.std()) if col_data.std() == col_data.std() else 0.0,  # Handle NaN
                                "min": float(col_data.min()),
                                "max": float(col_data.max()),
                                "q25": float(col_data.quantile(0.25)),
                                "q75": float(col_data.quantile(0.75)),
                            }
                    except Exception as e:
                        self.logger.warning(
                            f"Error computing stats for column '{col}' in group '{group_name}': {e}"
                        )
                        self._add_warning(
                            result,
                            f"Skipped stats for column '{col}' in group '{group_name}' (error: {type(e).__name__})"
                        )
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
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                null_warnings=self.null_warnings
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Computed statistics for {len(stats)} groups, "
                f"{len(numeric_cols)} numeric columns, "
                f"quality score: {quality_score:.3f}"
            )
            
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
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        null_warnings: int = 0
    ) -> float:
        """Calculate quality score based on data quality metrics.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed processing
            null_warnings: Number of null value warnings
            
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
        penalty = 0.0
        if null_warnings > 0:
            penalty = min(0.15, null_warnings * 0.05)  # Up to 15% penalty
        
        quality_score = max(0.0, base_quality - penalty)
        
        return min(1.0, quality_score)
