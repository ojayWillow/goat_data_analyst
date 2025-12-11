#!/usr/bin/env python3
"""Pytest-compatible tests for Anomaly Detector agent using real data.

Tests cover:
- LOF (Local Outlier Factor) detection
- One-Class SVM detection
- Isolation Forest detection
- Ensemble voting method
- Summary report generation
- Batch detection (detect_all)

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
        assert detector.name == 'AnomalyDetector'
        assert len(detector.workers) == 4
    
    def test_set_data(self, detector, sample_data):
        """Test setting data in detector."""
        detector.set_data(sample_data)
        assert detector.data is not None
        assert len(detector.data) == len(sample_data)
    
    def test_lof_detection(self, detector, sample_data):
        """Test LOF (Local Outlier Factor) detection."""
        detector.set_data(sample_data)
        result = detector.detect_lof(n_neighbors=5, contamination=0.1)
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_ocsvm_detection(self, detector, sample_data):
        """Test One-Class SVM detection."""
        detector.set_data(sample_data)
        result = detector.detect_ocsvm(nu=0.05, kernel='rbf')
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_isolation_forest_detection(self, detector, sample_data):
        """Test Isolation Forest detection."""
        detector.set_data(sample_data)
        result = detector.detect_isolation_forest(contamination=0.1)
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_ensemble_detection(self, detector, sample_data):
        """Test Ensemble voting detection."""
        detector.set_data(sample_data)
        result = detector.detect_ensemble(threshold=0.5)
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_detect_all(self, detector, sample_data):
        """Test running all detection methods at once."""
        detector.set_data(sample_data)
        results = detector.detect_all()
        
        assert results is not None
        assert isinstance(results, dict)
        # Should have at least some results
        assert len(results) > 0
    
    def test_summary_report(self, detector, sample_data):
        """Test summary report generation."""
        detector.set_data(sample_data)
        detector.detect_all()  # Run detections first
        report = detector.summary_report()
        
        assert report is not None
        assert 'status' in report
        assert report['status'] == 'success'
        assert 'timestamp' in report


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
    
    def test_lof_on_real_data(self, detector, fitness_data):
        """Test LOF detection on real dataset."""
        detector.set_data(fitness_data)
        result = detector.detect_lof()
        
        assert result is not None
        logger.info(f"LOF detection completed")
    
    def test_isolation_forest_on_real_data(self, detector, fitness_data):
        """Test Isolation Forest on real dataset."""
        detector.set_data(fitness_data)
        result = detector.detect_isolation_forest()
        
        assert result is not None
        logger.info(f"Isolation Forest detection completed")
    
    def test_detect_all_on_real_data(self, detector, fitness_data):
        """Test all methods on real dataset."""
        detector.set_data(fitness_data)
        results = detector.detect_all()
        
        assert results is not None
        assert len(results) > 0
        logger.info(f"All detection methods completed")


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
    
    def test_lof_performance_on_100k_rows(self, detector, hotel_data):
        """Test LOF performance on 100K rows."""
        detector.set_data(hotel_data)
        
        start = time.time()
        result = detector.detect_lof()
        elapsed = time.time() - start
        
        logger.info(f"LOF on {len(hotel_data):,} rows: {elapsed:.2f}s")
        assert result is not None
        # Should complete in reasonable time
        assert elapsed < 30.0
    
    def test_isolation_forest_performance(self, detector, hotel_data):
        """Test Isolation Forest performance on 100K rows."""
        detector.set_data(hotel_data)
        
        start = time.time()
        result = detector.detect_isolation_forest()
        elapsed = time.time() - start
        
        logger.info(f"Isolation Forest on {len(hotel_data):,} rows: {elapsed:.2f}s")
        assert result is not None
        # Should complete in reasonable time
        assert elapsed < 30.0
    
    def test_detect_all_performance(self, detector, hotel_data):
        """Test all methods performance on 100K rows."""
        detector.set_data(hotel_data)
        
        start = time.time()
        results = detector.detect_all()
        elapsed = time.time() - start
        
        logger.info(f"All methods on {len(hotel_data):,} rows: {elapsed:.2f}s")
        assert results is not None
        # All 4 methods should complete in reasonable time
        assert elapsed < 60.0


class TestAnomalyDetectorEdgeCases:
    """Edge case tests."""
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    def test_small_dataframe(self, detector):
        """Test with small dataframe (5 rows)."""
        df = pd.DataFrame({
            'value1': [1, 2, 3, 4, 100],  # 100 is potential outlier
            'value2': [10, 20, 30, 40, 500]
        })
        detector.set_data(df)
        
        result = detector.detect_isolation_forest()
        assert result is not None
    
    def test_no_anomalies(self, detector):
        """Test data with no clear anomalies."""
        df = pd.DataFrame({
            'value1': [1, 2, 3, 4, 5],
            'value2': [10, 20, 30, 40, 50]
        })
        detector.set_data(df)
        
        result = detector.detect_isolation_forest(contamination=0.01)
        assert result is not None
    
    def test_mixed_types(self, detector):
        """Test with mixed numeric and categorical columns."""
        df = pd.DataFrame({
            'numeric': [1, 2, 3, 4, 5],
            'category': ['a', 'b', 'c', 'd', 'e']
        })
        detector.set_data(df)
        
        # Should handle gracefully - only numeric columns
        result = detector.detect_isolation_forest()
        assert result is not None
    
    def test_get_summary(self, detector):
        """Test get_summary method."""
        df = pd.DataFrame({'value': [1, 2, 3]})
        detector.set_data(df)
        
        summary = detector.get_summary()
        assert summary is not None
        assert isinstance(summary, str)
        assert 'AnomalyDetector' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
