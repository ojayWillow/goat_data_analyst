"""Test suite for Predictor Agent and all workers."""

import pytest
import pandas as pd
import numpy as np
from typing import List

from agents.predictor import Predictor
from agents.predictor.workers import (
    LinearRegressionWorker,
    DecisionTreeWorker,
    TimeSeriesWorker,
    ModelValidatorWorker,
    ErrorType,
)


# ===== FIXTURES =====

@pytest.fixture
def sample_regression_data():
    """Create sample regression dataset."""
    np.random.seed(42)
    n_samples = 100
    X1 = np.random.randn(n_samples)
    X2 = np.random.randn(n_samples)
    y = 2 * X1 + 3 * X2 + np.random.randn(n_samples) * 0.1
    
    df = pd.DataFrame({
        'feature1': X1,
        'feature2': X2,
        'target': y,
    })
    return df


@pytest.fixture
def sample_classification_data():
    """Create sample classification dataset."""
    np.random.seed(42)
    n_samples = 100
    X1 = np.random.randn(n_samples)
    X2 = np.random.randn(n_samples)
    y = ((X1 + X2) > 0).astype(int)
    
    df = pd.DataFrame({
        'feature1': X1,
        'feature2': X2,
        'target': y,
    })
    return df


@pytest.fixture
def sample_timeseries_data():
    """Create sample time series dataset."""
    np.random.seed(42)
    n_samples = 60
    t = np.arange(n_samples)
    trend = 0.5 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 12)
    noise = np.random.randn(n_samples)
    series = trend + seasonal + noise
    
    df = pd.DataFrame({
        'time': t,
        'value': series,
    })
    return df


@pytest.fixture
def predictor(sample_regression_data):
    """Create Predictor instance with data."""
    pred = Predictor()
    pred.set_data(sample_regression_data)
    return pred


# ===== LINEAR REGRESSION WORKER TESTS =====

class TestLinearRegressionWorker:
    """Test suite for LinearRegressionWorker."""
    
    def test_worker_initialization(self):
        """Test worker initializes correctly."""
        worker = LinearRegressionWorker()
        assert worker.name == "LinearRegressionWorker"
        assert worker.model is None
    
    def test_fit_simple_regression(self, sample_regression_data):
        """Test fitting on simple regression data."""
        worker = LinearRegressionWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['feature1', 'feature2'],
            target='target',
        )
        
        assert result.success
        assert result.worker == "LinearRegressionWorker"
        assert 'r2_score' in result.data
        assert 'coefficients' in result.data
        assert 'predictions' in result.data
        assert 'residuals' in result.data
    
    def test_r2_score_reasonable(self, sample_regression_data):
        """Test that R2 score is reasonable."""
        worker = LinearRegressionWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['feature1', 'feature2'],
            target='target',
        )
        
        assert 0 <= result.data['r2_score'] <= 1
    
    def test_coefficients_shape(self, sample_regression_data):
        """Test coefficients have correct shape."""
        worker = LinearRegressionWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['feature1', 'feature2'],
            target='target',
        )
        
        assert len(result.data['coefficients']) == 2
        assert 'feature1' in result.data['coefficients']
        assert 'feature2' in result.data['coefficients']
    
    def test_error_missing_data(self):
        """Test error handling with missing data."""
        worker = LinearRegressionWorker()
        result = worker.execute(
            df=None,
            features=['feature1', 'feature2'],
            target='target',
        )
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_error_missing_column(self, sample_regression_data):
        """Test error handling with missing column."""
        worker = LinearRegressionWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['missing_feature'],
            target='target',
        )
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_error_no_features(self, sample_regression_data):
        """Test error handling with no features."""
        worker = LinearRegressionWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=[],
            target='target',
        )
        
        assert not result.success
    
    def test_predictions_shape(self, sample_regression_data):
        """Test predictions have correct shape."""
        worker = LinearRegressionWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['feature1', 'feature2'],
            target='target',
        )
        
        assert len(result.data['predictions']) == len(sample_regression_data)


# ===== DECISION TREE WORKER TESTS =====

