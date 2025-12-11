"""Visualizer Agent - Coordinates chart creation workers.

Creates interactive and static charts using a plugin architecture.
Easy to extend with new chart types.

Integrated with Week 1 Systems:
- Structured logging with metrics
- Automatic retry with exponential backoff
- Error recovery and handling
"""

from typing import Any, Dict, Optional
import pandas as pd

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
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

logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)


class Visualizer:
    """Visualizer Agent - coordinates chart creation workers.
    
    Chart Types:
    - Line charts (time series)
    - Bar charts (categorical)
    - Scatter plots (correlations)
    - Histograms (distributions)
    - Box plots (quartiles)
    - Heatmaps (correlations)
    - Pie charts (composition)
    
    PLUGIN SYSTEM: Easy to add new chart types!
    
    Week 1 Integration:
    - Structured logging with metrics at each step
    - Automatic retry on transient failures
    - Error recovery and detailed error messages
    """

    def __init__(self) -> None:
        """Initialize Visualizer agent and all workers."""
        self.name = "Visualizer"
        self.logger = get_logger("Visualizer")
        self.structured_logger = get_structured_logger("Visualizer")
        self.data: Optional[pd.DataFrame] = None
        self.charts: Dict[str, Any] = {}

        # === STEP 1: INITIALIZE ALL WORKERS ===
        self.line_worker = LineChartWorker()
        self.bar_worker = BarChartWorker()
        self.scatter_worker = ScatterPlotWorker()
        self.histogram_worker = HistogramWorker()
        self.boxplot_worker = BoxPlotWorker()
        self.heatmap_worker = HeatmapWorker()
        self.pie_worker = PieChartWorker()

        self.logger.info("Visualizer initialized with 7 chart workers")
        self.structured_logger.info("Visualizer initialized", {
            "workers": 7,
            "worker_names": [
                "LineChartWorker",
                "BarChartWorker",
                "ScatterPlotWorker",
                "HistogramWorker",
                "BoxPlotWorker",
                "HeatmapWorker",
                "PieChartWorker"
            ]
        })

    # === SECTION 1: DATA MANAGEMENT ===

    @retry_on_error(max_attempts=2, backoff=1)
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data to visualize.
        
        Args:
            df: DataFrame to visualize
        """
        self.data = df.copy()
        self.charts = {}
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
        self.structured_logger.info("Data set for visualization", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "numeric_cols": len(df.select_dtypes(include=['number']).columns),
            "categorical_cols": len(df.select_dtypes(include=['object']).columns)
        })

    @retry_on_error(max_attempts=2, backoff=1)
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data

    # === SECTION 2: CHART CREATION METHODS ===

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
        """
        if self.data is None:
            error_msg = "No data set"
            self.structured_logger.error("Line chart creation failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Creating line chart", {
            "x_col": x_col,
            "y_col": y_col,
            "theme": theme
        })
        
        try:
            result = self.line_worker.safe_execute(
                df=self.data,
                x_col=x_col,
                y_col=y_col,
                title=title,
                theme=theme,
                markers=markers,
            )
            
            self._store_chart(result)
            self.structured_logger.info("Line chart created successfully", {
                "chart_id": len(self.charts)
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Line chart creation failed", {
                "x_col": x_col,
                "y_col": y_col,
                "error": str(e)
            })
            raise AgentError(f"Chart creation failed: {e}")

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
            error_msg = "No data set"
            self.structured_logger.error("Bar chart creation failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Creating bar chart", {
            "x_col": x_col,
            "y_col": y_col,
            "theme": theme
        })
        
        try:
            result = self.bar_worker.safe_execute(
                df=self.data,
                x_col=x_col,
                y_col=y_col,
                title=title,
                theme=theme,
                color=color,
            )
            
            self._store_chart(result)
            self.structured_logger.info("Bar chart created successfully", {
                "chart_id": len(self.charts)
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Bar chart creation failed", {
                "x_col": x_col,
                "y_col": y_col,
                "error": str(e)
            })
            raise AgentError(f"Chart creation failed: {e}")

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
            error_msg = "No data set"
            self.structured_logger.error("Scatter plot creation failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Creating scatter plot", {
            "x_col": x_col,
            "y_col": y_col,
            "theme": theme
        })
        
        try:
            result = self.scatter_worker.safe_execute(
                df=self.data,
                x_col=x_col,
                y_col=y_col,
                title=title,
                theme=theme,
                color_col=color_col,
                size_col=size_col,
            )
            
            self._store_chart(result)
            self.structured_logger.info("Scatter plot created successfully", {
                "chart_id": len(self.charts)
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Scatter plot creation failed", {
                "x_col": x_col,
                "y_col": y_col,
                "error": str(e)
            })
            raise AgentError(f"Chart creation failed: {e}")

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
            error_msg = "No data set"
            self.structured_logger.error("Histogram creation failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Creating histogram", {
            "column": col,
            "bins": bins,
            "theme": theme
        })
        
        try:
            result = self.histogram_worker.safe_execute(
                df=self.data,
                col=col,
                bins=bins,
                title=title,
                theme=theme,
            )
            
            self._store_chart(result)
            self.structured_logger.info("Histogram created successfully", {
                "chart_id": len(self.charts)
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Histogram creation failed", {
                "column": col,
                "error": str(e)
            })
            raise AgentError(f"Chart creation failed: {e}")

    @retry_on_error(max_attempts=3, backoff=2)
    def box_plot(self, y_col: str, x_col: Optional[str] = None, title: Optional[str] = None,
                 theme: str = 'plotly_white') -> Dict[str, Any]:
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
            error_msg = "No data set"
            self.structured_logger.error("Box plot creation failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Creating box plot", {
            "y_col": y_col,
            "x_col": x_col,
            "theme": theme
        })
        
        try:
            result = self.boxplot_worker.safe_execute(
                df=self.data,
                y_col=y_col,
                x_col=x_col,
                title=title,
                theme=theme,
            )
            
            self._store_chart(result)
            self.structured_logger.info("Box plot created successfully", {
                "chart_id": len(self.charts)
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Box plot creation failed", {
                "y_col": y_col,
                "error": str(e)
            })
            raise AgentError(f"Chart creation failed: {e}")

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
            error_msg = "No data set"
            self.structured_logger.error("Heatmap creation failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Creating heatmap", {
            "palette": palette,
            "theme": theme,
            "numeric_only": numeric_only
        })
        
        try:
            result = self.heatmap_worker.safe_execute(
                df=self.data,
                title=title,
                theme=theme,
                palette=palette,
                numeric_only=numeric_only,
            )
            
            self._store_chart(result)
            self.structured_logger.info("Heatmap created successfully", {
                "chart_id": len(self.charts)
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Heatmap creation failed", {
                "palette": palette,
                "error": str(e)
            })
            raise AgentError(f"Chart creation failed: {e}")

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
            error_msg = "No data set"
            self.structured_logger.error("Pie chart creation failed", {
                "error": error_msg
            })
            raise AgentError(error_msg)
        
        self.structured_logger.info("Creating pie chart", {
            "column": col,
            "palette": palette,
            "theme": theme
        })
        
        try:
            result = self.pie_worker.safe_execute(
                df=self.data,
                col=col,
                title=title,
                theme=theme,
                palette=palette,
            )
            
            self._store_chart(result)
            self.structured_logger.info("Pie chart created successfully", {
                "chart_id": len(self.charts)
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Pie chart creation failed", {
                "column": col,
                "error": str(e)
            })
            raise AgentError(f"Chart creation failed: {e}")

    # === SECTION 3: CHART MANAGEMENT ===

    def _store_chart(self, result: WorkerResult) -> None:
        """Store chart internally.
        
        Args:
            result: WorkerResult
        """
        if result.success and result.data:
            chart_id = f"{result.chart_type}_{len(self.charts)}"
            self.charts[chart_id] = result.data

    @retry_on_error(max_attempts=2, backoff=1)
    def get_chart(self, chart_id: str) -> Optional[Any]:
        """Get a previously created chart.
        
        Args:
            chart_id: Chart ID
            
        Returns:
            Chart object or None
        """
        return self.charts.get(chart_id)

    @retry_on_error(max_attempts=2, backoff=1)
    def list_charts(self) -> Dict[str, Any]:
        """List all created charts.
        
        Returns:
            Chart information
        """
        result = {
            "status": "success",
            "count": len(self.charts),
            "charts": list(self.charts.keys()),
        }
        
        self.structured_logger.info("Charts listed", {
            "count": result["count"],
            "charts": result["charts"]
        })
        
        return result

    @retry_on_error(max_attempts=2, backoff=1)
    def get_summary(self) -> str:
        """Get summary of Visualizer state.
        
        Returns:
            Summary string
        """
        if self.data is None:
            return "Visualizer: No data loaded"
        
        return (
            f"Visualizer Summary:\n"
            f"  Data: {self.data.shape[0]} rows, {self.data.shape[1]} columns\n"
            f"  Charts created: {len(self.charts)}"
        )
