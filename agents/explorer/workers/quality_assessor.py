"""QualityAssessor - Worker for assessing overall data quality.

Evaluates data quality including null values, duplicates, and completeness.
Provides comprehensive quality metrics and identifies problematic columns.
"""

from typing import Any, Dict, Optional, List
import pandas as pd

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from core.logger import get_logger
from agents.error_intelligence.main import ErrorIntelligence

logger = get_logger(__name__)

# Constants
NULL_WARNING_THRESHOLD = 0.20  # Warn if more than 20% nulls
DUPLICATE_WARNING_THRESHOLD = 0.05  # Warn if more than 5% duplicates
PROBLEMATIC_NULL_THRESHOLD = 0.30  # Mark column as problematic if >30% null
QUALITY_EXCELLENT = 95  # >= 95 is excellent
QUALITY_GOOD = 80  # >= 80 is good
QUALITY_FAIR = 60  # >= 60 is fair
QUALITY_POOR = 40  # >= 40 is poor


class QualityAssessor(BaseWorker):
    """Worker that assesses overall data quality.
    
    Evaluates data quality across multiple dimensions:
    - Null/missing value analysis
    - Duplicate row detection
    - Column-level completeness
    - Problematic column identification
    - Overall quality score
    
    Input Requirements:
        df: pandas.DataFrame - DataFrame to assess (required)
    
    Output Format:
        result.data contains:
            overall_quality_score: Overall quality (0-100 scale)
            quality_rating: Human-readable rating (Excellent, Good, Fair, Poor, Very Poor)
            null_cells: Total null cells
            null_percentage: Percentage of null cells
            duplicate_rows: Number of duplicate rows
            duplicate_percentage: Percentage of duplicates
            complete_rows: Number of rows without any nulls
            column_quality: Dict with per-column metrics
            problematic_columns: List of columns with issues
    
    Quality Score:
        Calculated as:
        - Base: 100 - null_percentage - (duplicate_percentage * 0.5)
        - Clamped: 0-100
        - Normalized: 0-1 for quality_score
    
    Quality Ratings:
        - Excellent: >= 95
        - Good: >= 80
        - Fair: >= 60
        - Poor: >= 40
        - Very Poor: < 40
    
    Example:
        >>> assessor = QualityAssessor()
        >>> result = assessor.safe_execute(df=df)
        >>> if result.success:
        ...     print(f"Quality: {result.data['quality_rating']}")
        ...     print(f"Score: {result.data['overall_quality_score']}")
    
    Raises:
        None (all errors returned in WorkerResult)
    """
    
    def __init__(self) -> None:
        """Initialize QualityAssessor worker."""
        super().__init__("QualityAssessor")
        self.error_intelligence = ErrorIntelligence()
    
    def _validate_input(self, **kwargs: Any) -> Optional[WorkerError]:
        """Validate input parameters.
        
        Args:
            **kwargs: Must contain 'df' key with DataFrame value
            
        Returns:
            WorkerError if validation fails, None if valid
        """
        df = kwargs.get('df')
        
        if df is None:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="No DataFrame provided (df=None)",
                severity="error",
                suggestion="Call with df parameter: assessor.safe_execute(df=your_dataframe)"
            )
        
        if not isinstance(df, pd.DataFrame):
            return WorkerError(
                error_type=ErrorType.TYPE_ERROR,
                message=f"Expected DataFrame, got {type(df).__name__}",
                severity="error",
                details={"received_type": str(type(df))},
                suggestion="Pass a pandas DataFrame as the df parameter"
            )
        
        if df.empty:
            return WorkerError(
                error_type=ErrorType.MISSING_DATA,
                message="DataFrame is empty (0 rows)",
                severity="error",
                details={"shape": str(df.shape)},
                suggestion="Ensure DataFrame has data before assessment"
            )
        
        return None
    
    def execute(self, **kwargs: Any) -> WorkerResult:
        """Assess data quality in DataFrame.
        
        Args:
            df: DataFrame to assess
            
        Returns:
            WorkerResult with quality metrics
            
        Note:
            NEVER raises exceptions. All errors returned in WorkerResult.
        """
        # Note: validate_input() already checked in safe_execute()
        df = kwargs.get('df')
        
        result = self._create_result(
            task_type="quality_assessment",
            quality_score=1.0
        )
        
        try:
            self.logger.info(
                f"Assessing data quality for {df.shape[0]} rows, {df.shape[1]} columns"
            )
            
            # Calculate quality metrics
            total_cells = df.shape[0] * df.shape[1]
            null_cells = df.isnull().sum().sum()
            null_pct = (null_cells / total_cells * 100) if total_cells > 0 else 0
            
            duplicates = df.duplicated().sum()
            duplicate_pct = (duplicates / len(df) * 100) if len(df) > 0 else 0
            
            # Column-level quality analysis
            column_quality = self._assess_column_quality(df)
            
            # Calculate overall quality score (0-100)
            quality_score = 100 - null_pct - (duplicate_pct * 0.5)
            quality_score = max(0, min(100, quality_score))
            
            # Identify problematic columns
            problematic_cols = self._identify_problematic_columns(
                column_quality,
                PROBLEMATIC_NULL_THRESHOLD
            )
            
            # Add warnings if needed
            warnings_list: List[str] = []
            
            if null_pct > (NULL_WARNING_THRESHOLD * 100):
                warnings_list.append(
                    f"Dataset has {null_pct:.2f}% null values (threshold: {NULL_WARNING_THRESHOLD * 100}%)"
                )
            
            if duplicate_pct > (DUPLICATE_WARNING_THRESHOLD * 100):
                warnings_list.append(
                    f"Dataset has {duplicate_pct:.2f}% duplicate rows (threshold: {DUPLICATE_WARNING_THRESHOLD * 100}%)"
                )
            
            if problematic_cols:
                warnings_list.append(
                    f"Found {len(problematic_cols)} columns with high null percentage "
                    f"(threshold: {PROBLEMATIC_NULL_THRESHOLD * 100}%)"
                )
            
            # Add all warnings to result
            for warning in warnings_list:
                self._add_warning(result, warning)
            
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
                "warning_count": len(warnings_list),
            }
            
            # Quality score normalized to 0-1 for result
            normalized_quality = quality_score / 100
            result.quality_score = normalized_quality
            result.success = True
            
            self.logger.info(
                f"Quality assessment complete. Score: {quality_score:.2f} "
                f"({self._rate_quality(quality_score)})"
            )
            
            return result
        
        except Exception as e:
            """Catch unexpected exceptions.
            
            Should not happen if code is correct, but safety net ensures
            WorkerResult is always returned.
            """
            self.logger.error(f"QualityAssessor execute() failed: {e}", exc_info=True)
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                str(e),
                severity="critical",
                details={
                    "error_type": type(e).__name__,
                    "shape": str(df.shape)
                },
                suggestion="Check DataFrame structure and column values"
            )
            result.success = False
            result.quality_score = 0.0
            
            return result
    
    def _assess_column_quality(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Assess quality of individual columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary mapping column names to quality metrics
        """
        column_quality: Dict[str, Dict[str, Any]] = {}
        
        for col in df.columns:
            try:
                null_count = df[col].isnull().sum()
                null_pct_col = (null_count / len(df) * 100) if len(df) > 0 else 0
                
                column_quality[col] = {
                    "null_count": int(null_count),
                    "null_percentage": round(null_pct_col, 2),
                    "completeness": round(100 - null_pct_col, 2),
                    "data_type": str(df[col].dtype),
                    "unique_values": int(df[col].nunique()),
                }
            except Exception as e:
                self.logger.warning(f"Error assessing column '{col}': {e}")
                column_quality[col] = {
                    "null_count": 0,
                    "null_percentage": 0.0,
                    "completeness": 0.0,
                    "data_type": "unknown",
                    "unique_values": 0,
                    "assessment_error": str(e),
                }
        
        return column_quality
    
    def _identify_problematic_columns(
        self,
        column_quality: Dict[str, Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Identify columns with quality issues.
        
        Args:
            column_quality: Column quality dictionary
            threshold: Null percentage threshold (0-1)
            
        Returns:
            List of problematic column dicts
        """
        problematic: List[Dict[str, Any]] = []
        
        for col_name, metrics in column_quality.items():
            null_pct = metrics.get('null_percentage', 0) / 100  # Convert to decimal
            
            if null_pct > threshold:
                problematic.append({
                    "column": col_name,
                    "null_percentage": metrics.get('null_percentage', 0),
                    "issue": f"High null percentage (>{threshold * 100:.0f}%)",
                    "severity": "high" if null_pct > 0.5 else "medium",
                })
        
        return problematic
    
    @staticmethod
    def _rate_quality(score: float) -> str:
        """Rate data quality based on score.
        
        Args:
            score: Quality score (0-100 scale)
            
        Returns:
            Human-readable quality rating
            
        Ratings:
            Excellent: >= 95
            Good: >= 80
            Fair: >= 60
            Poor: >= 40
            Very Poor: < 40
        """
        if score >= QUALITY_EXCELLENT:
            return "Excellent"
        elif score >= QUALITY_GOOD:
            return "Good"
        elif score >= QUALITY_FAIR:
            return "Fair"
        elif score >= QUALITY_POOR:
            return "Poor"
        else:
            return "Very Poor"
