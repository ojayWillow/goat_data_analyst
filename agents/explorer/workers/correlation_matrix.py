"""Correlation Matrix - Computes and analyzes correlation matrices."""

import pandas as pd
import numpy as np
from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class CorrelationMatrix(BaseWorker):
    """Worker that computes correlation matrices."""
    
    def __init__(self):
        """Initialize CorrelationMatrix."""
        super().__init__("CorrelationMatrix")
    
    def execute(self, df: pd.DataFrame = None, method: str = 'pearson', **kwargs) -> WorkerResult:
        """Compute correlation matrix.
        
        Args:
            df: DataFrame to analyze
            method: 'pearson', 'spearman', or 'kendall'
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with correlation matrix
        """
        result = self._create_result(task_type="correlation_matrix")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(result, ErrorType.LOAD_ERROR, "No numeric columns")
                result.success = False
                return result
            
            corr_matrix = numeric_df.corr(method=method)
            
            result.data = {
                "method": method,
                "shape": corr_matrix.shape,
                "columns": numeric_df.columns.tolist()
            }
            
            logger.info(f"Correlation matrix computed: {method}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Correlation matrix failed: {e}")
            result.success = False
            return result
