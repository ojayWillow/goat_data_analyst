"""DuplicateAnalyzer - Analyzes duplicate data and provides recommendations."""

import pandas as pd
import numpy as np
from typing import Any, Dict
from .base_worker import BaseWorker, WorkerResult, ErrorType
from agents.error_intelligence.main import ErrorIntelligence


class DuplicateAnalyzer(BaseWorker):
    """Analyzes duplicate records and recommends deduplication actions."""
    
    def __init__(self):
        super().__init__("duplicate_analyzer")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Analyze duplicates and generate recommendations.
        
        Args:
            df: DataFrame to analyze
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with insights and recommendations
        """
        result = self._create_result(
            success=True,
            task_type="duplicate_analysis",
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
                self.error_intelligence.track_error(
                    agent_name="recommender",
                    worker_name="DuplicateAnalyzer",
                    operation="analyze_duplicates",
                    error_type="DataValidationError",
                    error_message="DataFrame is empty or None"
                )
                return result
            
            duplicates = df.duplicated().sum()
            duplicate_pct = (duplicates / len(df) * 100) if len(df) > 0 else 0
            
            insights = []
            recommendations = []
            
            if duplicates > 0:
                insight = {
                    "type": "warning",
                    "message": f"Found {duplicates:,} duplicate rows ({duplicate_pct:.2f}%)",
                    "severity": "medium"
                }
                insights.append(insight)
                
                rec = {
                    "action": "deduplication",
                    "suggestion": f"Remove {duplicates:,} duplicate rows to clean dataset"
                }
                recommendations.append(rec)
            else:
                insight = {
                    "type": "positive",
                    "message": "No duplicate rows detected",
                    "severity": "low"
                }
                insights.append(insight)
            
            # Check for partial duplicates
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                partial_dup = df[numeric_cols].duplicated().sum()
                if partial_dup > 0:
                    insight = {
                        "type": "info",
                        "message": f"Found {partial_dup:,} partial duplicates (numeric columns only)",
                        "severity": "low"
                    }
                    insights.append(insight)
            
            result.data = {
                "duplicate_count": int(duplicates),
                "duplicate_percentage": round(duplicate_pct, 2),
                "total_rows": len(df),
                "insights": insights,
                "recommendations": recommendations,
            }
            
            self.logger.info(f"Duplicate analysis: {duplicates} duplicates found")
            self.error_intelligence.track_success(
                agent_name="recommender",
                worker_name="DuplicateAnalyzer",
                operation="analyze_duplicates"
            )
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Analysis failed: {str(e)}",
                severity="error"
            )
            result.success = False
            self.error_intelligence.track_error(
                agent_name="recommender",
                worker_name="DuplicateAnalyzer",
                operation="analyze_duplicates",
                error_type=type(e).__name__,
                error_message=str(e)
            )
        
        return result
