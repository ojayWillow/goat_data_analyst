"""Explorer Agent - Data exploration and statistical analysis.

Integrated with Week 1 foundation systems:
- Configuration management
- Error recovery with retry logic
- Structured logging
- Input/output validation

Computes descriptive statistics, distributions, correlations, and insights
from loaded datasets.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timezone

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


class Explorer:
    """Agent for exploring and analyzing data.
    
    Capabilities:
    - Descriptive statistics (mean, median, std, min, max, etc.)
    - Distribution analysis
    - Correlation analysis
    - Categorical summaries
    - Time series analysis preparation
    - Data quality assessment
    - Outlier detection (basic)
    
    Integrated with Week 1 systems:
    - Centralized configuration
    - Error recovery on all operations
    - Structured logging of all activities
    - Input/output validation
    """
    
    def __init__(self):
        """Initialize Explorer agent with Week 1 systems."""
        self.name = "Explorer"
        self.config = AgentConfig()
        self.data = None
        self.analysis_cache = {}
        logger.info(f"{self.name} initialized", extra={'version': '2.0-week1-integrated'})
    
    @validate_input({'df': 'dataframe'})
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data to explore with validation.
        
        Args:
            df: DataFrame to analyze (validated)
        """
        with logger.operation('set_data', {'rows': len(df), 'columns': len(df.columns)}):
            self.data = df
            self.analysis_cache = {}  # Clear cache
            logger.info(
                'Data set for exploration',
                extra={
                    'rows': df.shape[0],
                    'columns': df.shape[1],
                    'memory_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
                }
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
    def describe_numeric(self) -> Dict[str, Any]:
        """Get detailed numeric statistics with error recovery.
        
        Returns:
            Dictionary with statistics for numeric columns (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('describe_numeric'):
            try:
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
                logger.info('Found numeric columns', extra={'count': len(numeric_cols)})
                
                if not numeric_cols:
                    return {"status": "no_numeric_columns", "message": "No numeric columns found"}
                
                stats = {}
                
                for col in numeric_cols:
                    series = self.data[col].dropna()
                    
                    if len(series) == 0:
                        continue
                    
                    stats[col] = {
                        "count": len(series),
                        "mean": float(series.mean()),
                        "median": float(series.median()),
                        "std": float(series.std()),
                        "var": float(series.var()),
                        "min": float(series.min()),
                        "q25": float(series.quantile(0.25)),
                        "q50": float(series.quantile(0.50)),
                        "q75": float(series.quantile(0.75)),
                        "max": float(series.max()),
                        "iqr": float(series.quantile(0.75) - series.quantile(0.25)),
                        "skewness": float(series.skew()),
                        "kurtosis": float(series.kurtosis()),
                        "range": float(series.max() - series.min()),
                    }
                
                logger.info(
                    'Numeric statistics computed',
                    extra={'columns': len(stats), 'timestamp': datetime.now(timezone.utc).isoformat()}
                )
                
                return {
                    "status": "success",
                    "numeric_columns": numeric_cols,
                    "statistics": stats,
                }
            
            except Exception as e:
                logger.error(
                    'Error computing numeric statistics',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Failed to compute statistics: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def describe_categorical(self) -> Dict[str, Any]:
        """Get categorical data summaries with error recovery.
        
        Returns:
            Dictionary with statistics for categorical columns (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('describe_categorical'):
            try:
                categorical_cols = self.data.select_dtypes(include=['object']).columns.tolist()
                logger.info('Found categorical columns', extra={'count': len(categorical_cols)})
                
                if not categorical_cols:
                    return {"status": "no_categorical_columns", "message": "No categorical columns found"}
                
                stats = {}
                
                for col in categorical_cols:
                    value_counts = self.data[col].value_counts()
                    
                    stats[col] = {
                        "count": len(self.data[col]),
                        "unique_values": self.data[col].nunique(),
                        "most_common": value_counts.index[0] if len(value_counts) > 0 else None,
                        "most_common_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                        "least_common": value_counts.index[-1] if len(value_counts) > 0 else None,
                        "least_common_count": int(value_counts.iloc[-1]) if len(value_counts) > 0 else 0,
                        "missing": int(self.data[col].isna().sum()),
                        "top_10_values": dict(value_counts.head(10).items()),
                    }
                
                logger.info(
                    'Categorical statistics computed',
                    extra={'columns': len(stats)}
                )
                
                return {
                    "status": "success",
                    "categorical_columns": categorical_cols,
                    "statistics": stats,
                }
            
            except Exception as e:
                logger.error(
                    'Error computing categorical statistics',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Failed to compute categorical statistics: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlations between numeric columns with error recovery.
        
        Returns:
            Dictionary with correlation matrix and insights (validated)
            
        Raises:
            AgentError: If no data set or insufficient numeric columns
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('correlation_analysis'):
            try:
                numeric_data = self.data.select_dtypes(include=[np.number])
                
                if numeric_data.shape[1] < 2:
                    return {"status": "insufficient_columns", "message": "Need at least 2 numeric columns"}
                
                # Compute correlation matrix
                corr_matrix = numeric_data.corr().round(3)
                
                # Find strong correlations (|r| > 0.7)
                strong_corrs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            strong_corrs.append({
                                "col1": corr_matrix.columns[i],
                                "col2": corr_matrix.columns[j],
                                "correlation": float(corr_val),
                            })
                
                logger.info(
                    'Correlation analysis complete',
                    extra={'strong_correlations': len(strong_corrs), 'total_columns': len(corr_matrix)}
                )
                
                return {
                    "status": "success",
                    "correlation_matrix": corr_matrix.to_dict(),
                    "strong_correlations": strong_corrs,
                    "columns": corr_matrix.columns.tolist(),
                }
            
            except Exception as e:
                logger.error(
                    'Error computing correlations',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Failed to compute correlations: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def data_quality_assessment(self) -> Dict[str, Any]:
        """Assess overall data quality with error recovery.
        
        Returns:
            Data quality metrics and recommendations (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('data_quality_assessment'):
            try:
                total_cells = self.data.shape[0] * self.data.shape[1]
                null_cells = self.data.isnull().sum().sum()
                null_pct = (null_cells / total_cells * 100) if total_cells > 0 else 0
                
                duplicates = self.data.duplicated().sum()
                duplicate_pct = (duplicates / len(self.data) * 100) if len(self.data) > 0 else 0
                
                # Column-level quality
                column_quality = {}
                for col in self.data.columns:
                    null_count = self.data[col].isnull().sum()
                    null_pct_col = (null_count / len(self.data) * 100) if len(self.data) > 0 else 0
                    column_quality[col] = {
                        "null_count": int(null_count),
                        "null_percentage": float(null_pct_col),
                        "completeness": float(100 - null_pct_col),
                    }
                
                # Overall quality score (0-100)
                quality_score = 100 - null_pct - (duplicate_pct * 0.5)
                quality_score = max(0, min(100, quality_score))
                
                logger.info(
                    'Data quality assessment complete',
                    extra={
                        'quality_score': round(quality_score, 2),
                        'null_percentage': round(null_pct, 2),
                        'duplicate_percentage': round(duplicate_pct, 2)
                    }
                )
                
                return {
                    "status": "success",
                    "overall_quality_score": round(quality_score, 2),
                    "null_cells": null_cells,
                    "null_percentage": round(null_pct, 2),
                    "total_cells": total_cells,
                    "duplicates": int(duplicates),
                    "duplicate_percentage": round(duplicate_pct, 2),
                    "column_quality": column_quality,
                    "quality_rating": self._rate_quality(quality_score),
                }
            
            except Exception as e:
                logger.error(
                    'Error assessing data quality',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Failed to assess data quality: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1, fallback={})
    @validate_output('dict')
    def detect_outliers(self, method: str = "iqr", threshold: float = 1.5) -> Dict[str, Any]:
        """Detect outliers in numeric columns with error recovery.
        
        Args:
            method: Detection method ('iqr' or 'zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Dictionary with outlier information (validated)
            
        Raises:
            AgentError: If no data set or invalid method
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if method not in ["iqr", "zscore"]:
            raise AgentError(f"Unknown method: {method}. Use 'iqr' or 'zscore'")
        
        with logger.operation('detect_outliers', {'method': method, 'threshold': threshold}):
            try:
                numeric_data = self.data.select_dtypes(include=[np.number])
                outliers = {}
                total_outliers = 0
                
                for col in numeric_data.columns:
                    series = numeric_data[col].dropna()
                    
                    if method == "iqr":
                        Q1 = series.quantile(0.25)
                        Q3 = series.quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - threshold * IQR
                        upper_bound = Q3 + threshold * IQR
                        outlier_mask = (series < lower_bound) | (series > upper_bound)
                    
                    else:  # zscore
                        z_scores = np.abs((series - series.mean()) / series.std())
                        outlier_mask = z_scores > threshold
                    
                    outlier_count = outlier_mask.sum()
                    outlier_pct = (outlier_count / len(series) * 100) if len(series) > 0 else 0
                    
                    if outlier_count > 0:
                        outliers[col] = {
                            "count": int(outlier_count),
                            "percentage": round(outlier_pct, 2),
                            "values": series[outlier_mask].tolist()[:10],  # Top 10
                        }
                        total_outliers += outlier_count
                
                logger.info(
                    'Outlier detection complete',
                    extra={'total_outliers': total_outliers, 'columns_with_outliers': len(outliers)}
                )
                
                return {
                    "status": "success",
                    "method": method,
                    "threshold": threshold,
                    "columns_with_outliers": list(outliers.keys()),
                    "outliers": outliers,
                    "total_outliers": total_outliers,
                }
            
            except Exception as e:
                logger.error(
                    'Error detecting outliers',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Failed to detect outliers: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def get_summary_report(self) -> Dict[str, Any]:
        """Get comprehensive summary report with error recovery.
        
        Returns:
            Dictionary with all analysis results (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('get_summary_report'):
            try:
                logger.info('Generating comprehensive summary report')
                
                return {
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "shape": {"rows": self.data.shape[0], "columns": self.data.shape[1]},
                    "numeric_stats": self.describe_numeric(),
                    "categorical_stats": self.describe_categorical(),
                    "correlations": self.correlation_analysis(),
                    "data_quality": self.data_quality_assessment(),
                    "outliers": self.detect_outliers(),
                }
            
            except Exception as e:
                logger.error(
                    'Error generating summary report',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Failed to generate report: {e}")
    
    @staticmethod
    def _rate_quality(score: float) -> str:
        """Rate data quality based on score.
        
        Args:
            score: Quality score (0-100)
            
        Returns:
            Quality rating string
        """
        if score >= 95:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Very Poor"
