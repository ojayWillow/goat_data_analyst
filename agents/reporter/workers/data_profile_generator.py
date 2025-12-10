"""DataProfileGenerator - Generates detailed data profile reports."""

import pandas as pd
import numpy as np
from typing import Any, Dict
from datetime import datetime, timezone
from .base_worker import BaseWorker, WorkerResult, ErrorType


class DataProfileGenerator(BaseWorker):
    """Generates detailed data profile reports."""
    
    def __init__(self):
        super().__init__("data_profile_generator")
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Generate data profile.
        
        Args:
            df: DataFrame to profile
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with data profile
        """
        result = self._create_result(
            success=True,
            task_type="data_profile",
            data={}
        )
        
        try:
            if df is None or df.empty:
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    "DataFrame is empty or None",
                    severity="error"
                )
                return result
            
            profile = {
                "report_type": "data_profile",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "columns": {},
            }
            
            for col in df.columns:
                dtype = str(df[col].dtype)
                null_count = df[col].isnull().sum()
                null_pct = (null_count / len(df) * 100) if len(df) > 0 else 0
                unique = df[col].nunique()
                
                col_info = {
                    "data_type": dtype,
                    "missing_values": int(null_count),
                    "missing_percentage": round(null_pct, 2),
                    "unique_values": unique,
                    "completeness": round(100 - null_pct, 2),
                }
                
                # Add type-specific statistics
                if df[col].dtype in [np.int64, np.float64, np.int32, np.float32]:
                    series = df[col].dropna()
                    col_info["statistics"] = {
                        "mean": float(series.mean()) if len(series) > 0 else None,
                        "median": float(series.median()) if len(series) > 0 else None,
                        "std": float(series.std()) if len(series) > 0 else None,
                        "min": float(series.min()) if len(series) > 0 else None,
                        "max": float(series.max()) if len(series) > 0 else None,
                    }
                else:
                    top_values = df[col].value_counts().head(3)
                    col_info["top_values"] = dict(top_values.items())
                
                profile["columns"][col] = col_info
            
            result.data = profile
            self.logger.info(f"Data profile generated for {len(df.columns)} columns")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Generation failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
