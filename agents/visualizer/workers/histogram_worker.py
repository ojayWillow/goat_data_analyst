"""Histogram Worker - Distribution visualization.

Creates histograms to visualize the distribution of numeric data.
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
from .config import get_theme
from core.logger import get_logger

# ===== CONSTANTS =====
DEFAULT_THEME: str = "plotly_white"
DEFAULT_BINS: int = 30
MIN_BINS: int = 5
MAX_BINS: int = 200

logger = get_logger(__name__)


class HistogramWorker(BaseChartWorker):
    """Worker that creates histograms for distribution analysis.
    
    Purpose:
        Visualize the distribution of numeric data across bins.
    
    Input Format:
        {
            'df': pd.DataFrame,           # Required
            'col': str,                   # Required: Numeric column
            'bins': int,                  # Optional: Number of bins (default: 30)
            'title': Optional[str],       # Optional
            'theme': str                  # Optional
        }
    
    Example:
        >>> worker = HistogramWorker()
        >>> df = pd.DataFrame({'values': range(1000)})
        >>> result = worker.execute(df=df, col='values', bins=30)
    """
    
    def __init__(self) -> None:
        """Initialize HistogramWorker."""
        super().__init__("HistogramWorker", "histogram")
        self.logger = get_logger(self.__class__.__name__)
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute histogram creation."""
        df: Optional[pd.DataFrame] = kwargs.get('df')
        col: Optional[str] = kwargs.get('col')
        bins: int = kwargs.get('bins', DEFAULT_BINS)
        title: Optional[str] = kwargs.get('title')
        theme: str = kwargs.get('theme', DEFAULT_THEME)
        
        result = self._create_result(quality_score=1.0)
        
        # === VALIDATION ===
        
        if not self._validate_dataframe(df):
            self._add_error(result, ErrorType.MISSING_DATA, "Invalid DataFrame")
            return result
        
        is_valid, missing = self._validate_columns(df, [col])
        if not is_valid:
            self._add_error(result, ErrorType.MISSING_COLUMN, f"Missing: {missing}")
            return result
        
        if not pd.api.types.is_numeric_dtype(df[col]):
            self._add_error(result, ErrorType.INVALID_DATA_TYPE, f"Column must be numeric")
            return result
        
        # Validate bins parameter
        if not isinstance(bins, int) or bins < MIN_BINS or bins > MAX_BINS:
            self._add_warning(result, f"Invalid bins ({bins}), using default")
            bins = DEFAULT_BINS
        
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
            
            self.logger.info(f"Creating histogram for {col} ({bins} bins)")
            
            fig = px.histogram(
                df,
                x=col,
                nbins=bins,
                title=title or f"Distribution of {col}",
                template=get_theme(theme),
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.success = True
            result.metadata = {
                "column": col,
                "bins": bins,
                "data_points": len(df),
                "title": title or f"Distribution of {col}",
                "theme": theme
            }
            
            self.logger.info(f"Histogram created. Quality: {quality_score:.2f}")
            return result
        
        except Exception as e:
            self._handle_error(result, e, ErrorType.RENDER_ERROR)
            return result
