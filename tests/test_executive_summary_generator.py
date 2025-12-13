"""Tests for ExecutiveSummaryGenerator worker.

Tests quality assessment, recommendations, and consistency checks.
"""

import pytest
import pandas as pd
import numpy as np
from agents.reporter.workers.executive_summary_generator import ExecutiveSummaryGenerator


@pytest.fixture
def generator():
    """Create ExecutiveSummaryGenerator instance."""
    return ExecutiveSummaryGenerator()


@pytest.fixture
def clean_df():
    """Create clean DataFrame for testing."""
    return pd.DataFrame({
        "col1": [1, 2, 3, 4, 5],
        "col2": ["a", "b", "c", "d", "e"],
        "col3": [1.1, 2.2, 3.3, 4.4, 5.5]
    })


@pytest.fixture
def dirty_df():
    """Create DataFrame with quality issues."""
    return pd.DataFrame({
        "col1": [1, 2, None, None, 5, 5, 5],
        "col2": ["a", "b", "c", None, "e", "a", "b"],
        "col3": [1.1, 1.1, 1.1, 1.1, 1.1, 6.6, 7.7]
    })


class TestExecutiveSummaryGenerator:
    """Test ExecutiveSummaryGenerator functionality."""
    
    def test_worker_initialization(self, generator):
        """Worker should initialize correctly."""
        assert generator.worker_name == "executive_summary_generator"
        assert generator.logger is not None
    
    def test_execute_clean_data(self, generator, clean_df):
        """Should generate summary for clean data."""
        result = generator.execute(clean_df)
        
        assert result.success is True
        assert result.worker_name == "executive_summary_generator"
        assert result.task_type == "executive_summary"
        assert "dataset_info" in result.data
        assert "data_quality" in result.data
        assert "summary_statement" in result.data
    
    def test_execute_none_dataframe(self, generator):
        """Should fail gracefully with None DataFrame."""
        result = generator.execute(None)
        
        assert result.success is False
        assert result.has_errors() is True
    
    def test_execute_empty_dataframe(self, generator):
        """Should fail with empty DataFrame."""
        result = generator.execute(pd.DataFrame())
        
        assert result.success is False
    
    def test_dataset_info_structure(self, generator, clean_df):
        """Should include correct dataset info."""
        result = generator.execute(clean_df)
        dataset_info = result.data["dataset_info"]
        
        assert dataset_info["rows"] == 5
        assert dataset_info["columns"] == 3
        assert dataset_info["numeric_columns"] == 2
        assert dataset_info["categorical_columns"] == 1
        assert "memory_mb" in dataset_info
    
    def test_data_quality_metrics(self, generator, clean_df):
        """Should calculate data quality metrics."""
        result = generator.execute(clean_df)
        quality = result.data["data_quality"]
        
        assert "overall_rating" in quality
        assert "quality_score" in quality
        assert "null_percentage" in quality
        assert "duplicate_count" in quality
        assert quality["null_percentage"] == 0.0
        assert quality["duplicate_count"] >= 0
    
    def test_quality_rating_very_good_or_excellent(self, generator, clean_df):
        """Clean data should get Very Good or Excellent rating."""
        result = generator.execute(clean_df)
        rating = result.data["data_quality"]["overall_rating"]
        
        assert rating in ["Excellent", "Very Good"]
    
    def test_quality_rating_poor(self, generator):
        """Dirty data should get lower rating."""
        df = pd.DataFrame({
            "col1": [None, None, None, None, None],
            "col2": [1, 1, 1, 1, 1]
        })
        result = generator.execute(df)
        rating = result.data["data_quality"]["overall_rating"]
        
        assert rating in ["Fair", "Poor"]
    
    def test_null_detection(self, generator):
        """Should correctly detect null values."""
        df = pd.DataFrame({
            "col1": [1, 2, None, None],
            "col2": ["a", None, "c", "d"]
        })
        result = generator.execute(df)
        quality = result.data["data_quality"]
        
        assert quality["null_count"] > 0
        assert quality["null_percentage"] > 0
    
    def test_duplicate_detection(self, generator):
        """Should correctly detect duplicate rows."""
        df = pd.DataFrame({
            "col1": [1, 1, 1, 2, 2],
            "col2": ["a", "a", "a", "b", "b"]
        })
        result = generator.execute(df)
        quality = result.data["data_quality"]
        
        # Should have at least 2 duplicates (3 rows with [1, 'a'] = 2 duplicates)
        assert quality["duplicate_count"] >= 2
    
    def test_completeness_score(self, generator):
        """Should calculate completeness score."""
        df = pd.DataFrame({
            "col1": [1, 2, None, 4, 5]
        })
        result = generator.execute(df)
        quality = result.data["data_quality"]
        
        # 4 out of 5 complete = 80% complete
        assert 75 <= quality["completeness_score"] <= 85
    
    def test_recommendations_present(self, generator, dirty_df):
        """Should include recommendations for dirty data."""
        result = generator.execute(dirty_df)
        recommendations = result.data["recommendations"]
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
    
    def test_recommendations_null_warning(self, generator):
        """Should recommend action for high null percentage."""
        df = pd.DataFrame({
            "col1": [1, None, None, None, None, None]
        })
        result = generator.execute(df)
        recommendations = result.data["recommendations"]
        
        assert any("missing" in rec.lower() for rec in recommendations)
    
    def test_summary_statement_generated(self, generator, clean_df):
        """Should generate human-readable summary."""
        result = generator.execute(clean_df)
        summary = result.data["summary_statement"]
        
        assert isinstance(summary, str)
        assert "rows" in summary.lower() or "columns" in summary.lower()
        assert "quality" in summary.lower()
    
    def test_consistency_checks(self, generator):
        """Should detect consistency issues."""
        df = pd.DataFrame({
            "col1": ["a", "", "  ", "d"],
            "col2": [1, 2, 3, 4]
        })
        result = generator.execute(df)
        consistency = result.data["consistency"]
        
        assert "issues_found" in consistency
        assert isinstance(consistency["issues"], list)
        assert consistency["issues_found"] >= 1
    
    def test_quality_score_calculation(self, generator, clean_df):
        """Quality score should be between 0 and 1."""
        result = generator.execute(clean_df)
        
        assert 0 <= result.quality_score <= 1
        assert isinstance(result.quality_score, float)
    
    def test_quality_score_high_for_clean_data(self, generator, clean_df):
        """Quality score should be high for clean data."""
        result = generator.execute(clean_df)
        
        # Should be >= 0.85 for clean data
        assert result.quality_score >= 0.85
    
    def test_quality_score_low_for_dirty_data(self, generator, dirty_df):
        """Quality score should be lower for dirty data."""
        result = generator.execute(dirty_df)
        
        # Dirty data should have lower score (allow small margin for edge cases)
        assert result.quality_score <= 0.90
    
    def test_rows_processed_tracking(self, generator, clean_df):
        """Should track rows processed."""
        result = generator.execute(clean_df)
        
        assert result.rows_processed == len(clean_df)
    
    def test_date_columns_detected(self, generator):
        """Should detect date columns."""
        df = pd.DataFrame({
            "date_col": pd.date_range("2024-01-01", periods=5),
            "value_col": [1, 2, 3, 4, 5]
        })
        result = generator.execute(df)
        dataset_info = result.data["dataset_info"]
        
        assert dataset_info["date_columns"] >= 1
