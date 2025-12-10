"""Lag/Lead Function Worker - Shifts data backward and forward in time."""

import pandas as pd
import numpy as np
from typing import Optional, List

from agents.aggregator.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class LagLeadFunctionWorker(BaseWorker):
    """Worker that creates lag and lead functions (time shifts)."""
    
    def __init__(self):
        """Initialize LagLeadFunctionWorker."""
        super().__init__("LagLeadFunctionWorker")
    
    def execute(
        self,
        df: pd.DataFrame = None,
        lag_periods: Optional[List[int]] = None,
        lead_periods: Optional[List[int]] = None,
        columns: Optional[List[str]] = None,
        group_by: Optional[str] = None,
        **kwargs
    ) -> WorkerResult:
        """Create lag and lead functions.
        
        Args:
            df: DataFrame to process
            lag_periods: List of lag periods (e.g., [1, 2, 3])
            lead_periods: List of lead periods (e.g., [1, 2])
            columns: Columns to apply lags/leads (None = all numeric)
            group_by: Optional column to group by before lagging
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with lag/lead results
        """
        result = self._create_result(task_type="lag_lead_functions")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        try:
            # Select numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(result, ErrorType.LOAD_ERROR, "No numeric columns found")
                result.success = False
                return result
            
            # Default periods
            if lag_periods is None:
                lag_periods = [1]
            if lead_periods is None:
                lead_periods = []
            
            # Filter columns if specified
            if columns is not None:
                numeric_df = numeric_df[[col for col in columns if col in numeric_df.columns]]
            
            # Create lag and lead functions
            lag_lead_data = {}
            
            # Lag function
            for period in lag_periods:
                if period < 1:
                    self._add_error(result, ErrorType.VALIDATION_ERROR, "lag periods must be >= 1")
                    result.success = False
                    return result
                
                if group_by is not None and group_by in df.columns:
                    for col in numeric_df.columns:
                        lag_col = df.groupby(group_by)[col].shift(period)
                        lag_lead_data[f'{col}_lag_{period}'] = lag_col
                else:
                    for col in numeric_df.columns:
                        lag_col = numeric_df[col].shift(period)
                        lag_lead_data[f'{col}_lag_{period}'] = lag_col
            
            # Lead function
            for period in lead_periods:
                if period < 1:
                    self._add_error(result, ErrorType.VALIDATION_ERROR, "lead periods must be >= 1")
                    result.success = False
                    return result
                
                if group_by is not None and group_by in df.columns:
                    for col in numeric_df.columns:
                        lead_col = df.groupby(group_by)[col].shift(-period)
                        lag_lead_data[f'{col}_lead_{period}'] = lead_col
                else:
                    for col in numeric_df.columns:
                        lead_col = numeric_df[col].shift(-period)
                        lag_lead_data[f'{col}_lead_{period}'] = lead_col
            
            result.data = {
                "lag_periods": lag_periods,
                "lead_periods": lead_periods,
                "group_by": group_by,
                "columns_processed": numeric_df.columns.tolist(),
                "new_columns_created": len(lag_lead_data),
                "rows_processed": len(numeric_df),
                "total_null_values_created": sum(col.isna().sum() for col in lag_lead_data.values())
            }
            
            logger.info(f"Lag/Lead: lags={lag_periods}, leads={lead_periods}, group_by={group_by}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Lag/Lead functions failed: {e}")
            result.success = False
            return result
