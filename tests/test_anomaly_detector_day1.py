"""Week 2 Day 1: AnomalyDetector Agent Integration Tests (10 tests).

Tests:
1. Agent initialization
2. Data loading
3. LOF detection
4. One-Class SVM detection
5. Isolation Forest detection
6. Ensemble detection
7. Detect all methods
8. Empty dataframe handling
9. Single row handling
10. Performance benchmark
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import time

from agents.anomaly_detector import AnomalyDetector


class TestAnomalyDetectorInitialization:
    """Test 1: Agent initialization."""

    def test_agent_initializes(self):
        """Test agent initializes successfully."""
        detector = AnomalyDetector()
        assert detector is not None
        assert detector.name == "AnomalyDetector"
        assert len(detector.workers) == 4
        assert detector.data is None


class TestAnomalyDetectorDataLoading:
    """Test 2: Data loading and management."""

    @pytest.fixture
    def detector(self):
        return AnomalyDetector()

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame (100 rows, 5 numeric columns)."""
        np.random.seed(42)
        return pd.DataFrame({
            'feature_1': np.random.randn(100),
            'feature_2': np.random.randn(100),
            'feature_3': np.random.randn(100),
            'feature_4': np.random.randn(100),
            'feature_5': np.random.randn(100),
        })

    def test_set_data(self, detector, sample_data):
        """Test setting data."""
        detector.set_data(sample_data)
        assert detector.data is not None
        assert detector.data.shape == (100, 5)

    def test_get_data(self, detector, sample_data):
        """Test getting data."""
        detector.set_data(sample_data)
        retrieved = detector.get_data()
        assert retrieved is not None
        assert retrieved.shape == sample_data.shape

    def test_data_copy(self, detector, sample_data):
        """Test data is copied (not referenced)."""
        detector.set_data(sample_data)
        sample_data.iloc[0, 0] = 999
        assert detector.get_data().iloc[0, 0] != 999


class TestLOFDetection:
    """Test 3: LOF (Local Outlier Factor) detection."""

    @pytest.fixture
    def detector_with_data(self):
        detector = AnomalyDetector()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100),
        })
        detector.set_data(df)
        return detector

    def test_lof_detection(self, detector_with_data):
        """Test LOF detection runs successfully."""
        result = detector_with_data.detect_lof()
        assert result is not None
        assert isinstance(result, dict)
        assert 'data' in result or 'anomalies' in result or 'scores' in result

    def test_lof_with_parameters(self, detector_with_data):
        """Test LOF with custom parameters."""
        result = detector_with_data.detect_lof(n_neighbors=10, contamination=0.05)
        assert result is not None

    def test_lof_results_stored(self, detector_with_data):
        """Test LOF results are stored in detection_results."""
        detector_with_data.detect_lof()
        assert 'lof' in detector_with_data.detection_results


class TestOCSVMDetection:
    """Test 4: One-Class SVM detection."""

    @pytest.fixture
    def detector_with_data(self):
        detector = AnomalyDetector()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
        })
        detector.set_data(df)
        return detector

    def test_ocsvm_detection(self, detector_with_data):
        """Test One-Class SVM detection runs successfully."""
        result = detector_with_data.detect_ocsvm()
        assert result is not None
        assert isinstance(result, dict)

    def test_ocsvm_with_parameters(self, detector_with_data):
        """Test One-Class SVM with custom parameters."""
        result = detector_with_data.detect_ocsvm(nu=0.1, kernel='linear')
        assert result is not None


class TestIsolationForestDetection:
    """Test 5: Isolation Forest detection."""

    @pytest.fixture
    def detector_with_data(self):
        detector = AnomalyDetector()
        np.random.seed(42)
        df = pd.DataFrame({
            'a': np.random.randn(100),
            'b': np.random.randn(100),
            'c': np.random.randn(100),
        })
        detector.set_data(df)
        return detector

    def test_isolation_forest_detection(self, detector_with_data):
        """Test Isolation Forest detection runs successfully."""
        result = detector_with_data.detect_isolation_forest()
        assert result is not None
        assert isinstance(result, dict)

    def test_isolation_forest_with_parameters(self, detector_with_data):
        """Test Isolation Forest with custom parameters."""
        result = detector_with_data.detect_isolation_forest(
            contamination=0.1,
            n_estimators=50
        )
        assert result is not None


class TestEnsembleDetection:
    """Test 6: Ensemble detection."""

    @pytest.fixture
    def detector_with_data(self):
        detector = AnomalyDetector()
        np.random.seed(42)
        df = pd.DataFrame({
            'col1': np.random.randn(100),
            'col2': np.random.randn(100),
        })
        detector.set_data(df)
        return detector

    def test_ensemble_detection(self, detector_with_data):
        """Test ensemble detection runs successfully."""
        result = detector_with_data.detect_ensemble()
        assert result is not None
        assert isinstance(result, dict)

    def test_ensemble_with_threshold(self, detector_with_data):
        """Test ensemble with custom threshold."""
        result = detector_with_data.detect_ensemble(threshold=0.6)
        assert result is not None


class TestDetectAll:
    """Test 7: Run all detection methods simultaneously."""

    @pytest.fixture
    def detector_with_data(self):
        detector = AnomalyDetector()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100),
        })
        detector.set_data(df)
        return detector

    def test_detect_all(self, detector_with_data):
        """Test all detection methods run together."""
        results = detector_with_data.detect_all()
        assert results is not None
        assert isinstance(results, dict)
        assert len(results) > 0

    def test_detect_all_with_custom_params(self, detector_with_data):
        """Test detect_all with custom parameters."""
        results = detector_with_data.detect_all(
            lof_params={'n_neighbors': 15},
            ocsvm_params={'nu': 0.1},
            iforest_params={'contamination': 0.15},
            ensemble_params={'threshold': 0.5}
        )
        assert results is not None


class TestEdgeCases:
    """Test 8: Empty dataframe handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        detector = AnomalyDetector()
        empty_df = pd.DataFrame()
        detector.set_data(empty_df)
        assert detector.get_data() is not None
        assert detector.get_data().shape[0] == 0

    def test_single_row_dataframe(self):
        """Test 9: Single row handling."""
        detector = AnomalyDetector()
        single_row = pd.DataFrame({
            'x': [1.0],
            'y': [2.0],
            'z': [3.0]
        })
        detector.set_data(single_row)
        assert detector.get_data().shape[0] == 1

    def test_no_data_error(self):
        """Test error when no data is set."""
        detector = AnomalyDetector()
        with pytest.raises(Exception):
            detector.detect_lof()


class TestPerformance:
    """Test 10: Performance benchmark."""

    def test_detection_performance_1k_rows(self):
        """Test detection on 1,000 rows completes in reasonable time."""
        detector = AnomalyDetector()
        np.random.seed(42)
        df = pd.DataFrame({
            f'feature_{i}': np.random.randn(1000)
            for i in range(5)
        })
        detector.set_data(df)

        start = time.time()
        results = detector.detect_all()
        elapsed = time.time() - start

        assert elapsed < 30  # Should complete in < 30 seconds
        assert results is not None


class TestSummaryReport:
    """Test summary report generation."""

    def test_summary_report(self):
        """Test summary report generation."""
        detector = AnomalyDetector()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
        })
        detector.set_data(df)
        detector.detect_all()

        report = detector.summary_report()
        assert report is not None
        assert 'status' in report
        assert 'timestamp' in report
        assert 'total_detections' in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
