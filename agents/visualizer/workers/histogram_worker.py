"""Histogram Worker - Distribution visualization."""

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


class HistogramWorker(BaseChartWorker):
    """Worker that creates histograms."""
    
    def __init__(self):
        """Initialize HistogramWorker."""
        super().__init__("HistogramWorker", "histogram")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute histogram creation.
        
        Args:
            df: DataFrame to visualize
            col: Column to visualize
            title: Optional chart title
            theme: Optional theme name
            bins: Optional number of bins (default 30)
            
        Returns:
            WorkerResult with chart
        """
        df = kwargs.get('df')
        col = kwargs.get('col')
        title = kwargs.get('title')
        theme = kwargs.get('theme', 'plotly_white')
        bins = kwargs.get('bins', 30)
        
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
            
            fig = px.histogram(
                df,
                x=col,
                nbins=bins,
                title=title or f"Distribution of {col}",
                template=get_theme(theme),
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.metadata = {
                "column": col,
                "bins": bins,
                "values": len(df),
                "theme": theme,
                "title": title or f"Distribution of {col}",
            }
            
            logger.info(f"Histogram created: {col} with {bins} bins")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.RENDER_ERROR, str(e))
            result.success = False
            return result
