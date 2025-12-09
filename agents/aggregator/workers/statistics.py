"""Statistics Worker - Handles summary statistics calculations.

Computes comprehensive statistics grouped by categories.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class StatisticsWorker(BaseWorker):
    """Worker that computes summary statistics."""
    
    def __init__(self):
        super().__init__("StatisticsWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Compute summary statistics.
        
        Args:
            df: DataFrame to analyze
            group_column: Column to group by
            
        Returns:
            WorkerResult with summary statistics
        """
        return self.safe_execute(**kwargs)
    
    def execute(self, **kwargs) -> WorkerResult:
        """Perform summary statistics computation."""
        df = kwargs.get('df')
        group_column = kwargs.get('group_column')
        
        result = self._create_result(
            task_type="summary_statistics",
            quality_score=1.0
        )
        
        # Validate data
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
            
            # Validate group column
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
            
            # Get numeric columns
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
            
            # Compute statistics for each group
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
