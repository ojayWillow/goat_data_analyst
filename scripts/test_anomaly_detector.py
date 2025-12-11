#!/usr/bin/env python3
"""Pytest-compatible tests for Anomaly Detector agent using real data.

Tests cover:
- IQR-based outlier detection
- Z-score detection
- Modified Z-score detection
- Isolation Forest detection
- Multivariate (Mahalanobis) analysis
- Summary report generation

Run with: pytest scripts/test_anomaly_detector.py -v
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
from agents.anomaly_detector.anomaly_detector import AnomalyDetector
from core.logger import get_logger

logger = get_logger(__name__)


class TestAnomalyDetectorBasic:
    """Basic anomaly detection tests."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()
    
    @pytest.fixture
    def detector(self):
        """Create an AnomalyDetector instance."""
        return AnomalyDetector()
    
    @pytest.fixture
    def sample_data(self, loader):
        """Load sample_data.csv."""
        sample_file = project_root / "data" / "sample_data.csv"
        result = loader.load(str(sample_file))
        assert result['status'] == 'success'
        return result['data']
    
    def test_detector_initialization(self, detector):
        """Test AnomalyDetector initializes correctly."""
        assert detector is not None
        assert hasattr(detector, 'name')
    
    def test_set_data(self, detector, sample_data):
        """Test setting data in detector."""
        detector.set_data(sample_data)
        assert detector.data is not None
        assert len(detector.data) == len(sample_data)
    
    def test_iqr_detection(self, detector, sample_data):
        """Test IQR-based outlier detection."""
        detector.set_data(sample_data)
        
        # Get numeric columns
        num_cols = sample_data.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            result = detector.iqr_detection(num_cols[0], multiplier=1.5)
            assert result is not None
            assert isinstance(result, dict)
            assert 'bounds' in result
            assert 'outliers_count' in result
    
    def test_zscore_detection(self, detector, sample_data):
        """Test Z-score based detection."""
        detector.set_data(sample_data)
        
        num_cols = sample_data.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            result = detector.zscore_detection(num_cols[0], threshold=3.0)
            assert result is not None
            assert isinstance(result, dict)
    
    def test_modified_zscore_detection(self, detector, sample_data):
        """Test modified Z-score detection."""
        detector.set_data(sample_data)
        
        num_cols = sample_data.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            result = detector.modified_zscore_detection(num_cols[0], threshold=3.5)
            assert result is not None
            assert isinstance(result, dict)
    
    def test_isolation_forest_detection(self, detector, sample_data):
        """Test Isolation Forest based detection."""
        detector.set_data(sample_data)
        
        num_cols = sample_data.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 2:
            result = detector.isolation_forest_detection(num_cols, contamination=0.1)
            assert result is not None
            assert isinstance(result, dict)
    
    def test_multivariate_analysis(self, detector, sample_data):
        """Test multivariate (Mahalanobis) analysis."""
        detector.set_data(sample_data)
        
        num_cols = sample_data.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 2:
            result = detector.multivariate_analysis(num_cols)
            assert result is not None
            assert isinstance(result, dict)
    
    def test_summary_report(self, detector, sample_data):
        """Test summary report generation."""
        detector.set_data(sample_data)
        report = detector.summary_report()
        
        assert report is not None
        assert isinstance(report, dict)


class TestAnomalyDetectorWithRealData:
    """Test with larger real datasets."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    @pytest.fixture
    def fitness_data(self, loader):
        """Load fitness_dataset.csv (~1K rows)."""
        data_file = project_root / "data" / "fitness_dataset.csv"
        if not data_file.exists():
            pytest.skip("fitness_dataset.csv not found")
        
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load fitness_dataset.csv")
        
        return result['data']
    
    def test_iqr_on_real_data(self, detector, fitness_data):
        """Test IQR detection on real dataset."""
        detector.set_data(fitness_data)
        
        num_cols = fitness_data.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            result = detector.iqr_detection(num_cols[0])
            assert result is not None
            logger.info(f"IQR found {result.get('outliers_count', 0)} outliers")
    
    def test_isolation_forest_on_real_data(self, detector, fitness_data):
        """Test Isolation Forest on real dataset."""
        detector.set_data(fitness_data)
        
        num_cols = fitness_data.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 2:
            result = detector.isolation_forest_detection(num_cols[:2], contamination=0.05)
            assert result is not None
            logger.info(f"Isolation Forest found {result.get('anomalies_count', 0)} anomalies")


class TestAnomalyDetectorPerformance:
    """Performance tests."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    @pytest.fixture
    def hotel_data(self, loader):
        """Load hotel_bookings.csv (~100K rows)."""
        data_file = project_root / "data" / "hotel_bookings.csv"
        if not data_file.exists():
            pytest.skip("hotel_bookings.csv not found")
        
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load hotel_bookings.csv")
        
        return result['data']
    
    def test_iqr_performance_on_100k_rows(self, detector, hotel_data):
        """Test IQR performance on 100K rows."""
        detector.set_data(hotel_data)
        
        num_cols = hotel_data.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            start = time.time()
            result = detector.iqr_detection(num_cols[0])
            elapsed = time.time() - start
            
            logger.info(f"IQR on {len(hotel_data):,} rows: {elapsed:.2f}s")
            assert elapsed < 10.0
    
    def test_isolation_forest_performance(self, detector, hotel_data):
        """Test Isolation Forest performance on 100K rows."""
        detector.set_data(hotel_data)
        
        num_cols = hotel_data.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 2:
            start = time.time()
            result = detector.isolation_forest_detection(num_cols[:2], contamination=0.05)
            elapsed = time.time() - start
            
            logger.info(f"Isolation Forest on {len(hotel_data):,} rows: {elapsed:.2f}s")
            assert elapsed < 15.0


class TestAnomalyDetectorEdgeCases:
    """Edge case tests."""
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    def test_single_column_data(self, detector):
        """Test with single column."""
        df = pd.DataFrame({'value': [1, 2, 3, 4, 100]})  # 100 is outlier
        detector.set_data(df)
        
        result = detector.iqr_detection('value')
        assert result is not None
        # Should detect the 100 as outlier
        assert result.get('outliers_count', 0) > 0
    
    def test_no_outliers(self, detector):
        """Test data with no outliers."""
        df = pd.DataFrame({'value': [1, 2, 3, 4, 5]})
        detector.set_data(df)
        
        result = detector.iqr_detection('value')
        assert result is not None
        assert result.get('outliers_count', 0) == 0
    
    def test_all_same_values(self, detector):
        """Test with all same values."""
        df = pd.DataFrame({'value': [5, 5, 5, 5, 5]})
        detector.set_data(df)
        
        result = detector.iqr_detection('value')
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
