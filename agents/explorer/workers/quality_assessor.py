"""QualityAssessor - Worker for assessing data quality.

Evaluates overall data quality including nulls, duplicates, and completeness.
"""

import pandas as pd
from typing import Any, Dict

from .base_worker import BaseWorker, WorkerResult, ErrorType
from core.logger import get_logger

logger = get_logger(__name__)


class QualityAssessor(BaseWorker):
    """Worker that assesses data quality."""
    
    def __init__(self):
        super().__init__("QualityAssessor")
    
    def execute(self, **kwargs) -> WorkerResult:
        """Assess data quality.
        
        Args:
            df: DataFrame to assess
            
        Returns:
            WorkerResult with quality metrics
        """
        return self.safe_execute(**kwargs)
    
    def execute(self, **kwargs) -> WorkerResult:
        """Perform data quality assessment."""
        df = kwargs.get('df')
        
        result = self._create_result(
            task_type="quality_assessment",
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
            self.logger.info("Assessing data quality...")
            
            # Calculate quality metrics
            total_cells = df.shape[0] * df.shape[1]
            null_cells = df.isnull().sum().sum()
            null_pct = (null_cells / total_cells * 100) if total_cells > 0 else 0
            
            duplicates = df.duplicated().sum()
            duplicate_pct = (duplicates / len(df) * 100) if len(df) > 0 else 0
            
            # Column-level quality
            column_quality = {}
            for col in df.columns:
                null_count = df[col].isnull().sum()
                null_pct_col = (null_count / len(df) * 100) if len(df) > 0 else 0
                column_quality[col] = {
                    "null_count": int(null_count),
                    "null_percentage": round(null_pct_col, 2),
                    "completeness": round(100 - null_pct_col, 2),
                }
            
            # Overall quality score (0-100)
            quality_score = 100 - null_pct - (duplicate_pct * 0.5)
            quality_score = max(0, min(100, quality_score))
            
            # Identify problematic columns
            problematic_cols = []
            for col, metrics in column_quality.items():
                if metrics['null_percentage'] > 30:  # More than 30% null
                    problematic_cols.append({
                        "column": col,
                        "null_percentage": metrics['null_percentage'],
                        "issue": "High null percentage"
                    })
            
            # Add warnings if needed
            if null_pct > 20:
                self._add_warning(result, f"Dataset has {null_pct:.2f}% null values")
            
            if duplicate_pct > 5:
                self._add_warning(result, f"Dataset has {duplicate_pct:.2f}% duplicate rows")
            
            if problematic_cols:
                self._add_warning(result, f"Found {len(problematic_cols)} columns with high null percentage")
            
            result.data = {
                "overall_quality_score": round(quality_score, 2),
                "quality_rating": self._rate_quality(quality_score),
                "total_cells": total_cells,
                "null_cells": null_cells,
                "null_percentage": round(null_pct, 2),
                "total_rows": df.shape[0],
                "total_columns": df.shape[1],
                "duplicate_rows": int(duplicates),
                "duplicate_percentage": round(duplicate_pct, 2),
                "complete_rows": int(len(df) - duplicates),
                "column_quality": column_quality,
                "problematic_columns": problematic_cols,
            }
            
            # Quality score normalized to 0-1
            normalized_quality = quality_score / 100
            result.quality_score = normalized_quality
            
            self.logger.info(f"Data quality assessment complete. Score: {quality_score:.2f}")
            return result
        
        except Exception as e:
            self.logger.error(f"QualityAssessor failed: {e}")
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                suggestion="Check DataFrame structure and data types"
            )
            result.success = False
            result.quality_score = 0
            return result
    
    @staticmethod
    def _rate_quality(score: float) -> str:
        """Rate data quality based on score.
        
        Args:
            score: Quality score (0-100)
            
        Returns:
            Quality rating
        """
        if score >= 95:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Very Poor"
