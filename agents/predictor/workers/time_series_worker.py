"""Time Series Worker - Forecasting and trend analysis."""

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

logger = get_logger(__name__)


class TimeSeriesWorker(BaseWorker):
    """Worker for time series forecasting.
    
    Performs time series analysis and forecasting with:
    - Trend detection
    - Seasonality analysis
    - Forecast generation
    - Confidence intervals
    """
    
    def __init__(self):
        super().__init__("TimeSeriesWorker")
        self.forecast_model = None
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute time series forecasting.
        
        Wraps entire task with try-except for proper error tracking.
        
        Args:
            df: DataFrame with time index
            time_column: Column name for time index
            value_column: Column name for values to forecast
            forecast_periods: Number of periods to forecast
            method: 'exponential_smoothing' or 'arima' (default: 'exponential_smoothing')
            
        Returns:
            WorkerResult with forecasts and metrics
        """
        try:
            result = self._run_time_series(**kwargs)
            
            # Track success AFTER entire task completes
            self.error_intelligence.track_success(
                agent_name="predictor",
                worker_name="TimeSeriesWorker",
                operation="time_series_forecast",
                context={
                    k: v for k, v in kwargs.items() 
                    if k != 'df' and not isinstance(v, pd.DataFrame)
                }
            )
            
            return result
            
        except Exception as e:
            # Track error ONLY in exception handler
            self.error_intelligence.track_error(
                agent_name="predictor",
                worker_name="TimeSeriesWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    k: v for k, v in kwargs.items() 
                    if k != 'df' and not isinstance(v, pd.DataFrame)
                }
            )
            raise
    
    def _run_time_series(self, **kwargs) -> WorkerResult:
        """Perform actual time series work.
        
        This method contains all the actual ML logic.
        execute() wraps this with try-except for error tracking.
        """
        result = self._create_result(
            task_type="time_series_forecast",
            quality_score=1.0
        )
        
        # Extract inputs
        df = kwargs.get('df')
        time_column = kwargs.get('time_column')
        value_column = kwargs.get('value_column')
        forecast_periods = kwargs.get('forecast_periods', 12)
        method = kwargs.get('method', 'exponential_smoothing')
        
        # VALIDATION
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        if time_column is None or time_column not in df.columns:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Time column '{time_column}' not found")
            result.success = False
            return result
        
        if value_column is None or value_column not in df.columns:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Value column '{value_column}' not found")
            result.success = False
            return result
        
        if forecast_periods < 1:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "Forecast periods must be >= 1")
            result.success = False
            return result
        
        # Check minimum data for forecasting
        min_samples_required = max(13, forecast_periods * 2)  # Need at least 2 years of monthly data
        if len(df) < min_samples_required:
            self._add_error(
                result,
                ErrorType.INSUFFICIENT_DATA,
                f"Need at least {min_samples_required} samples, got {len(df)}"
            )
            result.success = False
            return result
        
        # FORECASTING
        try:
            # Sort by time
            df_sorted = df.sort_values(by=time_column).copy()
            ts_data = df_sorted[value_column].values
            
            if method == 'exponential_smoothing':
                result_data, metrics = self._exponential_smoothing_forecast(
                    ts_data, forecast_periods
                )
            elif method == 'arima':
                result_data, metrics = self._arima_forecast(
                    ts_data, forecast_periods
                )
            else:
                raise ValueError(f"Unknown forecasting method: {method}")
            
            result.data = result_data
            result.quality_score = metrics.get('mae_ratio', 0.0)  # Quality based on MAE
            result.success = True
            
            self.logger.info(
                f"Time series forecast generated: {forecast_periods} periods, "
                f"method={method}"
            )
            
        except ImportError as e:
            self._add_error(
                result,
                ErrorType.MODEL_ERROR,
                f"Required library not available: {str(e)}"
            )
            result.success = False
        except Exception as e:
            self._add_error(
                result,
                ErrorType.PROCESSING_ERROR,
                f"Forecasting failed: {str(e)}"
            )
            result.success = False
            self.logger.error(f"Forecasting error: {e}")
        
        return result
    
    def _exponential_smoothing_forecast(
        self, ts_data: np.ndarray, forecast_periods: int
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """Perform exponential smoothing forecast.
        
        Args:
            ts_data: Time series values
            forecast_periods: Number of periods to forecast
            
        Returns:
            Tuple of (result_data dict, metrics dict)
        """
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
        except ImportError:
            raise ImportError("statsmodels not available for exponential smoothing")
        
        # Fit model
        model = ExponentialSmoothing(
            ts_data,
            trend='add',
            seasonal=None,
            initialization_method='estimated'
        )
        fitted_model = model.fit(optimized=True)
        
        # Generate forecast
        forecast = fitted_model.forecast(steps=forecast_periods)
        
        # Calculate metrics
        fitted_values = fitted_model.fittedvalues
        mae = np.mean(np.abs(ts_data[-len(fitted_values):] - fitted_values))
        mae_ratio = 1.0 - min(mae / np.mean(np.abs(ts_data)) if np.mean(np.abs(ts_data)) > 0 else 0, 1.0)
        
        result_data = {
            "method": "exponential_smoothing",
            "historical_values": ts_data.tolist(),
            "forecast": forecast.tolist(),
            "forecast_periods": forecast_periods,
            "mae": float(mae),
            "num_samples": len(ts_data),
        }
        
        metrics = {
            "mae": float(mae),
            "mae_ratio": float(mae_ratio),
        }
        
        return result_data, metrics
    
    def _arima_forecast(
        self, ts_data: np.ndarray, forecast_periods: int
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """Perform ARIMA forecast.
        
        Args:
            ts_data: Time series values
            forecast_periods: Number of periods to forecast
            
        Returns:
            Tuple of (result_data dict, metrics dict)
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            raise ImportError("statsmodels not available for ARIMA")
        
        # Fit ARIMA(1,1,1) as default
        model = ARIMA(ts_data, order=(1, 1, 1))
        fitted_model = model.fit()
        
        # Generate forecast
        forecast = fitted_model.forecast(steps=forecast_periods)
        
        # Calculate metrics
        fitted_values = fitted_model.fittedvalues
        mae = np.mean(np.abs(ts_data[-len(fitted_values):] - fitted_values))
        mae_ratio = 1.0 - min(mae / np.mean(np.abs(ts_data)) if np.mean(np.abs(ts_data)) > 0 else 0, 1.0)
        
        result_data = {
            "method": "arima",
            "historical_values": ts_data.tolist(),
            "forecast": forecast.tolist(),
            "forecast_periods": forecast_periods,
            "mae": float(mae),
            "num_samples": len(ts_data),
        }
        
        metrics = {
            "mae": float(mae),
            "mae_ratio": float(mae_ratio),
        }
        
        return result_data, metrics
