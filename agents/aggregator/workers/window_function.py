"""WindowFunction - Rolling window operations."""

import pandas as pd
import numpy as np
from typing import List, Optional

from agents.aggregator.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class WindowFunction(BaseWorker):
    """Worker that calculates rolling window functions on data."""
    
    def __init__(self):
        """Initialize WindowFunction."""
        super().__init__("WindowFunction")
    
    def execute(
        self,
        df: pd.DataFrame = None,
        window_size: int = 3,
        operations: Optional[List[str]] = None,
        **kwargs
    ) -> WorkerResult:
        """Calculate rolling window operations.
        
        Args:
            df: DataFrame to process
            window_size: Size of rolling window
            operations: List of operations ('mean', 'sum', 'std', 'min', 'max')
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with windowed data
        """
        result = self._create_result(task_type="window_functions")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        if operations is None:
            operations = ['mean']
        
        try:
            # Select numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(result, ErrorType.LOAD_ERROR, "No numeric columns found")
                result.success = False
                return result
            
            if window_size < 1:
                self._add_error(result, ErrorType.VALIDATION_ERROR, "window_size must be >= 1")
                result.success = False
                return result
            
            windowed_results = {}
            
            for operation in operations:
                if operation == 'mean':
                    windowed_results[f'rolling_{operation}'] = numeric_df.rolling(window=window_size).mean()
                elif operation == 'sum':
                    windowed_results[f'rolling_{operation}'] = numeric_df.rolling(window=window_size).sum()
                elif operation == 'std':
                    windowed_results[f'rolling_{operation}'] = numeric_df.rolling(window=window_size).std()
                elif operation == 'min':
                    windowed_results[f'rolling_{operation}'] = numeric_df.rolling(window=window_size).min()
                elif operation == 'max':
                    windowed_results[f'rolling_{operation}'] = numeric_df.rolling(window=window_size).max()
                else:
                    logger.warning(f"Unknown operation: {operation}")
            
            result.data = {
                "window_size": window_size,
                "operations_applied": list(windowed_results.keys()),
                "numeric_columns": numeric_df.columns.tolist(),
                "rows_processed": len(numeric_df),
                "nan_count_after_windowing": sum(
                    numeric_df.rolling(window=window_size).mean().isna().sum().sum()
                )
            }
            
            logger.info(f"Window functions: window_size={window_size}, operations={operations}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Window functions failed: {e}")
            result.success = False
            return result
