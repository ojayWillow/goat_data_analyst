"""Explorer Agent - Data exploration and statistical analysis.

Computes descriptive statistics, distributions, correlations, and insights
from loaded datasets.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

from core.logger import get_logger
from core.exceptions import AgentError

logger = get_logger(__name__)


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
    """
    
    def __init__(self):
        """Initialize Explorer agent."""
        self.name = "Explorer"
        self.data = None
        self.analysis_cache = {}
        logger.info(f"{self.name} initialized")
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data to explore.
        
        Args:
            df: DataFrame to analyze
        """
        self.data = df
        self.analysis_cache = {}  # Clear cache
        logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    def describe_numeric(self) -> Dict[str, Any]:
        """Get detailed numeric statistics.
        
        Returns:
            Dictionary with statistics for numeric columns
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Computing numeric statistics...")
            
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
            
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
            
            logger.info(f"Computed statistics for {len(stats)} numeric columns")
            
            return {
                "status": "success",
                "numeric_columns": numeric_cols,
                "statistics": stats,
            }
        
        except Exception as e:
            logger.error(f"Error computing numeric statistics: {e}")
            raise AgentError(f"Failed to compute statistics: {e}")
    
    def describe_categorical(self) -> Dict[str, Any]:
        """Get categorical data summaries.
        
        Returns:
            Dictionary with statistics for categorical columns
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Computing categorical statistics...")
            
            categorical_cols = self.data.select_dtypes(include=['object']).columns.tolist()
            
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
            
            logger.info(f"Computed statistics for {len(stats)} categorical columns")
            
            return {
                "status": "success",
                "categorical_columns": categorical_cols,
                "statistics": stats,
            }
        
        except Exception as e:
            logger.error(f"Error computing categorical statistics: {e}")
            raise AgentError(f"Failed to compute categorical statistics: {e}")
    
    def correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlations between numeric columns.
        
        Returns:
            Dictionary with correlation matrix and insights
            
        Raises:
            AgentError: If no data set or insufficient numeric columns
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Computing correlations...")
            
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
            
            logger.info(f"Found {len(strong_corrs)} strong correlations")
            
            return {
                "status": "success",
                "correlation_matrix": corr_matrix.to_dict(),
                "strong_correlations": strong_corrs,
                "columns": corr_matrix.columns.tolist(),
            }
        
        except Exception as e:
            logger.error(f"Error computing correlations: {e}")
            raise AgentError(f"Failed to compute correlations: {e}")
    
    def data_quality_assessment(self) -> Dict[str, Any]:
        """Assess overall data quality.
        
        Returns:
            Data quality metrics and recommendations
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Assessing data quality...")
            
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
            logger.error(f"Error assessing data quality: {e}")
            raise AgentError(f"Failed to assess data quality: {e}")
    
    def detect_outliers(self, method: str = "iqr", threshold: float = 1.5) -> Dict[str, Any]:
        """Detect outliers in numeric columns.
        
        Args:
            method: Detection method ('iqr' or 'zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Dictionary with outlier information
            
        Raises:
            AgentError: If no data set or invalid method
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if method not in ["iqr", "zscore"]:
            raise AgentError(f"Unknown method: {method}. Use 'iqr' or 'zscore'")
        
        try:
            logger.info(f"Detecting outliers using {method} method...")
            
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
            
            logger.info(f"Found {total_outliers} total outliers")
            
            return {
                "status": "success",
                "method": method,
                "threshold": threshold,
                "columns_with_outliers": list(outliers.keys()),
                "outliers": outliers,
                "total_outliers": total_outliers,
            }
        
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            raise AgentError(f"Failed to detect outliers: {e}")
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Get comprehensive summary report.
        
        Returns:
            Dictionary with all analysis results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating summary report...")
            
            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "shape": {"rows": self.data.shape[0], "columns": self.data.shape[1]},
                "numeric_stats": self.describe_numeric(),
                "categorical_stats": self.describe_categorical(),
                "correlations": self.correlation_analysis(),
                "data_quality": self.data_quality_assessment(),
                "outliers": self.detect_outliers(),
            }
        
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
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
