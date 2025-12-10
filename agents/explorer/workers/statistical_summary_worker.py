"""Statistical Summary Worker - Provides comprehensive statistical summary."""

import pandas as pd
import numpy as np
import time

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class StatisticalSummaryWorker(BaseWorker):
    """Worker that calculates comprehensive statistical summaries."""
    
    def __init__(self):
        """Initialize StatisticalSummaryWorker."""
        super().__init__("StatisticalSummaryWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Calculate statistical summary for all numeric columns.
        
        Args:
            **kwargs: df and other arguments
            
        Returns:
            WorkerResult with statistical summaries
        """
        df = kwargs.get('df')
        result = self._create_result(task_type="statistical_summary")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        start_time = time.time()
        
        try:
            numeric_data = df.select_dtypes(include=[np.number])
            summary = {}
            
            for col in numeric_data.columns:
                series = numeric_data[col].dropna()
                summary[col] = {
                    "mean": round(float(series.mean()), 6),
                    "median": round(float(series.median()), 6),
                    "std": round(float(series.std()), 6),
                    "min": round(float(series.min()), 6),
                    "max": round(float(series.max()), 6),
                    "q25": round(float(series.quantile(0.25)), 6),
                    "q75": round(float(series.quantile(0.75)), 6),
                    "null_count": int(numeric_data[col].isna().sum())
                }
            
            duration = time.time() - start_time
            
            result.data = {
                "columns_analyzed": len(summary),
                "duration_sec": round(duration, 3),
                "summary_keys": list(summary.keys())
            }
            
            logger.info(f"Statistical summary: {len(summary)} columns in {duration:.3f}s")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Statistical summary failed: {e}")
            result.success = False
            return result
