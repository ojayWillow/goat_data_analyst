"""Visualizer Agent - Data visualization and chart generation.

Creates interactive and static charts using Plotly and Matplotlib.
Supports multiple chart types and customization options.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import json
from datetime import datetime

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from core.logger import get_logger
from core.exceptions import AgentError

logger = get_logger(__name__)


class Visualizer:
    """Agent for data visualization.
    
    Capabilities:
    - Line charts (time series)
    - Bar charts (categorical comparisons)
    - Scatter plots (correlations)
    - Histograms (distributions)
    - Box plots (quartile analysis)
    - Heatmaps (correlations)
    - Pie charts (composition)
    - Multi-series charts
    - Interactive charts (Plotly)
    """
    
    def __init__(self):
        """Initialize Visualizer agent."""
        self.name = "Visualizer"
        self.data = None
        self.charts = {}
        
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available. Install with: pip install plotly")
        
        logger.info(f"{self.name} initialized")
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data to visualize.
        
        Args:
            df: DataFrame to visualize
        """
        self.data = df.copy()
        self.charts = {}  # Clear chart cache
        logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    def line_chart(self, x_col: str, y_col: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create line chart.
        
        Args:
            x_col: Column for X-axis
            y_col: Column for Y-axis
            title: Chart title
            
        Returns:
            Dictionary with chart data
            
        Raises:
            AgentError: If columns don't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if x_col not in self.data.columns or y_col not in self.data.columns:
            raise AgentError(f"Columns not found")
        
        try:
            logger.info(f"Creating line chart: X={x_col}, Y={y_col}")
            
            if not PLOTLY_AVAILABLE:
                return {"status": "error", "message": "Plotly not installed"}
            
            fig = px.line(
                self.data,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} over {x_col}",
                markers=True,
                template="plotly_white"
            )
            
            chart_id = f"line_{x_col}_{y_col}"
            self.charts[chart_id] = fig
            
            return {
                "status": "success",
                "chart_type": "line",
                "chart_id": chart_id,
                "x_column": x_col,
                "y_column": y_col,
                "data_points": len(self.data),
                "plotly_json": fig.to_json(),
            }
        
        except Exception as e:
            logger.error(f"Line chart creation failed: {e}")
            raise AgentError(f"Failed to create line chart: {e}")
    
    def bar_chart(self, x_col: str, y_col: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create bar chart.
        
        Args:
            x_col: Column for X-axis (categorical)
            y_col: Column for Y-axis (numeric)
            title: Chart title
            
        Returns:
            Dictionary with chart data
            
        Raises:
            AgentError: If columns don't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if x_col not in self.data.columns or y_col not in self.data.columns:
            raise AgentError(f"Columns not found")
        
        try:
            logger.info(f"Creating bar chart: X={x_col}, Y={y_col}")
            
            if not PLOTLY_AVAILABLE:
                return {"status": "error", "message": "Plotly not installed"}
            
            fig = px.bar(
                self.data,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} by {x_col}",
                template="plotly_white"
            )
            
            chart_id = f"bar_{x_col}_{y_col}"
            self.charts[chart_id] = fig
            
            return {
                "status": "success",
                "chart_type": "bar",
                "chart_id": chart_id,
                "x_column": x_col,
                "y_column": y_col,
                "categories": self.data[x_col].nunique(),
                "plotly_json": fig.to_json(),
            }
        
        except Exception as e:
            logger.error(f"Bar chart creation failed: {e}")
            raise AgentError(f"Failed to create bar chart: {e}")
    
    def scatter_plot(self, x_col: str, y_col: str, color_col: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        """Create scatter plot.
        
        Args:
            x_col: Column for X-axis
            y_col: Column for Y-axis
            color_col: Optional column for color coding
            title: Chart title
            
        Returns:
            Dictionary with chart data
            
        Raises:
            AgentError: If columns don't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if x_col not in self.data.columns or y_col not in self.data.columns:
            raise AgentError(f"Columns not found")
        
        try:
            logger.info(f"Creating scatter plot: X={x_col}, Y={y_col}")
            
            if not PLOTLY_AVAILABLE:
                return {"status": "error", "message": "Plotly not installed"}
            
            fig = px.scatter(
                self.data,
                x=x_col,
                y=y_col,
                color=color_col,
                title=title or f"{y_col} vs {x_col}",
                template="plotly_white"
            )
            
            chart_id = f"scatter_{x_col}_{y_col}"
            self.charts[chart_id] = fig
            
            return {
                "status": "success",
                "chart_type": "scatter",
                "chart_id": chart_id,
                "x_column": x_col,
                "y_column": y_col,
                "color_column": color_col,
                "points": len(self.data),
                "plotly_json": fig.to_json(),
            }
        
        except Exception as e:
            logger.error(f"Scatter plot creation failed: {e}")
            raise AgentError(f"Failed to create scatter plot: {e}")
    
    def histogram(self, col: str, bins: int = 30, title: Optional[str] = None) -> Dict[str, Any]:
        """Create histogram.
        
        Args:
            col: Column to visualize
            bins: Number of bins
            title: Chart title
            
        Returns:
            Dictionary with chart data
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"Creating histogram: {col} with {bins} bins")
            
            if not PLOTLY_AVAILABLE:
                return {"status": "error", "message": "Plotly not installed"}
            
            fig = px.histogram(
                self.data,
                x=col,
                nbins=bins,
                title=title or f"Distribution of {col}",
                template="plotly_white"
            )
            
            chart_id = f"hist_{col}"
            self.charts[chart_id] = fig
            
            return {
                "status": "success",
                "chart_type": "histogram",
                "chart_id": chart_id,
                "column": col,
                "bins": bins,
                "values": len(self.data),
                "plotly_json": fig.to_json(),
            }
        
        except Exception as e:
            logger.error(f"Histogram creation failed: {e}")
            raise AgentError(f"Failed to create histogram: {e}")
    
    def box_plot(self, y_col: str, x_col: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        """Create box plot.
        
        Args:
            y_col: Column for Y-axis (numeric)
            x_col: Optional column for X-axis (categorical)
            title: Chart title
            
        Returns:
            Dictionary with chart data
            
        Raises:
            AgentError: If columns don't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if y_col not in self.data.columns:
            raise AgentError(f"Column '{y_col}' not found")
        
        try:
            logger.info(f"Creating box plot: Y={y_col}, X={x_col}")
            
            if not PLOTLY_AVAILABLE:
                return {"status": "error", "message": "Plotly not installed"}
            
            fig = px.box(
                self.data,
                x=x_col,
                y=y_col,
                title=title or f"Box plot of {y_col}",
                template="plotly_white"
            )
            
            chart_id = f"box_{y_col}"
            self.charts[chart_id] = fig
            
            return {
                "status": "success",
                "chart_type": "box",
                "chart_id": chart_id,
                "y_column": y_col,
                "x_column": x_col,
                "plotly_json": fig.to_json(),
            }
        
        except Exception as e:
            logger.error(f"Box plot creation failed: {e}")
            raise AgentError(f"Failed to create box plot: {e}")
    
    def heatmap(self, numeric_only: bool = True, title: Optional[str] = None) -> Dict[str, Any]:
        """Create correlation heatmap.
        
        Args:
            numeric_only: Include only numeric columns
            title: Chart title
            
        Returns:
            Dictionary with chart data
            
        Raises:
            AgentError: If insufficient numeric columns
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Creating correlation heatmap")
            
            if not PLOTLY_AVAILABLE:
                return {"status": "error", "message": "Plotly not installed"}
            
            if numeric_only:
                numeric_data = self.data.select_dtypes(include=[np.number])
            else:
                numeric_data = self.data
            
            if numeric_data.shape[1] < 2:
                return {"status": "error", "message": "Need at least 2 numeric columns"}
            
            corr_matrix = numeric_data.corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmid=0
            ))
            
            fig.update_layout(
                title=title or "Correlation Heatmap",
                template="plotly_white"
            )
            
            chart_id = "heatmap_corr"
            self.charts[chart_id] = fig
            
            return {
                "status": "success",
                "chart_type": "heatmap",
                "chart_id": chart_id,
                "columns": len(corr_matrix.columns),
                "correlation_range": [float(corr_matrix.values.min()), float(corr_matrix.values.max())],
                "plotly_json": fig.to_json(),
            }
        
        except Exception as e:
            logger.error(f"Heatmap creation failed: {e}")
            raise AgentError(f"Failed to create heatmap: {e}")
    
    def pie_chart(self, col: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create pie chart for categorical data.
        
        Args:
            col: Column to visualize
            title: Chart title
            
        Returns:
            Dictionary with chart data
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"Creating pie chart: {col}")
            
            if not PLOTLY_AVAILABLE:
                return {"status": "error", "message": "Plotly not installed"}
            
            value_counts = self.data[col].value_counts()
            
            fig = go.Figure(data=[go.Pie(
                labels=value_counts.index,
                values=value_counts.values
            )])
            
            fig.update_layout(
                title=title or f"Distribution of {col}",
                template="plotly_white"
            )
            
            chart_id = f"pie_{col}"
            self.charts[chart_id] = fig
            
            return {
                "status": "success",
                "chart_type": "pie",
                "chart_id": chart_id,
                "column": col,
                "categories": len(value_counts),
                "plotly_json": fig.to_json(),
            }
        
        except Exception as e:
            logger.error(f"Pie chart creation failed: {e}")
            raise AgentError(f"Failed to create pie chart: {e}")
    
    def get_chart(self, chart_id: str) -> Optional[Any]:
        """Get a previously created chart.
        
        Args:
            chart_id: Chart ID
            
        Returns:
            Plotly figure or None
        """
        return self.charts.get(chart_id)
    
    def list_charts(self) -> Dict[str, Any]:
        """List all created charts.
        
        Returns:
            Dictionary with chart information
        """
        return {
            "status": "success",
            "count": len(self.charts),
            "charts": list(self.charts.keys()),
        }
