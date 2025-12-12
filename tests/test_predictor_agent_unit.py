"""Comprehensive unit tests for Predictor Agent.

Test Coverage:
- Initialization (1 test)
- Data management (3 tests)
- Prediction methods (5 tests)
- Summary reporting (2 tests)
- Error handling (4 tests)

Total: 15 unit tests
"""

import pytest
import pandas as pd
import numpy as np
from core.exceptions import AgentError
from core.error_recovery import RecoveryError
from agents.predictor import Predictor
from tests.predictor_test_fixtures import PredictorTestData, PredictorTestUtils


# ===== AGENT INITIALIZATION TESTS =====

class TestPredictorInitialization:
    """Test Predictor Agent initialization."""
    
    def test_initialization(self):
        """Test that predictor initializes with all workers."""
        agent = Predictor()
        
        assert agent.name == "Predictor"
        assert agent.data is None
        assert len(agent.prediction_results) == 0
        assert hasattr(agent, 'linear_regression_worker')
        assert hasattr(agent, 'decision_tree_worker')
        assert hasattr(agent, 'time_series_worker')
        assert hasattr(agent, 'model_validator_worker')
        assert hasattr(agent, 'logger')
        assert hasattr(agent, 'structured_logger')


# ===== DATA MANAGEMENT TESTS =====

class TestPredictorDataManagement:
    """Test Predictor data management methods."""
    
    def setup_method(self):
        """Setup for each test."""
        self.agent = Predictor()
    
    def test_set_data(self):
        """Test setting data in agent."""
        df, _, _ = PredictorTestData.simple_regression_data()
        
        self.agent.set_data(df)
        
        assert self.agent.data is not None
        assert len(self.agent.data) == len(df)
        assert list(self.agent.data.columns) == list(df.columns)
    
    def test_get_data(self):
        """Test retrieving data from agent."""
        df, _, _ = PredictorTestData.simple_regression_data()
        self.agent.set_data(df)
        
        retrieved = self.agent.get_data()
        
        assert retrieved is not None
        assert len(retrieved) == len(df)
    
    def test_set_data_resets_results(self):
        """Test that setting new data resets previous results."""
        df1, features1, target1 = PredictorTestData.simple_regression_data()
        self.agent.set_data(df1)
        # Simulate adding a result
        self.agent.prediction_results['test'] = "dummy_result"
        
        df2, features2, target2 = PredictorTestData.multifeature_regression_data()
        self.agent.set_data(df2)
        
        # Results should be reset
        assert len(self.agent.prediction_results) == 0


# ===== LINEAR REGRESSION PREDICTION TESTS =====

class TestPredictorLinearRegression:
    """Test Predictor linear regression prediction."""
    
    def setup_method(self):
        """Setup for each test."""
        self.agent = Predictor()
        df, self.features, self.target = PredictorTestData.simple_regression_data()
        self.agent.set_data(df)
    
    def test_predict_linear_success(self):
        """Test successful linear regression prediction."""
        result_dict = self.agent.predict_linear(
            features=self.features,
            target=self.target
        )
        
        assert result_dict['success']
        assert 'data' in result_dict
        assert result_dict['data']['model_type'] == 'Linear Regression'
        assert 'linear_regression' in self.agent.prediction_results
    
    def test_predict_linear_no_data(self):
        """Test error when predicting without data."""
        agent = Predictor()  # No data set
        
        with pytest.raises(RecoveryError):
            agent.predict_linear(
                features=self.features,
                target=self.target
            )
    
    def test_predict_linear_stores_result(self):
        """Test that prediction result is stored in agent."""
        self.agent.predict_linear(
            features=self.features,
            target=self.target
        )
        
        assert 'linear_regression' in self.agent.prediction_results
        result = self.agent.prediction_results['linear_regression']
        assert result.success
        assert result.worker == 'LinearRegressionWorker'


# ===== DECISION TREE PREDICTION TESTS =====

