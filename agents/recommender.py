"""Recommender Agent - Insights extraction and recommendations.

Generates actionable insights and recommendations based on data analysis,
trends, anomalies, and statistical patterns.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

from core.logger import get_logger
from core.exceptions import AgentError

logger = get_logger(__name__)


class Recommender:
    """Agent for generating insights and recommendations.
    
    Capabilities:
    - Pattern recognition
    - Trend-based recommendations
    - Anomaly-based insights
    - Correlation insights
    - Data quality recommendations
    - Performance insights
    - Actionable suggestions
    - Risk assessment
    """
    
    def __init__(self):
        """Initialize Recommender agent."""
        self.name = "Recommender"
        self.data = None
        self.insights = []
        self.recommendations = []
        logger.info(f"{self.name} initialized")
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data for analysis.
        
        Args:
            df: DataFrame to analyze
        """
        self.data = df.copy()
        self.insights = []
        self.recommendations = []
        logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    def analyze_missing_data(self) -> Dict[str, Any]:
        """Analyze and recommend actions for missing data.
        
        Returns:
            Dictionary with insights and recommendations
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Analyzing missing data...")
            
            total_cells = self.data.shape[0] * self.data.shape[1]
            null_cells = self.data.isnull().sum().sum()
            null_pct = (null_cells / total_cells * 100) if total_cells > 0 else 0
            
            insights = []
            recommendations = []
            
            # Check for columns with high null percentage
            null_by_col = self.data.isnull().sum() / len(self.data) * 100
            high_null_cols = null_by_col[null_by_col > 50]
            
            if len(high_null_cols) > 0:
                insight = f"Found {len(high_null_cols)} columns with >50% missing data"
                insights.append({"type": "warning", "message": insight, "severity": "high"})
                
                for col, pct in high_null_cols.items():
                    rec = f"Consider removing '{col}' ({pct:.1f}% missing) or imputing values"
                    recommendations.append({"action": "data_cleaning", "target": col, "suggestion": rec})
            
            # Overall null percentage
            if null_pct > 20:
                insight = f"Dataset has {null_pct:.1f}% missing values overall"
                insights.append({"type": "warning", "message": insight, "severity": "medium"})
                recommendations.append({"action": "imputation", "suggestion": "Consider imputation strategy (mean, median, forward-fill)"})
            elif null_pct == 0:
                insight = "No missing values detected - excellent data quality"
                insights.append({"type": "positive", "message": insight, "severity": "low"})
            
            return {
                "status": "success",
                "analysis_type": "missing_data",
                "null_percentage": round(null_pct, 2),
                "insights": insights,
                "recommendations": recommendations,
            }
        
        except Exception as e:
            logger.error(f"Missing data analysis failed: {e}")
            raise AgentError(f"Analysis failed: {e}")
    
    def analyze_duplicates(self) -> Dict[str, Any]:
        """Analyze and recommend actions for duplicate data.
        
        Returns:
            Dictionary with insights and recommendations
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Analyzing duplicate data...")
            
            duplicates = self.data.duplicated().sum()
            duplicate_pct = (duplicates / len(self.data) * 100) if len(self.data) > 0 else 0
            
            insights = []
            recommendations = []
            
            if duplicates > 0:
                insight = f"Found {duplicates:,} duplicate rows ({duplicate_pct:.2f}%)"
                insights.append({"type": "warning", "message": insight, "severity": "medium"})
                
                rec = f"Remove {duplicates:,} duplicate rows to clean dataset"
                recommendations.append({"action": "deduplication", "suggestion": rec})
            else:
                insight = "No duplicate rows detected"
                insights.append({"type": "positive", "message": insight, "severity": "low"})
            
            # Check for partial duplicates
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                partial_dup = self.data[numeric_cols].duplicated().sum()
                if partial_dup > 0:
                    insight = f"Found {partial_dup:,} partial duplicates (numeric columns only)"
                    insights.append({"type": "info", "message": insight, "severity": "low"})
            
            return {
                "status": "success",
                "analysis_type": "duplicates",
                "duplicate_count": int(duplicates),
                "duplicate_percentage": round(duplicate_pct, 2),
                "insights": insights,
                "recommendations": recommendations,
            }
        
        except Exception as e:
            logger.error(f"Duplicate analysis failed: {e}")
            raise AgentError(f"Analysis failed: {e}")
    
    def analyze_distributions(self) -> Dict[str, Any]:
        """Analyze numeric distributions and provide insights.
        
        Returns:
            Dictionary with distribution insights
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Analyzing distributions...")
            
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
            insights = []
            recommendations = []
            
            for col in numeric_cols:
                series = self.data[col].dropna()
                if len(series) < 3:
                    continue
                
                skewness = series.skew()
                kurtosis = series.kurtosis()
                
                # Check for skewness
                if abs(skewness) > 1:
                    direction = "right" if skewness > 0 else "left"
                    insight = f"'{col}' has strong {direction} skew ({skewness:.2f})"
                    insights.append({"type": "info", "message": insight, "severity": "low", "column": col})
                    recommendations.append({"action": "transformation", "target": col, "suggestion": f"Consider log or Box-Cox transformation for '{col}'"})
                
                # Check for heavy tails
                if kurtosis > 3:
                    insight = f"'{col}' has heavy tails (high kurtosis: {kurtosis:.2f})"
                    insights.append({"type": "warning", "message": insight, "severity": "medium", "column": col})
                    recommendations.append({"action": "outlier_handling", "target": col, "suggestion": f"Investigate outliers in '{col}'"})
            
            if len(insights) == 0:
                insights.append({"type": "positive", "message": "All distributions appear normal", "severity": "low"})
            
            return {
                "status": "success",
                "analysis_type": "distributions",
                "columns_analyzed": len(numeric_cols),
                "insights": insights,
                "recommendations": recommendations,
            }
        
        except Exception as e:
            logger.error(f"Distribution analysis failed: {e}")
            raise AgentError(f"Analysis failed: {e}")
    
    def analyze_correlations(self) -> Dict[str, Any]:
        """Analyze correlations and provide insights.
        
        Returns:
            Dictionary with correlation insights
            
        Raises:
            AgentError: If no data set or insufficient columns
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Analyzing correlations...")
            
            numeric_data = self.data.select_dtypes(include=[np.number])
            
            if numeric_data.shape[1] < 2:
                return {"status": "insufficient_data", "message": "Need at least 2 numeric columns"}
            
            corr_matrix = numeric_data.corr()
            insights = []
            recommendations = []
            
            # Find strong correlations
            strong_corrs = []
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
                insight = f"Found {len(strong_corrs)} strong correlations (|r| > 0.7)"
                insights.append({"type": "info", "message": insight, "severity": "low"})
                
                # Check for multicollinearity
                if len(strong_corrs) > 3:
                    recommendations.append({"action": "feature_engineering", "suggestion": "Consider removing highly correlated features to reduce multicollinearity"})
                
                for corr in strong_corrs:
                    insight = f"'{corr['col1']}' and '{corr['col2']}' strongly correlated ({corr['correlation']:.2f})"
                    insights.append({"type": "info", "message": insight, "severity": "low"})
            else:
                insight = "No strong correlations detected - features are independent"
                insights.append({"type": "positive", "message": insight, "severity": "low"})
            
            return {
                "status": "success",
                "analysis_type": "correlations",
                "strong_correlations": len(strong_corrs),
                "insights": insights,
                "recommendations": recommendations,
            }
        
        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            raise AgentError(f"Analysis failed: {e}")
    
    def generate_action_plan(self) -> Dict[str, Any]:
        """Generate comprehensive action plan based on all analyses.
        
        Returns:
            Dictionary with action plan and priorities
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating action plan...")
            
            # Run all analyses
            missing = self.analyze_missing_data()
            duplicates = self.analyze_duplicates()
            distributions = self.analyze_distributions()
            correlations = self.analyze_correlations()
            
            # Collect all recommendations
            all_recs = []
            all_recs.extend(missing.get("recommendations", []))
            all_recs.extend(duplicates.get("recommendations", []))
            all_recs.extend(distributions.get("recommendations", []))
            all_recs.extend(correlations.get("recommendations", []))
            
            # Prioritize by action type
            priorities = {
                "deduplication": 1,      # Highest priority
                "data_cleaning": 2,
                "imputation": 3,
                "outlier_handling": 4,
                "transformation": 5,
                "feature_engineering": 6,  # Lowest priority
            }
            
            # Sort by priority
            sorted_recs = sorted(
                all_recs,
                key=lambda x: priorities.get(x.get("action"), 99)
            )
            
            # Remove duplicates while preserving order
            seen = set()
            unique_recs = []
            for rec in sorted_recs:
                rec_str = str(rec)
                if rec_str not in seen:
                    seen.add(rec_str)
                    unique_recs.append(rec)
            
            return {
                "status": "success",
                "plan_type": "comprehensive_action_plan",
                "timestamp": datetime.utcnow().isoformat(),
                "data_shape": {"rows": self.data.shape[0], "columns": self.data.shape[1]},
                "total_actions": len(unique_recs),
                "actions": unique_recs,
                "analyses": {
                    "missing_data": missing,
                    "duplicates": duplicates,
                    "distributions": distributions,
                    "correlations": correlations,
                },
            }
        
        except Exception as e:
            logger.error(f"Action plan generation failed: {e}")
            raise AgentError(f"Generation failed: {e}")
    
    def get_summary_insights(self) -> Dict[str, Any]:
        """Get high-level summary insights.
        
        Returns:
            Dictionary with key insights
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            logger.info("Generating summary insights...")
            
            insights = []
            
            # Dataset size
            rows, cols = self.data.shape
            insights.append({"metric": "Size", "value": f"{rows:,} rows × {cols} columns"})
            
            # Data quality
            null_pct = (self.data.isnull().sum().sum() / (rows * cols) * 100) if (rows * cols) > 0 else 0
            if null_pct == 0:
                quality = "Excellent"
            elif null_pct < 5:
                quality = "Good"
            elif null_pct < 20:
                quality = "Fair"
            else:
                quality = "Poor"
            insights.append({"metric": "Data Quality", "value": quality, "detail": f"{null_pct:.1f}% missing"})
            
            # Duplicates
            dup_count = self.data.duplicated().sum()
            insights.append({"metric": "Duplicates", "value": f"{dup_count} rows", "percentage": f"{(dup_count/rows*100):.2f}%"})
            
            # Columns
            numeric = len(self.data.select_dtypes(include=[np.number]).columns)
            categorical = len(self.data.select_dtypes(include=['object']).columns)
            insights.append({"metric": "Numeric Columns", "value": numeric})
            insights.append({"metric": "Categorical Columns", "value": categorical})
            
            return {
                "status": "success",
                "insights_type": "summary",
                "insights": insights,
            }
        
        except Exception as e:
            logger.error(f"Summary insights failed: {e}")
            raise AgentError(f"Failed: {e}")
