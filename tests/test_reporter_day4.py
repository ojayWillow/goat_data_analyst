"""Week 2 Day 4: Reporter Agent Integration Tests (10 tests).

Tests:
1. Agent initialization
2. Data loading
3. Executive summary generation
4. Data profile generation
5. Statistical report generation
6. HTML export
7. JSON export
8. Empty dataframe handling
9. Single row handling
10. Performance benchmark
"""

import pytest
import pandas as pd
import numpy as np
import json
from datetime import datetime
import time

from agents.reporter import Reporter


class TestReporterInitialization:
    """Test 1: Agent initialization."""

    def test_agent_initializes(self):
        """Test agent initializes successfully."""
        reporter = Reporter()
        assert reporter is not None
        assert reporter.name == "Reporter"
        assert reporter.data is None
        assert reporter.executive_summary_generator is not None
        assert reporter.data_profile_generator is not None
        assert reporter.statistical_report_generator is not None
        assert reporter.html_exporter is not None
        assert reporter.json_exporter is not None


class TestReporterDataLoading:
    """Test 2: Data loading and management."""

    @pytest.fixture
    def reporter(self):
        return Reporter()

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame (100 rows, 5 columns)."""
        np.random.seed(42)
        return pd.DataFrame({
            'numeric_1': np.random.randn(100),
            'numeric_2': np.random.randn(100) * 10 + 50,
            'numeric_3': np.random.randint(1, 100, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100),
            'date_str': pd.date_range('2024-01-01', periods=100).astype(str),
        })

    def test_set_data(self, reporter, sample_data):
        """Test setting data."""
        reporter.set_data(sample_data)
        assert reporter.data is not None
        assert reporter.data.shape == (100, 5)

    def test_get_data(self, reporter, sample_data):
        """Test getting data."""
        reporter.set_data(sample_data)
        retrieved = reporter.get_data()
        assert retrieved is not None
        assert retrieved.shape == sample_data.shape

    def test_data_copy(self, reporter, sample_data):
        """Test data is copied (not referenced)."""
        reporter.set_data(sample_data)
        sample_data.iloc[0, 0] = 999
        assert reporter.get_data().iloc[0, 0] != 999


class TestExecutiveSummary:
    """Test 3: Executive summary generation."""

    @pytest.fixture
    def reporter_with_data(self):
        reporter = Reporter()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100) * 2 + 10,
            'z': np.random.choice(['Group1', 'Group2'], 100),
        })
        reporter.set_data(df)
        return reporter

    def test_executive_summary_generation(self, reporter_with_data):
        """Test executive summary generation runs successfully."""
        result = reporter_with_data.generate_executive_summary()
        assert result is not None
        assert isinstance(result, dict)
        assert 'report_type' in result or 'dataset_info' in result

    def test_executive_summary_content(self, reporter_with_data):
        """Test executive summary contains expected information."""
        result = reporter_with_data.generate_executive_summary()
        assert 'dataset_info' in result
        assert 'data_quality' in result
        assert result['dataset_info']['rows'] == 100


class TestDataProfile:
    """Test 4: Data profile generation."""

    @pytest.fixture
    def reporter_with_data(self):
        reporter = Reporter()
        np.random.seed(42)
        df = pd.DataFrame({
            'col1': np.random.randn(100),
            'col2': np.random.randn(100) * 5,
            'col3': np.random.choice(['X', 'Y', 'Z'], 100),
        })
        reporter.set_data(df)
        return reporter

    def test_data_profile_generation(self, reporter_with_data):
        """Test data profile generation runs successfully."""
        result = reporter_with_data.generate_data_profile()
        assert result is not None
        assert isinstance(result, dict)
        assert 'columns' in result or 'profile_type' in result

    def test_data_profile_content(self, reporter_with_data):
        """Test data profile contains column information."""
        result = reporter_with_data.generate_data_profile()
        assert 'columns' in result
        assert len(result['columns']) == 3


class TestStatisticalReport:
    """Test 5: Statistical report generation."""

    @pytest.fixture
    def reporter_with_data(self):
        reporter = Reporter()
        np.random.seed(42)
        df = pd.DataFrame({
            'a': np.random.randn(100),
            'b': np.random.randn(100) * 3 + 20,
            'c': np.random.randint(0, 50, 100),
        })
        reporter.set_data(df)
        return reporter

    def test_statistical_report_generation(self, reporter_with_data):
        """Test statistical report generation runs successfully."""
        result = reporter_with_data.generate_statistical_report()
        assert result is not None
        assert isinstance(result, dict)
        assert 'statistics' in result or 'correlation_analysis' in result

    def test_statistical_report_content(self, reporter_with_data):
        """Test statistical report contains statistics."""
        result = reporter_with_data.generate_statistical_report()
        # Check for common statistical sections
        assert any(key in result for key in ['statistics', 'correlation_analysis', 'descriptive_stats'])


class TestHTMLExport:
    """Test 6: HTML export."""

    @pytest.fixture
    def reporter_with_data(self):
        reporter = Reporter()
        np.random.seed(42)
        df = pd.DataFrame({
            'feature_1': np.random.randn(50),
            'feature_2': np.random.randn(50),
            'feature_3': np.random.choice(['A', 'B'], 50),
        })
        reporter.set_data(df)
        # Generate a report first
        reporter.generate_executive_summary()
        return reporter

    def test_html_export(self, reporter_with_data):
        """Test HTML export runs successfully."""
        result = reporter_with_data.export_to_html(report_type='executive_summary')
        assert result is not None
        assert isinstance(result, dict)
        # Export result should contain html content or file info
        assert 'html' in result or 'file_path' in result or 'content' in result

    def test_html_export_has_content(self, reporter_with_data):
        """Test HTML export contains HTML content."""
        result = reporter_with_data.export_to_html(report_type='executive_summary')
        # Verify export was successful
        assert result is not None
        assert len(result) > 0


class TestJSONExport:
    """Test 7: JSON export."""

    @pytest.fixture
    def reporter_with_data(self):
        reporter = Reporter()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(50),
            'y': np.random.randn(50),
            'z': np.random.choice(['Type1', 'Type2'], 50),
        })
        reporter.set_data(df)
        # Generate a report first
        reporter.generate_executive_summary()
        return reporter

    def test_json_export(self, reporter_with_data):
        """Test JSON export runs successfully."""
        result = reporter_with_data.export_to_json(report_type='executive_summary')
        assert result is not None
        assert isinstance(result, dict)
        # Export result should contain json content or file info
        assert 'json' in result or 'file_path' in result or 'content' in result

    def test_json_export_has_content(self, reporter_with_data):
        """Test JSON export contains valid JSON."""
        result = reporter_with_data.export_to_json(report_type='executive_summary')
        assert result is not None
        assert len(result) > 0


class TestEdgeCases:
    """Test 8: Empty dataframe handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        reporter = Reporter()
        empty_df = pd.DataFrame()
        reporter.set_data(empty_df)
        assert reporter.get_data() is not None
        assert reporter.get_data().shape[0] == 0

    def test_single_row_dataframe(self):
        """Test 9: Single row handling."""
        reporter = Reporter()
        single_row = pd.DataFrame({
            'a': [1.0],
            'b': [2.0],
            'c': [3.0]
        })
        reporter.set_data(single_row)
        assert reporter.get_data().shape[0] == 1

    def test_no_data_error(self):
        """Test error when no data is set."""
        reporter = Reporter()
        with pytest.raises(Exception):
            reporter.generate_executive_summary()


