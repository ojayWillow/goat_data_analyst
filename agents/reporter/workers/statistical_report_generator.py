"""StatisticalReportGenerator - Generates statistical analysis reports."""

import pandas as pd
import numpy as np
from typing import Any, Dict
from datetime import datetime, timezone
from .base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence


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
            task_type="statistical_report",
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
            
            report = {
                "report_type": "statistical_analysis",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "statistics": {},
                "correlation_analysis": {},
            }
            
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) > 0:
                # Basic statistics
                report["statistics"] = df[numeric_cols].describe().to_dict()
                
                # Correlation matrix
                if len(numeric_cols) > 1:
                    corr_matrix = df[numeric_cols].corr()
                    report["correlation_analysis"]["matrix"] = corr_matrix.to_dict()
                    
                    # High correlations
                    high_corr = []
                    for i in range(len(numeric_cols)):
                        for j in range(i+1, len(numeric_cols)):
                            corr_val = corr_matrix.iloc[i, j]
                            if abs(corr_val) > 0.7:
                                high_corr.append({
                                    "pair": (numeric_cols[i], numeric_cols[j]),
                                    "correlation": float(corr_val)
                                })
                    report["correlation_analysis"]["high_correlations"] = high_corr
            
            result.data = report
            self.logger.info(f"Statistical report generated for {len(numeric_cols)} numeric columns")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Generation failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
