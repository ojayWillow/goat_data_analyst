"""Time Series - ARIMA and Exponential Smoothing forecasting."""

from .base import Base, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence
import pandas as pd
import numpy as np

logger = get_logger(__name__)


class TimeSeries(Base):
    """Worker for time series forecasting.
    
    Performs time series analysis and provides:
    - ARIMA forecasts
    - Exponential smoothing forecasts
    - Trend and seasonal decomposition
    - Confidence intervals
    """
    
    def __init__(self):
        super().__init__("TimeSeries")
        self.model = None
        self.method = None
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute time series forecasting.
        
        Args:
            series: Time series data (pandas Series or array)
            periods: Number of periods to forecast (default: 12)
            method: 'arima' or 'exponential_smoothing' (default: 'auto')
            decompose: Whether to decompose (default: True)
            
        Returns:
            WorkerResult with forecasts and confidence intervals
        """
        result = self._create_result(
            task_type="time_series_forecasting",
            quality_score=1.0
        )
        
        # Extract inputs
        series = kwargs.get('series')
        periods = kwargs.get('periods', 12)
        method = kwargs.get('method', 'auto')
        decompose = kwargs.get('decompose', True)
        
        # VALIDATION
        if series is None:
            self._add_error(result, ErrorType.MISSING_DATA, "No time series data provided")
            result.success = False
            return result
        
        # Convert to pandas Series
        if isinstance(series, (list, np.ndarray)):
            series = pd.Series(series)
        elif not isinstance(series, pd.Series):
            self._add_error(result, ErrorType.INVALID_PARAMETER, "Series must be list, array, or pandas Series")
            result.success = False
            return result
        
        if len(series) < 4:
            self._add_error(result, ErrorType.INSUFFICIENT_DATA, f"Need at least 4 values, got {len(series)}")
            result.success = False
            return result
        
        if periods < 1:
            self._add_error(result, ErrorType.INVALID_PARAMETER, "Periods must be >= 1")
            result.success = False
            return result
        
        # FORECASTING
        try:
            try:
                from statsmodels.tsa.arima.model import ARIMA
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
                from statsmodels.tsa.seasonal import seasonal_decompose
            except ImportError:
                self._add_error(result, ErrorType.MODEL_ERROR, "statsmodels not available")
                result.success = False
                return result
            
            # Remove any NaN values
            clean_series = series.dropna()
            if len(clean_series) < len(series):
                self._add_warning(result, f"Removed {len(series) - len(clean_series)} NaN values")
            
            series = clean_series
            
            # Auto-detect method
            if method == 'auto':
                # Try ARIMA first, fallback to exponential smoothing
                self.method = 'arima'
            else:
                self.method = method
            
            forecast_data = {}
            
            # ARIMA Forecasting
            if self.method == 'arima':
                try:
                    # Auto ARIMA (p, d, q) = (1, 1, 1) as default
                    self.model = ARIMA(series, order=(1, 1, 1))
                    fitted_model = self.model.fit()
                    
                    # Get forecast
                    forecast_result = fitted_model.get_forecast(steps=periods)
                    forecast_values = forecast_result.predicted_mean.values
                    conf_int = forecast_result.conf_int(alpha=0.05)
                    
                    forecast_data = {
                        "method": "ARIMA(1,1,1)",
                        "forecast": forecast_values.tolist(),
                        "confidence_interval_lower": conf_int.iloc[:, 0].values.tolist(),
                        "confidence_interval_upper": conf_int.iloc[:, 1].values.tolist(),
                        "aic": float(fitted_model.aic),
                        "bic": float(fitted_model.bic),
                    }
                    
                    self.logger.info(f"ARIMA forecast generated: {periods} periods, AIC={fitted_model.aic:.2f}")
                    
                except Exception as e:
                    # Fallback to exponential smoothing
                    self.logger.warning(f"ARIMA failed, trying exponential smoothing: {e}")
                    self.method = 'exponential_smoothing'
            
            # Exponential Smoothing Forecasting
            if self.method == 'exponential_smoothing' or not forecast_data:
                try:
                    self.model = ExponentialSmoothing(
                        series,
                        trend='add',
                        seasonal=None,
                        initialization_method='estimated'
                    )
                    fitted_model = self.model.fit(optimized=True)
                    forecast_values = fitted_model.forecast(steps=periods).values
                    
                    forecast_data = {
                        "method": "ExponentialSmoothing",
                        "forecast": forecast_values.tolist(),
                        "smoothing_level": float(fitted_model.params[0]) if hasattr(fitted_model, 'params') else None,
                        "aic": float(fitted_model.aic) if hasattr(fitted_model, 'aic') else None,
                    }
                    
                    self.logger.info(f"Exponential smoothing forecast generated: {periods} periods")
                    
                except Exception as e:
                    # Both failed, return error
                    self._add_error(
                        result,
                        ErrorType.PROCESSING_ERROR,
                        f"Both ARIMA and exponential smoothing failed: {str(e)}"
                    )
                    result.success = False
                    return result
            
            # DECOMPOSITION
            decomp_data = {}
            if decompose and len(series) >= 12:
                try:
                    decomposition = seasonal_decompose(series, model='additive', period=12)
                    decomp_data = {
                        "trend": decomposition.trend.fillna(0).tolist(),
                        "seasonal": decomposition.seasonal.fillna(0).tolist(),
                        "residual": decomposition.resid.fillna(0).tolist(),
                    }
                except Exception as e:
                    self._add_warning(result, f"Decomposition failed: {e}")
            
            # Combine results
            result.data = {
                "forecast_data": forecast_data,
                "decomposition": decomp_data,
                "series_length": len(series),
                "forecast_periods": periods,
                "original_values": series.values.tolist(),
            }
            
            result.success = True
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.PROCESSING_ERROR,
                f"Forecasting failed: {str(e)}"
            )
            result.success = False
            self.logger.error(f"Forecasting error: {e}")
        
        return result
