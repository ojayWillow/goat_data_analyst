"""Advanced Quality Score Calculator for Data Quality Assessment.

Calculates quality scores based on:
1. Null/Missing Data (40% weight)
2. Duplicate Rows (20% weight)
3. Column Type Consistency (15% weight)
4. Statistical Outliers (15% weight)
5. Memory Efficiency (10% weight)

Formula:
quality_score = (
    (1 - null_pct/100) * 0.40 +
    (1 - duplicate_pct/100) * 0.20 +
    type_consistency * 0.15 +
    (1 - outlier_pct/100) * 0.15 +
    memory_efficiency * 0.10
)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


class QualityScoreCalculator:
    """Calculate comprehensive data quality scores."""

    @staticmethod
    def calculate(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """Calculate quality score and detailed metrics.
        
        Args:
            df: DataFrame to assess
            
        Returns:
            (quality_score, detailed_metrics)
        """
        if df.empty:
            return 0.0, {"error": "Empty DataFrame"}

        metrics = {}

        # 1. Null/Missing Data (40% weight)
        null_score, null_metrics = QualityScoreCalculator._calculate_null_score(df)
        metrics['null_score'] = null_score
        metrics.update(null_metrics)

        # 2. Duplicate Rows (20% weight)
        duplicate_score, duplicate_metrics = QualityScoreCalculator._calculate_duplicate_score(df)
        metrics['duplicate_score'] = duplicate_score
        metrics.update(duplicate_metrics)

        # 3. Column Type Consistency (15% weight)
        type_score, type_metrics = QualityScoreCalculator._calculate_type_consistency_score(df)
        metrics['type_consistency_score'] = type_score
        metrics.update(type_metrics)

        # 4. Statistical Outliers (15% weight)
        outlier_score, outlier_metrics = QualityScoreCalculator._calculate_outlier_score(df)
        metrics['outlier_score'] = outlier_score
        metrics.update(outlier_metrics)

        # 5. Memory Efficiency (10% weight)
        memory_score, memory_metrics = QualityScoreCalculator._calculate_memory_score(df)
        metrics['memory_score'] = memory_score
        metrics.update(memory_metrics)

        # Weighted quality score
        quality_score = (
            null_score * 0.40 +
            duplicate_score * 0.20 +
            type_score * 0.15 +
            outlier_score * 0.15 +
            memory_score * 0.10
        )

        # Ensure 0-1 range
        quality_score = max(0.0, min(1.0, quality_score))

        metrics['overall_quality_score'] = quality_score
        metrics['score_components'] = {
            'null_handling': {'score': null_score, 'weight': 0.40},
            'duplicate_handling': {'score': duplicate_score, 'weight': 0.20},
            'type_consistency': {'score': type_score, 'weight': 0.15},
            'outlier_handling': {'score': outlier_score, 'weight': 0.15},
            'memory_efficiency': {'score': memory_score, 'weight': 0.10}
        }

        return quality_score, metrics

    @staticmethod
    def _calculate_null_score(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """Calculate null value score (40% weight).
        
        Perfect: No nulls = 1.0
        Good: < 5% = 0.95
        Acceptable: 5-10% = 0.80
        Poor: 10-20% = 0.50
        Bad: > 20% = 0.0
        """
        null_count = df.isnull().sum().sum()
        total_cells = df.shape[0] * df.shape[1]
        null_pct = (null_count / total_cells * 100) if total_cells > 0 else 0.0

        if null_pct == 0:
            score = 1.0
        elif null_pct <= 5:
            score = 0.95
        elif null_pct <= 10:
            score = 0.80
        elif null_pct <= 20:
            score = 0.50
        else:
            score = max(0.0, 1.0 - (null_pct / 100))

        return score, {
            'null_pct': null_pct,
            'null_count': int(null_count),
            'total_cells': total_cells
        }

    @staticmethod
    def _calculate_duplicate_score(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """Calculate duplicate row score (20% weight).
        
        Perfect: No duplicates = 1.0
        Good: < 2% = 0.95
        Acceptable: 2-5% = 0.85
        Poor: 5-10% = 0.60
        Bad: > 10% = 0.0
        """
        total_rows = len(df)
        duplicate_rows = df.duplicated().sum()
        duplicate_pct = (duplicate_rows / total_rows * 100) if total_rows > 0 else 0.0

        if duplicate_pct == 0:
            score = 1.0
        elif duplicate_pct <= 2:
            score = 0.95
        elif duplicate_pct <= 5:
            score = 0.85
        elif duplicate_pct <= 10:
            score = 0.60
        else:
            score = max(0.0, 1.0 - (duplicate_pct / 100))

        return score, {
            'duplicate_pct': duplicate_pct,
            'duplicate_rows': int(duplicate_rows),
            'total_rows': total_rows
        }

    @staticmethod
    def _calculate_type_consistency_score(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """Calculate column type consistency score (15% weight).
        
        Checks if numeric columns have mixed types, string columns have nulls, etc.
        """
        consistency_issues = 0
        total_columns = df.shape[1]

        for col in df.columns:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue

            # Check if numeric column has non-numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                non_numeric = col_data.apply(lambda x: not isinstance(x, (int, float, np.number)))
                if non_numeric.any():
                    consistency_issues += 1
            
            # Check if object column has mostly nulls
            elif pd.api.types.is_object_dtype(df[col]):
                null_pct = df[col].isnull().sum() / len(df) * 100
                if null_pct > 80:
                    consistency_issues += 1

        consistency_score = 1.0 - (consistency_issues / total_columns) if total_columns > 0 else 1.0
        
        return consistency_score, {
            'type_consistency_issues': int(consistency_issues),
            'total_columns': total_columns
        }

    @staticmethod
    def _calculate_outlier_score(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """Calculate statistical outlier score (15% weight).
        
        Uses IQR method for numeric columns.
        Acceptable: < 1% outliers
        Good: < 5% outliers
        Poor: > 5% outliers
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        total_numeric_cells = len(df) * len(numeric_cols) if len(numeric_cols) > 0 else 1
        
        outlier_count = 0

        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) < 4:  # Need at least 4 values for IQR
                continue

            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1

            if IQR > 0:
                outliers = ((col_data < (Q1 - 1.5 * IQR)) | (col_data > (Q3 + 1.5 * IQR))).sum()
                outlier_count += outliers

        outlier_pct = (outlier_count / total_numeric_cells * 100) if total_numeric_cells > 0 else 0.0

        if outlier_pct < 1:
            score = 1.0
        elif outlier_pct < 5:
            score = 0.95
        else:
            score = max(0.0, 1.0 - (outlier_pct / 100))

        return score, {
            'outlier_pct': outlier_pct,
            'outlier_count': int(outlier_count),
            'numeric_columns': len(numeric_cols)
        }

    @staticmethod
    def _calculate_memory_score(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """Calculate memory efficiency score (10% weight).
        
        Checks if dtypes are optimized.
        """
        total_memory = df.memory_usage(deep=True).sum() / 1024**2  # MB
        
        # Estimate optimal memory usage
        optimal_memory = 0
        dtype_issues = 0

        for col in df.columns:
            if df[col].dtype == 'object':
                # Could potentially be category
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio < 0.1:  # Less than 10% unique values
                    dtype_issues += 1
                optimal_memory += df[col].memory_usage(deep=True) / 1024**2
            else:
                optimal_memory += df[col].memory_usage() / 1024**2

        # Memory efficiency based on dtype optimization
        dtype_efficiency = 1.0 - (dtype_issues / len(df.columns)) if len(df.columns) > 0 else 1.0
        
        return dtype_efficiency, {
            'memory_usage_mb': round(total_memory, 2),
            'optimal_memory_mb': round(optimal_memory, 2),
            'dtype_optimization_issues': int(dtype_issues)
        }

    @staticmethod
    def get_quality_summary(quality_score: float, metrics: Dict[str, Any]) -> str:
        """Get human-readable quality summary.
        
        Args:
            quality_score: Overall quality score (0-1)
            metrics: Detailed metrics
            
        Returns:
            Summary string
        """
        if quality_score >= 0.95:
            rating = "Excellent"
        elif quality_score >= 0.85:
            rating = "Good"
        elif quality_score >= 0.70:
            rating = "Acceptable"
        elif quality_score >= 0.50:
            rating = "Poor"
        else:
            rating = "Bad"

        summary = f"Data Quality: {rating} ({quality_score:.2%})\n"
        summary += f"  Null Data: {metrics.get('null_pct', 0):.1f}%\n"
        summary += f"  Duplicates: {metrics.get('duplicate_pct', 0):.1f}%\n"
        summary += f"  Outliers: {metrics.get('outlier_pct', 0):.1f}%\n"
        summary += f"  Memory: {metrics.get('memory_usage_mb', 0):.1f}MB\n"

        return summary
