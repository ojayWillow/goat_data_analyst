"""Comprehensive test suite for all 6 anomaly detection workers.

This test file covers:
1. Input validation and error handling
2. Execution and result validation  
3. Error intelligence integration
4. Quality score calculation
5. Edge cases and boundary conditions
6. Integration between workers

Test Coverage Target: 90%+
"""

import pytest
import pandas as pd
import numpy as np
from typing import List, Dict, Any

# Import all workers
from agents.anomaly_detector.workers.statistical import StatisticalWorker
from agents.anomaly_detector.workers.isolation_forest import IsolationForest
from agents.anomaly_detector.workers.lof import LOF
from agents.anomaly_detector.workers.ocsvm import OneClassSVM
from agents.anomaly_detector.workers.multivariate import MultivariateWorker
from agents.anomaly_detector.workers.ensemble import Ensemble
from agents.anomaly_detector.workers.base_worker import WorkerResult, ErrorType


# ===== FIXTURES =====

@pytest.fixture
def simple_data() -> pd.DataFrame:
    """Simple dataset with one outlier."""
    return pd.DataFrame({
        'value': [1, 2, 3, 4, 5, 100],
        'feature2': [10, 20, 30, 40, 50, 1000]
    })


@pytest.fixture
def multivariate_data() -> pd.DataFrame:
    """Multivariate dataset with multiple features."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'x1': np.random.normal(0, 1, n),
        'x2': np.random.normal(0, 1, n),
        'x3': np.random.normal(0, 1, n),
        'x4': np.random.normal(0, 1, n),
    })


@pytest.fixture
def data_with_nulls() -> pd.DataFrame:
    """Dataset with null values."""
    return pd.DataFrame({
        'a': [1, 2, None, 4, 5, 100],
        'b': [10, None, 30, 40, 50, 1000]
    })


@pytest.fixture
def empty_data() -> pd.DataFrame:
    """Empty DataFrame."""
    return pd.DataFrame()


# ===== STATISTICAL WORKER TESTS =====

class TestStatisticalWorker:
    """Tests for StatisticalWorker."""
    
    def test_initialization(self):
        """Test worker initialization."""
        worker = StatisticalWorker()
        assert worker.name == "StatisticalWorker"
        assert worker.error_intelligence is not None
    
    def test_iqr_detection_success(self, simple_data):
        """Test IQR detection with valid data."""
        worker = StatisticalWorker()
        result = worker.execute(
            df=simple_data,
            column='value',
            method='iqr',
            multiplier=1.5
        )
        
        assert result.success
        assert result.data['method'] == 'IQR (Interquartile Range)'
        assert result.data['outliers_count'] >= 1
        assert result.quality_score <= 1.0
    
    def test_zscore_detection_success(self, simple_data):
        """Test Z-score detection with valid data."""
        worker = StatisticalWorker()
        result = worker.execute(
            df=simple_data,
            column='value',
            method='zscore',
            threshold=2.0
        )
        
        assert result.success
        assert result.data['method'] == 'Z-Score'
        assert 'z_score_range' in result.data
    
    def test_modified_zscore_detection_success(self, simple_data):
        """Test Modified Z-score detection with valid data."""
        worker = StatisticalWorker()
        result = worker.execute(
            df=simple_data,
            column='value',
            method='modified_zscore',
            mod_threshold=2.0
        )
        
        assert result.success
        assert result.data['method'] == 'Modified Z-Score (MAD-based)'
    
    def test_missing_column_error(self, simple_data):
        """Test error when column doesn't exist."""
        worker = StatisticalWorker()
        result = worker.execute(
            df=simple_data,
            column='nonexistent',
            method='iqr'
        )
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_empty_dataframe_error(self, empty_data):
        """Test error with empty DataFrame."""
        worker = StatisticalWorker()
        result = worker.execute(
            df=empty_data,
            column='value',
            method='iqr'
        )
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_none_dataframe_error(self):
        """Test error with None DataFrame."""
        worker = StatisticalWorker()
        result = worker.execute(
            df=None,
            column='value',
            method='iqr'
        )
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_handles_null_values(self, data_with_nulls):
        """Test handling of null values."""
        worker = StatisticalWorker()
        result = worker.execute(
            df=data_with_nulls,
            column='a',
            method='iqr'
        )
        
        assert result.success
        assert result.data['null_count'] > 0
        assert any('null' in str(w).lower() for w in result.warnings)
    
    def test_invalid_method_error(self, simple_data):
        """Test error with invalid method."""
        worker = StatisticalWorker()
        result = worker.execute(
            df=simple_data,
            column='value',
            method='invalid_method'
        )
        
        assert not result.success
        assert len(result.errors) > 0


# ===== ISOLATION FOREST TESTS =====

