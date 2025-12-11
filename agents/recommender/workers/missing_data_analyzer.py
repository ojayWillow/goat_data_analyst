"""MissingDataAnalyzer - Analyzes missing data and provides recommendations."""

import pandas as pd
from typing import Any, Dict, Optional
from .base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence


class MissingDataAnalyzer(BaseWorker):
    """Analyzes missing data patterns and recommends cleanup actions."""
    
    def __init__(self):
        super().__init__("missing_data_analyzer")
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Analyze missing data and generate recommendations.
        
        Args:
            df: DataFrame to analyze
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with insights and recommendations
        """
        result = self._create_result(
            success=True,
            task_type="missing_data_analysis",
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
            
            total_cells = df.shape[0] * df.shape[1]
            null_cells = df.isnull().sum().sum()
            null_pct = (null_cells / total_cells * 100) if total_cells > 0 else 0
            
            insights = []
            recommendations = []
            
            # Check for columns with high null percentage
            null_by_col = df.isnull().sum() / len(df) * 100
            high_null_cols = null_by_col[null_by_col > 50]
            
            if len(high_null_cols) > 0:
                insight = {
                    "type": "warning",
                    "message": f"Found {len(high_null_cols)} columns with >50% missing data",
                    "severity": "high"
                }
                insights.append(insight)
                
                for col, pct in high_null_cols.items():
                    rec = {
                        "action": "data_cleaning",
                        "target": col,
                        "suggestion": f"Consider removing '{col}' ({pct:.1f}% missing) or imputing values"
                    }
                    recommendations.append(rec)
            
            # Overall null percentage
            if null_pct > 20:
                insight = {
                    "type": "warning",
                    "message": f"Dataset has {null_pct:.1f}% missing values overall",
                    "severity": "medium"
                }
                insights.append(insight)
                recommendations.append({
                    "action": "imputation",
                    "suggestion": "Consider imputation strategy (mean, median, forward-fill)"
                })
            elif null_pct == 0:
                insight = {
                    "type": "positive",
                    "message": "No missing values detected - excellent data quality",
                    "severity": "low"
                }
                insights.append(insight)
            
            result.data = {
                "null_percentage": round(null_pct, 2),
                "null_cells": int(null_cells),
                "total_cells": int(total_cells),
                "high_null_columns": len(high_null_cols),
                "insights": insights,
                "recommendations": recommendations,
            }
            
            self.logger.info(f"Missing data analysis: {null_pct:.2f}% null")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Analysis failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
