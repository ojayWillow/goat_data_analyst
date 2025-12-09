"""NumericAnalyzer - Worker for analyzing numeric columns.

Analyzes numeric data and computes descriptive statistics.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class NumericAnalyzer(BaseWorker):
    """Worker that analyzes numeric columns in data."""
    
    def __init__(self):
        super().__init__("NumericAnalyzer")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Analyze numeric columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            WorkerResult with numeric statistics
        """
        return self.safe_execute(**kwargs)
    
    def execute(self, **kwargs) -> WorkerResult:
        """Perform numeric analysis."""
        df = kwargs.get('df')
        
        result = self._create_result(
            task_type="numeric_analysis",
            quality_score=1.0
        )
        
        if df is None or df.empty:
            self._add_error(
                result,
                ErrorType.MISSING_DATA,
                "No data provided or data is empty",
                severity="error",
                suggestion="Ensure DataFrame is not None or empty"
            )
            result.success = False
            result.quality_score = 0
            return result
        
        try:
            self.logger.info(f"Analyzing numeric columns...")
            
            # Select numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                self.logger.warning("No numeric columns found")
                self._add_warning(result, "No numeric columns found in data")
                result.data = {
                    "numeric_columns": [],
                    "statistics": {},
                }
                result.quality_score = 0.5
                return result
            
            # Analyze each numeric column
            stats = {}
            errors_found = []
            warnings_found = []
            
            for col in numeric_cols:
                try:
                    series = df[col].dropna()
                    
                    if len(series) == 0:
                        warnings_found.append(f"Column '{col}' is empty after removing NaN")
                        continue
                    
                    # Compute statistics
                    col_stats = self._compute_statistics(col, series)
                    stats[col] = col_stats
                    
                except Exception as e:
                    errors_found.append(f"Error analyzing column '{col}': {str(e)}")
                    self.logger.error(f"Error analyzing column {col}: {e}")
            
            # Add warnings
            for warning in warnings_found:
                self._add_warning(result, warning)
            
            # Add errors if any
            if errors_found:
                for error_msg in errors_found:
                    self._add_error(
                        result,
                        ErrorType.COMPUTATION_ERROR,
                        error_msg,
                        severity="warning"
                    )
            
            result.data = {
                "numeric_columns": numeric_cols,
                "statistics": stats,
                "columns_analyzed": len(stats),
            }
            
            # Quality score: lower if warnings/errors
            quality_score = 1.0
            quality_score -= (len(warnings_found) * 0.1)
            quality_score -= (len(errors_found) * 0.2)
            quality_score = max(0, min(1, quality_score))
            result.quality_score = quality_score
            
            self.logger.info(f"Analyzed {len(stats)} numeric columns")
            return result
        
        except Exception as e:
            self.logger.error(f"NumericAnalyzer failed: {e}")
            self._add_error(
                result,
                ErrorType.UNKNOWN_ERROR,
                str(e),
                severity="critical",
                suggestion="Check DataFrame structure and numeric column types"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _compute_statistics(self, col_name: str, series: pd.Series) -> Dict[str, Any]:
        """Compute statistics for a numeric column.
        
        Args:
            col_name: Column name
            series: Series data (NaN already removed)
            
        Returns:
            Dictionary of statistics
        """
        try:
            return {
                "count": int(len(series)),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "var": float(series.var()),
                "min": float(series.min()),
                "max": float(series.max()),
                "q25": float(series.quantile(0.25)),
                "q50": float(series.quantile(0.50)),
                "q75": float(series.quantile(0.75)),
                "iqr": float(series.quantile(0.75) - series.quantile(0.25)),
                "range": float(series.max() - series.min()),
                "skewness": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
            }
        except Exception as e:
            self.logger.error(f"Error computing statistics for {col_name}: {e}")
            raise
