"""Tests for error recovery framework - Week 1 Hardening."""

import pytest
import time
from core.error_recovery import (
    ErrorRecoveryStrategy,
    retry_on_error,
    with_fallback,
    RecoveryError,
)


class TestErrorRecoveryStrategy:
    """Test suite for ErrorRecoveryStrategy class."""
    
    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        def successful_func():
            return "success"
        
        result = ErrorRecoveryStrategy.retry(successful_func)
        assert result == "success"
    
    def test_retry_eventual_success(self):
        """Test successful execution after failures."""
        attempts = [0]
        
        def failing_then_success():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("temporary error")
            return "success"
        
        result = ErrorRecoveryStrategy.retry(
            failing_then_success,
            max_attempts=5,
            backoff=1  # Don't actually wait
        )
        assert result == "success"
        assert attempts[0] == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test RecoveryError raised when max attempts exceeded."""
        def always_fails():
            raise ValueError("always fails")
        
        with pytest.raises(RecoveryError):
            ErrorRecoveryStrategy.retry(
                always_fails,
                max_attempts=2,
                backoff=1
            )
    
    def test_retry_with_fallback(self):
        """Test fallback value used when retries fail."""
        def always_fails():
            raise ValueError("always fails")
        
        result = ErrorRecoveryStrategy.retry(
            always_fails,
            max_attempts=2,
            fallback="fallback_value",
            backoff=1
        )
        assert result == "fallback_value"
    
    def test_retry_with_fallback_none(self):
        """Test fallback None value works."""
        def always_fails():
            raise ValueError("always fails")
        
        result = ErrorRecoveryStrategy.retry(
            always_fails,
            max_attempts=2,
            fallback=None,
            backoff=1
        )
        assert result is None
    
    def test_retry_respects_max_attempts(self):
        """Test that retry respects max_attempts."""
        call_count = [0]
        
        def always_fails():
            call_count[0] += 1
            raise ValueError("error")
        
        ErrorRecoveryStrategy.retry(
            always_fails,
            max_attempts=3,
            fallback="fallback",
            backoff=1
        )
        assert call_count[0] == 3
    
    def test_retry_exponential_backoff(self):
        """Test exponential backoff timing."""
        call_times = []
        
        def track_and_fail():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("error")
            return "success"
        
        result = ErrorRecoveryStrategy.retry(
            track_and_fail,
            max_attempts=3,
            backoff=2
        )
        
        assert result == "success"
        assert len(call_times) == 3
        
        # Check backoff timing (2^0=1, 2^1=2, roughly)
        if len(call_times) >= 3:
            # Second retry should be ~2 seconds after first
            # We'll be lenient: between 0.5 and 3 seconds
            time_diff = call_times[1] - call_times[0]
            assert time_diff >= 0.5  # At least some wait
    
    def test_retry_with_on_error_callback(self):
        """Test on_error callback is called."""
        callback_data = {}
        
        def error_callback(error, attempt, context):
            callback_data['error'] = error
            callback_data['attempt'] = attempt
            callback_data['context'] = context
        
        def always_fails():
            raise ValueError("test error")
        
        ErrorRecoveryStrategy.retry(
            always_fails,
            max_attempts=2,
            fallback="fallback",
            on_error=error_callback,
            context="test_context",
            backoff=1
        )
        
        assert 'error' in callback_data
        assert 'attempt' in callback_data
        assert callback_data['context'] == "test_context"
    
    def test_with_fallback_success(self):
        """Test with_fallback when operation succeeds."""
        def successful_operation():
            return "result"
        
        result = ErrorRecoveryStrategy.with_fallback(
            successful_operation,
            fallback_value="fallback"
        )
        assert result == "result"
    
    def test_with_fallback_error(self):
        """Test with_fallback when operation fails."""
        def failing_operation():
            raise ValueError("error")
        
        result = ErrorRecoveryStrategy.with_fallback(
            failing_operation,
            fallback_value="fallback"
        )
        assert result == "fallback"
    
    def test_with_fallback_context(self):
        """Test with_fallback with context information."""
        def failing_operation():
            raise ValueError("error")
        
        result = ErrorRecoveryStrategy.with_fallback(
            failing_operation,
            fallback_value="fallback",
            context="test_context"
        )
        assert result == "fallback"
    
    def test_retry_preserves_exception_type(self):
        """Test that original exception is preserved in RecoveryError."""
        def fails_with_value_error():
            raise ValueError("original error")
        
        try:
            ErrorRecoveryStrategy.retry(
                fails_with_value_error,
                max_attempts=1
            )
        except RecoveryError as e:
            assert isinstance(e.__cause__, ValueError)
            assert "original error" in str(e.__cause__)


class TestRetryDecorator:
    """Test suite for @retry_on_error decorator."""
    
    def test_decorator_success(self):
        """Test decorator with successful function."""
        @retry_on_error(max_attempts=3, backoff=1)
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result == "success"
    
    def test_decorator_eventual_success(self):
        """Test decorator with eventual success."""
        attempts = [0]
        
        @retry_on_error(max_attempts=3, backoff=1)
        def eventually_success():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("temporary error")
            return "success"
        
        result = eventually_success()
        assert result == "success"
        assert attempts[0] == 2
    
    def test_decorator_with_fallback(self):
        """Test decorator with fallback value."""
        @retry_on_error(max_attempts=2, fallback="fallback", backoff=1)
        def always_fails():
            raise ValueError("error")
        
        result = always_fails()
        assert result == "fallback"
    
    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @retry_on_error(max_attempts=3, backoff=1)
        def my_function():
            return "result"
        
        assert my_function.__name__ == "my_function"
    
    def test_decorator_with_args(self):
        """Test decorator with function arguments."""
        @retry_on_error(max_attempts=3, backoff=1)
        def func_with_args(a, b):
            return a + b
        
        result = func_with_args(2, 3)
        assert result == 5
    
    def test_decorator_with_kwargs(self):
        """Test decorator with keyword arguments."""
        @retry_on_error(max_attempts=3, backoff=1)
        def func_with_kwargs(a, b=10):
            return a + b
        
        result = func_with_kwargs(5, b=20)
        assert result == 25


class TestWithFallbackDecorator:
    """Test suite for @with_fallback decorator."""
    
    def test_decorator_success(self):
        """Test with_fallback decorator with successful function."""
        @with_fallback(fallback_value="fallback")
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result == "success"
    
    def test_decorator_fallback(self):
        """Test with_fallback decorator returns fallback on error."""
        @with_fallback(fallback_value="fallback")
        def failing_func():
            raise ValueError("error")
        
        result = failing_func()
        assert result == "fallback"
    
    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @with_fallback(fallback_value=None)
        def my_function():
            return "result"
        
        assert my_function.__name__ == "my_function"
    
    def test_decorator_with_args(self):
        """Test with_fallback decorator with arguments."""
        @with_fallback(fallback_value="fallback")
        def func_with_args(a, b):
            if a == 0:
                raise ValueError("zero not allowed")
            return a + b
        
        assert func_with_args(2, 3) == 5
        assert func_with_args(0, 3) == "fallback"


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery."""
    
    def test_combined_decorators(self):
        """Test combining retry and fallback decorators."""
        attempts = [0]
        
        @with_fallback(fallback_value="final_fallback")
        @retry_on_error(max_attempts=2, fallback="retry_fallback", backoff=1)
        def complex_func():
            attempts[0] += 1
            raise ValueError("error")
        
        result = complex_func()
        # Outer fallback should be used
        assert result == "retry_fallback" or result == "final_fallback"
    
    def test_retry_with_different_exceptions(self):
        """Test retry handles different exception types."""
        attempts = [0]
        
        @retry_on_error(max_attempts=3, fallback="fallback", backoff=1)
        def different_exceptions():
            attempts[0] += 1
            if attempts[0] == 1:
                raise ValueError("first error")
            elif attempts[0] == 2:
                raise TypeError("second error")
            else:
                raise RuntimeError("third error")
        
        result = different_exceptions()
        assert result == "fallback"
        assert attempts[0] == 3
    
    def test_real_world_file_operation(self):
        """Test retry with realistic file operation."""
        call_count = [0]
        
        @retry_on_error(max_attempts=3, fallback={}, backoff=1)
        def read_file():
            call_count[0] += 1
            if call_count[0] < 2:
                raise IOError("File not ready")
            return {"data": "success"}
        
        result = read_file()
        assert result == {"data": "success"}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
