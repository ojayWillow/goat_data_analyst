"""Statistical Worker - IQR, Z-score, and Modified Z-score anomaly detection."""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Any, Dict

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class StatisticalWorker(BaseWorker):
    """Worker that performs statistical anomaly detection.
    
    Methods:
    - IQR (Interquartile Range) detection
    - Z-score detection
    - Modified Z-score detection (more robust)
    """
    
    def __init__(self):
        """Initialize StatisticalWorker."""
        super().__init__("StatisticalWorker")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Execute statistical anomaly detection.
        
        Args:
            df: DataFrame to analyze
            column: Column to detect anomalies in
            method: 'iqr', 'zscore', or 'modified_zscore'
            multiplier: IQR multiplier (default 1.5) for IQR method
            threshold: Z-score threshold (default 3.0) for zscore method
            mod_threshold: Modified Z-score threshold (default 3.5)
            
        Returns:
            WorkerResult with detection results
        """
        try:
            result = self._run_statistical(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="StatisticalWorker",
                operation="statistical_detection",
                context={"method": kwargs.get('method', 'iqr'), "column": kwargs.get('column')}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="StatisticalWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"method": kwargs.get('method', 'iqr'), "column": kwargs.get('column')}
            )
            raise
    
    def _run_statistical(self, **kwargs) -> WorkerResult:
        """Perform statistical detection."""
        df = kwargs.get('df')
        column = kwargs.get('column')
        method = kwargs.get('method', 'iqr')
        multiplier = kwargs.get('multiplier', 1.5)
        threshold = kwargs.get('threshold', 3.0)
        mod_threshold = kwargs.get('mod_threshold', 3.5)
        
        # Create empty result
        result = self._create_result(
            task_type=f"statistical_{method}_detection",
            quality_score=1.0
        )
        
        # Validate inputs
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided")
            result.success = False
            return result
        
        if column not in df.columns:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Column '{column}' not found")
            result.success = False
            return result
        
        try:
            if method == 'iqr':
                return self._iqr_detection(df, column, multiplier)
            elif method == 'zscore':
                return self._zscore_detection(df, column, threshold)
            elif method == 'modified_zscore':
                return self._modified_zscore_detection(df, column, mod_threshold)
            else:
                self._add_error(result, ErrorType.INVALID_PARAMETER, f"Unknown method: {method}")
                result.success = False
                return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, str(e))
            result.success = False
            return result
    
    def _iqr_detection(self, df: pd.DataFrame, column: str, multiplier: float) -> WorkerResult:
        """IQR-based outlier detection.
        
        Args:
            df: DataFrame
            column: Column name
            multiplier: IQR multiplier (default 1.5)
            
        Returns:
            WorkerResult with IQR detection results
        """
        result = self._create_result(
            task_type="iqr_detection",
            quality_score=1.0
        )
        
        series = df[column].dropna()
        
        if len(series) < 2:
            self._add_error(result, ErrorType.INSUFFICIENT_DATA, "Insufficient data after removing NaNs")
            result.success = False
            return result
        
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        outliers_mask = (series < lower_bound) | (series > upper_bound)
        outlier_indices = series[outliers_mask].index.tolist()
        outlier_values = series[outliers_mask].values
        
        outlier_count = len(outlier_values)
        outlier_pct = (outlier_count / len(series) * 100) if len(series) > 0 else 0
        
        lower_outliers = series[series < lower_bound].values
        upper_outliers = series[series > upper_bound].values
        
        result.data = {
            "method": "IQR",
            "column": column,
            "multiplier": multiplier,
            "bounds": {
                "lower": float(lower_bound),
                "upper": float(upper_bound),
            },
            "statistics": {
                "Q1": float(Q1),
                "Q3": float(Q3),
                "IQR": float(IQR),
            },
            "outliers_count": outlier_count,
            "outliers_percentage": round(outlier_pct, 2),
            "lower_outliers_count": len(lower_outliers),
            "upper_outliers_count": len(upper_outliers),
            "outlier_values": sorted(outlier_values)[:20],
            "outlier_indices": outlier_indices[:20],
        }
        
        logger.info(f"IQR detection: {outlier_count} outliers ({outlier_pct:.2f}%)")
        return result
    
    def _zscore_detection(self, df: pd.DataFrame, column: str, threshold: float) -> WorkerResult:
        """Z-score-based outlier detection.
        
        Args:
            df: DataFrame
            column: Column name
            threshold: Z-score threshold (default 3.0)
            
        Returns:
            WorkerResult with Z-score detection results
        """
        result = self._create_result(
            task_type="zscore_detection",
            quality_score=1.0
        )
        
        series = df[column].dropna()
        
        if len(series) < 2:
            self._add_error(result, ErrorType.INSUFFICIENT_DATA, "Insufficient data after removing NaNs")
            result.success = False
            return result
        
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            self._add_warning(result, "Zero standard deviation - cannot compute Z-scores")
            result.success = False
            return result
        
        z_scores = np.abs((series - mean) / std)
        outliers_mask = z_scores > threshold
        outlier_indices = series[outliers_mask].index.tolist()
        outlier_values = series[outliers_mask].values
        
        outlier_count = len(outlier_values)
        outlier_pct = (outlier_count / len(series) * 100) if len(series) > 0 else 0
        
        result.data = {
            "method": "Z-Score",
            "column": column,
            "threshold": threshold,
            "statistics": {
                "mean": float(mean),
                "std": float(std),
            },
            "outliers_count": outlier_count,
            "outliers_percentage": round(outlier_pct, 2),
            "outlier_values": sorted(outlier_values)[:20],
            "outlier_indices": outlier_indices[:20],
            "z_score_range": [float(z_scores.min()), float(z_scores.max())],
        }
        
        logger.info(f"Z-score detection: {outlier_count} outliers ({outlier_pct:.2f}%)")
        return result
    
    def _modified_zscore_detection(self, df: pd.DataFrame, column: str, threshold: float) -> WorkerResult:
        """Modified Z-score detection (more robust to skewed distributions).
        
        Args:
            df: DataFrame
            column: Column name
            threshold: Modified Z-score threshold (default 3.5)
            
        Returns:
            WorkerResult with Modified Z-score detection results
        """
        result = self._create_result(
            task_type="modified_zscore_detection",
            quality_score=1.0
        )
        
        series = df[column].dropna()
        
        if len(series) < 2:
            self._add_error(result, ErrorType.INSUFFICIENT_DATA, "Insufficient data after removing NaNs")
            result.success = False
            return result
        
        median = series.median()
        mad = stats.median_abs_deviation(series)
        
        if mad == 0:
            self._add_warning(result, "Zero MAD (Median Absolute Deviation) - cannot compute Modified Z-scores")
            result.success = False
            return result
        
        modified_z_scores = 0.6745 * (series - median) / mad
        outliers_mask = np.abs(modified_z_scores) > threshold
        outlier_indices = series[outliers_mask].index.tolist()
        outlier_values = series[outliers_mask].values
        
        outlier_count = len(outlier_values)
        outlier_pct = (outlier_count / len(series) * 100) if len(series) > 0 else 0
        
        result.data = {
            "method": "Modified Z-Score",
            "column": column,
            "threshold": threshold,
            "statistics": {
                "median": float(median),
                "mad": float(mad),
            },
            "outliers_count": outlier_count,
            "outliers_percentage": round(outlier_pct, 2),
            "outlier_values": sorted(outlier_values)[:20],
            "outlier_indices": outlier_indices[:20],
            "z_score_range": [float(np.abs(modified_z_scores).min()), float(np.abs(modified_z_scores).max())],
        }
        
        logger.info(f"Modified Z-score detection: {outlier_count} outliers ({outlier_pct:.2f}%)")
        return result
