"""Tests for structured logging system - Week 1 Hardening."""

import pytest
import json
import tempfile
from pathlib import Path
from core.structured_logger import (
    StructuredLogger,
    get_structured_logger,
    log_operation,
    log_metrics,
    JSONFormatter,
)
import logging


class TestJSONFormatter:
    """Test JSON formatter."""
    
    def test_format_basic_record(self):
        """Test formatting basic log record."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['level'] == 'INFO'
        assert data['message'] == 'Test message'
        assert 'timestamp' in data
        assert data['logger'] == 'test_logger'
    
    def test_format_record_with_function(self):
        """Test formatting record with function info."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test_logger',
            level=logging.ERROR,
            pathname='test.py',
            lineno=20,
            msg='Error occurred',
            args=(),
            exc_info=None,
        )
        record.funcName = 'my_function'
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['level'] == 'ERROR'
        assert data['function'] == 'my_function'
        assert data['line'] == 20


class TestStructuredLogger:
    """Test suite for StructuredLogger."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_logger_initialization(self, temp_log_dir):
        """Test logger initialization."""
        logger = StructuredLogger('test', temp_log_dir)
        assert logger.name == 'test'
        assert Path(temp_log_dir).exists()
    
    def test_logger_debug(self, temp_log_dir):
        """Test debug logging."""
        logger = StructuredLogger('test', temp_log_dir)
        logger.debug('Debug message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
        assert metrics['by_level'].get('DEBUG', 0) == 1
    
    def test_logger_info(self, temp_log_dir):
        """Test info logging."""
        logger = StructuredLogger('test', temp_log_dir)
        logger.info('Info message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
        assert metrics['by_level'].get('INFO', 0) == 1
    
    def test_logger_warning(self, temp_log_dir):
        """Test warning logging."""
        logger = StructuredLogger('test', temp_log_dir)
        logger.warning('Warning message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
        assert metrics['by_level'].get('WARNING', 0) == 1
    
    def test_logger_error(self, temp_log_dir):
        """Test error logging."""
        logger = StructuredLogger('test', temp_log_dir)
        logger.error('Error message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
        assert metrics['by_level'].get('ERROR', 0) == 1
    
    def test_logger_critical(self, temp_log_dir):
        """Test critical logging."""
        logger = StructuredLogger('test', temp_log_dir)
        logger.critical('Critical message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
        assert metrics['by_level'].get('CRITICAL', 0) == 1
    
    def test_logger_with_extra_data(self, temp_log_dir):
        """Test logging with extra data."""
        logger = StructuredLogger('test', temp_log_dir)
        logger.info('Message', extra={'user_id': 123, 'action': 'login'})
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
    
    def test_multiple_log_levels(self, temp_log_dir):
        """Test logging multiple levels."""
        logger = StructuredLogger('test', temp_log_dir)
        
        logger.debug('Debug')
        logger.info('Info')
        logger.warning('Warning')
        logger.error('Error')
        logger.critical('Critical')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 5
        assert metrics['by_level']['DEBUG'] == 1
        assert metrics['by_level']['INFO'] == 1
        assert metrics['by_level']['WARNING'] == 1
        assert metrics['by_level']['ERROR'] == 1
        assert metrics['by_level']['CRITICAL'] == 1
    
    def test_operation_context_success(self, temp_log_dir):
        """Test operation context manager (success case)."""
        logger = StructuredLogger('test', temp_log_dir)
        
        with logger.operation('load_data', {'file': 'data.csv'}):
            result = 42
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 2  # Started + completed
        assert 'load_data' in metrics['operations']
        assert metrics['operations']['load_data'][0]['status'] == 'success'
    
    def test_operation_context_failure(self, temp_log_dir):
        """Test operation context manager (failure case)."""
        logger = StructuredLogger('test', temp_log_dir)
        
        with pytest.raises(ValueError):
            with logger.operation('risky_operation'):
                raise ValueError('Something went wrong')
        
        metrics = logger.get_metrics()
        assert 'risky_operation' in metrics['operations']
        assert metrics['operations']['risky_operation'][0]['status'] == 'failed'
    
    def test_operation_context_timing(self, temp_log_dir):
        """Test operation timing is recorded."""
        import time
        logger = StructuredLogger('test', temp_log_dir)
        
        with logger.operation('slow_operation'):
            time.sleep(0.1)
        
        metrics = logger.get_metrics()
        elapsed = metrics['operations']['slow_operation'][0]['elapsed']
        assert elapsed >= 0.1
    
    def test_metrics_reset(self, temp_log_dir):
        """Test metrics reset."""
        logger = StructuredLogger('test', temp_log_dir)
        
        logger.info('Message 1')
        logger.info('Message 2')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 2
        
        logger.reset_metrics()
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 0
    
    def test_operation_with_multiple_calls(self, temp_log_dir):
        """Test operation metrics with multiple calls."""
        logger = StructuredLogger('test', temp_log_dir)
        
        # First call
        with logger.operation('database_query'):
            pass
        
        # Second call
        with logger.operation('database_query'):
            pass
        
        metrics = logger.get_metrics()
        assert len(metrics['operations']['database_query']) == 2


class TestGetStructuredLogger:
    """Test suite for get_structured_logger function."""
    
    def test_get_logger(self):
        """Test get_structured_logger."""
        logger = get_structured_logger('test_logger')
        assert logger is not None
        assert isinstance(logger, StructuredLogger)
    
    def test_get_logger_caching(self):
        """Test logger caching."""
        logger1 = get_structured_logger('cached_logger')
        logger2 = get_structured_logger('cached_logger')
        
        # Should return same instance
        assert logger1 is logger2
    
    def test_get_logger_different_names(self):
        """Test different logger names."""
        logger1 = get_structured_logger('logger1')
        logger2 = get_structured_logger('logger2')
        
        # Should be different instances
        assert logger1 is not logger2
    
    def test_get_logger_with_custom_dir(self):
        """Test get_structured_logger with custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('test', tmpdir)
            assert logger is not None


