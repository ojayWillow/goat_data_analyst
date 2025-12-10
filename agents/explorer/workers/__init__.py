"""Explorer Workers - Specialized workers for data analysis.

Each worker handles a specific analysis task.
All workers inherit from BaseWorker and use standardized communication.

Core Workers:
- NumericAnalyzer: Analyzes numeric columns
- CategoricalAnalyzer: Analyzes categorical columns
- CorrelationAnalyzer: Analyzes correlations
- QualityAssessor: Assesses data quality

Statistical Workers (Week 1 Day 2):
- NormalityTester: Shapiro-Wilk normality test
- DistributionComparison: Kolmogorov-Smirnov test
- DistributionFitter: Distribution fitting
- SkewnessKurtosisAnalyzer: Skewness/kurtosis analysis
- OutlierDetector: Z-score outlier detection
- CorrelationMatrixWorker: Correlation matrix
- StatisticalSummaryWorker: Comprehensive statistical summary
- PerformanceTestWorker: Performance testing
"""

from .base_worker import BaseWorker, WorkerResult, WorkerError, ErrorType
from .numeric_analyzer import NumericAnalyzer
from .categorical_analyzer import CategoricalAnalyzer
from .correlation_analyzer import CorrelationAnalyzer
from .quality_assessor import QualityAssessor

# Statistical workers
from .normality_tester import NormalityTester
from .distribution_comparison import DistributionComparison
from .distribution_fitter import DistributionFitter
from .skewness_kurtosis_analyzer import SkewnessKurtosisAnalyzer
from .outlier_detector import OutlierDetector
from .correlation_matrix_worker import CorrelationMatrixWorker
from .statistical_summary_worker import StatisticalSummaryWorker
from .performance_test_worker import PerformanceTestWorker

__all__ = [
    # Base
    'BaseWorker',
    'WorkerResult',
    'WorkerError',
    'ErrorType',
    # Core workers
    'NumericAnalyzer',
    'CategoricalAnalyzer',
    'CorrelationAnalyzer',
    'QualityAssessor',
    # Statistical workers
    'NormalityTester',
    'DistributionComparison',
    'DistributionFitter',
    'SkewnessKurtosisAnalyzer',
    'OutlierDetector',
    'CorrelationMatrixWorker',
    'StatisticalSummaryWorker',
    'PerformanceTestWorker',
]
