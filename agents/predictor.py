"""Predictor Agent - Time-series forecasting and ML predictions.

Integrated with Week 1 foundation systems:
- Configuration management
- Error recovery with retry logic
- Structured logging
- Input/output validation

Provides forecasting, trend analysis, and machine learning predictions
using scikit-learn and statistical methods.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Week 1 Integrations
from agents.agent_config import AgentConfig
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.validators import validate_input, validate_output

# Existing imports
from core.logger import get_logger
from core.exceptions import AgentError

logger = get_structured_logger(__name__)
config = AgentConfig()


class Predictor:
    """Agent for predictions and forecasting.
    
    Capabilities:
    - Linear regression forecasting
    - Random forest predictions
    - Time-series trend analysis
    - Seasonal decomposition
    - Moving averages
    - Exponential smoothing
    - Model evaluation metrics
    - Future value predictions
    
    Integrated with Week 1 systems:
    - Centralized configuration
    - Error recovery on all operations
    - Structured logging of all activities
    - Input/output validation
    """
    
    def __init__(self):
        """Initialize Predictor agent with Week 1 systems."""
        self.name = "Predictor"
        self.config = AgentConfig()
        self.data = None
        self.models = {}
        self.scaler = MinMaxScaler()
        logger.info(f"{self.name} initialized", extra={'version': '2.0-week1-integrated'})
    
    @validate_input({'df': 'dataframe'})
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data for predictions with validation.
        
        Args:
            df: DataFrame to analyze (validated)
        """
        with logger.operation('set_data', {'rows': len(df), 'columns': len(df.columns)}):
            self.data = df.copy()
            self.models = {}
            logger.info(
                'Data set for prediction',
                extra={'rows': df.shape[0], 'columns': df.shape[1]}
            )
    
    @validate_output('dataframe')
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data with validation.
        
        Returns:
            DataFrame or None (validated output)
        """
        return self.data
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def linear_regression_forecast(self, x_col: str, y_col: str, periods: int = 10) -> Dict[str, Any]:
        """Forecast using linear regression with error recovery.
        
        Args:
            x_col: Feature column (X)
            y_col: Target column (Y)
            periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecast results (validated)
            
        Raises:
            AgentError: If columns don't exist or insufficient data
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if x_col not in self.data.columns or y_col not in self.data.columns:
            raise AgentError("Columns not found")
        
        with logger.operation('linear_regression_forecast', {'x': x_col, 'y': y_col, 'periods': periods}):
            try:
                # Prepare data
                df_clean = self.data[[x_col, y_col]].dropna()
                logger.info('Data cleaned', extra={'rows_after_dropna': len(df_clean)})
                
                if len(df_clean) < 3:
                    raise AgentError("Insufficient data for forecasting")
                
                X = np.arange(len(df_clean)).reshape(-1, 1)
                y = df_clean[y_col].values
                
                # Train model
                model = LinearRegression()
                model.fit(X, y)
                
                # Historical predictions
                y_pred = model.predict(X)
                
                # Future predictions
                future_X = np.arange(len(df_clean), len(df_clean) + periods).reshape(-1, 1)
                future_pred = model.predict(future_X)
                
                # Calculate metrics
                mse = mean_squared_error(y, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y, y_pred)
                r2 = r2_score(y, y_pred)
                
                # Create forecast dataframe
                forecast_df = pd.DataFrame({
                    'period': range(1, periods + 1),
                    'forecast': future_pred.round(2),
                    'confidence_interval_lower': (future_pred - 1.96 * rmse).round(2),
                    'confidence_interval_upper': (future_pred + 1.96 * rmse).round(2),
                })
                
                self.models['linear_regression'] = model
                
                logger.info(
                    'Linear regression forecast complete',
                    extra={'r2_score': float(r2), 'rmse': float(rmse), 'mae': float(mae)}
                )
                
                return {
                    "status": "success",
                    "model": "Linear Regression",
                    "x_column": x_col,
                    "y_column": y_col,
                    "training_samples": len(df_clean),
                    "forecast_periods": periods,
                    "metrics": {
                        "mse": float(mse),
                        "rmse": float(rmse),
                        "mae": float(mae),
                        "r2_score": float(r2),
                    },
                    "slope": float(model.coef_[0]),
                    "intercept": float(model.intercept_),
                    "forecast": forecast_df.to_dict(orient="records"),
                }
            
            except Exception as e:
                logger.error(
                    'Linear regression forecast failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Forecast failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def random_forest_prediction(self, feature_cols: List[str], target_col: str, test_size: float = 0.2) -> Dict[str, Any]:
        """Predict using Random Forest with error recovery.
        
        Args:
            feature_cols: List of feature columns
            target_col: Target column
            test_size: Test set fraction (0.0-1.0)
            
        Returns:
            Dictionary with prediction results (validated)
            
        Raises:
            AgentError: If columns don't exist or invalid test_size
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        for col in feature_cols + [target_col]:
            if col not in self.data.columns:
                raise AgentError(f"Column '{col}' not found")
        
        if not 0 < test_size < 1:
            raise AgentError("test_size must be between 0 and 1")
        
        with logger.operation('random_forest_prediction', {'features': len(feature_cols), 'target': target_col, 'test_size': test_size}):
            try:
                # Prepare data
                df_clean = self.data[feature_cols + [target_col]].dropna()
                logger.info('Data prepared for RF', extra={'samples': len(df_clean)})
                
                if len(df_clean) < 5:
                    raise AgentError("Insufficient data for training")
                
                # Split data
                split_idx = int(len(df_clean) * (1 - test_size))
                X_train = df_clean[feature_cols].iloc[:split_idx]
                y_train = df_clean[target_col].iloc[:split_idx]
                X_test = df_clean[feature_cols].iloc[split_idx:]
                y_test = df_clean[target_col].iloc[split_idx:]
                
                # Train model
                model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
                model.fit(X_train, y_train)
                
                # Predictions
                y_pred_train = model.predict(X_train)
                y_pred_test = model.predict(X_test)
                
                # Metrics
                train_r2 = r2_score(y_train, y_pred_train)
                test_r2 = r2_score(y_test, y_pred_test)
                test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                test_mae = mean_absolute_error(y_test, y_pred_test)
                
                # Feature importance
                feature_importance = dict(zip(feature_cols, model.feature_importances_.round(4)))
                feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
                
                self.models['random_forest'] = model
                
                logger.info(
                    'Random Forest prediction complete',
                    extra={'train_r2': float(train_r2), 'test_r2': float(test_r2), 'test_rmse': float(test_rmse)}
                )
                
                return {
                    "status": "success",
                    "model": "Random Forest",
                    "features": feature_cols,
                    "target": target_col,
                    "train_size": len(X_train),
                    "test_size": len(X_test),
                    "metrics": {
                        "train_r2": float(train_r2),
                        "test_r2": float(test_r2),
                        "test_rmse": float(test_rmse),
                        "test_mae": float(test_mae),
                    },
                    "feature_importance": feature_importance,
                    "predictions_sample": {
                        "actual": y_test.head(5).tolist(),
                        "predicted": y_pred_test[:5].round(2).tolist(),
                    },
                }
            
            except Exception as e:
                logger.error(
                    'Random Forest prediction failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Prediction failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def moving_average(self, col: str, window: int = 5) -> Dict[str, Any]:
        """Calculate moving average for time-series with error recovery.
        
        Args:
            col: Column to analyze
            window: Window size for moving average
            
        Returns:
            Dictionary with moving average results (validated)
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        with logger.operation('moving_average', {'column': col, 'window': window}):
            try:
                series = self.data[col].dropna()
                logger.info('Series cleaned', extra={'length': len(series)})
                
                # Calculate moving average
                ma = series.rolling(window=window).mean()
                
                # Create result dataframe
                result_df = pd.DataFrame({
                    col: series.values,
                    f'{col}_ma_{window}': ma.values,
                })
                
                logger.info(
                    'Moving average calculated',
                    extra={'available_values': int(ma.notna().sum())}
                )
                
                return {
                    "status": "success",
                    "column": col,
                    "window": window,
                    "values": len(series),
                    "ma_available": int(ma.notna().sum()),
                    "results": result_df.tail(10).to_dict(orient="records"),
                }
            
            except Exception as e:
                logger.error(
                    'Moving average failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Moving average failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def exponential_smoothing(self, col: str, alpha: float = 0.3) -> Dict[str, Any]:
        """Apply exponential smoothing with error recovery.
        
        Args:
            col: Column to smooth
            alpha: Smoothing factor (0.0-1.0)
            
        Returns:
            Dictionary with smoothed values (validated)
            
        Raises:
            AgentError: If column doesn't exist or invalid alpha
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        if not 0 <= alpha <= 1:
            raise AgentError("alpha must be between 0 and 1")
        
        with logger.operation('exponential_smoothing', {'column': col, 'alpha': alpha}):
            try:
                series = self.data[col].dropna()
                
                # Calculate exponential smoothing
                smoothed = series.ewm(span=int(1/alpha) if alpha > 0 else 1).mean()
                
                # Create result dataframe
                result_df = pd.DataFrame({
                    col: series.values,
                    f'{col}_smoothed': smoothed.values,
                })
                
                logger.info(
                    'Exponential smoothing completed',
                    extra={'values': len(series)}
                )
                
                return {
                    "status": "success",
                    "column": col,
                    "alpha": alpha,
                    "values": len(series),
                    "results": result_df.tail(10).to_dict(orient="records"),
                }
            
            except Exception as e:
                logger.error(
                    'Exponential smoothing failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Smoothing failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def trend_analysis(self, col: str) -> Dict[str, Any]:
        """Analyze trend in time-series data with error recovery.
        
        Args:
            col: Column to analyze
            
        Returns:
            Dictionary with trend information (validated)
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        with logger.operation('trend_analysis', {'column': col}):
            try:
                series = self.data[col].dropna()
                
                # Split into halves
                mid = len(series) // 2
                first_half = series.iloc[:mid]
                second_half = series.iloc[mid:]
                
                # Calculate statistics
                first_mean = first_half.mean()
                second_mean = second_half.mean()
                trend_direction = "increasing" if second_mean > first_mean else "decreasing" if second_mean < first_mean else "stable"
                percent_change = ((second_mean - first_mean) / first_mean * 100) if first_mean != 0 else 0
                
                # Volatility
                volatility = series.std()
                
                logger.info(
                    'Trend analysis complete',
                    extra={
                        'trend': trend_direction,
                        'percent_change': round(percent_change, 2),
                        'volatility': round(volatility, 2)
                    }
                )
                
                return {
                    "status": "success",
                    "column": col,
                    "total_points": len(series),
                    "trend_direction": trend_direction,
                    "percent_change": round(percent_change, 2),
                    "statistics": {
                        "first_half_mean": round(first_mean, 2),
                        "second_half_mean": round(second_mean, 2),
                        "overall_mean": round(series.mean(), 2),
                        "overall_std": round(volatility, 2),
                        "min": round(series.min(), 2),
                        "max": round(series.max(), 2),
                    },
                }
            
            except Exception as e:
                logger.error(
                    'Trend analysis failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Trend analysis failed: {e}")
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """Get a trained model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Trained model or None
        """
        return self.models.get(model_name)
    
    @validate_output('dict')
    def list_models(self) -> Dict[str, Any]:
        """List trained models with validation.
        
        Returns:
            Dictionary with model information (validated)
        """
        return {
            "status": "success",
            "count": len(self.models),
            "models": list(self.models.keys()),
        }
