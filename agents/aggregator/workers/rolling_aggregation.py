"""RollingAggregation - Multi-column rolling aggregations."""

import pandas as pd
import numpy as np
from typing import List, Optional

from agents.aggregator.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class RollingAggregation(BaseWorker):
    """Worker that performs rolling aggregations on multiple columns."""
    
    def __init__(self):
        """Initialize RollingAggregation."""
        super().__init__("RollingAggregation")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(
        self,
        df: pd.DataFrame = None,
        window_size: int = 5,
        columns: Optional[List[str]] = None,
        agg_dict: Optional[dict] = None,
        **kwargs
    ) -> WorkerResult:
        """Perform rolling aggregations on specified columns.
        
        Args:
            df: DataFrame to process
            window_size: Size of rolling window
            columns: Columns to aggregate
            agg_dict: Dict mapping columns to operations
            
        Returns:
            WorkerResult with aggregation results
        """
        try:
            result = self._run_rolling_agg(df, window_size, columns, agg_dict, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="RollingAggregation",
                operation="rolling_aggregation",
                context={"window_size": window_size}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="RollingAggregation",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"window_size": window_size}
            )
            raise
    
    def _run_rolling_agg(self, df, window_size, columns, agg_dict, **kwargs) -> WorkerResult:
        """Perform rolling aggregation."""
        result = self._create_result(task_type="rolling_aggregation")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(result, ErrorType.LOAD_ERROR, "No numeric columns found")
                result.success = False
                return result
            
            if window_size < 1:
                self._add_error(result, ErrorType.VALIDATION_ERROR, "window_size must be >= 1")
                result.success = False
                return result
            
            if agg_dict is None:
                agg_dict = {col: ['mean', 'sum'] for col in numeric_df.columns}
            
            if columns is not None:
                agg_dict = {k: v for k, v in agg_dict.items() if k in columns}
            
            rolling_obj = numeric_df.rolling(window=window_size)
            agg_results = rolling_obj.agg(agg_dict)
            
            result.data = {
                "window_size": window_size,
                "columns_aggregated": list(agg_dict.keys()),
                "operations_per_column": agg_dict,
                "rows_processed": len(numeric_df),
                "output_shape": str(agg_results.shape),
                "null_values_in_output": int(agg_results.isna().sum().sum())
            }
            
            logger.info(f"Rolling aggregation: window={window_size}, cols={len(agg_dict)}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Rolling aggregation failed: {e}")
            result.success = False
            return result
