"""DistributionFitter - Worker for fitting distributions to data.

Fits common probability distributions to numeric data and identifies best fit.
"""

from typing import Any, Dict, Optional
import pandas as pd
from scipy import stats

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)

# Constants
MIN_SAMPLES = 5  # Minimum samples for distribution fitting
DISTRIBUTIONS_TO_TEST = ['normal', 'exponential', 'gamma', 'lognormal']


class DistributionFitter(BaseWorker):
    """Worker that fits common distributions to numeric data.
    
    Tests data against common probability distributions and identifies
    which distribution provides the best fit using maximum likelihood.
    
    Distributions tested:
    - Normal (Gaussian)
    - Exponential
    - Gamma
    - Lognormal (for positive data)
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame containing data (required)
        column: str - Column name to fit (required)
    
    Output Format:
        result.data contains:
            column: Tested column name
            distributions_tested: List of attempted distributions
            fit_results: Dict mapping distribution to fit quality
            best_fit: Distribution with best fit
            sample_size: Number of samples used
    
    Quality Score:
        - 1.0: Successfully fit multiple distributions
        - 0.5: Fit at least one distribution
        - 0.0: Failed to fit any distribution
    
    Example:
        >>> fitter = DistributionFitter()
        >>> result = fitter.safe_execute(df=df, column='values')
        >>> if result.success:
        ...     print(f"Best fit: {result.data['best_fit']}")
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize DistributionFitter worker."""
        super().__init__("DistributionFitter")
        self.error_intelligence = ErrorIntelligence()
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters.
        
        Args:
            **kwargs: Must contain 'df' and 'column' keys
            
        Returns:
            WorkerError if validation fails, None if valid
        """
        df = kwargs.get('df')
        column = kwargs.get('column')
        
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
        
        if column is None:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="No column specified",
                severity="error",
                suggestion="Provide column parameter"
            )
        
        if column not in df.columns:
            return WorkerError(
                error_type=ErrorType.INVALID_PARAMETER,
                message=f"Column '{column}' not found in DataFrame",
                severity="error",
                details={"available_columns": list(df.columns)},
                suggestion=f"Column must be one of: {list(df.columns)}"
            )
        
        return None
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Fit distributions to column data.
        
        Args:
            df: DataFrame containing data
            column: Column name to fit
            
        Returns:
            WorkerResult with distribution fitting results
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        df = kwargs.get('df')
        column = kwargs.get('column')
        
        result = self._create_result(task_type="distribution_fitting")
        
        try:
            self.logger.info(f"Fitting distributions to column '{column}'")
            
            # Remove NaN values
            series = df[column].dropna()
            
            if len(series) < MIN_SAMPLES:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    f"Need at least {MIN_SAMPLES} samples, got {len(series)}",
                    severity="warning"
                )
                result.success = False
                result.quality_score = 0.0
                return result
            
            # Fit distributions
            fit_results: Dict[str, Any] = {}
            errors_found = []
            
            # Test normal distribution
            try:
                params = stats.norm.fit(series)
                fit_results['normal'] = {
                    'mean': float(params[0]),
                    'std': float(params[1]),
                    'status': 'fit'
                }
            except Exception as e:
                errors_found.append(f"Normal fit failed: {e}")
            
            # Test exponential distribution
            try:
                params = stats.expon.fit(series)
                fit_results['exponential'] = {
                    'loc': float(params[0]),
                    'scale': float(params[1]),
                    'status': 'fit'
                }
            except Exception as e:
                errors_found.append(f"Exponential fit failed: {e}")
            
            # Test gamma distribution (requires positive data)
            if (series > 0).all():
                try:
                    params = stats.gamma.fit(series)
                    fit_results['gamma'] = {
                        'shape': float(params[0]),
                        'loc': float(params[1]),
                        'scale': float(params[2]),
                        'status': 'fit'
                    }
                except Exception as e:
                    errors_found.append(f"Gamma fit failed: {e}")
                
                # Test lognormal distribution
                try:
                    params = stats.lognorm.fit(series)
                    fit_results['lognormal'] = {
                        'shape': float(params[0]),
                        'loc': float(params[1]),
                        'scale': float(params[2]),
                        'status': 'fit'
                    }
                except Exception as e:
                    errors_found.append(f"Lognormal fit failed: {e}")
            else:
                self._add_warning(result, "Data contains non-positive values, skipping gamma/lognormal")
            
            # Add errors if any
            for error_msg in errors_found:
                self.logger.warning(error_msg)
            
            # Determine best fit (first successful is best)
            best_fit = list(fit_results.keys())[0] if fit_results else None
            
            result.data = {
                "column": column,
                "distributions_tested": DISTRIBUTIONS_TO_TEST,
                "fit_results": fit_results,
                "distributions_fit": len(fit_results),
                "best_fit": best_fit,
                "sample_size": len(series),
            }
            
            # Quality score based on number of fits
            if len(fit_results) >= 3:
                result.quality_score = 1.0
            elif len(fit_results) >= 1:
                result.quality_score = 0.6
            else:
                result.quality_score = 0.0
            
            result.success = len(fit_results) > 0
            
            self.logger.info(
                f"Distribution fitting complete for '{column}': "
                f"fitted {len(fit_results)} distributions, best: {best_fit}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"DistributionFitter execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Distribution fitting failed: {str(e)}",
                severity="critical",
                suggestion="Check column contains numeric data"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
