"""NormalityTester - Worker for testing normality of data.

Tests if data follows a normal distribution using Shapiro-Wilk test.
"""

from typing import Any, Dict, Optional
import pandas as pd
from scipy import stats

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)

# Constants
MIN_SAMPLES = 3  # Minimum samples for Shapiro-Wilk
MAX_SAMPLES = 5000  # Maximum samples for Shapiro-Wilk
NORMALITY_ALPHA = 0.05  # Significance level


class NormalityTester(BaseWorker):
    """Worker that tests for normality using Shapiro-Wilk test.
    
    Tests whether numeric data follows a normal (Gaussian) distribution.
    Uses Shapiro-Wilk test which is reliable for sample sizes up to 5000.
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame containing data (required)
        column: str - Column name to test (required)
    
    Output Format:
        result.data contains:
            column: Tested column name
            test: Test name ('Shapiro-Wilk')
            statistic: Test statistic value
            p_value: P-value from test
            is_normal: Boolean (True if p_value > 0.05)
            sample_size: Number of non-null samples used
    
    Quality Score:
        - 1.0: Test executed successfully
        - 0.0: Test failed or insufficient data
    
    Example:
        >>> tester = NormalityTester()
        >>> result = tester.safe_execute(df=df, column='revenue')
        >>> if result.success:
        ...     is_normal = result.data['is_normal']
        ...     p_value = result.data['p_value']
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize NormalityTester worker."""
        super().__init__("NormalityTester")
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
        """Test normality of specified column.
        
        Args:
            df: DataFrame containing data
            column: Column name to test
            
        Returns:
            WorkerResult with normality test results
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        df = kwargs.get('df')
        column = kwargs.get('column')
        
        result = self._create_result(task_type="normality_test")
        
        try:
            self.logger.info(f"Testing normality of column '{column}'")
            
            # Remove NaN values
            series = df[column].dropna()
            
            if len(series) < MIN_SAMPLES:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    f"Need at least {MIN_SAMPLES} non-null values, got {len(series)}",
                    severity="warning",
                    suggestion="Ensure column has enough non-null data"
                )
                result.success = False
                result.quality_score = 0.0
                return result
            
            # Limit samples if needed (Shapiro-Wilk limitation)
            if len(series) > MAX_SAMPLES:
                self.logger.warning(
                    f"Series has {len(series)} samples, limiting to {MAX_SAMPLES} for test"
                )
                series = series.sample(MAX_SAMPLES, random_state=42)
                self._add_warning(
                    result,
                    f"Data truncated from {len(df[column])} to {len(series)} samples for testing"
                )
            
            # Perform Shapiro-Wilk test
            statistic, p_value = stats.shapiro(series)
            
            # Determine normality (reject null hypothesis if p < alpha)
            is_normal = p_value > NORMALITY_ALPHA
            
            result.data = {
                "column": column,
                "test": "Shapiro-Wilk",
                "statistic": round(float(statistic), 6),
                "p_value": round(float(p_value), 6),
                "is_normal": is_normal,
                "alpha": NORMALITY_ALPHA,
                "interpretation": "Normal distribution" if is_normal else "Non-normal distribution",
                "sample_size": len(series),
            }
            
            result.success = True
            result.quality_score = 1.0
            
            self.logger.info(
                f"Normality test on '{column}': statistic={statistic:.6f}, "
                f"p_value={p_value:.6f}, is_normal={is_normal}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"NormalityTester execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Normality test failed: {str(e)}",
                severity="critical",
                suggestion="Check column contains numeric data"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