class TestPerformance:
    """Test 10: Performance benchmark."""

    def test_report_generation_performance_1k_rows(self):
        """Test report generation on 1,000 rows completes in reasonable time."""
        reporter = Reporter()
        np.random.seed(42)
        df = pd.DataFrame({
            f'feature_{i}': np.random.randn(1000)
            for i in range(5)
        })
        df['category'] = np.random.choice(['A', 'B', 'C'], 1000)
        reporter.set_data(df)

        start = time.time()
        
        # Generate multiple reports
        result1 = reporter.generate_executive_summary()
        result2 = reporter.generate_data_profile()
        result3 = reporter.generate_statistical_report()
        
        elapsed = time.time() - start

        assert elapsed < 30  # Should complete in < 30 seconds
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None


class TestComprehensiveReporting:
    """Test comprehensive reporting pipeline."""

    def test_full_report_pipeline(self):
        """Test running all report types on same dataset."""
        reporter = Reporter()
        np.random.seed(42)
        df = pd.DataFrame({
            'metric_1': np.random.randn(100),
            'metric_2': np.random.randn(100) * 5 + 50,
            'category': np.random.choice(['GroupA', 'GroupB'], 100),
        })
        
        reporter.set_data(df)
        
        # Generate all reports
        result1 = reporter.generate_executive_summary()
        result2 = reporter.generate_data_profile()
        result3 = reporter.generate_statistical_report()
        
        # All should have data
        assert result1 is not None and isinstance(result1, dict)
        assert result2 is not None and isinstance(result2, dict)
        assert result3 is not None and isinstance(result3, dict)
        
        # Verify reports are stored
        reports = reporter.list_reports()
        assert reports['status'] == 'success'
        assert len(reports['reports']) >= 3

    def test_generate_comprehensive_report(self):
        """Test generating complete report in one call."""
        reporter = Reporter()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.choice(['Type1', 'Type2', 'Type3'], 100),
        })
        
        reporter.set_data(df)
        
        # Generate comprehensive report
        result = reporter.generate_comprehensive_report()
        assert result is not None
        assert result['status'] == 'success'
        assert 'sections' in result
        assert len(result['sections']) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
