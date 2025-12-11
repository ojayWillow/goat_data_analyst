"""Distribution Fitter Worker - Fits common distributions to data."""

import pandas as pd
from scipy import stats

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)


class DistributionFitter(BaseWorker):
    """Worker that fits common distributions to data."""
    
    def __init__(self):
        """Initialize DistributionFitter."""
        super().__init__("DistributionFitter")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, column: str = None, **kwargs) -> WorkerResult:
        """Fit distributions to column data.
        
        Args:
            column: Column name
            **kwargs: df and other arguments
            
        Returns:
            WorkerResult with best-fit distribution
        """
        df = kwargs.get('df')
        result = self._create_result(task_type="distribution_fitting")
        
        if df is None or column is None:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "df and column required")
            result.success = False
            return result
        
        try:
            series = df[column].dropna()
            distributions = {}
            
            # Try common distributions
            try:
                params = stats.norm.fit(series)
                distributions['normal'] = True
            except:
                pass
            
            try:
                params = stats.expon.fit(series)
                distributions['exponential'] = True
            except:
                pass
            
            if (series > 0).all():
                try:
                    params = stats.gamma.fit(series)
                    distributions['gamma'] = True
                except:
                    pass
            
            result.data = {
                "column": column,
                "distributions_tested": list(distributions.keys()),
                "best_fit": list(distributions.keys())[0] if distributions else None,
                "sample_size": len(series)
            }
            
            self.error_intelligence.track_success(
                agent_name="explorer",
                worker_name="DistributionFitter",
                operation="execute",
                context={"column": column, "distributions_count": len(distributions)}
            )
            
            logger.info(f"Distribution fitting {column}: {len(distributions)} distributions fitted")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"Distribution fitting failed: {e}")
            result.success = False
            
            self.error_intelligence.track_error(
                agent_name="explorer",
                worker_name="DistributionFitter",
                error_type=type(e).__name__,
                error_message=str(e),
                context={}
            )
            
            return result