class TestLogOperationDecorator:
    """Test suite for @log_operation decorator."""
    
    def test_decorator_success(self):
        """Test decorator with successful operation."""
        @log_operation('test_operation')
        def my_operation():
            return 'success'
        
        result = my_operation()
        assert result == 'success'
    
    def test_decorator_with_args(self):
        """Test decorator with function arguments."""
        @log_operation('add_numbers')
        def add(a, b):
            return a + b
        
        result = add(2, 3)
        assert result == 5
    
    def test_decorator_with_kwargs(self):
        """Test decorator with keyword arguments."""
        @log_operation('multiply')
        def multiply(a, b=2):
            return a * b
        
        result = multiply(5, b=3)
        assert result == 15
    
    def test_decorator_error_propagation(self):
        """Test that decorator propagates errors."""
        @log_operation('failing_operation')
        def failing_op():
            raise ValueError('Test error')
        
        with pytest.raises(ValueError):
            failing_op()
    
    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @log_operation('operation_name')
        def my_function():
            return 'result'
        
        assert my_function.__name__ == 'my_function'


class TestLogMetricsDecorator:
    """Test suite for @log_metrics decorator."""
    
    def test_decorator_success(self):
        """Test metrics decorator with successful operation."""
        @log_metrics('metric_test')
        def my_function():
            return 'success'
        
        result = my_function()
        assert result == 'success'
    
    def test_decorator_with_args(self):
        """Test metrics decorator with arguments."""
        @log_metrics('square')
        def square(x):
            return x ** 2
        
        result = square(5)
        assert result == 25
    
    def test_decorator_error_handling(self):
        """Test metrics decorator error handling."""
        @log_metrics('error_metric')
        def failing_op():
            raise RuntimeError('Test error')
        
        with pytest.raises(RuntimeError):
            failing_op()
    
    def test_decorator_preserves_function_name(self):
        """Test that metrics decorator preserves function name."""
        @log_metrics('op_name')
        def my_function():
            return 'result'
        
        assert my_function.__name__ == 'my_function'


class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_multiple_operations(self):
        """Test multiple operations with logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('integration_test', tmpdir)
            
            with logger.operation('op1'):
                logger.info('Operation 1 running')
            
            with logger.operation('op2'):
                logger.info('Operation 2 running')
            
            with logger.operation('op3'):
                logger.warning('Operation 3 warning')
            
            metrics = logger.get_metrics()
            assert metrics['total_logs'] == 9  # 3 operations x (start + log + end)
    
    def test_nested_operations(self):
        """Test nested operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('nested_test', tmpdir)
            
            with logger.operation('outer'):
                logger.info('Outer operation')
                with logger.operation('inner'):
                    logger.info('Inner operation')
            
            metrics = logger.get_metrics()
            assert 'outer' in metrics['operations']
            assert 'inner' in metrics['operations']
    
    def test_decorator_with_operation_context(self):
        """Test combining decorator with operation context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('decorator_test', tmpdir)
            
            @log_operation('decorated_op')
            def decorated_function():
                logger.info('Inside decorated function')
                return 'result'
            
            result = decorated_function()
            assert result == 'result'
    
    def test_file_logging(self):
        """Test that logs are written to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('file_test', tmpdir)
            logger.info('Test message')
            
            log_file = Path(tmpdir) / 'file_test.log'
            assert log_file.exists()
            assert log_file.stat().st_size > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
