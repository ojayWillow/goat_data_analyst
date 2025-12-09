"""Line Chart Worker - Time series and continuous data visualization."""

import pandas as pd
from typing import Any, Dict, Optional

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .config import get_theme, get_palette
from core.logger import get_logger

logger = get_logger(__name__)


class LineChartWorker(BaseChartWorker):
    """Worker that creates line charts."""
    
    def __init__(self):
        """Initialize LineChartWorker."""
        super().__init__("LineChartWorker", "line")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute line chart creation.
        
        Args:
            df: DataFrame to visualize
            x_col: Column for X-axis
            y_col: Column for Y-axis
            title: Optional chart title
            theme: Optional theme name
            markers: Optional (default True)
            
        Returns:
            WorkerResult with chart
        """
        df = kwargs.get('df')
        x_col = kwargs.get('x_col')
        y_col = kwargs.get('y_col')
        title = kwargs.get('title')
        theme = kwargs.get('theme', 'plotly_white')
        markers = kwargs.get('markers', True)
        
        result = self._create_result()
        
        # Validate DataFrame
        validation = self._validate_dataframe(df)
        if validation:
            return validation
        
        # Validate columns
        validation = self._validate_columns(df, [x_col, y_col])
        if validation:
            return validation
        
        try:
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                result.success = False
                return result
            
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} over {x_col}",
                markers=markers,
                template=get_theme(theme),
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.metadata = {
                "x_column": x_col,
                "y_column": y_col,
                "data_points": len(df),
                "theme": theme,
                "title": title or f"{y_col} over {x_col}",
            }
            
            logger.info(f"Line chart created: {x_col} vs {y_col}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.RENDER_ERROR, str(e))
            result.success = False
            return result