class TestDecisionTreeWorker:
    """Test suite for DecisionTreeWorker."""
    
    def test_worker_initialization(self):
        """Test worker initializes correctly."""
        worker = DecisionTreeWorker()
        assert worker.name == "DecisionTreeWorker"
        assert worker.model is None
    
    def test_fit_regression(self, sample_regression_data):
        """Test fitting on regression data."""
        worker = DecisionTreeWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['feature1', 'feature2'],
            target='target',
            mode='regression',
        )
        
        assert result.success
        assert result.data['mode'] == 'regression'
        assert 'feature_importance' in result.data
        assert 'tree_depth' in result.data
    
    def test_fit_classification(self, sample_classification_data):
        """Test fitting on classification data."""
        worker = DecisionTreeWorker()
        result = worker.execute(
            df=sample_classification_data,
            features=['feature1', 'feature2'],
            target='target',
            mode='classification',
        )
        
        assert result.success
        assert result.data['mode'] == 'classification'
        assert 'accuracy' in result.data
    
    def test_feature_importance(self, sample_regression_data):
        """Test feature importance extraction."""
        worker = DecisionTreeWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['feature1', 'feature2'],
            target='target',
        )
        
        assert 'feature_importance' in result.data
        importances = result.data['feature_importance']
        assert len(importances) == 2
        assert all(0 <= v <= 1 for v in importances.values())
    
    def test_tree_depth_positive(self, sample_regression_data):
        """Test tree depth is positive."""
        worker = DecisionTreeWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['feature1', 'feature2'],
            target='target',
        )
        
        assert result.data['tree_depth'] > 0
        assert result.data['num_leaves'] > 0
    
    def test_max_depth_constraint(self, sample_regression_data):
        """Test max_depth constraint is respected."""
        worker = DecisionTreeWorker()
        result = worker.execute(
            df=sample_regression_data,
            features=['feature1', 'feature2'],
            target='target',
            max_depth=2,
        )
        
        assert result.success
        assert result.data['tree_depth'] <= 2
    
    def test_error_insufficient_data(self):
        """Test error with insufficient data."""
        worker = DecisionTreeWorker()
        df = pd.DataFrame({'x': [1, 2], 'y': [1, 2]})
        result = worker.execute(
            df=df,
            features=['x'],
            target='y',
        )
        
        assert not result.success


# ===== TIME SERIES WORKER TESTS =====

class TestTimeSeriesWorker:
    """Test suite for TimeSeriesWorker."""
    
    def test_worker_initialization(self):
        """Test worker initializes correctly."""
        worker = TimeSeriesWorker()
        assert worker.name == "TimeSeriesWorker"
    
    def test_forecast_with_series(self, sample_timeseries_data):
        """Test forecasting with time series data."""
        worker = TimeSeriesWorker()
        result = worker.execute(
            series=sample_timeseries_data['value'],
            periods=12,
            method='auto',
        )
        
        assert result.success
        assert 'forecast_data' in result.data
        assert len(result.data['forecast_data']['forecast']) == 12
    
    def test_forecast_with_list(self):
        """Test forecasting with list data."""
        worker = TimeSeriesWorker()
        series_list = [1.0, 2.0, 1.5, 3.0, 2.5, 4.0, 3.5, 5.0]
        result = worker.execute(
            series=series_list,
            periods=4,
        )
        
        assert result.success
        assert len(result.data['forecast_data']['forecast']) == 4
    
    def test_confidence_intervals(self, sample_timeseries_data):
        """Test confidence intervals are generated."""
        worker = TimeSeriesWorker()
        result = worker.execute(
            series=sample_timeseries_data['value'],
            periods=10,
            method='arima',
        )
        
        if result.success and 'confidence_interval_lower' in result.data['forecast_data']:
            assert len(result.data['forecast_data']['confidence_interval_lower']) == 10
            assert len(result.data['forecast_data']['confidence_interval_upper']) == 10
    
    def test_decomposition(self, sample_timeseries_data):
        """Test time series decomposition."""
        worker = TimeSeriesWorker()
        result = worker.execute(
            series=sample_timeseries_data['value'],
            periods=12,
            decompose=True,
        )
        
        if result.success and result.data['decomposition']:
            assert 'trend' in result.data['decomposition']
            assert 'seasonal' in result.data['decomposition']
            assert 'residual' in result.data['decomposition']
    
    def test_error_no_series(self):
        """Test error with no series."""
        worker = TimeSeriesWorker()
        result = worker.execute(
            series=None,
            periods=5,
        )
        
        assert not result.success
    
    def test_error_insufficient_data(self):
        """Test error with insufficient data."""
        worker = TimeSeriesWorker()
        result = worker.execute(
            series=[1.0, 2.0],
            periods=5,
        )
        
        assert not result.success


# ===== MODEL VALIDATOR WORKER TESTS =====

