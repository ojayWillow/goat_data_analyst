"""Scatter Plot Worker - Correlation and relationship visualization."""

import pandas as pd
from typing import Any, Dict, Optional

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .config import get_theme, get_palette
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)


class ScatterPlotWorker(BaseChartWorker):
    """Worker that creates scatter plots."""
    
    def __init__(self):
        """Initialize ScatterPlotWorker."""
        super().__init__("ScatterPlotWorker", "scatter")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute scatter plot creation.
        
        Args:
            df: DataFrame to visualize
            x_col: Column for X-axis
            y_col: Column for Y-axis
            title: Optional chart title
            theme: Optional theme name
            color_col: Optional column for color coding
            size_col: Optional column for size coding
            
        Returns:
            WorkerResult with chart
        """
        df = kwargs.get('df')
        x_col = kwargs.get('x_col')
        y_col = kwargs.get('y_col')
        title = kwargs.get('title')
        theme = kwargs.get('theme', 'plotly_white')
        color_col = kwargs.get('color_col')
        size_col = kwargs.get('size_col')
        
        result = self._create_result()
        
        # Validate DataFrame
        validation = self._validate_dataframe(df)
        if validation:
            return validation
        
        # Validate columns
        cols_to_check = [x_col, y_col]
        if color_col:
            cols_to_check.append(color_col)
        if size_col:
            cols_to_check.append(size_col)
        validation = self._validate_columns(df, cols_to_check)
        if validation:
            return validation
        
        try:
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                result.success = False
                return result
            
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                size=size_col,
                title=title or f"{y_col} vs {x_col}",
                template=get_theme(theme),
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.metadata = {
                "x_column": x_col,
                "y_column": y_col,
                "color_column": color_col,
                "size_column": size_col,
                "points": len(df),
                "theme": theme,
                "title": title or f"{y_col} vs {x_col}",
            }
            
            logger.info(f"Scatter plot created: {x_col} vs {y_col}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.RENDER_ERROR, str(e))
            result.success = False
            return result
