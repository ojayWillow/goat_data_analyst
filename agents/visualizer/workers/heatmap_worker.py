"""Heatmap Worker - Correlation visualization.

Creates heatmaps for correlation analysis of numeric variables.
"""

from typing import Any, Dict, Optional
import pandas as pd
import logging

try:
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .config import get_palette
from core.logger import get_logger

# ===== CONSTANTS =====
DEFAULT_PALETTE: str = "rdbu"

logger = get_logger(__name__)


class HeatmapWorker(BaseChartWorker):
    """Worker that creates correlation heatmaps.
    
    Purpose:
        Visualize correlations between numeric variables using a heatmap.
    
    Input Format:
        {
            'df': pd.DataFrame,           # Required
            'title': Optional[str],       # Optional
            'theme': str,                 # Optional (not used for heatmap)
            'palette': str,               # Optional: Color palette (default: rdbu)
            'numeric_only': bool          # Optional: Only numeric cols (default: True)
        }
    
    Example:
        >>> worker = HeatmapWorker()
        >>> df = pd.DataFrame({
        ...     'a': range(100),
        ...     'b': [i*2 for i in range(100)],
        ...     'c': [i*3 for i in range(100)]
        ... })
        >>> result = worker.execute(df=df, palette='rdbu')
    """
    
    def __init__(self) -> None:
        """Initialize HeatmapWorker."""
        super().__init__("HeatmapWorker", "heatmap")
        self.logger = get_logger(self.__class__.__name__)
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute heatmap creation."""
        df: Optional[pd.DataFrame] = kwargs.get('df')
        title: Optional[str] = kwargs.get('title')
        palette: str = kwargs.get('palette', DEFAULT_PALETTE)
        numeric_only: bool = kwargs.get('numeric_only', True)
        
        result = self._create_result(quality_score=1.0)
        
        # === VALIDATION ===
        
        if not self._validate_dataframe(df):
            self._add_error(result, ErrorType.MISSING_DATA, "Invalid DataFrame")
            return result
        
        # Select numeric columns if requested
        if numeric_only:
            df_numeric = df.select_dtypes(include=['number'])
            if df_numeric.empty:
                self._add_error(result, ErrorType.MISSING_DATA, "No numeric columns found")
                return result
            df = df_numeric
        
        if len(df.columns) < 2:
            self._add_error(result, ErrorType.MISSING_DATA, "Need >= 2 columns for heatmap")
            return result
        
        # === DATA QUALITY ===
        
        try:
            quality_score = self._check_data_quality(df, result)
            result.quality_score = quality_score
            result.rows_processed = len(df)
            result.rows_failed = df.isna().sum().sum()
            
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                return result
            
            # === EXECUTION ===
            
            self.logger.info(f"Creating heatmap for {len(df.columns)} columns")
            
            # Calculate correlation
            corr_matrix = df.corr()
            
            # Create heatmap using figure factory
            colorscale = self._get_colorscale(palette)
            fig = ff.create_annotated_heatmap(
                z=corr_matrix.values,
                x=list(corr_matrix.columns),
                y=list(corr_matrix.columns),
                colorscale=colorscale,
                showscale=True,
                reversescale=False
            )
            
            fig.update_layout(
                title=title or "Correlation Heatmap",
                xaxis_title="Variables",
                yaxis_title="Variables"
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.success = True
            result.metadata = {
                "num_columns": len(df.columns),
                "columns": list(df.columns),
                "data_points": len(df),
                "palette": palette,
                "title": title or "Correlation Heatmap"
            }
            
            self.logger.info(f"Heatmap created. Quality: {quality_score:.2f}")
            return result
        
        except Exception as e:
            self._handle_error(result, e, ErrorType.RENDER_ERROR)
            return result
    
    def _get_colorscale(self, palette: str) -> str:
        """Get Plotly colorscale from palette name."""
        palette_map = {
            'rdbu': 'RdBu',
            'viridis': 'Viridis',
            'reds': 'Reds',
            'blues': 'Blues',
            'greens': 'Greens',
        }
        return palette_map.get(palette, 'RdBu')
