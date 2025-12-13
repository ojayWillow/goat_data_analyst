"""Base Worker for Visualizer - Plugin interface for chart types.

This module provides the abstract base class for all chart workers with:
- Comprehensive error tracking and classification
- Data quality scoring (0-1 range)
- Structured error intelligence integration
- Full type hints and validation
- Complete docstrings

Easy to extend: Just inherit BaseChartWorker and implement execute().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Tuple
from enum import Enum
from datetime import datetime, timezone
import time
import pandas as pd
import logging

from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

# ===== CONSTANTS =====
MIN_ROWS_REQUIRED: int = 1
MAX_COLS_ALLOWED: int = 10000
QUALITY_THRESHOLD: float = 0.8
EXECUTION_TIMEOUT_SECONDS: float = 30.0

logger = get_logger(__name__)


class ErrorType(Enum):
    """Standard error types for visualization workers."""
    
    # Data Quality Errors
    MISSING_DATA = "missing_data"
    NULL_VALUE_ERROR = "null_value_error"
    EMPTY_DATAFRAME = "empty_dataframe"
    
    # Column/Structure Errors
    INVALID_COLUMN = "invalid_column"
    MISSING_COLUMN = "missing_column"
    INVALID_DATA_TYPE = "invalid_data_type"
    
    # Parameter Errors
    INVALID_PARAMETER = "invalid_parameter"
    MISSING_PARAMETER = "missing_parameter"
    
    # Dependency Errors
    MISSING_DEPENDENCY = "missing_dependency"
    
    # Rendering Errors
    RENDER_ERROR = "render_error"
    PLOT_GENERATION_ERROR = "plot_generation_error"
    
    # System Errors
    TIMEOUT_ERROR = "timeout_error"
    MEMORY_ERROR = "memory_error"
    UNEXPECTED_ERROR = "unexpected_error"


class DataQualityIssue:
    """Record a single data quality issue."""
    
    def __init__(
        self,
        issue_type: str,
        column: Optional[str] = None,
        row_count: int = 0,
        sample_value: Optional[Any] = None,
        severity: str = "warning"  # warning, error, critical
    ) -> None:
        """Initialize quality issue.
        
        Args:
            issue_type: Type of issue (e.g., 'null_values')
            column: Affected column name
            row_count: Number of rows affected
            sample_value: Sample problematic value
            severity: Issue severity level
        """
        self.issue_type = issue_type
        self.column = column
        self.row_count = row_count
        self.sample_value = sample_value
        self.severity = severity
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type,
            "column": self.column,
            "rows_affected": self.row_count,
            "sample": str(self.sample_value)[:100],
            "severity": self.severity,
            "timestamp": self.timestamp
        }


class ErrorRecord:
    """Complete error information for analysis."""
    
    def __init__(
        self,
        error_type: ErrorType,
        worker_name: str,
        message: str,
        column_name: Optional[str] = None,
        sample_data: Optional[Any] = None,
        expected_value: Optional[Any] = None,
        actual_value: Optional[Any] = None
    ) -> None:
        """Initialize error record.
        
        Args:
            error_type: StandardErrorType enum
            worker_name: Name of worker that encountered error
            message: Human-readable error message
            column_name: Affected column (if applicable)
            sample_data: Sample data for diagnosis
            expected_value: What was expected
            actual_value: What was actually found
        """
        self.error_type = error_type
        self.worker_name = worker_name
        self.message = message
        self.column_name = column_name
        self.sample_data = sample_data
        self.expected_value = expected_value
        self.actual_value = actual_value
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for tracking."""
        return {
            "error_type": self.error_type.value,
            "worker": self.worker_name,
            "message": self.message,
            "column": self.column_name,
            "sample": str(self.sample_data)[:100] if self.sample_data else None,
            "expected": str(self.expected_value),
            "actual": str(self.actual_value),
            "timestamp": self.timestamp
        }


