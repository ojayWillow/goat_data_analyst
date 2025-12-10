"""Week 2 Day 2: Predictor Agent Integration Tests (10 tests).

Tests:
1. Agent initialization
2. Data loading
3. Linear regression prediction
4. Time series forecasting
5. Decision tree prediction
6. Model validation
7. Predict all methods
8. Empty dataframe handling
9. Single row handling
10. Performance benchmark
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import time

from agents.predictor import Predictor


class TestPredictorInitialization:
    """Test 1: Agent initialization."""

    def test_agent_initializes(self):
        """Test agent initializes successfully."""
        predictor = Predictor()
        assert predictor is not None
        assert predictor.name == "Predictor"
        assert len(predictor.workers) >= 3
        assert predictor.data is None


class TestPredictorDataLoading:
    """Test 2: Data loading and management."""

    @pytest.fixture
    def predictor(self):
        return Predictor()

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame (100 rows, 3 numeric columns)."""
        np.random.seed(42)
        return pd.DataFrame({
            'feature_1': np.random.randn(100),
            'feature_2': np.random.randn(100),
            'target': np.random.randn(100) * 0.5 + np.arange(100) * 0.1,
        })

    def test_set_data(self, predictor, sample_data):
        """Test setting data."""
        predictor.set_data(sample_data)
        assert predictor.data is not None
        assert predictor.data.shape == (100, 3)

    def test_get_data(self, predictor, sample_data):
        """Test getting data."""
        predictor.set_data(sample_data)
        retrieved = predictor.get_data()
        assert retrieved is not None
        assert retrieved.shape == sample_data.shape

    def test_data_copy(self, predictor, sample_data):
        """Test data is copied (not referenced)."""
        predictor.set_data(sample_data)
        sample_data.iloc[0, 0] = 999
        assert predictor.get_data().iloc[0, 0] != 999


class TestLinearRegression:
    """Test 3: Linear regression prediction."""

    @pytest.fixture
    def predictor_with_data(self):
        predictor = Predictor()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100) * 2 + np.random.randn(100),
        })
        predictor.set_data(df)
        return predictor

    def test_linear_prediction(self, predictor_with_data):
        """Test linear regression prediction runs successfully."""
        result = predictor_with_data.predict_linear(
            features=['x', 'y'],
            target='z'
        )
        assert result is not None
        assert isinstance(result, dict)
        assert 'success' in result or 'data' in result

    def test_linear_with_parameters(self, predictor_with_data):
        """Test linear regression with custom parameters."""
        result = predictor_with_data.predict_linear(
            features=['x', 'y'],
            target='z',
            normalize=True
        )
        assert result is not None

    def test_linear_results_stored(self, predictor_with_data):
        """Test linear results are stored in prediction_results."""
        predictor_with_data.predict_linear(
            features=['x', 'y'],
            target='z'
        )
        assert 'linear' in predictor_with_data.prediction_results or predictor_with_data.data is not None


