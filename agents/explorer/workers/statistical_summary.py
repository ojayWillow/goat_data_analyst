"""Statistical Summary - Generates comprehensive statistical summaries."""

import pandas as pd
import numpy as np
from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)


class StatisticalSummary(BaseWorker):
    """Worker that generates statistical summaries."""
    
    def __init__(self):
        """Initialize StatisticalSummary."""
        super().__init__("StatisticalSummary")
        self.error_intelligence = ErrorIntelligence()
    
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
            self._add_error(result, ErrorType.MISSING_DATA, "df required")
            result.success = False
            return result
        
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(result, ErrorType.COMPUTATION_ERROR, "No numeric columns")
                result.success = False
                return result
            
            summary = numeric_df.describe()
            
            result.data = {
                "columns": numeric_df.columns.tolist(),
                "rows": len(numeric_df),
                "statistics": summary.to_dict()
            }
            
            self.error_intelligence.track_success(
                agent_name="explorer",
                worker_name="StatisticalSummary",
                operation="execute",
                context={"columns": len(numeric_df.columns), "rows": len(numeric_df)}
            )
            
            logger.info(f"Statistical summary generated for {len(numeric_df.columns)} columns")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"Statistical summary failed: {e}")
            result.success = False
            
            self.error_intelligence.track_error(
                agent_name="explorer",
                worker_name="StatisticalSummary",
                error_type=type(e).__name__,
                error_message=str(e),
                context={}
            )
            
            return result