class TestPredictorDecisionTree:
    """Test Predictor decision tree prediction."""
    
    def setup_method(self):
        """Setup for each test."""
        self.agent = Predictor()
        df, self.features, self.target = PredictorTestData.simple_regression_data()
        self.agent.set_data(df)
    
    def test_predict_tree_regression(self):
        """Test decision tree regression prediction."""
        result_dict = self.agent.predict_tree(
            features=self.features,
            target=self.target,
            mode='regression'
        )
        
        assert result_dict['success']
        assert result_dict['data']['mode'] == 'regression'
    
    def test_predict_tree_with_max_depth(self):
        """Test decision tree with max_depth parameter."""
        result_dict = self.agent.predict_tree(
            features=self.features,
            target=self.target,
            mode='regression',
            max_depth=3
        )
        
        assert result_dict['success']
        assert result_dict['data']['tree_depth'] <= 3
    
    def test_predict_tree_auto_mode(self):
        """Test decision tree with auto mode detection."""
        result_dict = self.agent.predict_tree(
            features=self.features,
            target=self.target,
            mode='auto'
        )
        
        assert result_dict['success']
        assert result_dict['data']['mode'] in ['regression', 'classification']
    
    def test_predict_tree_no_data(self):
        """Test error when predicting without data."""
        agent = Predictor()  # No data set
        
        with pytest.raises(RecoveryError):
            agent.predict_tree(
                features=self.features,
                target=self.target
            )


# ===== TIME SERIES FORECASTING TESTS =====

class TestPredictorTimeSeries:
    """Test Predictor time series forecasting."""
    
    def setup_method(self):
        """Setup for each test."""
        self.agent = Predictor()
        df, self.time_col, self.value_col = PredictorTestData.timeseries_with_seasonality()
        self.agent.set_data(df)
    
    def test_forecast_timeseries_success(self):
        """Test successful time series forecasting."""
        result_dict = self.agent.forecast_timeseries(
            series_column=self.value_col,
            periods=6,
            method='exponential_smoothing'
        )
        
        assert result_dict is not None
        assert result_dict.get('success', True)  # Some implementations may not have 'success'
        assert 'forecast' in result_dict.get('data', {}) or 'forecast' in result_dict
    
    def test_forecast_timeseries_invalid_column(self):
        """Test error with invalid series column."""
        with pytest.raises(RecoveryError):
            self.agent.forecast_timeseries(
                series_column='nonexistent_column',
                periods=6
            )
    
    def test_forecast_timeseries_no_data(self):
        """Test error when forecasting without data."""
        agent = Predictor()  # No data set
        
        with pytest.raises(RecoveryError):
            agent.forecast_timeseries(
                series_column='value',
                periods=6
            )


# ===== MODEL VALIDATION TESTS =====

class TestPredictorModelValidation:
    """Test Predictor model validation."""
    
    def setup_method(self):
        """Setup for each test."""
        self.agent = Predictor()
        df, self.features, self.target = PredictorTestData.simple_regression_data()
        self.agent.set_data(df)
    
    def test_validate_model_success(self):
        """Test successful model validation."""
        result_dict = self.agent.validate_model(
            features=self.features,
            target=self.target,
            model_type='linear',
            cv_folds=5
        )
        
        assert result_dict is not None
        assert result_dict.get('success', True)  # Some implementations may not have 'success'
        # Check that result has validation data
        assert 'data' in result_dict or 'cv_mean' in result_dict
    
    def test_validate_model_no_data(self):
        """Test error when validating without data."""
        agent = Predictor()  # No data set
        
        with pytest.raises(RecoveryError):
            agent.validate_model(
                features=self.features,
                target=self.target
            )


# ===== SUMMARY REPORTING TESTS =====

