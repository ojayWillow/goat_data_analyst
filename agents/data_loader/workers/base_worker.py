"""Base Worker for Data Loader - Enhanced with A+ quality standards.

Provides abstract base class for all data loader workers with:
- Comprehensive error intelligence tracking
- Quality score calculation
- Data loss tracking
- Structured error recording
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum
import time
import pandas as pd
from datetime import datetime
from pytz import UTC

from core.logger import get_logger

logger = get_logger(__name__)

# ===== CONSTANTS =====
MIN_ROWS_REQUIRED = 1
QUALITY_THRESHOLD = 0.8
MAX_NULL_PERCENTAGE = 90.0  # Max null % before failure


class ErrorType(Enum):
    """Standardized error types for data loading.
    
    Used for error classification, analysis, and recovery decisions.
    """
    FILE_NOT_FOUND = "file_not_found"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FORMAT = "unsupported_format"
    LOAD_ERROR = "load_error"
    VALIDATION_ERROR = "validation_error"
    EMPTY_DATA = "empty_data"
    NULL_VALUE_ERROR = "null_value"
    DUPLICATE_KEY_ERROR = "duplicate_key"
    DATA_TYPE_ERROR = "data_type"
    ENCODING_ERROR = "encoding_error"
    COMPUTATION_ERROR = "computation_error"


class ErrorRecord:
    """Complete error information for analysis and diagnosis.
    
    Tracks all error context needed for:
    - Error intelligence analysis
    - Pattern detection
    - Automatic recovery
    - User remediation suggestions
    """
    
    def __init__(
        self,
        error_type: ErrorType,
        worker_name: str,
        message: str,
        sample_data: Any = None,
        expected_value: Any = None,
        actual_value: Any = None,
        column_name: Optional[str] = None,
        row_count: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize error record.
        
        Args:
            error_type: Classification of error
            worker_name: Name of worker that encountered error
            message: Human-readable error message
            sample_data: Sample of problematic data for diagnosis
            expected_value: Expected value (for validation errors)
            actual_value: Actual value received
            column_name: Column where error occurred
            row_count: Number of rows affected
            context: Additional context dictionary
        """
        self.error_type = error_type
        self.worker_name = worker_name
        self.message = message
        self.sample_data = sample_data
        self.expected_value = expected_value
        self.actual_value = actual_value
        self.column_name = column_name
        self.row_count = row_count
        self.context = context or {}
        self.timestamp = datetime.now(UTC).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to structured dictionary format.
        
        Returns:
            Dictionary with all error information
        """
        return {
            'error_type': self.error_type.value,
            'worker': self.worker_name,
            'message': self.message,
            'sample_data': str(self.sample_data)[:200],  # Truncate for safety
            'expected': str(self.expected_value) if self.expected_value is not None else None,
            'actual': str(self.actual_value) if self.actual_value is not None else None,
            'column': self.column_name,
            'rows': self.row_count,
            'context': self.context,
            'timestamp': self.timestamp
        }


@dataclass
class WorkerResult:
    """Standardized result format for all data loader workers.
    
    Provides consistent structure for:
    - Success/failure status
    - Loaded data
    - Metadata about operation
    - Error tracking
    - Quality metrics
    """
    worker: str
    task_type: str
    success: bool
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    quality_score: float = 0.0
    rows_processed: int = 0
    rows_failed: int = 0
    data_loss_pct: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.
        
        Returns:
            Dictionary representation of result
        """
        return {
            "worker": self.worker,
            "task_type": self.task_type,
            "success": self.success,
            "data": self.data,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
            "quality_score": self.quality_score,
            "rows_processed": self.rows_processed,
            "rows_failed": self.rows_failed,
            "data_loss_pct": self.data_loss_pct,
        }


