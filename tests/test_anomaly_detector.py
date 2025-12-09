"""Test suite for Anomaly Detector Agent and Workers."""

import pytest
import pandas as pd
import numpy as np
from agents.anomaly_detector import AnomalyDetector
from agents.anomaly_detector.workers import (
    StatisticalWorker,
    IsolationForestWorker,
    MultivariateWorker,
    WorkerResult,
    ErrorType,
)


class TestAnomalyDetectorInit:
    """Test AnomalyDetector initialization."""

    def test_init(self):
        """Test detector initializes correctly."""
        detector = AnomalyDetector()
        assert detector.name == "Anomaly Detector"
        assert detector.data is None
        assert detector.detection_results == {}
        assert hasattr(detector, 'statistical_worker')
        assert hasattr(detector, 'isolation_forest_worker')
        assert hasattr(detector, 'multivariate_worker')


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
        assert result.data["method"] == "IQR"
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
        assert result.data["method"] == "Modified Z-Score"

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
    """Test IsolationForestWorker."""

    @pytest.fixture
    def worker(self):
        """Create worker instance."""
        return IsolationForestWorker()

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
            feature_cols=["Feature1", "Feature2"],
            contamination=0.1,
        )
        assert result.success
        assert result.data["method"] == "Isolation Forest"
        assert result.data["anomalies_count"] >= 0
        assert "anomaly_score_range" in result.data

    def test_invalid_feature_cols(self, worker, sample_df):
        """Test with invalid feature columns."""
        result = worker.safe_execute(
            df=sample_df,
            feature_cols=["NonExistent"],
            contamination=0.1,
        )
        assert not result.success

    def test_no_feature_cols(self, worker, sample_df):
        """Test with no feature columns."""
        result = worker.safe_execute(
            df=sample_df,
            feature_cols=[],
            contamination=0.1,
        )
        assert not result.success

    def test_invalid_contamination(self, worker, sample_df):
        """Test with invalid contamination."""
        result = worker.safe_execute(
            df=sample_df,
            feature_cols=["Feature1"],
            contamination=1.5,  # > 1.0 is invalid
        )
        assert not result.success


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
            feature_cols=["X", "Y"],
            percentile=95,
        )
        assert result.success
        assert result.data["method"] == "Mahalanobis Distance"
        assert "distance_statistics" in result.data
        assert "distance_threshold" in result.data

    def test_invalid_percentile(self, worker, sample_df):
        """Test with invalid percentile."""
        result = worker.safe_execute(
            df=sample_df,
            feature_cols=["X"],
            percentile=150,  # > 100 is invalid
        )
        assert not result.success


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

    def test_detect_iqr(self, detector):
        """Test detect_iqr method."""
        result = detector.detect_iqr("Price", multiplier=1.5)
        assert result["success"]
        assert result["data"]["method"] == "IQR"
        assert "iqr_Price" in detector.detection_results

    def test_detect_zscore(self, detector):
        """Test detect_zscore method."""
        result = detector.detect_zscore("Price", threshold=2.0)
        assert result["success"]
        assert result["data"]["method"] == "Z-Score"

    def test_detect_modified_zscore(self, detector):
        """Test detect_modified_zscore method."""
        result = detector.detect_modified_zscore("Price", threshold=3.5)
        assert result["success"]
        assert result["data"]["method"] == "Modified Z-Score"

    def test_detect_isolation_forest(self, detector):
        """Test detect_isolation_forest method."""
        result = detector.detect_isolation_forest(
            ["Price", "Quantity"],
            contamination=0.1,
        )
        assert result["success"]
        assert result["data"]["method"] == "Isolation Forest"

    def test_detect_multivariate(self, detector):
        """Test detect_multivariate method."""
        result = detector.detect_multivariate(
            ["Price", "Quantity"],
            percentile=95,
        )
        assert result["success"]
        assert result["data"]["method"] == "Mahalanobis Distance"

    def test_detect_all_statistical(self, detector):
        """Test detect_all_statistical method."""
        results = detector.detect_all_statistical("Price")
        assert "iqr" in results
        assert "zscore" in results
        assert "modified_zscore" in results
        assert all(r["success"] for r in results.values())

    def test_detect_all(self, detector):
        """Test detect_all method."""
        results = detector.detect_all(
            statistical_cols=["Price"],
            ml_feature_cols=["Price", "Quantity"],
        )
        assert "statistical_Price" in results
        assert "isolation_forest" in results
        assert "multivariate" in results

    def test_no_data_error(self):
        """Test error when no data is set."""
        detector = AnomalyDetector()
        with pytest.raises(Exception):
            detector.detect_iqr("Price")

    def test_summary_report(self, detector):
        """Test summary_report method."""
        detector.detect_iqr("Price")
        detector.detect_zscore("Price")
        summary = detector.summary_report()
        assert summary["total_detections"] == 2
        assert summary["successful"] >= 1
        assert "timestamp" in summary


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
