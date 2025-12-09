"""Error Recovery Framework for GOAT Data Analyst - Hardening Phase 1

Provides robust error handling with:
- Retry logic with exponential backoff
- Timeout protection
- Graceful degradation
- Detailed error context
- Recovery strategies

Usage:
    from core.error_recovery import ErrorRecoveryStrategy, retry_on_error
    
    # Using decorator:
    @retry_on_error(max_attempts=3, backoff=2)
    def load_data(file_path):
        return pd.read_csv(file_path)
    
    # Using context manager:
    result = ErrorRecoveryStrategy.retry(
        func=lambda: pd.read_csv('data.csv'),
        max_attempts=3,
        fallback=None
    )
"""

import time
import functools
from typing import Callable, Any, Optional, TypeVar
from core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RecoveryError(Exception):
    """Exception raised when all recovery attempts fail."""
    pass


class ErrorRecoveryStrategy:
    """Provides retry logic, timeouts, and graceful degradation."""
    
    @staticmethod
    def retry(
        func: Callable[..., T],
        max_attempts: int = 3,
        backoff: int = 2,
        timeout: Optional[int] = None,
        fallback: Optional[T] = None,
        on_error: Optional[Callable] = None,
        context: Optional[str] = None,
    ) -> T:
        """Retry a function with exponential backoff.
        
        Args:
            func: Function to execute
            max_attempts: Number of retry attempts
            backoff: Exponential backoff multiplier
            timeout: Timeout per attempt in seconds
            fallback: Value to return if all retries fail
            on_error: Callback function for errors
            context: Context string for logging
            
        Returns:
            Function result or fallback value
            
        Raises:
            RecoveryError: If all retries fail and no fallback provided
        """
        last_exception = None
        context_str = f" ({context})" if context else ""
        
        for attempt in range(max_attempts):
            try:
                if timeout:
                    return ErrorRecoveryStrategy._execute_with_timeout(func, timeout)
                else:
                    return func()
            
            except Exception as e:
                last_exception = e
                
                if attempt == max_attempts - 1:
                    # Last attempt failed
                    if on_error:
                        try:
                            on_error(e, attempt, context)
                        except Exception as callback_error:
                            logger.warning(f"Error in on_error callback: {callback_error}")
                    
                    if fallback is not None:
                        logger.warning(
                            f"All {max_attempts} retry attempts failed{context_str}. "
                            f"Using fallback value. Last error: {e}"
                        )
                        return fallback
                    
                    error_msg = f"Recovery failed after {max_attempts} attempts{context_str}: {e}"
                    logger.error(error_msg)
                    raise RecoveryError(error_msg) from e
                
                # Calculate backoff
                wait_time = backoff ** attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed{context_str}. "
                    f"Error: {type(e).__name__}: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
    
    @staticmethod
    def _execute_with_timeout(
        func: Callable[..., T],
        timeout_seconds: int
    ) -> T:
        """Execute function with timeout (for non-blocking operations).
        
        Args:
            func: Function to execute
            timeout_seconds: Timeout in seconds
            
        Returns:
            Function result
            
        Raises:
            TimeoutError: If function exceeds timeout
        """
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation exceeded {timeout_seconds}s timeout")
        
        # Set signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            result = func()
            signal.alarm(0)  # Cancel alarm
            return result
        except Exception as e:
            signal.alarm(0)  # Cancel alarm
            raise
        finally:
            signal.signal(signal.SIGALRM, old_handler)
    
    @staticmethod
    def with_fallback(
        func: Callable[..., T],
        fallback_value: T,
        context: Optional[str] = None,
    ) -> T:
        """Execute function with fallback value on any error.
        
        Args:
            func: Function to execute
            fallback_value: Value to return on error
            context: Context string for logging
            
        Returns:
            Function result or fallback value
        """
        context_str = f" ({context})" if context else ""
        try:
            return func()
        except Exception as e:
            logger.warning(f"Operation failed{context_str}: {e}. Using fallback value.")
            return fallback_value


def retry_on_error(
    max_attempts: int = 3,
    backoff: int = 2,
    timeout: Optional[int] = None,
    fallback: Optional[Any] = None,
):
    """Decorator for retry logic.
    
    Args:
        max_attempts: Number of attempts
        backoff: Backoff multiplier
        timeout: Timeout per attempt
        fallback: Fallback value
        
    Returns:
        Decorated function
        
    Example:
        @retry_on_error(max_attempts=3, backoff=2)
        def load_data(path):
            return pd.read_csv(path)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return ErrorRecoveryStrategy.retry(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                backoff=backoff,
                timeout=timeout,
                fallback=fallback,
                context=func.__name__,
            )
        return wrapper
    return decorator


def with_fallback(fallback_value: Any):
    """Decorator for fallback value on error.
    
    Args:
        fallback_value: Value to return on error
        
    Returns:
        Decorated function
        
    Example:
        @with_fallback(fallback_value=None)
        def risky_operation():
            return compute_something()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return ErrorRecoveryStrategy.with_fallback(
                lambda: func(*args, **kwargs),
                fallback_value=fallback_value,
                context=func.__name__,
            )
        return wrapper
    return decorator
