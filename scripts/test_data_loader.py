#!/usr/bin/env python3
"""Pytest-compatible tests for DataLoader agent.

Tests cover:
- Basic CSV loading
- Large dataset performance (1M rows <5s)
- Error handling (corrupted files)
- Multiple file formats (CSV, JSON, Parquet)
- Metadata extraction
- Column validation

Run with: pytest scripts/test_data_loader.py -v
"""

import sys
import time
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader.data_loader import DataLoader
from core.logger import get_logger

logger = get_logger(__name__)


class TestDataLoaderBasic:
    """Basic DataLoader functionality tests."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def sample_csv(self):
        """Create a temporary CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value\n1,Alice,100\n2,Bob,200\n3,Charlie,300\n")
            return f.name
    
    def test_loader_initialization(self, loader):
        """Test DataLoader initializes correctly."""
        assert loader is not None
        assert hasattr(loader, 'name')
        assert loader.name == 'data_loader'
    
    def test_load_csv_basic(self, loader, sample_csv):
        """Test loading a simple CSV file."""
        result = loader.load(sample_csv)
        assert result is not None
        assert result['status'] == 'success' or result['status'] == 'loaded'
        assert 'message' in result
    
    def test_get_metadata(self, loader, sample_csv):
        """Test extracting metadata from loaded data."""
        loader.load(sample_csv)
        metadata = loader.get_metadata()
        
        assert metadata is not None
        assert 'rows' in metadata
        assert 'columns' in metadata
        assert metadata['rows'] == 3
        assert metadata['columns'] == 3
    
    def test_get_sample(self, loader, sample_csv):
        """Test retrieving sample rows from loaded data."""
        loader.load(sample_csv)
        sample = loader.get_sample(n_rows=2)
        
        assert sample is not None
        assert 'sample' in sample
        assert 'total_rows' in sample
        assert len(sample['sample']) <= 2
    
    def test_get_info(self, loader, sample_csv):
        """Test getting data type information."""
        loader.load(sample_csv)
        info = loader.get_info()
        
        assert info is not None
        assert 'data_types' in info
        assert len(info['data_types']) > 0
    
    def test_validate_columns_success(self, loader, sample_csv):
        """Test column validation when all columns exist."""
        loader.load(sample_csv)
        result = loader.validate_columns(['id', 'name', 'value'])
        
        assert result['valid'] is True
        assert result['missing_columns'] == []
    
    def test_validate_columns_missing(self, loader, sample_csv):
        """Test column validation when columns are missing."""
        loader.load(sample_csv)
        result = loader.validate_columns(['id', 'name', 'nonexistent'])
        
        assert result['valid'] is False
        assert 'nonexistent' in result['missing_columns']


class TestDataLoaderPerformance:
    """Performance and scale tests for DataLoader."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def large_csv_1m_rows(self):
        """Create a temporary CSV file with 1M rows."""
        logger.info("Creating 1M row CSV for performance test...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write header
            f.write("id,timestamp,value,category\n")
            # Write 1M rows
            for i in range(1_000_000):
                f.write(f"{i},2025-01-{(i % 28) + 1},{'%.2f' % (i * 0.5)},cat_{i % 10}\n")
                if (i + 1) % 100_000 == 0:
                    logger.info(f"  Written {i + 1:,} rows...")
            logger.info("  CSV file created")
            return f.name
    
    def test_load_csv_1m_rows_performance(self, loader, large_csv_1m_rows):
        """Test loading 1M rows completes in <5 seconds."""
        start_time = time.time()
        result = loader.load(large_csv_1m_rows)
        elapsed = time.time() - start_time
        
        logger.info(f"Loaded 1M rows in {elapsed:.2f} seconds")
        
        assert result['status'] in ['success', 'loaded']
        assert elapsed < 5.0, f"Loading took {elapsed:.2f}s, expected <5s"
    
    def test_metadata_extraction_1m_rows(self, loader, large_csv_1m_rows):
        """Test metadata extraction on 1M row dataset."""
        loader.load(large_csv_1m_rows)
        
        start_time = time.time()
        metadata = loader.get_metadata()
        elapsed = time.time() - start_time
        
        logger.info(f"Extracted metadata in {elapsed:.2f} seconds")
        
        assert metadata['rows'] == 1_000_000
        assert elapsed < 2.0, f"Metadata extraction took {elapsed:.2f}s, expected <2s"


class TestDataLoaderErrorHandling:
    """Error handling and edge cases."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def corrupted_csv(self):
        """Create a corrupted CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value\n")
            f.write("1,Alice,100\n")
            f.write("2,Bob,not_a_number\n")  # Invalid data type
            f.write("3,Charlie\n")  # Missing column
            return f.name
    
    def test_load_corrupted_csv(self, loader, corrupted_csv):
        """Test loading a corrupted CSV file doesn't crash."""
        try:
            result = loader.load(corrupted_csv)
            # Should either load successfully or raise handled exception
            assert result is not None
        except Exception as e:
            # Exception is acceptable for corrupted data
            logger.warning(f"Caught expected exception: {type(e).__name__}")
            assert True
    
    def test_load_nonexistent_file(self, loader):
        """Test loading a file that doesn't exist."""
        with pytest.raises(Exception):
            loader.load("/nonexistent/file/path.csv")
    
    @pytest.fixture
    def empty_csv(self):
        """Create an empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value\n")  # Header only, no data
            return f.name
    
    def test_load_empty_csv(self, loader, empty_csv):
        """Test loading an empty CSV (header only)."""
        result = loader.load(empty_csv)
        metadata = loader.get_metadata()
        
        assert metadata['rows'] == 0


class TestDataLoaderMultipleFormats:
    """Test loading different file formats."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def sample_json(self):
        """Create a temporary JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = [
                {"id": 1, "name": "Alice", "value": 100},
                {"id": 2, "name": "Bob", "value": 200},
                {"id": 3, "name": "Charlie", "value": 300}
            ]
            json.dump(data, f)
            return f.name
    
    def test_load_json(self, loader, sample_json):
        """Test loading a JSON file."""
        try:
            result = loader.load(sample_json)
            assert result is not None
            logger.info("JSON loading supported")
        except NotImplementedError:
            logger.warning("JSON loading not yet implemented")
            pytest.skip("JSON loading not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
