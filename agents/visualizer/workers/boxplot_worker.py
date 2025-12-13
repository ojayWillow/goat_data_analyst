"""Box Plot Worker - Quartile and distribution visualization.

Creates box plots for visualizing quartiles and outliers.
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

logger = get_logger(__name__)


class BoxPlotWorker(BaseChartWorker):
    """Worker that creates box plots for quartile analysis.
    
    Purpose:
        Visualize distribution, quartiles, and outliers for numeric data.
    
    Input Format:
        {
            'df': pd.DataFrame,           # Required
            'y_col': str,                 # Required: Numeric column
            'x_col': Optional[str],       # Optional: Grouping column
            'title': Optional[str],       # Optional
            'theme': str                  # Optional
        }
    
    Example:
        >>> worker = BoxPlotWorker()
        >>> df = pd.DataFrame({
        ...     'value': range(100),
        ...     'category': ['A']*50 + ['B']*50
        ... })
        >>> result = worker.execute(df=df, y_col='value', x_col='category')
    """
    
    def __init__(self) -> None:
        """Initialize BoxPlotWorker."""
        super().__init__("BoxPlotWorker", "boxplot")
        self.logger = get_logger(self.__class__.__name__)
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute box plot creation."""
        df: Optional[pd.DataFrame] = kwargs.get('df')
        y_col: Optional[str] = kwargs.get('y_col')
        x_col: Optional[str] = kwargs.get('x_col')
        title: Optional[str] = kwargs.get('title')
        theme: str = kwargs.get('theme', DEFAULT_THEME)
        
        result = self._create_result(quality_score=1.0)
        
        # === VALIDATION ===
        
        if not self._validate_dataframe(df):
            self._add_error(result, ErrorType.MISSING_DATA, "Invalid DataFrame")
            return result
        
        required_cols = [y_col]
        if x_col:
            required_cols.append(x_col)
        
        is_valid, missing = self._validate_columns(df, required_cols)
        if not is_valid:
            self._add_error(result, ErrorType.MISSING_COLUMN, f"Missing: {missing}")
            return result
        
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            self._add_error(result, ErrorType.INVALID_DATA_TYPE, f"Y column must be numeric")
            return result
        
        # === DATA QUALITY ===
        
        try:
            quality_score = self._check_data_quality(df, result)
            result.quality_score = quality_score
            result.rows_processed = len(df)
            result.rows_failed = df[y_col].isna().sum()
            if x_col:
                result.rows_failed += df[x_col].isna().sum()
            
            if not PLOTLY_AVAILABLE:
                self._add_error(result, ErrorType.MISSING_DEPENDENCY, "Plotly not installed")
                return result
            
            # === EXECUTION ===
            
            self.logger.info(f"Creating boxplot for {y_col}" + (f" by {x_col}" if x_col else ""))
            
            fig = px.box(
                df,
                y=y_col,
                x=x_col,
                title=title or f"Distribution of {y_col}",
                template=get_theme(theme),
            )
            
            result.data = fig
            result.plotly_json = fig.to_json()
            result.success = True
            result.metadata = {
                "y_column": y_col,
                "x_column": x_col,
                "data_points": len(df),
                "title": title or f"Distribution of {y_col}",
                "theme": theme
            }
            
            self.logger.info(f"Boxplot created. Quality: {quality_score:.2f}")
            return result
        
        except Exception as e:
            self._handle_error(result, e, ErrorType.RENDER_ERROR)
            return result
