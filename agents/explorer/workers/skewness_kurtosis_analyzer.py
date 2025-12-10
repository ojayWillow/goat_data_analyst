"""Skewness/Kurtosis Worker - Analyzes distribution shape."""

import pandas as pd
from scipy import stats

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class SkewnessKurtosisAnalyzer(BaseWorker):
    """Worker that calculates skewness and kurtosis."""
    
    def __init__(self):
        """Initialize SkewnessKurtosisAnalyzer."""
        super().__init__("SkewnessKurtosisAnalyzer")
    
    def execute(self, column: str = None, **kwargs) -> WorkerResult:
        """Calculate skewness and kurtosis.
        
        Args:
            column: Column name
            **kwargs: df and other arguments
            
        Returns:
            WorkerResult with skewness/kurtosis values
        """
        df = kwargs.get('df')
        result = self._create_result(task_type="skewness_kurtosis")
        
        if df is None or column is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df and column required")
            result.success = False
            return result
        
        try:
            series = df[column].dropna()
            
            skewness = stats.skew(series)
            kurtosis = stats.kurtosis(series)
            
            result.data = {
                "column": column,
                "skewness": round(float(skewness), 6),
                "kurtosis": round(float(kurtosis), 6),
                "is_symmetric": bool(abs(skewness) < 0.5),
                "is_normal_peaked": bool(abs(kurtosis) < 0.5)
            }
            
            logger.info(f"Skewness/Kurtosis {column}: skew={skewness}, kurt={kurtosis}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Skewness/Kurtosis failed: {e}")
            result.success = False
            return result
