"""ExecutiveSummaryGenerator - Generates executive summary reports.

Enhanced with:
- Advanced quality assessment
- Data consistency checks
- Actionable recommendations
- Detailed quality metrics
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List
from datetime import datetime, timezone
from .base_worker import BaseWorker, WorkerResult, ErrorType, ValidationUtils
from agents.error_intelligence.main import ErrorIntelligence


class ExecutiveSummaryGenerator(BaseWorker):
    """Generates comprehensive executive summary reports.
    
    Provides:
    - Dataset overview
    - Data quality assessment with recommendations
    - Data completeness analysis
    - Data consistency metrics
    """
    
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
            # Validate input
            is_valid, error_msg = ValidationUtils.validate_dataframe(df)
            if not is_valid:
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    error_msg,
                    severity="error",
                    suggestion="Provide a non-empty DataFrame with at least 1 row and 1 column"
                )
                result.success = False
                return result
            
            # Get quality metrics
            metrics = ValidationUtils.get_data_quality_metrics(df)
            rows = metrics["rows"]
            cols = metrics["columns"]
            null_pct = metrics["null_percentage"]
            duplicates = metrics["duplicate_count"]
            
            # Analyze data types
            numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
            categorical_cols = len(df.select_dtypes(include=['object']).columns)
            date_cols = len(df.select_dtypes(include=['datetime64']).columns)
            
            # Advanced quality assessment
            quality_rating, quality_score = self._assess_quality(
                null_pct=null_pct,
                duplicates=duplicates,
                duplicate_pct=metrics["duplicate_percentage"],
                rows=rows
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                null_pct=null_pct,
                duplicates=duplicates,
                quality_rating=quality_rating,
                rows=rows,
                cols=cols
            )
            
            # Check consistency
            consistency_issues = self._check_consistency(df)
            
            summary = {
                "report_type": "executive_summary",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "dataset_info": {
                    "rows": rows,
                    "columns": cols,
                    "numeric_columns": numeric_cols,
                    "categorical_columns": categorical_cols,
                    "date_columns": date_cols,
                    "total_cells": metrics["total_cells"],
                    "memory_mb": metrics["memory_mb"],
                },
                "data_quality": {
                    "overall_rating": quality_rating,
                    "quality_score": round(quality_score, 3),
                    "null_percentage": metrics["null_percentage"],
                    "null_count": metrics["null_count"],
                    "duplicate_count": metrics["duplicate_count"],
                    "duplicate_percentage": metrics["duplicate_percentage"],
                    "completeness_score": round(100 - null_pct, 2),
                    "uniqueness_score": round(100 - metrics["duplicate_percentage"], 2),
                },
                "consistency": {
                    "issues_found": len(consistency_issues),
                    "issues": consistency_issues[:5],  # Top 5 issues
                },
                "recommendations": recommendations,
                "summary_statement": self._generate_summary_statement(
                    rows=rows,
                    cols=cols,
                    quality_rating=quality_rating,
                    null_pct=null_pct,
                    duplicates=duplicates
                ),
            }
            
            result.data = summary
            result.quality_score = quality_score
            result.rows_processed = rows
            
            self.logger.info(f"Executive summary generated: {rows} rows, {cols} columns, rating: {quality_rating}")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Generation failed: {str(e)}",
                severity="error",
                details={"exception_type": type(e).__name__}
            )
            result.success = False
        
        return result
    
    def _assess_quality(
        self,
        null_pct: float,
        duplicates: int,
        duplicate_pct: float,
        rows: int
    ) -> tuple[str, float]:
        """Assess data quality with scoring.
        
        Args:
            null_pct: Percentage of null values
            duplicates: Count of duplicate rows
            duplicate_pct: Percentage of duplicate rows
            rows: Total rows
            
        Returns:
            Tuple of (rating, score)
        """
        score = 1.0
        
        # Deduct for nulls
        if null_pct > 0:
            score -= (null_pct / 100) * 0.3
        
        # Deduct for duplicates
        if duplicate_pct > 0:
            score -= (duplicate_pct / 100) * 0.3
        
        # Deduct for small sample size
        if rows < 100:
            score -= 0.1
        
        # Ensure score is in valid range
        score = max(0, min(1, score))
        
        # Determine rating
        if score >= 0.95:
            rating = "Excellent"
        elif score >= 0.85:
            rating = "Very Good"
        elif score >= 0.70:
            rating = "Good"
        elif score >= 0.50:
            rating = "Fair"
        else:
            rating = "Poor"
        
        return rating, score
    
    def _generate_recommendations(self,
                                   null_pct: float,
                                   duplicates: int,
                                   quality_rating: str,
                                   rows: int,
                                   cols: int) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if null_pct > 20:
            recommendations.append(f"Address {null_pct:.1f}% missing values using imputation or removal strategies")
        
        if null_pct > 10:
            recommendations.append("Consider investigating missing value patterns and causes")
        
        if duplicates > rows * 0.05:  # > 5% duplicates
            recommendations.append(f"Investigate {duplicates} duplicate rows and remove if necessary")
        
        if quality_rating in ["Fair", "Poor"]:
            recommendations.append("Conduct data cleaning and validation before analysis")
        
        if rows < 100:
            recommendations.append(f"Current sample size ({rows}) may be too small for statistical significance")
        
        if cols < 3:
            recommendations.append("Dataset has limited dimensions; consider feature engineering")
        
        if not recommendations:
            recommendations.append("Data appears clean and ready for analysis")
        
        return recommendations
    
    def _check_consistency(self, df: pd.DataFrame) -> List[str]:
        """Check for data consistency issues."""
        issues = []
        
        # Check for empty strings in object columns
        for col in df.select_dtypes(include=['object']).columns:
            empty_strings = (df[col] == "").sum()
            if empty_strings > 0:
                issues.append(f"Column '{col}' has {empty_strings} empty strings")
        
        # Check for whitespace-only values
        for col in df.select_dtypes(include=['object']).columns:
            whitespace_only = df[col].apply(lambda x: isinstance(x, str) and x.strip() == "").sum()
            if whitespace_only > 0:
                issues.append(f"Column '{col}' has {whitespace_only} whitespace-only values")
        
        # Check for inconsistent types in numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                if df[col].isnull().sum() > df[col].shape[0] * 0.5:
                    issues.append(f"Column '{col}' is >50% null (possible type mismatch)")
        
        return issues
    
    def _generate_summary_statement(self,
                                    rows: int,
                                    cols: int,
                                    quality_rating: str,
                                    null_pct: float,
                                    duplicates: int) -> str:
        """Generate human-readable summary statement."""
        return (
            f"Dataset contains {rows:,} rows and {cols} columns with {quality_rating} data quality. "
            f"{null_pct:.1f}% missing values and {duplicates} duplicate rows detected. "
            f"Suitable for {('basic' if quality_rating in ['Fair', 'Poor'] else 'advanced')} analysis."
        )
