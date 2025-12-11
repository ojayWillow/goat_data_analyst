"""Heatmap Worker - Correlation matrix visualization."""

import pandas as pd
import numpy as np
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


class HeatmapWorker(BaseChartWorker):
    """Worker that creates heatmaps."""
    
    def __init__(self):
        """Initialize HeatmapWorker."""
        super().__init__("HeatmapWorker", "heatmap")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute heatmap creation.
        
        Args:
            df: DataFrame to visualize
            title: Optional chart title
            theme: Optional theme name
            palette: Optional color palette
            numeric_only: Optional (default True)
            
        Returns:
            WorkerResult with chart
        """
        df = kwargs.get('df')
        title = kwargs.get('title')
        theme = kwargs.get('theme', 'plotly_white')
        palette = kwargs.get('palette', 'rdbu')
        numeric_only = kwargs.get('numeric_only', True)
        
        result = self._create_result()
        
        # Validate DataFrame
        validation = self._validate_dataframe(df)
        if validation:
            return validation
        
        try:
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                result.success = False
                return result
            
            # Filter numeric columns
            if numeric_only:
                numeric_df = df.select_dtypes(include=[np.number])
            else:
                numeric_df = df
            
            if numeric_df.shape[1] < 2:
                self._add_error(result, ErrorType.INVALID_PARAMETER, "Need at least 2 columns")
                result.success = False
                return result
            
            corr_matrix = numeric_df.corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale=get_palette(palette),
                zmid=0
            ))
            
            fig.update_layout(
                title=title or "Correlation Heatmap",
                template=get_theme(theme)
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.metadata = {
                "columns": len(corr_matrix.columns),
                "correlation_min": float(corr_matrix.values.min()),
                "correlation_max": float(corr_matrix.values.max()),
                "palette": palette,
                "theme": theme,
                "title": title or "Correlation Heatmap",
            }
            
            logger.info(f"Heatmap created with {len(corr_matrix.columns)} columns")
            return result
        
        except Exception as e:
            self._add_error(result, ErrorType.RENDER_ERROR, str(e))
            result.success = False
            return result
