"""Tests for Reporter BaseWorker and shared utilities.

Tests validation utilities, error handling, and result formatting.
"""

import pytest
import pandas as pd
import numpy as np
from agents.reporter.workers.base_worker import (
    BaseWorker,
    ValidationUtils,
    WorkerError,
    WorkerResult,
    ErrorType,
)


class TestValidationUtils:
    """Test ValidationUtils for data validation."""
    
    def test_validate_dataframe_valid(self):
        """Valid DataFrame should pass validation."""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        is_valid, error_msg = ValidationUtils.validate_dataframe(df)
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_dataframe_none(self):
        """None should fail validation."""
        is_valid, error_msg = ValidationUtils.validate_dataframe(None)
        assert is_valid is False
        assert error_msg == "DataFrame is None"
    
    def test_validate_dataframe_not_dataframe(self):
        """Non-DataFrame should fail validation."""
        is_valid, error_msg = ValidationUtils.validate_dataframe([1, 2, 3])
        assert is_valid is False
        assert "Expected DataFrame" in error_msg
    
    def test_validate_dataframe_empty_not_allowed(self):
        """Empty DataFrame should fail when not allowed."""
        df = pd.DataFrame()
        is_valid, error_msg = ValidationUtils.validate_dataframe(df, allow_empty=False)
        assert is_valid is False
        assert "empty" in error_msg.lower()
    
    def test_validate_dataframe_empty_allowed(self):
        """Empty DataFrame should pass when allowed."""
        df = pd.DataFrame()
        is_valid, error_msg = ValidationUtils.validate_dataframe(df, allow_empty=True)
        assert is_valid is True
    
    def test_validate_dataframe_min_rows(self):
        """Should validate minimum rows."""
        df = pd.DataFrame({"col1": [1, 2]})
        is_valid, error_msg = ValidationUtils.validate_dataframe(df, min_rows=5)
        assert is_valid is False
        assert "2 rows" in error_msg
    
    def test_validate_dataframe_min_cols(self):
        """Should validate minimum columns."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        is_valid, error_msg = ValidationUtils.validate_dataframe(df, min_cols=3)
        assert is_valid is False
        assert "1 columns" in error_msg
    
    def test_validate_column_exists_all_present(self):
        """Should pass when all columns exist."""
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        is_valid, error_msg = ValidationUtils.validate_column_exists(df, ["a", "b"])
        assert is_valid is True
    
    def test_validate_column_exists_missing(self):
        """Should fail when columns missing."""
        df = pd.DataFrame({"a": [1], "b": [2]})
        is_valid, error_msg = ValidationUtils.validate_column_exists(df, ["a", "d"])
        assert is_valid is False
        assert "Missing columns" in error_msg
    
    def test_get_data_quality_metrics(self):
        """Should calculate quality metrics correctly."""
        df = pd.DataFrame({
            "a": [1, 2, None, 4, 5],
            "b": [1, 1, 2, 3, 4]
        })
        
        metrics = ValidationUtils.get_data_quality_metrics(df)
        
        assert metrics["rows"] == 5
        assert metrics["columns"] == 2
        assert metrics["null_count"] == 1
        assert metrics["null_percentage"] > 0
        assert metrics["duplicate_count"] == 0
        assert "memory_mb" in metrics


class TestWorkerError:
    """Test WorkerError for error reporting."""
    
    def test_worker_error_creation(self):
        """WorkerError should store all attributes."""
        error = WorkerError(
            error_type=ErrorType.DATA_VALIDATION_ERROR,
            message="Test error",
            severity="critical",
            suggestion="Test fix"
        )
        
        assert error.error_type == ErrorType.DATA_VALIDATION_ERROR
        assert error.message == "Test error"
        assert error.severity == "critical"
        assert error.suggestion == "Test fix"
    
    def test_worker_error_to_dict(self):
        """to_dict should include all fields."""
        error = WorkerError(
            error_type=ErrorType.COMPUTATION_ERROR,
            message="Test",
            severity="error",
            details={"key": "value"},
            context={"ctx": "data"}
        )
        
        result_dict = error.to_dict()
        
        assert result_dict["type"] == "computation_error"
        assert result_dict["message"] == "Test"
        assert result_dict["severity"] == "error"
        assert result_dict["details"]["key"] == "value"
        assert result_dict["context"]["ctx"] == "data"
        assert "timestamp" in result_dict


class TestWorkerResult:
    """Test WorkerResult for standardized output."""
    
    def test_worker_result_creation(self):
        """WorkerResult should be created with all fields."""
        result = WorkerResult(
            worker_name="test_worker",
            task_type="test_task",
            success=True,
            data={"key": "value"},
            quality_score=0.95
        )
        
        assert result.worker_name == "test_worker"
        assert result.task_type == "test_task"
        assert result.success is True
        assert result.data["key"] == "value"
        assert result.quality_score == 0.95
    
    def test_worker_result_quality_score_clamping(self):
        """Quality score should be clamped to 0-1 range."""
        result_high = WorkerResult(
            worker_name="test",
            task_type="test",
            quality_score=1.5
        )
        result_low = WorkerResult(
            worker_name="test",
            task_type="test",
            quality_score=-0.5
        )
        
        assert result_high.quality_score == 1.0
        assert result_low.quality_score == 0.0
    
    def test_worker_result_has_errors(self):
        """has_errors should detect presence of errors."""
        result = WorkerResult(
            worker_name="test",
            task_type="test"
        )
        
        assert result.has_errors() is False
        
        error = WorkerError(
            error_type=ErrorType.DATA_VALIDATION_ERROR,
            message="Test error"
        )
        result.errors.append(error)
        
        assert result.has_errors() is True
    
    def test_worker_result_has_critical_errors(self):
        """has_critical_errors should detect critical errors."""
        result = WorkerResult(
            worker_name="test",
            task_type="test"
        )
        
        # Add warning
        warning_error = WorkerError(
            error_type=ErrorType.DATA_VALIDATION_ERROR,
            message="Warning",
            severity="warning"
        )
        result.errors.append(warning_error)
        assert result.has_critical_errors() is False
        
        # Add critical
        critical_error = WorkerError(
            error_type=ErrorType.COMPUTATION_ERROR,
            message="Critical",
            severity="critical"
        )
        result.errors.append(critical_error)
        assert result.has_critical_errors() is True
    
    def test_worker_result_get_error_summary(self):
        """get_error_summary should combine all errors."""
        result = WorkerResult(
            worker_name="test",
            task_type="test"
        )
        
        result.errors.append(WorkerError(
            error_type=ErrorType.DATA_VALIDATION_ERROR,
            message="Error 1"
        ))
        result.errors.append(WorkerError(
            error_type=ErrorType.COMPUTATION_ERROR,
            message="Error 2"
        ))
        
        summary = result.get_error_summary()
        assert "data_validation_error" in summary
        assert "computation_error" in summary
    
    def test_worker_result_to_dict(self):
        """to_dict should include all fields."""
        result = WorkerResult(
            worker_name="test",
            task_type="test_task",
            success=True,
            quality_score=0.85,
            data={"test": "data"}
        )
        result.rows_processed = 100
        result.execution_time_ms = 250
        
        result_dict = result.to_dict()
        
        assert result_dict["worker"] == "test"
        assert result_dict["task_type"] == "test_task"
        assert result_dict["success"] is True
        assert result_dict["quality_score"] == 0.85
        assert result_dict["rows_processed"] == 100
        assert result_dict["execution_time_ms"] == 250


class TestErrorType:
    """Test ErrorType enum."""
    
    def test_error_type_values(self):
        """All ErrorType values should be strings."""
        for error_type in ErrorType:
            assert isinstance(error_type.value, str)
    
    def test_error_type_data_validation(self):
        """DATA_VALIDATION_ERROR should exist."""
        assert hasattr(ErrorType, "DATA_VALIDATION_ERROR")
    
    def test_error_type_computation(self):
        """COMPUTATION_ERROR should exist."""
        assert hasattr(ErrorType, "COMPUTATION_ERROR")
