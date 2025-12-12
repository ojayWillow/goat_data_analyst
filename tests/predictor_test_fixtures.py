"""Test fixtures and utilities for Predictor Agent testing.

Provides:
- Sample DataFrames for various scenarios
- Time series data
- Classification/regression datasets
- Mock model objects
- Helper utilities
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from typing import Tuple


class PredictorTestData:
    """Generate test data for predictor workers."""
    
    # ===== REGRESSION DATA =====
    
    @staticmethod
    def simple_regression_data() -> Tuple[pd.DataFrame, list, str]:
        """Simple linear regression dataset.
        
        Returns:
            (DataFrame, features list, target column name)
        """
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n) * 10 + 50
        X2 = np.random.randn(n) * 5 + 20
        y = 2 * X1 + 3 * X2 + np.random.randn(n) * 5
        
        df = pd.DataFrame({
            'feature_1': X1,
            'feature_2': X2,
            'target': y
        })
        
        return df, ['feature_1', 'feature_2'], 'target'
    
    @staticmethod
    def multifeature_regression_data() -> Tuple[pd.DataFrame, list, str]:
        """Regression with multiple features.
        
        Returns:
            (DataFrame with 5 features, features list, target)
        """
        np.random.seed(42)
        n = 150
        data = {
            f'feature_{i}': np.random.randn(n) * 10 for i in range(1, 6)
        }
        # Create target with known relationship
        target = (2 * data['feature_1'] - 1.5 * data['feature_2'] + 
                 0.5 * data['feature_3'] + np.random.randn(n) * 2)
        data['target'] = target
        
        df = pd.DataFrame(data)
        features = [f'feature_{i}' for i in range(1, 6)]
        
        return df, features, 'target'
    
    @staticmethod
    def regression_with_nulls() -> Tuple[pd.DataFrame, list, str]:
        """Regression data with some null values.
        
        Returns:
            (DataFrame with NaNs, features, target)
        """
        df, features, target = PredictorTestData.simple_regression_data()
        # Add some nulls (10% of data)
        mask = np.random.random(len(df)) < 0.1
        df.loc[mask, features[0]] = np.nan
        return df, features, target
    
    @staticmethod
    def small_regression_data() -> Tuple[pd.DataFrame, list, str]:
        """Very small regression dataset (edge case).
        
        Returns:
            (Small DataFrame with 5 rows, features, target)
        """
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],
            'y': [5, 11, 17, 23, 29]
        })
        return df, ['x1', 'x2'], 'y'
    
    # ===== CLASSIFICATION DATA =====
    
    @staticmethod
    def binary_classification_data() -> Tuple[pd.DataFrame, list, str]:
        """Binary classification dataset.
        
        Returns:
            (DataFrame with binary target, features, target)
        """
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n) * 2 + 1
        X2 = np.random.randn(n) * 2 + 1
        # Simple decision boundary
        y = ((X1 + X2) > 2).astype(int)
        
        df = pd.DataFrame({
            'feature_1': X1,
            'feature_2': X2,
            'class': y
        })
        
        return df, ['feature_1', 'feature_2'], 'class'
    
    @staticmethod
    def multiclass_classification_data() -> Tuple[pd.DataFrame, list, str]:
        """Multiclass classification dataset.
        
        Returns:
            (DataFrame with 3 classes, features, target)
        """
        np.random.seed(42)
        n = 120
        X1 = np.random.randn(n) * 2
        X2 = np.random.randn(n) * 2
        # Create 3 classes
        y = np.where(X1 + X2 > 1, 2, np.where(X1 - X2 > 0, 1, 0))
        
        df = pd.DataFrame({
            'feature_1': X1,
            'feature_2': X2,
            'label': y
        })
        
        return df, ['feature_1', 'feature_2'], 'label'
    
    # ===== TIME SERIES DATA =====
    
    @staticmethod
    def simple_timeseries_data() -> Tuple[pd.DataFrame, str, str]:
        """Simple time series dataset.
        
        Returns:
            (DataFrame, time_column, value_column)
        """
        dates = pd.date_range('2023-01-01', periods=60, freq='D')
        # Linear trend with noise
        values = 100 + np.arange(60) * 0.5 + np.random.randn(60) * 2
        
        df = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        return df, 'date', 'value'
    
    @staticmethod
    def timeseries_with_seasonality() -> Tuple[pd.DataFrame, str, str]:
        """Time series with seasonal pattern.
        
        Returns:
            (DataFrame with 3 years monthly data, time_col, value_col)
        """
        dates = pd.date_range('2021-01-01', periods=36, freq='MS')
        # Trend + seasonality
        trend = np.arange(36) * 10
        seasonal = 30 * np.sin(np.arange(36) * 2 * np.pi / 12)
        noise = np.random.randn(36) * 5
        values = 1000 + trend + seasonal + noise
        
        df = pd.DataFrame({
            'timestamp': dates,
            'sales': values
        })
        
        return df, 'timestamp', 'sales'
    
    @staticmethod
    def long_timeseries_data() -> Tuple[pd.DataFrame, str, str]:
        """Longer time series for ARIMA.
        
        Returns:
            (DataFrame with 2 years daily data, time_col, value_col)
        """
        dates = pd.date_range('2022-01-01', periods=730, freq='D')
        # Complex pattern
        trend = np.arange(730) * 0.1
        seasonal = 50 * np.sin(np.arange(730) * 2 * np.pi / 365)
        noise = np.random.randn(730) * 3
        values = 500 + trend + seasonal + noise
        
        df = pd.DataFrame({
            'date': dates,
            'metric': values
        })
        
        return df, 'date', 'metric'
    
    # ===== EDGE CASES =====
    
    @staticmethod
    def empty_dataframe() -> pd.DataFrame:
        """Empty DataFrame."""
        return pd.DataFrame()
    
    @staticmethod
    def single_row_data() -> Tuple[pd.DataFrame, list, str]:
        """Single row DataFrame (edge case).
        
        Returns:
            (DataFrame with 1 row, features, target)
        """
        df = pd.DataFrame({
            'x': [1],
            'y': [2]
        })
        return df, ['x'], 'y'
    
    @staticmethod
    def all_nulls_data() -> Tuple[pd.DataFrame, list, str]:
        """DataFrame with all null values.
        
        Returns:
            (DataFrame all NaNs, features, target)
        """
        df = pd.DataFrame({
            'x1': [np.nan] * 10,
            'x2': [np.nan] * 10,
            'y': [np.nan] * 10
        })
        return df, ['x1', 'x2'], 'y'
    
    @staticmethod
    def constant_target_data() -> Tuple[pd.DataFrame, list, str]:
        """Data where target is constant (R² = 0 case).
        
        Returns:
            (DataFrame with constant target, features, target)
        """
        df = pd.DataFrame({
            'x1': np.random.randn(50),
            'x2': np.random.randn(50),
            'y': [5.0] * 50  # Constant!
        })
        return df, ['x1', 'x2'], 'y'
    
    @staticmethod
    def duplicate_rows_data() -> Tuple[pd.DataFrame, list, str]:
        """Data with duplicate rows.
        
        Returns:
            (DataFrame with duplicates, features, target)
        """
        base_df, features, target = PredictorTestData.simple_regression_data()
        # Add duplicates
        duplicates = base_df.iloc[:10].copy()
        df = pd.concat([base_df, duplicates], ignore_index=True)
        return df, features, target
    
    # ===== MOCK MODELS =====
    
    @staticmethod
    def get_fitted_linear_model() -> LinearRegression:
        """Get a pre-fitted linear regression model.
        
        Returns:
            Fitted LinearRegression model
        """
        df, features, target = PredictorTestData.simple_regression_data()
        X = df[features].values
        y = df[target].values
        
        model = LinearRegression()
        model.fit(X, y)
        return model
    
    @staticmethod
    def get_fitted_tree_regressor() -> DecisionTreeRegressor:
        """Get a pre-fitted tree regressor.
        
        Returns:
            Fitted DecisionTreeRegressor
        """
        df, features, target = PredictorTestData.simple_regression_data()
        X = df[features].values
        y = df[target].values
        
        model = DecisionTreeRegressor(max_depth=5, random_state=42)
        model.fit(X, y)
        return model
    
    @staticmethod
    def get_fitted_tree_classifier() -> DecisionTreeClassifier:
        """Get a pre-fitted tree classifier.
        
        Returns:
            Fitted DecisionTreeClassifier
        """
        df, features, target = PredictorTestData.binary_classification_data()
        X = df[features].values
        y = df[target].values
        
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        model.fit(X, y)
        return model


class PredictorTestUtils:
    """Utility functions for testing."""
    
    @staticmethod
    def assert_worker_result_valid(result) -> bool:
        """Check if WorkerResult has all required fields.
        
        Args:
            result: WorkerResult object
            
        Returns:
            True if valid
            
        Raises:
            AssertionError if invalid
        """
        required_fields = {
            'worker': str,
            'task_type': str,
            'success': bool,
            'data': dict,
            'errors': list,
            'warnings': list,
            'quality_score': (int, float),
            'metadata': dict,
            'timestamp': str,
            'execution_time_ms': (int, float),
        }
        
        for field, expected_type in required_fields.items():
            assert hasattr(result, field), f"Missing field: {field}"
            value = getattr(result, field)
            if isinstance(expected_type, tuple):
                assert isinstance(value, expected_type), \
                    f"{field} must be {expected_type}, got {type(value)}"
            else:
                assert isinstance(value, expected_type), \
                    f"{field} must be {expected_type}, got {type(value)}"
        
        return True
    
    @staticmethod
    def assert_quality_score_valid(score: float) -> bool:
        """Check if quality score is in valid range.
        
        Args:
            score: Quality score value
            
        Returns:
            True if valid
            
        Raises:
            AssertionError if invalid
        """
        assert isinstance(score, (int, float)), \
            f"Quality score must be numeric, got {type(score)}"
        assert 0.0 <= score <= 1.0, \
            f"Quality score must be 0-1, got {score}"
        return True
    
    @staticmethod
    def assert_regression_metrics_valid(metrics: dict) -> bool:
        """Check if regression metrics are valid.
        
        Args:
            metrics: Dict with r2_score, rmse, mae
            
        Returns:
            True if valid
        """
        assert 'r2_score' in metrics, "Missing r2_score"
        assert 'rmse' in metrics, "Missing rmse"
        assert 'mae' in metrics, "Missing mae"
        
        assert -1 <= metrics['r2_score'] <= 1, \
            f"R² must be -1 to 1, got {metrics['r2_score']}"
        assert metrics['rmse'] >= 0, \
            f"RMSE must be >= 0, got {metrics['rmse']}"
        assert metrics['mae'] >= 0, \
            f"MAE must be >= 0, got {metrics['mae']}"
        
        return True
    
    @staticmethod
    def compare_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        """Compare predicted vs actual values.
        
        Args:
            y_true: Actual values
            y_pred: Predicted values
            
        Returns:
            Dict with metrics
        """
        residuals = y_true - y_pred
        mse = np.mean(residuals ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(residuals))
        mape = np.mean(np.abs(residuals / y_true)) if np.all(y_true != 0) else np.inf
        
        return {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'mean_actual': float(np.mean(y_true)),
            'mean_predicted': float(np.mean(y_pred)),
        }
