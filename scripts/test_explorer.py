#!/usr/bin/env python3
"""Pytest-compatible tests for Explorer agent using diverse challenging datasets.

Tests cover:
- Numeric statistics computation on varied data
- Categorical statistics computation
- Correlation analysis
- Data quality assessment
- Outlier detection (IQR method)
- Summary report generation
- Performance with large datasets (10MB+)

Datasets tested:
- Small: sample_data.csv
- Medium: fitness_dataset.csv, ted_main.csv
- Large: hotel_bookings.csv, country_vaccinations.csv, fifa21_raw_data.csv
- Huge: olist_geolocation_dataset.csv (61MB)

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
        return DataLoader()
    
    @pytest.fixture
    def explorer(self):
        return Explorer()
    
    @pytest.fixture
    def sample_data(self, loader):
        sample_file = project_root / "data" / "sample_data.csv"
        result = loader.load(str(sample_file))
        assert result['status'] == 'success'
        return result['data']
    
    def test_explorer_initialization(self, explorer):
        assert explorer is not None
        assert explorer.name == 'Explorer'
    
    def test_set_data(self, explorer, sample_data):
        explorer.set_data(sample_data)
        assert explorer.data is not None
        assert len(explorer.data) == len(sample_data)
    
    def test_describe_numeric(self, explorer, sample_data):
        explorer.set_data(sample_data)
        result = explorer.describe_numeric()
        assert result is not None
        assert isinstance(result, dict)
    
    def test_describe_categorical(self, explorer, sample_data):
        explorer.set_data(sample_data)
        result = explorer.describe_categorical()
        assert result is not None
        assert isinstance(result, dict)
    
    def test_correlation_analysis(self, explorer, sample_data):
        explorer.set_data(sample_data)
        result = explorer.correlation_analysis()
        assert result is not None
        assert isinstance(result, dict)
    
    def test_data_quality_assessment(self, explorer, sample_data):
        explorer.set_data(sample_data)
        result = explorer.data_quality_assessment()
        assert result is not None
        assert isinstance(result, dict)
    
    def test_detect_outliers_zscore(self, explorer, sample_data):
        explorer.set_data(sample_data)
        numeric_cols = sample_data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            result = explorer.detect_outliers_zscore(numeric_cols[0])
            assert result is not None
            assert isinstance(result, dict)
    
    def test_summary_report(self, explorer, sample_data):
        explorer.set_data(sample_data)
        result = explorer.summary_report()
        assert result is not None
        assert isinstance(result, dict)
        assert result['status'] == 'success'


class TestExplorerWithMediumData:
    """Test Explorer with medium datasets (~7-17MB)."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    @pytest.fixture
    def explorer(self):
        return Explorer()
    
    @pytest.fixture
    def ted_data(self, loader):
        data_file = project_root / "data" / "ted_main.csv"
        if not data_file.exists():
            pytest.skip("ted_main.csv not found")
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load ted_main.csv")
        return result['data']
    
    def test_numeric_stats_ted(self, explorer, ted_data):
        explorer.set_data(ted_data)
        result = explorer.describe_numeric()
        assert result is not None
        logger.info(f"TED talks numeric analysis done")
    
    def test_quality_ted(self, explorer, ted_data):
        explorer.set_data(ted_data)
        result = explorer.data_quality_assessment()
        assert result is not None


