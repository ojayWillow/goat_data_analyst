"""LagLeadFunction - Lag and lead operations for time series."""

import pandas as pd
import numpy as np
from typing import List, Optional

from agents.aggregator.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class LagLeadFunction(BaseWorker):
    """Worker that calculates lag and lead functions on time series data."""
    
    def __init__(self):
        """Initialize LagLeadFunction."""
        super().__init__("LagLeadFunction")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(
        self,
        df: pd.DataFrame = None,
        lag_periods: int = 1,
        lead_periods: int = 0,
        columns: Optional[List[str]] = None,
        **kwargs
    ) -> WorkerResult:
        """Calculate lag and lead functions.
        
        Args:
            df: DataFrame to process
            lag_periods: Number of periods to lag
            lead_periods: Number of periods to lead
            columns: Columns to apply lag/lead
            
        Returns:
            WorkerResult with lag/lead results
        """
        try:
            result = self._calculate_lag_lead(df, lag_periods, lead_periods, columns, **kwargs)
            
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="LagLeadFunction",
                error_type="SUCCESS",
                error_message="Lag/Lead calculated successfully",
                context={"operation": "lag_lead_functions"}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="LagLeadFunction",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "operation": "lag_lead_functions",
                    "lag_periods": lag_periods,
                    "lead_periods": lead_periods,
                }
            )
            raise
    
    def _calculate_lag_lead(self, df, lag_periods, lead_periods, columns, **kwargs) -> WorkerResult:
        """Calculate lag and lead functions."""
        result = self._create_result(task_type="lag_lead_functions")
        
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
            
            if lag_periods < 0:
                self._add_error(result, ErrorType.VALIDATION_ERROR, "lag_periods must be >= 0")
                result.success = False
                return result
            
            if lead_periods < 0:
                self._add_error(result, ErrorType.VALIDATION_ERROR, "lead_periods must be >= 0")
                result.success = False
                return result
            
            if columns is not None:
                numeric_df = numeric_df[[col for col in columns if col in numeric_df.columns]]
            
            lag_results = {}
            lead_results = {}
            
            if lag_periods > 0:
                lag_results = numeric_df.shift(lag_periods)
            
            if lead_periods > 0:
                lead_results = numeric_df.shift(-lead_periods)
            
            result.data = {
                "lag_periods": lag_periods,
                "lead_periods": lead_periods,
                "columns_processed": numeric_df.columns.tolist(),
                "rows_processed": len(numeric_df),
                "lag_nan_rows": int(lag_results.isna().any(axis=1).sum()) if lag_periods > 0 else 0,
                "lead_nan_rows": int(lead_results.isna().any(axis=1).sum()) if lead_periods > 0 else 0,
                "total_null_values": int(lag_results.isna().sum().sum() + lead_results.isna().sum().sum())
            }
            
            logger.info(f"Lag/Lead functions: lag={lag_periods}, lead={lead_periods}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Lag/Lead functions failed: {e}")
            result.success = False
            return result
