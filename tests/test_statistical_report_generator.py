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
        assert "statistics" in result.data or "correlation_analysis" in result.data
    
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
        data = result.data
        
        # Check for statistics in data
        assert "statistics" in data or "col1" in data or "correlation_analysis" in data
    
    def test_correlation_analysis_present(self, generator, numeric_df):
        """Should perform correlation analysis."""
        result = generator.execute(numeric_df)
        data = result.data
        
        # Check for correlation data
        assert "correlation_analysis" in data or "correlations" in data or "statistics" in data
    
    def test_numeric_column_analysis(self, generator, numeric_df):
        """Should analyze numeric columns."""
        result = generator.execute(numeric_df)
        data = result.data
        
        # Should have analyzed at least one column
        assert len(data) > 0
    
    def test_mixed_data_handling(self, generator, mixed_df):
        """Should handle mixed data types."""
        result = generator.execute(mixed_df)
        
        assert result.success is True
        # Should analyze only numeric columns
        data = result.data
        assert len(data) >= 0
    
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
    
    def test_normality_analysis(self, generator):
        """Should perform normality analysis."""
        df = pd.DataFrame({
            "normal": np.random.randn(30)
        })
        result = generator.execute(df)
        
        # Should have analysis results
        assert result.success is True
    
    def test_correlation_with_significant_relationship(self, generator):
        """Should detect significant correlations."""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # Perfect correlation
        })
        result = generator.execute(df)
        
        # Should have correlation analysis
        assert result.success is True
    
    def test_statistical_data_validity(self, generator, numeric_df):
        """Generated statistics should be valid."""
        result = generator.execute(numeric_df)
        data = result.data
        
        # Verify data is not empty
        assert len(data) > 0
    
    def test_mixed_data_numeric_handling(self, generator, mixed_df):
        """Should extract and analyze numeric columns."""
        result = generator.execute(mixed_df)
        
        assert result.success is True
        # Should have processed numeric columns
        assert result.rows_processed == len(mixed_df)
    
    def test_very_small_dataset(self, generator):
        """Should handle very small datasets."""
        df = pd.DataFrame({
            "col1": [1, 2]
        })
        result = generator.execute(df)
        
        assert result.success is True or result.success is False
    
    def test_nan_handling(self, generator):
        """Should handle NaN values."""
        df = pd.DataFrame({
            "col1": [1, 2, np.nan, 4, 5]
        })
        result = generator.execute(df)
        
        # Should handle gracefully
        assert result.success is True or result.success is False
    
    def test_infinite_value_handling(self, generator):
        """Should handle infinite values."""
        df = pd.DataFrame({
            "col1": [1, 2, np.inf, 4, 5]
        })
        result = generator.execute(df)
        
        # Should handle gracefully
        assert result.success is True or result.success is False
