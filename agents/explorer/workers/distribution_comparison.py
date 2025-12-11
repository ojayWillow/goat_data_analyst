"""Distribution Comparison Worker - KS test and other distribution tests."""

import pandas as pd
from scipy import stats

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)


class DistributionComparison(BaseWorker):
    """Worker that compares distributions using Kolmogorov-Smirnov test."""
    
    def __init__(self):
        """Initialize DistributionComparison."""
        super().__init__("DistributionComparison")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, col1: str = None, col2: str = None, **kwargs) -> WorkerResult:
        """Execute KS test comparing two distributions.
        
        Args:
            col1: First column name
            col2: Second column name
            **kwargs: df and other arguments
            
        Returns:
            WorkerResult with test results
        """
        df = kwargs.get('df')
        result = self._create_result(task_type="distribution_comparison")
        
        if df is None or col1 is None or col2 is None:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "df, col1, col2 required")
            result.success = False
            return result
        
        try:
            s1 = df[col1].dropna()
            s2 = df[col2].dropna()
            
            if len(s1) < 2 or len(s2) < 2:
                self._add_error(result, ErrorType.INSUFFICIENT_DATA, "Need at least 2 values in each column")
                result.success = False
                return result
            
            statistic, p_value = stats.ks_2samp(s1, s2)
            
            result.data = {
                "col1": col1,
                "col2": col2,
                "test": "Kolmogorov-Smirnov",
                "statistic": round(float(statistic), 6),
                "p_value": round(float(p_value), 6),
                "distributions_equal": bool(p_value > 0.05)
            }
            
            self.error_intelligence.track_success(
                agent_name="explorer",
                worker_name="DistributionComparison",
                operation="execute",
                context={"col1": col1, "col2": col2, "p_value": float(p_value)}
            )
            
            logger.info(f"KS test {col1} vs {col2}: p_value={p_value}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"KS test failed: {e}")
            result.success = False
            
            self.error_intelligence.track_error(
                agent_name="explorer",
                worker_name="DistributionComparison",
                error_type=type(e).__name__,
                error_message=str(e),
                context={}
            )
            
            return result
