"""Rolling Worker - Handles rolling aggregations for time series.

Performs rolling window calculations on numeric columns.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class RollingWorker(BaseWorker):
    """Worker that performs rolling aggregations."""
    
    def __init__(self):
        super().__init__("RollingWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Perform rolling aggregation.
        
        Args:
            df: DataFrame to analyze
            column: Column to aggregate
            window: Rolling window size
            aggfunc: Aggregation function
            
        Returns:
            WorkerResult with rolling aggregation
        """
        try:
            result = self._run_rolling(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="RollingWorker",
                operation="rolling_aggregation",
                context={"column": kwargs.get('column'), "window": kwargs.get('window')}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="RollingWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"column": kwargs.get('column'), "window": kwargs.get('window')}
            )
            raise
    
    def _run_rolling(self, **kwargs) -> WorkerResult:
        """Perform rolling window operation."""
        df = kwargs.get('df')
        column = kwargs.get('column')
        window = kwargs.get('window')
        aggfunc = kwargs.get('aggfunc', 'mean')
        
        result = self._create_result(
            task_type="rolling_aggregation",
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
            self.logger.info(f"Rolling {aggfunc} on '{column}' with window={window}")
            
            if not column or not window:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "column and window are required",
                    severity="error",
                    suggestion="Provide both column and window size"
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
            
            if not isinstance(window, int) or window < 1:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "window must be positive integer",
                    severity="error",
                    suggestion="Use window >= 1"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            if not pd.api.types.is_numeric_dtype(df[column]):
                self._add_warning(
                    result,
                    f"Column '{column}' is not numeric, conversion may occur"
                )
            
            rolling_result = df[column].rolling(window=window).agg(aggfunc)
            
            result_df = pd.DataFrame({
                column: df[column],
                f"{column}_rolling_{aggfunc}": rolling_result
            })
            
            result.data = {
                "rolling_data": result_df.to_dict(orient='records'),
                "column": column,
                "window": window,
                "function": aggfunc,
                "non_null_values": int(rolling_result.notna().sum()),
                "null_values": int(rolling_result.isna().sum()),
                "total_rows": len(result_df),
            }
            
            self.logger.info(f"Rolling aggregation completed: {result.data['non_null_values']} non-null values")
            return result
        
        except Exception as e:
            self.logger.error(f"Rolling aggregation failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                suggestion="Check column type and window parameters"
            )
            result.success = False
            result.quality_score = 0
            return result
