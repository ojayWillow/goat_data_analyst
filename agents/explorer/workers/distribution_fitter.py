"""Distribution Fitter Worker - Fits common distributions to data."""

import pandas as pd
from scipy import stats

from agents.explorer.workers.base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class DistributionFitter(BaseWorker):
    """Worker that fits common distributions to data."""
    
    def __init__(self):
        """Initialize DistributionFitter."""
        super().__init__("DistributionFitter")
    
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
            self._add_error(result, ErrorType.VALIDATION_ERROR, "df and column required")
            result.success = False
            return result
        
        try:
            series = df[column].dropna()
            distributions = {}
            
            # Try common distributions
            try:
                params = stats.norm.fit(series)
                distributions['normal'] = True
            except: pass
            
            try:
                params = stats.expon.fit(series)
                distributions['exponential'] = True
            except: pass
            
            if (series > 0).all():
                try:
                    params = stats.gamma.fit(series)
                    distributions['gamma'] = True
                except: pass
            
            result.data = {
                "column": column,
                "distributions_tested": list(distributions.keys()),
                "best_fit": list(distributions.keys())[0] if distributions else None,
                "sample_size": len(series)
            }
            
            logger.info(f"Distribution fitting {column}: {len(distributions)} distributions fitted")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.LOAD_ERROR, f"Distribution fitting failed: {e}")
            result.success = False
            return result
