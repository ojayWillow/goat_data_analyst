"""StatisticalReportGenerator - Generates statistical analysis reports.

Enhanced with:
- Distribution analysis (skewness, kurtosis)
- Normality tests (Shapiro-Wilk)
- Variance analysis
- P-values for correlations
- Better edge case handling
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from scipy import stats as scipy_stats
from .base_worker import BaseWorker, WorkerResult, ErrorType, ValidationUtils
from agents.error_intelligence.main import ErrorIntelligence


class StatisticalReportGenerator(BaseWorker):
    """Generates comprehensive statistical analysis reports.
    
    Provides:
    - Descriptive statistics
    - Distribution analysis
    - Normality testing
    - Correlation analysis with p-values
    - Variance analysis
    """
    
    def __init__(self):
        super().__init__("statistical_report_generator")
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Generate comprehensive statistical report.
        
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
            # Validate input
            is_valid, error_msg = ValidationUtils.validate_dataframe(
                df,
                min_cols=1,
                allow_empty=False
            )
            if not is_valid:
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    error_msg,
                    severity="error"
                )
                result.success = False
                return result
            
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) == 0:
                self._add_warning(
                    result,
                    "No numeric columns found; statistical analysis not performed"
                )
                result.data = {
                    "report_type": "statistical_analysis",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "statistics": {},
                    "distribution_analysis": {},
                    "correlation_analysis": {},
                    "message": "No numeric columns available",
                }
                result.quality_score = 0.5
                return result
            
            report = {
                "report_type": "statistical_analysis",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "numeric_columns_analyzed": len(numeric_cols),
                "statistics": self._get_descriptive_statistics(df[numeric_cols]),
                "distribution_analysis": self._get_distribution_analysis(df[numeric_cols]),
                "normality_tests": self._get_normality_tests(df[numeric_cols]),
                "correlation_analysis": self._get_correlation_analysis(df[numeric_cols]),
            }
            
            result.data = report
            result.rows_processed = len(df)
            result.quality_score = 0.95  # High quality statistical analysis
            
            self.logger.info(f"Statistical report generated for {len(numeric_cols)} numeric columns")
            
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
    
    def _get_descriptive_statistics(self, numeric_df: pd.DataFrame) -> Dict[str, Any]:
        """Get descriptive statistics for all numeric columns."""
        try:
            # Use pandas describe
            describe = numeric_df.describe(percentiles=[.25, .5, .75, .95, .99])
            return describe.to_dict()
        except Exception:
            return {}
    
    def _get_distribution_analysis(self, numeric_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distributions of numeric columns."""
        distributions = {}
        
        for col in numeric_df.columns:
            try:
                series = numeric_df[col].dropna()
                
                if len(series) < 2:
                    continue
                
                # Calculate distribution metrics
                skewness = float(scipy_stats.skew(series))
                kurtosis = float(scipy_stats.kurtosis(series))
                
                # Classify distribution
                dist_type = self._classify_distribution(skewness, kurtosis)
                
                distributions[col] = {
                    "skewness": round(skewness, 4),
                    "kurtosis": round(kurtosis, 4),
                    "distribution_type": dist_type,
                    "description": self._describe_distribution(skewness, kurtosis),
                }
            except Exception:
                continue
        
        return distributions
    
    def _classify_distribution(self, skewness: float, kurtosis: float) -> str:
        """Classify distribution based on skewness and kurtosis."""
        if abs(skewness) < 0.5 and abs(kurtosis) < 3:
            return "Normal-like"
        elif skewness > 0.5:
            return "Right-skewed"
        elif skewness < -0.5:
            return "Left-skewed"
        else:
            return "Other"
    
    def _describe_distribution(self, skewness: float, kurtosis: float) -> str:
        """Create human-readable distribution description."""
        parts = []
        
        if abs(skewness) < 0.5:
            parts.append("symmetric")
        elif skewness > 0:
            parts.append("right-tailed")
        else:
            parts.append("left-tailed")
        
        if kurtosis > 3:
            parts.append("heavy-tailed")
        elif kurtosis < -1:
            parts.append("light-tailed")
        else:
            parts.append("normal-tailed")
        
        return " ".join(parts)
    
    def _get_normality_tests(self, numeric_df: pd.DataFrame) -> Dict[str, Any]:
        """Perform normality tests (Shapiro-Wilk)."""
        tests = {}
        
        for col in numeric_df.columns:
            try:
                series = numeric_df[col].dropna()
                
                # Shapiro-Wilk test (works for n <= 5000)
                if 3 <= len(series) <= 5000:
                    stat, p_value = scipy_stats.shapiro(series)
                    tests[col] = {
                        "test": "Shapiro-Wilk",
                        "statistic": round(float(stat), 4),
                        "p_value": round(float(p_value), 6),
                        "is_normal": p_value > 0.05,
                        "significance_level": 0.05,
                    }
            except Exception:
                continue
        
        return tests
    
    def _get_correlation_analysis(self, numeric_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations with p-values."""
        analysis = {}
        
        if len(numeric_df.columns) < 2:
            return {"message": "Need at least 2 numeric columns for correlation analysis"}
        
        try:
            # Correlation matrix
            corr_matrix = numeric_df.corr()
            analysis["correlation_matrix"] = corr_matrix.to_dict()
            
            # P-value matrix
            p_values = self._get_pvalue_matrix(numeric_df)
            analysis["p_values_matrix"] = p_values
            
            # High correlations with significance
            high_corr = []
            numeric_cols = numeric_df.columns.tolist()
            
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    corr_val = corr_matrix.iloc[i, j]
                    p_val = p_values.get(f"{col1}_{col2}", None)
                    
                    # Significant and strong correlations
                    if p_val and p_val < 0.05 and abs(corr_val) > 0.5:
                        high_corr.append({
                            "pair": [col1, col2],
                            "correlation": round(float(corr_val), 4),
                            "p_value": round(float(p_val), 6),
                            "significant": True,
                            "strength": self._classify_correlation(abs(corr_val)),
                        })
            
            analysis["significant_correlations"] = sorted(
                high_corr,
                key=lambda x: abs(x["correlation"]),
                reverse=True
            )
            
        except Exception as e:
            self.logger.warning(f"Correlation analysis failed: {e}")
            analysis["message"] = "Correlation analysis could not be completed"
        
        return analysis
    
    def _get_pvalue_matrix(self, numeric_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate p-values for correlations."""
        p_values = {}
        numeric_cols = numeric_df.columns.tolist()
        
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                col1, col2 = numeric_cols[i], numeric_cols[j]
                
                try:
                    # Pearson correlation p-value
                    _, p_val = scipy_stats.pearsonr(
                        numeric_df[col1].dropna(),
                        numeric_df[col2].dropna()
                    )
                    p_values[f"{col1}_{col2}"] = p_val
                except Exception:
                    p_values[f"{col1}_{col2}"] = 1.0
        
        return p_values
    
    def _classify_correlation(self, corr_abs: float) -> str:
        """Classify correlation strength."""
        if corr_abs > 0.8:
            return "Very Strong"
        elif corr_abs > 0.6:
            return "Strong"
        elif corr_abs > 0.4:
            return "Moderate"
        elif corr_abs > 0.2:
            return "Weak"
        else:
            return "Very Weak"
