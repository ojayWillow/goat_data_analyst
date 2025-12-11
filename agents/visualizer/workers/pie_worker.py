"""Pie Chart Worker - Composition and proportion visualization."""

import pandas as pd
from typing import Any, Dict, Optional

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .config import get_theme, get_palette
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

logger = get_logger(__name__)


class PieChartWorker(BaseChartWorker):
    """Worker that creates pie charts."""
    
    def __init__(self):
        """Initialize PieChartWorker."""
        super().__init__("PieChartWorker", "pie")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute pie chart creation.
        
        Args:
            df: DataFrame to visualize
            col: Column to visualize
            title: Optional chart title
            theme: Optional theme name
            palette: Optional color palette
            
        Returns:
            WorkerResult with chart
        """
        df = kwargs.get('df')
        col = kwargs.get('col')
        title = kwargs.get('title')
        theme = kwargs.get('theme', 'plotly_white')
        palette = kwargs.get('palette', 'set1')
        
        result = self._create_result()
        
        # Validate DataFrame
        validation = self._validate_dataframe(df)
        if validation:
            return validation
        
        # Validate columns
        validation = self._validate_columns(df, [col])
        if validation:
            return validation
        
        try:
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                result.success = False
                return result
            
            value_counts = df[col].value_counts()
            
            fig = go.Figure(data=[go.Pie(
                labels=value_counts.index,
                values=value_counts.values,
            )])
            
            fig.update_layout(
                title=title or f"Distribution of {col}",
                template=get_theme(theme)
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.metadata = {
                "column": col,
                "categories": len(value_counts),
                "palette": palette,
                "theme": theme,
                "title": title or f"Distribution of {col}",
            }
            
            logger.info(f"Pie chart created: {col} with {len(value_counts)} categories")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.RENDER_ERROR, str(e))
            result.success = False
            return result
