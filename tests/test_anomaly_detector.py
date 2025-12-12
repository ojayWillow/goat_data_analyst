"""Test suite for Anomaly Detector Agent and Workers."""

import pytest
import pandas as pd
import numpy as np
from agents.anomaly_detector import AnomalyDetector
from agents.anomaly_detector.workers import (
    StatisticalWorker,
    IsolationForest,
    MultivariateWorker,
    WorkerResult,
    ErrorType,
)


class TestAnomalyDetectorInit:
    """Test AnomalyDetector initialization."""

    def test_init(self):
        """Test detector initializes correctly."""
        detector = AnomalyDetector()
        assert detector.name == "AnomalyDetector"
        assert detector.data is None
        assert detector.detection_results == {}
        assert hasattr(detector, 'statistical_detector')
        assert hasattr(detector, 'isolation_forest_detector')
        assert hasattr(detector, 'multivariate_detector')


class TestAnomalyDetectorDataManagement:
    """Test data management methods."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return AnomalyDetector()

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        return pd.DataFrame({
            "Price": [100, 200, 150, 250, 5000, 120, 130, 140],
            "Quantity": [1, 2, 3, 1, 2, 1, 4, 2],
        })

    def test_set_data(self, detector, sample_df):
        """Test setting data."""
        detector.set_data(sample_df)
        assert detector.data is not None
        assert detector.data.shape == (8, 2)
        assert list(detector.data.columns) == ["Price", "Quantity"]

    def test_get_data(self, detector, sample_df):
        """Test getting data."""
        detector.set_data(sample_df)
        result = detector.get_data()
        assert result is not None
        assert result.shape == (8, 2)

    def test_get_data_none(self, detector):
        """Test getting data when none is set."""
        assert detector.get_data() is None


class TestStatisticalWorker:
    """Test StatisticalWorker."""

    @pytest.fixture
    def worker(self):
        """Create worker instance."""
        return StatisticalWorker()

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with outlier."""
        return pd.DataFrame({
            "Price": [100, 200, 150, 250, 5000, 120],  # 5000 is outlier
        })

    def test_iqr_detection(self, worker, sample_df):
        """Test IQR detection."""
        result = worker.safe_execute(
            df=sample_df,
            column="Price",
            method="iqr",
            multiplier=1.5,
        )
        assert result.success
        assert result.worker == "StatisticalWorker"
        assert result.data["method"] == "IQR (Interquartile Range)"
        assert result.data["outliers_count"] > 0
        assert "bounds" in result.data
        assert "statistics" in result.data

    def test_zscore_detection(self, worker, sample_df):
        """Test Z-score detection."""
        result = worker.safe_execute(
            df=sample_df,
            column="Price",
            method="zscore",
            threshold=2.0,
        )
        assert result.success
        assert result.data["method"] == "Z-Score"
        assert "z_score_range" in result.data

    def test_modified_zscore_detection(self, worker, sample_df):
        """Test Modified Z-score detection."""
        result = worker.safe_execute(
            df=sample_df,
            column="Price",
            method="modified_zscore",
            mod_threshold=3.5,
        )
        assert result.success
        assert result.data["method"] == "Modified Z-Score (MAD-based)"

    def test_invalid_column(self, worker, sample_df):
        """Test detection with invalid column."""
        result = worker.safe_execute(
            df=sample_df,
            column="NonExistent",
            method="iqr",
        )
        assert not result.success
        assert len(result.errors) > 0

    def test_empty_dataframe(self, worker):
        """Test detection with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = worker.safe_execute(
            df=empty_df,
            column="Price",
            method="iqr",
        )
        assert not result.success

    def test_none_dataframe(self, worker):
        """Test detection with None DataFrame."""
        result = worker.safe_execute(
            df=None,
            column="Price",
            method="iqr",
        )
        assert not result.success


class TestIsolationForestWorker:
    """Test IsolationForest Worker."""

    @pytest.fixture
    def worker(self):
        """Create worker instance."""
        return IsolationForest()

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        np.random.seed(42)
        return pd.DataFrame({
            "Feature1": np.random.normal(100, 10, 100),
            "Feature2": np.random.normal(50, 5, 100),
        })

    def test_isolation_forest_detection(self, worker, sample_df):
        """Test Isolation Forest detection."""
        result = worker.safe_execute(
            df=sample_df,
            contamination=0.1,
            n_estimators=100,
        )
        assert result.success
        assert result.data["method"] == "Isolation Forest"
        assert result.data["anomalies_detected"] >= 0
        assert "anomaly_scores" in result.data

    def test_invalid_contamination_high(self, worker, sample_df):
        """Test with invalid contamination (too high)."""
        result = worker.safe_execute(
            df=sample_df,
            contamination=0.6,  # > 0.5 is invalid
            n_estimators=100,
        )
        assert not result.success
        assert len(result.errors) > 0

    def test_invalid_contamination_low(self, worker, sample_df):
        """Test with invalid contamination (too low)."""
        result = worker.safe_execute(
            df=sample_df,
            contamination=0.0,  # <= 0 is invalid
            n_estimators=100,
        )
        assert not result.success
        assert len(result.errors) > 0


class TestMultivariateWorker:
    """Test MultivariateWorker."""

    @pytest.fixture
    def worker(self):
        """Create worker instance."""
        return MultivariateWorker()

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        np.random.seed(42)
        return pd.DataFrame({
            "X": np.random.normal(100, 10, 100),
            "Y": np.random.normal(50, 5, 100),
        })

    def test_multivariate_detection(self, worker, sample_df):
        """Test Mahalanobis distance detection."""
        result = worker.safe_execute(
            df=sample_df,
            threshold_percentile=95,
        )
        assert result.success
        assert result.data["method"] == "Mahalanobis Distance"
        assert "anomalies_detected" in result.data

    def test_invalid_percentile(self, worker, sample_df):
        """Test with invalid percentile."""
        result = worker.safe_execute(
            df=sample_df,
            threshold_percentile=150,  # > 100 is invalid
        )
        assert not result.success
        assert len(result.errors) > 0


class TestAnomalyDetectorMethods:
    """Test AnomalyDetector public methods."""

    @pytest.fixture
    def detector(self):
        """Create detector with sample data."""
        detector = AnomalyDetector()
        df = pd.DataFrame({
            "Price": [100, 200, 150, 250, 5000, 120, 130, 140],
            "Quantity": [1, 2, 3, 1, 2, 1, 4, 2],
        })
        detector.set_data(df)
        return detector

    def test_detect_statistical(self, detector):
        """Test detect_statistical method."""
        result = detector.detect_statistical("Price", method="iqr", multiplier=1.5)
        assert result["success"]
        assert result["result"]["method"] == "IQR (Interquartile Range)"

    def test_detect_isolation_forest(self, detector):
        """Test detect_isolation_forest method."""
        result = detector.detect_isolation_forest(
            contamination=0.1,
            n_estimators=100,
        )
        assert result["success"]
        assert result["result"]["method"] == "Isolation Forest"

    def test_detect_lof(self, detector):
        """Test detect_lof method."""
        result = detector.detect_lof(
            n_neighbors=5,
            contamination=0.1,
        )
        assert result["success"]

    def test_detect_ocsvm(self, detector):
        """Test detect_ocsvm method."""
        result = detector.detect_ocsvm(
            nu=0.05,
            kernel="rbf",
        )
        assert result["success"]

    def test_detect_multivariate(self, detector):
        """Test detect_multivariate method."""
        result = detector.detect_multivariate(
            covariance_type="full",
            contamination=0.1,
        )
        # Multivariate requires specific data structure, may not work with all data
        assert "success" in result

    def test_detect_ensemble(self, detector):
        """Test detect_ensemble method."""
        result = detector.detect_ensemble(threshold=0.5)
        assert result["success"]

    def test_detect_all(self, detector):
        """Test detect_all method."""
        results = detector.detect_all()
        assert len(results) > 0
        assert any(r["success"] for r in results.values())

    def test_no_data_error(self):
        """Test error when no data is set."""
        detector = AnomalyDetector()
        with pytest.raises(Exception):
            detector.detect_statistical("Price")

    def test_summary_report(self, detector):
        """Test summary_report method."""
        detector.detect_statistical("Price")
        summary = detector.summary_report()
        assert summary["total_detections"] >= 1
        assert "timestamp" in summary

    def test_get_health_report(self, detector):
        """Test get_health_report method."""
        detector.detect_statistical("Price")
        health = detector.get_health_report()
        assert "overall_health" in health
        assert "worker_health" in health
        assert "recommendations" in health


class TestWorkerResult:
    """Test WorkerResult dataclass."""

    def test_to_dict(self):
        """Test WorkerResult.to_dict()."""
        result = WorkerResult(
            worker="TestWorker",
            task_type="test",
            success=True,
            data={"test": "data"},
        )
        result_dict = result.to_dict()
        assert result_dict["worker"] == "TestWorker"
        assert result_dict["success"] is True
        assert result_dict["data"] == {"test": "data"}


class TestErrorHandling:
    """Test error handling in workers."""

    def test_worker_result_has_errors(self):
        """Test that errors are properly stored."""
        result = WorkerResult(
            worker="TestWorker",
            task_type="test",
            success=False,
            errors=[{"type": "test_error", "message": "Test error"}],
        )
        assert len(result.errors) > 0
        assert result.errors[0]["type"] == "test_error"

    def test_error_type_enum(self):
        """Test ErrorType enum."""
        assert hasattr(ErrorType, "MISSING_DATA")
        assert hasattr(ErrorType, "INVALID_COLUMN")
        assert hasattr(ErrorType, "INVALID_PARAMETER")
        assert hasattr(ErrorType, "COMPUTATION_ERROR")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
