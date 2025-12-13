"""Pie Chart Worker - Composition visualization.

Creates pie charts for showing parts of a whole.
"""

from typing import Any, Dict, Optional
import pandas as pd
import logging

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import BaseChartWorker, WorkerResult, ErrorType
from .config import get_palette
from core.logger import get_logger

# ===== CONSTANTS =====
DEFAULT_PALETTE: str = "set1"
MAX_SLICES: int = 20  # Reasonable limit for readability

logger = get_logger(__name__)


class PieChartWorker(BaseChartWorker):
    """Worker that creates pie charts for composition analysis.
    
    Purpose:
        Visualize the proportional composition of categorical data.
    
    Input Format:
        {
            'df': pd.DataFrame,           # Required
            'col': str,                   # Required: Column to visualize
            'title': Optional[str],       # Optional
            'theme': str,                 # Optional (not used for pie)
            'palette': str                # Optional: Color palette (default: set1)
        }
    
    Example:
        >>> worker = PieChartWorker()
        >>> df = pd.DataFrame({
        ...     'category': ['A', 'B', 'C', 'A', 'B'],
        ...     'value': [10, 20, 30, 15, 25]
        ... })
        >>> result = worker.execute(df=df, col='category')
    """
    
    def __init__(self) -> None:
        """Initialize PieChartWorker."""
        super().__init__("PieChartWorker", "pie")
        self.logger = get_logger(self.__class__.__name__)
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute pie chart creation."""
        df: Optional[pd.DataFrame] = kwargs.get('df')
        col: Optional[str] = kwargs.get('col')
        title: Optional[str] = kwargs.get('title')
        palette: str = kwargs.get('palette', DEFAULT_PALETTE)
        
        result = self._create_result(quality_score=1.0)
        
        # === VALIDATION ===
        
        if not self._validate_dataframe(df):
            self._add_error(result, ErrorType.MISSING_DATA, "Invalid DataFrame")
            return result
        
        is_valid, missing = self._validate_columns(df, [col])
        if not is_valid:
            self._add_error(result, ErrorType.MISSING_COLUMN, f"Missing: {missing}")
            return result
        
        # Check number of categories
        unique_count = df[col].nunique()
        if unique_count > MAX_SLICES:
            self._add_warning(
                result,
                f"Many categories ({unique_count} > {MAX_SLICES}): "
                f"chart may be crowded. Consider filtering or aggregating."
            )
        
        # === DATA QUALITY ===
        
        try:
            quality_score = self._check_data_quality(df, result)
            result.quality_score = quality_score
            result.rows_processed = len(df)
            result.rows_failed = df[col].isna().sum()
            
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                return result
            
            # === EXECUTION ===
            
            self.logger.info(f"Creating pie chart for {col} ({unique_count} categories)")
            
            fig = px.pie(
                df,
                names=col,
                title=title or f"Composition by {col}",
                color_discrete_sequence=self._get_palette(palette)
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.success = True
            result.metadata = {
                "column": col,
                "categories": unique_count,
                "data_points": len(df),
                "palette": palette,
                "title": title or f"Composition by {col}"
            }
            
            self.logger.info(f"Pie chart created. Quality: {quality_score:.2f}")
            return result
        
        except Exception as e:
            self._handle_error(result, e, ErrorType.RENDER_ERROR)
            return result
    
    def _get_palette(self, palette: str) -> Optional[list]:
        """Get color palette for Plotly."""
        # Return None to use default, or specific palette list
        # This is simplified - can be extended with more palettes
        return None