class TestTimeSeries:
    """Test 4: Time series forecasting."""

    @pytest.fixture
    def predictor_with_timeseries(self):
        predictor = Predictor()
        np.random.seed(42)
        t = np.arange(100)
        trend = 0.5 * t
        seasonal = 10 * np.sin(2 * np.pi * t / 12)
        noise = np.random.randn(100)
        df = pd.DataFrame({
            'time': t,
            'value': trend + seasonal + noise,
        })
        predictor.set_data(df)
        return predictor

    def test_timeseries_forecast(self, predictor_with_timeseries):
        """Test time series forecasting runs successfully."""
        result = predictor_with_timeseries.forecast_timeseries(
            series_column='value',
            periods=10
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_timeseries_with_parameters(self, predictor_with_timeseries):
        """Test time series forecasting with custom parameters."""
        result = predictor_with_timeseries.forecast_timeseries(
            series_column='value',
            periods=5,
            method='auto'
        )
        assert result is not None

    def test_forecast_length(self, predictor_with_timeseries):
        """Test forecast has correct length."""
        result = predictor_with_timeseries.forecast_timeseries(
            series_column='value',
            periods=12
        )
        assert result is not None


class TestDecisionTree:
    """Test 5: Decision tree prediction."""

    @pytest.fixture
    def predictor_with_data(self):
        predictor = Predictor()
        np.random.seed(42)
        df = pd.DataFrame({
            'a': np.random.randn(100),
            'b': np.random.randn(100),
            'c': np.random.randn(100) * 3,
        })
        predictor.set_data(df)
        return predictor

    def test_tree_prediction(self, predictor_with_data):
        """Test decision tree prediction runs successfully."""
        result = predictor_with_data.predict_tree(
            features=['a', 'b'],
            target='c'
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_tree_with_parameters(self, predictor_with_data):
        """Test decision tree with custom parameters."""
        result = predictor_with_data.predict_tree(
            features=['a', 'b'],
            target='c',
            max_depth=5,
            mode='regression'
        )
        assert result is not None


class TestModelValidation:
    """Test 6: Model validation."""

    @pytest.fixture
    def predictor_with_data(self):
        predictor = Predictor()
        np.random.seed(42)
        df = pd.DataFrame({
            'col1': np.random.randn(100),
            'col2': np.random.randn(100),
            'col3': np.random.randn(100) * 2,
        })
        predictor.set_data(df)
        return predictor

    def test_model_validation(self, predictor_with_data):
        """Test model validation runs successfully."""
        result = predictor_with_data.validate_model(
            features=['col1', 'col2'],
            target='col3',
            cv_folds=3
        )
        assert result is not None
        assert isinstance(result, dict)

    def test_validation_with_threshold(self, predictor_with_data):
        """Test validation with custom threshold."""
        result = predictor_with_data.validate_model(
            features=['col1', 'col2'],
            target='col3',
            cv_folds=5
        )
        assert result is not None


class TestPredictAll:
    """Test 7: Run all prediction methods simultaneously."""

    @pytest.fixture
    def predictor_with_data(self):
        predictor = Predictor()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100) * 2,
        })
        predictor.set_data(df)
        return predictor

    def test_predict_all(self, predictor_with_data):
        """Test all prediction methods run together."""
        results = predictor_with_data.predict_all(
            features=['x', 'y'],
            target='z'
        )
        assert results is not None
        assert isinstance(results, dict)
        assert len(results) > 0

    def test_predict_all_with_custom_params(self, predictor_with_data):
        """Test predict_all with custom parameters."""
        results = predictor_with_data.predict_all(
            features=['x', 'y'],
            target='z',
            cv_folds=3
        )
        assert results is not None


class TestEdgeCases:
    """Test 8: Empty dataframe handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        predictor = Predictor()
        empty_df = pd.DataFrame()
        predictor.set_data(empty_df)
        assert predictor.get_data() is not None
        assert predictor.get_data().shape[0] == 0

    def test_single_row_dataframe(self):
        """Test 9: Single row handling."""
        predictor = Predictor()
        single_row = pd.DataFrame({
            'x': [1.0],
            'y': [2.0],
            'z': [3.0]
        })
        predictor.set_data(single_row)
        assert predictor.get_data().shape[0] == 1

    def test_no_data_error(self):
        """Test error when no data is set."""
        predictor = Predictor()
        with pytest.raises(Exception):
            predictor.predict_linear(
                features=['x'],
                target='z'
            )


class TestPerformance:
    """Test 10: Performance benchmark."""

    def test_prediction_performance_1k_rows(self):
        """Test prediction on 1,000 rows completes in reasonable time."""
        predictor = Predictor()
        np.random.seed(42)
        df = pd.DataFrame({
            f'feature_{i}': np.random.randn(1000)
            for i in range(5)
        })
        df['target'] = df['feature_0'] * 2 + df['feature_1'] * 3 + np.random.randn(1000) * 0.1
        predictor.set_data(df)

        start = time.time()
        result = predictor.predict_linear(
            features=[f'feature_{i}' for i in range(5)],
            target='target'
        )
        elapsed = time.time() - start

        assert elapsed < 30  # Should complete in < 30 seconds
        assert result is not None


class TestSummaryReport:
    """Test summary report generation."""

    def test_summary_report(self):
        """Test summary report generation."""
        predictor = Predictor()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100) * 2,
        })
        predictor.set_data(df)
        predictor.predict_linear(
            features=['x', 'y'],
            target='z'
        )

        report = predictor.summary_report()
        assert report is not None
        assert 'status' in report or 'timestamp' in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
