"""ExponentialWeighted - Exponential weighted moving average.

Exponential weighted moving average calculations with full validation
and quality scoring per A+ worker guidance.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

from .base_worker import BaseWorker, WorkerResult, ErrorType, WorkerError
from .validation_utils import ValidationUtils
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
MIN_SPAN = 1
MAX_SPAN = 1000
DEFAULT_SPAN = 10


class ExponentialWeighted(BaseWorker):
    """Worker that calculates exponential weighted moving average.
    
    Calculates EWMA with:
    - Configurable span values
    - Adjustment options
    - Quality scoring
    """
    
    def __init__(self) -> None:
        """Initialize ExponentialWeighted."""
        super().__init__("ExponentialWeighted")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.columns_processed: int = 0
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - span is valid integer
        - DataFrame has numeric columns
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check span
        span = kwargs.get('span', DEFAULT_SPAN)
        if not isinstance(span, int):
            return WorkerError(
                ErrorType.TYPE_ERROR,
                f"span must be integer, got {type(span).__name__}",
                severity="error",
                suggestion="Provide span as positive integer"
            )
        
        if span < MIN_SPAN or span > MAX_SPAN:
            return WorkerError(
                ErrorType.VALUE_ERROR,
                f"span must be between {MIN_SPAN} and {MAX_SPAN}, got {span}",
                severity="error",
                suggestion=f"Use value between {MIN_SPAN} and {MAX_SPAN}"
            )
        
        # Check numeric columns
        numeric_error = ValidationUtils.validate_numeric_columns(df)
        if numeric_error:
            return numeric_error
        
        return None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Calculate exponential weighted moving average.
        
        Args:
            df: DataFrame to process
            span: Span for exponential weighting (default: 10)
            adjust: Whether to apply exponential scaling (default: True)
            
        Returns:
            WorkerResult with EWMA results
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_ewma(**kwargs)
            
            # Track success with error intelligence
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="ExponentialWeighted",
                operation="exponential_weighted",
                context={
                    "span": kwargs.get('span', DEFAULT_SPAN),
                    "success": result.success,
                    "quality_score": result.quality_score,
                    "columns_processed": self.columns_processed
                }
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="ExponentialWeighted",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "span": kwargs.get('span', DEFAULT_SPAN),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed
                }
            )
            raise
    
    def _run_ewma(self, **kwargs) -> WorkerResult:
        """Calculate exponential weighted moving average.
        
        Returns:
            WorkerResult with EWMA results or errors
        """
        df = kwargs.get('df')
        span = kwargs.get('span', DEFAULT_SPAN)
        adjust = kwargs.get('adjust', True)
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.columns_processed = 0
        
        result = self._create_result(
            task_type="exponential_weighted",
            quality_score=1.0
        )
        
        self.logger.info(
            f"Calculating EWMA: span={span}, adjust={adjust}"
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
                    suggestion="DataFrame must contain numeric columns"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            self.columns_processed = len(numeric_df.columns)
            
            # Check for null values
            null_count = numeric_df.isnull().sum().sum()
            if null_count > 0:
                self._add_warning(
                    result,
                    f"Found {null_count} null values in data. "
                    f"EWMA will propagate NaN values across series."
                )
            
            # Calculate EWMA and standard deviation
            ewma = numeric_df.ewm(span=span, adjust=adjust).mean()
            ewma_std = numeric_df.ewm(span=span, adjust=adjust).std()
            
            # Count output nulls
            output_nulls = ewma.isna().sum().sum()
            
            # Build statistics
            ewma_stats: Dict[str, float] = {}
            ewma_std_stats: Dict[str, float] = {}
            
            for col in ewma.columns:
                ewma_stats[col] = float(ewma[col].mean()) if ewma[col].notna().any() else 0.0
                ewma_std_stats[col] = float(ewma_std[col].mean()) if ewma_std[col].notna().any() else 0.0
            
            # Build result data
            result.data = {
                "method": "Exponential Weighted Moving Average",
                "span": span,
                "adjust": adjust,
                "columns_processed": numeric_df.columns.tolist(),
                "columns_count": len(numeric_df.columns),
                "rows_processed": len(numeric_df),
                "input_null_values": int(null_count),
                "output_null_values": int(output_nulls),
                "ewma_mean_per_column": ewma_stats,
                "ewma_std_per_column": ewma_std_stats,
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                input_nulls=null_count,
                output_nulls=output_nulls
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"EWMA completed: {len(numeric_df.columns)} columns, "
                f"{len(numeric_df)} rows, quality score: {quality_score:.3f}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Exponential weighted calculation failed: {e}")
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
                suggestion="Check span value and numeric data validity"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        input_nulls: int = 0,
        output_nulls: int = 0
    ) -> float:
        """Calculate quality score based on EWMA computation quality.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed
            input_nulls: Input null values
            output_nulls: Output null values
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from processing
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            return 1.0
        
        base_quality = rows_processed / total_rows
        
        # Penalty for nulls (EWMA propagates NaNs, so penalty is minimal)
        null_penalty = 0.0
        if input_nulls > 0 and rows_processed > 0:
            null_ratio = input_nulls / (rows_processed * 10)  # Rough estimate
            null_penalty = min(0.1, null_ratio * 0.05)  # Up to 10% penalty
        
        quality_score = max(0.0, base_quality - null_penalty)
        
        return min(1.0, quality_score)
