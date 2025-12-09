"""Comprehensive tests for DataLoader agent and workers."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json

from agents.data_loader import DataLoader
from agents.data_loader.workers import (
    CSVLoaderWorker,
    JSONExcelLoaderWorker,
    ParquetLoaderWorker,
    ValidatorWorker,
)


class TestDataLoaderInit:
    """Test DataLoader initialization."""

    def test_init(self):
        """Test loader initializes correctly."""
        loader = DataLoader()
        assert loader.name == "DataLoader"
        assert loader.loaded_data is None
        assert loader.metadata == {}
        assert hasattr(loader, 'csv_loader')
        assert hasattr(loader, 'json_excel_loader')
        assert hasattr(loader, 'parquet_loader')
        assert hasattr(loader, 'validator')
        assert "csv" in loader.SUPPORTED_FORMATS
        assert "parquet" in loader.SUPPORTED_FORMATS


class TestCSVLoading:
    """Test CSV file loading."""

    @pytest.fixture
    def csv_file(self):
        """Create temporary CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,age,score\n")
            f.write("Alice,30,95.5\n")
            f.write("Bob,25,87.3\n")
            f.write("Charlie,35,92.1\n")
            f.flush()
            temp_path = f.name
        
        yield temp_path
        Path(temp_path).unlink()
    
    def test_csv_loader_worker(self, csv_file):
        """Test CSVLoaderWorker directly."""
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path=csv_file)
        assert result.success
        assert result.data is not None
        assert len(result.data) == 3
        assert "name" in result.data.columns

    def test_loader_load_csv(self, csv_file):
        """Test DataLoader.load() with CSV."""
        loader = DataLoader()
        result = loader.load(csv_file)
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert result['data'].shape[0] == 3
        assert 'metadata' in result


class TestJSONLoading:
    """Test JSON file loading."""

    @pytest.fixture
    def json_file(self):
        """Create temporary JSON file."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            temp_path = f.name
        
        yield temp_path
        Path(temp_path).unlink()
    
    def test_json_loader_worker(self, json_file):
        """Test JSONExcelLoaderWorker with JSON."""
        worker = JSONExcelLoaderWorker()
        result = worker.safe_execute(file_path=json_file, file_format="json")
        assert result.success
        assert result.data is not None
        assert len(result.data) == 3

    def test_loader_load_json(self, json_file):
        """Test DataLoader.load() with JSON."""
        loader = DataLoader()
        result = loader.load(json_file)
        assert result['status'] == 'success'
        assert result['data'] is not None


class TestExcelLoading:
    """Test Excel file loading."""

    @pytest.fixture
    def excel_file(self):
        """Create temporary Excel file."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
        })
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name
        
        df.to_excel(temp_path, index=False)
        yield temp_path
        Path(temp_path).unlink()
    
    def test_excel_loader_worker(self, excel_file):
        """Test JSONExcelLoaderWorker with Excel."""
        worker = JSONExcelLoaderWorker()
        result = worker.safe_execute(file_path=excel_file, file_format="xlsx")
        assert result.success
        assert result.data is not None
        assert len(result.data) == 3

    def test_loader_load_excel(self, excel_file):
        """Test DataLoader.load() with Excel."""
        loader = DataLoader()
        result = loader.load(excel_file)
        assert result['status'] == 'success'
        assert result['data'] is not None


class TestParquetLoading:
    """Test Parquet file loading."""

    @pytest.fixture
    def parquet_file(self):
        """Create temporary Parquet file."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
        })
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            temp_path = f.name
        
        df.to_parquet(temp_path, index=False)
        yield temp_path
        Path(temp_path).unlink()
    
    def test_parquet_loader_worker(self, parquet_file):
        """Test ParquetLoaderWorker."""
        worker = ParquetLoaderWorker()
        result = worker.safe_execute(file_path=parquet_file)
        assert result.success
        assert result.data is not None
        assert len(result.data) == 3

    def test_loader_load_parquet(self, parquet_file):
        """Test DataLoader.load() with Parquet."""
        loader = DataLoader()
        result = loader.load(parquet_file)
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert result['metadata']['rows'] == 3


class TestDataLoaderMethods:
    """Test DataLoader public methods."""

    @pytest.fixture
    def loaded_loader(self):
        """Create loader with CSV data."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
        })
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        df.to_csv(temp_path, index=False)
        
        loader = DataLoader()
        loader.load(temp_path)
        
        yield loader
        Path(temp_path).unlink()

    def test_get_data(self, loaded_loader):
        """Test get_data() method."""
        data = loaded_loader.get_data()
        assert data is not None
        assert len(data) == 3

    def test_get_metadata(self, loaded_loader):
        """Test get_metadata() method."""
        metadata = loaded_loader.get_metadata()
        assert metadata['rows'] == 3
        assert metadata['columns'] == 2

    def test_get_info(self, loaded_loader):
        """Test get_info() method."""
        info = loaded_loader.get_info()
        assert info['status'] == 'success'
        assert 'metadata' in info

    def test_get_sample(self, loaded_loader):
        """Test get_sample() method."""
        sample = loaded_loader.get_sample(n_rows=2)
        assert sample['status'] == 'success'
        assert len(sample['data']) == 2

    def test_validate_columns_valid(self, loaded_loader):
        """Test validate_columns() with valid columns."""
        result = loaded_loader.validate_columns(["name", "age"])
        assert result['valid'] is True
        assert len(result['missing']) == 0

    def test_validate_columns_missing(self, loaded_loader):
        """Test validate_columns() with missing columns."""
        result = loaded_loader.validate_columns(["name", "salary"])
        assert result['valid'] is False
        assert "salary" in result['missing']

    def test_get_summary(self, loaded_loader):
        """Test get_summary() method."""
        summary = loaded_loader.get_summary()
        assert "3" in summary
        assert "Rows" in summary


class TestValidatorWorker:
    """Test ValidatorWorker."""

    def test_validator_success(self):
        """Test successful validation."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        })
        worker = ValidatorWorker()
        result = worker.safe_execute(df=df, file_path="test.csv", file_format="csv")
        assert result.success
        assert result.metadata["rows"] == 3
        assert result.metadata["columns"] == 2

    def test_validator_none_df(self):
        """Test validation with None DataFrame."""
        worker = ValidatorWorker()
        result = worker.safe_execute(df=None, file_path="test.csv", file_format="csv")
        assert not result.success

    def test_validator_empty_df(self):
        """Test validation with empty DataFrame."""
        worker = ValidatorWorker()
        result = worker.safe_execute(df=pd.DataFrame(), file_path="test.csv", file_format="csv")
        assert not result.success


class TestErrorHandling:
    """Test error handling."""

    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        loader = DataLoader()
        result = loader.load("/nonexistent/file.csv")
        assert result['status'] == 'error'
        assert result['data'] is None

    def test_load_unsupported_format(self):
        """Test loading unsupported format."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            loader = DataLoader()
            result = loader.load(temp_path)
            assert result['status'] == 'error'
        finally:
            Path(temp_path).unlink()

    def test_worker_result_errors(self):
        """Test WorkerResult error handling."""
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path="/nonexistent/file.csv")
        assert not result.success
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
