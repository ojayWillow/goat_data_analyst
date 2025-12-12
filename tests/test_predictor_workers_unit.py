"""Comprehensive unit tests for Predictor Workers.

Test Coverage:
- LinearRegressionWorker (5 tests)
- DecisionTreeWorker (6 tests)
- TimeSeriesWorker (6 tests)
- ModelValidatorWorker (6 tests)
- Error scenarios (5 tests)

Total: 28 unit tests
"""

import pytest
import pandas as pd
import numpy as np
from agents.predictor.workers import (
    LinearRegression,
    DecisionTree,
    TimeSeries,
    ModelValidator,
    WorkerResult,
    ErrorType,
)
from tests.predictor_test_fixtures import PredictorTestData, PredictorTestUtils


# ===== LINEAR REGRESSION WORKER TESTS (5 tests) =====

class TestLinearRegressionWorker:
    """Test LinearRegressionWorker."""
    
    def setup_method(self):
        """Setup for each test."""
        self.worker = LinearRegression()
    
    def test_simple_linear_regression(self):
        """Test basic linear regression functionality."""
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target
        )
        
        assert result.success
        assert len(result.errors) == 0
        assert result.data['model_type'] == 'Linear Regression'
        assert 'r2_score' in result.data
        assert 'rmse' in result.data
        assert 'mae' in result.data
        assert 'coefficients' in result.data
        assert 'intercept' in result.data
        assert len(result.data['predictions']) == len(df)
        assert len(result.data['residuals']) == len(df)
        PredictorTestUtils.assert_quality_score_valid(result.quality_score)
    
    def test_multifeature_regression(self):
        """Test regression with multiple features."""
        df, features, target = PredictorTestData.multifeature_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target
        )
        
        assert result.success
        assert len(features) == 5
        assert len(result.data['coefficients']) == 5
        assert all(isinstance(v, float) for v in result.data['coefficients'].values())
    
    def test_invalid_input_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = PredictorTestData.empty_dataframe()
        
        result = self.worker.safe_execute(
            df=df,
            features=['x'],
            target='y'
        )
        
        assert not result.success
        assert len(result.errors) > 0
        assert any(e['type'] == 'missing_data' for e in result.errors)
    
    def test_invalid_input_missing_columns(self):
        """Test handling of missing required columns."""
        df, _, _ = PredictorTestData.simple_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=['nonexistent_column'],
            target='target'
        )
        
        assert not result.success
        assert any(e['type'] == 'invalid_column' for e in result.errors)
    
    def test_insufficient_data(self):
        """Test handling of insufficient data rows."""
        df, features, target = PredictorTestData.simple_regression_data()
        # Use more features than data rows
        df_small = df.head(1)  # Only 1 row, but 2 features
        
        result = self.worker.safe_execute(
            df=df_small,
            features=features,
            target=target
        )
        
        assert not result.success
        assert any(e['type'] == 'insufficient_data' for e in result.errors)


# ===== DECISION TREE WORKER TESTS (6 tests) =====

class TestDecisionTreeWorker:
    """Test DecisionTreeWorker."""
    
    def setup_method(self):
        """Setup for each test."""
        self.worker = DecisionTree()
    
    def test_regression_mode(self):
        """Test decision tree in regression mode."""
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            mode='regression'
        )
        
        assert result.success
        assert result.data['mode'] == 'regression'
        assert 'tree_depth' in result.data
        assert 'num_nodes' in result.data
        assert 'num_leaves' in result.data
        assert 'feature_importance' in result.data
        assert 'r2_score' in result.data
        assert 'rmse' in result.data
        assert 'mae' in result.data
    
    def test_classification_mode(self):
        """Test decision tree in classification mode."""
        df, features, target = PredictorTestData.binary_classification_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            mode='classification'
        )
        
        assert result.success
        assert result.data['mode'] == 'classification'
        assert 'accuracy' in result.data
        assert 0 <= result.data['accuracy'] <= 1
    
    def test_auto_mode_detection_regression(self):
        """Test auto mode detection for regression."""
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            mode='auto'
        )
        
        assert result.success
        assert result.data['mode'] == 'regression'  # Many unique continuous values
    
    def test_auto_mode_detection_classification(self):
        """Test auto mode detection for classification."""
        df, features, target = PredictorTestData.binary_classification_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            mode='auto'
        )
        
        assert result.success
        assert result.data['mode'] == 'classification'  # Few unique values
    
    def test_feature_importance_ranking(self):
        """Test that feature importance is properly ranked."""
        df, features, target = PredictorTestData.multifeature_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            mode='regression'
        )
        
        assert result.success
        importance_dict = result.data['feature_importance']
        # Check it's sorted (first importance >= second importance)
        importances = list(importance_dict.values())
        assert importances == sorted(importances, reverse=True)
    
    def test_max_depth_parameter(self):
        """Test max_depth parameter limits tree depth."""
        df, features, target = PredictorTestData.simple_regression_data()
        max_depth = 3
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            mode='regression',
            max_depth=max_depth
        )
        
        assert result.success
        assert result.data['tree_depth'] <= max_depth


