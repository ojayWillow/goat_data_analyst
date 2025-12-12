"""Comprehensive test suite for Explorer Agent workers.

Tests all 12 workers with valid/invalid inputs, edge cases, and error scenarios.
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any

from agents.explorer.workers import (
    NumericAnalyzer,
    CategoricalAnalyzer,
    CorrelationAnalyzer,
    QualityAssessor,
    NormalityTester,
    DistributionFitter,
    DistributionComparison,
    SkewnessKurtosisAnalyzer,
    OutlierDetector,
    CorrelationMatrix,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def clean_dataframe():
    """Fixture: Clean DataFrame with various data types."""
    np.random.seed(42)
    return pd.DataFrame({
        'int_col': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'float_col': [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.1],
        'category_col': ['A', 'B', 'A', 'B', 'C', 'A', 'B', 'C', 'C', 'A'],
        'values': np.random.normal(loc=100, scale=15, size=10),
    })


@pytest.fixture
def dataframe_with_nulls():
    """Fixture: DataFrame with missing values."""
    df = pd.DataFrame({
        'col1': [1, 2, np.nan, 4, 5],
        'col2': [10, np.nan, 30, np.nan, 50],
        'col3': ['A', 'B', np.nan, 'D', np.nan],
    })
    return df


@pytest.fixture
def dataframe_with_duplicates():
    """Fixture: DataFrame with duplicate rows."""
    return pd.DataFrame({
        'id': [1, 2, 2, 3, 3, 3],
        'value': [10, 20, 20, 30, 30, 30],
        'category': ['X', 'Y', 'Y', 'Z', 'Z', 'Z'],
    })


@pytest.fixture
def dataframe_with_outliers():
    """Fixture: DataFrame with statistical outliers."""
    np.random.seed(42)
    data = np.random.normal(loc=100, scale=10, size=100)
    # Add outliers
    data[0] = 500  # Extreme outlier
    data[1] = -200  # Extreme outlier
    return pd.DataFrame({'values': data})


@pytest.fixture
def skewed_data():
    """Fixture: DataFrame with skewed distribution."""
    np.random.seed(42)
    # Right-skewed data (exponential)
    return pd.DataFrame({
        'skewed': np.random.exponential(scale=2, size=100),
    })


# ============================================================================
# NUMERIC ANALYZER TESTS
# ============================================================================

class TestNumericAnalyzer:
    """Test NumericAnalyzer worker."""
    
    def test_valid_input(self, clean_dataframe):
        """Test with valid input."""
        analyzer = NumericAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe)
        
        assert result.success is True
        assert result.quality_score == 1.0
        assert len(result.errors) == 0
        assert 'numeric_columns' in result.data
    
    def test_no_dataframe(self):
        """Test with missing DataFrame."""
        analyzer = NumericAnalyzer()
        result = analyzer.safe_execute(df=None)
        
        assert result.success is False
        assert result.quality_score == 0.0
        assert len(result.errors) > 0
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        analyzer = NumericAnalyzer()
        result = analyzer.safe_execute(df=pd.DataFrame())
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_with_nulls(self, dataframe_with_nulls):
        """Test with DataFrame containing nulls."""
        analyzer = NumericAnalyzer()
        result = analyzer.safe_execute(df=dataframe_with_nulls)
        
        assert result.success is True
        assert len(result.errors) == 0
    
    def test_quality_score(self, clean_dataframe):
        """Test quality score calculation."""
        analyzer = NumericAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe)
        
        assert 0 <= result.quality_score <= 1
    
    def test_returns_worker_result(self, clean_dataframe):
        """Test that execute always returns WorkerResult."""
        analyzer = NumericAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe)
        
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'quality_score')
        assert hasattr(result, 'errors')


# ============================================================================
# CATEGORICAL ANALYZER TESTS
# ============================================================================

class TestCategoricalAnalyzer:
    """Test CategoricalAnalyzer worker."""
    
    def test_valid_input(self, clean_dataframe):
        """Test with valid input."""
        analyzer = CategoricalAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe)
        
        assert result.success is True
        assert result.quality_score > 0
        assert 'categorical_columns' in result.data
    
    def test_no_dataframe(self):
        """Test with missing DataFrame."""
        analyzer = CategoricalAnalyzer()
        result = analyzer.safe_execute(df=None)
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_with_nulls(self, dataframe_with_nulls):
        """Test with nulls."""
        analyzer = CategoricalAnalyzer()
        result = analyzer.safe_execute(df=dataframe_with_nulls)
        
        assert result.success is True


# ============================================================================
# CORRELATION ANALYZER TESTS
# ============================================================================

class TestCorrelationAnalyzer:
    """Test CorrelationAnalyzer worker."""
    
    def test_valid_input(self, clean_dataframe):
        """Test with valid input."""
        analyzer = CorrelationAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe)
        
        assert result.success is True
        assert result.quality_score > 0
        assert 'correlation_matrix' in result.data
    
    def test_threshold_parameter(self, clean_dataframe):
        """Test with custom threshold."""
        analyzer = CorrelationAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe, threshold=0.5)
        
        assert result.success is True
        assert result.data['threshold'] == 0.5
    
    def test_invalid_threshold(self, clean_dataframe):
        """Test with invalid threshold."""
        analyzer = CorrelationAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe, threshold=2.0)
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_no_dataframe(self):
        """Test with missing DataFrame."""
        analyzer = CorrelationAnalyzer()
        result = analyzer.safe_execute(df=None)
        
        assert result.success is False


# ============================================================================
# QUALITY ASSESSOR TESTS
# ============================================================================

class TestQualityAssessor:
    """Test QualityAssessor worker."""
    
    def test_clean_data(self, clean_dataframe):
        """Test with clean data."""
        assessor = QualityAssessor()
        result = assessor.safe_execute(df=clean_dataframe)
        
        assert result.success is True
        assert result.quality_score > 0.8  # Clean data
        assert 'overall_quality_score' in result.data
    
    def test_data_with_nulls(self, dataframe_with_nulls):
        """Test with nulls."""
        assessor = QualityAssessor()
        result = assessor.safe_execute(df=dataframe_with_nulls)
        
        assert result.success is True
        assert result.data['null_percentage'] > 0
    
    def test_data_with_duplicates(self, dataframe_with_duplicates):
        """Test with duplicates."""
        assessor = QualityAssessor()
        result = assessor.safe_execute(df=dataframe_with_duplicates)
        
        assert result.success is True
        assert result.data['duplicate_rows'] > 0
    
    def test_quality_rating(self, clean_dataframe):
        """Test quality rating mapping."""
        assessor = QualityAssessor()
        result = assessor.safe_execute(df=clean_dataframe)
        
        assert result.success is True
        assert result.data['quality_rating'] in [
            'Excellent', 'Good', 'Fair', 'Poor', 'Very Poor'
        ]


# ============================================================================
# NORMALITY TESTER TESTS
# ============================================================================

class TestNormalityTester:
    """Test NormalityTester worker."""
    
    def test_normal_distribution(self, clean_dataframe):
        """Test with approximately normal data."""
        tester = NormalityTester()
        result = tester.safe_execute(df=clean_dataframe, column='values')
        
        assert result.success is True
        assert result.quality_score == 1.0
        assert 'p_value' in result.data
        assert 'is_normal' in result.data
    
    def test_missing_column(self, clean_dataframe):
        """Test with non-existent column."""
        tester = NormalityTester()
        result = tester.safe_execute(df=clean_dataframe, column='nonexistent')
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_insufficient_data(self):
        """Test with too few data points."""
        df = pd.DataFrame({'col': [1, 2]})
        tester = NormalityTester()
        result = tester.safe_execute(df=df, column='col')
        
        assert result.success is False
    
    def test_no_dataframe(self):
        """Test with missing DataFrame."""
        tester = NormalityTester()
        result = tester.safe_execute(df=None, column='col')
        
        assert result.success is False


# ============================================================================
# DISTRIBUTION FITTER TESTS
# ============================================================================

class TestDistributionFitter:
    """Test DistributionFitter worker."""
    
    def test_valid_input(self, clean_dataframe):
        """Test with valid input."""
        fitter = DistributionFitter()
        result = fitter.safe_execute(df=clean_dataframe, column='values')
        
        assert result.success is True
        assert 'fit_results' in result.data
        assert 'best_fit' in result.data
    
    def test_positive_data_fitting(self, skewed_data):
        """Test fitting with positive-only data."""
        fitter = DistributionFitter()
        result = fitter.safe_execute(df=skewed_data, column='skewed')
        
        assert result.success is True
        assert result.data['distributions_fit'] >= 1
    
    def test_missing_column(self, clean_dataframe):
        """Test with non-existent column."""
        fitter = DistributionFitter()
        result = fitter.safe_execute(df=clean_dataframe, column='nonexistent')
        
        assert result.success is False


# ============================================================================
# DISTRIBUTION COMPARISON TESTS
# ============================================================================

class TestDistributionComparison:
    """Test DistributionComparison worker."""
    
    def test_valid_input(self, clean_dataframe):
        """Test with valid input."""
        comparator = DistributionComparison()
        result = comparator.safe_execute(
            df=clean_dataframe,
            col1='int_col',
            col2='float_col'
        )
        
        assert result.success is True
        assert 'p_value' in result.data
        assert 'distributions_equal' in result.data
    
    def test_missing_columns(self, clean_dataframe):
        """Test with missing column."""
        comparator = DistributionComparison()
        result = comparator.safe_execute(
            df=clean_dataframe,
            col1='nonexistent',
            col2='int_col'
        )
        
        assert result.success is False
    
    def test_no_dataframe(self):
        """Test with missing DataFrame."""
        comparator = DistributionComparison()
        result = comparator.safe_execute(df=None, col1='a', col2='b')
        
        assert result.success is False


# ============================================================================
# SKEWNESS KURTOSIS ANALYZER TESTS
# ============================================================================

class TestSkewnessKurtosisAnalyzer:
    """Test SkewnessKurtosisAnalyzer worker."""
    
    def test_valid_input(self, clean_dataframe):
        """Test with valid input."""
        analyzer = SkewnessKurtosisAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe, column='values')
        
        assert result.success is True
        assert 'skewness' in result.data
        assert 'kurtosis' in result.data
    
    def test_skewed_data(self, skewed_data):
        """Test with skewed data."""
        analyzer = SkewnessKurtosisAnalyzer()
        result = analyzer.safe_execute(df=skewed_data, column='skewed')
        
        assert result.success is True
        assert result.data['skewness'] > 0  # Right-skewed
    
    def test_missing_column(self, clean_dataframe):
        """Test with non-existent column."""
        analyzer = SkewnessKurtosisAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe, column='nonexistent')
        
        assert result.success is False


# ============================================================================
# OUTLIER DETECTOR TESTS
# ============================================================================

class TestOutlierDetector:
    """Test OutlierDetector worker."""
    
    def test_valid_input(self, dataframe_with_outliers):
        """Test with valid input."""
        detector = OutlierDetector()
        result = detector.safe_execute(df=dataframe_with_outliers, column='values')
        
        assert result.success is True
        assert 'outlier_count' in result.data
        assert 'outlier_percentage' in result.data
    
    def test_outlier_detection(self, dataframe_with_outliers):
        """Test that outliers are detected."""
        detector = OutlierDetector()
        result = detector.safe_execute(df=dataframe_with_outliers, column='values')
        
        assert result.success is True
        assert result.data['outlier_count'] > 0  # Should find outliers
    
    def test_custom_threshold(self, dataframe_with_outliers):
        """Test with custom Z-score threshold."""
        detector = OutlierDetector()
        result = detector.safe_execute(
            df=dataframe_with_outliers,
            column='values',
            threshold=2.0
        )
        
        assert result.success is True
        assert result.data['zscore_threshold'] == 2.0
    
    def test_missing_column(self, dataframe_with_outliers):
        """Test with non-existent column."""
        detector = OutlierDetector()
        result = detector.safe_execute(
            df=dataframe_with_outliers,
            column='nonexistent'
        )
        
        assert result.success is False


# ============================================================================
# CORRELATION MATRIX TESTS
# ============================================================================

class TestCorrelationMatrix:
    """Test CorrelationMatrix worker."""
    
    def test_valid_input(self, clean_dataframe):
        """Test with valid input."""
        matrix = CorrelationMatrix()
        result = matrix.safe_execute(df=clean_dataframe)
        
        assert result.success is True
        assert 'correlation_matrix' in result.data
        assert result.data['method'] == 'pearson'
    
    def test_pearson_method(self, clean_dataframe):
        """Test Pearson correlation."""
        matrix = CorrelationMatrix()
        result = matrix.safe_execute(df=clean_dataframe, method='pearson')
        
        assert result.success is True
        assert result.data['method'] == 'pearson'
    
    def test_spearman_method(self, clean_dataframe):
        """Test Spearman correlation."""
        matrix = CorrelationMatrix()
        result = matrix.safe_execute(df=clean_dataframe, method='spearman')
        
        assert result.success is True
        assert result.data['method'] == 'spearman'
    
    def test_kendall_method(self, clean_dataframe):
        """Test Kendall correlation."""
        matrix = CorrelationMatrix()
        result = matrix.safe_execute(df=clean_dataframe, method='kendall')
        
        assert result.success is True
        assert result.data['method'] == 'kendall'
    
    def test_invalid_method(self, clean_dataframe):
        """Test with invalid method."""
        matrix = CorrelationMatrix()
        result = matrix.safe_execute(df=clean_dataframe, method='invalid')
        
        assert result.success is False
    
    def test_no_dataframe(self):
        """Test with missing DataFrame."""
        matrix = CorrelationMatrix()
        result = matrix.safe_execute(df=None)
        
        assert result.success is False


# ============================================================================
# ERROR HANDLING TESTS (ALL WORKERS)
# ============================================================================

class TestErrorHandling:
    """Test error handling across all workers."""
    
    def test_never_raises_numeric_analyzer(self, clean_dataframe):
        """Test that NumericAnalyzer never raises."""
        analyzer = NumericAnalyzer()
        try:
            result = analyzer.safe_execute(df=None)
            assert result.success is False
        except Exception:
            pytest.fail("safe_execute() should never raise")
    
    def test_never_raises_categorical_analyzer(self):
        """Test that CategoricalAnalyzer never raises."""
        analyzer = CategoricalAnalyzer()
        try:
            result = analyzer.safe_execute(df=None)
            assert result.success is False
        except Exception:
            pytest.fail("safe_execute() should never raise")
    
    def test_never_raises_all_workers(self):
        """Test that all workers never raise on bad input."""
        workers = [
            NumericAnalyzer(),
            CategoricalAnalyzer(),
            CorrelationAnalyzer(),
            QualityAssessor(),
            NormalityTester(),
            DistributionFitter(),
            DistributionComparison(),
            SkewnessKurtosisAnalyzer(),
            OutlierDetector(),
            CorrelationMatrix(),
        ]
        
        for worker in workers:
            try:
                result = worker.safe_execute(df=None)
                assert result.success is False
            except Exception:
                pytest.fail(f"{worker.__class__.__name__} raised exception")
    
    def test_quality_score_in_range(self, clean_dataframe):
        """Test that quality score is always 0-1."""
        workers = [
            NumericAnalyzer(),
            CategoricalAnalyzer(),
            CorrelationAnalyzer(),
            QualityAssessor(),
        ]
        
        for worker in workers:
            result = worker.safe_execute(df=clean_dataframe)
            assert 0 <= result.quality_score <= 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test workers working together."""
    
    def test_pipeline_execution(self, clean_dataframe):
        """Test running multiple workers in sequence."""
        workers = [
            NumericAnalyzer(),
            CategoricalAnalyzer(),
            CorrelationAnalyzer(),
            QualityAssessor(),
        ]
        
        for worker in workers:
            result = worker.safe_execute(df=clean_dataframe)
            assert result.success is True
            assert result.quality_score > 0
    
    def test_worker_result_structure(self, clean_dataframe):
        """Test that all workers return proper WorkerResult."""
        analyzer = NumericAnalyzer()
        result = analyzer.safe_execute(df=clean_dataframe)
        
        # Check WorkerResult structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'quality_score')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')
        
        # Check types
        assert isinstance(result.success, bool)
        assert isinstance(result.data, dict)
        assert isinstance(result.quality_score, (int, float))
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
