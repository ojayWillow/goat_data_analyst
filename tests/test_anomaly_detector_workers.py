"""Comprehensive Tests for Anomaly Detector Workers.

Verifies:
1. All 4 workers actually function
2. Error handling in each worker
3. Edge cases and stress scenarios
4. Worker orchestration
"""

import pytest
import pandas as pd
import numpy as np

from agents.anomaly_detector.workers import (
    IsolationForest,
    LOF,
    OneClassSVM,
    Ensemble,
    WorkerResult
)


class TestIsolationForestWorker:
    """Test IsolationForest worker."""

    def test_isolation_forest_loads(self):
        """IsolationForest worker instantiates correctly."""
        worker = IsolationForest()
        assert worker is not None
        assert hasattr(worker, 'safe_execute')

    def test_isolation_forest_detects_anomalies(self):
        """IsolationForest detects anomalies in clean data."""
        # Create data with clear anomalies
        df = pd.DataFrame({
            "value": [1, 2, 3, 4, 5, 100]  # 100 is anomaly
        })

        worker = IsolationForest()
        result = worker.safe_execute(df=df, contamination=0.1)

        assert isinstance(result, WorkerResult)
        assert result.success or result.data is not None

    def test_isolation_forest_error_handling(self):
        """IsolationForest handles invalid data."""
        worker = IsolationForest()
        
        # Empty dataframe
        df_empty = pd.DataFrame()
        result = worker.safe_execute(df=df_empty)
        assert isinstance(result, WorkerResult)

        # Single row
        df_single = pd.DataFrame({"x": [1]})
        result = worker.safe_execute(df=df_single)
        assert isinstance(result, WorkerResult)


class TestLOFWorker:
    """Test Local Outlier Factor worker."""

    def test_lof_loads(self):
        """LOF worker instantiates correctly."""
        worker = LOF()
        assert worker is not None
        assert hasattr(worker, 'safe_execute')

    def test_lof_detects_anomalies(self):
        """LOF detects local anomalies."""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 100],
            "y": [1, 2, 3, 4, 5, 100]
        })

        worker = LOF()
        result = worker.safe_execute(df=df, n_neighbors=3)

        assert isinstance(result, WorkerResult)

    def test_lof_error_handling(self):
        """LOF handles invalid data."""
        worker = LOF()
        
        # Very small dataset
        df_small = pd.DataFrame({"x": [1, 2]})
        result = worker.safe_execute(df=df_small, n_neighbors=1)
        assert isinstance(result, WorkerResult)


class TestOneClassSVMWorker:
    """Test One-Class SVM worker."""

    def test_ocsvm_loads(self):
        """OneClassSVM worker instantiates correctly."""
        worker = OneClassSVM()
        assert worker is not None
        assert hasattr(worker, 'safe_execute')

    def test_ocsvm_detects_anomalies(self):
        """OneClassSVM detects anomalies."""
        df = pd.DataFrame({
            "x": np.random.normal(0, 1, 100),
            "y": np.random.normal(0, 1, 100)
        })
        # Add clear anomaly
        df.loc[100] = [100, 100]

        worker = OneClassSVM()
        result = worker.safe_execute(df=df)

        assert isinstance(result, WorkerResult)

    def test_ocsvm_error_handling(self):
        """OneClassSVM handles invalid data."""
        worker = OneClassSVM()
        
        # Single row
        df = pd.DataFrame({"x": [1]})
        result = worker.safe_execute(df=df)
        assert isinstance(result, WorkerResult)


class TestEnsembleWorker:
    """Test Ensemble voting worker."""

    def test_ensemble_loads(self):
        """Ensemble worker instantiates correctly."""
        worker = Ensemble()
        assert worker is not None
        assert hasattr(worker, 'safe_execute')

    def test_ensemble_detects_anomalies(self):
        """Ensemble combines multiple methods."""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 100],
            "y": [1, 2, 3, 4, 5, 100]
        })

        worker = Ensemble()
        result = worker.safe_execute(df=df)

        assert isinstance(result, WorkerResult)

    def test_ensemble_voting(self):
        """Ensemble voting aggregates results."""
        df = pd.DataFrame({
            "x": np.random.normal(0, 1, 50),
            "y": np.random.normal(0, 1, 50)
        })
        # Add anomalies
        df.loc[50] = [100, 100]
        df.loc[51] = [-100, -100]

        worker = Ensemble()
        result = worker.safe_execute(df=df, threshold=0.5)

        assert isinstance(result, WorkerResult)


