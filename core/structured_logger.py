"""Structured Logging System for GOAT Data Analyst - Hardening Phase 1

Provides comprehensive logging with:
- JSON structured logging
- Performance metrics
- Audit trail support
- Context preservation
- Integration with configuration

Usage:
    from core.structured_logger import get_structured_logger
    
    logger = get_structured_logger(__name__)
    logger.info('Operation started', extra={'user_id': 123, 'action': 'load'})
    logger.error('Operation failed', extra={'error_code': 'E001', 'retry_count': 2})
"""

import logging
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from pathlib import Path
import functools
from contextlib import contextmanager
import sys
import os


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string
        """
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, default=str)


class StructuredLogger:
    """Structured logger with metrics and audit trail support."""
    
    def __init__(self, name: str, log_dir: str = './logs'):
        """Initialize structured logger.
        
        Args:
            name: Logger name (usually __name__)
            log_dir: Directory for log files
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.file_handler = None
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # Prevent duplicate logs
        
        # Remove existing handlers to avoid duplicates
        for handler in list(self.logger.handlers):
            try:
                handler.close()
            except Exception:
                pass
            self.logger.removeHandler(handler)
        
        # Console handler (JSON formatted) - ONLY if not in pytest
        if 'pytest' not in sys.modules:
            try:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)
                console_handler.setFormatter(JSONFormatter())
                self.logger.addHandler(console_handler)
            except Exception:
                pass
        
        # File handler (JSON formatted) - only if not in pytest
        if 'pytest' not in sys.modules:
            try:
                file_path = self.log_dir / f"{name.replace('.', '_')}.log"
                self.file_handler = logging.FileHandler(file_path, mode='a')
                self.file_handler.setLevel(logging.DEBUG)
                self.file_handler.setFormatter(JSONFormatter())
                self.logger.addHandler(self.file_handler)
            except (IOError, OSError):
                # If file can't be created, just use console
                pass
        
        # Metrics
        self.metrics = {
            'total_logs': 0,
            'by_level': {},
            'operations': {},
        }
    
    def _log_with_extra(self, level: int, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log with extra data.
        
        Args:
            level: Log level
            msg: Log message
            extra: Extra data dictionary
        """
        try:
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                '',
                0,
                msg,
                (),
                None,
            )
            
            if extra:
                record.extra_data = extra
            
            # Update metrics
            self.metrics['total_logs'] += 1
            level_name = logging.getLevelName(level)
            self.metrics['by_level'][level_name] = self.metrics['by_level'].get(level_name, 0) + 1
            
            self.logger.handle(record)
        except Exception:
            # Silently fail if logging fails (don't crash the app)
            pass
    
    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log_with_extra(logging.DEBUG, msg, extra)
    
    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log_with_extra(logging.INFO, msg, extra)
    
    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log_with_extra(logging.WARNING, msg, extra)
    
    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None, exc_info=False):
        """Log error message."""
        try:
            record = self.logger.makeRecord(
                self.logger.name,
                logging.ERROR,
                '',
                0,
                msg,
                (),
                None,
            )
            
            if extra:
                record.extra_data = extra
            
            if exc_info:
                record.exc_info = sys.exc_info()
            
            self.metrics['total_logs'] += 1
            self.metrics['by_level']['ERROR'] = self.metrics['by_level'].get('ERROR', 0) + 1
            self.logger.handle(record)
        except Exception:
            pass
    
    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._log_with_extra(logging.CRITICAL, msg, extra)
    
    @contextmanager
    def operation(self, operation_name: str, context: Optional[Dict[str, Any]] = None):
        """Context manager for operation tracking.
        
        Args:
            operation_name: Name of operation
            context: Additional context data
            
        Example:
            with logger.operation('load_data', {'file': 'data.csv'}):
                result = load_data('data.csv')
        """
        start_time = time.time()
        context = context or {}
        
        self.info(f"Operation started: {operation_name}", extra=context)
        
        try:
            yield
            elapsed = time.time() - start_time
            self.info(
                f"Operation completed: {operation_name}",
                extra={
                    **context,
                    'elapsed_seconds': round(elapsed, 3),
                    'status': 'success'
                }
            )
            
            # Track operation metrics
            if operation_name not in self.metrics['operations']:
                self.metrics['operations'][operation_name] = []
            self.metrics['operations'][operation_name].append({
                'elapsed': elapsed,
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        except Exception as e:
            elapsed = time.time() - start_time
            self.error(
                f"Operation failed: {operation_name}: {e}",
                extra={
                    **context,
                    'elapsed_seconds': round(elapsed, 3),
                    'status': 'failed',
                    'error': str(e)
                },
                exc_info=True
            )
            
            # Track operation metrics
            if operation_name not in self.metrics['operations']:
                self.metrics['operations'][operation_name] = []
            self.metrics['operations'][operation_name].append({
                'elapsed': elapsed,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics.
        
        Returns:
            Dictionary with metrics
        """
        return {
            'total_logs': self.metrics['total_logs'],
            'by_level': self.metrics['by_level'],
            'operations': self.metrics['operations'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
    
    def reset_metrics(self):
        """Reset metrics."""
        self.metrics = {
            'total_logs': 0,
            'by_level': {},
            'operations': {},
        }
    
    def close(self):
        """Close all handlers safely."""
        try:
            for handler in list(self.logger.handlers):
                try:
                    handler.flush()
                    handler.close()
                except Exception:
                    pass
                try:
                    self.logger.removeHandler(handler)
                except Exception:
                    pass
        except Exception:
            pass


# Global logger cache
_logger_cache = {}

def get_structured_logger(name: str, log_dir: str = './logs') -> StructuredLogger:
    """Get or create structured logger.
    
    Args:
        name: Logger name (usually __name__)
        log_dir: Directory for log files
        
    Returns:
        StructuredLogger instance
    """
    cache_key = (name, log_dir)
    if cache_key not in _logger_cache:
        _logger_cache[cache_key] = StructuredLogger(name, log_dir)
    return _logger_cache[cache_key]


def log_operation(operation_name: str):
    """Decorator for operation logging.
    
    Args:
        operation_name: Name of operation
        
    Example:
        @log_operation('load_data')
        def load_data(filepath):
            return pd.read_csv(filepath)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)
            with logger.operation(operation_name or func.__name__):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_metrics(operation_name: str):
    """Decorator for metrics logging.
    
    Args:
        operation_name: Name of operation
        
    Example:
        @log_metrics('process_data')
        def process_data(data):
            return data * 2
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    f"Metric logged: {operation_name}",
                    extra={
                        'operation': operation_name,
                        'elapsed_seconds': round(elapsed, 3),
                        'status': 'success'
                    }
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Metric logged: {operation_name}",
                    extra={
                        'operation': operation_name,
                        'elapsed_seconds': round(elapsed, 3),
                        'status': 'failed',
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator
