"""DistributionComparison - Worker for comparing distributions.

Compares distributions of two columns using Kolmogorov-Smirnov test.
"""

from typing import Any, Dict, Optional
import pandas as pd
from scipy import stats

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)

# Constants
MIN_SAMPLES = 2  # Minimum samples for KS test
SIGNIFICANCE_LEVEL = 0.05  # Alpha for hypothesis testing


class DistributionComparison(BaseWorker):
    """Worker that compares distributions using Kolmogorov-Smirnov test.
    
    Tests whether two samples come from the same distribution using
    the Kolmogorov-Smirnov (KS) test. This is a non-parametric test
    that works for any continuous distribution.
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame containing data (required)
        col1: str - First column name (required)
        col2: str - Second column name (required)
    
    Output Format:
        result.data contains:
            col1: First column name
            col2: Second column name
            test: Test name ('Kolmogorov-Smirnov')
            statistic: KS test statistic (0-1)
            p_value: P-value from test
            distributions_equal: Boolean (True if p_value > 0.05)
            interpretation: Human-readable result
            sample_sizes: Dict with sizes for both columns
    
    Quality Score:
        - 1.0: Test executed successfully
        - 0.0: Test failed or insufficient data
    
    Example:
        >>> comparator = DistributionComparison()
        >>> result = comparator.safe_execute(df=df, col1='col1', col2='col2')
        >>> if result.success:
        ...     if result.data['distributions_equal']:
        ...         print("Distributions are statistically similar")
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize DistributionComparison worker."""
        super().__init__("DistributionComparison")
        self.error_intelligence = ErrorIntelligence()
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters.
        
        Args:
            **kwargs: Must contain 'df', 'col1', and 'col2' keys
            
        Returns:
            WorkerError if validation fails, None if valid
        """
        df = kwargs.get('df')
        col1 = kwargs.get('col1')
        col2 = kwargs.get('col2')
        
        if df is None:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="No DataFrame provided (df=None)",
                severity="error",
                suggestion="Provide df parameter"
            )
        
        if not isinstance(df, pd.DataFrame):
            return WorkerError(
                error_type=ErrorType.TYPE_ERROR,
                message=f"Expected DataFrame, got {type(df).__name__}",
                severity="error",
                suggestion="df must be a pandas DataFrame"
            )
        
        if col1 is None or col2 is None:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="Both col1 and col2 must be specified",
                severity="error",
                suggestion="Provide col1 and col2 parameters"
            )
        
        if col1 not in df.columns:
            return WorkerError(
                error_type=ErrorType.INVALID_PARAMETER,
                message=f"Column '{col1}' not found in DataFrame",
                severity="error",
                suggestion=f"Available columns: {list(df.columns)}"
            )
        
        if col2 not in df.columns:
            return WorkerError(
                error_type=ErrorType.INVALID_PARAMETER,
                message=f"Column '{col2}' not found in DataFrame",
                severity="error",
                suggestion=f"Available columns: {list(df.columns)}"
            )
        
        return None
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Compare distributions of two columns.
        
        Args:
            df: DataFrame containing data
            col1: First column name
            col2: Second column name
            
        Returns:
            WorkerResult with KS test results
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        df = kwargs.get('df')
        col1 = kwargs.get('col1')
        col2 = kwargs.get('col2')
        
        result = self._create_result(task_type="distribution_comparison")
        
        try:
            self.logger.info(f"Comparing distributions: '{col1}' vs '{col2}'")
            
            # Remove NaN values
            s1 = df[col1].dropna()
            s2 = df[col2].dropna()
            
            if len(s1) < MIN_SAMPLES or len(s2) < MIN_SAMPLES:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    f"Need at least {MIN_SAMPLES} samples in each column, "
                    f"got {len(s1)} and {len(s2)}",
                    severity="warning"
                )
                result.success = False
                result.quality_score = 0.0
                return result
            
            # Perform Kolmogorov-Smirnov test
            statistic, p_value = stats.ks_2samp(s1, s2)
            
            # Determine if distributions are equal
            distributions_equal = p_value > SIGNIFICANCE_LEVEL
            
            result.data = {
                "col1": col1,
                "col2": col2,
                "test": "Kolmogorov-Smirnov",
                "statistic": round(float(statistic), 6),
                "p_value": round(float(p_value), 6),
                "distributions_equal": distributions_equal,
                "alpha": SIGNIFICANCE_LEVEL,
                "interpretation": "Distributions are statistically similar" if distributions_equal else "Distributions are significantly different",
                "sample_sizes": {
                    col1: len(s1),
                    col2: len(s2)
                },
            }
            
            result.success = True
            result.quality_score = 1.0
            
            self.logger.info(
                f"KS test '{col1}' vs '{col2}': statistic={statistic:.6f}, "
                f"p_value={p_value:.6f}, equal={distributions_equal}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"DistributionComparison execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"KS test failed: {str(e)}",
                severity="critical",
                suggestion="Check columns contain numeric data"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
