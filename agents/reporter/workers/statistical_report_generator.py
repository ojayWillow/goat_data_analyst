"""StatisticalReportGenerator - Generates statistical analysis reports."""

import pandas as pd
import numpy as np
from typing import Any, Dict
from datetime import datetime
from .base_worker import BaseWorker, WorkerResult, ErrorType


class StatisticalReportGenerator(BaseWorker):
    """Generates statistical analysis reports."""
    
    def __init__(self):
        super().__init__("statistical_report_generator")
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Generate statistical report.
        
        Args:
            df: DataFrame to analyze
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with statistical analysis
        """
        result = self._create_result(
            success=True,
            task_type="statistical_analysis",
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
            
            numeric_data = df.select_dtypes(include=[np.number])
            
            report = {
                "report_type": "statistical_analysis",
                "generated_at": datetime.utcnow().isoformat(),
                "summary_statistics": numeric_data.describe().round(2).to_dict(),
                "correlation_analysis": {},
            }
            
            # Correlation analysis
            if numeric_data.shape[1] >= 2:
                corr_matrix = numeric_data.corr()
                report["correlation_analysis"] = {
                    "matrix": corr_matrix.round(3).to_dict(),
                    "strong_correlations": [],
                }
                
                # Find strong correlations
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            report["correlation_analysis"]["strong_correlations"].append({
                                "col1": corr_matrix.columns[i],
                                "col2": corr_matrix.columns[j],
                                "correlation": float(corr_val),
                            })
            
            result.data = report
            self.logger.info(f"Statistical report generated for {numeric_data.shape[1]} numeric columns")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Generation failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