@dataclass
class WorkerResult:
    """Standardized result format for chart workers.
    
    Attributes:
        worker: Worker name
        chart_type: Type of chart (line, bar, scatter, etc.)
        success: Whether execution succeeded
        data: Plotly Figure object
        quality_score: Data quality score (0-1)
        rows_processed: Number of rows successfully processed
        rows_failed: Number of rows that failed
        metadata: Execution metadata
        errors: List of error records
        warnings: Non-fatal warnings
        execution_time_ms: Execution duration in milliseconds
        plotly_json: JSON representation of Plotly figure
    """
    worker: str
    chart_type: str
    success: bool
    data: Any = None
    quality_score: float = 0.0
    rows_processed: int = 0
    rows_failed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data_quality_issues: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    plotly_json: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.
        
        Returns:
            Dictionary representation of result
        """
        return {
            "worker": self.worker,
            "chart_type": self.chart_type,
            "success": self.success,
            "data": self.data,
            "quality_score": self.quality_score,
            "rows_processed": self.rows_processed,
            "rows_failed": self.rows_failed,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "data_quality_issues": self.data_quality_issues,
            "execution_time_ms": self.execution_time_ms,
            "plotly_json": self.plotly_json,
        }


class BaseChartWorker(ABC):
    """Base class for all chart workers with A+ standards.
    
    PLUGIN ARCHITECTURE:
    - Extend this class to create new chart types
    - Override execute() with your chart logic
    - Register in workers/__init__.py
    - Automatic error handling and quality tracking
    
    Features:
    - Comprehensive input validation
    - Error intelligence integration
    - Data quality scoring
    - Structured error reporting
    - Timeout protection
    
    Example:
        class MyChartWorker(BaseChartWorker):
            def __init__(self):
                super().__init__("MyChartWorker", "my_chart")
            
            def execute(self, **kwargs) -> WorkerResult:
                df = kwargs.get('df')
                result = self._create_result()
                
                # Validate
                if not self._validate_dataframe(df):
                    return result
                
                try:
                    # Your chart logic
                    fig = self._create_chart(df)
                    result.data = fig
                    result.success = True
                except Exception as e:
                    self._handle_error(result, e)
                
                return result
    """
    
    def __init__(self, name: str, chart_type: str) -> None:
        """Initialize chart worker.
        
        Args:
            name: Worker name (e.g., "LineChartWorker")
            chart_type: Chart type (e.g., "line")
            
        Raises:
            ValueError: If name or chart_type is empty
        """
        if not name or not isinstance(name, str):
            raise ValueError("Worker name must be non-empty string")
        if not chart_type or not isinstance(chart_type, str):
            raise ValueError("Chart type must be non-empty string")
        
        self.name: str = name
        self.chart_type: str = chart_type
        self.version: str = "1.0.0"
        self.logger: logging.Logger = get_logger(self.__class__.__name__)
        self.error_intelligence: ErrorIntelligence = ErrorIntelligence()
        self.errors: List[ErrorRecord] = []
        self.warnings: List[str] = []
    
    @abstractmethod
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the chart creation.
        
        Args:
            df: DataFrame to visualize
            **kwargs: Chart-specific parameters
            
        Returns:
            WorkerResult with chart or error information
        """
        pass
    
    def safe_execute(self, **kwargs) -> WorkerResult:
        """Safely execute with comprehensive error handling.
        
        Implements:
        - Timeout protection
        - Error tracking
        - Quality scoring
        - Structured logging
        
        Args:
            **kwargs: Chart-specific parameters
            
        Returns:
            WorkerResult with proper error handling
        """
        start_time = time.time()
        self.errors = []
        self.warnings = []
        
        try:
            # Execute worker
            result = self.execute(**kwargs)
            
            # Calculate execution time
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            # Check timeout
            if result.execution_time_ms > EXECUTION_TIMEOUT_SECONDS * 1000:
                self.logger.warning(
                    f"{self.name} exceeded timeout: "
                    f"{result.execution_time_ms}ms > {EXECUTION_TIMEOUT_SECONDS * 1000}ms"
                )
                result.warnings.append(
                    f"Execution took {result.execution_time_ms:.0f}ms "
                    f"(timeout: {EXECUTION_TIMEOUT_SECONDS * 1000}ms)"
                )
            
            # Track success
            if result.success:
                self.error_intelligence.track_success(
                    agent_name="visualizer",
                    worker_name=self.name,
                    operation="execute",
                    context={
                        "chart_type": self.chart_type,
                        "quality_score": result.quality_score,
                        "execution_time_ms": result.execution_time_ms
                    }
                )
                self.logger.info(
                    f"{self.name} succeeded: quality={result.quality_score:.2f}, "
                    f"time={result.execution_time_ms:.0f}ms"
                )
            else:
                # Track failure
                if result.errors:
                    error_types = [e.get("error_type", "unknown") for e in result.errors]
                    error_msg = "; ".join(error_types)
                    self.error_intelligence.track_error(
                        agent_name="visualizer",
                        worker_name=self.name,
                        error_type="execution_failure",
                        error_message=error_msg,
                        context={"chart_type": self.chart_type}
                    )
                    self.logger.error(
                        f"{self.name} failed with errors: {error_msg}"
                    )
            
            return result
        
        except Exception as e:
            # Unexpected error
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"{self.name} failed with exception: {type(e).__name__}: {str(e)}"
            )
            
            # Track error
            self.error_intelligence.track_error(
                agent_name="visualizer",
                worker_name=self.name,
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "safe_execute", "chart_type": self.chart_type}
            )
            
            # Return error result
            return WorkerResult(
                worker=self.name,
                chart_type=self.chart_type,
                success=False,
                data=None,
                quality_score=0.0,
                rows_processed=0,
                rows_failed=0,
                errors=[{
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }],
                execution_time_ms=duration_ms,
            )
    
    def _create_result(
        self,
        metadata: Optional[Dict[str, Any]] = None,
        quality_score: float = 1.0
    ) -> WorkerResult:
        """Create a new WorkerResult.
        
        Args:
            metadata: Additional metadata
            quality_score: Initial quality score (default 1.0)
            
        Returns:
            New WorkerResult instance
        """
        return WorkerResult(
            worker=self.name,
            chart_type=self.chart_type,
            success=True,
            quality_score=quality_score,
            metadata=metadata or {},
        )
    
    def _add_error(
        self,
        result: WorkerResult,
        error_type: ErrorType,
        message: str,
        column: Optional[str] = None
    ) -> None:
        """Add error to result.
        
        Args:
            result: WorkerResult to update
            error_type: Type of error
            message: Error message
            column: Affected column (if applicable)
        """
        error_dict = {
            "error_type": error_type.value,
            "message": message,
            "column": column,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        result.errors.append(error_dict)
        result.success = False
        self.logger.error(f"{self.name}: {message}")
    
    def _add_warning(self, result: WorkerResult, message: str) -> None:
        """Add non-fatal warning to result.
        
        Args:
            result: WorkerResult to update
            message: Warning message
        """
        result.warnings.append(message)
        self.logger.warning(f"{self.name}: {message}")
    
    def _add_quality_issue(
        self,
        result: WorkerResult,
        issue: DataQualityIssue
    ) -> None:
        """Add data quality issue.
        
        Args:
            result: WorkerResult to update
            issue: DataQualityIssue instance
        """
        result.data_quality_issues.append(issue.to_dict())
    
    def _validate_dataframe(self, df: Optional[pd.DataFrame]) -> bool:
        """Validate DataFrame is present and not empty.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if valid, False otherwise
        """
        if df is None:
            self.logger.error(f"{self.name}: DataFrame is None")
            return False
        
        if not isinstance(df, pd.DataFrame):
            self.logger.error(
                f"{self.name}: Expected DataFrame, got {type(df).__name__}"
            )
            return False
        
        if df.empty:
            self.logger.error(f"{self.name}: DataFrame is empty")
            return False
        
        if len(df) < MIN_ROWS_REQUIRED:
            self.logger.error(
                f"{self.name}: Insufficient data ({len(df)} rows, "
                f"minimum {MIN_ROWS_REQUIRED})"
            )
            return False
        
        if len(df.columns) > MAX_COLS_ALLOWED:
            self.logger.error(
                f"{self.name}: Too many columns ({len(df.columns)}, "
                f"maximum {MAX_COLS_ALLOWED})"
            )
            return False
        
        return True
    
    def _validate_columns(
        self,
        df: pd.DataFrame,
        columns: List[str],
        required: bool = True
    ) -> Tuple[bool, List[str]]:
        """Validate that columns exist in DataFrame.
        
        Args:
            df: DataFrame to check
            columns: Required column names
            required: If True, all columns must exist
            
        Returns:
            Tuple of (is_valid, missing_columns)
        """
        missing = [col for col in columns if col not in df.columns]
        
        if missing:
            self.logger.error(
                f"{self.name}: Missing columns {missing}. "
                f"Available: {list(df.columns)}"
            )
            return (False, missing) if required else (True, missing)
        
        return True, []
    
    def _validate_column_types(
        self,
        df: pd.DataFrame,
        column_types: Dict[str, str]
    ) -> bool:
        """Validate column data types.
        
        Args:
            df: DataFrame to check
            column_types: Dict of {column: expected_dtype}
                Examples: 'numeric', 'string', 'datetime'
                
        Returns:
            True if all columns match expected types
        """
        for col, expected_type in column_types.items():
            if col not in df.columns:
                self.logger.error(f"{self.name}: Column '{col}' not found")
                return False
            
            col_dtype = df[col].dtype
            
            # Check type match
            type_match = False
            if expected_type == "numeric":
                type_match = pd.api.types.is_numeric_dtype(col_dtype)
            elif expected_type == "string":
                type_match = pd.api.types.is_string_dtype(col_dtype)
            elif expected_type == "datetime":
                type_match = pd.api.types.is_datetime64_any_dtype(col_dtype)
            elif expected_type == "categorical":
                type_match = pd.api.types.is_categorical_dtype(col_dtype)
            
            if not type_match:
                self.logger.error(
                    f"{self.name}: Column '{col}' has type {col_dtype}, "
                    f"expected {expected_type}"
                )
                return False
        
        return True
    
    def _check_data_quality(
        self,
        df: pd.DataFrame,
        result: WorkerResult
    ) -> float:
        """Analyze data quality and calculate score.
        
        Checks for:
        - Null values
        - Duplicates
        - Data type mismatches
        - Extreme values
        
        Args:
            df: DataFrame to analyze
            result: WorkerResult to update
            
        Returns:
            Quality score (0-1)
        """
        quality_score = 1.0
        total_cells = df.size
        problematic_cells = 0
        
        # Check for nulls
        null_count = df.isna().sum().sum()
        if null_count > 0:
            problematic_cells += null_count
            null_pct = (null_count / total_cells) * 100
            issue = DataQualityIssue(
                issue_type="null_values",
                row_count=df.isna().any(axis=1).sum(),
                sample_value=f"{null_pct:.1f}% null",
                severity="warning" if null_pct < 10 else "error"
            )
            self._add_quality_issue(result, issue)
            self.logger.warning(f"{self.name}: Found {null_count} null values ({null_pct:.1f}%)")
        
        # Check for duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            issue = DataQualityIssue(
                issue_type="duplicates",
                row_count=dup_count,
                sample_value=f"{(dup_count/len(df))*100:.1f}% duplicates",
                severity="warning"
            )
            self._add_quality_issue(result, issue)
            self.logger.warning(f"{self.name}: Found {dup_count} duplicate rows")
        
        # Calculate quality score
        if total_cells > 0:
            quality_score = 1.0 - (problematic_cells / total_cells)
        
        result.quality_score = max(0.0, min(1.0, quality_score))
        return result.quality_score
    
    def _handle_error(
        self,
        result: WorkerResult,
        exception: Exception,
        error_type: ErrorType = ErrorType.UNEXPECTED_ERROR
    ) -> None:
        """Handle exception and update result.
        
        Args:
            result: WorkerResult to update
            exception: Exception that occurred
            error_type: Type of error to record
        """
        error_msg = str(exception)
        self._add_error(result, error_type, error_msg)
        result.success = False
        result.quality_score = 0.0
        self.logger.error(f"{self.name} error: {error_type.value}: {error_msg}")
