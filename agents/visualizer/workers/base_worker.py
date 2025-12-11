"""Base Worker for Visualizer - Plugin interface for chart types.

This module provides the abstract base class for all chart workers.
Easy to extend: Just inherit BaseChartWorker and implement execute().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum
import time
import pandas as pd

from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class ErrorType(Enum):
    """Error types for visualization."""
    MISSING_DATA = "missing_data"
    INVALID_COLUMN = "invalid_column"
    INVALID_PARAMETER = "invalid_parameter"
    RENDER_ERROR = "render_error"
    MISSING_DEPENDENCY = "missing_dependency"


@dataclass
class WorkerResult:
    """Standardized result format for chart workers."""
    worker: str
    chart_type: str
    success: bool
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    plotly_json: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "worker": self.worker,
            "chart_type": self.chart_type,
            "success": self.success,
            "data": self.data,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
            "plotly_json": self.plotly_json,
        }


class BaseChartWorker(ABC):
    """Base class for all chart workers.
    
    PLUGIN ARCHITECTURE:
    - Extend this class to create new chart types
    - Override execute() with your chart logic
    - Register in workers/__init__.py
    - Done!
    
    Example:
        class MyNewChartWorker(BaseChartWorker):
            def __init__(self):
                super().__init__("MyNewChartWorker", "my_chart")
            
            def execute(self, **kwargs) -> WorkerResult:
                # Your chart logic here
                result = self._create_result()
                # ... create chart ...
                return result
    """
    
    def __init__(self, name: str, chart_type: str):
        """Initialize chart worker.
        
        Args:
            name: Worker name (e.g., "LineChartWorker")
            chart_type: Chart type (e.g., "line")
        """
        self.name = name
        self.chart_type = chart_type
        self.logger = get_logger(self.__class__.__name__)
        self.error_intelligence = ErrorIntelligence()
    
    @abstractmethod
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the chart creation.
        
        Args:
            df: DataFrame to visualize
            **kwargs: Chart-specific parameters
            
        Returns:
            WorkerResult with chart
        """
        pass
    
    def safe_execute(self, **kwargs) -> WorkerResult:
        """Safely execute with error handling.
        
        Args:
            **kwargs: Chart-specific parameters
            
        Returns:
            WorkerResult with proper error handling
        """
        start_time = time.time()
        try:
            result = self.execute(**kwargs)
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            # Track success
            if result.success:
                self.error_intelligence.track_success(
                    agent_name="visualizer",
                    worker_name=self.name,
                    operation="execute",
                    context={"chart_type": self.chart_type}
                )
            else:
                # Track failure if errors exist
                if result.errors:
                    error_msg = "; ".join([str(e.get("message", "")) for e in result.errors])
                    self.error_intelligence.track_error(
                        agent_name="visualizer",
                        worker_name=self.name,
                        error_type="execution_failure",
                        error_message=error_msg,
                        context={"chart_type": self.chart_type}
                    )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Chart execution failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            
            # Track error
            self.error_intelligence.track_error(
                agent_name="visualizer",
                worker_name=self.name,
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "safe_execute", "chart_type": self.chart_type}
            )
            
            return WorkerResult(
                worker=self.name,
                chart_type=self.chart_type,
                success=False,
                data=None,
                errors=[{"type": "execution_error", "message": str(e)}],
                execution_time_ms=duration_ms,
            )
    
    def _create_result(self, metadata: Optional[Dict[str, Any]] = None) -> WorkerResult:
        """Create a new WorkerResult.
        
        Args:
            metadata: Additional metadata
            
        Returns:
            New WorkerResult instance
        """
        return WorkerResult(
            worker=self.name,
            chart_type=self.chart_type,
            success=True,
            metadata=metadata or {},
        )
    
    def _add_error(self, result: WorkerResult, error_type: ErrorType, message: str) -> None:
        """Add error to result.
        
        Args:
            result: WorkerResult
            error_type: Type of error
            message: Error message
        """
        result.errors.append({"type": error_type.value, "message": message})
    
    def _add_warning(self, result: WorkerResult, message: str) -> None:
        """Add warning to result.
        
        Args:
            result: WorkerResult
            message: Warning message
        """
        result.warnings.append(message)
        self.logger.warning(message)
    
    def _validate_dataframe(self, df: pd.DataFrame) -> WorkerResult:
        """Validate DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            WorkerResult or None if valid
        """
        result = self._create_result()
        
        if df is None:
            self._add_error(result, ErrorType.MISSING_DATA, "DataFrame is None")
            result.success = False
            return result
        
        if df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "DataFrame is empty")
            result.success = False
            return result
        
        return None  # Valid
    
    def _validate_columns(self, df: pd.DataFrame, columns: List[str]) -> WorkerResult:
        """Validate that columns exist.
        
        Args:
            df: DataFrame
            columns: Required column names
            
        Returns:
            WorkerResult or None if valid
        """
        result = self._create_result()
        missing = [col for col in columns if col not in df.columns]
        
        if missing:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Missing columns: {missing}")
            result.success = False
            return result
        
        return None  # Valid
