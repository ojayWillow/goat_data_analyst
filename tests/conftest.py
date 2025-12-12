"""Pytest configuration for GOAT Data Analyst tests."""

import pytest
import logging
import sys
import warnings
from pathlib import Path
import io

# Suppress ALL closed file warnings and I/O errors
warnings.filterwarnings("ignore", message=".*I/O operation on closed file.*")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=".*unclosed file.*")


def pytest_configure(config):
    """Configure pytest at session start."""
    # Suppress I/O warnings from logging cleanup
    warnings.filterwarnings("ignore", message=".*I/O operation on closed file.*")
    warnings.filterwarnings("ignore", category=ResourceWarning)
    
    # Close ALL file handlers to prevent I/O errors during test collection
    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, logging.FileHandler):
            try:
                handler.close()
                root.removeHandler(handler)
            except (ValueError, OSError, AttributeError):
                # Already closed or other I/O error - ignore
                pass


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Clean up logging between tests."""
    yield
    
    # Suppress warnings during cleanup
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*I/O operation on closed file.*")
        warnings.filterwarnings("ignore", category=ResourceWarning)
        
        try:
            from core.structured_logger import _logger_cache
            for logger in list(_logger_cache.values()):
                try:
                    if hasattr(logger, 'close'):
                        logger.close()
                except (ValueError, OSError, AttributeError):
                    # Already closed or other I/O error - ignore
                    pass
            _logger_cache.clear()
        except (ImportError, AttributeError, Exception):
            pass

        # Also clean up root logger handlers
        try:
            root = logging.getLogger()
            for handler in list(root.handlers):
                try:
                    if hasattr(handler, 'close') and not isinstance(handler.stream, sys.stderr):
                        handler.close()
                    root.removeHandler(handler)
                except (ValueError, OSError, AttributeError):
                    # Already closed or other I/O error - ignore
                    pass
        except (AttributeError, Exception):
            pass


@pytest.fixture
def temp_log_dir(tmp_path):
    """Provide a temporary directory for logs."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir)


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        if "performance" in item.nodeid.lower() or "1m" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
