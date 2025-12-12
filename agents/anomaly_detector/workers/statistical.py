"""Statistical Worker - Statistical anomaly detection using IQR, Z-score, and Modified Z-score methods.

This worker implements three complementary statistical methods for detecting anomalies:
1. IQR (Interquartile Range) - Robust to skewed distributions
2. Z-score - Assumes normal distribution
3. Modified Z-score (MAD-based) - Most robust to outliers

All methods follow A+ quality standards with comprehensive error handling and quality tracking.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Any, Dict, Optional
from datetime import datetime

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

# ===== CONSTANTS =====
DEFAULT_IQR_MULTIPLIER: float = 1.5
DEFAULT_ZSCORE_THRESHOLD: float = 3.0
DEFAULT_MOD_ZSCORE_THRESHOLD: float = 3.5
MIN_REQUIRED_SAMPLES: int = 2
ZERO_STD_TOLERANCE: float = 1e-10
QUALITY_THRESHOLD: float = 0.0

logger = get_logger(__name__)


class StatisticalWorker(BaseWorker):
    """Statistical anomaly detection worker using multiple methods.
    
    Performs anomaly detection using three statistical approaches:
    - IQR (Interquartile Range) for robust outlier detection
    - Z-score for normally distributed data
    - Modified Z-score for robust detection in skewed distributions
    
    Example:
        >>> worker = StatisticalWorker()
        >>> df = pd.DataFrame({'value': [1, 2, 3, 100, 4, 5]})
        >>> result = worker.execute(df=df, column='value', method='iqr')
        >>> print(f"Anomalies: {result.data['outliers_count']}")
        Anomalies: 1
    """
    
    def __init__(self) -> None:
        """Initialize StatisticalWorker with error intelligence tracking."""
        super().__init__("StatisticalWorker")
        self.error_intelligence: ErrorIntelligence = ErrorIntelligence()
        self.logger = get_logger("StatisticalWorker")
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Execute statistical anomaly detection with error handling.
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            column (str): Column name to detect anomalies in
            method (str, optional): Detection method: 'iqr', 'zscore', 'modified_zscore'. Defaults to 'iqr'.
            multiplier (float, optional): IQR multiplier for IQR method. Defaults to 1.5.
            threshold (float, optional): Z-score threshold. Defaults to 3.0.
            mod_threshold (float, optional): Modified Z-score threshold. Defaults to 3.5.
        
        Returns:
            WorkerResult: Standardized result with detection results
        """
        try:
            result: WorkerResult = self._run_statistical(**kwargs)
            self.error_intelligence.track_success(
                agent_name="anomaly_detector",
                worker_name="StatisticalWorker",
                operation="statistical_detection",
                context={
                    "method": kwargs.get('method', 'iqr'),
                    "column": kwargs.get('column', 'unknown')
                }
            )
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="anomaly_detector",
                worker_name="StatisticalWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "method": kwargs.get('method', 'iqr'),
                    "column": kwargs.get('column', 'unknown')
                }
            )
            raise
    
    def _run_statistical(self, **kwargs: Any) -> WorkerResult:
        """Run statistical detection with method routing.
        
        Args:
            **kwargs: Parameters for specific method
        
        Returns:
            WorkerResult: Detection results or error result
        """
        df: Optional[pd.DataFrame] = kwargs.get('df')
        column: str = kwargs.get('column', '')
        method: str = kwargs.get('method', 'iqr')
        multiplier: float = kwargs.get('multiplier', DEFAULT_IQR_MULTIPLIER)
        threshold: float = kwargs.get('threshold', DEFAULT_ZSCORE_THRESHOLD)
        mod_threshold: float = kwargs.get('mod_threshold', DEFAULT_MOD_ZSCORE_THRESHOLD)
        
        result: WorkerResult = self._create_result(
            task_type=f"statistical_{method}_detection",
            quality_score=1.0
        )
        
        if df is None or df.empty:
            self._add_error(result, ErrorType.MISSING_DATA, "No data provided to StatisticalWorker")
            result.success = False
            return result
        
        if not column or column not in df.columns:
            self._add_error(result, ErrorType.INVALID_COLUMN, f"Column '{column}' not found in DataFrame")
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
                self._add_error(result, ErrorType.INVALID_PARAMETER, f"Unknown method: '{method}'")
                result.success = False
                return result
        
        except Exception as e:
            self._add_error(result, ErrorType.COMPUTATION_ERROR, f"Detection failed: {str(e)}")
            result.success = False
            self.logger.error(f"Error in {method} detection: {str(e)}")
            return result
    
    def _iqr_detection(self, df: pd.DataFrame, column: str, multiplier: float) -> WorkerResult:
        """IQR-based outlier detection (Interquartile Range method)."""
        result: WorkerResult = self._create_result(task_type="iqr_detection", quality_score=1.0)
        
        series: pd.Series = df[column].dropna()
        null_count: int = len(df[column]) - len(series)
        
        if null_count > 0:
            self._add_warning(result, f"Found {null_count} null values - removed for analysis")
        
        if len(series) < MIN_REQUIRED_SAMPLES:
            self._add_error(result, ErrorType.INSUFFICIENT_DATA, f"Insufficient data: {len(series)} samples")
            result.success = False
            return result
        
        Q1: np.floating = series.quantile(0.25)
        Q3: np.floating = series.quantile(0.75)
        IQR: np.floating = Q3 - Q1
        lower_bound: np.floating = Q1 - multiplier * IQR
        upper_bound: np.floating = Q3 + multiplier * IQR
        
        outliers_mask: pd.Series = (series < lower_bound) | (series > upper_bound)
        outlier_indices: list = series[outliers_mask].index.tolist()
        outlier_values: np.ndarray = series[outliers_mask].values
        
        outlier_count: int = len(outlier_values)
        outlier_pct: float = (outlier_count / len(series) * 100) if len(series) > 0 else 0
        rows_failed: int = null_count + outlier_count
        total_rows: int = len(df[column])
        quality_score: float = max(QUALITY_THRESHOLD, 1.0 - (rows_failed / total_rows) if total_rows > 0 else 0.0)
        result.quality_score = quality_score
        
        lower_outliers: np.ndarray = series[series < lower_bound].values
        upper_outliers: np.ndarray = series[series > upper_bound].values
        
        result.data = {
            "method": "IQR (Interquartile Range)",
            "column": column,
            "multiplier": multiplier,
            "sample_count": len(series),
            "null_count": null_count,
            "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)},
            "statistics": {
                "Q1": float(Q1),
                "Q3": float(Q3),
                "median": float(series.median()),
                "IQR": float(IQR),
                "mean": float(series.mean()),
                "std": float(series.std()),
            },
            "outliers_count": outlier_count,
            "outliers_percentage": round(outlier_pct, 2),
            "lower_outliers_count": len(lower_outliers),
            "upper_outliers_count": len(upper_outliers),
            "outlier_values_sample": sorted(outlier_values.tolist())[:20],
            "outlier_indices_sample": outlier_indices[:20],
        }
        
        self.logger.info(f"IQR detection: {outlier_count} outliers ({outlier_pct:.2f}%) in column '{column}'")
        return result
    
    def _zscore_detection(self, df: pd.DataFrame, column: str, threshold: float) -> WorkerResult:
        """Z-score-based outlier detection."""
        result: WorkerResult = self._create_result(task_type="zscore_detection", quality_score=1.0)
        
        series: pd.Series = df[column].dropna()
        null_count: int = len(df[column]) - len(series)
        
        if null_count > 0:
            self._add_warning(result, f"Found {null_count} null values - removed for analysis")
        
        if len(series) < MIN_REQUIRED_SAMPLES:
            self._add_error(result, ErrorType.INSUFFICIENT_DATA, f"Insufficient data: {len(series)} samples")
            result.success = False
            return result
        
        mean: np.floating = series.mean()
        std: np.floating = series.std()
        
        if std < ZERO_STD_TOLERANCE:
            self._add_warning(result, "Zero standard deviation - cannot compute Z-scores")
            self._add_error(result, ErrorType.COMPUTATION_ERROR, "Cannot compute Z-scores with zero std")
            result.success = False
            return result
        
        z_scores: np.ndarray = np.abs((series - mean) / std)
        outliers_mask: np.ndarray = z_scores > threshold
        outlier_indices: list = series[outliers_mask].index.tolist()
        outlier_values: np.ndarray = series[outliers_mask].values
        
        outlier_count: int = len(outlier_values)
        outlier_pct: float = (outlier_count / len(series) * 100) if len(series) > 0 else 0
        rows_failed: int = null_count + outlier_count
        total_rows: int = len(df[column])
        quality_score: float = max(QUALITY_THRESHOLD, 1.0 - (rows_failed / total_rows) if total_rows > 0 else 0.0)
        result.quality_score = quality_score
        
        result.data = {
            "method": "Z-Score",
            "column": column,
            "threshold": threshold,
            "sample_count": len(series),
            "null_count": null_count,
            "statistics": {"mean": float(mean), "std": float(std), "median": float(series.median())},
            "outliers_count": outlier_count,
            "outliers_percentage": round(outlier_pct, 2),
            "outlier_values_sample": sorted(outlier_values.tolist())[:20],
            "outlier_indices_sample": outlier_indices[:20],
            "z_score_range": [float(z_scores.min()), float(z_scores.max())],
        }
        
        self.logger.info(f"Z-score detection: {outlier_count} outliers ({outlier_pct:.2f}%) in column '{column}'")
        return result
    
    def _modified_zscore_detection(self, df: pd.DataFrame, column: str, threshold: float) -> WorkerResult:
        """Modified Z-score detection (MAD-based, most robust)."""
        result: WorkerResult = self._create_result(task_type="modified_zscore_detection", quality_score=1.0)
        
        series: pd.Series = df[column].dropna()
        null_count: int = len(df[column]) - len(series)
        
        if null_count > 0:
            self._add_warning(result, f"Found {null_count} null values - removed for analysis")
        
        if len(series) < MIN_REQUIRED_SAMPLES:
            self._add_error(result, ErrorType.INSUFFICIENT_DATA, f"Insufficient data: {len(series)} samples")
            result.success = False
            return result
        
        median: np.floating = series.median()
        mad: np.floating = stats.median_abs_deviation(series)
        
        if mad < ZERO_STD_TOLERANCE:
            self._add_warning(result, "Zero MAD - cannot compute modified Z-scores")
            self._add_error(result, ErrorType.COMPUTATION_ERROR, "Cannot compute modified Z-scores with zero MAD")
            result.success = False
            return result
        
        modified_z_scores: np.ndarray = 0.6745 * (series - median) / mad
        outliers_mask: np.ndarray = np.abs(modified_z_scores) > threshold
        outlier_indices: list = series[outliers_mask].index.tolist()
        outlier_values: np.ndarray = series[outliers_mask].values
        
        outlier_count: int = len(outlier_values)
        outlier_pct: float = (outlier_count / len(series) * 100) if len(series) > 0 else 0
        rows_failed: int = null_count + outlier_count
        total_rows: int = len(df[column])
        quality_score: float = max(QUALITY_THRESHOLD, 1.0 - (rows_failed / total_rows) if total_rows > 0 else 0.0)
        result.quality_score = quality_score
        
        result.data = {
            "method": "Modified Z-Score (MAD-based)",
            "column": column,
            "threshold": threshold,
            "sample_count": len(series),
            "null_count": null_count,
            "statistics": {"median": float(median), "mad": float(mad), "mean": float(series.mean())},
            "outliers_count": outlier_count,
            "outliers_percentage": round(outlier_pct, 2),
            "outlier_values_sample": sorted(outlier_values.tolist())[:20],
            "outlier_indices_sample": outlier_indices[:20],
            "modified_z_score_range": [float(np.abs(modified_z_scores).min()), float(np.abs(modified_z_scores).max())],
        }
        
        self.logger.info(f"Modified Z-score detection: {outlier_count} outliers ({outlier_pct:.2f}%) in column '{column}'")
        return result
