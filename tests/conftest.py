"""Pytest configuration for GOAT Data Analyst tests."""

import pytest
import warnings

# Suppress ALL warnings
warnings.filterwarnings("ignore")


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
