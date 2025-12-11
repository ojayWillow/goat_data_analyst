#!/usr/bin/env python3
"""Pytest-compatible tests for Explorer agent using real data.

Tests cover:
- Numeric statistics computation
- Categorical statistics computation
- Correlation analysis
- Data quality assessment
- Outlier detection (Z-score method)
- Summary report generation

Run with: pytest scripts/test_explorer.py -v
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
from agents.explorer.explorer import Explorer
from core.logger import get_logger

logger = get_logger(__name__)


class TestExplorerWithSmallData:
    """Test Explorer with small dataset (sample_data.csv)."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def explorer(self):
        """Create an Explorer instance."""
        return Explorer()
    
    @pytest.fixture
    def sample_data(self, loader):
        """Load sample_data.csv."""
        sample_file = project_root / "data" / "sample_data.csv"
        result = loader.load(str(sample_file))
        assert result['status'] == 'success'
        return result['data']
    
    def test_explorer_initialization(self, explorer):
        """Test Explorer initializes correctly."""
        assert explorer is not None
        assert hasattr(explorer, 'name')
        assert explorer.name == 'Explorer'  # Actual name is 'Explorer'
    
    def test_set_data(self, explorer, sample_data):
        """Test setting data in Explorer."""
        explorer.set_data(sample_data)
        assert explorer.data is not None
        assert len(explorer.data) == len(sample_data)
    
    def test_describe_numeric(self, explorer, sample_data):
        """Test computing numeric statistics."""
        explorer.set_data(sample_data)
        result = explorer.describe_numeric()
        
        assert result is not None
        assert isinstance(result, dict)
        # Result is a WorkerResult dict with 'success' field
        assert 'success' in result or 'data' in result
    
    def test_describe_categorical(self, explorer, sample_data):
        """Test computing categorical statistics."""
        explorer.set_data(sample_data)
        result = explorer.describe_categorical()
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_correlation_analysis(self, explorer, sample_data):
        """Test correlation analysis."""
        explorer.set_data(sample_data)
        result = explorer.correlation_analysis()
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_data_quality_assessment(self, explorer, sample_data):
        """Test data quality assessment."""
        explorer.set_data(sample_data)
        result = explorer.data_quality_assessment()
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_detect_outliers_zscore(self, explorer, sample_data):
        """Test outlier detection using Z-score method."""
        explorer.set_data(sample_data)
        
        # Find a numeric column
        numeric_cols = sample_data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            result = explorer.detect_outliers_zscore(numeric_cols[0])
            assert result is not None
            assert isinstance(result, dict)
    
    def test_summary_report(self, explorer, sample_data):
        """Test summary report generation."""
        explorer.set_data(sample_data)
        result = explorer.summary_report()
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'status' in result
        assert result['status'] == 'success'


class TestExplorerWithLargeData:
    """Test Explorer with larger dataset (fitness_dataset.csv ~1K rows)."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def explorer(self):
        """Create an Explorer instance."""
        return Explorer()
    
    @pytest.fixture
    def large_data(self, loader):
        """Load fitness_dataset.csv (~1K rows)."""
        data_file = project_root / "data" / "fitness_dataset.csv"
        if not data_file.exists():
            pytest.skip("fitness_dataset.csv not found")
        
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load fitness_dataset.csv")
        
        return result['data']
    
    def test_numeric_stats_on_large_data(self, explorer, large_data):
        """Test numeric statistics on larger dataset."""
        explorer.set_data(large_data)
        result = explorer.describe_numeric()
        
        assert result is not None
        logger.info(f"Numeric analysis completed")
    
    def test_categorical_stats_on_large_data(self, explorer, large_data):
        """Test categorical statistics on larger dataset."""
        explorer.set_data(large_data)
        result = explorer.describe_categorical()
        
        assert result is not None
        logger.info(f"Categorical analysis completed")
    
    def test_quality_assessment_on_large_data(self, explorer, large_data):
        """Test data quality on larger dataset."""
        explorer.set_data(large_data)
        result = explorer.data_quality_assessment()
        
        assert result is not None
        logger.info(f"Quality assessment completed")


class TestExplorerPerformance:
    """Performance tests for Explorer."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def explorer(self):
        """Create an Explorer instance."""
        return Explorer()
    
    @pytest.fixture
    def hotel_bookings(self, loader):
        """Load hotel_bookings.csv (~100K rows)."""
        data_file = project_root / "data" / "hotel_bookings.csv"
        if not data_file.exists():
            pytest.skip("hotel_bookings.csv not found")
        
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load hotel_bookings.csv")
        
        return result['data']
    
    def test_numeric_stats_performance(self, explorer, hotel_bookings):
        """Test numeric statistics performance on ~100K rows."""
        explorer.set_data(hotel_bookings)
        
        start_time = time.time()
        result = explorer.describe_numeric()
        elapsed = time.time() - start_time
        
        logger.info(f"Numeric stats on {len(hotel_bookings):,} rows: {elapsed:.2f}s")
        assert result is not None
        # Should complete reasonably fast
        assert elapsed < 15.0, f"Numeric stats took {elapsed:.2f}s, expected <15s"
    
    def test_quality_assessment_performance(self, explorer, hotel_bookings):
        """Test quality assessment performance on ~100K rows."""
        explorer.set_data(hotel_bookings)
        
        start_time = time.time()
        result = explorer.data_quality_assessment()
        elapsed = time.time() - start_time
        
        logger.info(f"Quality assessment on {len(hotel_bookings):,} rows: {elapsed:.2f}s")
        assert result is not None
        # Should complete reasonably fast
        assert elapsed < 15.0, f"Quality assessment took {elapsed:.2f}s, expected <15s"
    
    def test_summary_report_performance(self, explorer, hotel_bookings):
        """Test summary report generation performance."""
        explorer.set_data(hotel_bookings)
        
        start_time = time.time()
        result = explorer.summary_report()
        elapsed = time.time() - start_time
        
        logger.info(f"Summary report on {len(hotel_bookings):,} rows: {elapsed:.2f}s")
        assert result is not None
        assert result['status'] == 'success'
        # Full report involves multiple operations
        assert elapsed < 30.0, f"Summary report took {elapsed:.2f}s, expected <30s"


class TestExplorerEdgeCases:
    """Test Explorer with edge cases and various data types."""
    
    @pytest.fixture
    def explorer(self):
        """Create an Explorer instance."""
        return Explorer()
    
    def test_empty_dataframe(self, explorer):
        """Test Explorer with empty DataFrame."""
        empty_df = pd.DataFrame()
        explorer.set_data(empty_df)
        
        result = explorer.describe_numeric()
        # Should handle gracefully
        assert result is not None
    
    def test_single_column_dataframe(self, explorer):
        """Test Explorer with single column DataFrame."""
        df = pd.DataFrame({'value': [1, 2, 3, 4, 5]})
        explorer.set_data(df)
        
        result = explorer.describe_numeric()
        assert result is not None
    
    def test_mixed_types_dataframe(self, explorer):
        """Test Explorer with mixed data types."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'str_col': ['a', 'b', 'c', 'd', 'e'],
            'bool_col': [True, False, True, False, True]
        })
        explorer.set_data(df)
        
        numeric_result = explorer.describe_numeric()
        categorical_result = explorer.describe_categorical()
        
        assert numeric_result is not None
        assert categorical_result is not None
    
    def test_analyze_alias(self, explorer):
        """Test analyze() alias for summary_report()."""
        df = pd.DataFrame({'value': [1, 2, 3, 4, 5]})
        explorer.set_data(df)
        
        result = explorer.analyze()
        assert result is not None
        assert result['status'] == 'success'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
