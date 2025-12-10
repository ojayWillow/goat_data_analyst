"""ExecutiveSummaryGenerator - Generates executive summary reports."""

import pandas as pd
import numpy as np
from typing import Any, Dict
from datetime import datetime
from .base_worker import BaseWorker, WorkerResult, ErrorType


class ExecutiveSummaryGenerator(BaseWorker):
    """Generates executive summary reports."""
    
    def __init__(self):
        super().__init__("executive_summary_generator")
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Generate executive summary.
        
        Args:
            df: DataFrame to summarize
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with executive summary
        """
        result = self._create_result(
            success=True,
            task_type="executive_summary",
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
            
            rows, cols = df.shape
            null_pct = (df.isnull().sum().sum() / (rows * cols) * 100) if (rows * cols) > 0 else 0
            duplicates = df.duplicated().sum()
            numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
            categorical_cols = len(df.select_dtypes(include=['object']).columns)
            
            # Quality rating
            if null_pct == 0 and duplicates == 0:
                quality = "Excellent"
            elif null_pct < 5 and duplicates < 1:
                quality = "Good"
            elif null_pct < 20 and duplicates < 5:
                quality = "Fair"
            else:
                quality = "Poor"
            
            summary = {
                "report_type": "executive_summary",
                "generated_at": datetime.utcnow().isoformat(),
                "dataset_info": {
                    "rows": rows,
                    "columns": cols,
                    "numeric_columns": numeric_cols,
                    "categorical_columns": categorical_cols,
                    "total_cells": rows * cols,
                },
                "data_quality": {
                    "quality_rating": quality,
                    "null_percentage": round(null_pct, 2),
                    "duplicate_count": int(duplicates),
                    "duplicate_percentage": round((duplicates / rows * 100) if rows > 0 else 0, 2),
                },
                "summary_statement": f"Dataset contains {rows:,} rows and {cols} columns with {quality} data quality.",
            }
            
            result.data = summary
            self.logger.info(f"Executive summary generated for {rows} rows, {cols} columns")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Generation failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
