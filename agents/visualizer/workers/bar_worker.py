"""Bar Chart Worker - Categorical data visualization.

Creates bar charts for comparing values across categories with
comprehensive error handling and data quality tracking.

Features:
- Validates categorical X-axis and numeric Y-axis
- Detects and reports data quality issues
- Optional color/grouping column support
- Structured error reporting
"""

from typing import Any, Dict, Optional
import pandas as pd
import logging
from datetime import datetime, timezone

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_worker import (
    BaseChartWorker, WorkerResult, ErrorType, DataQualityIssue
)
from .config import get_theme, get_palette
from agents.error_intelligence.main import ErrorIntelligence
from core.logger import get_logger

# ===== CONSTANTS =====
DEFAULT_THEME: str = "plotly_white"
MAX_CATEGORIES: int = 100  # Reasonable limit for bar chart
MIN_DATA_POINTS: int = 1

logger = get_logger(__name__)


class BarChartWorker(BaseChartWorker):
    """Worker that creates bar charts for categorical data.
    
    Purpose:
        Visualize numeric values across categories using bar charts with
        optional color/grouping support for multi-dimensional analysis.
    
    Input Format:
        {
            'df': pd.DataFrame,           # Required: DataFrame
            'x_col': str,                 # Required: Categorical X-axis column
            'y_col': str,                 # Required: Numeric Y-axis column
            'title': Optional[str],       # Optional: Chart title
            'theme': str,                 # Optional: Plotly theme (default: plotly_white)
            'color': Optional[str]        # Optional: Color/grouping column
        }
    
    Output Format:
        {
            'success': bool,              # Execution succeeded
            'data': plotly.Figure,        # Plotly figure object
            'quality_score': float,       # Data quality (0-1)
            'errors': List[Dict],         # Any errors encountered
            'warnings': List[str],        # Non-fatal warnings
            'data_quality_issues': [],    # Detected data quality problems
            'metadata': {
                'x_column': str,
                'y_column': str,
                'categories': int,
                'theme': str,
                'title': str,
                'color_column': Optional[str]
            }
        }
    
    Quality Score:
        - Starts at 1.0 (perfect)
        - Decreases with null values and duplicates
        - formula: 1.0 - (problematic_cells / total_cells)
    
    Example:
        >>> worker = BarChartWorker()
        >>> df = pd.DataFrame({
        ...     'region': ['North', 'South', 'East', 'West'],
        ...     'sales': [100, 150, 200, 175]
        ... })
        >>> result = worker.execute(
        ...     df=df,
        ...     x_col='region',
        ...     y_col='sales',
        ...     title='Sales by Region',
        ...     theme='plotly_white',
        ...     color=None
        ... )
        >>> result.success
        True
    
    Raises:
        ValueError: If required parameters missing or invalid
        ImportError: If Plotly not available
    """
    
    def __init__(self) -> None:
        """Initialize BarChartWorker."""
        super().__init__("BarChartWorker", "bar")
        self.logger = get_logger(self.__class__.__name__)
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute bar chart creation.
        
        Args:
            df: DataFrame to visualize
            x_col: Column for X-axis (categorical)
            y_col: Column for Y-axis (numeric)
            title: Optional chart title
            theme: Optional theme name (default: plotly_white)
            color: Optional color/grouping column
            **kwargs: Additional keyword arguments
            
        Returns:
            WorkerResult with chart or error information
        """
        # Extract parameters
        df: Optional[pd.DataFrame] = kwargs.get('df')
        x_col: Optional[str] = kwargs.get('x_col')
        y_col: Optional[str] = kwargs.get('y_col')
        title: Optional[str] = kwargs.get('title')
        theme: str = kwargs.get('theme', DEFAULT_THEME)
        color: Optional[str] = kwargs.get('color')
        
        # Create result
        result = self._create_result(quality_score=1.0)
        
        # === VALIDATION PHASE ===
        
        # Validate DataFrame
        if not self._validate_dataframe(df):
            self._add_error(
                result,
                ErrorType.MISSING_DATA,
                "DataFrame is None, empty, or invalid"
            )
            return result
        
        # Validate required columns
        required_cols = [x_col, y_col]
        if color:
            required_cols.append(color)
        
        is_valid, missing = self._validate_columns(df, required_cols)
        if not is_valid:
            self._add_error(
                result,
                ErrorType.MISSING_COLUMN,
                f"Required columns missing: {missing}"
            )
            return result
        
        # Validate Y-axis is numeric
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            self._add_error(
                result,
                ErrorType.INVALID_DATA_TYPE,
                f"Y-axis column '{y_col}' must be numeric, got {df[y_col].dtype}"
            )
            return result
        
        # Check number of categories
        unique_x = df[x_col].nunique()
        if unique_x > MAX_CATEGORIES:
            self._add_warning(
                result,
                f"Many categories ({unique_x} > {MAX_CATEGORIES}): "
                f"chart may be crowded. Consider filtering data."
            )
        
        # Validate theme parameter
        if not isinstance(theme, str):
            self._add_warning(result, f"Invalid theme type, using default")
            theme = DEFAULT_THEME
        
        # === DATA QUALITY PHASE ===
        
        try:
            # Check data quality
            quality_score = self._check_data_quality(df, result)
            result.quality_score = quality_score
            
            # Track processed rows
            result.rows_processed = len(df)
            result.rows_failed = df[y_col].isna().sum()
            if color:
                result.rows_failed += df[color].isna().sum()
            
            # === EXECUTION PHASE ===
            
            # Check Plotly availability
            if not PLOTLY_AVAILABLE:
                self._add_error(
                    result,
                    ErrorType.MISSING_DEPENDENCY,
                    "Plotly library not installed. Install with: pip install plotly"
                )
                return result
            
            # Create chart
            self.logger.info(
                f"Creating bar chart: {x_col} vs {y_col} "
                f"({unique_x} categories, color={color is not None})"
            )
            
            fig = px.bar(
                df,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} by {x_col}",
                color=color,
                template=get_theme(theme),
            )
            
            # === SUCCESS PHASE ===
            
            # Populate result
            result.data = fig
            result.plotly_json = fig.to_json()
            result.success = True
            result.metadata = {
                "x_column": x_col,
                "y_column": y_col,
                "categories": unique_x,
                "theme": theme,
                "title": title or f"{y_col} by {x_col}",
                "color_column": color,
                "null_values": int(df[y_col].isna().sum()),
                "duplicate_rows": int(df.duplicated().sum())
            }
            
            self.logger.info(
                f"Bar chart created successfully. Quality: {quality_score:.2f}"
            )
            return result
        
        except Exception as e:
            # Handle unexpected errors
            self._handle_error(
                result,
                e,
                ErrorType.RENDER_ERROR
            )
            return result
