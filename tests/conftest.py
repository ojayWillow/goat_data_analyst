"""Pytest configuration for GOAT Data Analyst tests.

This file configures pytest to properly handle:
- Logging setup and teardown
- File handle cleanup
- Pytest capture integration with custom logging
"""

import pytest
import logging
import sys
from pathlib import Path


@pytest.fixture(scope="session")
def pytest_configure(config):
    """Configure pytest at session start."""
    # Disable pytest's log capture to avoid conflicts with our logging
    logging.getLogger().setLevel(logging.WARNING)
    

@pytest.fixture(autouse=True)
def cleanup_logging():
    """Clean up logging between tests."""
    yield
    # After each test, clean up logger cache
    try:
        from core.structured_logger import _logger_cache
        # Close all loggers
        for (name, log_dir), logger in _logger_cache.items():
            if hasattr(logger, 'close'):
                logger.close()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_logger_handlers():
    """Reset logging handlers before each test."""
    # Get root logger and remove all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        try:
            handler.close()
            root_logger.removeHandler(handler)
        except Exception:
            pass
    
    yield
    
    # Cleanup after test
    for handler in root_logger.handlers[:]:
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


# Add hooks to handle test outcomes
def pytest_runtest_makereport(item, call):
    """Hook to clean up after each test."""
    if call.when == "teardown":
        # Clean up any open file handles
        try:
            import gc
            gc.collect()
        except Exception:
            pass
