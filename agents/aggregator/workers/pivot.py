"""Pivot Worker - Handles pivot table creation.

Reshapes data into pivot tables for cross-tabular analysis.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class PivotWorker(BaseWorker):
    """Worker that creates pivot tables."""
    
    def __init__(self):
        super().__init__("PivotWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Create pivot table.
        
        Args:
            df: DataFrame to pivot
            index: Column(s) for rows
            columns: Column(s) for columns
            values: Column to aggregate
            aggfunc: Aggregation function (default: 'sum')
            
        Returns:
            WorkerResult with pivot table
        """
        try:
            result = self._create_pivot(**kwargs)
            
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="PivotWorker",
                error_type="SUCCESS",
                error_message="Pivot table created successfully",
                context={"operation": "pivot_table"}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="PivotWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "operation": "pivot_table",
                    "index": kwargs.get('index'),
                    "columns": kwargs.get('columns'),
                }
            )
            raise
    
    def _create_pivot(self, **kwargs) -> WorkerResult:
        """Perform pivot table operation."""
        df = kwargs.get('df')
        index = kwargs.get('index')
        columns = kwargs.get('columns')
        values = kwargs.get('values')
        aggfunc = kwargs.get('aggfunc', 'sum')
        
        result = self._create_result(
            task_type="pivot_table",
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
            self.logger.info(f"Creating pivot table: index={index}, columns={columns}, values={values}")
            
            if not index or not columns or not values:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "index, columns, and values are required",
                    severity="error",
                    suggestion="Provide all three parameters"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            required_cols = [index, columns, values]
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
            
            pivot = pd.pivot_table(
                df,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            ).reset_index()
            
            result.data = {
                "pivot_data": pivot.to_dict(orient='records'),
                "shape": pivot.shape,
                "rows": pivot.shape[0],
                "columns": pivot.shape[1],
                "index": index,
                "columns_field": columns,
                "values": values,
                "aggfunc": aggfunc,
            }
            
            self.logger.info(f"Pivot table created: {pivot.shape[0]} rows x {pivot.shape[1]} columns")
            return result
        
        except Exception as e:
            self.logger.error(f"Pivot table creation failed: {e}")
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
