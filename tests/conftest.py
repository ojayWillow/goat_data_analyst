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
    # Just set log level, don't touch handlers
    logging.getLogger().setLevel(logging.WARNING)


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Clean up logging between tests."""
    yield
    # After each test, clean up logger cache
    try:
        from core.structured_logger import _logger_cache
        for (name, log_dir), logger in list(_logger_cache.items()):
            try:
                if hasattr(logger, 'close'):
                    logger.close()
            except Exception:
                pass
        _logger_cache.clear()
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
    for item in items:
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
