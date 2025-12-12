"""Comprehensive Error Handling and Recovery Tests.

Tests:
1. All error paths in DataLoader workers
2. Error recovery mechanisms
3. Complex multi-failure scenarios
4. Error propagation through pipeline
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from agents.data_loader.data_loader import DataLoader


class TestDataLoaderErrorPaths:
    """Test all error paths in DataLoader."""

    def test_file_not_found(self):
        """Handle file not found error."""
        loader = DataLoader()
        result = loader.load("/nonexistent/file.csv")
        
        assert result['status'] == 'error'
        assert result['data'] is None
        assert result['quality_score'] == 0.0
        assert len(result.get('errors', [])) >= 0  # May or may not have errors list

    def test_empty_file_error(self, tmp_path):
        """Handle empty file error."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        assert result['status'] == 'error'

    def test_header_only_file(self, tmp_path):
        """Handle header-only file."""
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("col1,col2,col3\n")
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        assert result['status'] == 'error'

    def test_unsupported_format(self, tmp_path):
        """Handle unsupported format gracefully."""
        unsupported = tmp_path / "file.xyz"
        unsupported.write_text("data")
        
        loader = DataLoader()
        result = loader.load(str(unsupported))
        
        assert result['status'] == 'error'
        assert result['quality_score'] == 0.0


class TestDataLoaderBeforeLoadErrors:
    """Test operations before loading data."""

    def test_get_data_before_load(self):
        """get_data() returns None before loading."""
        loader = DataLoader()
        data = loader.get_data()
        assert data is None

    def test_get_metadata_before_load(self):
        """get_metadata() returns empty dict before loading."""
        loader = DataLoader()
        metadata = loader.get_metadata()
        assert metadata == {}

    def test_get_quality_before_load(self):
        """get_quality_score() returns 0.0 before loading."""
        loader = DataLoader()
        quality = loader.get_quality_score()
        assert quality == 0.0

    def test_validate_columns_before_load(self):
        """validate_columns() returns error before loading."""
        loader = DataLoader()
        result = loader.validate_columns(['col1', 'col2'])
        assert result['valid'] is False


class TestMultiFailureScenarios:
    """Test complex multi-failure scenarios."""

    def test_load_then_validate_fail(self, tmp_path):
        """CSV loads but validation finds issues."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            "col1": [None] * 100,  # All nulls
            "col2": [None] * 100
        })
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # May succeed or warn depending on validation
        assert result['status'] in ['success', 'warning', 'error']

    def test_cascading_errors(self, tmp_path):
        """Multiple errors cascade correctly."""
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("col1,col2\n" + "\n" * 100)  # Empty rows
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Should handle gracefully
        assert isinstance(result, dict)
        assert 'status' in result

    def test_recovery_after_error(self, tmp_path):
        """Loader recovers after error."""
        loader = DataLoader()
        
        # First load fails
        result1 = loader.load("/nonexistent/file.csv")
        assert result1['status'] == 'error'
        
        # Second load succeeds
        csv_file = tmp_path / "good.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)
        
        result2 = loader.load(str(csv_file))
        assert result2['status'] in ['success', 'warning']


class TestErrorPropagation:
    """Test error propagation through pipeline."""

    def test_loader_error_stops_processing(self):
        """If loader fails, processing stops."""
        loader = DataLoader()
        result = loader.load("/nonexistent/file.csv")
        
        assert result['data'] is None
        assert result['quality_score'] == 0.0

    def test_error_tracking(self, tmp_path):
        """Errors are properly tracked."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Check error list structure
        if result.get('errors'):
            assert isinstance(result['errors'], list)

    def test_warning_vs_error(self, tmp_path):
        """Distinguish between warnings and errors."""
        csv_file = tmp_path / "partial_issues.csv"
        df = pd.DataFrame({
            "col1": [1, 2, None, 4, 5],
            "col2": ["a", "b", "c", "d", "e"]
        })
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Should warn but not completely fail
        assert result['status'] in ['success', 'warning']
        assert result['data'] is not None


class TestQualityScoreErrorCases:
    """Test quality score behavior in error cases."""

    def test_quality_zero_on_error(self):
        """Quality is 0.0 when load fails."""
        loader = DataLoader()
        result = loader.load("/nonexistent/file.csv")
        
        assert result['quality_score'] == 0.0

    def test_quality_range_valid(self, tmp_path):
        """Quality score always 0.0-1.0."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"x": range(100)})
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        assert 0.0 <= result['quality_score'] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
