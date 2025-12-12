"""Base Worker for Anomaly Detector - Template and protocol for all detection workers.

Implements comprehensive error handling and intelligence tracking as per
GOAT Data Analyst guidance (Section 4: Error Handling & Intelligence).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import time
from datetime import datetime

from core.logger import get_logger
from core.exceptions import AgentError

logger = get_logger(__name__)


class ErrorType(Enum):
    """Error types for anomaly detection workers.
    
    Classified error types for tracking and analysis:
    - Data Quality: Issues with data content
    - Format: Issues with data format/structure
    - Computation: Issues during calculation
    - System: System-level issues
    - Configuration: Issues with parameters
    """
    # Data Quality Errors
    MISSING_DATA = "missing_data"
    NULL_VALUE_ERROR = "null_value"
    DUPLICATE_KEY_ERROR = "duplicate_key"
    DATA_TYPE_ERROR = "data_type"
    
    # Format Errors
    INVALID_COLUMN = "invalid_column"
    DATE_FORMAT_ERROR = "date_format"
    ENCODING_ERROR = "encoding"
    
    # Computation Errors
    DIVISION_BY_ZERO = "division_by_zero"
    NAN_PROPAGATION = "nan_propagation"
    COMPUTATION_ERROR = "computation_error"
    
    # System Errors
    SKLEARN_UNAVAILABLE = "sklearn_unavailable"
    MEMORY_ERROR = "memory_error"
    TIMEOUT_ERROR = "timeout_error"
    
    # Configuration Errors
    INVALID_PARAMETER = "invalid_parameter"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class ErrorRecord:
    """Complete error information for analysis.
    
    Captures full context for every error encountered,
    enabling intelligent error recovery and learning.
    
    Attributes:
        error_type: Classification of error
        worker_name: Name of worker that encountered error
        message: Human-readable error message
        column_name: Column involved (if applicable)
        row_count: Number of rows affected
        sample_data: Sample data that caused error
        expected_value: What was expected
        actual_value: What was actually received
        timestamp: When error occurred
    """
    error_type: ErrorType
    worker_name: str
    message: str
    column_name: Optional[str] = None
    row_count: Optional[int] = None
    sample_data: Optional[Any] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to structured dictionary format.
        
        Returns:
            Dict with all error details for logging/analysis
        """
        return {
            'error_type': self.error_type.value,
            'worker': self.worker_name,
            'message': self.message,
            'column': self.column_name,
            'rows': self.row_count,
            'sample': str(self.sample_data)[:200] if self.sample_data else None,
            'expected': str(self.expected_value) if self.expected_value else None,
            'actual': str(self.actual_value) if self.actual_value else None,
            'timestamp': self.timestamp
        }


