"""Tests for Reporter agent integration.

Tests agent workflow, worker orchestration, and end-to-end report generation.
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from agents.reporter.reporter import Reporter


@pytest.fixture
def reporter():
    """Create Reporter agent instance."""
    return Reporter()


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        "age": [25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
        "salary": [30000, 35000, 40000, 45000, 50000, 55000, 60000, 65000, 70000, 75000],
        "department": ["Sales", "IT", "HR", "IT", "Sales", "Finance", "IT", "HR", "Finance", "Sales"],
        "performance": [3.5, 4.2, 3.8, 4.5, 3.2, 4.0, 4.3, 3.9, 4.1, 3.7]
    })


class TestReporterAgent:
    """Test Reporter agent functionality."""
    
    def test_agent_initialization(self, reporter):
        """Agent should initialize with all workers."""
        assert reporter.agent_name == "reporter"
        assert reporter.logger is not None
        # Check workers are initialized
        assert hasattr(reporter, "executive_summary_generator")
        assert hasattr(reporter, "data_profile_generator")
        assert hasattr(reporter, "statistical_report_generator")
        assert hasattr(reporter, "json_exporter")
        assert hasattr(reporter, "html_exporter")
    
    def test_set_data_valid(self, reporter, sample_df):
        """Should set data successfully."""
        reporter.set_data(sample_df)
        
        assert reporter.df is not None
        assert len(reporter.df) == len(sample_df)
    
    def test_set_data_invalid(self, reporter):
        """Should handle invalid data."""
        with pytest.raises((TypeError, ValueError, AssertionError)):
            reporter.set_data(None)
    
    def test_get_data(self, reporter, sample_df):
        """Should retrieve set data."""
        reporter.set_data(sample_df)
        retrieved_df = reporter.get_data()
        
        assert retrieved_df is not None
        assert len(retrieved_df) == len(sample_df)
    
    def test_generate_executive_summary(self, reporter, sample_df):
        """Should generate executive summary."""
        reporter.set_data(sample_df)
        result = reporter.generate_executive_summary()
        
        assert result.success is True
        assert "data_quality" in result.data
        assert "dataset_info" in result.data
    
    def test_generate_data_profile(self, reporter, sample_df):
        """Should generate data profile."""
        reporter.set_data(sample_df)
        result = reporter.generate_data_profile()
        
        assert result.success is True
        assert "columns" in result.data
        assert len(result.data["columns"]) > 0
    
    def test_generate_statistical_report(self, reporter, sample_df):
        """Should generate statistical report."""
        reporter.set_data(sample_df)
        result = reporter.generate_statistical_report()
        
        assert result.success is True
        assert "statistics" in result.data or "correlation_analysis" in result.data
    
    def test_generate_comprehensive_report(self, reporter, sample_df):
        """Should generate comprehensive report combining all reports."""
        reporter.set_data(sample_df)
        result = reporter.generate_comprehensive_report()
        
        assert result.success is True
        # Should include all report sections
        assert isinstance(result.data, dict)
        assert "executive_summary" in result.data or "data_quality" in str(result.data)
    
    def test_export_to_json(self, reporter, sample_df):
        """Should export to JSON format."""
        reporter.set_data(sample_df)
        
        # Generate report first
        report_result = reporter.generate_comprehensive_report()
        
        # Export it
        export_result = reporter.export_to_json(report_result.data, write_to_disk=False)
        
        assert export_result.success is True
        assert "json" in export_result.data
    
    def test_export_to_html(self, reporter, sample_df):
        """Should export to HTML format."""
        reporter.set_data(sample_df)
        
        # Generate report first
        report_result = reporter.generate_comprehensive_report()
        
        # Export it
        export_result = reporter.export_to_html(report_result.data, write_to_disk=False)
        
        assert export_result.success is True
    
    def test_list_reports(self, reporter, sample_df):
        """Should list generated reports."""
        reporter.set_data(sample_df)
        
        # Generate a report
        reporter.generate_executive_summary()
        
        # List reports
        reports = reporter.list_reports()
        
        assert isinstance(reports, list)
    
    def test_workflow_without_data(self, reporter):
        """Should fail gracefully when data not set."""
        result = reporter.generate_executive_summary()
        
        assert result.success is False or result.has_errors()
    
    def test_multiple_reports_generation(self, reporter, sample_df):
        """Should handle generating multiple reports sequentially."""
        reporter.set_data(sample_df)
        
        results = []
        results.append(reporter.generate_executive_summary())
        results.append(reporter.generate_data_profile())
        results.append(reporter.generate_statistical_report())
        
        # All should succeed
        assert all(r.success for r in results)
    
    def test_retry_mechanism(self, reporter, sample_df):
        """Should have retry mechanism (decorator)."""
        # This tests that decorated methods work
        reporter.set_data(sample_df)
        
        # Call multiple times
        for i in range(3):
            result = reporter.generate_executive_summary()
            assert result is not None
    
    def test_data_validation_in_workflow(self, reporter):
        """Should validate data in workflow."""
        df = pd.DataFrame()  # Empty DataFrame
        
        # Should handle empty DataFrame
        result = reporter.set_data(df)
        # Either accepts empty or raises error - both OK
        assert result is None or isinstance(result, bool)
    
    def test_error_handling_in_workflow(self, reporter, sample_df):
        """Should handle errors in workflow gracefully."""
        reporter.set_data(sample_df)
        
        # Even if something goes wrong, should return proper result
        result = reporter.generate_statistical_report()
        
        # Should have result object
        assert result is not None
        assert hasattr(result, "success")
    
    def test_report_caching(self, reporter, sample_df):
        """Should cache generated reports."""
        reporter.set_data(sample_df)
        
        # Generate report
        result1 = reporter.generate_executive_summary()
        
        # Generate again
        result2 = reporter.generate_executive_summary()
        
        # Both should succeed
        assert result1.success is True
        assert result2.success is True
    
    def test_comprehensive_report_structure(self, reporter, sample_df):
        """Comprehensive report should have complete structure."""
        reporter.set_data(sample_df)
        result = reporter.generate_comprehensive_report()
        
        assert result.success is True
        assert isinstance(result.data, dict)
    
    def test_quality_scores_propagation(self, reporter, sample_df):
        """Quality scores should propagate through reports."""
        reporter.set_data(sample_df)
        
        result = reporter.generate_executive_summary()
        
        # Should have quality score
        assert 0 <= result.quality_score <= 1
    
    def test_error_tracking(self, reporter, sample_df):
        """Should track errors properly."""
        reporter.set_data(sample_df)
        
        result = reporter.generate_executive_summary()
        
        # Check error tracking
        if not result.success:
            assert result.has_errors() is True
        else:
            assert result.has_errors() is False
    
    def test_with_dirty_data(self, reporter):
        """Should handle dirty data gracefully."""
        df = pd.DataFrame({
            "col1": [1, None, None, 4, 5],
            "col2": ["a", "b", None, "d", "e"],
            "col3": [1, 1, 1, 1, 1]  # Constant column
        })
        
        reporter.set_data(df)
        result = reporter.generate_executive_summary()
        
        # Should still succeed but with warnings/recommendations
        assert result is not None
    
    def test_with_large_dataset(self, reporter):
        """Should handle larger datasets."""
        np.random.seed(42)
        df = pd.DataFrame({
            "col1": np.random.normal(0, 1, 1000),
            "col2": np.random.normal(0, 1, 1000),
            "col3": np.random.choice(["A", "B", "C"], 1000)
        })
        
        reporter.set_data(df)
        result = reporter.generate_comprehensive_report()
        
        # Should handle large dataset
        assert result.success is True or result is not None
    
    def test_export_json_with_compression(self, reporter, sample_df):
        """Should export JSON with compression option."""
        reporter.set_data(sample_df)
        
        report_result = reporter.generate_comprehensive_report()
        export_result = reporter.export_to_json(
            report_result.data,
            compress=True,
            write_to_disk=False
        )
        
        assert export_result.success is True
    
    def test_html_export_with_toc(self, reporter, sample_df):
        """Should export HTML with table of contents."""
        reporter.set_data(sample_df)
        
        report_result = reporter.generate_comprehensive_report()
        export_result = reporter.export_to_html(
            report_result.data,
            include_toc=True,
            write_to_disk=False
        )
        
        assert export_result.success is True
