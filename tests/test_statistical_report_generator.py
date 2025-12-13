"""Tests for StatisticalReportGenerator worker.

Tests distribution analysis, normality tests, and correlation significance.
"""

import pytest
import pandas as pd
import numpy as np
from agents.reporter.workers.statistical_report_generator import StatisticalReportGenerator


@pytest.fixture
def generator():
    """Create StatisticalReportGenerator instance."""
    return StatisticalReportGenerator()


@pytest.fixture
def numeric_df():
    """Create DataFrame with numeric data."""
    np.random.seed(42)
    return pd.DataFrame({
        "age": np.random.normal(40, 10, 100),
        "income": np.random.normal(50000, 15000, 100),
        "score": np.random.uniform(0, 100, 100)
    })


@pytest.fixture
def correlated_df():
    """Create DataFrame with correlated columns."""
    np.random.seed(42)
    x = np.random.normal(0, 1, 100)
    return pd.DataFrame({
        "x": x,
        "y": 2 * x + np.random.normal(0, 0.1, 100),  # Strong correlation
        "z": np.random.normal(0, 1, 100)  # Independent
    })


class TestStatisticalReportGenerator:
    """Test StatisticalReportGenerator functionality."""
    
    def test_worker_initialization(self, generator):
        """Worker should initialize correctly."""
        assert generator.worker_name == "statistical_report_generator"
        assert generator.logger is not None
    
    def test_execute_numeric_data(self, generator, numeric_df):
        """Should generate report for numeric data."""
        result = generator.execute(numeric_df)
        
        assert result.success is True
        assert result.task_type == "statistical_report"
    
    def test_execute_non_numeric_data(self, generator):
        """Should handle non-numeric data gracefully."""
        df = pd.DataFrame({
            "name": ["A", "B", "C"],
            "category": ["X", "Y", "Z"]
        })
        result = generator.execute(df)
        
        assert result.success is True
        assert "message" in result.data or len(result.warnings) > 0
    
    def test_execute_mixed_data(self, generator):
        """Should extract numeric columns from mixed data."""
        df = pd.DataFrame({
            "name": ["A", "B", "C"],
            "value": [1, 2, 3],
            "score": [10, 20, 30]
        })
        result = generator.execute(df)
        
        assert result.success is True
        assert result.data["numeric_columns_analyzed"] == 2
    
    def test_descriptive_statistics(self, generator, numeric_df):
        """Should include descriptive statistics."""
        result = generator.execute(numeric_df)
        stats = result.data["statistics"]
        
        assert "age" in stats or "count" in str(stats)
        assert len(stats) > 0
    
    def test_distribution_analysis_present(self, generator, numeric_df):
        """Should include distribution analysis."""
        result = generator.execute(numeric_df)
        dist_analysis = result.data["distribution_analysis"]
        
        assert len(dist_analysis) > 0
    
    def test_distribution_skewness(self, generator, numeric_df):
        """Should calculate skewness for distributions."""
        result = generator.execute(numeric_df)
        dist = result.data["distribution_analysis"]
        
        for col_name, metrics in dist.items():
            assert "skewness" in metrics
            assert isinstance(metrics["skewness"], float)
    
    def test_distribution_kurtosis(self, generator, numeric_df):
        """Should calculate kurtosis for distributions."""
        result = generator.execute(numeric_df)
        dist = result.data["distribution_analysis"]
        
        for col_name, metrics in dist.items():
            assert "kurtosis" in metrics
            assert isinstance(metrics["kurtosis"], float)
    
    def test_distribution_type_classification(self, generator, numeric_df):
        """Should classify distribution types."""
        result = generator.execute(numeric_df)
        dist = result.data["distribution_analysis"]
        
        for col_name, metrics in dist.items():
            assert "distribution_type" in metrics
            assert metrics["distribution_type"] in [
                "Normal-like", "Right-skewed", "Left-skewed", "Other"
            ]
    
    def test_distribution_description(self, generator, numeric_df):
        """Should provide human-readable distribution description."""
        result = generator.execute(numeric_df)
        dist = result.data["distribution_analysis"]
        
        for col_name, metrics in dist.items():
            assert "description" in metrics
            assert isinstance(metrics["description"], str)
    
    def test_normality_tests_present(self, generator, numeric_df):
        """Should include normality tests."""
        result = generator.execute(numeric_df)
        tests = result.data["normality_tests"]
        
        assert len(tests) > 0
    
    def test_shapiro_wilk_test(self, generator, numeric_df):
        """Should perform Shapiro-Wilk test."""
        result = generator.execute(numeric_df)
        tests = result.data["normality_tests"]
        
        for col_name, test_result in tests.items():
            assert test_result["test"] == "Shapiro-Wilk"
            assert "statistic" in test_result
            assert "p_value" in test_result
            assert "is_normal" in test_result
    
    def test_normality_p_value_range(self, generator, numeric_df):
        """P-values should be between 0 and 1."""
        result = generator.execute(numeric_df)
        tests = result.data["normality_tests"]
        
        for col_name, test_result in tests.items():
            p_val = test_result["p_value"]
            assert 0 <= p_val <= 1
    
    def test_correlation_matrix_present(self, generator, correlated_df):
        """Should include correlation matrix."""
        result = generator.execute(correlated_df)
        corr = result.data["correlation_analysis"]
        
        assert "correlation_matrix" in corr
        assert len(corr["correlation_matrix"]) > 0
    
    def test_p_values_matrix_present(self, generator, correlated_df):
        """Should include p-values matrix."""
        result = generator.execute(correlated_df)
        corr = result.data["correlation_analysis"]
        
        assert "p_values_matrix" in corr
        assert len(corr["p_values_matrix"]) > 0
    
    def test_significant_correlations_detected(self, generator, correlated_df):
        """Should detect significant correlations."""
        result = generator.execute(correlated_df)
        corr = result.data["correlation_analysis"]
        
        sig_corrs = corr["significant_correlations"]
        # Should find correlation between x and y
        assert len(sig_corrs) > 0
    
    def test_correlation_strength_classification(self, generator, correlated_df):
        """Should classify correlation strength."""
        result = generator.execute(correlated_df)
        corr = result.data["correlation_analysis"]
        
        sig_corrs = corr["significant_correlations"]
        for corr_pair in sig_corrs:
            assert "strength" in corr_pair
            assert corr_pair["strength"] in [
                "Very Strong", "Strong", "Moderate", "Weak", "Very Weak"
            ]
    
    def test_correlation_pair_format(self, generator, correlated_df):
        """Correlation pairs should have correct format."""
        result = generator.execute(correlated_df)
        corr = result.data["correlation_analysis"]
        
        sig_corrs = corr["significant_correlations"]
        for pair in sig_corrs:
            assert "pair" in pair
            assert "correlation" in pair
            assert "p_value" in pair
            assert "significant" in pair
            assert len(pair["pair"]) == 2
    
    def test_no_correlation_with_single_column(self, generator):
        """Should handle single numeric column."""
        df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
        result = generator.execute(df)
        
        # Should complete without error
        assert result.success is True
    
    def test_quality_score_high(self, generator, numeric_df):
        """Quality score should be high for good data."""
        result = generator.execute(numeric_df)
        
        assert result.quality_score > 0.9
    
    def test_rows_processed_tracking(self, generator, numeric_df):
        """Should track rows processed."""
        result = generator.execute(numeric_df)
        
        assert result.rows_processed == len(numeric_df)
    
    def test_execution_time_tracked(self, generator, numeric_df):
        """Should track execution time."""
        result = generator.safe_execute(numeric_df)
        
        assert result.execution_time_ms >= 0
    
    def test_nan_handling(self, generator):
        """Should handle NaN values gracefully."""
        df = pd.DataFrame({
            "col1": [1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10],
            "col2": [10, 20, 30, np.nan, 50, 60, 70, 80, 90, 100]
        })
        result = generator.execute(df)
        
        # Should complete without error
        assert result.success is True
    
    def test_constant_column_handling(self, generator):
        """Should handle constant columns (zero variance)."""
        df = pd.DataFrame({
            "constant": [5, 5, 5, 5, 5],
            "variable": [1, 2, 3, 4, 5]
        })
        result = generator.execute(df)
        
        # Should complete without error
        assert result.success is True
    
    def test_correlation_with_independent_variables(self, generator, numeric_df):
        """Should show weak/no correlation for independent variables."""
        result = generator.execute(numeric_df)
        corr = result.data["correlation_analysis"]
        
        # With random independent variables, correlations should be weak
        # This test just ensures the correlation analysis runs
        assert "correlation_matrix" in corr
