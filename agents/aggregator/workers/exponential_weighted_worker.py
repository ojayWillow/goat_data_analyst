"""Exponential Weighted Worker - Calculates exponential weighted moving averages."""

import pandas as pd
import numpy as np
from typing import Optional

from agents.aggregator.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class ExponentialWeightedWorker(BaseWorker):
    """Worker that calculates exponential weighted moving averages (EWMA)."""
    
    def __init__(self):
        """Initialize ExponentialWeightedWorker."""
        super().__init__("ExponentialWeightedWorker")
    
    def execute(
        self,
        df: pd.DataFrame = None,
        span: int = 20,
        alpha: Optional[float] = None,
        halflife: Optional[int] = None,
        include_std: bool = True,
        **kwargs
    ) -> WorkerResult:
        """Calculate exponential weighted moving average.
        
        Args:
            df: DataFrame to process
            span: Span parameter (default 20)
            alpha: Smoothing factor (0-1), alternative to span
            halflife: Half-life in periods, alternative to span
            include_std: Include exponential weighted std dev
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with EWMA results
        """
        result = self._create_result(task_type="exponential_weighted")
        
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
            
            # Validate parameters
            if alpha is not None:
                if alpha <= 0 or alpha >= 1:
                    self._add_error(result, ErrorType.VALIDATION_ERROR, "alpha must be between 0 and 1")
                    result.success = False
                    return result
                ewm = numeric_df.ewm(alpha=alpha)
            elif halflife is not None:
                if halflife <= 0:
                    self._add_error(result, ErrorType.VALIDATION_ERROR, "halflife must be > 0")
                    result.success = False
                    return result
                ewm = numeric_df.ewm(halflife=halflife)
            else:
                if span <= 0:
                    self._add_error(result, ErrorType.VALIDATION_ERROR, "span must be > 0")
                    result.success = False
                    return result
                ewm = numeric_df.ewm(span=span)
            
            # Calculate EWMA
            ewma_mean = ewm.mean()
            
            # Optionally calculate exponential weighted std
            ewma_data = {
                "ewma_mean": ewma_mean,
            }
            
            if include_std:
                ewma_std = ewm.std()
                ewma_data["ewma_std"] = ewma_std
            
            result.data = {
                "method": "exponential_weighted",
                "span": span if alpha is None and halflife is None else None,
                "alpha": alpha,
                "halflife": halflife,
                "include_std": include_std,
                "numeric_columns": numeric_df.columns.tolist(),
                "rows_processed": len(numeric_df),
                "output_shape": str(ewma_mean.shape)
            }
            
            logger.info(f"EWMA: span={span}, alpha={alpha}, halflife={halflife}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"EWMA calculation failed: {e}")
            result.success = False
            return result
