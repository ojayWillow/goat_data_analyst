"""Normality Tester Worker - Tests if data follows normal distribution."""

import pandas as pd
from scipy import stats

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)


class NormalityTester(BaseWorker):
    """Worker that tests for normality using Shapiro-Wilk test."""
    
    def __init__(self):
        """Initialize NormalityTester."""
        super().__init__("NormalityTester")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, column: str = None, **kwargs) -> WorkerResult:
        """Execute normality test on a column.
        
        Args:
            column: Column name to test
            **kwargs: df and other arguments
            
        Returns:
            WorkerResult with test results
        """
        df = kwargs.get('df')
        result = self._create_result(task_type="normality_test")
        
        if df is None or column is None:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "df and column required")
            result.success = False
            return result
        
        if column not in df.columns:
            self._add_error(result, ErrorType.INVALID_PARAMETER, f"Column '{column}' not found")
            result.success = False
            return result
        
        try:
            series = df[column].dropna()
            
            if len(series) < 3:
                self._add_error(result, ErrorType.INSUFFICIENT_DATA, "Need at least 3 values")
                result.success = False
                return result
            
            statistic, p_value = stats.shapiro(series)
            
            result.data = {
                "column": column,
                "test": "Shapiro-Wilk",
                "statistic": round(float(statistic), 6),
                "p_value": round(float(p_value), 6),
                "is_normal": bool(p_value > 0.05),
                "sample_size": len(series)
            }
            
            self.error_intelligence.track_success(
                agent_name="explorer",
                worker_name="NormalityTester",
                operation="execute",
                context={"column": column, "p_value": float(p_value), "is_normal": bool(p_value > 0.05)}
            )
            
            logger.info(f"Normality test on {column}: p_value={p_value}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"Normality test failed: {e}")
            result.success = False
            
            self.error_intelligence.track_error(
                agent_name="explorer",
                worker_name="NormalityTester",
                error_type=type(e).__name__,
                error_message=str(e),
                context={}
            )
            
            return result
