"""SkewnessKurtosisAnalyzer - Worker for analyzing distribution shape.

Calculates skewness and kurtosis to characterize the shape of distributions.
"""

from typing import Any, Dict, Optional
import pandas as pd
from scipy import stats

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)

# Constants
MIN_SAMPLES = 3  # Minimum samples for skewness/kurtosis
SYMMETRY_THRESHOLD = 0.5  # Threshold for considering symmetric
KURTOSIS_THRESHOLD = 0.5  # Threshold for normal peakedness


class SkewnessKurtosisAnalyzer(BaseWorker):
    """Worker that calculates skewness and kurtosis of distributions.
    
    Analyzes the shape of data distributions using two key metrics:
    - Skewness: Measures asymmetry (left/right tails)
    - Kurtosis: Measures tail weight (peakedness)
    
    Skewness Interpretation:
        - > 0: Right-skewed (positive tail)
        - < 0: Left-skewed (negative tail)
        - ~0: Symmetric
    
    Kurtosis Interpretation:
        - > 0: Leptokurtic (heavy tails, peaked)
        - < 0: Platykurtic (light tails, flat)
        - ~0: Mesokurtic (normal-like)
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame containing data (required)
        column: str - Column name to analyze (required)
    
    Output Format:
        result.data contains:
            column: Analyzed column name
            skewness: Skewness coefficient
            kurtosis: Excess kurtosis (relative to normal)
            is_symmetric: Boolean (True if |skewness| < 0.5)
            is_normal_peaked: Boolean (True if |kurtosis| < 0.5)
            skewness_interpretation: Human-readable skewness
            kurtosis_interpretation: Human-readable kurtosis
            sample_size: Number of samples used
    
    Quality Score:
        - 1.0: Successfully calculated both metrics
        - 0.0: Failed or insufficient data
    
    Example:
        >>> analyzer = SkewnessKurtosisAnalyzer()
        >>> result = analyzer.safe_execute(df=df, column='revenue')
        >>> if result.success:
        ...     print(f"Skewness: {result.data['skewness']}")
        ...     print(f"Kurtosis: {result.data['kurtosis']}")
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize SkewnessKurtosisAnalyzer worker."""
        super().__init__("SkewnessKurtosisAnalyzer")
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
        """Calculate skewness and kurtosis for column.
        
        Args:
            df: DataFrame containing data
            column: Column name to analyze
            
        Returns:
            WorkerResult with skewness/kurtosis metrics
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        df = kwargs.get('df')
        column = kwargs.get('column')
        
        result = self._create_result(task_type="skewness_kurtosis")
        
        try:
            self.logger.info(f"Calculating skewness/kurtosis for column '{column}'")
            
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
            
            # Calculate skewness and kurtosis
            skewness = stats.skew(series)
            kurtosis_val = stats.kurtosis(series)  # Excess kurtosis (relative to normal)
            
            # Interpret metrics
            is_symmetric = abs(skewness) < SYMMETRY_THRESHOLD
            is_normal_peaked = abs(kurtosis_val) < KURTOSIS_THRESHOLD
            
            result.data = {
                "column": column,
                "skewness": round(float(skewness), 6),
                "kurtosis": round(float(kurtosis_val), 6),
                "is_symmetric": is_symmetric,
                "is_normal_peaked": is_normal_peaked,
                "skewness_interpretation": self._interpret_skewness(skewness),
                "kurtosis_interpretation": self._interpret_kurtosis(kurtosis_val),
                "sample_size": len(series),
            }
            
            result.success = True
            result.quality_score = 1.0
            
            self.logger.info(
                f"Skewness/Kurtosis for '{column}': "
                f"skewness={skewness:.6f}, kurtosis={kurtosis_val:.6f}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"SkewnessKurtosisAnalyzer execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Skewness/Kurtosis calculation failed: {str(e)}",
                severity="critical",
                suggestion="Check column contains numeric data"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
    
    @staticmethod
    def _interpret_skewness(skewness: float) -> str:
        """Interpret skewness value.
        
        Args:
            skewness: Skewness coefficient
            
        Returns:
            Human-readable interpretation
        """
        if skewness > SYMMETRY_THRESHOLD:
            return "Right-skewed (positive tail)"
        elif skewness < -SYMMETRY_THRESHOLD:
            return "Left-skewed (negative tail)"
        else:
            return "Approximately symmetric"
    
    @staticmethod
    def _interpret_kurtosis(kurtosis_val: float) -> str:
        """Interpret kurtosis value.
        
        Args:
            kurtosis_val: Excess kurtosis value
            
        Returns:
            Human-readable interpretation
        """
        if kurtosis_val > KURTOSIS_THRESHOLD:
            return "Leptokurtic (heavy tails, peaked)"
        elif kurtosis_val < -KURTOSIS_THRESHOLD:
            return "Platykurtic (light tails, flat)"
        else:
            return "Mesokurtic (normal-like tails)"
