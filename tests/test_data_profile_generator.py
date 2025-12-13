"""Tests for DataProfileGenerator worker.

Tests column profiling, outlier detection, distribution analysis, and cardinality assessment.
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
        "age": [25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
        "salary": [30000, 35000, 40000, 45000, 50000, 55000, 60000, 65000, 70000, 75000],
        "score": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    })


@pytest.fixture
def mixed_df():
    """Create DataFrame with mixed types."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "score": [85.5, 90.2, 78.3, 92.1, 88.7],
        "date": pd.date_range("2024-01-01", periods=5)
    })


class TestDataProfileGenerator:
    """Test DataProfileGenerator functionality."""
    
    def test_worker_initialization(self, generator):
        """Worker should initialize correctly."""
        assert generator.worker_name == "data_profile_generator"
        assert generator.logger is not None
    
    def test_execute_numeric_data(self, generator, numeric_df):
        """Should generate profile for numeric data."""
        result = generator.execute(numeric_df)
        
        assert result.success is True
        assert "columns" in result.data
        assert len(result.data["columns"]) == 3
    
    def test_execute_mixed_data(self, generator, mixed_df):
        """Should handle mixed data types."""
        result = generator.execute(mixed_df)
        
        assert result.success is True
        assert "columns" in result.data
        assert len(result.data["columns"]) == 5
    
    def test_execute_empty_dataframe(self, generator):
        """Should fail with empty DataFrame."""
        result = generator.execute(pd.DataFrame())
        
        assert result.success is False
    
    def test_column_data_type_detection(self, generator, mixed_df):
        """Should correctly detect column data types."""
        result = generator.execute(mixed_df)
        columns = result.data["columns"]
        
        assert "int" in columns["id"]["data_type"]
        assert "object" in columns["name"]["data_type"]
        assert "float" in columns["score"]["data_type"]
    
    def test_null_value_tracking(self, generator):
        """Should track null values per column."""
        df = pd.DataFrame({
            "col1": [1, 2, None, 4, 5],
            "col2": ["a", "b", "c", None, "e"]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert columns["col1"]["missing_values"] == 1
        assert columns["col2"]["missing_values"] == 1
    
    def test_unique_value_counting(self, generator, mixed_df):
        """Should count unique values."""
        result = generator.execute(mixed_df)
        columns = result.data["columns"]
        
        # All unique in id
        assert columns["id"]["unique_values"] == 5
        # Less unique in category
        assert columns["category"]["unique_values"] == 3
    
    def test_completeness_calculation(self, generator):
        """Should calculate completeness percentage."""
        df = pd.DataFrame({
            "col1": [1, 2, None, 4, 5]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        # 4 out of 5 complete = 80%
        assert 75 <= columns["col1"]["completeness"] <= 85
    
    def test_cardinality_assessment_low(self, generator):
        """Should assess cardinality as low for binary columns."""
        df = pd.DataFrame({
            "binary": [0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert columns["binary"]["cardinality"] == "Low"
    
    def test_cardinality_assessment_high(self, generator):
        """Should assess cardinality as high for unique columns."""
        df = pd.DataFrame({
            "unique": list(range(100))
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        assert columns["unique"]["cardinality"] == "High"
    
    def test_numeric_column_statistics(self, generator, numeric_df):
        """Should include statistics for numeric columns."""
        result = generator.execute(numeric_df)
        columns = result.data["columns"]
        
        age_stats = columns["age"]["statistics"]
        assert "mean" in age_stats
        assert "median" in age_stats
        assert "std" in age_stats
        assert "min" in age_stats
        assert "max" in age_stats
    
    def test_numeric_distribution_metrics(self, generator, numeric_df):
        """Should calculate distribution metrics for numeric columns."""
        result = generator.execute(numeric_df)
        columns = result.data["columns"]
        
        age_dist = columns["age"]["distribution"]
        assert "skewness" in age_dist
        assert "kurtosis" in age_dist
        assert "range" in age_dist
    
    def test_outlier_detection(self, generator):
        """Should detect outliers using IQR method."""
        df = pd.DataFrame({
            "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is outlier
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        outliers = columns["values"]["outliers"]
        assert outliers["count"] >= 1
        assert outliers["percentage"] > 0
    
    def test_categorical_value_distribution(self, generator, mixed_df):
        """Should analyze categorical value distributions."""
        result = generator.execute(mixed_df)
        columns = result.data["columns"]
        
        cat_dist = columns["category"]["value_distribution"]
        assert "total_distinct" in cat_dist
        assert "diversity_score" in cat_dist
        assert "top_values" in cat_dist
    
    def test_datetime_column_analysis(self, generator, mixed_df):
        """Should analyze datetime columns."""
        result = generator.execute(mixed_df)
        columns = result.data["columns"]
        
        date_info = columns["date"]["datetime_info"]
        assert "min_date" in date_info
        assert "max_date" in date_info
        assert "date_range_days" in date_info
    
    def test_summary_statistics(self, generator, numeric_df):
        """Should include summary statistics."""
        result = generator.execute(numeric_df)
        summary = result.data["summary_statistics"]
        
        assert summary["total_rows"] == 10
        assert summary["total_columns"] == 3
        assert summary["numeric_columns"] == 3
    
    def test_quality_score_calculation(self, generator, numeric_df):
        """Should calculate overall quality score."""
        result = generator.execute(numeric_df)
        
        assert 0 <= result.quality_score <= 1
    
    def test_quality_score_high_for_complete_data(self, generator, numeric_df):
        """Quality score should be high for complete data."""
        result = generator.execute(numeric_df)
        
        assert result.quality_score > 0.95
    
    def test_quality_score_low_for_incomplete_data(self, generator):
        """Quality score should be lower for incomplete data."""
        df = pd.DataFrame({
            "col1": [None] * 10,
            "col2": [1, None, None, None, None, None, None, None, None, None]
        })
        result = generator.execute(df)
        
        assert result.quality_score < 0.5
    
    def test_rows_processed_tracking(self, generator, numeric_df):
        """Should track rows processed."""
        result = generator.execute(numeric_df)
        
        assert result.rows_processed == len(numeric_df)
    
    def test_execution_time_tracked(self, generator, numeric_df):
        """Should track execution time."""
        result = generator.safe_execute(numeric_df)
        
        assert result.execution_time_ms >= 0
    
    def test_nan_handling_in_numeric_stats(self, generator):
        """Should properly handle NaN values in statistics."""
        df = pd.DataFrame({
            "values": [1.0, 2.0, np.nan, 4.0, 5.0]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        # Should complete without error
        assert "statistics" in columns["values"]
        assert result.success is True
    
    def test_zero_variance_column(self, generator):
        """Should handle zero-variance columns."""
        df = pd.DataFrame({
            "constant": [1, 1, 1, 1, 1]
        })
        result = generator.execute(df)
        columns = result.data["columns"]
        
        dist = columns["constant"]["distribution"]
        # All same value = zero skewness
        assert dist["skewness"] == 0.0
