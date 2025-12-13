"""BaseWorker - Abstract base class for Reporter workers.

Defines the common protocol that all workers use.
Ensures consistent quality standards and error reporting.

Enhanced with:
- Validation utilities
- Performance metrics
- Better error context
- Retry mechanisms
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime, timezone
import traceback
import time
import functools
import pandas as pd

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
    EMPTY_DATA_ERROR = "empty_data_error"
    UNKNOWN_ERROR = "unknown_error"


class WorkerError:
    """Standardized error report from a worker."""
    
    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.suggestion = suggestion
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.error_type.value,
            "message": self.message,
            "severity": self.severity,
            "details": self.details,
            "suggestion": self.suggestion,
            "context": self.context,
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
        self.quality_score = max(0, min(1, quality_score))
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.execution_time_ms = 0
        self.rows_processed = 0
        self.rows_failed = 0
    
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
            "rows_processed": self.rows_processed,
            "rows_failed": self.rows_failed,
        }
    
    def has_errors(self) -> bool:
        """Check if result has any errors."""
        return len(self.errors) > 0
    
    def has_critical_errors(self) -> bool:
        """Check if result has critical errors."""
        return any(e.severity == "critical" for e in self.errors)
    
    def get_error_summary(self) -> str:
        """Get summary of all errors."""
        if not self.errors:
            return "No errors"
        return "; ".join([f"{e.error_type.value}: {e.message}" for e in self.errors])


class ValidationUtils:
    """Utility class for validation operations."""
    
    @staticmethod
    def validate_dataframe(
        df: Optional[pd.DataFrame],
        min_rows: int = 0,
        min_cols: int = 0,
        allow_empty: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """Validate DataFrame with detailed error messages.
        
        Args:
            df: DataFrame to validate
            min_rows: Minimum rows required
            min_cols: Minimum columns required
            allow_empty: Allow empty DataFrames
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if df is None:
            return False, "DataFrame is None"
        
        if not isinstance(df, pd.DataFrame):
            return False, f"Expected DataFrame, got {type(df).__name__}"
        
        if df.empty and not allow_empty:
            return False, "DataFrame is empty"
        
        if len(df) < min_rows:
            return False, f"DataFrame has {len(df)} rows, need at least {min_rows}"
        
        if len(df.columns) < min_cols:
            return False, f"DataFrame has {len(df.columns)} columns, need at least {min_cols}"
        
        return True, None
    
    @staticmethod
    def validate_column_exists(df: pd.DataFrame, columns: List[str]) -> tuple[bool, Optional[str]]:
        """Validate columns exist in DataFrame.
        
        Args:
            df: DataFrame to check
            columns: Column names to verify
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        missing = set(columns) - set(df.columns)
        if missing:
            return False, f"Missing columns: {missing}"
        return True, None
    
    @staticmethod
    def get_data_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate data quality metrics.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with quality metrics
        """
        rows, cols = df.shape
        total_cells = rows * cols
        null_count = df.isnull().sum().sum()
        null_pct = (null_count / total_cells * 100) if total_cells > 0 else 0
        
        return {
            "rows": rows,
            "columns": cols,
            "total_cells": total_cells,
            "null_count": int(null_count),
            "null_percentage": round(null_pct, 2),
            "duplicate_count": int(df.duplicated().sum()),
            "duplicate_percentage": round((df.duplicated().sum() / rows * 100) if rows > 0 else 0, 2),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
        }


class BaseWorker(ABC):
    """Abstract base class for all Reporter workers.
    
    Defines protocol all workers must follow.
    Ensures consistent quality standards and error handling.
    """
    
    def __init__(self, worker_name: str):
        self.worker_name = worker_name
        self.logger = get_logger(f"reporter.workers.{worker_name}")
        self.error_intelligence = ErrorIntelligence()
        self.logger.info(f"Worker initialized: {worker_name}")
    
    @abstractmethod
    def execute(self, **kwargs) -> WorkerResult:
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
        **kwargs
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
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add error to result with full context."""
        error = WorkerError(
            error_type=error_type,
            message=message,
            severity=severity,
            details=details,
            suggestion=suggestion,
            context=context,
        )
        result.errors.append(error)
        log_func = getattr(self.logger, severity, self.logger.warning)
        log_func(f"[{error_type.value}] {message}")
    
    def _add_warning(self, result: WorkerResult, warning: str) -> None:
        """Add warning to result."""
        result.warnings.append(warning)
        self.logger.warning(f"Warning: {warning}")
    
    def safe_execute(self, **kwargs) -> WorkerResult:
        """Execute with error handling.
        
        Wraps execute() with try-catch to ensure
        WorkerResult is always returned.
        """
        start_time = time.time()
        
        try:
            result = self.execute(**kwargs)
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Track success
            if result.success:
                self.error_intelligence.track_success(
                    agent_name="reporter",
                    worker_name=self.worker_name,
                    operation="execute",
                    context={
                        "task_type": result.task_type,
                        "quality_score": result.quality_score,
                        "execution_time_ms": result.execution_time_ms,
                    }
                )
            else:
                # Track failure if errors exist
                if result.errors:
                    error_msg = "; ".join([e.message for e in result.errors])
                    self.error_intelligence.track_error(
                        agent_name="reporter",
                        worker_name=self.worker_name,
                        error_type="execution_failure",
                        error_message=error_msg,
                        context={"task_type": result.task_type}
                    )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Worker execution failed: {e}")
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Track error
            self.error_intelligence.track_error(
                agent_name="reporter",
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
                details={"traceback": traceback.format_exc()},
            )
            result.execution_time_ms = duration_ms
            return result
