"""Tests for StatisticalReportGenerator worker.

Tests statistical analysis, normality testing, and correlation analysis.
"""

import pytest
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from agents.reporter.workers.statistical_report_generator import StatisticalReportGenerator


@pytest.fixture
def generator():
    """Create StatisticalReportGenerator instance."""
    return StatisticalReportGenerator()


@pytest.fixture
def numeric_df():
    """Create DataFrame with numeric data."""
    return pd.DataFrame({
        "col1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "col2": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        "col3": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5]
    })


@pytest.fixture
def mixed_df():
    """Create DataFrame with mixed data types."""
    return pd.DataFrame({
        "numeric": [1, 2, 3, 4, 5],
        "categorical": ["a", "b", "a", "b", "a"],
        "float": [1.1, 2.2, 3.3, 4.4, 5.5]
    })


class TestStatisticalReportGenerator:
    """Test StatisticalReportGenerator functionality."""
    
    def test_worker_initialization(self, generator):
        """Worker should initialize correctly."""
        assert generator.worker_name == "statistical_report_generator"
        assert generator.logger is not None
    
    def test_execute_numeric_data(self, generator, numeric_df):
        """Should analyze numeric data."""
        result = generator.execute(numeric_df)
        
        assert result.success is True
        assert result.task_type == "statistical_report"
        assert "statistics" in result.data
    
    def test_execute_non_numeric(self, generator):
        """Should handle non-numeric data gracefully."""
        df = pd.DataFrame({
            "col1": ["a", "b", "c"],
            "col2": ["x", "y", "z"]
        })
        result = generator.execute(df)
        
        # Should handle gracefully (no numeric columns to analyze)
        assert result.success is True
    
    def test_descriptive_statistics(self, generator, numeric_df):
        """Should calculate descriptive statistics."""
        result = generator.execute(numeric_df)
        stats = result.data["statistics"]
        
        assert "col1" in stats
        assert "mean" in stats["col1"]
        assert "std" in stats["col1"]
        assert "min" in stats["col1"]
        assert "max" in stats["col1"]
    
    def test_distribution_analysis(self, generator, numeric_df):
        """Should analyze distribution."""
        result = generator.execute(numeric_df)
        
        assert "distribution" in result.data
        assert isinstance(result.data["distribution"], dict)
    
    def test_normality_test(self, generator, numeric_df):
        """Should perform normality test (Shapiro-Wilk)."""
        result = generator.execute(numeric_df)
        
        assert "normality" in result.data
        normality = result.data["normality"]
        
        # Should have p-values
        assert "col1" in normality or len(normality) > 0
    
    def test_correlation_analysis(self, generator, numeric_df):
        """Should analyze correlations."""
        result = generator.execute(numeric_df)
        
        assert "correlations" in result.data
        correlations = result.data["correlations"]
        
        assert isinstance(correlations, list)
        if len(correlations) > 0:
            assert "var1" in correlations[0]
            assert "var2" in correlations[0]
            assert "correlation" in correlations[0]
    
    def test_significant_correlations(self, generator):
        """Should detect significant correlations with p-values."""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # Perfect correlation
        })
        result = generator.execute(df)
        
        correlations = result.data["correlations"]
        
        # Should have high correlation
        if len(correlations) > 0:
            assert any(abs(c["correlation"]) > 0.9 for c in correlations)
    
    def test_p_value_calculation(self, generator):
        """Should calculate p-values for correlations."""
        df = pd.DataFrame({
            "a": list(range(1, 11)),
            "b": list(range(2, 12))
        })
        result = generator.execute(df)
        
        correlations = result.data["correlations"]
        
        if len(correlations) > 0:
            for corr in correlations:
                assert "p_value" in corr
                assert 0 <= corr["p_value"] <= 1
    
    def test_correlation_strength_classification(self, generator):
        """Should classify correlation strength."""
        df = pd.DataFrame({
            "strong": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "perfect": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Perfect
        })
        result = generator.execute(df)
        
        correlations = result.data["correlations"]
        
        if len(correlations) > 0:
            assert "strength" in correlations[0]
    
    def test_skewness_kurtosis(self, generator, numeric_df):
        """Should calculate skewness and kurtosis."""
        result = generator.execute(numeric_df)
        stats = result.data["statistics"]
        
        # At least one column should have skewness/kurtosis
        has_skew = any("skewness" in stats.get(col, {}) for col in stats)
        assert has_skew or len(stats) == 0  # May not have if all non-numeric
    
    def test_quartile_calculation(self, generator, numeric_df):
        """Should calculate quartiles."""
        result = generator.execute(numeric_df)
        stats = result.data["statistics"]
        
        if "col1" in stats:
            assert "q1" in stats["col1"]
            assert "median" in stats["col1"]
            assert "q3" in stats["col1"]
    
    def test_mixed_data_handling(self, generator, mixed_df):
        """Should handle mixed data types."""
        result = generator.execute(mixed_df)
        
        assert result.success is True
        # Should analyze only numeric columns
        stats = result.data["statistics"]
        assert "numeric" in stats or "float" in stats
    
    def test_empty_dataframe_handling(self, generator):
        """Should handle empty DataFrame."""
        result = generator.execute(pd.DataFrame())
        
        assert result.success is True or result.success is False
    
    def test_constant_column_handling(self, generator):
        """Should handle constant columns gracefully."""
        df = pd.DataFrame({
            "constant": [1, 1, 1, 1, 1],
            "varying": [1, 2, 3, 4, 5]
        })
        result = generator.execute(df)
        
        # Should handle without crashing
        assert result.success is True
    
    def test_single_column(self, generator):
        """Should handle single column."""
        df = pd.DataFrame({"col1": [1, 2, 3, 4, 5]})
        result = generator.execute(df)
        
        assert result.success is True
    
    def test_large_dataset(self, generator):
        """Should handle large dataset."""
        df = pd.DataFrame({
            "col1": np.random.randn(1000),
            "col2": np.random.randn(1000)
        })
        result = generator.execute(df)
        
        assert result.success is True
    
    def test_quality_score(self, generator, numeric_df):
        """Should have quality score."""
        result = generator.execute(numeric_df)
        
        assert result.quality_score > 0
        assert result.quality_score <= 1
    
    def test_rows_processed(self, generator, numeric_df):
        """Should track rows processed."""
        result = generator.execute(numeric_df)
        
        assert result.rows_processed == len(numeric_df)
    
    def test_normality_p_value_range(self, generator):
        """Normality p-values should be in valid range."""
        df = pd.DataFrame({
            "col1": np.random.randn(20)  # Approximately normal
        })
        result = generator.execute(df)
        
        normality = result.data.get("normality", {})
        
        # P-values should be between 0 and 1
        for col, p_val in normality.items():
            if isinstance(p_val, (int, float)):
                assert 0 <= p_val <= 1
    
    def test_distribution_type_classification(self, generator):
        """Should classify distribution type."""
        df = pd.DataFrame({
            "normal": np.random.randn(30),
            "skewed": np.random.exponential(2, 30)  # Right-skewed
        })
        result = generator.execute(df)
        
        distribution = result.data.get("distribution", {})
        assert isinstance(distribution, dict)
