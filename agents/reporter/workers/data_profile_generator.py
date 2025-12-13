"""DataProfileGenerator - Generates detailed data profile reports.

Enhanced with:
- Outlier detection
- Distribution analysis
- Cardinality metrics
- Data drift detection prep
- Improved categorical analysis
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from .base_worker import BaseWorker, WorkerResult, ErrorType, ValidationUtils
from agents.error_intelligence.main import ErrorIntelligence


class DataProfileGenerator(BaseWorker):
    """Generates detailed data profile reports with advanced analytics.
    
    Provides:
    - Per-column statistics
    - Outlier detection (IQR method)
    - Distribution analysis
    - Cardinality assessment
    - Missing data analysis
    - Type-specific statistics
    """
    
    def __init__(self):
        super().__init__("data_profile_generator")
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Generate comprehensive data profile.
        
        Args:
            df: DataFrame to profile
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with detailed data profile
        """
        result = self._create_result(
            success=True,
            task_type="data_profile",
            data={}
        )
        
        try:
            # Validate input
            is_valid, error_msg = ValidationUtils.validate_dataframe(df)
            if not is_valid:
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    error_msg,
                    severity="error"
                )
                result.success = False
                return result
            
            profile = {
                "report_type": "data_profile",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "columns": {},
                "summary_statistics": self._get_summary_stats(df),
            }
            
            # Profile each column
            for col in df.columns:
                col_info = self._profile_column(df, col)
                profile["columns"][col] = col_info
            
            result.data = profile
            result.rows_processed = len(df)
            
            # Calculate quality score
            avg_completeness = np.mean([v["completeness"] for v in profile["columns"].values()])
            result.quality_score = avg_completeness / 100.0
            
            self.logger.info(f"Data profile generated for {len(df.columns)} columns")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Generation failed: {str(e)}",
                severity="error",
                details={"exception_type": type(e).__name__}
            )
            result.success = False
        
        return result
    
    def _profile_column(self, df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Profile a single column with advanced metrics."""
        dtype = str(df[col].dtype)
        series = df[col]
        null_count = series.isnull().sum()
        null_pct = (null_count / len(series) * 100) if len(series) > 0 else 0
        unique = series.nunique()
        
        col_info = {
            "data_type": dtype,
            "missing_values": int(null_count),
            "missing_percentage": round(null_pct, 2),
            "unique_values": unique,
            "unique_percentage": round((unique / len(series) * 100) if len(series) > 0 else 0, 2),
            "completeness": round(100 - null_pct, 2),
            "cardinality": self._assess_cardinality(unique, len(series)),
        }
        
        # Type-specific analysis
        if df[col].dtype in [np.int64, np.float64, np.int32, np.float32]:
            col_info.update(self._profile_numeric_column(series))
        elif df[col].dtype == 'object':
            col_info.update(self._profile_categorical_column(series))
        elif df[col].dtype == 'datetime64[ns]':
            col_info.update(self._profile_datetime_column(series))
        
        return col_info
    
    def _profile_numeric_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile numeric column with distribution and outlier analysis."""
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {"statistics": {}}
        
        # Basic statistics
        stats = {
            "count": int(len(clean_series)),
            "mean": float(clean_series.mean()),
            "median": float(clean_series.median()),
            "std": float(clean_series.std()),
            "var": float(clean_series.var()),
            "min": float(clean_series.min()),
            "q25": float(clean_series.quantile(0.25)),
            "q50": float(clean_series.quantile(0.50)),
            "q75": float(clean_series.quantile(0.75)),
            "max": float(clean_series.max()),
        }
        
        # Distribution metrics
        skewness = clean_series.skew()
        kurtosis = clean_series.kurtosis()
        
        # Outlier detection (IQR method)
        q1 = clean_series.quantile(0.25)
        q3 = clean_series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = ((clean_series < lower_bound) | (clean_series > upper_bound)).sum()
        outlier_pct = (outliers / len(clean_series) * 100) if len(clean_series) > 0 else 0
        
        return {
            "statistics": stats,
            "distribution": {
                "skewness": round(float(skewness), 3),
                "kurtosis": round(float(kurtosis), 3),
                "range": round(stats["max"] - stats["min"], 3),
            },
            "outliers": {
                "count": int(outliers),
                "percentage": round(outlier_pct, 2),
                "lower_bound": round(lower_bound, 3),
                "upper_bound": round(upper_bound, 3),
            },
        }
    
    def _profile_categorical_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile categorical column with value distribution."""
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {"value_distribution": {}}
        
        value_counts = clean_series.value_counts()
        top_values = value_counts.head(5)
        
        # Calculate diversity metric (entropy-inspired)
        probabilities = value_counts / len(clean_series)
        diversity = round(float(-(probabilities * np.log2(probabilities + 1e-10)).sum()), 3)
        
        distribution = {
            "total_distinct": int(value_counts.nunique()),
            "diversity_score": diversity,  # Higher = more diverse
            "top_values": dict(top_values.items()),
            "top_value_frequency": round(float(top_values.iloc[0] / len(clean_series) * 100), 2) if len(top_values) > 0 else 0,
        }
        
        return {"value_distribution": distribution}
    
    def _profile_datetime_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile datetime column."""
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {"datetime_info": {}}
        
        try:
            datetime_info = {
                "min_date": str(clean_series.min()),
                "max_date": str(clean_series.max()),
                "date_range_days": int((clean_series.max() - clean_series.min()).days),
                "unique_dates": int(clean_series.nunique()),
            }
            return {"datetime_info": datetime_info}
        except Exception:
            return {"datetime_info": {"error": "Could not parse datetime column"}}
    
    def _assess_cardinality(self, unique_count: int, total_count: int) -> str:
        """Assess cardinality of a column.
        
        Returns:
        - 'Low': <5% unique values
        - 'Medium': 5-50% unique values
        - 'High': >50% unique values
        """
        if total_count == 0:
            return "Unknown"
        
        pct = (unique_count / total_count) * 100
        
        if pct < 5:
            return "Low"
        elif pct < 50:
            return "Medium"
        else:
            return "High"
    
    def _get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get overall summary statistics."""
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_cells": len(df) * len(df.columns),
            "numeric_columns": len(df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": len(df.select_dtypes(include=['object']).columns),
            "datetime_columns": len(df.select_dtypes(include=['datetime64']).columns),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
        }
