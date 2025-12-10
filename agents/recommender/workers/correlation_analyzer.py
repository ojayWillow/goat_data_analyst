"""CorrelationAnalyzer - Analyzes feature correlations and provides feature engineering recommendations."""

import pandas as pd
import numpy as np
from typing import Any, Dict
from .base_worker import BaseWorker, WorkerResult, ErrorType


class CorrelationAnalyzer(BaseWorker):
    """Analyzes correlations and recommends feature engineering actions."""
    
    def __init__(self):
        super().__init__("correlation_analyzer")
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Analyze correlations and generate recommendations.
        
        Args:
            df: DataFrame to analyze
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with insights and recommendations
        """
        result = self._create_result(
            success=True,
            task_type="correlation_analysis",
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
            
            if numeric_data.shape[1] < 2:
                result.data = {
                    "status": "insufficient_data",
                    "message": "Need at least 2 numeric columns",
                    "insights": [],
                    "recommendations": [],
                }
                return result
            
            corr_matrix = numeric_data.corr()
            insights = []
            recommendations = []
            strong_corrs = []
            
            # Find strong correlations
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        strong_corrs.append({
                            "col1": corr_matrix.columns[i],
                            "col2": corr_matrix.columns[j],
                            "correlation": float(corr_val),
                        })
            
            if len(strong_corrs) > 0:
                insight = {
                    "type": "info",
                    "message": f"Found {len(strong_corrs)} strong correlations (|r| > 0.7)",
                    "severity": "low"
                }
                insights.append(insight)
                
                # Check for multicollinearity
                if len(strong_corrs) > 3:
                    recommendations.append({
                        "action": "feature_engineering",
                        "suggestion": "Consider removing highly correlated features to reduce multicollinearity"
                    })
                
                for corr in strong_corrs[:5]:  # Show top 5
                    insight = {
                        "type": "info",
                        "message": f"'{corr['col1']}' and '{corr['col2']}' strongly correlated ({corr['correlation']:.2f})",
                        "severity": "low"
                    }
                    insights.append(insight)
            else:
                insight = {
                    "type": "positive",
                    "message": "No strong correlations detected - features are independent",
                    "severity": "low"
                }
                insights.append(insight)
            
            result.data = {
                "strong_correlations": len(strong_corrs),
                "top_correlations": strong_corrs[:5],
                "columns_analyzed": numeric_data.shape[1],
                "insights": insights,
                "recommendations": recommendations,
            }
            
            self.logger.info(f"Correlation analysis: {len(strong_corrs)} strong correlations found")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Analysis failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
