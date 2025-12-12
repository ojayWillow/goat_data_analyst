"""Explorer Agent - Comprehensive data exploration and statistical analysis.

Coordinates 12 workers for systematic data exploration.
Implements retry logic, error intelligence, and health reporting.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from .workers import (
    NumericAnalyzer,
    CategoricalAnalyzer,
    CorrelationAnalyzer,
    QualityAssessor,
    # Statistical workers
    NormalityTester,
    DistributionComparison,
    DistributionFitter,
    SkewnessKurtosisAnalyzer,
    OutlierDetector,
    CorrelationMatrix,
    StatisticalSummary,
    PerformanceTest,
    WorkerResult,
    ErrorType,
)
from core.structured_logger import get_structured_logger
from core.error_recovery import retry_on_error
from core.exceptions import AgentError

structured_logger = get_structured_logger(__name__)


class Explorer:
    """Agent for exploring data with comprehensive statistical analysis.
    
    Manages 12 workers for systematic data analysis:
    
    **Core Workers (4):**
    - NumericAnalyzer: Analyzes numeric columns
    - CategoricalAnalyzer: Analyzes categorical columns
    - CorrelationAnalyzer: Analyzes correlations
    - QualityAssessor: Assesses overall quality
    
    **Statistical Workers (8):**
    - NormalityTester: Shapiro-Wilk normality test
    - DistributionComparison: Kolmogorov-Smirnov test
    - DistributionFitter: Distribution fitting
    - SkewnessKurtosisAnalyzer: Skewness/kurtosis analysis
    - OutlierDetector: Z-score outlier detection
    - CorrelationMatrix: Correlation matrix
    - StatisticalSummary: Comprehensive stats
    - PerformanceTest: Performance testing
    
    **Features:**
    - Structured logging with metrics
    - Automatic retry on transient failures
    - Error intelligence tracking
    - Quality score aggregation
    - Health reports and recommendations
    
    **Usage:**
        >>> explorer = Explorer()
        >>> explorer.set_data(df)
        >>> report = explorer.summary_report()
        >>> print(f"Quality: {report['overall_quality_score']}")
    
    Attributes:
        name: Agent identifier
        data: Current DataFrame being analyzed
        core_workers: List of core analysis workers
        statistical_workers: List of statistical workers
        all_workers: Combined list of all workers
        analysis_cache: Cache of analysis results
    """
    
    # Constants
    MAX_RETRIES = 3
    RETRY_BACKOFF = 2  # seconds
    
    def __init__(self) -> None:
        """Initialize Explorer agent with all workers."""
        self.name = "Explorer"
        self.structured_logger = get_structured_logger("Explorer")
        self.data: Optional[pd.DataFrame] = None
        
        # Core workers
        self.numeric_worker = NumericAnalyzer()
        self.categorical_worker = CategoricalAnalyzer()
        self.correlation_worker = CorrelationAnalyzer()
        self.quality_worker = QualityAssessor()
        
        # Statistical workers
        self.normality_tester = NormalityTester()
        self.distribution_comparison = DistributionComparison()
        self.distribution_fitter = DistributionFitter()
        self.skewness_kurtosis = SkewnessKurtosisAnalyzer()
        self.outlier_detector = OutlierDetector()
        self.correlation_matrix = CorrelationMatrix()
        self.statistical_summary = StatisticalSummary()
        self.performance_test = PerformanceTest()
        
        self.core_workers = [
            self.numeric_worker,
            self.categorical_worker,
            self.correlation_worker,
            self.quality_worker,
        ]
        
        self.statistical_workers = [
            self.normality_tester,
            self.distribution_comparison,
            self.distribution_fitter,
            self.skewness_kurtosis,
            self.outlier_detector,
            self.correlation_matrix,
            self.statistical_summary,
            self.performance_test,
        ]
        
        self.all_workers = self.core_workers + self.statistical_workers
        self.analysis_cache: Dict[str, Any] = {}
        
        self.structured_logger.info("Explorer initialized", {
            "core_workers": len(self.core_workers),
            "statistical_workers": len(self.statistical_workers),
            "total_workers": len(self.all_workers)
        })
    
    @retry_on_error(max_attempts=2, backoff=1)
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data to explore.
        
        Args:
            df: DataFrame to analyze
            
        Raises:
            AgentError: If DataFrame is None
        """
        if df is None:
            raise AgentError("Cannot set None as data")
        
        self.data = df
        self.analysis_cache = {}  # Clear cache when data changes
        
        self.structured_logger.info("Data set for exploration", {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "dtypes": dict(df.dtypes.astype(str).value_counts())
        })
    
    @retry_on_error(max_attempts=2, backoff=1)
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None if not set
        """
        return self.data
    
    @retry_on_error(max_attempts=2, backoff=1)
    def analyze(self) -> Dict[str, Any]:
        """Analyze data (alias for summary_report).
        
        Convenience method for testing and general use.
        
        Returns:
            Dictionary with all analysis results
            
        Raises:
            AgentError: If no data set
        """
        return self.summary_report()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def summary_report(self) -> Dict[str, Any]:
        """Get comprehensive summary report using core workers.
        
        Coordinates core workers, validates quality, reports findings.
        Uses cached results when available.
        
        Returns:
            Dictionary with analysis results and quality metrics
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        # Check cache
        cache_key = f"summary_{id(self.data)}"
        if cache_key in self.analysis_cache:
            self.structured_logger.info("Using cached summary report")
            return self.analysis_cache[cache_key]
        
        try:
            self.structured_logger.info("Summary report generation started", {
                "rows": self.data.shape[0],
                "columns": self.data.shape[1]
            })
            
            # Execute core workers
            worker_results = self._execute_workers(self.core_workers)
            
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
                "columns": list(self.data.columns)
            }
            
            # Cache result
            self.analysis_cache[cache_key] = report
            
            self.structured_logger.info("Summary report generated successfully", {
                "workers": len(worker_results),
                "quality_score": report["overall_quality_score"]
            })
            
            return report
        
        except Exception as e:
            self.structured_logger.error("Summary report generation failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise AgentError(f"Exploration failed: {e}")
    
    # Statistical analysis methods
    
    @retry_on_error(max_attempts=3, backoff=2)
    def test_normality(self, column: str) -> Dict[str, Any]:
        """Test normality using NormalityTester worker.
        
        Args:
            column: Column name to test
            
        Returns:
            Normality test results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.normality_tester.safe_execute(df=self.data, column=column)
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def ks_test(self, col1: str, col2: str) -> Dict[str, Any]:
        """Compare distributions using DistributionComparison worker.
        
        Args:
            col1: First column name
            col2: Second column name
            
        Returns:
            Distribution comparison results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.distribution_comparison.safe_execute(
            df=self.data, col1=col1, col2=col2
        )
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def fit_distribution(self, column: str) -> Dict[str, Any]:
        """Fit distributions using DistributionFitter worker.
        
        Args:
            column: Column name to fit
            
        Returns:
            Distribution fitting results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.distribution_fitter.safe_execute(df=self.data, column=column)
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def calculate_skewness_kurtosis(self, column: str) -> Dict[str, Any]:
        """Calculate skewness/kurtosis using SkewnessKurtosisAnalyzer worker.
        
        Args:
            column: Column name to analyze
            
        Returns:
            Skewness and kurtosis results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.skewness_kurtosis.safe_execute(df=self.data, column=column)
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def detect_outliers_zscore(self, column: str, threshold: float = 3.0) -> Dict[str, Any]:
        """Detect outliers using OutlierDetector worker.
        
        Args:
            column: Column name to analyze
            threshold: Z-score threshold (default: 3.0)
            
        Returns:
            Outlier detection results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.outlier_detector.safe_execute(
            df=self.data, column=column, threshold=threshold
        )
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def get_correlation_matrix(self) -> Dict[str, Any]:
        """Get correlation matrix using CorrelationMatrix worker.
        
        Returns:
            Correlation matrix results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.correlation_matrix.safe_execute(df=self.data)
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def get_statistical_summary(self) -> Dict[str, Any]:
        """Get statistical summary using StatisticalSummary worker.
        
        Returns:
            Statistical summary results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.statistical_summary.safe_execute(df=self.data)
        return result.to_dict()
    
    # Core analysis methods
    
    @retry_on_error(max_attempts=3, backoff=2)
    def describe_numeric(self) -> Dict[str, Any]:
        """Get detailed numeric statistics.
        
        Returns:
            Numeric column analysis
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.numeric_worker.safe_execute(df=self.data)
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def describe_categorical(self) -> Dict[str, Any]:
        """Get categorical data summaries.
        
        Returns:
            Categorical column analysis
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.categorical_worker.safe_execute(df=self.data)
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlations between numeric columns.
        
        Returns:
            Correlation analysis results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.correlation_worker.safe_execute(df=self.data)
        return result.to_dict()
    
    @retry_on_error(max_attempts=3, backoff=2)
    def data_quality_assessment(self) -> Dict[str, Any]:
        """Assess overall data quality.
        
        Returns:
            Quality assessment results
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        result = self.quality_worker.safe_execute(df=self.data)
        return result.to_dict()
    
    # Private helper methods
    
    def _execute_workers(self, workers: List) -> List[Dict[str, Any]]:
        """Execute a list of workers and collect results.
        
        Args:
            workers: List of worker instances
            
        Returns:
            List of WorkerResult dictionaries
        """
        self.structured_logger.info("Executing workers", {"worker_count": len(workers)})
        
        results = []
        for worker in workers:
            result = worker.safe_execute(df=self.data)
            results.append(result.to_dict())
        
        return results
    
    def _validate_worker_quality(self, worker_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate quality of worker outputs.
        
        Args:
            worker_results: List of worker result dictionaries
            
        Returns:
            Validation report
        """
        validation = {
            "total_workers": len(worker_results),
            "successful_workers": sum(1 for r in worker_results if r['success']),
            "failed_workers": sum(1 for r in worker_results if not r['success']),
            "worker_details": []
        }
        
        for result in worker_results:
            validation['worker_details'].append({
                "worker": result['worker'],
                "success": result['success'],
                "quality_score": result['quality_score'],
                "error_count": len(result['errors'])
            })
        
        return validation
    
    def _calculate_overall_quality(self, worker_results: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score.
        
        Args:
            worker_results: List of worker result dictionaries
            
        Returns:
            Aggregated quality score (0-1)
        """
        if not worker_results:
            return 0.0
        
        scores = [r['quality_score'] for r in worker_results]
        return round(sum(scores) / len(scores), 3)
    
    def _build_summary(self, worker_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build human-readable summary from worker results.
        
        Args:
            worker_results: List of worker result dictionaries
            
        Returns:
            Summary dictionary
        """
        summary: Dict[str, Any] = {}
        
        for result in worker_results:
            worker_name = result['worker']
            data = result.get('data', {})
            
            if worker_name == 'NumericAnalyzer':
                summary['numeric_columns'] = data.get('numeric_columns', [])
            elif worker_name == 'CategoricalAnalyzer':
                summary['categorical_columns'] = data.get('categorical_columns', [])
            elif worker_name == 'CorrelationAnalyzer':
                summary['correlations'] = data.get('strong_correlations', [])
            elif worker_name == 'QualityAssessor':
                summary['quality_score'] = data.get('overall_quality_score')
                summary['quality_rating'] = data.get('quality_rating')
        
        return summary
