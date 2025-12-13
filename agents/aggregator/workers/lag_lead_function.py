"""LagLeadFunction - Lag and lead operations for time series.

Lag and lead operations for time series data with full validation
and quality scoring per A+ worker guidance.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Any, Dict

from .base_worker import BaseWorker, WorkerResult, ErrorType, WorkerError
from .validation_utils import ValidationUtils
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
MIN_PERIODS = 0
MAX_PERIODS = 100
DEFAULT_LAG = 1
DEFAULT_LEAD = 0


class LagLeadFunction(BaseWorker):
    """Worker that calculates lag and lead functions on time series data.
    
    Calculates lag and lead operations including:
    - Configurable lag/lead periods
    - Column selection
    - Null value tracking
    - Quality scoring
    """
    
    def __init__(self) -> None:
        """Initialize LagLeadFunction."""
        super().__init__("LagLeadFunction")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.nan_rows_created: int = 0
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - lag_periods is valid integer
        - lead_periods is valid integer
        - columns (if provided) exist and are numeric
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check lag_periods
        lag_periods = kwargs.get('lag_periods', DEFAULT_LAG)
        if not isinstance(lag_periods, int):
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"lag_periods must be integer, got {type(lag_periods).__name__}",
                severity="error",
                suggestion="Provide lag_periods as integer"
            )
        
        if lag_periods < MIN_PERIODS or lag_periods > MAX_PERIODS:
            return WorkerError(
                ErrorType.VALUE_ERROR,
                f"lag_periods must be between {MIN_PERIODS} and {MAX_PERIODS}, got {lag_periods}",
                severity="error",
                suggestion=f"Use value between {MIN_PERIODS} and {MAX_PERIODS}"
            )
        
        # Check lead_periods
        lead_periods = kwargs.get('lead_periods', DEFAULT_LEAD)
        if not isinstance(lead_periods, int):
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"lead_periods must be integer, got {type(lead_periods).__name__}",
                severity="error",
                suggestion="Provide lead_periods as integer"
            )
        
        if lead_periods < MIN_PERIODS or lead_periods > MAX_PERIODS:
            return WorkerError(
                ErrorType.VALUE_ERROR,
                f"lead_periods must be between {MIN_PERIODS} and {MAX_PERIODS}, got {lead_periods}",
                severity="error",
                suggestion=f"Use value between {MIN_PERIODS} and {MAX_PERIODS}"
            )
        
        # Check columns if provided
        columns = kwargs.get('columns')
        if columns:
            if isinstance(columns, str):
                columns = [columns]
            
            col_error = ValidationUtils.validate_columns_exist(
                df, columns, "lag/lead columns"
            )
            if col_error:
                return col_error
            
            # Check columns are numeric
            numeric_error = ValidationUtils.validate_numeric_columns(df, columns)
            if numeric_error:
                return numeric_error
        else:
            # Check that DataFrame has numeric columns
            numeric_error = ValidationUtils.validate_numeric_columns(df)
            if numeric_error:
                return numeric_error
        
        return None
    
    def execute(
        self,
        **kwargs
    ) -> WorkerResult:
        """Calculate lag and lead functions.
        
        Args:
            df: DataFrame to process
            lag_periods: Number of periods to lag (default: 1)
            lead_periods: Number of periods to lead (default: 0)
            columns: Columns to apply lag/lead (default: all numeric)
            
        Returns:
            WorkerResult with lag/lead results
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_lag_lead(**kwargs)
            
            # Track success with error intelligence
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="LagLeadFunction",
                operation="lag_lead_functions",
                context={
                    "lag_periods": kwargs.get('lag_periods', DEFAULT_LAG),
                    "lead_periods": kwargs.get('lead_periods', DEFAULT_LEAD),
                    "success": result.success,
                    "quality_score": result.quality_score
                }
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="LagLeadFunction",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "lag_periods": kwargs.get('lag_periods', DEFAULT_LAG),
                    "lead_periods": kwargs.get('lead_periods', DEFAULT_LEAD),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed
                }
            )
            raise
    
    def _run_lag_lead(self, **kwargs) -> WorkerResult:
        """Calculate lag and lead functions.
        
        Returns:
            WorkerResult with lag/lead results or errors
        """
        df = kwargs.get('df')
        lag_periods = kwargs.get('lag_periods', DEFAULT_LAG)
        lead_periods = kwargs.get('lead_periods', DEFAULT_LEAD)
        columns = kwargs.get('columns')
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.nan_rows_created = 0
        
        result = self._create_result(
            task_type="lag_lead_functions",
            quality_score=1.0
        )
        
        self.logger.info(
            f"Computing lag/lead: lag_periods={lag_periods}, lead_periods={lead_periods}"
        )
        
        try:
            # Get numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(
                    result,
                    ErrorType.MISSING_DATA,
                    "No numeric columns found in DataFrame",
                    severity="error",
                    suggestion="DataFrame must contain numeric columns for lag/lead operations"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            # Filter to specified columns if provided
            if columns:
                if isinstance(columns, str):
                    columns = [columns]
                numeric_df = numeric_df[[col for col in columns if col in numeric_df.columns]]
            
            # Calculate lag and lead
            lag_results = None
            lead_results = None
            nan_count = 0
            
            if lag_periods > 0:
                lag_results = numeric_df.shift(lag_periods)
                nan_count += lag_results.isna().sum().sum()
            
            if lead_periods > 0:
                lead_results = numeric_df.shift(-lead_periods)
                nan_count += lead_results.isna().sum().sum()
            
            # Count rows with any NaN values (created by shift)
            if lag_periods > 0:
                lag_nan_rows = int(lag_results.isna().any(axis=1).sum())
            else:
                lag_nan_rows = 0
            
            if lead_periods > 0:
                lead_nan_rows = int(lead_results.isna().any(axis=1).sum())
            else:
                lead_nan_rows = 0
            
            self.nan_rows_created = lag_nan_rows + lead_nan_rows
            
            if self.nan_rows_created > 0:
                self._add_warning(
                    result,
                    f"Lag/lead operations created {self.nan_rows_created} rows with NaN values. "
                    f"First {lag_periods} rows are NaN for lag, last {lead_periods} for lead."
                )
            
            # Build result data
            result.data = {
                "lag_periods": lag_periods,
                "lead_periods": lead_periods,
                "columns_processed": numeric_df.columns.tolist(),
                "columns_count": len(numeric_df.columns),
                "rows_processed": len(numeric_df),
                "lag_nan_rows_created": lag_nan_rows,
                "lead_nan_rows_created": lead_nan_rows,
                "total_nan_values_created": int(nan_count),
                "operation_description": f"Lag {lag_periods} periods + Lead {lead_periods} periods",
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                nan_rows_created=self.nan_rows_created
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Lag/lead completed: {len(numeric_df.columns)} columns, "
                f"{len(numeric_df)} rows, {self.nan_rows_created} NaN rows, "
                f"quality score: {quality_score:.3f}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Lag/lead functions failed: {e}")
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
                suggestion="Check DataFrame structure and numeric column existence"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        nan_rows_created: int = 0
    ) -> float:
        """Calculate quality score based on shift operations.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed
            nan_rows_created: Rows with NaN created by shift
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from processing
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            return 1.0
        
        base_quality = rows_processed / total_rows
        
        # Penalty for NaN rows (expected behavior of shift, small penalty)
        nan_penalty = min(0.15, (nan_rows_created / rows_processed) * 0.2) if rows_processed > 0 else 0
        
        quality_score = max(0.0, base_quality - nan_penalty)
        
        return min(1.0, quality_score)
