"""Box Plot Worker - Quartile and outlier visualization."""

import pandas as pd
from typing import Any, Dict, Optional

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .config import get_theme
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)


class BoxPlotWorker(BaseChartWorker):
    """Worker that creates box plots."""
    
    def __init__(self):
        """Initialize BoxPlotWorker."""
        super().__init__("BoxPlotWorker", "box")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute box plot creation.
        
        Args:
            df: DataFrame to visualize
            y_col: Column for Y-axis (numeric)
            title: Optional chart title
            theme: Optional theme name
            x_col: Optional column for X-axis (categorical)
            
        Returns:
            WorkerResult with chart
        """
        df = kwargs.get('df')
        y_col = kwargs.get('y_col')
        x_col = kwargs.get('x_col')
        title = kwargs.get('title')
        theme = kwargs.get('theme', 'plotly_white')
        
        result = self._create_result()
        
        # Validate DataFrame
        validation = self._validate_dataframe(df)
        if validation:
            return validation
        
        # Validate columns
        cols_to_check = [y_col]
        if x_col:
            cols_to_check.append(x_col)
        validation = self._validate_columns(df, cols_to_check)
        if validation:
            return validation
        
        try:
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                result.success = False
                return result
            
            fig = px.box(
                df,
                x=x_col,
                y=y_col,
                title=title or f"Box plot of {y_col}",
                template=get_theme(theme),
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.metadata = {
                "y_column": y_col,
                "x_column": x_col,
                "theme": theme,
                "title": title or f"Box plot of {y_col}",
            }
            
            logger.info(f"Box plot created: {y_col}")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.RENDER_ERROR, str(e))
            result.success = False
            return result
