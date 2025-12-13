"""Error Record - Core error tracking data structures.

Provides standardized error tracking with type safety,
severity levels, and comprehensive context capture.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


class ErrorType(Enum):
    """Error type classification."""
    DATA_LOAD_ERROR = "data_load_error"
    DATA_VALIDATION_ERROR = "data_validation_error"
    DATA_TRANSFORMATION_ERROR = "data_transformation_error"
    AGENT_LIFECYCLE_ERROR = "agent_lifecycle_error"
    TASK_EXECUTION_ERROR = "task_execution_error"
    WORKFLOW_EXECUTION_ERROR = "workflow_execution_error"
    NARRATIVE_GENERATION_ERROR = "narrative_generation_error"
    WORKER_ERROR = "worker_error"
    CONFIGURATION_ERROR = "configuration_error"
    DATABASE_ERROR = "database_error"
    VISUALIZATION_ERROR = "visualization_error"
    PREDICTION_ERROR = "prediction_error"
    ANOMALY_DETECTION_ERROR = "anomaly_detection_error"
    REPORT_GENERATION_ERROR = "report_generation_error"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Standardized error record with full context.
    
    Attributes:
        error_type: Type of error (ErrorType enum)
        severity: Severity level (ErrorSeverity enum)
        worker_name: Name of worker that failed
        message: Error message
        context: Additional context dict
        timestamp: When error occurred (ISO format)
        traceback: Full traceback if available
    """
    
    error_type: ErrorType
    severity: ErrorSeverity
    worker_name: str
    message: str
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    traceback: Optional[str] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.context is None:
            self.context = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dict representation
        """
        return {
            'error_type': self.error_type.value,
            'severity': self.severity.value,
            'worker_name': self.worker_name,
            'message': self.message,
            'context': self.context,
            'timestamp': self.timestamp,
            'traceback': self.traceback
        }
    
    def is_critical(self) -> bool:
        """Check if error is critical.
        
        Returns:
            True if CRITICAL or HIGH severity
        """
        return self.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]
    
    def summary(self) -> str:
        """Get short summary.
        
        Returns:
            Summary string
        """
        return f"[{self.severity.value.upper()}] {self.worker_name}: {self.message}"


class ErrorRecordBuilder:
    """Builder for ErrorRecord with fluent interface.
    
    Example:
        record = (ErrorRecordBuilder()
            .with_type(ErrorType.DATA_VALIDATION_ERROR)
            .with_severity(ErrorSeverity.HIGH)
            .with_worker("DataLoader")
            .with_message("Invalid data format")
            .with_context({"rows": 1000})
            .build())
    """
    
    def __init__(self):
        self._error_type: Optional[ErrorType] = None
        self._severity: Optional[ErrorSeverity] = None
        self._worker_name: Optional[str] = None
        self._message: Optional[str] = None
        self._context: Dict[str, Any] = {}
        self._timestamp: Optional[str] = None
        self._traceback: Optional[str] = None
    
    def with_type(self, error_type: ErrorType) -> 'ErrorRecordBuilder':
        """Set error type."""
        self._error_type = error_type
        return self
    
    def with_severity(self, severity: ErrorSeverity) -> 'ErrorRecordBuilder':
        """Set severity."""
        self._severity = severity
        return self
    
    def with_worker(self, worker_name: str) -> 'ErrorRecordBuilder':
        """Set worker name."""
        self._worker_name = worker_name
        return self
    
    def with_message(self, message: str) -> 'ErrorRecordBuilder':
        """Set message."""
        self._message = message
        return self
    
    def with_context(self, context: Dict[str, Any]) -> 'ErrorRecordBuilder':
        """Set context."""
        self._context = context
        return self
    
    def add_context(self, key: str, value: Any) -> 'ErrorRecordBuilder':
        """Add single context item."""
        self._context[key] = value
        return self
    
    def with_traceback(self, traceback: str) -> 'ErrorRecordBuilder':
        """Set traceback."""
        self._traceback = traceback
        return self
    
    def with_timestamp(self, timestamp: str) -> 'ErrorRecordBuilder':
        """Set timestamp."""
        self._timestamp = timestamp
        return self
    
    def build(self) -> ErrorRecord:
        """Build ErrorRecord.
        
        Returns:
            Configured ErrorRecord
        
        Raises:
            ValueError: If required fields missing
        """
        if not self._error_type:
            raise ValueError("error_type is required")
        if not self._severity:
            raise ValueError("severity is required")
        if not self._worker_name:
            raise ValueError("worker_name is required")
        if not self._message:
            raise ValueError("message is required")
        
        return ErrorRecord(
            error_type=self._error_type,
            severity=self._severity,
            worker_name=self._worker_name,
            message=self._message,
            context=self._context,
            timestamp=self._timestamp,
            traceback=self._traceback
        )