# ===== TIME SERIES WORKER TESTS (6 tests) =====

class TestTimeSeriesWorker:
    """Test TimeSeriesWorker."""
    
    def setup_method(self):
        """Setup for each test."""
        self.worker = TimeSeries()
    
    def test_exponential_smoothing_forecast(self):
        """Test exponential smoothing forecasting."""
        df, time_col, value_col = PredictorTestData.timeseries_with_seasonality()
        
        result = self.worker.safe_execute(
            df=df,
            time_column=time_col,
            value_column=value_col,
            forecast_periods=6,
            method='exponential_smoothing'
        )
        
        assert result.success
        assert result.data['method'] == 'exponential_smoothing'
        assert len(result.data['forecast']) == 6
        assert 'mae' in result.data
        assert len(result.data['historical_values']) == len(df)
    
    def test_arima_forecast(self):
        """Test ARIMA forecasting."""
        df, time_col, value_col = PredictorTestData.long_timeseries_data()
        
        result = self.worker.safe_execute(
            df=df,
            time_column=time_col,
            value_column=value_col,
            forecast_periods=30,
            method='arima'
        )
        
        assert result.success
        assert result.data['method'] == 'arima'
        assert len(result.data['forecast']) == 30
        assert 'mae' in result.data
    
    def test_missing_time_column(self):
        """Test error handling for missing time column."""
        df, _, value_col = PredictorTestData.simple_timeseries_data()
        
        result = self.worker.safe_execute(
            df=df,
            time_column='nonexistent_time',
            value_column=value_col,
            forecast_periods=6,
            method='exponential_smoothing'
        )
        
        assert not result.success
        assert any(e['type'] == 'invalid_column' for e in result.errors)
    
    def test_missing_value_column(self):
        """Test error handling for missing value column."""
        df, time_col, _ = PredictorTestData.simple_timeseries_data()
        
        result = self.worker.safe_execute(
            df=df,
            time_column=time_col,
            value_column='nonexistent_value',
            forecast_periods=6,
            method='exponential_smoothing'
        )
        
        assert not result.success
        assert any(e['type'] == 'invalid_column' for e in result.errors)
    
    def test_insufficient_data_for_forecast(self):
        """Test error handling when insufficient historical data."""
        # Create very short time series (less than minimum required)
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=5),
            'value': [10, 11, 12, 13, 14]
        })
        
        result = self.worker.safe_execute(
            df=df,
            time_column='date',
            value_column='value',
            forecast_periods=6,
            method='exponential_smoothing'
        )
        
        assert not result.success
        assert any(e['type'] == 'insufficient_data' for e in result.errors)
    
    def test_forecast_periods_validation(self):
        """Test validation of forecast periods parameter."""
        df, time_col, value_col = PredictorTestData.timeseries_with_seasonality()
        
        result = self.worker.safe_execute(
            df=df,
            time_column=time_col,
            value_column=value_col,
            forecast_periods=0,  # Invalid
            method='exponential_smoothing'
        )
        
        assert not result.success
        assert any(e['type'] == 'invalid_parameter' for e in result.errors)


# ===== MODEL VALIDATOR WORKER TESTS (6 tests) =====

