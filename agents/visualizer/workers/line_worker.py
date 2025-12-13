"""Line Chart Worker - Time series and continuous data visualization.

Creates line charts for visualizing trends and time-series data with
comprehensive error handling and data quality tracking.

Features:
- Validates required columns and data types
- Detects and reports data quality issues
- Automatic chart customization
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
DEFAULT_MARKERS: bool = True
MIN_DATA_POINTS: int = 2  # Minimum points for line chart

logger = get_logger(__name__)


class LineChartWorker(BaseChartWorker):
    """Worker that creates line charts for time-series data.
    
    Purpose:
        Visualize trends and time-series data using line charts with
        optional markers and full customization support.
    
    Input Format:
        {
            'df': pd.DataFrame,           # Required: DataFrame
            'x_col': str,                 # Required: X-axis column
            'y_col': str,                 # Required: Y-axis column
            'title': Optional[str],       # Optional: Chart title
            'theme': str,                 # Optional: Plotly theme (default: plotly_white)
            'markers': bool               # Optional: Show markers (default: True)
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
                'data_points': int,
                'theme': str,
                'title': str
            }
        }
    
    Quality Score:
        - Starts at 1.0 (perfect)
        - Decreases with null values and duplicates
        - formula: 1.0 - (problematic_cells / total_cells)
    
    Example:
        >>> worker = LineChartWorker()
        >>> df = pd.DataFrame({
        ...     'date': pd.date_range('2024-01-01', periods=100),
        ...     'value': range(100)
        ... })
        >>> result = worker.execute(
        ...     df=df,
        ...     x_col='date',
        ...     y_col='value',
        ...     title='Sales Over Time',
        ...     theme='plotly_white',
        ...     markers=True
        ... )
        >>> result.success
        True
        >>> result.quality_score
        1.0
    
    Raises:
        ValueError: If required parameters missing or invalid
        ImportError: If Plotly not available
    """
    
    def __init__(self) -> None:
        """Initialize LineChartWorker."""
        super().__init__("LineChartWorker", "line")
        self.logger = get_logger(self.__class__.__name__)
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute line chart creation.
        
        Args:
            df: DataFrame to visualize
            x_col: Column for X-axis
            y_col: Column for Y-axis
            title: Optional chart title
            theme: Optional theme name (default: plotly_white)
            markers: Optional show markers (default: True)
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
        markers: bool = kwargs.get('markers', DEFAULT_MARKERS)
        
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
        
        # Validate required columns exist
        is_valid, missing = self._validate_columns(df, [x_col, y_col])
        if not is_valid:
            self._add_error(
                result,
                ErrorType.MISSING_COLUMN,
                f"Required columns missing: {missing}"
            )
            return result
        
        # Validate column types
        col_types = {
            x_col: 'numeric',  # Could be datetime or numeric
            y_col: 'numeric'
        }
        # Be lenient with x_col for time-series (could be datetime or numeric)
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            self._add_error(
                result,
                ErrorType.INVALID_DATA_TYPE,
                f"Y-axis column '{y_col}' must be numeric, got {df[y_col].dtype}"
            )
            return result
        
        # Validate minimum data points
        if len(df) < MIN_DATA_POINTS:
            self._add_error(
                result,
                ErrorType.MISSING_DATA,
                f"Insufficient data points: {len(df)}, minimum {MIN_DATA_POINTS} required"
            )
            return result
        
        # Validate theme parameter
        if not isinstance(theme, str):
            self._add_warning(result, f"Invalid theme type, using default")
            theme = DEFAULT_THEME
        
        # Validate markers parameter
        if not isinstance(markers, bool):
            self._add_warning(result, f"Invalid markers type, using default")
            markers = DEFAULT_MARKERS
        
        # === DATA QUALITY PHASE ===
        
        try:
            # Check data quality
            quality_score = self._check_data_quality(df, result)
            result.quality_score = quality_score
            
            # Track processed rows
            result.rows_processed = len(df)
            result.rows_failed = df[x_col].isna().sum() + df[y_col].isna().sum()
            
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
                f"Creating line chart: {x_col} vs {y_col} "
                f"({len(df)} points, markers={markers})"
            )
            
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=title or f"{y_col} over {x_col}",
                markers=markers,
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
                "data_points": len(df),
                "theme": theme,
                "title": title or f"{y_col} over {x_col}",
                "markers_enabled": markers,
                "null_values": int(df[x_col].isna().sum() + df[y_col].isna().sum()),
                "duplicate_rows": int(df.duplicated().sum())
            }
            
            self.logger.info(
                f"Line chart created successfully. Quality: {quality_score:.2f}"
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
