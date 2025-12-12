"""BaseWorker - Abstract base class for Explorer workers.

Defines the common language/protocol that all workers use.
Ensures consistent quality standards and error reporting.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime, timezone
import traceback
import time

from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class ErrorType(Enum):
    """Standard error types across all workers."""
    DATA_VALIDATION_ERROR = "data_validation_error"
    COMPUTATION_ERROR = "computation_error"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    MISSING_DATA = "missing_data"
    INVALID_PARAMETER = "invalid_parameter"
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
    ) -> None:
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.suggestion = suggestion
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
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
    
    Attributes:
        worker_name: Name of the worker that produced this result
        task_type: Type of task executed (e.g., 'numeric_analysis')
        success: Whether the worker executed successfully
        data: Result data from the worker
        errors: List of errors encountered during execution
        warnings: List of non-fatal warnings
        quality_score: Quality metric from 0-1
        metadata: Additional execution metadata
        timestamp: ISO format timestamp of execution
        execution_time_ms: Execution duration in milliseconds
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
    ) -> None:
        self.worker_name = worker_name
        self.task_type = task_type
        self.success = success
        self.data = data or {}
        self.errors = errors or []
        self.warnings = warnings or []
        self.quality_score = max(0, min(1, quality_score))  # Clamp 0-1
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.execution_time_ms = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation of the result
        """
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
        """Check if result contains errors.
        
        Returns:
            True if any errors exist
        """
        return len(self.errors) > 0
    
    def has_critical_errors(self) -> bool:
        """Check if result contains critical errors.
        
        Returns:
            True if any critical errors exist
        """
        return any(e.severity == "critical" for e in self.errors)
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of error types.
        
        Returns:
            Dictionary mapping error type to count
        """
        summary: Dict[str, int] = {}
        for error in self.errors:
            error_type = error.error_type.value
            summary[error_type] = summary.get(error_type, 0) + 1
        return summary


class BaseWorker(ABC):
    """Abstract base class for all Explorer workers.
    
    Defines protocol all workers must follow.
    Ensures consistent quality standards and error handling.
    
    Key Principles:
    - execute() should NEVER raise exceptions
    - Always return WorkerResult with success/failure status
    - Track errors in result, not exceptions
    - Validate input and report missing data clearly
    - Calculate quality score (0-1) based on data processed
    
    Subclass Requirements:
    - Override execute() method
    - Optionally override _validate_input()
    - Document task_type and expected parameters
    - Set quality_score based on data processed/errors
    """
    
    def __init__(self, worker_name: str) -> None:
        """Initialize base worker.
        
        Args:
            worker_name: Unique identifier for this worker
        """
        self.worker_name = worker_name
        self.logger = get_logger(f"explorer.workers.{worker_name}")
        self.error_intelligence = ErrorIntelligence()
        self.logger.info(f"Worker initialized: {worker_name}")
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute the worker's task.
        
        CRITICAL: Must NEVER raise exceptions.
        Must always return WorkerResult object.
        If error occurs, return result with success=False and error details.
        
        Args:
            **kwargs: Task-specific parameters (must include 'df' for DataFrame)
            
        Returns:
            WorkerResult with standardized format
            
        Note:
            Called by safe_execute(), which wraps with timeout/retry logic.
            Subclasses MUST catch all exceptions and return as WorkerResult.
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
        """Create a standardized result.
        
        Args:
            success: Whether task succeeded
            data: Result data from task
            task_type: Type of task executed
            quality_score: Quality metric (0-1)
            **kwargs: Additional parameters for WorkerResult
            
        Returns:
            WorkerResult instance
        """
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
        """Add error to result.
        
        Args:
            result: WorkerResult to add error to
            error_type: Type of error from ErrorType enum
            message: Human-readable error message
            severity: One of 'info', 'warning', 'error', 'critical'
            details: Additional context/details about error
            suggestion: Recommendation for fixing the error
        """
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
        """Add warning to result.
        
        Args:
            result: WorkerResult to add warning to
            warning: Warning message
        """
        result.warnings.append(warning)
        self.logger.warning(f"Warning: {warning}")
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters.
        
        Override in subclasses to add custom validation.
        
        Args:
            **kwargs: Input parameters to validate
            
        Returns:
            WorkerError if validation fails, None if valid
        """
        return None
    
    def safe_execute(self, **kwargs: Any) -> WorkerResult:
        """Execute with error handling.
        
        Wraps execute() with try-catch to ensure WorkerResult is always returned.
        Handles validation, execution timing, and error intelligence tracking.
        
        Args:
            **kwargs: Task-specific parameters
            
        Returns:
            WorkerResult (guaranteed non-None)
            
        Note:
            This method guarantees WorkerResult is always returned,
            even if execute() implementation has bugs.
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
            
            # Execute task - MUST return WorkerResult, never raise
            result = self.execute(**kwargs)
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Ensure result is valid
            if not isinstance(result, WorkerResult):
                self.logger.error(f"execute() returned non-WorkerResult: {type(result)}")
                fallback_result = self._create_result(success=False, quality_score=0)
                self._add_error(
                    fallback_result,
                    ErrorType.UNKNOWN_ERROR,
                    "execute() returned non-WorkerResult object",
                    severity="critical",
                    details={"returned_type": str(type(result))},
                    suggestion="Ensure execute() always returns WorkerResult"
                )
                fallback_result.execution_time_ms = int((time.time() - start_time) * 1000)
                return fallback_result
            
            # Track result in error intelligence
            if result.success:
                self.error_intelligence.track_success(
                    agent_name="explorer",
                    worker_name=self.worker_name,
                    operation="execute",
                    context={
                        "task_type": result.task_type,
                        "quality_score": result.quality_score
                    }
                )
            else:
                # Track failure
                if result.errors:
                    error_summary = result.get_error_summary()
                    error_msg = "; ".join([e.message for e in result.errors[:3]])
                    self.error_intelligence.track_error(
                        agent_name="explorer",
                        worker_name=self.worker_name,
                        error_type="execution_failure",
                        error_message=error_msg,
                        context={
                            "task_type": result.task_type,
                            "error_count": len(result.errors),
                            "error_types": error_summary
                        }
                    )
            
            return result
        
        except Exception as e:
            """Catch unexpected exceptions from execute().
            
            This is a safety net for execute() implementations that raise.
            Logs error and returns failed WorkerResult.
            """
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"Worker execution failed with exception: {e}", exc_info=True)
            
            # Track error
            self.error_intelligence.track_error(
                agent_name="explorer",
                worker_name=self.worker_name,
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "safe_execute"}
            )
            
            result = self._create_result(success=False, quality_score=0)
            self._add_error(
                result,
                ErrorType.UNKNOWN_ERROR,
                str(e),
                severity="critical",
                details={
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                },
                suggestion="Check worker implementation and input parameters",
            )
            result.execution_time_ms = duration_ms
            
            return result
