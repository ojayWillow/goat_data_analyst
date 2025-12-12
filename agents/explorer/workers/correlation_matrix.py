"""CorrelationMatrix - Worker for computing correlation matrices.

Computes full correlation matrices using Pearson, Spearman, or Kendall methods.
"""

from typing import Any, Dict, Optional
import pandas as pd
import numpy as np

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_METHOD = 'pearson'  # Default correlation method
VALID_METHODS = ['pearson', 'spearman', 'kendall']  # Valid correlation methods
MIN_NUMERIC_COLUMNS = 2  # Minimum columns needed


class CorrelationMatrix(BaseWorker):
    """Worker that computes correlation matrices.
    
    Computes correlation matrices for all numeric columns using
    multiple correlation methods:
    - Pearson: Linear correlation (most common)
    - Spearman: Rank correlation (monotonic relationships)
    - Kendall: Rank correlation (rank pairs)
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame containing data (required)
        method: str - Correlation method (default: 'pearson')
    
    Output Format:
        result.data contains:
            method: Correlation method used
            correlation_matrix: Full correlation matrix as dict
            shape: Shape of matrix (n_cols, n_cols)
            columns: Column names used
            numeric_columns_count: Number of numeric columns
            correlations_computed: Total correlation pairs computed
    
    Quality Score:
        - 1.0: Successfully computed matrix
        - 0.5: Matrix computed but with warnings
        - 0.0: Failed or no numeric columns
    
    Correlation Methods:
        - Pearson: Measures linear association (-1 to 1)
        - Spearman: Rank-based, captures monotonic relationships
        - Kendall: Rank-based, tau coefficient
    
    Example:
        >>> matrix_worker = CorrelationMatrix()
        >>> result = matrix_worker.safe_execute(df=df, method='pearson')
        >>> if result.success:
        ...     corr_data = result.data['correlation_matrix']
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize CorrelationMatrix worker."""
        super().__init__("CorrelationMatrix")
        self.error_intelligence = ErrorIntelligence()
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters.
        
        Args:
            **kwargs: Must contain 'df' key with DataFrame value
            
        Returns:
            WorkerError if validation fails, None if valid
        """
        df = kwargs.get('df')
        method = kwargs.get('method', DEFAULT_METHOD)
        
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
        
        if df.empty:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="DataFrame is empty (0 rows)",
                severity="error",
                suggestion="Ensure DataFrame has data"
            )
        
        if method not in VALID_METHODS:
            return WorkerError(
                error_type=ErrorType.INVALID_PARAMETER,
                message=f"Invalid method '{method}', must be one of {VALID_METHODS}",
                severity="error",
                suggestion=f"Use method in: {VALID_METHODS}"
            )
        
        return None
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Compute correlation matrix.
        
        Args:
            df: DataFrame containing data
            method: Correlation method (default: 'pearson')
            
        Returns:
            WorkerResult with correlation matrix
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        df = kwargs.get('df')
        method = kwargs.get('method', DEFAULT_METHOD)
        
        result = self._create_result(task_type="correlation_matrix")
        
        try:
            self.logger.info(f"Computing correlation matrix using {method} method")
            
            # Select only numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "No numeric columns found in DataFrame",
                    severity="error",
                    details={"columns": list(df.columns)},
                    suggestion="DataFrame must contain at least one numeric column"
                )
                result.success = False
                result.quality_score = 0.0
                return result
            
            if numeric_df.shape[1] < MIN_NUMERIC_COLUMNS:
                self._add_warning(
                    result,
                    f"Only {numeric_df.shape[1]} numeric column(s) found, "
                    f"need at least {MIN_NUMERIC_COLUMNS} for meaningful correlations"
                )
            
            # Compute correlation matrix
            corr_matrix = numeric_df.corr(method=method).round(4)
            
            # Convert to dict for serialization
            corr_dict = corr_matrix.to_dict()
            
            # Calculate total number of correlations
            n_cols = corr_matrix.shape[0]
            total_correlations = (n_cols * (n_cols - 1)) // 2  # Upper triangle
            
            result.data = {
                "method": method,
                "correlation_matrix": corr_dict,
                "shape": corr_matrix.shape,
                "columns": numeric_df.columns.tolist(),
                "numeric_columns_count": numeric_df.shape[1],
                "correlations_computed": total_correlations,
                "matrix_size": n_cols,
            }
            
            result.success = True
            result.quality_score = 1.0 if numeric_df.shape[1] >= MIN_NUMERIC_COLUMNS else 0.5
            
            self.logger.info(
                f"Correlation matrix computed ({method} method): "
                f"{numeric_df.shape[1]} columns, {total_correlations} correlation pairs"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"CorrelationMatrix execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Correlation matrix computation failed: {str(e)}",
                severity="critical",
                suggestion="Check that numeric columns have valid data"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
