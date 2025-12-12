"""Statistics Worker - Handles summary statistics calculations.

Computes comprehensive statistics grouped by categories.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class StatisticsWorker(BaseWorker):
    """Worker that computes summary statistics."""
    
    def __init__(self):
        super().__init__("StatisticsWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Compute summary statistics.
        
        Args:
            df: DataFrame to analyze
            group_column: Column to group by
            
        Returns:
            WorkerResult with summary statistics
        """
        try:
            result = self._run_statistics(**kwargs)
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="StatisticsWorker",
                operation="summary_statistics",
                context={"group_column": kwargs.get('group_column')}
            )
            
            return result
            
        except Exception as e:
            # Track error
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="StatisticsWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"group_column": kwargs.get('group_column')}
            )
            raise
    
    def _run_statistics(self, **kwargs) -> WorkerResult:
        """Perform summary statistics computation."""
        df = kwargs.get('df')
        group_column = kwargs.get('group_column')
        
        result = self._create_result(
            task_type="summary_statistics",
            quality_score=1.0
        )
        
        if df is None or df.empty:
            self._add_error(
                result,
                ErrorType.MISSING_DATA,
                "No data provided or data is empty",
                severity="error",
                suggestion="Ensure DataFrame is not None or empty"
            )
            result.success = False
            result.quality_score = 0
            return result
        
        try:
            self.logger.info(f"Computing summary statistics grouped by '{group_column}'")
            
            if not group_column:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "group_column is required",
                    severity="error",
                    suggestion="Provide group_column parameter"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            if group_column not in df.columns:
                self._add_error(
                    result,
                    ErrorType.VALUE_ERROR,
                    f"Column '{group_column}' not found",
                    severity="error",
                    suggestion=f"Available columns: {df.columns.tolist()}"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                self._add_warning(
                    result,
                    "No numeric columns found for statistics"
                )
                result.data = {
                    "numeric_columns": [],
                    "statistics": {},
                    "groups": 0,
                }
                result.quality_score = 0.5
                return result
            
            # FIX #1: Check for null values in numeric columns
            null_count = 0
            for col in numeric_cols:
                null_count += df[col].isnull().sum()
            
            if null_count > 0:
                self._add_warning(
                    result,
                    f"Found {null_count} null values in numeric columns. They will be ignored in calculations."
                )
                result.quality_score = 0.8  # Reduce quality score for imperfect data
            
            # Reject if too many nulls (>50%)
            null_percentage = (null_count / (len(df) * len(numeric_cols)) * 100) if (len(df) * len(numeric_cols)) > 0 else 0
            
            if null_percentage > 50:
                self._add_error(
                    result,
                    ErrorType.VALIDATION_ERROR,
                    f"Data too dirty: {null_percentage:.1f}% nulls",
                    severity="error",
                    suggestion="Provide cleaner data with <50% nulls"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            grouped = df.groupby(group_column)
            stats = {}
            
            for group_name, group_df in grouped:
                group_stats = {}
                for col in numeric_cols:
                    try:
                        col_data = group_df[col].dropna()
                        if len(col_data) > 0:
                            group_stats[col] = {
                                "count": int(col_data.count()),
                                "mean": float(col_data.mean()),
                                "median": float(col_data.median()),
                                "std": float(col_data.std()),
                                "min": float(col_data.min()),
                                "max": float(col_data.max()),
                                "q25": float(col_data.quantile(0.25)),
                                "q75": float(col_data.quantile(0.75)),
                            }
                    except Exception as e:
                        self.logger.warning(f"Error computing stats for {col} in {group_name}: {e}")
                        self._add_warning(
                            result,
                            f"Could not compute stats for column '{col}' in group '{group_name}'"
                        )
                
                if group_stats:
                    stats[str(group_name)] = group_stats
            
            result.data = {
                "statistics": stats,
                "groups": len(stats),
                "group_column": group_column,
                "numeric_columns": numeric_cols,
                "numeric_columns_count": len(numeric_cols),
            }
            
            self.logger.info(f"Computed statistics for {len(stats)} groups")
            return result
        
        except Exception as e:
            self.logger.error(f"Summary statistics failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                suggestion="Check group column and numeric data types"
            )
            result.success = False
            result.quality_score = 0
            return result
