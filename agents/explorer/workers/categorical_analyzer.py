"""CategoricalAnalyzer - Worker for analyzing categorical columns.

Analyzes categorical data and computes value counts.
"""

import pandas as pd
from typing import Any, Dict, Optional

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class CategoricalAnalyzer(BaseWorker):
    """Worker that analyzes categorical columns in data."""
    
    def __init__(self):
        super().__init__("CategoricalAnalyzer")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Analyze categorical columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            WorkerResult with categorical statistics
        """
        try:
            result = self._run_categorical_analysis(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="explorer",
                worker_name="CategoricalAnalyzer",
                operation="categorical_analysis",
                context={}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="explorer",
                worker_name="CategoricalAnalyzer",
                error_type=type(e).__name__,
                error_message=str(e),
                context={}
            )
            raise
    
    def _run_categorical_analysis(self, **kwargs) -> WorkerResult:
        """Perform categorical analysis."""
        df = kwargs.get('df')
        
        result = self._create_result(
            task_type="categorical_analysis",
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
            self.logger.info("Analyzing categorical columns...")
            
            # Select categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if not categorical_cols:
                self.logger.warning("No categorical columns found")
                self._add_warning(result, "No categorical columns found in data")
                result.data = {
                    "categorical_columns": [],
                    "statistics": {},
                }
                result.quality_score = 0.5
                return result
            
            # Analyze each categorical column
            stats = {}
            errors_found = []
            warnings_found = []
            
            for col in categorical_cols:
                try:
                    value_counts = df[col].value_counts()
                    
                    col_stats = self._compute_statistics(col, df[col], value_counts)
                    stats[col] = col_stats
                    
                except Exception as e:
                    errors_found.append(f"Error analyzing column '{col}': {str(e)}")
                    self.logger.error(f"Error analyzing column {col}: {e}")
            
            # Add warnings
            for warning in warnings_found:
                self._add_warning(result, warning)
            
            # Add errors
            if errors_found:
                for error_msg in errors_found:
                    self._add_error(
                        result,
                        ErrorType.COMPUTATION_ERROR,
                        error_msg,
                        severity="warning"
                    )
            
            result.data = {
                "categorical_columns": categorical_cols,
                "statistics": stats,
                "columns_analyzed": len(stats),
            }
            
            # Quality score
            quality_score = 1.0
            quality_score -= (len(warnings_found) * 0.1)
            quality_score -= (len(errors_found) * 0.2)
            quality_score = max(0, min(1, quality_score))
            result.quality_score = quality_score
            
            self.logger.info(f"Analyzed {len(stats)} categorical columns")
            return result
        
        except Exception as e:
            self.logger.error(f"CategoricalAnalyzer failed: {e}")
            self._add_error(
                result,
                ErrorType.UNKNOWN_ERROR,
                str(e),
                severity="critical",
                suggestion="Check DataFrame structure and categorical column types"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _compute_statistics(self, col_name: str, series: pd.Series, value_counts: pd.Series) -> Dict[str, Any]:
        """Compute statistics for a categorical column.
        
        Args:
            col_name: Column name
            series: Series data
            value_counts: Value counts
            
        Returns:
            Dictionary of statistics
        """
        try:
            null_count = series.isna().sum()
            null_pct = (null_count / len(series) * 100) if len(series) > 0 else 0
            
            return {
                "count": int(len(series)),
                "unique_values": int(series.nunique()),
                "null_count": int(null_count),
                "null_percentage": round(null_pct, 2),
                "most_common": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "most_common_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                "most_common_percentage": round((value_counts.iloc[0] / len(series) * 100) if len(value_counts) > 0 else 0, 2),
                "least_common": str(value_counts.index[-1]) if len(value_counts) > 0 else None,
                "least_common_count": int(value_counts.iloc[-1]) if len(value_counts) > 0 else 0,
                "top_10_values": dict(value_counts.head(10).items()),
            }
        except Exception as e:
            self.logger.error(f"Error computing categorical statistics for {col_name}: {e}")
            raise
