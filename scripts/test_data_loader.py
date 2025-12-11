#!/usr/bin/env python3
"""Pytest-compatible tests for Data Loader agent using diverse real datasets.

Tests cover:
- Small dataset loading (sample_data.csv)
- Medium dataset loading (fitness_dataset.csv ~84KB)
- Large dataset loading (hotel_bookings.csv ~17MB)
- Huge dataset loading (olist_geolocation_dataset.csv ~61MB)
- Complex dataset loading (fifa21_raw_data.csv ~8.7MB)
- Time-series dataset loading (country_vaccinations.csv ~17.6MB)
- Performance and memory efficiency

Run with: pytest scripts/test_data_loader.py -v
"""

import sys
import time
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader.data_loader import DataLoader
from core.logger import get_logger

logger = get_logger(__name__)


class TestDataLoaderBasic:
    """Basic data loader functionality tests."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    def test_loader_initialization(self, loader):
        """Test DataLoader initializes correctly."""
        assert loader is not None
        assert loader.name == 'DataLoader'
    
    def test_load_sample_data(self, loader):
        """Test loading small sample dataset."""
        sample_file = project_root / "data" / "sample_data.csv"
        result = loader.load(str(sample_file))
        
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert len(result['data']) > 0
        logger.info(f"Sample data: {result['data'].shape}")
    
    def test_load_invalid_file(self, loader):
        """Test loading non-existent file."""
        result = loader.load("/nonexistent/file.csv")
        assert result['status'] != 'success'
    
    def test_get_data_info(self, loader):
        """Test get_data_info method."""
        sample_file = project_root / "data" / "sample_data.csv"
        loader.load(str(sample_file))
        
        info = loader.get_data_info()
        assert info is not None
        assert isinstance(info, dict)


class TestDataLoaderWithMediumData:
    """Test with medium-sized real datasets."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    def test_load_fitness_data(self, loader):
        """Test loading fitness dataset (~84KB)."""
        data_file = project_root / "data" / "fitness_dataset.csv"
        if not data_file.exists():
            pytest.skip("fitness_dataset.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        logger.info(f"Fitness data: {result['data'].shape}")
    
    def test_load_ted_talks(self, loader):
        """Test loading TED talks dataset (~7.6MB)."""
        data_file = project_root / "data" / "ted_main.csv"
        if not data_file.exists():
            pytest.skip("ted_main.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        logger.info(f"TED talks: {result['data'].shape}")
    
    def test_load_vaccinations_data(self, loader):
        """Test loading vaccinations dataset (~17.6MB)."""
        data_file = project_root / "data" / "country_vaccinations.csv"
        if not data_file.exists():
            pytest.skip("country_vaccinations.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        logger.info(f"Vaccinations: {result['data'].shape}")


class TestDataLoaderWithLargeData:
    """Test with large real datasets (10-20MB)."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    def test_load_hotel_bookings(self, loader):
        """Test loading hotel bookings dataset (~16.9MB)."""
        data_file = project_root / "data" / "hotel_bookings.csv"
        if not data_file.exists():
            pytest.skip("hotel_bookings.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        assert result['data'].shape[0] > 100000
        logger.info(f"Hotel bookings: {result['data'].shape} - {result['data'].memory_usage(deep=True).sum() / 1024**2:.1f}MB")
    
    def test_load_fifa_data(self, loader):
        """Test loading FIFA 21 dataset (~8.7MB)."""
        data_file = project_root / "data" / "fifa21_raw_data.csv"
        if not data_file.exists():
            pytest.skip("fifa21_raw_data.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        logger.info(f"FIFA 21: {result['data'].shape}")
    
    def test_load_olist_orders(self, loader):
        """Test loading OLIST orders dataset (~17.6MB)."""
        data_file = project_root / "data" / "olist_orders_dataset.csv"
        if not data_file.exists():
            pytest.skip("olist_orders_dataset.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        logger.info(f"OLIST orders: {result['data'].shape}")


class TestDataLoaderPerformance:
    """Performance and stress tests with huge datasets."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    def test_huge_geolocation_dataset(self, loader):
        """Test loading massive OLIST geolocation dataset (~61.3MB)."""
        data_file = project_root / "data" / "olist_geolocation_dataset.csv"
        if not data_file.exists():
            pytest.skip("olist_geolocation_dataset.csv not found")
        
        start_time = time.time()
        result = loader.load(str(data_file))
        elapsed = time.time() - start_time
        
        assert result['status'] == 'success'
        rows, cols = result['data'].shape
        memory_mb = result['data'].memory_usage(deep=True).sum() / 1024**2
        
        logger.info(f"Huge geolocation: {rows:,} rows x {cols} cols")
        logger.info(f"Memory used: {memory_mb:.1f}MB")
        logger.info(f"Load time: {elapsed:.2f}s")
        
        # Should handle large dataset efficiently
        assert elapsed < 30.0
        assert rows > 1000000
    
    def test_multiple_large_datasets(self, loader):
        """Test sequential loading of multiple large datasets."""
        datasets = [
            ("hotel_bookings.csv", 100000),
            ("country_vaccinations.csv", 10000),
            ("olist_orders_dataset.csv", 100000),
        ]
        
        for filename, min_rows in datasets:
            data_file = project_root / "data" / filename
            if not data_file.exists():
                continue
            
            start = time.time()
            result = loader.load(str(data_file))
            elapsed = time.time() - start
            
            if result['status'] == 'success':
                logger.info(f"{filename}: {result['data'].shape[0]:,} rows in {elapsed:.2f}s")
                assert result['data'].shape[0] >= min_rows


class TestDataLoaderDataTypes:
    """Test handling of various data types."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    def test_mixed_dtypes_hotel_data(self, loader):
        """Test mixed data types (numeric + categorical + datetime)."""
        data_file = project_root / "data" / "hotel_bookings.csv"
        if not data_file.exists():
            pytest.skip("hotel_bookings.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        
        df = result['data']
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        assert len(numeric_cols) > 0
        assert len(categorical_cols) > 0
        logger.info(f"Numeric: {len(numeric_cols)}, Categorical: {len(categorical_cols)}")
    
    def test_timeseries_vaccinations(self, loader):
        """Test time-series data (vaccinations)."""
        data_file = project_root / "data" / "country_vaccinations.csv"
        if not data_file.exists():
            pytest.skip("country_vaccinations.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        
        df = result['data']
        # Should have date-like columns
        assert any('date' in col.lower() for col in df.columns)
        logger.info(f"Columns: {list(df.columns)[:5]}")
    
    def test_complex_fifa_data(self, loader):
        """Test complex structured data (FIFA 21)."""
        data_file = project_root / "data" / "fifa21_raw_data.csv"
        if not data_file.exists():
            pytest.skip("fifa21_raw_data.csv not found")
        
        result = loader.load(str(data_file))
        assert result['status'] == 'success'
        
        df = result['data']
        # FIFA data has many columns
        assert df.shape[1] > 50
        logger.info(f"FIFA 21: {df.shape[1]} columns")


class TestDataLoaderRobustness:
    """Robustness and error handling tests."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    def test_empty_result_handling(self, loader):
        """Test handling of file that results in empty data."""
        # This would need a file that loads but is empty
        # For now, just test error handling
        result = loader.load("/nonexistent.csv")
        assert result['status'] != 'success'
    
    def test_get_summary(self, loader):
        """Test get_summary method."""
        sample_file = project_root / "data" / "sample_data.csv"
        loader.load(str(sample_file))
        
        summary = loader.get_summary()
        assert summary is not None
        assert isinstance(summary, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
