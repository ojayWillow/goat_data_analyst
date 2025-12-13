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
            result = self._run_crosstab(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="aggregator",
                worker_name="CrossTabWorker",
                operation="crosstab",
                context={"rows": kwargs.get('rows'), "columns": kwargs.get('columns')}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="CrossTabWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"rows": kwargs.get('rows'), "columns": kwargs.get('columns')}
            )
            raise
    
    def _run_crosstab(self, **kwargs) -> WorkerResult:
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
            
            crosstab_data: List[Dict[str, Any]] = ct.to_dict(orient='records')
            
            if crosstab_data:
                result.data = {
                    "crosstab_data": crosstab_data,
                    "shape": ct.shape,
                    "rows": ct.shape[0],
                    "columns": ct.shape[1],
                    "row_field": rows,
                    "column_field": columns,
                    "values_field": values,
                    "aggfunc": aggfunc,
                }
            else:
                self._add_error(
                    result,
                    ErrorType.MISSING_DATA,
                    "Cross-tabulation produced no data",
                    severity="error",
                    suggestion="Check input data and parameters"
                )
                result.success = False
                result.quality_score = 0
                return result
            
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
