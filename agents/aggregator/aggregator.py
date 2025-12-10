"""Aggregator Agent - Orchestrator for data aggregation operations.

This agent ORCHESTRATES aggregation tasks by delegating to specialized workers:
- GroupBy operations → GroupByWorker
- Pivot operations → PivotWorker
- CrossTab operations → CrosstabWorker
- Rolling aggregations → RollingWorker
- Statistical summaries → StatisticsWorker
- Value counting → ValueCountWorker

Golden Rule: Manager = Thin orchestrator, Workers = Thick specialists
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError

# Import ALL workers - STEP 1 OF FIX
from agents.aggregator.workers import (
    GroupByWorker,
    PivotWorker,
    CrosstabWorker,
    RollingWorker,
    StatisticsWorker,
    ValueCountWorker,
)

logger = get_structured_logger(__name__)


class Aggregator:
    """Aggregator Manager: Thin orchestrator that delegates to workers.
    
    Pattern:
    1. User calls aggregator method
    2. Manager validates input
    3. Manager delegates to appropriate worker
    4. Worker executes and returns result
    5. Manager returns result to user
    """

    def __init__(self):
        """Initialize Aggregator with all worker instances."""
        self.name = "Aggregator"
        self.logger = get_logger("Aggregator")
        self.data = None
        
        # STEP 2 OF FIX: INITIALIZE ALL WORKERS
        self.groupby_worker = GroupByWorker()
        self.pivot_worker = PivotWorker()
        self.crosstab_worker = CrosstabWorker()
        self.rolling_worker = RollingWorker()
        self.statistics_worker = StatisticsWorker()
        self.value_count_worker = ValueCountWorker()
        
        logger.info(
            "Aggregator initialized with 6 workers",
            extra={
                "workers": 6,
                "worker_list": [
                    "GroupByWorker",
                    "PivotWorker",
                    "CrosstabWorker",
                    "RollingWorker",
                    "StatisticsWorker",
                    "ValueCountWorker",
                ]
            }
        )

    # ===== SECTION 1: Data Management =====

    def set_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Set data for aggregation operations."""
        try:
            if df is None or df.empty:
                return {
                    'status': 'error',
                    'message': 'Data is empty',
                    'data': None,
                    'metadata': {},
                    'errors': ['DataFrame is empty']
                }
            
            self.data = df.copy()
            logger.info(
                "Data set",
                extra={'rows': df.shape[0], 'columns': df.shape[1]}
            )
            
            return {
                'status': 'success',
                'message': f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns",
                'data': None,
                'metadata': {
                    'rows': df.shape[0],
                    'columns': df.shape[1],
                    'column_names': df.columns.tolist()
                },
                'errors': []
            }
        except Exception as e:
            logger.error("Failed to set data", extra={'error': str(e)})
            return {
                'status': 'error',
                'message': f"Failed to set data: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    def get_data(self) -> Optional[pd.DataFrame]:
        """Get currently loaded data."""
        return self.data

    # ===== SECTION 2: GroupBy Operations =====
    # Manager: Validate and delegate to GroupByWorker

    def groupby_single(self, group_col: str, agg_col: str, agg_func: str = "sum") -> Dict[str, Any]:
        """Group by single column and aggregate.
        
        Manager delegates to GroupByWorker.
        """
        # Manager: VALIDATE INPUT
        if self.data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data set. Use set_data() first.']
            }
        
        if group_col not in self.data.columns:
            return {
                'status': 'error',
                'message': f"Column '{group_col}' not found",
                'data': None,
                'metadata': {},
                'errors': [f"Column '{group_col}' not found"]
            }
        
        if agg_col not in self.data.columns:
            return {
                'status': 'error',
                'message': f"Column '{agg_col}' not found",
                'data': None,
                'metadata': {},
                'errors': [f"Column '{agg_col}' not found"]
            }
        
        # Manager: DELEGATE TO WORKER
        logger.info(
            "Delegating to GroupByWorker",
            extra={'group_col': group_col, 'agg_col': agg_col, 'agg_func': agg_func}
        )
        
        worker_result = self.groupby_worker.safe_execute(
            df=self.data,
            group_col=group_col,
            agg_col=agg_col,
            agg_func=agg_func
        )
        
        # Manager: CHECK RESULT
        if not worker_result.success:
            logger.error(
                "GroupByWorker failed",
                extra={'errors': [e['message'] for e in worker_result.errors]}
            )
            return {
                'status': 'error',
                'message': 'GroupBy operation failed',
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in worker_result.errors]
            }
        
        # Manager: RETURN RESULT
        return {
            'status': 'success',
            'message': f"Grouped by '{group_col}' into {len(worker_result.data)} groups",
            'data': worker_result.data,
            'metadata': {
                'groups': len(worker_result.data),
                'group_column': group_col,
                'aggregated_column': agg_col,
                'function': agg_func
            },
            'errors': []
        }

    def groupby_multiple(self, group_cols: List[str], agg_specs: Dict[str, str]) -> Dict[str, Any]:
        """Group by multiple columns with multiple aggregations.
        
        Manager delegates to GroupByWorker.
        """
        # Manager: VALIDATE INPUT
        if self.data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data set']
            }
        
        for col in group_cols:
            if col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Column '{col}' not found"]
                }
        
        for col in agg_specs.keys():
            if col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Column '{col}' not found"]
                }
        
        # Manager: DELEGATE TO WORKER
        logger.info(
            "Delegating to GroupByWorker (multiple)",
            extra={'group_cols': group_cols, 'agg_specs': agg_specs}
        )
        
        worker_result = self.groupby_worker.safe_execute(
            df=self.data,
            group_cols=group_cols,
            agg_specs=agg_specs
        )
        
        # Manager: CHECK AND RETURN
        if not worker_result.success:
            return {
                'status': 'error',
                'message': 'Multi-level GroupBy failed',
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in worker_result.errors]
            }
        
        return {
            'status': 'success',
            'message': f"Grouped into {len(worker_result.data)} groups",
            'data': worker_result.data,
            'metadata': {
                'groups': len(worker_result.data),
                'group_columns': group_cols,
                'aggregation_specs': agg_specs
            },
            'errors': []
        }

    # ===== SECTION 3: Pivot Operations =====
    # Manager: Validate and delegate to PivotWorker

    def pivot_table(self, index: str, columns: str, values: str, aggfunc: str = "sum") -> Dict[str, Any]:
        """Create pivot table.
        
        Manager delegates to PivotWorker.
        """
        # Manager: VALIDATE INPUT
        if self.data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data set']
            }
        
        for col in [index, columns, values]:
            if col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Column '{col}' not found"]
                }
        
        # Manager: DELEGATE TO WORKER
        logger.info(
            "Delegating to PivotWorker",
            extra={'index': index, 'columns': columns, 'values': values}
        )
        
        worker_result = self.pivot_worker.safe_execute(
            df=self.data,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc
        )
        
        # Manager: CHECK AND RETURN
        if not worker_result.success:
            return {
                'status': 'error',
                'message': 'Pivot table creation failed',
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in worker_result.errors]
            }
        
        return {
            'status': 'success',
            'message': f"Pivot table created: {worker_result.metadata['shape']}",
            'data': worker_result.data,
            'metadata': worker_result.metadata,
            'errors': []
        }

    # ===== SECTION 4: CrossTab Operations =====
    # Manager: Validate and delegate to CrosstabWorker

    def crosstab(self, row_col: str, col_col: str, values: Optional[str] = None, aggfunc: str = "count") -> Dict[str, Any]:
        """Create cross-tabulation.
        
        Manager delegates to CrosstabWorker.
        """
        # Manager: VALIDATE INPUT
        if self.data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data set']
            }
        
        for col in [row_col, col_col]:
            if col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Column '{col}' not found"]
                }
        
        if values and values not in self.data.columns:
            return {
                'status': 'error',
                'message': f"Column '{values}' not found",
                'data': None,
                'metadata': {},
                'errors': [f"Column '{values}' not found"]
            }
        
        # Manager: DELEGATE TO WORKER
        logger.info(
            "Delegating to CrosstabWorker",
            extra={'row_col': row_col, 'col_col': col_col, 'values': values}
        )
        
        worker_result = self.crosstab_worker.safe_execute(
            df=self.data,
            row_col=row_col,
            col_col=col_col,
            values=values,
            aggfunc=aggfunc
        )
        
        # Manager: CHECK AND RETURN
        if not worker_result.success:
            return {
                'status': 'error',
                'message': 'Crosstab creation failed',
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in worker_result.errors]
            }
        
        return {
            'status': 'success',
            'message': f"Crosstab created: {worker_result.metadata['shape']}",
            'data': worker_result.data,
            'metadata': worker_result.metadata,
            'errors': []
        }

    # ===== SECTION 5: Rolling Operations =====
    # Manager: Validate and delegate to RollingWorker

    def rolling_aggregation(self, col: str, window: int, aggfunc: str = "mean") -> Dict[str, Any]:
        """Apply rolling aggregation.
        
        Manager delegates to RollingWorker.
        """
        # Manager: VALIDATE INPUT
        if self.data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data set']
            }
        
        if col not in self.data.columns:
            return {
                'status': 'error',
                'message': f"Column '{col}' not found",
                'data': None,
                'metadata': {},
                'errors': [f"Column '{col}' not found"]
            }
        
        # Manager: DELEGATE TO WORKER
        logger.info(
            "Delegating to RollingWorker",
            extra={'col': col, 'window': window, 'aggfunc': aggfunc}
        )
        
        worker_result = self.rolling_worker.safe_execute(
            df=self.data,
            col=col,
            window=window,
            aggfunc=aggfunc
        )
        
        # Manager: CHECK AND RETURN
        if not worker_result.success:
            return {
                'status': 'error',
                'message': 'Rolling aggregation failed',
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in worker_result.errors]
            }
        
        return {
            'status': 'success',
            'message': f"Rolling aggregation applied",
            'data': worker_result.data,
            'metadata': worker_result.metadata,
            'errors': []
        }

    # ===== SECTION 6: Statistical Operations =====
    # Manager: Validate and delegate to StatisticsWorker

    def summary_statistics(self, group_col: str) -> Dict[str, Any]:
        """Get comprehensive summary statistics.
        
        Manager delegates to StatisticsWorker.
        """
        # Manager: VALIDATE INPUT
        if self.data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data set']
            }
        
        if group_col not in self.data.columns:
            return {
                'status': 'error',
                'message': f"Column '{group_col}' not found",
                'data': None,
                'metadata': {},
                'errors': [f"Column '{group_col}' not found"]
            }
        
        # Manager: DELEGATE TO WORKER
        logger.info(
            "Delegating to StatisticsWorker",
            extra={'group_col': group_col}
        )
        
        worker_result = self.statistics_worker.safe_execute(
            df=self.data,
            group_col=group_col
        )
        
        # Manager: CHECK AND RETURN
        if not worker_result.success:
            return {
                'status': 'error',
                'message': 'Summary statistics failed',
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in worker_result.errors]
            }
        
        return {
            'status': 'success',
            'message': f"Summary statistics computed",
            'data': worker_result.data,
            'metadata': worker_result.metadata,
            'errors': []
        }

    # ===== SECTION 7: Value Counting =====
    # Manager: Validate and delegate to ValueCountWorker

    def value_counts(self, col: str, top_n: int = 10) -> Dict[str, Any]:
        """Get value counts for a column.
        
        Manager delegates to ValueCountWorker.
        """
        # Manager: VALIDATE INPUT
        if self.data is None:
            return {
                'status': 'error',
                'message': 'No data loaded',
                'data': None,
                'metadata': {},
                'errors': ['No data set']
            }
        
        if col not in self.data.columns:
            return {
                'status': 'error',
                'message': f"Column '{col}' not found",
                'data': None,
                'metadata': {},
                'errors': [f"Column '{col}' not found"]
            }
        
        # Manager: DELEGATE TO WORKER
        logger.info(
            "Delegating to ValueCountWorker",
            extra={'col': col, 'top_n': top_n}
        )
        
        worker_result = self.value_count_worker.safe_execute(
            df=self.data,
            col=col,
            top_n=top_n
        )
        
        # Manager: CHECK AND RETURN
        if not worker_result.success:
            return {
                'status': 'error',
                'message': 'Value counts failed',
                'data': None,
                'metadata': {},
                'errors': [e['message'] for e in worker_result.errors]
            }
        
        return {
            'status': 'success',
            'message': f"Value counts computed",
            'data': worker_result.data,
            'metadata': worker_result.metadata,
            'errors': []
        }

    # ===== SECTION 8: Utilities =====

    def get_summary(self) -> str:
        """Get human-readable summary."""
        if self.data is None:
            return "Aggregator: No data loaded"
        
        return (
            f"Aggregator Summary:\n"
            f"  Data: {self.data.shape[0]} rows x {self.data.shape[1]} columns\n"
            f"  Columns: {', '.join(self.data.columns[:5])}{'...' if len(self.data.columns) > 5 else ''}\n"
            f"  Numeric: {len(self.data.select_dtypes(include=[np.number]).columns)}\n"
            f"  Categorical: {len(self.data.select_dtypes(include=['object']).columns)}"
        )