class TestModelValidatorWorker:
    """Test suite for ModelValidatorWorker."""
    
    def test_worker_initialization(self):
        """Test worker initializes correctly."""
        worker = ModelValidatorWorker()
        assert worker.name == "ModelValidatorWorker"
    
    def test_linear_validation(self, sample_regression_data):
        """Test linear model validation."""
        worker = ModelValidatorWorker()
        X = sample_regression_data[['feature1', 'feature2']].values
        y = sample_regression_data['target'].values
        
        result = worker.execute(
            X=X,
            y=y,
            model_type='linear',
            cv_folds=5,
        )
        
        assert result.success
        assert 'cross_validation' in result.data
        assert 'overall_metrics' in result.data
    
    def test_tree_validation(self, sample_regression_data):
        """Test tree model validation."""
        worker = ModelValidatorWorker()
        X = sample_regression_data[['feature1', 'feature2']].values
        y = sample_regression_data['target'].values
        
        result = worker.execute(
            X=X,
            y=y,
            model_type='tree',
            cv_folds=5,
        )
        
        assert result.success
        assert result.data['model_type'] == 'tree'
    
    def test_cv_scores_generated(self, sample_regression_data):
        """Test cross-validation scores are generated."""
        worker = ModelValidatorWorker()
        X = sample_regression_data[['feature1', 'feature2']].values
        y = sample_regression_data['target'].values
        
        result = worker.execute(
            X=X,
            y=y,
            cv_folds=5,
        )
        
        assert len(result.data['cross_validation']['r2_scores']) == 5
    
    def test_residual_analysis(self, sample_regression_data):
        """Test residual analysis."""
        worker = ModelValidatorWorker()
        X = sample_regression_data[['feature1', 'feature2']].values
        y = sample_regression_data['target'].values
        
        result = worker.execute(
            X=X,
            y=y,
        )
        
        assert 'residual_analysis' in result.data
        residual_data = result.data['residual_analysis']
        assert 'mean' in residual_data
        assert 'std' in residual_data
        assert 'skewness' in residual_data
    
    def test_error_missing_data(self):
        """Test error with missing data."""
        worker = ModelValidatorWorker()
        result = worker.execute(
            X=None,
            y=None,
        )
        
        assert not result.success


# ===== PREDICTOR AGENT TESTS =====

class TestPredictorAgent:
    """Test suite for Predictor Agent."""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        pred = Predictor()
        assert pred.name == "Predictor"
        assert pred.data is None
    
    def test_set_data(self, sample_regression_data):
        """Test setting data."""
        pred = Predictor()
        pred.set_data(sample_regression_data)
        
        assert pred.data is not None
        assert len(pred.data) == len(sample_regression_data)
    
    def test_get_data(self, sample_regression_data, predictor):
        """Test retrieving data."""
        retrieved_data = predictor.get_data()
        
        assert retrieved_data is not None
        assert len(retrieved_data) == len(sample_regression_data)
    
    def test_predict_linear(self, predictor):
        """Test linear prediction through agent."""
        result = predictor.predict_linear(
            features=['feature1', 'feature2'],
            target='target',
        )
        
        assert result['success']
        assert 'r2_score' in result['data']
    
    def test_predict_tree(self, predictor):
        """Test tree prediction through agent."""
        result = predictor.predict_tree(
            features=['feature1', 'feature2'],
            target='target',
            mode='regression',
        )
        
        assert result['success']
        assert 'feature_importance' in result['data']
    
    def test_forecast_timeseries(self, sample_timeseries_data):
        """Test time series forecasting through agent."""
        pred = Predictor()
        pred.set_data(sample_timeseries_data)
        
        result = pred.forecast_timeseries(
            series_column='value',
            periods=10,
        )
        
        assert result['success']
        assert len(result['data']['forecast_data']['forecast']) == 10
    
    def test_validate_model(self, predictor):
        """Test model validation through agent."""
        result = predictor.validate_model(
            features=['feature1', 'feature2'],
            target='target',
            model_type='linear',
            cv_folds=3,
        )
        
        assert result['success']
        assert 'cross_validation' in result['data']
    
    def test_no_data_error(self):
        """Test error when no data is set."""
        pred = Predictor()
        result = pred.predict_linear(
            features=['feature1'],
            target='target',
        )
        
        assert not result['success']
    
    def test_summary_report(self, predictor):
        """Test summary report generation."""
        predictor.predict_linear(
            features=['feature1', 'feature2'],
            target='target',
        )
        
        summary = predictor.summary_report()
        
        assert 'total_predictions' in summary
        assert 'successful' in summary
        assert summary['total_predictions'] >= 1
    
    def test_integration_full_pipeline(self, sample_regression_data):
        """Test full prediction pipeline."""
        pred = Predictor()
        pred.set_data(sample_regression_data)
        
        # Linear regression
        result1 = pred.predict_linear(
            features=['feature1', 'feature2'],
            target='target',
        )
        assert result1['success']
        
        # Tree prediction
        result2 = pred.predict_tree(
            features=['feature1', 'feature2'],
            target='target',
        )
        assert result2['success']
        
        # Model validation
        result3 = pred.validate_model(
            features=['feature1', 'feature2'],
            target='target',
        )
        assert result3['success']
        
        # Summary
        summary = pred.summary_report()
        assert summary['total_predictions'] == 3
        assert summary['successful'] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
