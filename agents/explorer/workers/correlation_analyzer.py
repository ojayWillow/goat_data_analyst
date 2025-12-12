"""CorrelationAnalyzer - Worker for analyzing correlations.

Analyzes correlations between numeric columns in a DataFrame.
Identifies strong correlations and computes full correlation matrix.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# Constants
DEFAULT_THRESHOLD = 0.7  # Default correlation threshold
MIN_NUMERIC_COLUMNS = 2  # Minimum columns needed for correlation
QUALITY_THRESHOLD = 0.8  # Threshold for good quality


class CorrelationAnalyzer(BaseWorker):
    """Worker that analyzes correlations between numeric columns.
    
    Computes correlation matrix for all numeric columns and identifies
    strong correlations above a specified threshold.
    
    Features:
    - Full correlation matrix computation
    - Strong correlation detection
    - Correlation strength rating (very_strong, strong, moderate, weak)
    - Positive/negative direction classification
    - Sorted by correlation strength
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame to analyze (required)
        threshold: float - Correlation threshold (default: 0.7)
    
    Output Format:
        result.data contains:
            correlation_matrix: Dict mapping column pairs to correlations
            strong_correlations: List of strong correlation dicts
            columns: List of analyzed column names
            correlation_count: Number of strong correlations found
            threshold: Used threshold value
    
    Quality Score:
        - 1.0: All numeric columns analyzed successfully
        - 0.5: Less than 2 numeric columns (warning)
        - 0.0: Errors occurred
    
    Example:
        >>> analyzer = CorrelationAnalyzer()
        >>> result = analyzer.safe_execute(df=df, threshold=0.7)
        >>> if result.success:
        ...     for corr in result.data['strong_correlations']:
        ...         print(f"{corr['column_1']} <-> {corr['column_2']}: {corr['correlation']}")
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize CorrelationAnalyzer worker."""
        super().__init__("CorrelationAnalyzer")
        self.error_intelligence = ErrorIntelligence()
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters.
        
        Args:
            **kwargs: Must contain 'df' key with DataFrame value
            
        Returns:
            WorkerError if validation fails, None if valid
        """
        df = kwargs.get('df')
        
        if df is None:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="No DataFrame provided (df=None)",
                severity="error",
                suggestion="Call with df parameter: analyzer.safe_execute(df=your_dataframe)"
            )
        
        if not isinstance(df, pd.DataFrame):
            return WorkerError(
                error_type=ErrorType.TYPE_ERROR,
                message=f"Expected DataFrame, got {type(df).__name__}",
                severity="error",
                details={"received_type": str(type(df))},
                suggestion="Pass a pandas DataFrame as the df parameter"
            )
        
        if df.empty:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="DataFrame is empty (0 rows)",
                severity="error",
                details={"shape": str(df.shape)},
                suggestion="Ensure DataFrame has data before analysis"
            )
        
        # Validate threshold parameter
        threshold = kwargs.get('threshold', DEFAULT_THRESHOLD)
        if not isinstance(threshold, (int, float)):
            return WorkerError(
                error_type=ErrorType.INVALID_PARAMETER,
                message=f"Threshold must be numeric, got {type(threshold).__name__}",
                severity="error",
                suggestion="Provide threshold as float between 0 and 1"
            )
        
        if not (0 <= threshold <= 1):
            return WorkerError(
                error_type=ErrorType.INVALID_PARAMETER,
                message=f"Threshold must be between 0 and 1, got {threshold}",
                severity="error",
                suggestion="Use threshold between 0 (all correlations) and 1 (perfect only)"
            )
        
        return None
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Analyze correlations in DataFrame.
        
        Args:
            df: DataFrame to analyze
            threshold: Correlation threshold (default: 0.7)
            
        Returns:
            WorkerResult with correlation analysis
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        # Note: validate_input() already checked in safe_execute()
        df = kwargs.get('df')
        threshold = kwargs.get('threshold', DEFAULT_THRESHOLD)
        
        result = self._create_result(
            task_type="correlation_analysis",
            quality_score=1.0
        )
        
        try:
            self.logger.info(
                f"Analyzing correlations from {df.shape[0]} rows, {df.shape[1]} columns "
                f"(threshold: {threshold})"
            )
            
            # Select numeric columns
            numeric_data = df.select_dtypes(include=[np.number])
            
            if numeric_data.shape[1] < MIN_NUMERIC_COLUMNS:
                self.logger.warning(
                    f"Only {numeric_data.shape[1]} numeric columns found, need at least {MIN_NUMERIC_COLUMNS}"
                )
                self._add_warning(
                    result,
                    f"Need at least {MIN_NUMERIC_COLUMNS} numeric columns for correlation analysis, "
                    f"found {numeric_data.shape[1]}"
                )
                result.data = {
                    "correlation_matrix": {},
                    "strong_correlations": [],
                    "columns": [],
                    "correlation_count": 0,
                    "threshold": threshold,
                }
                result.quality_score = 0.5
                result.success = True  # Not an error, just insufficient data
                return result
            
            # Compute correlation matrix
            corr_matrix = numeric_data.corr().round(4)
            
            # Find strong correlations
            strong_corrs = self._find_strong_correlations(corr_matrix, threshold)
            
            result.data = {
                "correlation_matrix": corr_matrix.to_dict(),
                "strong_correlations": strong_corrs,
                "columns": corr_matrix.columns.tolist(),
                "correlation_count": len(strong_corrs),
                "threshold": threshold,
                "numeric_columns_analyzed": numeric_data.shape[1],
            }
            
            result.quality_score = 1.0
            result.success = True
            
            self.logger.info(
                f"Analyzed {numeric_data.shape[1]} numeric columns, "
                f"found {len(strong_corrs)} strong correlations (threshold: {threshold})"
            )
            
            return result
        
        except Exception as e:
            """Catch unexpected exceptions.
            
            Should not happen if code is correct, but safety net ensures
            WorkerResult is always returned.
            """
            self.logger.error(f"CorrelationAnalyzer execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                details={
                    "error_type": type(e).__name__,
                    "shape": str(df.shape)
                },
                suggestion="Check that DataFrame has numeric columns without NaN issues"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
    
    def _find_strong_correlations(
        self,
        corr_matrix: pd.DataFrame,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Find strong correlations in the matrix.
        
        Args:
            corr_matrix: Correlation matrix from pandas
            threshold: Threshold for strong correlation (0-1)
            
        Returns:
            List of strong correlation dictionaries, sorted by strength
        """
        strong_corrs: List[Dict[str, Any]] = []
        
        # Iterate through upper triangle of correlation matrix
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                
                # Check if correlation exceeds threshold
                if abs(corr_val) > threshold:
                    strong_corrs.append({
                        "column_1": corr_matrix.columns[i],
                        "column_2": corr_matrix.columns[j],
                        "correlation": float(corr_val),
                        "strength": self._rate_correlation_strength(abs(corr_val)),
                        "direction": "positive" if corr_val > 0 else "negative",
                    })
        
        # Sort by absolute correlation value (strongest first)
        strong_corrs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return strong_corrs
    
    @staticmethod
    def _rate_correlation_strength(abs_corr: float) -> str:
        """Rate the strength of correlation.
        
        Args:
            abs_corr: Absolute correlation value (0-1)
            
        Returns:
            Strength rating string
            
        Ratings:
            very_strong: >= 0.9
            strong: 0.7 - 0.89
            moderate: 0.5 - 0.69
            weak: < 0.5
        """
        if abs_corr >= 0.9:
            return "very_strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        else:
            return "weak"