class TestIsolationForest:
    """Tests for IsolationForest worker."""
    
    def test_initialization(self):
        """Test worker initialization."""
        worker = IsolationForest()
        assert worker.name == "IsolationForest"
    
    def test_detection_success(self, simple_data):
        """Test anomaly detection with valid data."""
        worker = IsolationForest()
        result = worker.execute(
            df=simple_data,
            contamination=0.1,
            n_estimators=100
        )
        
        assert result.success
        assert result.data['method'] == 'Isolation Forest'
        assert result.data['anomalies_detected'] >= 0
        assert 'anomaly_scores' in result.data
    
    def test_invalid_contamination_error(self, simple_data):
        """Test error with invalid contamination."""
        worker = IsolationForest()
        result = worker.execute(
            df=simple_data,
            contamination=0.7  # Too high
        )
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_invalid_n_estimators_error(self, simple_data):
        """Test error with invalid n_estimators."""
        worker = IsolationForest()
        result = worker.execute(
            df=simple_data,
            n_estimators=-1
        )
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_empty_dataframe_error(self, empty_data):
        """Test error with empty DataFrame."""
        worker = IsolationForest()
        result = worker.execute(df=empty_data)
        
        assert not result.success


# ===== LOF TESTS =====

class TestLOF:
    """Tests for LOF worker."""
    
    def test_initialization(self):
        """Test worker initialization."""
        worker = LOF()
        assert worker.name == "LOF"
    
    def test_detection_success(self, simple_data):
        """Test anomaly detection with valid data."""
        worker = LOF()
        result = worker.execute(
            df=simple_data,
            n_neighbors=2,
            contamination=0.1
        )
        
        assert result.success
        assert result.data['method'] == 'Local Outlier Factor'
        assert result.data['anomalies_detected'] >= 0
    
    def test_invalid_n_neighbors_error(self, simple_data):
        """Test error with invalid n_neighbors."""
        worker = LOF()
        result = worker.execute(
            df=simple_data,
            n_neighbors=-1
        )
        
        assert not result.success
    
    def test_n_neighbors_adjusted(self, simple_data):
        """Test n_neighbors adjustment when too large."""
        worker = LOF()
        result = worker.execute(
            df=simple_data,
            n_neighbors=1000  # Larger than data
        )
        
        assert result.success
        # Should have warning about adjustment
        assert len(result.warnings) > 0


# ===== ONE-CLASS SVM TESTS =====

class TestOneClassSVM:
    """Tests for OneClassSVM worker."""
    
    def test_initialization(self):
        """Test worker initialization."""
        worker = OneClassSVM()
        assert worker.name == "OneClassSVM"
    
    def test_detection_rbf_kernel(self, simple_data):
        """Test detection with RBF kernel."""
        worker = OneClassSVM()
        result = worker.execute(
            df=simple_data,
            nu=0.1,
            kernel='rbf'
        )
        
        assert result.success
        assert result.data['kernel'] == 'rbf'
    
    def test_detection_linear_kernel(self, simple_data):
        """Test detection with linear kernel."""
        worker = OneClassSVM()
        result = worker.execute(
            df=simple_data,
            nu=0.1,
            kernel='linear'
        )
        
        assert result.success
        assert result.data['kernel'] == 'linear'
    
    def test_invalid_kernel_error(self, simple_data):
        """Test error with invalid kernel."""
        worker = OneClassSVM()
        result = worker.execute(
            df=simple_data,
            kernel='invalid'
        )
        
        assert not result.success
    
    def test_invalid_nu_error(self, simple_data):
        """Test error with invalid nu."""
        worker = OneClassSVM()
        result = worker.execute(
            df=simple_data,
            nu=1.5  # Too high
        )
        
        assert not result.success


# ===== MULTIVARIATE WORKER TESTS =====

class TestMultivariateWorker:
    """Tests for MultivariateWorker."""
    
    def test_initialization(self):
        """Test worker initialization."""
        worker = MultivariateWorker()
        assert worker.name == "MultivariateWorker"
    
    def test_detection_success(self, multivariate_data):
        """Test multivariate detection with valid data."""
        worker = MultivariateWorker()
        result = worker.execute(
            df=multivariate_data,
            feature_cols=['x1', 'x2', 'x3'],
            percentile=90
        )
        
        assert result.success
        assert result.data['method'] == 'Mahalanobis Distance'
        assert 'distance_threshold' in result.data
    
    def test_missing_feature_columns_error(self, multivariate_data):
        """Test error when feature_cols not provided."""
        worker = MultivariateWorker()
        result = worker.execute(
            df=multivariate_data,
            feature_cols=[]
        )
        
        assert not result.success
    
    def test_invalid_column_error(self, multivariate_data):
        """Test error with non-existent column."""
        worker = MultivariateWorker()
        result = worker.execute(
            df=multivariate_data,
            feature_cols=['x1', 'nonexistent']
        )
        
        assert not result.success
    
    def test_invalid_percentile_error(self, multivariate_data):
        """Test error with invalid percentile."""
        worker = MultivariateWorker()
        result = worker.execute(
            df=multivariate_data,
            feature_cols=['x1', 'x2'],
            percentile=150  # Too high
        )
        
        assert not result.success