@dataclass
class WorkerResult:
    """Standardized result format for all anomaly detector workers.
    
    Every worker returns this structure, enabling consistent error
    handling, quality tracking, and error intelligence integration.
    
    Attributes:
        worker: Worker name that produced result
        task_type: Type of task performed (e.g., 'anomaly_detection')
        success: Whether task completed successfully
        data: Analytical results/data
        errors: List of errors encountered (captured for learning)
        warnings: Non-fatal warnings
        quality_score: Quality metric (0-1, where 1.0 = perfect)
        metadata: Execution metadata
        timestamp: When result was generated
        execution_time_ms: How long execution took
    """
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
    rows_processed: int = 0
    rows_failed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.
        
        Returns:
            Dict with all result data for serialization
        """
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
            "rows_processed": self.rows_processed,
            "rows_failed": self.rows_failed,
        }


class BaseWorker(ABC):
    """Base class for all anomaly detector workers.
    
    Every anomaly detection worker extends this class and implements:
    - execute(): The actual detection logic
    - Input validation
    - Standardized error handling and intelligence tracking
    - Consistent result formatting
    - Quality score calculation
    
    GUIDANCE Compliance:
    - Section 3.1: Worker Responsibilities
    - Section 3.2: Worker Interface Contract
    - Section 3.3: Worker Implementation Requirements
    - Section 4: Error Handling & Intelligence
    
    Attributes:
        name: Worker name (e.g., 'LOFWorker')
        version: Semantic version
        logger: Structured logger
        error_tracker: For tracking errors with ErrorIntelligence
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize worker.
        
        Args:
            name: Worker name
            version: Semantic version (default: 1.0.0)
        """
        self.name = name
        self.version = version
        self.logger = get_logger(self.__class__.__name__)
        self.error_tracker = None  # Will be set by Agent
    
    @abstractmethod
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the anomaly detection task.
        
        Subclasses MUST implement this method to:
        1. Validate all inputs
        2. Perform detection logic
        3. Catch and classify errors
        4. Track execution quality
        5. Return structured result
        
        Args:
            **kwargs: Task-specific parameters (df, column, threshold, etc.)
            
        Returns:
            WorkerResult with detection results or comprehensive errors
            
        Raises:
            Should NOT raise - catch and return in WorkerResult
        """
        pass
    
    def safe_execute(self, **kwargs) -> WorkerResult:
        """Safely execute with comprehensive error handling.
        
        Wraps execute() with:
        - Timing measurement
        - Exception catching
        - Error tracking
        - Result validation
        
        Args:
            **kwargs: Task-specific parameters
            
        Returns:
            WorkerResult with proper error handling
        """
        start_time = time.time()
        try:
            result = self.execute(**kwargs)
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            # Track with error intelligence if available
            if self.error_tracker:
                if result.success:
                    self.error_tracker.track_success(
                        worker_name=self.name,
                        quality_score=result.quality_score,
                        execution_time_ms=result.execution_time_ms
                    )
                else:
                    self.error_tracker.track_error(
                        worker_name=self.name,
                        errors=result.errors,
                        quality_score=result.quality_score
                    )
            
            return result
        except Exception as e:
            self.logger.error(f"Worker execution failed: {e}", exc_info=True)
            duration_ms = (time.time() - start_time) * 1000
            
            # Track failure with error intelligence
            if self.error_tracker:
                self.error_tracker.track_error(
                    worker_name=self.name,
                    errors=[{
                        "type": ErrorType.COMPUTATION_ERROR.value,
                        "message": str(e)
                    }],
                    quality_score=0.0
                )
            
            return WorkerResult(
                worker=self.name,
                task_type="anomaly_detection",
                success=False,
                errors=[{
                    "type": ErrorType.COMPUTATION_ERROR.value,
                    "message": str(e)
                }],
                execution_time_ms=duration_ms,
                quality_score=0.0,
                timestamp=datetime.utcnow().isoformat(),
            )
    
    def _create_result(
        self,
        task_type: str,
        quality_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        rows_processed: int = 0,
        rows_failed: int = 0,
    ) -> WorkerResult:
        """Create a new WorkerResult object.
        
        Args:
            task_type: Type of detection task
            quality_score: Quality score (0-1, where 1.0 = perfect)
            metadata: Additional metadata
            rows_processed: Number of rows successfully processed
            rows_failed: Number of rows that failed
            
        Returns:
            New WorkerResult instance
        """
        return WorkerResult(
            worker=self.name,
            task_type=task_type,
            success=True,
            quality_score=quality_score,
            metadata=metadata or {},
            timestamp=datetime.utcnow().isoformat(),
            rows_processed=rows_processed,
            rows_failed=rows_failed,
        )
    
    def _add_error(
        self,
        result: WorkerResult,
        error_type: ErrorType,
        message: str,
        column_name: Optional[str] = None,
        row_count: Optional[int] = None,
        sample_data: Optional[Any] = None,
        expected_value: Optional[Any] = None,
        actual_value: Optional[Any] = None,
    ) -> None:
        """Add comprehensive error to result.
        
        GUIDANCE Compliance: Section 4.2 - Error Intelligence Tracking
        
        Captures full error context for analysis and learning:
        - Error type for classification
        - Column/row info for localization
        - Sample data for diagnosis
        - Expected vs actual for investigation
        
        Args:
            result: WorkerResult to add error to
            error_type: Type of error (from ErrorType enum)
            message: Human-readable error message
            column_name: Column involved (if applicable)
            row_count: Number of rows affected
            sample_data: Sample data that caused error
            expected_value: What was expected
            actual_value: What was actually received
        """
        error_record = ErrorRecord(
            error_type=error_type,
            worker_name=self.name,
            message=message,
            column_name=column_name,
            row_count=row_count,
            sample_data=sample_data,
            expected_value=expected_value,
            actual_value=actual_value,
        )
        
        result.errors.append(error_record.to_dict())
        result.success = False
        
        # Track with error intelligence
        if self.error_tracker:
            self.error_tracker.track_error(
                worker_name=self.name,
                errors=[error_record.to_dict()],
                quality_score=0.0
            )
    
    def _add_warning(
        self,
        result: WorkerResult,
        message: str
    ) -> None:
        """Add non-fatal warning to result.
        
        Warnings don't fail the operation but inform about
        degradations or quality issues.
        
        Args:
            result: WorkerResult to add warning to
            message: Warning message
        """
        result.warnings.append(message)
        self.logger.warning(f"{self.name}: {message}")
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int,
        errors_count: int = 0
    ) -> float:
        """Calculate quality score for execution.
        
        GUIDANCE Compliance: Section 3.3 - Worker Implementation Requirements
        
        Quality score formula:
        - Base: rows processed / total rows
        - Penalty: errors count * 0.1 (up to -0.5)
        
        Args:
            rows_processed: Number of rows successfully processed
            rows_failed: Number of rows that failed
            errors_count: Number of errors encountered
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        total_rows = rows_processed + rows_failed
        if total_rows == 0:
            return 0.0
        
        # Base quality from rows processed
        base_quality = rows_processed / total_rows
        
        # Apply penalty for errors (max 0.5 penalty)
        error_penalty = min(0.5, errors_count * 0.1)
        
        quality = max(0.0, base_quality - error_penalty)
        return min(1.0, quality)