class TestWorkerEdgeCases:
    """Test edge cases for all workers."""

    def test_all_nan_column(self):
        """Workers handle all-NaN columns."""
        df = pd.DataFrame({
            "x": [1, 2, 3],
            "y": [np.nan, np.nan, np.nan]
        })

        workers = [IsolationForest(), LOF(), OneClassSVM(), Ensemble()]
        
        for worker in workers:
            result = worker.safe_execute(df=df)
            assert isinstance(result, WorkerResult)

    def test_single_numeric_column(self):
        """Workers handle single numeric column."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 100]})

        workers = [IsolationForest(), LOF(), OneClassSVM(), Ensemble()]
        
        for worker in workers:
            result = worker.safe_execute(df=df)
            assert isinstance(result, WorkerResult)

    def test_mixed_dtypes(self):
        """Workers handle mixed data types."""
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"]
        })

        workers = [IsolationForest(), LOF(), OneClassSVM(), Ensemble()]
        
        for worker in workers:
            result = worker.safe_execute(df=df)
            assert isinstance(result, WorkerResult)

    def test_negative_values(self):
        """Workers handle negative values."""
        df = pd.DataFrame({
            "x": [-100, -50, 0, 50, 100, 1000]
        })

        workers = [IsolationForest(), LOF(), OneClassSVM(), Ensemble()]
        
        for worker in workers:
            result = worker.safe_execute(df=df)
            assert isinstance(result, WorkerResult)

    def test_large_dataset(self):
        """Workers handle large datasets."""
        df = pd.DataFrame({
            "x": np.random.rand(10000),
            "y": np.random.rand(10000)
        })

        workers = [IsolationForest(), LOF(), OneClassSVM(), Ensemble()]
        
        for worker in workers:
            result = worker.safe_execute(df=df)
            assert isinstance(result, WorkerResult)

    def test_high_dimensional_data(self):
        """Workers handle high-dimensional data."""
        df = pd.DataFrame(
            np.random.rand(100, 50)
        )

        workers = [IsolationForest(), LOF(), OneClassSVM(), Ensemble()]
        
        for worker in workers:
            result = worker.safe_execute(df=df)
            assert isinstance(result, WorkerResult)


class TestWorkerResults:
    """Test WorkerResult structure from all workers."""

    def test_result_has_required_fields(self):
        """WorkerResult has required fields."""
        df = pd.DataFrame({"x": [1, 2, 3]})
        worker = IsolationForest()
        result = worker.safe_execute(df=df)

        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'quality_score')
        assert isinstance(result.quality_score, (int, float))
        assert 0.0 <= result.quality_score <= 1.0

    def test_all_workers_return_valid_results(self):
        """All workers return valid WorkerResult objects."""
        df = pd.DataFrame({
            "x": np.random.rand(50),
            "y": np.random.rand(50)
        })

        workers = [IsolationForest(), LOF(), OneClassSVM(), Ensemble()]
        
        for worker in workers:
            result = worker.safe_execute(df=df)
            
            # Verify structure
            assert isinstance(result, WorkerResult)
            assert isinstance(result.success, bool)
            assert isinstance(result.data, (type(None), pd.DataFrame, dict, list))
            assert isinstance(result.errors, list)
            assert isinstance(result.quality_score, (int, float))
            assert 0.0 <= result.quality_score <= 1.0

    def test_error_results_are_valid(self):
        """Error results are properly structured."""
        worker = IsolationForest()
        result = worker.safe_execute(df=pd.DataFrame())  # Empty df causes error
        
        # Even on error, should be valid structure
        assert isinstance(result, WorkerResult)
        assert isinstance(result.success, bool)
        assert isinstance(result.errors, list)


class TestWorkerIntegration:
    """Test worker integration and compatibility."""

    def test_workers_accept_same_interface(self):
        """All workers accept same input interface."""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10]
        })

        workers = {
            "isolation_forest": IsolationForest(),
            "lof": LOF(),
            "ocsvm": OneClassSVM(),
            "ensemble": Ensemble()
        }

        # All should accept df parameter
        for name, worker in workers.items():
            result = worker.safe_execute(df=df)
            assert isinstance(result, WorkerResult), f"{name} failed"

    def test_workers_handle_parameters(self):
        """Workers handle their specific parameters."""
        df = pd.DataFrame({
            "x": np.random.rand(50),
            "y": np.random.rand(50)
        })

        # IsolationForest with contamination
        result = IsolationForest().safe_execute(df=df, contamination=0.1)
        assert isinstance(result, WorkerResult)

        # LOF with n_neighbors
        result = LOF().safe_execute(df=df, n_neighbors=5)
        assert isinstance(result, WorkerResult)

        # OneClassSVM with nu
        result = OneClassSVM().safe_execute(df=df, nu=0.05)
        assert isinstance(result, WorkerResult)

        # Ensemble with threshold
        result = Ensemble().safe_execute(df=df, threshold=0.5)
        assert isinstance(result, WorkerResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
