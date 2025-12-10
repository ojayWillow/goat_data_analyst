"""Statistical Summary - Generates comprehensive statistical summaries."""

import pandas as pd
import numpy as np
from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class StatisticalSummary(BaseWorker):
    """Worker that generates statistical summaries."""
    
    def __init__(self):
        """Initialize StatisticalSummary."""
        super().__init__("StatisticalSummary")
    
    def execute(self, df: pd.DataFrame = None, **kwargs) -> WorkerResult:
        """Generate statistical summary.
        
        Args:
            df: DataFrame to analyze
            **kwargs: Additional arguments
            
        Returns:
            WorkerResult with statistical summary
        """
        result = self._create_result(task_type="statistical_summary")
        
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
            
            summary = numeric_df.describe()
            
            result.data = {
                "columns": numeric_df.columns.tolist(),
                "rows": len(numeric_df),
                "statistics": summary.to_dict()
            }
            
            logger.info(f"Statistical summary generated for {len(numeric_df.columns)} columns")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Statistical summary failed: {e}")
            result.success = False
            return result
