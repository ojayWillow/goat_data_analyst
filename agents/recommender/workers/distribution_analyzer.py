"""DistributionAnalyzer - Analyzes data distributions and provides transformation recommendations."""

import pandas as pd
import numpy as np
from typing import Any, Dict
from .base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence


class DistributionAnalyzer(BaseWorker):
    """Analyzes numeric distributions and recommends transformations."""
    
    def __init__(self):
        super().__init__("distribution_analyzer")
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Analyze distributions and generate recommendations.
        
        Args:
            df: DataFrame to analyze
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with insights and recommendations
        """
        result = self._create_result(
            success=True,
            task_type="distribution_analysis",
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
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            insights = []
            recommendations = []
            skewed_cols = []
            kurtosis_cols = []
            
            for col in numeric_cols:
                series = df[col].dropna()
                if len(series) < 3:
                    continue
                
                skewness = series.skew()
                kurtosis = series.kurtosis()
                
                # Check for skewness
                if abs(skewness) > 1:
                    direction = "right" if skewness > 0 else "left"
                    insight = {
                        "type": "info",
                        "message": f"'{col}' has strong {direction} skew ({skewness:.2f})",
                        "severity": "low",
                        "column": col
                    }
                    insights.append(insight)
                    skewed_cols.append(col)
                    recommendations.append({
                        "action": "transformation",
                        "target": col,
                        "suggestion": f"Consider log or Box-Cox transformation for '{col}'"
                    })
                
                # Check for heavy tails
                if kurtosis > 3:
                    insight = {
                        "type": "warning",
                        "message": f"'{col}' has heavy tails (high kurtosis: {kurtosis:.2f})",
                        "severity": "medium",
                        "column": col
                    }
                    insights.append(insight)
                    kurtosis_cols.append(col)
                    recommendations.append({
                        "action": "outlier_handling",
                        "target": col,
                        "suggestion": f"Investigate outliers in '{col}'"
                    })
            
            if len(insights) == 0:
                insights.append({
                    "type": "positive",
                    "message": "All distributions appear normal",
                    "severity": "low"
                })
            
            result.data = {
                "columns_analyzed": len(numeric_cols),
                "skewed_columns": skewed_cols,
                "kurtosis_columns": kurtosis_cols,
                "insights": insights,
                "recommendations": recommendations,
            }
            
            self.logger.info(f"Distribution analysis: {len(numeric_cols)} columns analyzed")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Analysis failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
