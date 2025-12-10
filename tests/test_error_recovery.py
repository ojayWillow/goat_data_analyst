"""Tests for error recovery framework - Week 1 Hardening."""

import pytest
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
            backoff=0
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
                backoff=0
            )
    
    def test_retry_with_fallback(self):
        """Test fallback value used when retries fail."""
        def always_fails():
            raise ValueError("always fails")
        
        result = ErrorRecoveryStrategy.retry(
            always_fails,
            max_attempts=2,
            fallback="fallback_value",
            backoff=0
        )
        assert result == "fallback_value"
    
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
            backoff=0
        )
        assert call_count[0] == 3
    
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


class TestRetryDecorator:
    """Test suite for @retry_on_error decorator."""
    
    def test_decorator_success(self):
        """Test decorator with successful function."""
        @retry_on_error(max_attempts=3, backoff=0)
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result == "success"
    
    def test_decorator_eventual_success(self):
        """Test decorator with eventual success."""
        attempts = [0]
        
        @retry_on_error(max_attempts=3, backoff=0)
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
        @retry_on_error(max_attempts=2, fallback="fallback", backoff=0)
        def always_fails():
            raise ValueError("error")
        
        result = always_fails()
        assert result == "fallback"
    
    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @retry_on_error(max_attempts=3, backoff=0)
        def my_function():
            return "result"
        
        assert my_function.__name__ == "my_function"
    
    def test_decorator_with_args(self):
        """Test decorator with function arguments."""
        @retry_on_error(max_attempts=3, backoff=0)
        def func_with_args(a, b):
            return a + b
        
        result = func_with_args(2, 3)
        assert result == 5


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