class TestModelValidatorWorker:
    """Test ModelValidatorWorker."""
    
    def setup_method(self):
        """Setup for each test."""
        self.worker = ModelValidator()
    
    def test_linear_regression_validation(self):
        """Test validation of linear regression model."""
        model = PredictorTestData.get_fitted_linear_model()
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            model=model,
            cv_folds=5
        )
        
        assert result.success
        assert 'cv_mean' in result.data
        assert 'cv_std' in result.data
        assert 'cv_scores' in result.data
        assert len(result.data['cv_scores']) == 5
        assert 0 <= result.data['cv_mean'] <= 1 or -1 <= result.data['cv_mean'] <= 1
    
    def test_tree_regressor_validation(self):
        """Test validation of decision tree regressor."""
        model = PredictorTestData.get_fitted_tree_regressor()
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            model=model,
            cv_folds=5
        )
        
        assert result.success
        assert 'cv_mean' in result.data
        PredictorTestUtils.assert_quality_score_valid(result.quality_score)
    
    def test_tree_classifier_validation(self):
        """Test validation of decision tree classifier."""
        model = PredictorTestData.get_fitted_tree_classifier()
        df, features, target = PredictorTestData.binary_classification_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            model=model,
            cv_folds=5
        )
        
        assert result.success
        assert 'primary_metric' in result.data
        assert result.data['primary_metric'] == 'accuracy'
    
    def test_overfitting_detection(self):
        """Test detection of overfitting."""
        model = PredictorTestData.get_fitted_tree_regressor()
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            model=model,
            cv_folds=5
        )
        
        assert result.success
        assert 'is_overfitted' in result.data
        assert isinstance(result.data['is_overfitted'], bool)
        assert 'validation_status' in result.data
    
    def test_cv_folds_validation(self):
        """Test validation of cv_folds parameter."""
        model = PredictorTestData.get_fitted_linear_model()
        df, features, target = PredictorTestData.simple_regression_data()
        
        # Invalid cv_folds (more than data points would fail, but we have 100 rows)
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            model=model,
            cv_folds=150  # More than data size
        )
        
        assert not result.success
        assert any(e['type'] == 'invalid_parameter' for e in result.errors)
    
    def test_no_model_provided(self):
        """Test error when no model provided."""
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = self.worker.safe_execute(
            df=df,
            features=features,
            target=target,
            model=None,
            cv_folds=5
        )
        
        assert not result.success
        assert any(e['type'] == 'invalid_parameter' for e in result.errors)


# ===== ERROR HANDLING TESTS (5 tests) =====

class TestWorkerErrorHandling:
    """Test error handling across all workers."""
    
    def test_worker_result_format(self):
        """Test WorkerResult has all required fields."""
        worker = LinearRegression()
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = worker.safe_execute(
            df=df,
            features=features,
            target=target
        )
        
        PredictorTestUtils.assert_worker_result_valid(result)
    
    def test_error_result_format(self):
        """Test error result has proper format."""
        worker = LinearRegression()
        
        result = worker.safe_execute(
            df=PredictorTestData.empty_dataframe(),
            features=['x'],
            target='y'
        )
        
        assert not result.success
        assert len(result.errors) > 0
        PredictorTestUtils.assert_worker_result_valid(result)
    
    def test_execution_time_tracked(self):
        """Test execution time is properly tracked."""
        worker = LinearRegression()
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = worker.safe_execute(
            df=df,
            features=features,
            target=target
        )
        
        assert result.execution_time_ms >= 0
        assert isinstance(result.execution_time_ms, float)
    
    def test_timestamp_recorded(self):
        """Test timestamp is recorded in result."""
        worker = LinearRegression()
        df, features, target = PredictorTestData.simple_regression_data()
        
        result = worker.safe_execute(
            df=df,
            features=features,
            target=target
        )
        
        assert result.timestamp != ""
        assert "T" in result.timestamp  # ISO format check
    
    def test_quality_score_range(self):
        """Test quality score is always in valid range."""
        workers = [LinearRegression(), DecisionTree()]
        df, features, target = PredictorTestData.simple_regression_data()
        
        for worker in workers:
            result = worker.safe_execute(
                df=df,
                features=features,
                target=target
            )
            
            PredictorTestUtils.assert_quality_score_valid(result.quality_score)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