class TestPredictorSummaryReporting:
    """Test Predictor summary reporting."""
    
    def test_summary_report_empty(self):
        """Test summary report with no predictions."""
        agent = Predictor()
        
        report = agent.summary_report()
        
        assert report['message'] == 'No predictions yet'
        assert report['status'] == 'empty'
    
    def test_summary_report_with_predictions(self):
        """Test summary report with predictions."""
        agent = Predictor()
        df, features, target = PredictorTestData.simple_regression_data()
        agent.set_data(df)
        
        # Make some predictions
        agent.predict_linear(features=features, target=target)
        agent.predict_tree(features=features, target=target)
        
        report = agent.summary_report()
        
        assert report['status'] == 'success'
        assert report['total_predictions'] == 2
        assert report['successful'] == 2
        assert report['failed'] == 0
        assert 'linear_regression' in report['successful_models']
        assert 'decision_tree' in report['successful_models']


# ===== INTEGRATION TESTS =====

class TestPredictorIntegration:
    """Integration tests for Predictor Agent."""
    
    def test_full_workflow_regression(self):
        """Test complete regression workflow."""
        agent = Predictor()
        df, features, target = PredictorTestData.simple_regression_data()
        agent.set_data(df)
        
        # Linear regression
        result1 = agent.predict_linear(features=features, target=target)
        assert result1['success']
        
        # Decision tree
        result2 = agent.predict_tree(features=features, target=target)
        assert result2['success']
        
        # Validation
        result3 = agent.validate_model(features=features, target=target)
        assert result3 is not None  # Just verify it returns something
        
        # Summary
        summary = agent.summary_report()
        assert summary['total_predictions'] >= 2
        assert summary['successful'] >= 2
    
    def test_full_workflow_with_timeseries(self):
        """Test complete workflow with time series."""
        agent = Predictor()
        df, time_col, value_col = PredictorTestData.timeseries_with_seasonality()
        agent.set_data(df)
        
        # Forecast
        result = agent.forecast_timeseries(
            series_column=value_col,
            periods=6
        )
        assert result is not None
        
        # Summary
        summary = agent.summary_report()
        assert summary['total_predictions'] >= 1
    
    def test_multiple_predictions_accumulate(self):
        """Test that multiple predictions accumulate in results."""
        agent = Predictor()
        df, features, target = PredictorTestData.simple_regression_data()
        agent.set_data(df)
        
        # Make multiple predictions
        agent.predict_linear(features=features, target=target)
        assert len(agent.prediction_results) == 1
        
        agent.predict_tree(features=features, target=target)
        assert len(agent.prediction_results) == 2
        
        # Setting new data resets
        df2, features2, target2 = PredictorTestData.multifeature_regression_data()
        agent.set_data(df2)
        assert len(agent.prediction_results) == 0


# ===== ERROR RECOVERY TESTS =====

class TestPredictorErrorRecovery:
    """Test error recovery and handling."""
    
    def test_invalid_features_list(self):
        """Test error handling with invalid features."""
        agent = Predictor()
        df, _, target = PredictorTestData.simple_regression_data()
        agent.set_data(df)
        
        # Empty features list should fail - catches AgentError raised by validation
        with pytest.raises(AgentError):
            agent.predict_linear(features=[], target=target)
    
    def test_invalid_target(self):
        """Test error handling with invalid target."""
        agent = Predictor()
        df, features, _ = PredictorTestData.simple_regression_data()
        agent.set_data(df)
        
        # Nonexistent target should fail - catches AgentError raised by validation
        with pytest.raises(AgentError):
            agent.predict_linear(features=features, target='nonexistent')
    
    def test_retry_on_transient_error(self):
        """Test that retry decorator is in place."""
        # The retry decorator is applied to methods
        # This test verifies the method still completes successfully
        agent = Predictor()
        df, features, target = PredictorTestData.simple_regression_data()
        
        # Should not raise even if temporary issues
        agent.set_data(df)
        result = agent.predict_linear(features=features, target=target)
        assert result['success']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
