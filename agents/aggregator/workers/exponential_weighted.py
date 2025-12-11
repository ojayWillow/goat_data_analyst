"""ExponentialWeighted - Exponential weighted moving average."""

import pandas as pd
import numpy as np
from typing import Optional

from agents.aggregator.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class ExponentialWeighted(BaseWorker):
    """Worker that calculates exponential weighted moving average."""
    
    def __init__(self):
        """Initialize ExponentialWeighted."""
        super().__init__("ExponentialWeighted")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(
        self,
        df: pd.DataFrame = None,
        span: int = 10,
        adjust: bool = True,
        **kwargs
    ) -> WorkerResult:
        """Calculate exponential weighted moving average.
        
        Args:
            df: DataFrame to process
            span: Span for exponential weighting
            adjust: Whether to apply exponential scaling
            
        Returns:
            WorkerResult with EWMA results
        """
        try:
            result = self._run_ewma(df, span, adjust, **kwargs)
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="ExponentialWeighted",
                operation="exponential_weighted",
                context={"span": span}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="ExponentialWeighted",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"span": span}
            )
            raise
    
    def _run_ewma(self, df, span, adjust, **kwargs) -> WorkerResult:
        """Calculate exponential weighted moving average."""
        result = self._create_result(task_type="exponential_weighted")
        
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
            
            if span < 1:
                self._add_error(result, ErrorType.VALIDATION_ERROR, "span must be >= 1")
                result.success = False
                return result
            
            ewma = numeric_df.ewm(span=span, adjust=adjust).mean()
            ewma_std = numeric_df.ewm(span=span, adjust=adjust).std()
            
            result.data = {
                "method": "Exponential Weighted Moving Average",
                "span": span,
                "adjust": adjust,
                "columns_processed": numeric_df.columns.tolist(),
                "rows_processed": len(numeric_df),
                "ewma_mean": {col: float(ewma[col].mean()) for col in ewma.columns},
                "ewma_std": {col: float(ewma_std[col].mean()) for col in ewma_std.columns},
                "null_values_in_output": int(ewma.isna().sum().sum())
            }
            
            logger.info(f"Exponential weighted: span={span}, adjust={adjust}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Exponential weighted failed: {e}")
            result.success = False
            return result
