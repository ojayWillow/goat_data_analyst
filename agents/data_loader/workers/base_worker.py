"""Base Worker for Data Loader - Template and protocol for loading workers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum
import time
import pandas as pd

from core.logger import get_logger

logger = get_logger(__name__)


class ErrorType(Enum):
    """Error types for data loading."""
    FILE_NOT_FOUND = "file_not_found"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FORMAT = "unsupported_format"
    LOAD_ERROR = "load_error"
    VALIDATION_ERROR = "validation_error"
    EMPTY_DATA = "empty_data"


@dataclass
class WorkerResult:
    """Standardized result format for data loader workers."""
    worker: str
    task_type: str
    success: bool
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "worker": self.worker,
            "task_type": self.task_type,
            "success": self.success,
            "data": self.data,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
        }


class BaseWorker(ABC):
    """Base class for all data loader workers."""
    
    def __init__(self, name: str):
        """Initialize worker.
        
        Args:
            name: Worker name
        """
        self.name = name
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the loading task.
        
        Args:
            **kwargs: Task-specific parameters
            
        Returns:
            WorkerResult
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
                task_type="data_loading",
                success=False,
                data=None,
                errors=[{"type": "execution_error", "message": str(e)}],
                execution_time_ms=duration_ms,
            )
    
    def _create_result(self, task_type: str, metadata: Optional[Dict[str, Any]] = None) -> WorkerResult:
        """Create a new WorkerResult.
        
        Args:
            task_type: Type of task
            metadata: Additional metadata
            
        Returns:
            New WorkerResult instance
        """
        return WorkerResult(
            worker=self.name,
            task_type=task_type,
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
