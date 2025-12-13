"""Scatter Plot Worker - Correlation and relationship visualization.

Creates scatter plots for analyzing relationships between two numeric variables
with optional size and color dimensions.
"""

from typing import Any, Dict, Optional
import pandas as pd
import logging

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import (
    BaseChartWorker, WorkerResult, ErrorType
)
from .config import get_theme
from core.logger import get_logger

# ===== CONSTANTS =====
DEFAULT_THEME: str = "plotly_white"
MIN_DATA_POINTS: int = 2

logger = get_logger(__name__)


class ScatterPlotWorker(BaseChartWorker):
    """Worker that creates scatter plots.
    
    Purpose:
        Visualize relationships and correlations between two numeric variables
        with optional size and color dimensions.
    
    Input Format:
        {
            'df': pd.DataFrame,           # Required: DataFrame
            'x_col': str,                 # Required: X-axis column (numeric)
            'y_col': str,                 # Required: Y-axis column (numeric)
            'title': Optional[str],       # Optional: Chart title
            'theme': str,                 # Optional: Theme (default: plotly_white)
            'color_col': Optional[str],   # Optional: Color dimension
            'size_col': Optional[str]     # Optional: Size dimension
        }
    
    Quality Score:
        Starts at 1.0, decreases with data quality issues.
    
    Example:
        >>> worker = ScatterPlotWorker()
        >>> df = pd.DataFrame({
        ...     'x': range(100),
        ...     'y': [i*2 + 10 for i in range(100)],
        ...     'category': ['A']*50 + ['B']*50
        ... })
        >>> result = worker.execute(
        ...     df=df,
        ...     x_col='x',
        ...     y_col='y',
        ...     color_col='category'
        ... )
    """
    
    def __init__(self) -> None:
        """Initialize ScatterPlotWorker."""
        super().__init__("ScatterPlotWorker", "scatter")
        self.logger = get_logger(self.__class__.__name__)
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute scatter plot creation.
        
        Args:
            df: DataFrame to visualize
            x_col: X-axis column (numeric)
            y_col: Y-axis column (numeric)
            title: Optional chart title
            theme: Optional theme (default: plotly_white)
            color_col: Optional color column
            size_col: Optional size column
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with chart or error information
        """
        df: Optional[pd.DataFrame] = kwargs.get('df')
        x_col: Optional[str] = kwargs.get('x_col')
        y_col: Optional[str] = kwargs.get('y_col')
        title: Optional[str] = kwargs.get('title')
        theme: str = kwargs.get('theme', DEFAULT_THEME)
        color_col: Optional[str] = kwargs.get('color_col')
        size_col: Optional[str] = kwargs.get('size_col')
        
        result = self._create_result(quality_score=1.0)
        
        # === VALIDATION PHASE ===
        
        if not self._validate_dataframe(df):
            self._add_error(result, ErrorType.MISSING_DATA, "Invalid DataFrame")
            return result
        
        required_cols = [x_col, y_col]
        if color_col:
            required_cols.append(color_col)
        if size_col:
            required_cols.append(size_col)
        
        is_valid, missing = self._validate_columns(df, required_cols)
        if not is_valid:
            self._add_error(result, ErrorType.MISSING_COLUMN, f"Missing: {missing}")
            return result
        
        # Validate numeric axes
        if not pd.api.types.is_numeric_dtype(df[x_col]):
            self._add_error(result, ErrorType.INVALID_DATA_TYPE, f"X-axis must be numeric")
            return result
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            self._add_error(result, ErrorType.INVALID_DATA_TYPE, f"Y-axis must be numeric")
            return result
        
        if size_col and not pd.api.types.is_numeric_dtype(df[size_col]):
            self._add_warning(result, f"Size column not numeric, ignoring")
            size_col = None
        
        if len(df) < MIN_DATA_POINTS:
            self._add_error(result, ErrorType.MISSING_DATA, f"Need >= {MIN_DATA_POINTS} points")
            return result
        
        # === DATA QUALITY PHASE ===
        
        try:
            quality_score = self._check_data_quality(df, result)
            result.quality_score = quality_score
            result.rows_processed = len(df)
            result.rows_failed = df[x_col].isna().sum() + df[y_col].isna().sum()
            
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                return result
            
            # === EXECUTION PHASE ===
            
            self.logger.info(f"Creating scatter: {x_col} vs {y_col}")
            
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} vs {x_col}",
                color=color_col,
                size=size_col,
                template=get_theme(theme),
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.success = True
            result.metadata = {
                "x_column": x_col,
                "y_column": y_col,
                "data_points": len(df),
                "color_column": color_col,
                "size_column": size_col,
                "theme": theme,
                "title": title or f"{y_col} vs {x_col}"
            }
            
            self.logger.info(f"Scatter plot created. Quality: {quality_score:.2f}")
            return result
        
        except Exception as e:
            self._handle_error(result, e, ErrorType.RENDER_ERROR)
            return result