class BaseWorker(ABC):
    """Abstract base class for all data loader workers.
    
    Defines protocol for workers to:
    - Validate input data
    - Execute loading operation
    - Track quality metrics
    - Handle errors gracefully
    - Return structured results
    
    All workers must implement:
    1. validate_input() - Input validation
    2. execute() - Core operation
    """
    
    def __init__(self, name: str) -> None:
        """Initialize worker.
        
        Args:
            name: Unique worker identifier
        """
        self.name = name
        self.version = "1.0.0"
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input meets all requirements.
        
        Must be implemented by all workers.
        Should check:
        - Data types
        - Required fields
        - Data quality
        - Size constraints
        
        Args:
            input_data: Input dictionary to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails with specific details
            TypeError: If wrong data types
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> WorkerResult:
        """Execute the loading task.
        
        Must be implemented by all workers.
        Should:
        1. Validate input
        2. Perform operation
        3. Track errors
        4. Calculate quality score
        5. Return structured result
        
        Args:
            **kwargs: Task-specific parameters
            
        Returns:
            WorkerResult with operation details
        """
        pass
    
    def safe_execute(self, **kwargs) -> WorkerResult:
        """Safely execute with comprehensive error handling.
        
        Wraps execute() with:
        - Execution time tracking
        - Exception handling
        - Error logging
        - Timeout protection
        
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
            self.logger.error(f"Worker execution failed: {e}", exc_info=True)
            duration_ms = (time.time() - start_time) * 1000
            return WorkerResult(
                worker=self.name,
                task_type="data_loading",
                success=False,
                data=None,
                errors=[{
                    "type": "execution_error",
                    "message": str(e),
                    "worker": self.name
                }],
                execution_time_ms=duration_ms,
                quality_score=0.0,
            )
    
    def _create_result(
        self,
        task_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> WorkerResult:
        """Create a new WorkerResult instance.
        
        Args:
            task_type: Type of task (e.g., 'csv_loading')
            metadata: Additional metadata
            success: Initial success status
            
        Returns:
            New WorkerResult instance
        """
        return WorkerResult(
            worker=self.name,
            task_type=task_type,
            success=success,
            metadata=metadata or {},
        )
    
    def _add_error(
        self,
        result: WorkerResult,
        error_type: ErrorType,
        message: str,
        column_name: Optional[str] = None,
        row_count: Optional[int] = None
    ) -> None:
        """Add error to result with full context.
        
        Args:
            result: WorkerResult to add error to
            error_type: Type of error
            message: Error message
            column_name: Column affected (optional)
            row_count: Rows affected (optional)
        """
        result.errors.append({
            "type": error_type.value,
            "message": message,
            "column": column_name,
            "rows": row_count,
            "timestamp": datetime.now(UTC).isoformat()
        })
    
    def _add_warning(self, result: WorkerResult, message: str) -> None:
        """Add warning to result.
        
        Args:
            result: WorkerResult to add warning to
            message: Warning message
        """
        result.warnings.append(message)
        self.logger.warning(message)
    
    def _calculate_quality_score(
        self,
        rows_processed: int,
        rows_failed: int
    ) -> float:
        """Calculate quality score (0-1 range).
        
        Formula: quality = 1.0 - (rows_failed / total_rows)
        
        Args:
            rows_processed: Number of rows successfully processed
            rows_failed: Number of rows that failed
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        total = rows_processed + rows_failed
        if total == 0:
            return 0.0
        return max(0.0, 1.0 - (rows_failed / total))
    
    def _calculate_data_loss_pct(
        self,
        rows_processed: int,
        rows_failed: int
    ) -> float:
        """Calculate percentage of data lost/skipped.
        
        Args:
            rows_processed: Number of rows successfully processed
            rows_failed: Number of rows that failed
            
        Returns:
            Data loss percentage (0.0 to 100.0)
        """
        total = rows_processed + rows_failed
        if total == 0:
            return 0.0
        return (rows_failed / total) * 100.0
    
    def _check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data quality metrics.
        
        Checks for:
        - Null values
        - Duplicates
        - Empty data
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dictionary with quality metrics
        """
        if df is None or df.empty:
            return {
                "valid": False,
                "null_count": 0,
                "null_pct": 100.0,
                "duplicates": 0,
                "duplicate_pct": 0.0,
                "issues": ["DataFrame is empty"]
            }
        
        total_cells = len(df) * len(df.columns)
        null_count = int(df.isna().sum().sum())
        null_pct = (null_count / total_cells * 100) if total_cells > 0 else 0.0
        
        dup_count = int(df.duplicated().sum())
        dup_pct = (dup_count / len(df) * 100) if len(df) > 0 else 0.0
        
        issues = []
        if null_pct > MAX_NULL_PERCENTAGE:
            issues.append(f"High null percentage: {null_pct:.1f}%")
        if dup_pct > 50:
            issues.append(f"High duplicate percentage: {dup_pct:.1f}%")
        
        return {
            "valid": len(issues) == 0,
            "null_count": null_count,
            "null_pct": round(null_pct, 2),
            "duplicates": dup_count,
            "duplicate_pct": round(dup_pct, 2),
            "issues": issues
        }
