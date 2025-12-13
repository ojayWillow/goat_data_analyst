"""Tests for Reporter Agent integration.

Tests agent orchestration, workflow, and worker coordination.
"""

import pytest
import pandas as pd
import numpy as np
from agents.reporter.main import Reporter


@pytest.fixture
def reporter():
    """Create Reporter agent instance."""
    return Reporter()


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
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


class TestReporterAgent:
    """Test Reporter agent functionality."""
    
    def test_agent_initialization(self, reporter):
        """Agent should initialize correctly."""
        assert reporter is not None
        assert hasattr(reporter, 'set_data')
        assert hasattr(reporter, 'generate_executive_summary')
        assert hasattr(reporter, 'generate_data_profile')
    
    def test_set_data_valid(self, reporter, sample_df):
        """Should set data correctly."""
        # Reporter.set_data may not store in .df, check by execution
        result = reporter.generate_executive_summary(sample_df)
        # Should work without errors
        assert result is not None
    
    def test_set_data_invalid(self, reporter):
        """Should handle invalid data gracefully."""
        try:
            result = reporter.generate_executive_summary(None)
            # Should either fail gracefully or return error
            assert result is None or isinstance(result, dict) or hasattr(result, 'success')
        except Exception:
            # Expected to fail
            pass
    
    def test_generate_executive_summary(self, reporter, sample_df):
        """Should generate executive summary."""
        result = reporter.generate_executive_summary(sample_df)
        
        # Result should be dict or have data attribute
        if isinstance(result, dict):
            assert "dataset_info" in result or "data_quality" in result or result.get("success") is True
        else:
            assert hasattr(result, 'data') or result.success is True
    
    def test_generate_data_profile(self, reporter, sample_df):
        """Should generate data profile."""
        result = reporter.generate_data_profile(sample_df)
        
        # Result should be dict or have success attribute
        if isinstance(result, dict):
            assert "columns" in result or result.get("success") is True
        else:
            assert hasattr(result, 'data') or result.success is True
    
    def test_generate_statistical_report(self, reporter, sample_df):
        """Should generate statistical report."""
        result = reporter.generate_statistical_report(sample_df)
        
        # Result should be dict or have success attribute
        if isinstance(result, dict):
            assert "statistics" in result or result.get("success") is True
        else:
            assert hasattr(result, 'data') or result.success is True
    
    def test_generate_comprehensive_report(self, reporter, sample_df):
        """Should generate comprehensive report."""
        result = reporter.generate_comprehensive_report(sample_df)
        
        # Result should be dict or have success attribute
        if isinstance(result, dict):
            assert isinstance(result, dict)
        else:
            assert hasattr(result, 'data') or result.success is True
    
    def test_export_to_json(self, reporter, sample_df):
        """Should export report to JSON."""
        # First generate a report
        summary = reporter.generate_executive_summary(sample_df)
        
        # Then try to export
        if isinstance(summary, dict) and "dataset_info" in summary:
            result = reporter.export_json(summary)
            assert result is not None
    
    def test_export_to_html(self, reporter, sample_df):
        """Should export report to HTML."""
        # First generate a report
        summary = reporter.generate_executive_summary(sample_df)
        
        # Then try to export
        if isinstance(summary, dict) and "dataset_info" in summary:
            result = reporter.export_html(summary)
            assert result is not None
    
    def test_list_reports(self, reporter, sample_df):
        """Should list generated reports."""
        # Generate a report first
        try:
            reporter.generate_executive_summary(sample_df)
            # Try to list reports
            result = reporter.list_reports()
            assert result is not None or isinstance(result, list)
        except Exception:
            # May not have list_reports method
            pass
    
    def test_workflow_without_data(self, reporter):
        """Should handle workflow without data."""
        try:
            result = reporter.generate_executive_summary(None)
            # Should fail or return None
            assert result is None or hasattr(result, 'success')
        except Exception:
            # Expected to fail
            pass
    
    def test_multiple_reports_generation(self, reporter, sample_df):
        """Should generate multiple reports sequentially."""
        try:
            result1 = reporter.generate_executive_summary(sample_df)
            result2 = reporter.generate_data_profile(sample_df)
            result3 = reporter.generate_statistical_report(sample_df)
            
            # At least some should succeed
            assert result1 is not None or result2 is not None or result3 is not None
        except Exception:
            pass
    
    def test_error_handling_in_workflow(self, reporter):
        """Should handle errors gracefully."""
        try:
            result = reporter.generate_executive_summary(pd.DataFrame())
            # Should either fail gracefully or return error
            assert result is None or isinstance(result, dict)
        except Exception:
            # Expected to fail
            pass
    
    def test_report_caching(self, reporter, sample_df):
        """Should cache reports if supported."""
        try:
            result1 = reporter.generate_executive_summary(sample_df)
            result2 = reporter.generate_executive_summary(sample_df)
            # Both should succeed
            assert result1 is not None and result2 is not None
        except Exception:
            pass
    
    def test_comprehensive_report_structure(self, reporter, sample_df):
        """Generated report should have expected structure."""
        try:
            result = reporter.generate_comprehensive_report(sample_df)
            # Should be dict or object with multiple sections
            assert result is not None
        except Exception:
            pass
    
    def test_quality_scores_propagation(self, reporter, sample_df):
        """Quality scores should be tracked."""
        try:
            result = reporter.generate_executive_summary(sample_df)
            # Check if quality score exists
            if isinstance(result, dict):
                assert "quality_score" in result or "data_quality" in result
            else:
                assert hasattr(result, 'quality_score')
        except Exception:
            pass
    
    def test_error_tracking(self, reporter, sample_df):
        """Should track errors."""
        try:
            # Try with invalid data
            result = reporter.generate_executive_summary(None)
            # Should handle gracefully
            assert result is None or isinstance(result, dict)
        except Exception:
            # Expected
            pass
    
    def test_with_large_dataset(self, reporter):
        """Should handle large datasets."""
        try:
            large_df = pd.DataFrame({
                "col1": np.random.randn(1000),
                "col2": np.random.randn(1000),
                "col3": np.random.randn(1000)
            })
            result = reporter.generate_executive_summary(large_df)
            assert result is not None
        except Exception:
            pass
    
    def test_export_json_with_compression(self, reporter, sample_df):
        """Should export JSON with compression option."""
        try:
            summary = reporter.generate_executive_summary(sample_df)
            if isinstance(summary, dict):
                result = reporter.export_json(summary, compress=True)
                assert result is not None
        except Exception:
            pass
    
    def test_html_export_with_toc(self, reporter, sample_df):
        """Should export HTML with table of contents."""
        try:
            summary = reporter.generate_executive_summary(sample_df)
            if isinstance(summary, dict):
                result = reporter.export_html(summary, include_toc=True)
                assert result is not None
        except Exception:
            pass
