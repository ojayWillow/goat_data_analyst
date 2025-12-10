"""Tests for structured logging system - Week 1 Hardening."""

import pytest
import json
from core.structured_logger import (
    StructuredLogger,
    get_structured_logger,
    log_operation,
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
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        logger = StructuredLogger('test', './logs')
        assert logger.name == 'test'
    
    def test_logger_debug(self):
        """Test debug logging."""
        logger = StructuredLogger('test', './logs')
        logger.debug('Debug message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
    
    def test_logger_info(self):
        """Test info logging."""
        logger = StructuredLogger('test', './logs')
        logger.info('Info message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
    
    def test_logger_warning(self):
        """Test warning logging."""
        logger = StructuredLogger('test', './logs')
        logger.warning('Warning message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
    
    def test_logger_error(self):
        """Test error logging."""
        logger = StructuredLogger('test', './logs')
        logger.error('Error message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
    
    def test_logger_critical(self):
        """Test critical logging."""
        logger = StructuredLogger('test', './logs')
        logger.critical('Critical message')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
    
    def test_logger_with_extra_data(self):
        """Test logging with extra data."""
        logger = StructuredLogger('test', './logs')
        logger.info('Message', extra={'user_id': 123, 'action': 'login'})
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 1
    
    def test_multiple_log_levels(self):
        """Test logging multiple levels."""
        logger = StructuredLogger('test', './logs')
        
        logger.debug('Debug')
        logger.info('Info')
        logger.warning('Warning')
        logger.error('Error')
        logger.critical('Critical')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 5
    
    def test_operation_context_success(self):
        """Test operation context manager (success case)."""
        logger = StructuredLogger('test', './logs')
        
        with logger.operation('load_data', {'file': 'data.csv'}):
            result = 42
        
        metrics = logger.get_metrics()
        assert 'load_data' in metrics['operations']
        assert metrics['operations']['load_data'][0]['status'] == 'success'
    
    def test_operation_context_failure(self):
        """Test operation context manager (failure case)."""
        logger = StructuredLogger('test', './logs')
        
        with pytest.raises(ValueError):
            with logger.operation('risky_operation'):
                raise ValueError('Something went wrong')
        
        metrics = logger.get_metrics()
        assert 'risky_operation' in metrics['operations']
        assert metrics['operations']['risky_operation'][0]['status'] == 'failed'
    
    def test_metrics_reset(self):
        """Test metrics reset."""
        logger = StructuredLogger('test', './logs')
        
        logger.info('Message 1')
        logger.info('Message 2')
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 2
        
        logger.reset_metrics()
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 0
    
    def test_operation_with_multiple_calls(self):
        """Test operation metrics with multiple calls."""
        logger = StructuredLogger('test', './logs')
        
        with logger.operation('database_query'):
            pass
        
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
        
        assert logger1 is logger2
    
    def test_get_logger_different_names(self):
        """Test different logger names."""
        logger1 = get_structured_logger('logger1')
        logger2 = get_structured_logger('logger2')
        
        assert logger1 is not logger2


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
