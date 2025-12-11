"""GroupBy Worker - Handles grouping and aggregation operations.

Performs single and multiple column grouping with various aggregation functions.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class GroupByWorker(BaseWorker):
    """Worker that performs groupby operations."""
    
    def __init__(self):
        super().__init__("GroupByWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Perform groupby operation.
        
        Args:
            df: DataFrame to group
            group_cols: Column(s) to group by (str or list)
            agg_specs: Aggregation specs (str or dict)
            
        Returns:
            WorkerResult with grouped data
        """
        try:
            result = self._perform_groupby(**kwargs)
            
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="GroupByWorker",
                error_type="SUCCESS",
                error_message="GroupBy operation successful",
                context={"operation": "groupby_aggregation"}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="aggregator",
                worker_name="GroupByWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "operation": "groupby_aggregation",
                    "group_cols": kwargs.get('group_cols'),
                }
            )
            raise
    
    def _perform_groupby(self, **kwargs) -> WorkerResult:
        """Perform groupby aggregation."""
        df = kwargs.get('df')
        group_cols = kwargs.get('group_cols')
        agg_specs = kwargs.get('agg_specs')
        
        result = self._create_result(
            task_type="groupby_aggregation",
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
            self.logger.info(f"Performing groupby operation...")
            
            if isinstance(group_cols, str):
                group_cols = [group_cols]
            
            missing_cols = [col for col in group_cols if col not in df.columns]
            if missing_cols:
                self._add_error(
                    result,
                    ErrorType.VALUE_ERROR,
                    f"Group columns not found: {missing_cols}",
                    severity="error",
                    suggestion=f"Available columns: {df.columns.tolist()}"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            grouped = df.groupby(group_cols)
            
            if isinstance(agg_specs, str):
                aggregated = grouped.agg(agg_specs).reset_index()
            elif isinstance(agg_specs, dict):
                missing_agg_cols = [col for col in agg_specs.keys() if col not in df.columns]
                if missing_agg_cols:
                    self._add_error(
                        result,
                        ErrorType.VALUE_ERROR,
                        f"Aggregation columns not found: {missing_agg_cols}",
                        severity="error"
                    )
                    result.success = False
                    result.quality_score = 0
                    return result
                
                aggregated = grouped.agg(agg_specs).reset_index()
            else:
                self._add_error(
                    result,
                    ErrorType.INVALID_PARAMETER,
                    "agg_specs must be string or dict",
                    severity="error"
                )
                result.success = False
                result.quality_score = 0
                return result
            
            result.data = {
                "grouped_data": aggregated.to_dict(orient='records'),
                "groups_count": len(aggregated),
                "group_columns": group_cols,
                "aggregation_specs": agg_specs,
            }
            
            self.logger.info(f"Grouped into {len(aggregated)} groups")
            return result
        
        except Exception as e:
            self.logger.error(f"GroupBy failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                suggestion="Check column names and aggregation functions"
            )
            result.success = False
            result.quality_score = 0
            return result
