"""Pytest configuration for GOAT Data Analyst tests.

This file configures pytest to properly handle:
- Logging setup and teardown
- File handle cleanup
- Pytest capture integration with custom logging
- Prevents I/O operation on closed file errors
"""

import pytest
import logging
import sys
from pathlib import Path


def pytest_configure(config):
    """Configure pytest at session start."""
    # Disable pytest's log capture to avoid conflicts with our logging
    logging.getLogger().setLevel(logging.WARNING)
    
    # DO NOT disable capture - causes issues
    # Let pytest handle its own capture
    
    # Safely disable the logging plugin
    try:
        config.pluginmanager.set_blocked("logging")
    except Exception:
        pass
    
    # Close any existing file handlers to prevent I/O issues
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.FileHandler):
            try:
                handler.close()
                root_logger.removeHandler(handler)
            except Exception:
                pass


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Clean up logging between tests."""
    yield
    # After each test, clean up logger cache
    try:
        from core.structured_logger import _logger_cache
        # Close all loggers
        for (name, log_dir), logger in list(_logger_cache.items()):
            if hasattr(logger, 'close'):
                try:
                    logger.close()
                except Exception:
                    pass
        # Clear the cache
        _logger_cache.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_logger_handlers():
    """Reset logging handlers before each test."""
    # Get root logger and remove all handlers
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        try:
            handler.close()
            root_logger.removeHandler(handler)
        except Exception:
            pass
    
    yield
    
    # Cleanup after test
    for handler in list(root_logger.handlers):
        try:
            handler.close()
            root_logger.removeHandler(handler)
        except Exception:
            pass


@pytest.fixture
def temp_log_dir(tmp_path):
    """Provide a temporary directory for logs."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip problematic tests in CI."""
    # Mark performance tests to run separately
    for item in items:
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)


def pytest_runtest_makereport(item, call):
    """Hook to clean up after each test."""
    if call.when == "teardown":
        # Clean up any open file handles
        try:
            import gc
            gc.collect()
        except Exception:
            pass
