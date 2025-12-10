"""Explorer Agent - Data exploration with worker coordination and statistical analysis.

Manages specialized workers for different analysis tasks.
Validates quality and reports findings.

Integrated with Week 1 Systems:
- Structured logging with metrics
- Automatic retry with exponential backoff
- Error recovery and handling
- Statistical tests (Shapiro-Wilk, KS, distribution fitting)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import time
import pandas as pd
import numpy as np
from scipy import stats

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError

from .workers import (
    NumericAnalyzer,
    CategoricalAnalyzer,
    CorrelationAnalyzer,
    QualityAssessor,
    WorkerResult,
    ErrorType,
)

logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)


class Explorer:
    """Agent for exploring data with statistical analysis.
    
    Manages workers:
    - NumericAnalyzer: Analyzes numeric columns
    - CategoricalAnalyzer: Analyzes categorical columns
    - CorrelationAnalyzer: Analyzes correlations
    - QualityAssessor: Assesses overall quality
    
    Statistical Tests:
    - Shapiro-Wilk normality test
    - Kolmogorov-Smirnov test
    - Distribution fitting
    - Skewness/kurtosis analysis
    - Z-score outlier detection
    
    Week 1 Integration:
    - Structured logging with metrics at each step
    - Automatic retry on transient failures
    - Error recovery and detailed error messages
    """
    
    def __init__(self):
        """Initialize Explorer agent with workers."""
        self.name = "Explorer"
        self.logger = get_logger("Explorer")
        self.structured_logger = get_structured_logger("Explorer")
        self.data = None
        
        # Initialize workers
        self.numeric_worker = NumericAnalyzer()
        self.categorical_worker = CategoricalAnalyzer()
        self.correlation_worker = CorrelationAnalyzer()
        self.quality_worker = QualityAssessor()
        
        self.workers = [
            self.numeric_worker,
            self.categorical_worker,
            self.correlation_worker,
            self.quality_worker,
        ]
        
        self.analysis_cache = {}
        self.logger.info(f"{self.name} initialized with 4 workers")
        self.structured_logger.info("Explorer initialized", {
            "workers": 4,
            "worker_names": [
                "NumericAnalyzer",
                "CategoricalAnalyzer",
                "CorrelationAnalyzer",
                "QualityAssessor"
            ]
        })
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data to explore.
        
        Args:
            df: DataFrame to analyze
        """
        if df is None:
            raise AgentError("Cannot set None as data")
        
        self.data = df
        self.analysis_cache = {}  # Clear cache
        self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
        self.structured_logger.info("Data set for exploration", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "dtypes": dict(df.dtypes.astype(str).value_counts())
        })
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze data (alias for get_summary_report).
        
        Convenience method for testing and general use.
        
        Returns:
            Dictionary with all analysis results
        """
        return self.get_summary_report()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def get_summary_report(self) -> Dict[str, Any]:
        """Get comprehensive summary report.
        
        Coordinates all workers, validates quality, reports findings.
        
        Returns:
            Dictionary with all analysis results and quality metrics
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        try:
            self.logger.info("Starting comprehensive data exploration...")
            self.structured_logger.info("Summary report generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Execute all workers
            worker_results = self._execute_all_workers()
            
            # Validate worker quality
            validation_report = self._validate_worker_quality(worker_results)
            
            # Build comprehensive report
            report = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data_shape": {
                    "rows": self.data.shape[0],
                    "columns": self.data.shape[1],
                },
                "workers_executed": len(worker_results),
                "worker_results": {result['worker']: result for result in worker_results},
                "quality_validation": validation_report,
                "overall_quality_score": self._calculate_overall_quality(worker_results),
                "summary": self._build_summary(worker_results),
            }
            
            self.structured_logger.info("Summary report generated successfully", {
                "workers": len(worker_results),
                "quality_score": report["overall_quality_score"]
            })
            
            self.logger.info("Exploration complete")
            return report
        
        except Exception as e:
            self.logger.error(f"Exploration failed: {e}")
            self.structured_logger.error("Summary report generation failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise AgentError(f"Exploration failed: {e}")
    
    @retry_on_error(max_attempts=3, backoff=2)
    def test_normality(self, column: str) -> Dict[str, Any]:
        """Test if column follows normal distribution using Shapiro-Wilk test.
        
        Args:
            column: Column name to test
            
        Returns:
            Dictionary with test results
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if column not in self.data.columns:
            raise AgentError(f"Column '{column}' not found")
        
        self.structured_logger.info("Shapiro-Wilk normality test", {
            "column": column
        })
        
        try:
            series = self.data[column].dropna()
            
            if len(series) < 3:
                return {"status": "error", "message": "Need at least 3 values"}
            
            statistic, p_value = stats.shapiro(series)
            
            result = {
                "column": column,
                "test": "Shapiro-Wilk",
                "statistic": round(float(statistic), 6),
                "p_value": round(float(p_value), 6),
                "is_normal": p_value > 0.05,
                "sample_size": len(series)
            }
            
            self.structured_logger.info("Normality test completed", {
                "column": column,
                "p_value": p_value
            })
            
            return result
        except Exception as e:
            self.structured_logger.error("Normality test failed", {"error": str(e)})
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def ks_test(self, col1: str, col2: str) -> Dict[str, Any]:
        """Kolmogorov-Smirnov test to compare two distributions.
        
        Args:
            col1: First column
            col2: Second column
            
        Returns:
            Dictionary with test results
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("KS test", {"col1": col1, "col2": col2})
        
        try:
            s1 = self.data[col1].dropna()
            s2 = self.data[col2].dropna()
            
            statistic, p_value = stats.ks_2samp(s1, s2)
            
            result = {
                "col1": col1,
                "col2": col2,
                "test": "Kolmogorov-Smirnov",
                "statistic": round(float(statistic), 6),
                "p_value": round(float(p_value), 6),
                "distributions_equal": p_value > 0.05
            }
            
            self.structured_logger.info("KS test completed", {"p_value": p_value})
            return result
        except Exception as e:
            self.structured_logger.error("KS test failed", {"error": str(e)})
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def fit_distribution(self, column: str) -> Dict[str, Any]:
        """Fit common distributions to column data.
        
        Args:
            column: Column name
            
        Returns:
            Dictionary with best-fit distribution info
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Distribution fitting", {"column": column})
        
        try:
            series = self.data[column].dropna()
            distributions = {}
            
            # Try common distributions
            try:
                params = stats.norm.fit(series)
                distributions['normal'] = {'params': params, 'fit_quality': 'good'}
            except: pass
            
            try:
                params = stats.expon.fit(series)
                distributions['exponential'] = {'params': params, 'fit_quality': 'good'}
            except: pass
            
            if (series > 0).all():
                try:
                    params = stats.gamma.fit(series)
                    distributions['gamma'] = {'params': params, 'fit_quality': 'good'}
                except: pass
            
            result = {
                "column": column,
                "distributions_tested": list(distributions.keys()),
                "best_fit": list(distributions.keys())[0] if distributions else None,
                "sample_size": len(series)
            }
            
            self.structured_logger.info("Distribution fitting completed", {
                "column": column,
                "distributions": len(distributions)
            })
            
            return result
        except Exception as e:
            self.structured_logger.error("Distribution fitting failed", {"error": str(e)})
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def calculate_skewness_kurtosis(self, column: str) -> Dict[str, Any]:
        """Calculate skewness and kurtosis for a column.
        
        Args:
            column: Column name
            
        Returns:
            Dictionary with skewness and kurtosis values
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Skewness/Kurtosis", {"column": column})
        
        try:
            series = self.data[column].dropna()
            
            skewness = stats.skew(series)
            kurtosis = stats.kurtosis(series)
            
            result = {
                "column": column,
                "skewness": round(float(skewness), 6),
                "kurtosis": round(float(kurtosis), 6),
                "is_symmetric": abs(skewness) < 0.5,
                "is_normal_peaked": abs(kurtosis) < 0.5
            }
            
            self.structured_logger.info("Skewness/Kurtosis calculated", {
                "skewness": skewness,
                "kurtosis": kurtosis
            })
            
            return result
        except Exception as e:
            self.structured_logger.error("Skewness/Kurtosis failed", {"error": str(e)})
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def detect_outliers_zscore(self, column: str, threshold: float = 3) -> Dict[str, Any]:
        """Detect outliers using z-score method.
        
        Args:
            column: Column name
            threshold: Z-score threshold (default 3)
            
        Returns:
            Dictionary with outlier indices and values
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Z-score outlier detection", {
            "column": column,
            "threshold": threshold
        })
        
        try:
            series = self.data[column].dropna()
            z_scores = np.abs(stats.zscore(series))
            outliers = z_scores > threshold
            
            result = {
                "column": column,
                "method": "z-score",
                "threshold": threshold,
                "outlier_count": int(outliers.sum()),
                "outlier_percentage": round(outliers.sum() / len(series) * 100, 2),
                "outlier_indices": outliers.index[outliers].tolist() if hasattr(outliers, 'index') else []
            }
            
            self.structured_logger.info("Z-score outliers detected", {
                "count": result['outlier_count'],
                "percentage": result['outlier_percentage']
            })
            
            return result
        except Exception as e:
            self.structured_logger.error("Z-score detection failed", {"error": str(e)})
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def correlation_matrix(self) -> pd.DataFrame:
        """Get correlation matrix for all numeric columns.
        
        Returns:
            Correlation matrix DataFrame
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Correlation matrix calculation")
        
        try:
            numeric_data = self.data.select_dtypes(include=[np.number])
            corr_matrix = numeric_data.corr()
            
            self.structured_logger.info("Correlation matrix completed", {
                "shape": corr_matrix.shape
            })
            
            return corr_matrix
        except Exception as e:
            self.structured_logger.error("Correlation matrix failed", {"error": str(e)})
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def get_statistical_summary(self) -> Dict[str, Any]:
        """Get comprehensive statistical summary for all numeric columns.
        
        Returns:
            Dictionary with statistical summaries
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        start_time = time.time()
        self.structured_logger.info("Statistical summary calculation")
        
        try:
            numeric_data = self.data.select_dtypes(include=[np.number])
            summary = {}
            
            for col in numeric_data.columns:
                series = numeric_data[col].dropna()
                summary[col] = {
                    "mean": round(float(series.mean()), 6),
                    "median": round(float(series.median()), 6),
                    "std": round(float(series.std()), 6),
                    "min": round(float(series.min()), 6),
                    "max": round(float(series.max()), 6),
                    "q25": round(float(series.quantile(0.25)), 6),
                    "q75": round(float(series.quantile(0.75)), 6),
                    "null_count": int(numeric_data[col].isna().sum())
                }
            
            duration = time.time() - start_time
            self.structured_logger.info("Statistical summary completed", {
                "columns": len(summary),
                "duration_sec": round(duration, 3)
            })
            
            return summary
        except Exception as e:
            self.structured_logger.error("Statistical summary failed", {"error": str(e)})
            raise
    
    # Original methods below...
    
    @retry_on_error(max_attempts=3, backoff=2)
    def describe_numeric(self) -> Dict[str, Any]:
        """Get detailed numeric statistics.
        
        Returns:
            Dictionary with numeric analysis
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Numeric analysis started", {
            "columns": self.data.shape[1]
        })
        
        try:
            result = self.numeric_worker.safe_execute(df=self.data)
            self.structured_logger.info("Numeric analysis completed", {
                "success": result.success
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Numeric analysis failed", {
                "error": str(e)
            })
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def describe_categorical(self) -> Dict[str, Any]:
        """Get categorical data summaries.
        
        Returns:
            Dictionary with categorical analysis
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Categorical analysis started", {
            "columns": self.data.shape[1]
        })
        
        try:
            result = self.categorical_worker.safe_execute(df=self.data)
            self.structured_logger.info("Categorical analysis completed", {
                "success": result.success
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Categorical analysis failed", {
                "error": str(e)
            })
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlations between numeric columns.
        
        Returns:
            Dictionary with correlation analysis
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Correlation analysis started", {
            "columns": self.data.shape[1]
        })
        
        try:
            result = self.correlation_worker.safe_execute(df=self.data)
            self.structured_logger.info("Correlation analysis completed", {
                "success": result.success
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Correlation analysis failed", {
                "error": str(e)
            })
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def data_quality_assessment(self) -> Dict[str, Any]:
        """Assess overall data quality.
        
        Returns:
            Data quality metrics and recommendations
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Data quality assessment started", {
            "rows": self.data.shape[0],
            "columns": self.data.shape[1]
        })
        
        try:
            result = self.quality_worker.safe_execute(df=self.data)
            self.structured_logger.info("Data quality assessment completed", {
                "success": result.success
            })
            return result.to_dict()
        except Exception as e:
            self.structured_logger.error("Data quality assessment failed", {
                "error": str(e)
            })
            raise
    
    @retry_on_error(max_attempts=3, backoff=2)
    def detect_outliers(self, method: str = "iqr", threshold: float = 1.5) -> Dict[str, Any]:
        """Detect outliers in numeric columns.
        
        Args:
            method: Detection method ('iqr' or 'zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Dictionary with outlier information
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        self.structured_logger.info("Outlier detection started", {
            "method": method,
            "threshold": threshold
        })
        
        try:
            numeric_data = self.data.select_dtypes(include=[np.number])
            
            if numeric_data.empty:
                self.structured_logger.info("No numeric columns found")
                return {"status": "no_numeric_columns", "outliers": {}}
            
            outliers = {}
            
            for col in numeric_data.columns:
                series = numeric_data[col].dropna()
                
                if method == "iqr":
                    Q1 = series.quantile(0.25)
                    Q3 = series.quantile(0.75)
                    IQR = Q3 - Q1
                    lower = Q1 - threshold * IQR
                    upper = Q3 + threshold * IQR
                    mask = (series < lower) | (series > upper)
                else:  # zscore
                    z_scores = np.abs((series - series.mean()) / series.std())
                    mask = z_scores > threshold
                
                if mask.sum() > 0:
                    outliers[col] = {
                        "count": int(mask.sum()),
                        "percentage": round(mask.sum() / len(series) * 100, 2),
                    }
            
            result = {
                "status": "success",
                "method": method,
                "threshold": threshold,
                "outliers": outliers,
            }
            
            self.structured_logger.info("Outlier detection completed", {
                "outliers_found": len(outliers),
                "method": method
            })
            
            return result
        except Exception as e:
            self.structured_logger.error("Outlier detection failed", {
                "method": method,
                "error": str(e)
            })
            raise
    
    def _execute_all_workers(self) -> List[Dict[str, Any]]:
        """Execute all workers and collect results.
        
        Returns:
            List of worker results
        """
        self.logger.info("Executing all workers...")
        self.structured_logger.info("Executing all workers", {
            "worker_count": len(self.workers)
        })
        
        results = []
        
        for worker in self.workers:
            self.logger.info(f"Executing {worker.worker_name}...")
            self.structured_logger.info("Executing worker", {
                "worker": worker.worker_name
            })
            
            result = worker.safe_execute(df=self.data)
            results.append(result.to_dict())
        
        return results
    
    def _validate_worker_quality(self, worker_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate quality of worker outputs.
        
        Checks for errors, warns about quality issues.
        
        Args:
            worker_results: Results from all workers
            
        Returns:
            Validation report
        """
        self.logger.info("Validating worker quality...")
        self.structured_logger.info("Validating worker quality", {
            "worker_count": len(worker_results)
        })
        
        validation = {
            "total_workers": len(worker_results),
            "successful_workers": 0,
            "failed_workers": 0,
            "worker_details": [],
            "error_summary": {},
        }
        
        for result in worker_results:
            worker_name = result['worker']
            success = result['success']
            quality = result['quality_score']
            errors = result['errors']
            
            worker_detail = {
                "worker": worker_name,
                "success": success,
                "quality_score": quality,
                "error_count": len(errors),
                "has_critical_errors": any(e['severity'] == 'critical' for e in errors),
            }
            
            validation['worker_details'].append(worker_detail)
            
            if success:
                validation['successful_workers'] += 1
            else:
                validation['failed_workers'] += 1
            
            for error in errors:
                error_type = error['type']
                validation['error_summary'][error_type] = validation['error_summary'].get(error_type, 0) + 1
        
        self.structured_logger.info("Validation completed", {
            "successful": validation['successful_workers'],
            "failed": validation['failed_workers']
        })
        
        return validation
    
    def _calculate_overall_quality(self, worker_results: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score.
        
        Args:
            worker_results: Results from all workers
            
        Returns:
            Overall quality score (0-1)
        """
        if not worker_results:
            return 0.0
        
        scores = [r['quality_score'] for r in worker_results]
        avg_score = sum(scores) / len(scores)
        
        return round(avg_score, 3)
    
    def _build_summary(self, worker_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build human-readable summary from worker results.
        
        Args:
            worker_results: Results from all workers
            
        Returns:
            Summary dictionary
        """
        summary = {}
        
        for result in worker_results:
            worker_name = result['worker']
            data = result.get('data', {})
            
            if worker_name == 'NumericAnalyzer':
                summary['numeric_columns'] = data.get('numeric_columns', [])
                summary['numeric_stats'] = data.get('statistics', {})
            
            elif worker_name == 'CategoricalAnalyzer':
                summary['categorical_columns'] = data.get('categorical_columns', [])
                summary['categorical_stats'] = data.get('statistics', {})
            
            elif worker_name == 'CorrelationAnalyzer':
                summary['correlations'] = data.get('strong_correlations', [])
            
            elif worker_name == 'QualityAssessor':
                summary['quality_score'] = data.get('overall_quality_score')
                summary['quality_rating'] = data.get('quality_rating')
                summary['null_percentage'] = data.get('null_percentage')
                summary['duplicate_percentage'] = data.get('duplicate_percentage')
        
        return summary