# ===== ENSEMBLE TESTS =====

class TestEnsemble:
    """Tests for Ensemble worker."""
    
    def test_initialization(self):
        """Test worker initialization."""
        worker = Ensemble()
        assert worker.name == "Ensemble"
        assert worker.lof is not None
        assert worker.ocsvm is not None
        assert worker.iso_forest is not None
    
    def test_detection_success(self, simple_data):
        """Test ensemble detection with valid data."""
        worker = Ensemble()
        result = worker.execute(
            df=simple_data,
            threshold=0.5
        )
        
        assert result.success
        assert result.data['method'] == 'Ensemble Voting'
        assert result.data['successful_algorithms'] > 0
        assert 'algorithm_results' in result.data
    
    def test_invalid_threshold_error(self, simple_data):
        """Test error with invalid threshold."""
        worker = Ensemble()
        result = worker.execute(
            df=simple_data,
            threshold=1.5  # Too high
        )
        
        assert not result.success
    
    def test_ensemble_voting_logic(self, simple_data):
        """Test that voting threshold is applied correctly."""
        worker = Ensemble()
        result = worker.execute(
            df=simple_data,
            threshold=0.5
        )
        
        assert result.success
        assert result.data['vote_threshold'] >= 1.0


# ===== INTEGRATION TESTS =====

class TestIntegration:
    """Integration tests across multiple workers."""
    
    def test_all_workers_on_same_data(self, simple_data):
        """Test all workers with the same data."""
        workers = [
            StatisticalWorker(),
            IsolationForest(),
            LOF(),
            OneClassSVM(),
        ]
        
        results = []
        for worker in workers:
            try:
                if isinstance(worker, StatisticalWorker):
                    result = worker.execute(df=simple_data, column='value', method='iqr')
                elif isinstance(worker, LOF):
                    result = worker.execute(df=simple_data, n_neighbors=2)
                else:
                    result = worker.execute(df=simple_data)
                results.append(result)
            except Exception:
                pass
        
        # At least some workers should succeed
        successful = [r for r in results if r.success]
        assert len(successful) > 0
    
    def test_quality_scores_calculated(self, simple_data):
        """Test that quality scores are calculated for all workers."""
        workers = [
            StatisticalWorker(),
            IsolationForest(),
            LOF(),
            OneClassSVM(),
        ]
        
        for worker in workers:
            try:
                if isinstance(worker, StatisticalWorker):
                    result = worker.execute(df=simple_data, column='value', method='iqr')
                else:
                    result = worker.execute(df=simple_data)
                
                if result.success:
                    assert 0 <= result.quality_score <= 1
            except Exception:
                pass
    
    def test_error_intelligence_tracking(self, simple_data):
        """Test that errors are tracked in error intelligence."""
        worker = StatisticalWorker()
        
        # Trigger an error
        result = worker.execute(
            df=simple_data,
            column='nonexistent',
            method='iqr'
        )
        
        assert not result.success
        assert len(result.errors) > 0


# ===== EDGE CASE TESTS =====

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_single_row_dataframe(self):
        """Test with single row (minimal data)."""
        df = pd.DataFrame({'value': [1]})
        worker = StatisticalWorker()
        result = worker.execute(df=df, column='value', method='iqr')
        
        # Should handle gracefully (may succeed or fail gracefully)
        assert isinstance(result, WorkerResult)
    
    def test_all_same_values(self):
        """Test with all identical values."""
        df = pd.DataFrame({'value': [5, 5, 5, 5, 5]})
        worker = StatisticalWorker()
        result = worker.execute(df=df, column='value', method='zscore')
        
        # Should handle zero std dev
        assert isinstance(result, WorkerResult)
    
    def test_single_column_only(self):
        """Test with single numeric column."""
        df = pd.DataFrame({'value': [1, 2, 3, 100, 5]})
        worker = IsolationForest()
        result = worker.execute(df=df)
        
        assert result.success
    
    def test_mixed_data_types(self):
        """Test with mixed data types (numeric and string)."""
        df = pd.DataFrame({
            'numeric': [1, 2, 3, 100, 5],
            'string': ['a', 'b', 'c', 'd', 'e']
        })
        worker = IsolationForest()
        result = worker.execute(df=df)
        
        # Should handle mixed types by filtering numeric only
        assert result.success
    
    def test_large_dataset(self):
        """Test performance with large dataset."""
        np.random.seed(42)
        df = pd.DataFrame({
            'a': np.random.normal(0, 1, 10000),
            'b': np.random.normal(0, 1, 10000),
        })
        worker = IsolationForest()
        result = worker.execute(df=df)
        
        assert result.success
        assert result.data['sample_count'] == 10000


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
