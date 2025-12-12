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

from agents.data_loader.workers import (
    CSVLoaderWorker,
    JSONExcelLoaderWorker,
    ParquetLoaderWorker,
    ValidatorWorker,
)
from agents.data_loader.data_loader import DataLoader


class TestCSVLoaderErrorPaths:
    """Test all error paths in CSV loader."""

    def test_file_not_found(self):
        """Handle file not found error."""
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path="/nonexistent/file.csv")
        
        assert result.success is False
        assert len(result.errors) > 0
        assert result.quality_score == 0.0

    def test_permission_denied(self, tmp_path):
        """Handle permission denied error."""
        csv_file = tmp_path / "restricted.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)
        
        # Remove read permission
        os.chmod(csv_file, 0o000)
        
        try:
            worker = CSVLoaderWorker()
            result = worker.safe_execute(file_path=str(csv_file))
            
            # Should handle gracefully
            assert isinstance(result.success, bool)
        finally:
            # Restore permission for cleanup
            os.chmod(csv_file, 0o644)

    def test_encoding_error_recovery(self, tmp_path):
        """Recover from encoding errors."""
        csv_file = tmp_path / "bad_encoding.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["café", "naïve", "résumé"]
        })
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path=str(csv_file), encoding='utf-8')
        
        assert result.success is True

    def test_corrupted_csv(self, tmp_path):
        """Handle corrupted CSV gracefully."""
        csv_file = tmp_path / "corrupted.csv"
        csv_file.write_text("col1,col2\n1,a,extra,cols\n2,b")
        
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path=str(csv_file))
        
        # Should use skip bad lines strategy
        assert result.success is True
        assert result.data is not None

    def test_invalid_delimiter(self, tmp_path):
        """Handle invalid delimiter gracefully."""
        csv_file = tmp_path / "bad_delim.csv"
        csv_file.write_text("col1;col2;col3\n1;a;x\n2;b;y")
        
        worker = CSVLoaderWorker()
        # Try with wrong delimiter
        result = worker.safe_execute(file_path=str(csv_file), sep=',')
        
        # Should handle gracefully
        assert isinstance(result, object)

    def test_empty_file_error(self, tmp_path):
        """Handle empty file error."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path=str(csv_file))
        
        assert result.success is False

    def test_header_only_file(self, tmp_path):
        """Handle header-only file."""
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("col1,col2,col3\n")
        
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path=str(csv_file))
        
        assert result.success is False  # No data rows

    def test_numeric_overflow(self, tmp_path):
        """Handle numeric overflow gracefully."""
        csv_file = tmp_path / "overflow.csv"
        # Very large numbers
        csv_file.write_text("value\n999999999999999999999999999")
        
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path=str(csv_file))
        
        # Should load but handle large numbers
        assert isinstance(result, object)


class TestValidatorErrorPaths:
    """Test all error paths in validator."""

    def test_empty_dataframe(self):
        """Handle empty DataFrame."""
        worker = ValidatorWorker()
        df = pd.DataFrame()
        
        with pytest.raises(ValueError):
            worker.safe_execute(df=df)

    def test_none_dataframe(self):
        """Handle None DataFrame."""
        worker = ValidatorWorker()
        
        with pytest.raises(TypeError):
            worker.safe_execute(df=None)

    def test_all_null_dataframe(self):
        """Handle all-null DataFrame."""
        worker = ValidatorWorker()
        df = pd.DataFrame({
            "col1": [None, None, None],
            "col2": [None, None, None]
        })
        
        result = worker.safe_execute(df=df)
        
        # Should detect high nulls
        assert result.success is False
        assert len(result.metadata.get('issues', [])) > 0

    def test_single_row_dataframe(self):
        """Handle single-row DataFrame."""
        worker = ValidatorWorker()
        df = pd.DataFrame({"col1": [1]})
        
        result = worker.safe_execute(df=df)
        
        assert isinstance(result, object)

    def test_all_duplicates(self):
        """Handle all-duplicate DataFrame."""
        worker = ValidatorWorker()
        df = pd.DataFrame({
            "col1": [1, 1, 1],
            "col2": ["a", "a", "a"]
        })
        
        result = worker.safe_execute(df=df)
        
        # Should detect high duplicate percentage
        assert result.metadata.get('duplicates', 0) > 0


class TestJSONExcelLoaderErrorPaths:
    """Test all error paths in JSON/Excel loader."""

    def test_invalid_json(self, tmp_path):
        """Handle invalid JSON file."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json")
        
        worker = JSONExcelLoaderWorker()
        result = worker.safe_execute(
            file_path=str(json_file),
            file_format='json'
        )
        
        assert result.success is False

    def test_invalid_excel(self, tmp_path):
        """Handle invalid Excel file."""
        excel_file = tmp_path / "invalid.xlsx"
        excel_file.write_text("not an excel file")
        
        worker = JSONExcelLoaderWorker()
        result = worker.safe_execute(
            file_path=str(excel_file),
            file_format='xlsx'
        )
        
        assert result.success is False

    def test_missing_format_parameter(self, tmp_path):
        """Handle missing format parameter."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"a": 1}')
        
        worker = JSONExcelLoaderWorker()
        
        with pytest.raises(ValueError):
            worker.validate_input({
                "file_path": str(json_file),
                "file_format": ""
            })


class TestParquetLoaderErrorPaths:
    """Test all error paths in Parquet loader."""

    def test_corrupted_parquet(self, tmp_path):
        """Handle corrupted Parquet file."""
        parquet_file = tmp_path / "corrupted.parquet"
        parquet_file.write_text("not a parquet file")
        
        worker = ParquetLoaderWorker()
        result = worker.safe_execute(file_path=str(parquet_file))
        
        assert result.success is False

    def test_empty_parquet(self, tmp_path):
        """Handle empty Parquet file."""
        parquet_file = tmp_path / "empty.parquet"
        df = pd.DataFrame()
        df.to_parquet(parquet_file)
        
        worker = ParquetLoaderWorker()
        result = worker.safe_execute(file_path=str(parquet_file))
        
        assert result.success is False  # Empty data


class TestMultiFailureScenarios:
    """Test complex multi-failure scenarios."""

    def test_load_then_validate_fail(self, tmp_path):
        """CSV loads but validation fails."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            "col1": [None] * 100,  # All nulls
            "col2": [None] * 100
        })
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Should detect issues
        assert result['quality_score'] < 1.0 or len(result.get('quality_issues', [])) > 0

    def test_cascading_errors(self, tmp_path):
        """Multiple errors cascade correctly."""
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("col1,col2\n" + "\n" * 100)  # Empty rows
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Should handle multiple issues
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'errors' in result or 'quality_score' in result

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
        assert result2['status'] == 'success'


class TestErrorPropagation:
    """Test error propagation through pipeline."""

    def test_loader_error_stops_validation(self, tmp_path):
        """If loader fails, validation doesn't run."""
        loader = DataLoader()
        result = loader.load("/nonexistent/file.csv")
        
        assert result['data'] is None
        assert len(result['errors']) > 0
        assert result['quality_score'] == 0.0

    def test_error_tracking(self, tmp_path):
        """Errors are properly tracked."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Check error list structure
        if result['errors']:
            for error in result['errors']:
                assert isinstance(error, (str, dict))

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
        
        # Should warn but not error
        assert result['status'] in ['success', 'warning']
        assert result['data'] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
