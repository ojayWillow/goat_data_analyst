"""Correlation Matrix Worker - Analyzes correlations between numeric columns."""

import pandas as pd
import numpy as np

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class CorrelationMatrixWorker(BaseWorker):
    """Worker that calculates correlation matrix."""
    
    def __init__(self):
        """Initialize CorrelationMatrixWorker."""
        super().__init__("CorrelationMatrixWorker")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Calculate correlation matrix for numeric columns.
        
        Args:
            **kwargs: df and other arguments
            
        Returns:
            WorkerResult with correlation matrix
        """
        df = kwargs.get('df')
        result = self._create_result(task_type="correlation_matrix")
        
        if df is None:
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df required")
            result.success = False
            return result
        
        try:
            numeric_data = df.select_dtypes(include=[np.number])
            
            if numeric_data.empty:
                result.data = {"message": "No numeric columns found"}
                return result
            
            corr_matrix = numeric_data.corr()
            
            result.data = {
                "shape": corr_matrix.shape,
                "columns": corr_matrix.columns.tolist(),
                "num_pairs": int((corr_matrix.shape[0] ** 2 - corr_matrix.shape[0]) / 2)
            }
            
            logger.info(f"Correlation matrix: {corr_matrix.shape}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Correlation matrix failed: {e}")
            result.success = False
            return result
