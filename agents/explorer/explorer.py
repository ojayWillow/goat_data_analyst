"""Explorer Agent - Data exploration with worker coordination.

Manages specialized workers for different analysis tasks.
Validates quality and reports findings.

Integrated with Week 1 Systems:
- Structured logging with metrics
- Automatic retry with exponential backoff
- Error recovery and handling
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import pandas as pd

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
    """Agent for exploring data.
    
    Manages workers:
    - NumericAnalyzer: Analyzes numeric columns
    - CategoricalAnalyzer: Analyzes categorical columns
    - CorrelationAnalyzer: Analyzes correlations
    - QualityAssessor: Assesses overall quality
    
    Quality Validation:
    - Checks each worker's output quality
    - Identifies errors and mistakes
    - Classifies error types
    - Reports comprehensive findings
    
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
            # This uses numeric worker
            import numpy as np
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
        
        # Execute each worker
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
            
            # Track error types
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
        
        # Extract data from each worker's results
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
