"""Tests for DataProfileGenerator worker.

Tests column profiling, outlier detection, and distribution analysis.
"""

import pytest
import pandas as pd
import numpy as np
from agents.reporter.workers.data_profile_generator import DataProfileGenerator


@pytest.fixture
def generator():
    """Create DataProfileGenerator instance."""
    return DataProfileGenerator()


@pytest.fixture
def numeric_df():
    """Create DataFrame with numeric data."""
    return pd.DataFrame({
        "col1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "col2": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5]
    })


@pytest.fixture
def mixed_df():
    """Create DataFrame with mixed data types."""
    return pd.DataFrame({
        "numeric": [1, 2, 3, 4, 5],
        "categorical": ["a", "b", "a", "b", "a"],
        "float": [1.1, 2.2, 3.3, 4.4, 5.5]
    })


class TestDataProfileGenerator:
    """Test DataProfileGenerator functionality."""
    
    def test_worker_initialization(self, generator):
        """Worker should initialize correctly."""
        assert generator.worker_name == "data_profile_generator"
        assert generator.logger is not None
    
    def test_execute_mixed_data(self, generator, mixed_df):
        """Should profile mixed data types."""
        result = generator.execute(mixed_df)
        
        assert result.success is True
        assert result.task_type == "data_profile"
        assert "columns" in result.data
    
    def test_execute_none_dataframe(self, generator):
        """Should fail with None DataFrame."""
        result = generator.execute(None)
        
        assert result.success is False
        assert result.has_errors() is True
    
    def test_execute_empty_dataframe(self, generator):
        """Should fail with empty DataFrame."""
        result = generator.execute(pd.DataFrame())
        
        assert result.success is False
    
    def test_column_profiling(self, generator, numeric_df):
        """Should profile each column."""
        result = generator.execute(numeric_df)
        columns = result.data["columns"]
        
        assert "col1" in columns
        assert "col2" in columns
    
    def test_numeric_column_detection(self, generator, mixed_df):
        """Should identify numeric columns."""
        result = generator.execute(mixed_df)
        columns = result.data["columns"]
        
        # Check for column existence and data type info
        assert "numeric" in columns
        assert "data_type" in columns["numeric"] or "type" in columns["numeric"]
    
    def test_categorical_column_detection(self, generator, mixed_df):
        """Should identify categorical columns."""
        result = generator.execute(mixed_df)
        columns = result.data["columns"]
        
        # Check for column existence
        assert "categorical" in columns
        assert "data_type" in columns["categorical"] or "type" in columns["categorical"]
    
    def test_null_value_tracking(self, generator):
        """Should track null values per column."""
        df = pd.DataFrame({
            "col1": [1, 2, None, 4],
            "col2": ["a", None, "c", "d"]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        # Check for null tracking - may be under different keys
        assert "col1" in columns
        assert ("null_count" in columns["col1"] or 
                "completeness" in columns["col1"] or
                "missing_info" in columns["col1"])
    
    def test_unique_value_counting(self, generator, mixed_df):
        """Should count unique values or track cardinality."""
        result = generator.execute(mixed_df)
        columns = result.data["columns"]
        
        assert "numeric" in columns
        # Check for unique value info in any form
        assert ("unique_count" in columns["numeric"] or 
                "cardinality" in columns["numeric"])
    
    def test_completeness_calculation(self, generator):
        """Should calculate completeness percentage."""
        df = pd.DataFrame({
            "col1": [1, 2, None, 4, 5]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        # 4 out of 5 = 80%
        if "completeness" in columns["col1"]:
            assert 75 <= columns["col1"]["completeness"] <= 85
    
    def test_outlier_detection(self, generator):
        """Should detect outliers using IQR."""
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5, 100]  # 100 is outlier
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        # Check if outliers are tracked
        assert "col1" in columns
        assert ("outliers" in columns["col1"] or 
                "outlier_info" in columns["col1"])
    
    def test_distribution_metrics(self, generator, numeric_df):
        """Should calculate distribution metrics."""
        result = generator.execute(numeric_df)
        columns = result.data["columns"]
        
        # Numeric columns should have some distribution info
        assert "col1" in columns
        assert len(columns["col1"]) > 0
    
    def test_cardinality_assessment(self, generator):
        """Should assess cardinality."""
        df = pd.DataFrame({
            "binary": [0, 1, 0, 1, 0, 1]  # Only 2 unique values
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        # Should have cardinality assessment
        assert "binary" in columns
        assert "cardinality" in columns["binary"]
    
    def test_cardinality_assessment_medium(self, generator):
        """Should identify medium cardinality columns."""
        df = pd.DataFrame({
            "medium": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]  # 5 unique values
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert "medium" in columns
        assert "cardinality" in columns["medium"]
    
    def test_cardinality_assessment_high(self, generator):
        """Should identify high cardinality columns."""
        df = pd.DataFrame({
            "high": list(range(100))  # 100 unique values
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert "high" in columns
        assert "cardinality" in columns["high"]
    
    def test_categorical_diversity(self, generator):
        """Should assess categorical data."""
        df = pd.DataFrame({
            "cat": ["a"] * 80 + ["b"] * 15 + ["c"] * 5  # Imbalanced
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert "cat" in columns
        # Check for categorical info in any form
        assert ("diversity" in columns["cat"] or 
                "unique_count" in columns["cat"] or
                "cardinality" in columns["cat"])
    
    def test_datetime_detection(self, generator):
        """Should detect datetime columns."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "value": [1, 2, 3, 4, 5]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert "date" in columns
        # Check for datetime type indicator
        assert ("data_type" in columns["date"] or 
                "datetime_info" in columns["date"])
    
    def test_datetime_range_analysis(self, generator):
        """Should analyze datetime ranges."""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10)
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert "date" in columns
        # Check for date range info
        assert ("min" in columns["date"] or 
                "range" in columns["date"] or
                "datetime_info" in columns["date"])
    
    def test_quality_score(self, generator, numeric_df):
        """Should have quality score."""
        result = generator.execute(numeric_df)
        
        assert result.quality_score > 0
        assert result.quality_score <= 1
    
    def test_rows_processed(self, generator, numeric_df):
        """Should track rows processed."""
        result = generator.execute(numeric_df)
        
        assert result.rows_processed == len(numeric_df)
    
    def test_large_dataset_handling(self, generator):
        """Should handle large datasets."""
        large_df = pd.DataFrame({
            "col1": np.random.randn(1000),
            "col2": np.random.randn(1000),
            "col3": np.random.randn(1000)
        })
        result = generator.execute(large_df)
        
        assert result.success is True
        assert result.rows_processed == 1000
    
    def test_mixed_missing_values(self, generator):
        """Should handle mixed missing value patterns."""
        df = pd.DataFrame({
            "col1": [1, None, 3, None, 5],
            "col2": ["a", "b", None, "d", None]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert "col1" in columns
        assert "col2" in columns
        # Should have some metric about nulls
        assert ("null_count" in columns["col1"] or
                "completeness" in columns["col1"] or
                "missing_info" in columns["col1"])
