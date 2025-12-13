"""ValueCount Worker - Handles value counting operations.

Counts occurrences of unique values in columns.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class ValueCountWorker(BaseWorker):
    """Worker that counts unique values."""
    
    def __init__(self):
        super().__init__("ValueCountWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Count values in a column.
        
        Args:
            df: DataFrame to analyze
            column: Column to count values
            top_n: Number of top values to return
            
        Returns:
            WorkerResult with value counts
        """
        try:
            result = self._run_count_values(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="ValueCountWorker",
                operation="value_count",
                context={"column": kwargs.get('column')}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="ValueCountWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"column": kwargs.get('column')}
            )
            raise
    
    def _run_count_values(self, **kwargs) -> WorkerResult:
        """Perform value counting operation."""
        df = kwargs.get('df')
        column = kwargs.get('column')
        top_n = kwargs.get('top_n', 10)
        
        result = self._create_result(
            task_type="value_count",
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
            self.logger.info(f"Computing value counts for '{column}'")
            
            if not column:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "column is required",
                    severity="error",
                    suggestion="Provide column parameter"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            if column not in df.columns:
                self._add_error(
                    result,
                    ErrorType.VALUE_ERROR,
                    f"Column '{column}' not found",
                    severity="error",
                    suggestion=f"Available columns: {df.columns.tolist()}"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            if not isinstance(top_n, int) or top_n < 1:
                self._add_warning(
                    result,
                    f"top_n must be positive integer, using default 10"
                )
                top_n = 10
            
            vc = df[column].value_counts().head(top_n)
            
            result_list: List[Dict[str, Any]] = []
            for value, count in vc.items():
                pct = (count / len(df)) * 100
                result_list.append({
                    "value": value,
                    "count": int(count),
                    "percentage": round(pct, 2),
                })
            
            if result_list:
                result.data = {
                    "value_counts": result_list,
                    "column": column,
                    "total_unique": df[column].nunique(),
                    "top_n": top_n,
                    "results_returned": len(result_list),
                    "total_rows": len(df),
                    "null_count": int(df[column].isna().sum()),
                    "null_percentage": round((df[column].isna().sum() / len(df)) * 100, 2),
                }
            else:
                self._add_error(
                    result,
                    ErrorType.MISSING_DATA,
                    "No results available after processing",
                    severity="error",
                    suggestion="Ensure column contains valid values"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            self.logger.info(f"Value counts completed: {len(result_list)} values shown")
            return result
        
        except Exception as e:
            self.logger.error(f"Value count failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                suggestion="Check column name and data types"
            )
            result.success = False
            result.quality_score = 0
            return result
