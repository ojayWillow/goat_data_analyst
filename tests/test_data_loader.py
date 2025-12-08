"""Tests for DataLoader agent."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json

from agents.data_loader import DataLoader
from core.exceptions import DataLoadError, DataValidationError


class TestDataLoader:
    """Test DataLoader agent."""
    
    @pytest.fixture
    def loader(self):
        """Create DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def sample_csv_file(self):
        """Create a temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,age,city\n")
            f.write("Alice,30,New York\n")
            f.write("Bob,25,Los Angeles\n")
            f.write("Charlie,35,Chicago\n")
            f.flush()
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink()
    
    @pytest.fixture
    def sample_json_file(self):
        """Create a temporary JSON file for testing."""
        data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "Los Angeles"},
            {"name": "Charlie", "age": 35, "city": "Chicago"},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_loader_initialization(self, loader):
        """Test DataLoader initialization."""
        assert loader.name == "DataLoader"
        assert loader.loaded_data is None
        assert loader.metadata == {}
    
    def test_load_csv_success(self, loader, sample_csv_file):
        """Test loading CSV file."""
        result = loader.load(sample_csv_file)
        
        assert result["status"] == "success"
        assert result["data"] is not None
        assert result["data"].shape[0] == 3  # 3 rows
        assert result["data"].shape[1] == 3  # 3 columns
        assert "metadata" in result
    
    def test_load_json_success(self, loader, sample_json_file):
        """Test loading JSON file."""
        result = loader.load(sample_json_file)
        
        assert result["status"] == "success"
        assert result["data"] is not None
        assert result["data"].shape[0] == 3
    
    def test_load_nonexistent_file(self, loader):
        """Test loading nonexistent file."""
        with pytest.raises(DataLoadError):
            loader.load("/nonexistent/path/file.csv")
    
    def test_load_unsupported_format(self, loader):
        """Test loading unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            with pytest.raises(DataLoadError):
                loader.load(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_metadata_extraction(self, loader, sample_csv_file):
        """Test metadata extraction."""
        loader.load(sample_csv_file)
        metadata = loader.get_metadata()
        
        assert metadata["rows"] == 3
        assert metadata["columns"] == 3
        assert "column_names" in metadata
        assert "dtypes" in metadata
        assert "file_size_mb" in metadata
    
    def test_get_data(self, loader, sample_csv_file):
        """Test getting loaded data."""
        loader.load(sample_csv_file)
        data = loader.get_data()
        
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 3
    
    def test_get_sample(self, loader, sample_csv_file):
        """Test getting sample data."""
        loader.load(sample_csv_file)
        result = loader.get_sample(n_rows=2)
        
        assert result["status"] == "success"
        assert len(result["sample"]) == 2
        assert result["total_rows"] == 3
    
    def test_get_info(self, loader, sample_csv_file):
        """Test getting data info."""
        loader.load(sample_csv_file)
        info = loader.get_info()
        
        assert info["status"] == "success"
        assert "metadata" in info
        assert "data_types" in info
        assert "null_summary" in info
    
    def test_validate_columns_success(self, loader, sample_csv_file):
        """Test column validation - success case."""
        loader.load(sample_csv_file)
        result = loader.validate_columns(["name", "age"])
        
        assert result["status"] == "success"
        assert result["valid"] == True
        assert result["missing_columns"] == []
    
    def test_validate_columns_missing(self, loader, sample_csv_file):
        """Test column validation - missing columns."""
        loader.load(sample_csv_file)
        result = loader.validate_columns(["name", "salary", "department"])
        
        assert result["status"] == "error"
        assert result["valid"] == False
        assert "salary" in result["missing_columns"]
        assert "department" in result["missing_columns"]
    
    def test_get_info_no_data(self, loader):
        """Test getting info when no data loaded."""
        result = loader.get_info()
        
        assert result["status"] == "error"
        assert "message" in result
    
    def test_supported_formats(self, loader):
        """Test supported formats list."""
        assert "csv" in loader.SUPPORTED_FORMATS
        assert "json" in loader.SUPPORTED_FORMATS
        assert "xlsx" in loader.SUPPORTED_FORMATS
        assert "parquet" in loader.SUPPORTED_FORMATS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
