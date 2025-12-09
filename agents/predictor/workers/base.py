"""Base class for Predictor workers - Template and protocol for all prediction workers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import time
from datetime import datetime

from core.logger import get_logger

logger = get_logger(__name__)


class ErrorType(Enum):
    """Error types for predictor workers."""
    MISSING_DATA = "missing_data"
    INVALID_COLUMN = "invalid_column"
    INVALID_PARAMETER = "invalid_parameter"
    INSUFFICIENT_DATA = "insufficient_data"
    PROCESSING_ERROR = "processing_error"
    MODEL_ERROR = "model_error"
    VALIDATION_ERROR = "validation_error"


@dataclass
class WorkerResult:
    """Standardized result format for all predictor workers."""
    worker: str
    task_type: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "worker": self.worker,
            "task_type": self.task_type,
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
        }


class Base(ABC):
    """Base class for all predictor workers.
    
    Every predictor worker extends this class and implements:
    - execute(): The actual prediction logic
    - Validation of inputs
    - Standardized error handling
    - Consistent result formatting
    """
    
    def __init__(self, name: str):
        """Initialize worker.
        
        Args:
            name: Worker name (e.g., 'LinearRegression')
        """
        self.name = name
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the prediction task.
        
        Args:
            **kwargs: Task-specific parameters (df, features, target, etc.)
            
        Returns:
            WorkerResult with predictions or errors
        """
        pass
    
    def safe_execute(self, **kwargs) -> WorkerResult:
        """Safely execute with error handling.
        
        Args:
            **kwargs: Task-specific parameters
            
        Returns:
            WorkerResult with proper error handling
        """
        start_time = time.time()
        try:
            result = self.execute(**kwargs)
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            self.logger.error(f"Worker execution failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            return WorkerResult(
                worker=self.name,
                task_type="prediction",
                success=False,
                errors=[{"type": "execution_error", "message": str(e)}],
                execution_time_ms=duration_ms,
            )
    
    def _create_result(
        self,
        task_type: str,
        quality_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkerResult:
        """Create a new WorkerResult object.
        
        Args:
            task_type: Type of prediction task
            quality_score: Quality score (0-1)
            metadata: Additional metadata
            
        Returns:
            New WorkerResult instance
        """
        return WorkerResult(
            worker=self.name,
            task_type=task_type,
            success=True,
            quality_score=quality_score,
            metadata=metadata or {},
            timestamp=datetime.now().isoformat(),
        )
    
    def _add_error(
        self,
        result: WorkerResult,
        error_type: ErrorType,
        message: str,
        severity: str = "error",
    ) -> None:
        """Add error to result.
        
        Args:
            result: WorkerResult to add error to
            error_type: Type of error
            message: Error message
            severity: "error" or "warning"
        """
        if severity == "warning":
            result.warnings.append(message)
        else:
            result.errors.append({
                "type": error_type.value,
                "message": message,
            })
    
    def _add_warning(self, result: WorkerResult, message: str) -> None:
        """Add warning to result.
        
        Args:
            result: WorkerResult to add warning to
            message: Warning message
        """
        result.warnings.append(message)
        self.logger.warning(message)
