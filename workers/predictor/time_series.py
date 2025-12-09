"""TimeSeries Worker - Time series forecasting with ARIMA and exponential smoothing."""

from workers.base_worker import BaseWorker, WorkerResult, ErrorType
import pandas as pd
import numpy as np
from typing import Union, List

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False


class TimeSeriesWorker(BaseWorker):
    """Worker for time series forecasting.
    
    Returns forecast values, confidence intervals, decomposition components.
    """
    
    def __init__(self):
        super().__init__("TimeSeries")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute time series forecasting.
        
        Args:
            series: Time series data (list or pd.Series)
            periods: Number of periods to forecast
            method: 'auto', 'arima', or 'exponential_smoothing'
            decompose: Whether to decompose (seasonal) - default False
            
        Returns:
            WorkerResult with forecast, confidence intervals, decomposition
        """
        if not STATSMODELS_AVAILABLE:
            result = self._create_result(task_type="time_series")
            self._add_error(
                result,
                ErrorType.SKLEARN_UNAVAILABLE,
                "statsmodels not installed. Install with: pip install statsmodels"
            )
            result.success = False
            return result
        
        series = kwargs.get('series')
        periods = kwargs.get('periods', 10)
        method = kwargs.get('method', 'auto')
        decompose = kwargs.get('decompose', False)
        
        result = self._create_result(
            task_type="time_series",
            quality_score=1.0
        )
        
        # Validate inputs
        if series is None:
            self._add_error(result, ErrorType.MISSING_DATA, "No time series provided")
            result.success = False
            return result
        
        # Convert to list if needed
        if isinstance(series, pd.Series):
            series = series.values.tolist()
        elif not isinstance(series, (list, np.ndarray)):
            self._add_error(result, ErrorType.INVALID_PARAMETER, "Series must be list, array, or pd.Series")
            result.success = False
            return result
        
        if len(series) < 4:
            self._add_error(result, ErrorType.INSUFFICIENT_DATA, "Need at least 4 data points")
            result.success = False
            return result
        
        try:
            series_array = np.array(series, dtype=float)
            
            # Determine method
            if method == 'auto':
                # Use ARIMA for small series, exponential smoothing for larger
                method = 'exponential_smoothing' if len(series) > 20 else 'arima'
            
            if method == 'arima':
                forecast_data = self._forecast_arima(series_array, periods)
            elif method == 'exponential_smoothing':
                forecast_data = self._forecast_exponential_smoothing(series_array, periods)
            else:
                self._add_error(result, ErrorType.INVALID_PARAMETER, f"Unknown method: {method}")
                result.success = False
                return result
            
            result.data['forecast_data'] = forecast_data
            result.data['method'] = method
            result.data['num_historical_points'] = len(series)
            result.data['forecast_periods'] = periods
            
            # Optional decomposition
            if decompose and len(series) >= 12:
                try:
                    decomposition = self._decompose_series(series_array)
                    result.data['decomposition'] = decomposition
                except Exception as e:
                    self._add_warning(result, f"Decomposition failed: {str(e)}")
            
            result.success = True
            
        except Exception as e:
            self._add_error(result, ErrorType.PROCESSING_ERROR, f"Forecasting failed: {str(e)}")
            result.success = False
        
        return result
    
    def _forecast_arima(self, series: np.ndarray, periods: int) -> dict:
        """Forecast using ARIMA."""
        try:
            model = ARIMA(series, order=(1, 1, 1))
            results = model.fit()
            forecast = results.get_forecast(steps=periods)
            forecast_values = forecast.predicted_mean.values
            
            # Get confidence intervals if available
            conf_int = forecast.conf_int(alpha=0.05)
            
            return {
                'forecast': forecast_values.tolist(),
                'confidence_interval_lower': conf_int.iloc[:, 0].values.tolist() if conf_int is not None else None,
                'confidence_interval_upper': conf_int.iloc[:, 1].values.tolist() if conf_int is not None else None,
                'method_details': 'ARIMA(1,1,1)',
            }
        except Exception as e:
            raise Exception(f"ARIMA failed: {str(e)}")
    
    def _forecast_exponential_smoothing(self, series: np.ndarray, periods: int) -> dict:
        """Forecast using exponential smoothing."""
        try:
            # Simple exponential smoothing
            model = ExponentialSmoothing(series, trend='add' if len(series) > 10 else None)
            results = model.fit()
            forecast = results.forecast(steps=periods)
            
            return {
                'forecast': forecast.values.tolist(),
                'confidence_interval_lower': None,
                'confidence_interval_upper': None,
                'method_details': 'ExponentialSmoothing',
            }
        except Exception as e:
            raise Exception(f"Exponential smoothing failed: {str(e)}")
    
    def _decompose_series(self, series: np.ndarray) -> dict:
        """Decompose time series."""
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        # Use seasonal decomposition
        decomposition = seasonal_decompose(series, model='additive', period=12)
        
        return {
            'trend': decomposition.trend.values.tolist(),
            'seasonal': decomposition.seasonal.values.tolist(),
            'residual': decomposition.resid.values.tolist(),
        }
