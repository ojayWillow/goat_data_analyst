"""Visualizer Agent - Coordinates chart creation workers with A+ standards.

Creates interactive and static charts using a plugin architecture with:
- Comprehensive error intelligence tracking
- Health score reporting
- Resilience and retry logic
- Data quality metrics
- Structured logging

Features:
- Easy to extend with new chart types
- Automatic error recovery
- Health monitoring
- Quality score tracking

Integrated with:
- Error Intelligence System
- Structured Logging
- Automatic Retry with Exponential Backoff
"""

from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
import pandas as pd
import logging
import time

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from agents.error_intelligence.main import ErrorIntelligence
from .workers import (
    LineChartWorker,
    BarChartWorker,
    ScatterPlotWorker,
    HistogramWorker,
    BoxPlotWorker,
    HeatmapWorker,
    PieChartWorker,
    WorkerResult,
)

# ===== CONSTANTS =====
MAX_CHARTS_CACHED: int = 100
HEALTH_SCORE_THRESHOLD: float = 0.85

logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)


class Visualizer:
    """Visualizer Agent - Coordinates chart creation with A+ standards.
    
    Supports 7 chart types:
    - Line charts (time series, trends)
    - Bar charts (categorical comparison)
    - Scatter plots (correlations, relationships)
    - Histograms (distributions)
    - Box plots (quartiles, outliers)
    - Heatmaps (correlations)
    - Pie charts (composition)
    
    PLUGIN SYSTEM: Easy to add new chart types!
    
    Features:
    - Comprehensive input validation
    - Error intelligence integration
    - Health score tracking
    - Quality metrics
    - Automatic retry with exponential backoff
    - Structured logging with metrics
    
    Example:
        >>> visualizer = Visualizer()
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=100),
        ...     'sales': range(100)
        ... })
        >>> visualizer.set_data(df)
        >>> result = visualizer.line_chart('date', 'sales')
        >>> health = visualizer.get_health_report()
        >>> print(f"Health: {health['overall_health']:.1f}%")
    """

    def __init__(self) -> None:
        """Initialize Visualizer agent and all workers."""
        self.name = "Visualizer"
        self.version = "2.0.0"
        self.logger = get_logger("Visualizer")
        self.structured_logger = get_structured_logger("Visualizer")
        self.error_intelligence = ErrorIntelligence()
        
        # Data management
        self.data: Optional[pd.DataFrame] = None
        self.data_metadata: Dict[str, Any] = {}
        self.charts: Dict[str, Any] = {}
        
        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        self.errors_encountered: List[Dict[str, Any]] = []
        self.total_charts_created: int = 0
        self.start_time: float = time.time()

        # === INITIALIZE ALL WORKERS ===
        self.line_worker = LineChartWorker()
        self.bar_worker = BarChartWorker()
        self.scatter_worker = ScatterPlotWorker()
        self.histogram_worker = HistogramWorker()
        self.boxplot_worker = BoxPlotWorker()
        self.heatmap_worker = HeatmapWorker()
        self.pie_worker = PieChartWorker()
        
        # Worker registry
        self.workers = {
            'line': self.line_worker,
            'bar': self.bar_worker,
            'scatter': self.scatter_worker,
            'histogram': self.histogram_worker,
            'boxplot': self.boxplot_worker,
            'heatmap': self.heatmap_worker,
            'pie': self.pie_worker,
        }

        self.logger.info(
            f"{self.name} v{self.version} initialized with "
            f"{len(self.workers)} chart workers"
        )
        self.structured_logger.info(
            f"{self.name} initialized",
            {
                "version": self.version,
                "workers": len(self.workers),
                "worker_names": list(self.workers.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    # === SECTION 1: DATA MANAGEMENT ===

    @retry_on_error(max_attempts=2, backoff=1)
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data to visualize.
        
        Args:
            df: DataFrame to visualize
            
        Raises:
            TypeError: If df is not a DataFrame
            ValueError: If df is empty
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected DataFrame, got {type(df).__name__}")
        
        if df.empty:
            raise ValueError("Cannot set empty DataFrame")
        
        self.data = df.copy()
        self.charts = {}
        
        # Capture metadata
        self.data_metadata = {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "numeric_cols": len(df.select_dtypes(include=['number']).columns),
            "categorical_cols": len(df.select_dtypes(include=['object']).columns),
            "datetime_cols": len(df.select_dtypes(include=['datetime64']).columns),
            "null_count": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.logger.info(
            f"Data set: {self.data_metadata['rows']} rows, "
            f"{self.data_metadata['columns']} columns"
        )
        self.structured_logger.info("Data set for visualization", self.data_metadata)
        
        # Reset charts and execution history
        self.total_charts_created = 0
        self.execution_history = []
        self.errors_encountered = []

    @retry_on_error(max_attempts=2, backoff=1)
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data.copy() if self.data is not None else None

    # === SECTION 2: CHART CREATION METHODS ===

    def _execute_worker(
        self,
        worker_name: str,
        worker,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a worker with tracking and error handling.
        
        Args:
            worker_name: Name of worker type
            worker: Worker instance
            **kwargs: Worker parameters
            
        Returns:
            Result dictionary with chart and metadata
        """
        start_time = time.time()
        
        try:
            # Execute worker
            result: WorkerResult = worker.safe_execute(**kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # Track execution
            execution_record = {
                "worker": worker_name,
                "success": result.success,
                "quality_score": result.quality_score,
                "execution_time_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.execution_history.append(execution_record)
            
            if result.success:
                self._store_chart(result)
                self.total_charts_created += 1
                
                self.structured_logger.info(
                    f"{worker_name} chart created",
                    {
                        "chart_id": len(self.charts),
                        "quality": result.quality_score,
                        "time_ms": duration_ms
                    }
                )
            else:
                # Track error
                if result.errors:
                    self.errors_encountered.extend(result.errors)
                    error_types = [e.get('error_type', 'unknown') for e in result.errors]
                    self.structured_logger.error(
                        f"{worker_name} chart creation failed",
                        {"errors": error_types}
                    )
            
            return result.to_dict()
        
        except Exception as e:
            # Unexpected error
            duration_ms = (time.time() - start_time) * 1000
            error_record = {
                "error_type": type(e).__name__,
                "message": str(e),
                "worker": worker_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.errors_encountered.append(error_record)
            
            self.structured_logger.error(
                f"{worker_name} execution failed",
                {"error": str(e), "time_ms": duration_ms}
            )
            
            raise AgentError(f"Chart creation failed: {e}")

    @retry_on_error(max_attempts=3, backoff=2)
    def line_chart(self, x_col: str, y_col: str, title: Optional[str] = None,
                   theme: str = 'plotly_white', markers: bool = True) -> Dict[str, Any]:
        """Create line chart.
        
        Args:
            x_col: X-axis column
            y_col: Y-axis column
            title: Optional title
            theme: Theme name
            markers: Show markers
            
        Returns:
            Chart result dictionary
            
        Raises:
            AgentError: If data not set or chart creation fails
        """
        if self.data is None:
            raise AgentError("No data set. Call set_data() first.")
        
        return self._execute_worker(
            'line',
            self.line_worker,
            df=self.data,
            x_col=x_col,
            y_col=y_col,
            title=title,
            theme=theme,
            markers=markers,
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def bar_chart(self, x_col: str, y_col: str, title: Optional[str] = None,
                  theme: str = 'plotly_white', color: Optional[str] = None) -> Dict[str, Any]:
        """Create bar chart.
        
        Args:
            x_col: X-axis column (categorical)
            y_col: Y-axis column (numeric)
            title: Optional title
            theme: Theme name
            color: Optional color column
            
        Returns:
            Chart result dictionary
        """
        if self.data is None:
            raise AgentError("No data set. Call set_data() first.")
        
        return self._execute_worker(
            'bar',
            self.bar_worker,
            df=self.data,
            x_col=x_col,
            y_col=y_col,
            title=title,
            theme=theme,
            color=color,
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def scatter_plot(self, x_col: str, y_col: str, title: Optional[str] = None,
                     theme: str = 'plotly_white', color_col: Optional[str] = None,
                     size_col: Optional[str] = None) -> Dict[str, Any]:
        """Create scatter plot.
        
        Args:
            x_col: X-axis column
            y_col: Y-axis column
            title: Optional title
            theme: Theme name
            color_col: Optional color column
            size_col: Optional size column
            
        Returns:
            Chart result dictionary
        """
        if self.data is None:
            raise AgentError("No data set. Call set_data() first.")
        
        return self._execute_worker(
            'scatter',
            self.scatter_worker,
            df=self.data,
            x_col=x_col,
            y_col=y_col,
            title=title,
            theme=theme,
            color_col=color_col,
            size_col=size_col,
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def histogram(self, col: str, bins: int = 30, title: Optional[str] = None,
                  theme: str = 'plotly_white') -> Dict[str, Any]:
        """Create histogram.
        
        Args:
            col: Column to visualize
            bins: Number of bins
            title: Optional title
            theme: Theme name
            
        Returns:
            Chart result dictionary
        """
        if self.data is None:
            raise AgentError("No data set. Call set_data() first.")
        
        return self._execute_worker(
            'histogram',
            self.histogram_worker,
            df=self.data,
            col=col,
            bins=bins,
            title=title,
            theme=theme,
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def box_plot(self, y_col: str, x_col: Optional[str] = None,
                 title: Optional[str] = None, theme: str = 'plotly_white') -> Dict[str, Any]:
        """Create box plot.
        
        Args:
            y_col: Y-axis column
            x_col: Optional X-axis column
            title: Optional title
            theme: Theme name
            
        Returns:
            Chart result dictionary
        """
        if self.data is None:
            raise AgentError("No data set. Call set_data() first.")
        
        return self._execute_worker(
            'boxplot',
            self.boxplot_worker,
            df=self.data,
            y_col=y_col,
            x_col=x_col,
            title=title,
            theme=theme,
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def heatmap(self, title: Optional[str] = None, theme: str = 'plotly_white',
                palette: str = 'rdbu', numeric_only: bool = True) -> Dict[str, Any]:
        """Create correlation heatmap.
        
        Args:
            title: Optional title
            theme: Theme name
            palette: Color palette
            numeric_only: Only numeric columns
            
        Returns:
            Chart result dictionary
        """
        if self.data is None:
            raise AgentError("No data set. Call set_data() first.")
        
        return self._execute_worker(
            'heatmap',
            self.heatmap_worker,
            df=self.data,
            title=title,
            theme=theme,
            palette=palette,
            numeric_only=numeric_only,
        )

    @retry_on_error(max_attempts=3, backoff=2)
    def pie_chart(self, col: str, title: Optional[str] = None,
                  theme: str = 'plotly_white', palette: str = 'set1') -> Dict[str, Any]:
        """Create pie chart.
        
        Args:
            col: Column to visualize
            title: Optional title
            theme: Theme name
            palette: Color palette
            
        Returns:
            Chart result dictionary
        """
        if self.data is None:
            raise AgentError("No data set. Call set_data() first.")
        
        return self._execute_worker(
            'pie',
            self.pie_worker,
            df=self.data,
            col=col,
            title=title,
            theme=theme,
            palette=palette,
        )

    # === SECTION 3: CHART MANAGEMENT ===

    def _store_chart(self, result: WorkerResult) -> None:
        """Store chart internally with size management.
        
        Args:
            result: WorkerResult
        """
        if result.success and result.data:
            # Evict oldest chart if cache full
            if len(self.charts) >= MAX_CHARTS_CACHED:
                oldest_key = next(iter(self.charts))
                del self.charts[oldest_key]
                self.logger.warning(f"Chart cache full, evicting {oldest_key}")
            
            # Store new chart
            chart_id = f"{result.chart_type}_{len(self.charts)}"
            self.charts[chart_id] = {
                'data': result.data,
                'plotly_json': result.plotly_json,
                'metadata': result.metadata,
                'quality_score': result.quality_score,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    @retry_on_error(max_attempts=2, backoff=1)
    def get_chart(self, chart_id: str) -> Optional[Any]:
        """Get a previously created chart.
        
        Args:
            chart_id: Chart ID
            
        Returns:
            Chart object or None
        """
        chart = self.charts.get(chart_id)
        return chart.get('data') if chart else None

    @retry_on_error(max_attempts=2, backoff=1)
    def list_charts(self) -> Dict[str, Any]:
        """List all created charts.
        
        Returns:
            Chart information
        """
        charts_info = []
        for chart_id, chart_data in self.charts.items():
            charts_info.append({
                "id": chart_id,
                "quality_score": chart_data['quality_score'],
                "timestamp": chart_data['timestamp']
            })
        
        result = {
            "status": "success",
            "count": len(self.charts),
            "charts": charts_info,
        }
        
        self.structured_logger.info(
            "Charts listed",
            {"count": result["count"]}
        )
        
        return result

    # === SECTION 4: HEALTH & ERROR REPORTING ===

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report.
        
        Returns:
            Health metrics including overall score, errors, recommendations
        """
        # Calculate average quality score
        if self.execution_history:
            avg_quality = sum(
                e['quality_score'] for e in self.execution_history
            ) / len(self.execution_history)
        else:
            avg_quality = 1.0
        
        # Calculate health score (0-100)
        health_score = min(100, avg_quality * 100)
        
        # Categorize errors
        error_types = {}
        for error in self.errors_encountered:
            error_type = error.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Worker health
        worker_health = {}
        for worker_name in self.workers.keys():
            worker_executions = [
                e for e in self.execution_history
                if e['worker'] == worker_name
            ]
            if worker_executions:
                worker_avg_quality = sum(
                    e['quality_score'] for e in worker_executions
                ) / len(worker_executions)
                worker_health[worker_name] = worker_avg_quality * 100
            else:
                worker_health[worker_name] = 100.0  # No errors yet
        
        # Generate recommendations
        recommendations = []
        if health_score < HEALTH_SCORE_THRESHOLD * 100:
            recommendations.append(
                f"Overall health ({health_score:.1f}%) below threshold. "
                f"Review data quality and error patterns."
            )
        
        if self.data_metadata.get('null_count', 0) > 0:
            null_pct = (self.data_metadata['null_count'] /
                       (self.data_metadata['rows'] * self.data_metadata['columns'])) * 100
            if null_pct > 10:
                recommendations.append(
                    f"Data contains {null_pct:.1f}% null values. "
                    f"Consider imputation or filtering."
                )
        
        if self.data_metadata.get('duplicate_rows', 0) > 0:
            recommendations.append(
                f"Found {self.data_metadata['duplicate_rows']} duplicate rows. "
                f"Consider deduplication."
            )
        
        return {
            "status": "healthy" if health_score >= HEALTH_SCORE_THRESHOLD * 100 else "degraded",
            "overall_health": health_score,
            "total_charts_created": self.total_charts_created,
            "total_errors": len(self.errors_encountered),
            "error_types": error_types,
            "worker_health": worker_health,
            "average_quality_score": avg_quality,
            "execution_count": len(self.execution_history),
            "recommendations": recommendations,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_summary(self) -> str:
        """Get summary of Visualizer state.
        
        Returns:
            Summary string
        """
        if self.data is None:
            return "Visualizer: No data loaded"
        
        uptime_seconds = time.time() - self.start_time
        uptime_min = int(uptime_seconds / 60)
        
        return (
            f"Visualizer Summary:\n"
            f"  Version: {self.version}\n"
            f"  Data: {self.data_metadata.get('rows', 0)} rows, "
            f"{self.data_metadata.get('columns', 0)} columns\n"
            f"  Charts created: {self.total_charts_created}\n"
            f"  Charts cached: {len(self.charts)}\n"
            f"  Errors: {len(self.errors_encountered)}\n"
            f"  Uptime: {uptime_min}m"
        )
