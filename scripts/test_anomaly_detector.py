#!/usr/bin/env python3
"""Pytest-compatible tests for Anomaly Detector agent using diverse challenging datasets.

Tests cover:
- LOF (Local Outlier Factor) detection
- One-Class SVM detection
- Isolation Forest detection
- Ensemble voting method
- Summary report generation
- Batch detection (detect_all)
- Performance with large datasets (10MB+)

Datasets tested:
- Small: sample_data.csv
- Medium: fitness_dataset.csv, ted_main.csv
- Large: hotel_bookings.csv, fifa21_raw_data.csv
- Huge: olist_geolocation_dataset.csv (61MB)

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
        return DataLoader()
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    @pytest.fixture
    def sample_data(self, loader):
        sample_file = project_root / "data" / "sample_data.csv"
        result = loader.load(str(sample_file))
        assert result['status'] == 'success'
        return result['data']
    
    def test_detector_initialization(self, detector):
        assert detector is not None
        assert detector.name == 'AnomalyDetector'
        assert len(detector.workers) == 4
    
    def test_set_data(self, detector, sample_data):
        detector.set_data(sample_data)
        assert detector.data is not None
        assert len(detector.data) == len(sample_data)
    
    def test_lof_detection(self, detector, sample_data):
        detector.set_data(sample_data)
        result = detector.detect_lof(n_neighbors=5, contamination=0.1)
        assert result is not None
        assert isinstance(result, dict)
    
    def test_ocsvm_detection(self, detector, sample_data):
        detector.set_data(sample_data)
        result = detector.detect_ocsvm(nu=0.05, kernel='rbf')
        assert result is not None
        assert isinstance(result, dict)
    
    def test_isolation_forest_detection(self, detector, sample_data):
        detector.set_data(sample_data)
        result = detector.detect_isolation_forest(contamination=0.1)
        assert result is not None
        assert isinstance(result, dict)
    
    def test_ensemble_detection(self, detector, sample_data):
        detector.set_data(sample_data)
        result = detector.detect_ensemble(threshold=0.5)
        assert result is not None
        assert isinstance(result, dict)
    
    def test_detect_all(self, detector, sample_data):
        detector.set_data(sample_data)
        results = detector.detect_all()
        assert results is not None
        assert isinstance(results, dict)
        assert len(results) > 0
    
    def test_summary_report(self, detector, sample_data):
        detector.set_data(sample_data)
        detector.detect_all()
        report = detector.summary_report()
        assert report is not None
        assert 'status' in report
        assert report['status'] == 'success'


class TestAnomalyDetectorWithMediumData:
    """Test with medium datasets (~7-17MB)."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    @pytest.fixture
    def ted_data(self, loader):
        data_file = project_root / "data" / "ted_main.csv"
        if not data_file.exists():
            pytest.skip("ted_main.csv not found")
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load ted_main.csv")
        return result['data']
    
    def test_lof_on_ted(self, detector, ted_data):
        detector.set_data(ted_data)
        result = detector.detect_lof()
        assert result is not None
        logger.info(f"TED talks LOF detection completed")
    
    def test_isolation_forest_on_ted(self, detector, ted_data):
        detector.set_data(ted_data)
        result = detector.detect_isolation_forest()
        assert result is not None
        logger.info(f"TED talks Isolation Forest completed")


class TestAnomalyDetectorWithLargeData:
    """Test with large datasets (10-20MB)."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
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
    
    def test_lof_hotel(self, detector, hotel_data):
        detector.set_data(hotel_data)
        start = time.time()
        result = detector.detect_lof()
        elapsed = time.time() - start
        assert result is not None
        logger.info(f"Hotel ({len(hotel_data):,} rows): LOF in {elapsed:.2f}s")
    
    def test_isolation_forest_fifa(self, detector, fifa_data):
        detector.set_data(fifa_data)
        start = time.time()
        result = detector.detect_isolation_forest()
        elapsed = time.time() - start
        assert result is not None
        logger.info(f"FIFA 21 ({len(fifa_data):,} rows): Isolation Forest in {elapsed:.2f}s")
    
    def test_detect_all_hotel(self, detector, hotel_data):
        detector.set_data(hotel_data)
        start = time.time()
        results = detector.detect_all()
        elapsed = time.time() - start
        assert results is not None
        assert len(results) > 0
        logger.info(f"Hotel ({len(hotel_data):,} rows): all methods in {elapsed:.2f}s")


class TestAnomalyDetectorPerformance:
    """Performance tests with huge dataset (61MB)."""
    
    @pytest.fixture
    def loader(self):
        return DataLoader()
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    @pytest.fixture
    def geolocation_data(self, loader):
        data_file = project_root / "data" / "olist_geolocation_dataset.csv"
        if not data_file.exists():
            pytest.skip("olist_geolocation_dataset.csv not found")
        result = loader.load(str(data_file))
        if result['status'] != 'success':
            pytest.skip("Could not load olist_geolocation_dataset.csv")
        return result['data']
    
    def test_lof_huge_dataset(self, detector, geolocation_data):
        detector.set_data(geolocation_data)
        start = time.time()
        result = detector.detect_lof()
        elapsed = time.time() - start
        assert result is not None
        logger.info(f"Huge dataset ({len(geolocation_data):,} rows): LOF in {elapsed:.2f}s")
        assert elapsed < 60.0
    
    def test_isolation_forest_huge_dataset(self, detector, geolocation_data):
        detector.set_data(geolocation_data)
        start = time.time()
        result = detector.detect_isolation_forest()
        elapsed = time.time() - start
        assert result is not None
        logger.info(f"Huge dataset ({len(geolocation_data):,} rows): Isolation Forest in {elapsed:.2f}s")
        assert elapsed < 60.0
    
    def test_detect_all_huge_dataset(self, detector, geolocation_data):
        detector.set_data(geolocation_data)
        start = time.time()
        results = detector.detect_all()
        elapsed = time.time() - start
        assert results is not None
        logger.info(f"Huge dataset ({len(geolocation_data):,} rows): all methods in {elapsed:.2f}s")
        assert elapsed < 120.0


class TestAnomalyDetectorEdgeCases:
    """Edge case tests."""
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    def test_small_dataframe(self, detector):
        df = pd.DataFrame({
            'value1': [1, 2, 3, 4, 100],
            'value2': [10, 20, 30, 40, 500]
        })
        detector.set_data(df)
        result = detector.detect_isolation_forest()
        assert result is not None
    
    def test_no_anomalies(self, detector):
        df = pd.DataFrame({
            'value1': [1, 2, 3, 4, 5],
            'value2': [10, 20, 30, 40, 50]
        })
        detector.set_data(df)
        result = detector.detect_isolation_forest(contamination=0.01)
        assert result is not None
    
    def test_mixed_types(self, detector):
        df = pd.DataFrame({
            'numeric': [1, 2, 3, 4, 5],
            'category': ['a', 'b', 'c', 'd', 'e']
        })
        detector.set_data(df)
        result = detector.detect_isolation_forest()
        assert result is not None
    
    def test_get_summary(self, detector):
        df = pd.DataFrame({'value': [1, 2, 3]})
        detector.set_data(df)
        summary = detector.get_summary()
        assert summary is not None
        assert isinstance(summary, str)
        assert 'AnomalyDetector' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
