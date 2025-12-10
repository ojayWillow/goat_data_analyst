"""Outlier Detector Worker - Detects outliers using Z-score method."""

import pandas as pd
import numpy as np
from scipy import stats

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class OutlierDetector(BaseWorker):
    """Worker that detects outliers using z-score method."""
    
    def __init__(self):
        """Initialize OutlierDetector."""
        super().__init__("OutlierDetector")
    
    def execute(self, column: str = None, threshold: float = 3, **kwargs) -> WorkerResult:
        """Detect outliers using z-score.
        
        Args:
            column: Column name
            threshold: Z-score threshold (default 3)
            **kwargs: df and other arguments
            
        Returns:
            WorkerResult with outlier information
        """
        df = kwargs.get('df')
        result = self._create_result(task_type="outlier_detection")
        
        if df is None or column is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df and column required")
            result.success = False
            return result
        
        try:
            series = df[column].dropna()
            z_scores = np.abs(stats.zscore(series))
            outliers = z_scores > threshold
            
            result.data = {
                "column": column,
                "method": "z-score",
                "threshold": threshold,
                "outlier_count": int(outliers.sum()),
                "outlier_percentage": round(outliers.sum() / len(series) * 100, 2)
            }
            
            logger.info(f"Outliers {column}: {outliers.sum()} found")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Outlier detection failed: {e}")
            result.success = False
            return result