class TestExplorerWithLargeData:
    """Test Explorer with large datasets (10-20MB)."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    @pytest.fixture
    def explorer(self):
        return Explorer()
    
    @pytest.fixture
    def hotel_data(self, loader):
        data_file = project_root / "data" / "hotel_bookings.csv"
        if not data_file.exists():
            pytest.skip("hotel_bookings.csv not found")
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load hotel_bookings.csv")
        return result['data']
    
    @pytest.fixture
    def fifa_data(self, loader):
        data_file = project_root / "data" / "fifa21_raw_data.csv"
        if not data_file.exists():
            pytest.skip("fifa21_raw_data.csv not found")
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load fifa21_raw_data.csv")
        return result['data']
    
    @pytest.fixture
    def vaccinations_data(self, loader):
        data_file = project_root / "data" / "country_vaccinations.csv"
        if not data_file.exists():
            pytest.skip("country_vaccinations.csv not found")
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load country_vaccinations.csv")
        return result['data']
    
    def test_hotel_numeric_stats(self, explorer, hotel_data):
        explorer.set_data(hotel_data)
        start = time.time()
        result = explorer.describe_numeric()
        elapsed = time.time() - start
        assert result is not None
        logger.info(f"Hotel ({len(hotel_data):,} rows): numeric stats in {elapsed:.2f}s")
    
    def test_fifa_quality(self, explorer, fifa_data):
        explorer.set_data(fifa_data)
        start = time.time()
        result = explorer.data_quality_assessment()
        elapsed = time.time() - start
        assert result is not None
        logger.info(f"FIFA 21 ({len(fifa_data):,} rows): quality assessment in {elapsed:.2f}s")
    
    def test_vaccinations_summary(self, explorer, vaccinations_data):
        explorer.set_data(vaccinations_data)
        start = time.time()
        result = explorer.summary_report()
        elapsed = time.time() - start
        assert result is not None
        assert result['status'] == 'success'
        logger.info(f"Vaccinations ({len(vaccinations_data):,} rows): summary report in {elapsed:.2f}s")


class TestExplorerPerformance:
    """Performance tests with huge dataset (61MB)."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    @pytest.fixture
    def explorer(self):
        return Explorer()
    
    @pytest.fixture
    def geolocation_data(self, loader):
        data_file = project_root / "data" / "olist_geolocation_dataset.csv"
        if not data_file.exists():
            pytest.skip("olist_geolocation_dataset.csv not found")
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load olist_geolocation_dataset.csv")
        return result['data']
    
    def test_numeric_stats_huge_dataset(self, explorer, geolocation_data):
        explorer.set_data(geolocation_data)
        start = time.time()
        result = explorer.describe_numeric()
        elapsed = time.time() - start
        assert result is not None
        logger.info(f"Huge dataset ({len(geolocation_data):,} rows): numeric stats in {elapsed:.2f}s")
        assert elapsed < 30.0
    
    def test_quality_huge_dataset(self, explorer, geolocation_data):
        explorer.set_data(geolocation_data)
        start = time.time()
        result = explorer.data_quality_assessment()
        elapsed = time.time() - start
        assert result is not None
        logger.info(f"Huge dataset ({len(geolocation_data):,} rows): quality assessment in {elapsed:.2f}s")
        assert elapsed < 30.0
    
    def test_summary_huge_dataset(self, explorer, geolocation_data):
        explorer.set_data(geolocation_data)
        start = time.time()
        result = explorer.summary_report()
        elapsed = time.time() - start
        assert result is not None
        assert result['status'] == 'success'
        logger.info(f"Huge dataset ({len(geolocation_data):,} rows): summary report in {elapsed:.2f}s")
        assert elapsed < 60.0


class TestExplorerEdgeCases:
    """Edge case tests."""
    
    @pytest.fixture
    def explorer(self):
        return Explorer()
    
    def test_empty_dataframe(self, explorer):
        empty_df = pd.DataFrame()
        explorer.set_data(empty_df)
        result = explorer.describe_numeric()
        assert result is not None
    
    def test_single_column_dataframe(self, explorer):
        df = pd.DataFrame({'value': [1, 2, 3, 4, 5]})
        explorer.set_data(df)
        result = explorer.describe_numeric()
        assert result is not None
    
    def test_mixed_types_dataframe(self, explorer):
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
        df = pd.DataFrame({'value': [1, 2, 3, 4, 5]})
        explorer.set_data(df)
        result = explorer.analyze()
        assert result is not None
        assert result['status'] == 'success'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
