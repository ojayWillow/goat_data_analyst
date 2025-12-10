"""Performance Test Worker - Tests statistical operations performance on large datasets."""

import pandas as pd
import numpy as np
import time

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class PerformanceTestWorker(BaseWorker):
    """Worker that tests performance of statistical operations."""
    
    def __init__(self):
        """Initialize PerformanceTestWorker."""
        super().__init__("PerformanceTestWorker")
    
    def execute(self, target_rows: int = 100000, **kwargs) -> WorkerResult:
        """Test performance on large dataset.
        
        Args:
            target_rows: Target number of rows to test with
            **kwargs: df and other arguments
            
        Returns:
            WorkerResult with performance metrics
        """
        df = kwargs.get('df')
        result = self._create_result(task_type="performance_test")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        try:
            start_time = time.time()
            
            # Run statistical analysis on the data
            numeric_data = df.select_dtypes(include=[np.number])
            
            # Test correlation
            corr_matrix = numeric_data.corr()
            
            # Test summary stats
            for col in numeric_data.columns:
                series = numeric_data[col].dropna()
                _ = series.describe()
            
            duration = time.time() - start_time
            
            result.data = {
                "rows_tested": len(df),
                "duration_sec": round(duration, 3),
                "performance_ok": duration < 2.0 if len(df) >= 100000 else True,
                "rows_per_sec": round(len(df) / duration if duration > 0 else 0)
            }
            
            logger.info(f"Performance test: {len(df)} rows in {duration:.3f}s")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Performance test failed: {e}")
            result.success = False
            return result
