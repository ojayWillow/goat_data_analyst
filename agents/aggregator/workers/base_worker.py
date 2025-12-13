"""BaseWorker - Abstract base class for Aggregator workers.

Defines the common language/protocol that all Aggregator workers use.
Ensures consistent quality standards and error reporting.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
import traceback
import time

from core.logger import get_logger

logger = get_logger(__name__)


class ErrorType(Enum):
    """Standard error types across all workers."""
    DATA_VALIDATION_ERROR = "data_validation_error"
    COMPUTATION_ERROR = "computation_error"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    MISSING_DATA = "missing_data"
    INVALID_PARAMETER = "invalid_parameter"
    VALIDATION_ERROR = "validation_error"  # For data validation issues
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class WorkerError:
    """Standardized error report from a worker."""
    
    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        severity: str = "warning",  # info, warning, error, critical
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ):
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.suggestion = suggestion
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.error_type.value,
            "message": self.message,
            "severity": self.severity,
            "details": self.details,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp,
        }


class WorkerResult:
    """Standardized result from a worker - COMMON LANGUAGE.
    
    Every worker returns this format.
    Agent validates and aggregates these results.
    """
    
    def __init__(
        self,
        worker_name: str,
        task_type: str,
        success: bool = True,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[List[WorkerError]] = None,
        warnings: Optional[List[str]] = None,
        quality_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.worker_name = worker_name
        self.task_type = task_type
        self.success = success
        self.data = data or {}
        self.errors = errors or []
        self.warnings = warnings or []
        self.quality_score = max(0, min(1, quality_score))  # Clamp 0-1
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.execution_time_ms = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "worker": self.worker_name,
            "task_type": self.task_type,
            "success": self.success,
            "data": self.data,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings,
            "quality_score": round(self.quality_score, 3),
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
        }
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def has_critical_errors(self) -> bool:
        return any(e.severity == "critical" for e in self.errors)
    
    def get_error_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for error in self.errors:
            error_type = error.error_type.value
            summary[error_type] = summary.get(error_type, 0) + 1
        return summary


class BaseWorker(ABC):
    """Abstract base class for all Aggregator workers.
    
    Defines protocol all workers must follow.
    Ensures consistent quality standards and error handling.
    """
    
    def __init__(self, worker_name: str):
        self.worker_name = worker_name
        self.logger = get_logger(f"aggregator.workers.{worker_name}")
        self.logger.info(f"Worker initialized: {worker_name}")
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute the worker's task.
        
        Must be implemented by subclasses.
        Must always return WorkerResult object.
        
        Args:
            **kwargs: Task-specific parameters
            
        Returns:
            WorkerResult with standardized format
        """
        pass
    
    def _create_result(
        self,
        success: bool = True,
        data: Optional[Dict[str, Any]] = None,
        task_type: str = "generic",
        quality_score: float = 1.0,
        **kwargs: Any
    ) -> WorkerResult:
        """Create a standardized result."""
        return WorkerResult(
            worker_name=self.worker_name,
            task_type=task_type,
            success=success,
            data=data,
            quality_score=quality_score,
            **kwargs
        )
    
    def _add_error(
        self,
        result: WorkerResult,
        error_type: ErrorType,
        message: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add error to result."""
        error = WorkerError(
            error_type=error_type,
            message=message,
            severity=severity,
            details=details,
            suggestion=suggestion,
        )
        result.errors.append(error)
        
        log_func = getattr(self.logger, severity, self.logger.warning)
        log_func(f"[{error_type.value}] {message}")
    
    def _add_warning(self, result: WorkerResult, warning: str) -> None:
        """Add warning to result."""
        result.warnings.append(warning)
        self.logger.warning(f"Warning: {warning}")
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters. Override in subclasses.
        
        Subclasses should override this method to provide worker-specific
        input validation. This method is called by safe_execute() before
        the main execute() method.
        
        Returns:
            WorkerError if validation fails, None if valid
        """
        return None
    
    def safe_execute(self, **kwargs: Any) -> WorkerResult:
        """Execute with error handling.
        
        Wraps execute() with try-catch to ensure
        WorkerResult is always returned.
        """
        start_time = time.time()
        
        try:
            # Validate input
            validation_error = self._validate_input(**kwargs)
            if validation_error:
                result = self._create_result(success=False, quality_score=0)
                result.errors.append(validation_error)
                result.execution_time_ms = int((time.time() - start_time) * 1000)
                return result
            
            # Execute task
            result = self.execute(**kwargs)
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Worker execution failed: {e}")
            
            result = self._create_result(success=False, quality_score=0)
            self._add_error(
                result,
                ErrorType.UNKNOWN_ERROR,
                str(e),
                severity="critical",
                details={"traceback": traceback.format_exc()},
                suggestion="Check worker implementation and input parameters",
            )
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            
            return result
