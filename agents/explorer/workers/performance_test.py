"""Performance Test - Benchmarks and performance analysis."""

import pandas as pd
import time
import numpy as np
from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class PerformanceTest(BaseWorker):
    """Worker that benchmarks data operations."""
    
    def __init__(self):
        """Initialize PerformanceTest."""
        super().__init__("PerformanceTest")
    
    def execute(self, df: pd.DataFrame = None, operations: list = None, **kwargs) -> WorkerResult:
        """Benchmark performance of data operations.
        
        Args:
            df: DataFrame to benchmark
            operations: List of operations to test
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with performance metrics
        """
        result = self._create_result(task_type="performance_test")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        try:
            benchmarks = {}
            
            # Basic operations
            start = time.time()
            _ = df.describe()
            benchmarks['describe'] = time.time() - start
            
            start = time.time()
            _ = df.corr()
            benchmarks['corr'] = time.time() - start
            
            result.data = {
                "rows": len(df),
                "columns": len(df.columns),
                "benchmarks": benchmarks,
                "total_time": sum(benchmarks.values())
            }
            
            logger.info(f"Performance test completed")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Performance test failed: {e}")
            result.success = False
            return result
