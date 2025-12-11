"""CrossTab Worker - Handles cross-tabulation operations.

Creates cross-tabulations for categorical data analysis.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class CrossTabWorker(BaseWorker):
    """Worker that creates cross-tabulations."""
    
    def __init__(self):
        super().__init__("CrossTabWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Create cross-tabulation.
        
        Args:
            df: DataFrame to analyze
            rows: Column for rows
            columns: Column for columns
            values: Column to aggregate (optional)
            aggfunc: Aggregation function (default: 'count')
            
        Returns:
            WorkerResult with cross-tabulation
        """
        try:
            result = self._create_crosstab(**kwargs)
            
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="CrossTabWorker",
                error_type="SUCCESS",
                error_message="Crosstab created successfully",
                context={"operation": "crosstab"}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="CrossTabWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "operation": "crosstab",
                    "rows": kwargs.get('rows'),
                    "columns": kwargs.get('columns'),
                }
            )
            raise
    
    def _create_crosstab(self, **kwargs) -> WorkerResult:
        """Perform cross-tabulation operation."""
        df = kwargs.get('df')
        rows = kwargs.get('rows')
        columns = kwargs.get('columns')
        values = kwargs.get('values')
        aggfunc = kwargs.get('aggfunc', 'count')
        
        result = self._create_result(
            task_type="crosstab",
            quality_score=1.0
        )
        
        if df is None or df.empty:
            self._add_error(
                result,
                ErrorType.MISSING_DATA,
                "No data provided or data is empty",
                severity="error",
                suggestion="Ensure DataFrame is not None or empty"
            )
            result.success = False
            result.quality_score = 0
            return result
        
        try:
            self.logger.info(f"Creating crosstab: rows={rows}, columns={columns}")
            
            if not rows or not columns:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "rows and columns are required",
                    severity="error",
                    suggestion="Provide both rows and columns"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            required_cols = [rows, columns]
            if values:
                required_cols.append(values)
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self._add_error(
                    result,
                    ErrorType.VALUE_ERROR,
                    f"Columns not found: {missing_cols}",
                    severity="error",
                    suggestion=f"Available columns: {df.columns.tolist()}"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            if values:
                ct = pd.crosstab(
                    df[rows],
                    df[columns],
                    values=df[values],
                    aggfunc=aggfunc
                )
            else:
                ct = pd.crosstab(
                    df[rows],
                    df[columns]
                )
            
            ct = ct.reset_index()
            
            result.data = {
                "crosstab_data": ct.to_dict(orient='records'),
                "shape": ct.shape,
                "rows": ct.shape[0],
                "columns": ct.shape[1],
                "row_field": rows,
                "column_field": columns,
                "values_field": values,
                "aggfunc": aggfunc,
            }
            
            self.logger.info(f"Crosstab created: {ct.shape[0]} rows x {ct.shape[1]} columns")
            return result
        
        except Exception as e:
            self.logger.error(f"Crosstab creation failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                suggestion="Check column names and aggregation function"
            )
            result.success = False
            result.quality_score = 0
            return result
