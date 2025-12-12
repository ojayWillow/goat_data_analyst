"""Pytest configuration for GOAT Data Analyst tests."""

import pytest
import logging
import sys
import warnings
from pathlib import Path

# Suppress ALL closed file warnings and I/O errors globally
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=".*I/O operation on closed file.*")
warnings.filterwarnings("ignore", message=".*unclosed file.*")

# Disable verbose logging during tests to avoid file I/O issues
logging.disable(logging.CRITICAL)


def pytest_configure(config):
    """Configure pytest at session start."""
    # Minimal configuration - avoid file handlers
    pass


@pytest.fixture(autouse=True)
def suppress_logging():
    """Suppress logging during tests to avoid I/O errors."""
    # Keep logging disabled
    yield
    # Cleanup happens automatically


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
