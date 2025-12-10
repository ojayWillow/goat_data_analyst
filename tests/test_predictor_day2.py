"""Week 2 Day 2: Predictor Agent Integration Tests (10 tests).

Tests:
1. Agent initialization
2. Data loading
3. Linear regression prediction
4. Time series forecasting
5. Decision tree prediction
6. Model validation
7. Predict all methods (3 methods)
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
        assert predictor.data is None
        assert predictor.linear_regression_worker is not None
        assert predictor.decision_tree_worker is not None
        assert predictor.time_series_worker is not None
        assert predictor.model_validator_worker is not None


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

    def test_linear_multiple_features(self, predictor_with_data):
        """Test linear regression with multiple features."""
        result = predictor_with_data.predict_linear(
            features=['x', 'y'],
            target='z'
        )
        assert result is not None

    def test_linear_results_stored(self, predictor_with_data):
        """Test linear results are stored in prediction_results."""
        predictor_with_data.predict_linear(
            features=['x', 'y'],
            target='z'
        )
        assert 'linear_regression' in predictor_with_data.prediction_results


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

    def test_forecast_stored(self, predictor_with_timeseries):
        """Test forecast is stored in prediction_results."""
        predictor_with_timeseries.forecast_timeseries(
            series_column='value',
            periods=12
        )
        assert 'time_series' in predictor_with_timeseries.prediction_results


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

    def test_tree_with_max_depth(self, predictor_with_data):
        """Test decision tree with max_depth constraint."""
        result = predictor_with_data.predict_tree(
            features=['a', 'b'],
            target='c',
            max_depth=5,
            mode='regression'
        )
        assert result is not None

    def test_tree_results_stored(self, predictor_with_data):
        """Test tree results are stored."""
        predictor_with_data.predict_tree(
            features=['a', 'b'],
            target='c'
        )
        assert 'decision_tree' in predictor_with_data.prediction_results


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

    def test_validation_linear_model(self, predictor_with_data):
        """Test validation with linear model."""
        result = predictor_with_data.validate_model(
            features=['col1', 'col2'],
            target='col3',
            model_type='linear',
            cv_folds=3
        )
        assert result is not None

    def test_validation_stored(self, predictor_with_data):
        """Test validation results are stored."""
        predictor_with_data.validate_model(
            features=['col1', 'col2'],
            target='col3',
            cv_folds=3
        )
        assert 'validation' in predictor_with_data.prediction_results


class TestMultiplePredictions:
    """Test 7: Run multiple prediction methods simultaneously."""

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

    def test_run_all_three_methods(self, predictor_with_data):
        """Test all three prediction methods run sequentially."""
        # Linear
        result1 = predictor_with_data.predict_linear(
            features=['x', 'y'],
            target='z'
        )
        assert result1 is not None
        
        # Tree
        result2 = predictor_with_data.predict_tree(
            features=['x', 'y'],
            target='z'
        )
        assert result2 is not None
        
        # Time series
        df = predictor_with_data.get_data()
        df_ts = pd.DataFrame({
            'time': range(len(df)),
            'value': df['z'].values
        })
        predictor_with_data.set_data(df_ts)
        result3 = predictor_with_data.forecast_timeseries(
            series_column='value',
            periods=10
        )
        assert result3 is not None
        
        # Verify all stored
        assert len(predictor_with_data.prediction_results) >= 2

    def test_validation_with_predictions(self, predictor_with_data):
        """Test validation after predictions."""
        predictor_with_data.predict_linear(
            features=['x', 'y'],
            target='z'
        )
        
        result = predictor_with_data.validate_model(
            features=['x', 'y'],
            target='z',
            cv_folds=3
        )
        assert result is not None
        assert len(predictor_with_data.prediction_results) == 2


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
        assert 'status' in report
        assert 'total_predictions' in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
