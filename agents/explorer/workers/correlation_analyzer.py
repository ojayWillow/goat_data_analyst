"""CorrelationAnalyzer - Worker for analyzing correlations.

Analyzes correlations between numeric columns.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)


class CorrelationAnalyzer(BaseWorker):
    """Worker that analyzes correlations between columns."""
    
    def __init__(self):
        super().__init__("CorrelationAnalyzer")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs) -> WorkerResult:
        """Analyze correlations.
        
        Args:
            df: DataFrame to analyze
            threshold: Correlation threshold for strong correlations (default: 0.7)
            
        Returns:
            WorkerResult with correlation analysis
        """
        try:
            result = self._run_correlation_analysis(**kwargs)
            
            self.error_intelligence.track_success(
                agent_name="explorer",
                worker_name="CorrelationAnalyzer",
                operation="correlation_analysis",
                context={}
            )
            
            return result
            
        except Exception as e:
            self.error_intelligence.track_error(
                agent_name="explorer",
                worker_name="CorrelationAnalyzer",
                error_type=type(e).__name__,
                error_message=str(e),
                context={}
            )
            raise
    
    def _run_correlation_analysis(self, **kwargs) -> WorkerResult:
        """Perform correlation analysis."""
        df = kwargs.get('df')
        threshold = kwargs.get('threshold', 0.7)
        
        result = self._create_result(
            task_type="correlation_analysis",
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
            self.logger.info("Analyzing correlations...")
            
            # Select numeric columns
            numeric_data = df.select_dtypes(include=[np.number])
            
            if numeric_data.shape[1] < 2:
                self._add_warning(result, "Need at least 2 numeric columns for correlation analysis")
                result.data = {
                    "correlation_matrix": {},
                    "strong_correlations": [],
                    "columns": [],
                }
                result.quality_score = 0.5
                return result
            
            # Compute correlation matrix
            corr_matrix = numeric_data.corr().round(4)
            
            # Find strong correlations
            strong_corrs = self._find_strong_correlations(corr_matrix, threshold)
            
            result.data = {
                "correlation_matrix": corr_matrix.to_dict(),
                "strong_correlations": strong_corrs,
                "columns": corr_matrix.columns.tolist(),
                "correlation_count": len(strong_corrs),
                "threshold": threshold,
            }
            
            result.quality_score = 1.0
            self.logger.info(f"Found {len(strong_corrs)} strong correlations (threshold: {threshold})")
            return result
        
        except Exception as e:
            self.logger.error(f"CorrelationAnalyzer failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                suggestion="Check DataFrame has numeric columns without NaN"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    def _find_strong_correlations(self, corr_matrix: pd.DataFrame, threshold: float) -> List[Dict[str, Any]]:
        """Find strong correlations in the matrix.
        
        Args:
            corr_matrix: Correlation matrix
            threshold: Threshold for strong correlation
            
        Returns:
            List of strong correlations
        """
        strong_corrs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                
                if abs(corr_val) > threshold:
                    strong_corrs.append({
                        "column_1": corr_matrix.columns[i],
                        "column_2": corr_matrix.columns[j],
                        "correlation": float(corr_val),
                        "strength": self._rate_correlation_strength(abs(corr_val)),
                        "direction": "positive" if corr_val > 0 else "negative",
                    })
        
        # Sort by absolute correlation value
        strong_corrs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return strong_corrs
    
    @staticmethod
    def _rate_correlation_strength(abs_corr: float) -> str:
        """Rate the strength of correlation.
        
        Args:
            abs_corr: Absolute correlation value
            
        Returns:
            Strength rating
        """
        if abs_corr >= 0.9:
            return "very_strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        else:
            return "weak"
