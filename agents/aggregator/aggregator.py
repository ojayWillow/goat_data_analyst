"""Aggregator Agent - Coordinates data aggregation and time series operations.

Aggregates and transforms data using 4 specialized workers:
- WindowFunction: Rolling window operations
- RollingAggregation: Multi-column rolling aggregations
- ExponentialWeighted: EWMA calculations
- LagLeadFunction: Time series lag/lead shifts

Week 1 Day 4 - NEW AGENT IMPLEMENTATION:
- Agent coordinates all workers (doesn't implement logic)
- Each worker extends BaseWorker for standardization
- Methods delegate to workers
- Pure coordinator pattern consistent with DataLoader, Explorer, AnomalyDetector

Integrated with Week 1 Systems:
- Structured logging with metrics
- Automatic retry with exponential backoff
- Error recovery and handling
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from .workers import (
    WindowFunction,
    RollingAggregation,
    ExponentialWeighted,
    LagLeadFunction,
    WorkerResult,
)

logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)


class Aggregator:
    """Aggregator Agent - coordinates data aggregation workers.
    
    Manages 4 workers:
    - WindowFunction: Rolling window operations
    - RollingAggregation: Multi-column rolling aggregations
    - ExponentialWeighted: EWMA calculations
    - LagLeadFunction: Time series lag/lead shifts
    
    Week 1 Day 4 Implementation:
    - Agent coordinates all workers (doesn't implement)
    - Each worker extends BaseWorker
    - Methods delegate to workers
    - Pure coordinator pattern
    """

    def __init__(self) -> None:
        """Initialize the Aggregator agent and all workers."""
        self.name = "Aggregator"
        self.logger = get_logger("Aggregator")
        self.structured_logger = get_structured_logger("Aggregator")
        self.data: Optional[pd.DataFrame] = None
        self.aggregation_results: Dict[str, WorkerResult] = {}

        # === INITIALIZE ALL WORKERS ===
        self.window_function = WindowFunction()
        self.rolling_aggregation = RollingAggregation()
        self.exponential_weighted = ExponentialWeighted()
        self.lag_lead_function = LagLeadFunction()

        self.workers = [
            self.window_function,
            self.rolling_aggregation,
            self.exponential_weighted,
            self.lag_lead_function,
        ]

        self.logger.info("Aggregator initialized with 4 aggregation workers")
        self.structured_logger.info("Aggregator initialized", {
            "workers": 4,
            "worker_names": [
                "WindowFunction",
                "RollingAggregation",
                "ExponentialWeighted",
                "LagLeadFunction"
            ]
        })

    # === DATA MANAGEMENT ===

    def set_data(self, df: pd.DataFrame) -> None:
        """Store the DataFrame for aggregation operations.
        
        Args:
            df: DataFrame to process
        """
        self.data = df.copy()
        self.aggregation_results = {}
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
        self.structured_logger.info("Data set for aggregation", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "numeric_cols": len(df.select_dtypes(include=['number']).columns)
        })

    def get_data(self) -> Optional[pd.DataFrame]:
        """Retrieve the stored DataFrame.
        
        Returns:
            DataFrame or None if not set
        """
        return self.data

    # === AGGREGATION METHODS - DELEGATE TO WORKERS ===

    @retry_on_error(max_attempts=3, backoff=2)
    def apply_window_function(
        self,
        window_size: int = 3,
        operations: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Apply rolling window functions.
        
        Args:
            window_size: Size of rolling window
            operations: List of operations ('mean', 'sum', 'std', 'min', 'max')
            
        Returns:
            Window function result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Window function started", {
            "window_size": window_size,
            "operations": operations
        })

        try:
            if operations is None:
                operations = ['mean']
                
            worker_result = self.window_function.safe_execute(
                df=self.data,
                window_size=window_size,
                operations=operations,
            )

            self.aggregation_results["window_function"] = worker_result
            self.structured_logger.info("Window function completed", {"success": worker_result.success})
            
            return worker_result.to_dict()
        except Exception as e:
            self.structured_logger.error("Window function failed", {"error": str(e)})
            raise

    @retry_on_error(max_attempts=3, backoff=2)
    def apply_rolling_aggregation(
        self,
        window_size: int = 5,
        columns: Optional[List[str]] = None,
        agg_dict: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Apply multi-column rolling aggregations.
        
        Args:
            window_size: Size of rolling window
            columns: Columns to aggregate (None = all numeric)
            agg_dict: Dict mapping columns to operations
            
        Returns:
            Rolling aggregation result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Rolling aggregation started", {"window_size": window_size})

        try:
            worker_result = self.rolling_aggregation.safe_execute(
                df=self.data,
                window_size=window_size,
                columns=columns,
                agg_dict=agg_dict,
            )

            self.aggregation_results["rolling_aggregation"] = worker_result
            self.structured_logger.info("Rolling aggregation completed", {"success": worker_result.success})
            
            return worker_result.to_dict()
        except Exception as e:
            self.structured_logger.error("Rolling aggregation failed", {"error": str(e)})
            raise

    @retry_on_error(max_attempts=3, backoff=2)
    def apply_exponential_weighted(
        self,
        span: int = 10,
        adjust: bool = True,
    ) -> Dict[str, Any]:
        """Apply exponential weighted moving average.
        
        Args:
            span: Span for exponential weighting
            adjust: Whether to apply exponential scaling
            
        Returns:
            EWMA result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Exponential weighted started", {
            "span": span,
            "adjust": adjust
        })

        try:
            worker_result = self.exponential_weighted.safe_execute(
                df=self.data,
                span=span,
                adjust=adjust,
            )

            self.aggregation_results["exponential_weighted"] = worker_result
            self.structured_logger.info("Exponential weighted completed", {"success": worker_result.success})
            
            return worker_result.to_dict()
        except Exception as e:
            self.structured_logger.error("Exponential weighted failed", {"error": str(e)})
            raise

    @retry_on_error(max_attempts=3, backoff=2)
    def apply_lag_lead_function(
        self,
        lag_periods: int = 1,
        lead_periods: int = 0,
        columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Apply lag and lead time shifts.
        
        Args:
            lag_periods: Number of periods to lag
            lead_periods: Number of periods to lead
            columns: Columns to apply lag/lead (None = all numeric)
            
        Returns:
            Lag/lead function result as dictionary
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Lag/Lead function started", {
            "lag_periods": lag_periods,
            "lead_periods": lead_periods
        })

        try:
            worker_result = self.lag_lead_function.safe_execute(
                df=self.data,
                lag_periods=lag_periods,
                lead_periods=lead_periods,
                columns=columns,
            )

            self.aggregation_results["lag_lead_function"] = worker_result
            self.structured_logger.info("Lag/Lead function completed", {"success": worker_result.success})
            
            return worker_result.to_dict()
        except Exception as e:
            self.structured_logger.error("Lag/Lead function failed", {"error": str(e)})
            raise

    # === BATCH AGGREGATION ===

    @retry_on_error(max_attempts=3, backoff=2)
    def aggregate_all(
        self,
        window_params: Optional[Dict[str, Any]] = None,
        rolling_params: Optional[Dict[str, Any]] = None,
        ewma_params: Optional[Dict[str, Any]] = None,
        lag_lead_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run all 4 aggregation methods.
        
        Args:
            window_params: Parameters for window function
            rolling_params: Parameters for rolling aggregation
            ewma_params: Parameters for exponential weighted
            lag_lead_params: Parameters for lag/lead
            
        Returns:
            Dictionary with all aggregation results
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")

        self.structured_logger.info("Comprehensive aggregation started")

        results = {}

        # Default parameters
        window_params = window_params or {}
        rolling_params = rolling_params or {}
        ewma_params = ewma_params or {}
        lag_lead_params = lag_lead_params or {}

        # Run all aggregations
        try:
            results["window_function"] = self.apply_window_function(**window_params)
        except Exception as e:
            self.logger.warning(f"Window function failed: {e}")

        try:
            results["rolling_aggregation"] = self.apply_rolling_aggregation(**rolling_params)
        except Exception as e:
            self.logger.warning(f"Rolling aggregation failed: {e}")

        try:
            results["exponential_weighted"] = self.apply_exponential_weighted(**ewma_params)
        except Exception as e:
            self.logger.warning(f"Exponential weighted failed: {e}")

        try:
            results["lag_lead_function"] = self.apply_lag_lead_function(**lag_lead_params)
        except Exception as e:
            self.logger.warning(f"Lag/Lead function failed: {e}")

        self.structured_logger.info("Comprehensive aggregation completed", {
            "methods": len(results)
        })

        return results

    # === REPORTING ===

    def summary_report(self) -> Dict[str, Any]:
        """Get summary of all aggregations performed.
        
        Returns:
            Dictionary with aggregation summary
        """
        successful_aggregations = [
            k for k, v in self.aggregation_results.items() if v.success
        ]
        failed_aggregations = [
            k for k, v in self.aggregation_results.items() if not v.success
        ]

        report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_aggregations": len(self.aggregation_results),
            "successful": len(successful_aggregations),
            "failed": len(failed_aggregations),
            "successful_methods": successful_aggregations,
            "failed_methods": failed_aggregations,
            "results": {
                k: v.to_dict() for k, v in self.aggregation_results.items()
            },
        }
        
        self.structured_logger.info("Summary report generated", {
            "total_aggregations": report["total_aggregations"],
            "successful": report["successful"],
            "failed": report["failed"]
        })

        return report

    def get_summary(self) -> str:
        """Get human-readable info about the agent state.
        
        Returns:
            Summary string
        """
        if self.data is None:
            return "Aggregator: no data loaded"

        return (
            f"Aggregator Summary:\n"
            f"  Rows: {self.data.shape[0]}\n"
            f"  Columns: {self.data.shape[1]}\n"
            f"  Workers: {len(self.workers)}\n"
            f"  Aggregations run: {len(self.aggregation_results)}\n"
            f"  Successful: {sum(1 for v in self.aggregation_results.values() if v.success)}"
        )
