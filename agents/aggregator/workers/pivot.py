"""Pivot Worker - Handles pivot table creation.

Reshapes data into pivot tables for cross-tabular analysis with full validation
and quality scoring per A+ worker guidance.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union

from .base_worker import BaseWorker, WorkerResult, ErrorType, WorkerError
from .validation_utils import ValidationUtils
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# ===== CONSTANTS =====
VALID_AGGFUNCS = ['sum', 'mean', 'count', 'min', 'max', 'median', 'std']
DEFAULT_AGGFUNC = 'sum'
QUALITY_SCORE_DUPLICATES = 0.7  # Reduced if duplicates found and handled


class PivotWorker(BaseWorker):
    """Worker that creates pivot tables.
    
    Creates pivot tables for cross-tabular analysis with:
    - Flexible index/column/value specifications
    - Multiple aggregation functions
    - Duplicate detection and handling
    - Null value awareness
    - Quality scoring
    """
    
    def __init__(self) -> None:
        """Initialize PivotWorker."""
        super().__init__("PivotWorker")
        self.error_intelligence = ErrorIntelligence()
        self.rows_processed: int = 0
        self.rows_failed: int = 0
        self.duplicates_found: int = 0
    
    def _validate_input(self, **kwargs) -> Optional[WorkerError]:
        """Validate input parameters before execution.
        
        Validates:
        - DataFrame is provided and valid
        - index, columns, values are provided
        - All required columns exist
        - aggfunc is valid
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        # Check DataFrame
        df = kwargs.get('df')
        df_error = ValidationUtils.validate_dataframe(df)
        if df_error:
            return df_error
        
        # Check required parameters
        index = kwargs.get('index')
        columns = kwargs.get('columns')
        values = kwargs.get('values')
        
        if not index:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "index parameter is required",
                severity="error",
                suggestion="Provide index parameter (str)"
            )
        
        if not columns:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "columns parameter is required",
                severity="error",
                suggestion="Provide columns parameter (str)"
            )
        
        if not values:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                "values parameter is required",
                severity="error",
                suggestion="Provide values parameter (str)"
            )
        
        # Check columns exist
        required_cols = []
        for param in [index, columns, values]:
            if isinstance(param, str):
                required_cols.append(param)
            elif isinstance(param, list):
                required_cols.extend(param)
            else:
                return WorkerError(
                    ErrorType.TYPE_ERROR,
                    f"Parameters must be str or list[str], got {type(param).__name__}",
                    severity="error",
                    suggestion="Use string or list of strings for index, columns, values"
                )
        
        col_error = ValidationUtils.validate_columns_exist(
            df, required_cols, "pivot columns"
        )
        if col_error:
            return col_error
        
        # Check aggfunc is valid
        aggfunc = kwargs.get('aggfunc', DEFAULT_AGGFUNC)
        if aggfunc not in VALID_AGGFUNCS:
            return WorkerError(
                ErrorType.INVALID_PARAMETER,
                f"Invalid aggfunc: {aggfunc}",
                severity="error",
                details={"valid_aggfuncs": VALID_AGGFUNCS},
                suggestion=f"Use one of: {', '.join(VALID_AGGFUNCS)}"
            )
        
        return None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Create pivot table.
        
        Args:
            df: DataFrame to pivot
            index: Column(s) for rows (str or list[str])
            columns: Column(s) for columns (str or list[str])
            values: Column to aggregate (str)
            aggfunc: Aggregation function (default: 'sum')
            
        Returns:
            WorkerResult with pivot table
            
        Raises:
            Exception: Caught and handled by safe_execute wrapper
        """
        try:
            result = self._run_pivot(**kwargs)
            
            # Track success with error intelligence
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="PivotWorker",
                operation="pivot_table",
                context={
                    "index": str(kwargs.get('index')),
                    "columns": str(kwargs.get('columns')),
                    "success": result.success,
                    "quality_score": result.quality_score
                }
            )
            
            return result
            
        except Exception as e:
            # Track error with error intelligence
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="PivotWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "index": str(kwargs.get('index')),
                    "columns": str(kwargs.get('columns')),
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed
                }
            )
            raise
    
    def _run_pivot(self, **kwargs) -> WorkerResult:
        """Perform pivot table operation.
        
        Returns:
            WorkerResult with pivot table or errors
        """
        df = kwargs.get('df')
        index = kwargs.get('index')
        columns = kwargs.get('columns')
        values = kwargs.get('values')
        aggfunc = kwargs.get('aggfunc', DEFAULT_AGGFUNC)
        
        # Reset counters
        self.rows_processed = len(df) if df is not None else 0
        self.rows_failed = 0
        self.duplicates_found = 0
        
        result = self._create_result(
            task_type="pivot_table",
            quality_score=1.0
        )
        
        self.logger.info(
            f"Creating pivot table: index={index}, columns={columns}, values={values}, aggfunc={aggfunc}"
        )
        
        try:
            # Check for null values in pivot columns
            pivot_cols = []
            for param in [index, columns, values]:
                if isinstance(param, str):
                    pivot_cols.append(param)
                elif isinstance(param, list):
                    pivot_cols.extend(param)
            
            null_count = df[pivot_cols].isnull().sum().sum()
            if null_count > 0:
                self._add_warning(
                    result,
                    f"Found {null_count} null values in pivot columns. "
                    f"They will be excluded from the pivot operation."
                )
            
            # Check for duplicate key combinations
            key_cols = []
            if isinstance(index, str):
                key_cols.append(index)
            elif isinstance(index, list):
                key_cols.extend(index)
            
            if isinstance(columns, str):
                key_cols.append(columns)
            elif isinstance(columns, list):
                key_cols.extend(columns)
            
            key_combination = df[key_cols].dropna()
            duplicates = key_combination.duplicated().sum()
            self.duplicates_found = duplicates
            
            if duplicates > 0:
                self._add_warning(
                    result,
                    f"Found {duplicates} duplicate (index, column) key combinations. "
                    f"Using aggfunc='{aggfunc}' to combine duplicate values."
                )
                if aggfunc == 'sum':
                    # Reduce quality score slightly for duplicates
                    quality_reduction = min(0.15, duplicates * 0.01)
                else:
                    quality_reduction = min(0.1, duplicates * 0.005)
            else:
                quality_reduction = 0
            
            # Create pivot table
            pivot = pd.pivot_table(
                df,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            )
            
            # Handle case where pivot returns Series instead of DataFrame
            if isinstance(pivot, pd.Series):
                pivot = pivot.to_frame().reset_index()
            else:
                pivot = pivot.reset_index()
            
            if pivot.empty:
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    "Pivot table resulted in empty DataFrame",
                    severity="error",
                    suggestion="Check that values exist in all index-column combinations"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            # Build result data
            result.data = {
                "pivot_data": pivot.to_dict(orient='records'),
                "shape": list(pivot.shape),
                "rows": pivot.shape[0],
                "columns": pivot.shape[1],
                "index_column": str(index),
                "column_field": str(columns),
                "values_column": values,
                "aggregation_function": aggfunc,
                "null_values_found": int(null_count),
                "duplicate_combinations": duplicates,
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                rows_processed=self.rows_processed,
                rows_failed=self.rows_failed,
                duplicates_found=duplicates,
                quality_reduction=quality_reduction
            )
            result.quality_score = quality_score
            result.success = True
            
            self.logger.info(
                f"Pivot table created: {pivot.shape[0]} rows x {pivot.shape[1]} columns, "
                f"quality score: {quality_score:.3f}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Pivot table creation failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                details={
                    "exception_type": type(e).__name__,
                    "rows_processed": self.rows_processed,
                    "rows_failed": self.rows_failed,
                    "duplicates_found": self.duplicates_found
                },
                suggestion="Check column names and aggregation function validity"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        duplicates_found: int = 0,
        quality_reduction: float = 0.0
    ) -> float:
        """Calculate quality score based on data quality metrics.
        
        Args:
            rows_processed: Rows successfully processed
            rows_failed: Rows that failed processing
            duplicates_found: Number of duplicate key combinations
            quality_reduction: Penalty for duplicates
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        # Base quality from successful processing
        total_rows = rows_processed + rows_failed
        
        if total_rows == 0:
            base_quality = 1.0
        else:
            base_quality = rows_processed / total_rows
        
        # Apply reduction
        quality_score = max(0.0, base_quality - quality_reduction)
        
        return min(1.0, quality_score)
