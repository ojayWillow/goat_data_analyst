"""Integration tests for ReportGenerator agent.

Tests the complete report generation pipeline:
- Agent initialization
- Worker coordination
- Data flow
- Error handling
- Output validation
"""

import pytest
from typing import Dict, List, Any
from agents.report_generator.report_generator import ReportGenerator
from core.exceptions import WorkerError


class TestReportGeneratorInitialization:
    """Test ReportGenerator initialization."""

    def test_initialization(self):
        """Test agent initializes with all workers."""
        agent = ReportGenerator()
        
        assert agent.name == "ReportGenerator"
        assert agent.logger is not None
        assert agent.structured_logger is not None
        assert agent.topic_analyzer is not None
        assert agent.chart_mapper is not None
        assert agent.chart_selector is not None
        assert agent.report_formatter is not None
        assert agent.customization_engine is not None

    def test_workers_connected(self):
        """Test all workers are properly connected."""
        agent = ReportGenerator()
        
        # Test worker names
        assert agent.topic_analyzer.name == "TopicAnalyzer"
        assert agent.chart_mapper.name == "ChartMapper"
        assert agent.chart_selector.name == "ChartSelector"
        assert agent.report_formatter.name == "ReportFormatter"
        assert agent.customization_engine.name == "CustomizationEngine"

    def test_chart_mapper_passed_to_selector(self):
        """Test ChartMapper is passed to ChartSelector."""
        agent = ReportGenerator()
        
        # ChartSelector should have reference to ChartMapper
        assert agent.chart_selector.chart_mapper is not None
        assert agent.chart_selector.chart_mapper.name == "ChartMapper"


class TestAnalyzeNarrative:
    """Test narrative analysis through agent."""

    @pytest.fixture
    def agent(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    @pytest.fixture
    def sample_narrative(self):
        """Sample narrative."""
        return """
        # Quarterly Report Q4 2024
        
        ## Executive Summary
        This quarter showed exceptional growth with revenue up 15% YoY.
        We identified key market trends and customer anomalies.
        
        ## Key Metrics
        - Revenue: $575K (up from $500K)
        - Customer Growth: 20%
        - Churn Rate: 3.2%
        
        ## Recommendations
        Focus on retention and regional expansion.
        """

    def test_analyze_narrative_success(self, agent, sample_narrative):
        """Test successful narrative analysis."""
        result = agent.analyze_narrative(sample_narrative)
        
        assert result is not None
        assert 'topics' in result
        assert 'sections' in result
        assert len(result['topics']) > 0

    def test_analyze_empty_narrative(self, agent):
        """Test with empty narrative."""
        with pytest.raises(WorkerError):
            agent.analyze_narrative("")


class TestSelectCharts:
    """Test chart selection through agent."""

    @pytest.fixture
    def agent(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    @pytest.fixture
    def sample_narrative(self):
        """Sample narrative."""
        return """
        Revenue trends show consistent growth.
        Customer distribution varies by region.
        Anomalies detected in Q2 data.
        """

    @pytest.fixture
    def sample_charts(self):
        """Sample available charts."""
        return [
            {'id': 'chart_1', 'type': 'line_chart', 'name': 'Revenue Trend', 'path': '/charts/trend.png'},
            {'id': 'chart_2', 'type': 'scatter_plot', 'name': 'Customer Distribution', 'path': '/charts/dist.png'},
            {'id': 'chart_3', 'type': 'box_plot', 'name': 'Anomalies', 'path': '/charts/anomalies.png'},
            {'id': 'chart_4', 'type': 'bar_chart', 'name': 'Regional Comparison', 'path': '/charts/regional.png'},
            {'id': 'chart_5', 'type': 'heatmap', 'name': 'Correlation Matrix', 'path': '/charts/corr.png'},
        ]

    def test_select_charts_success(self, agent, sample_narrative, sample_charts):
        """Test successful chart selection."""
        result = agent.select_charts_for_narrative(
            sample_narrative,
            sample_charts
        )
        
        assert isinstance(result, dict)
        assert len(result) > 0
        # Each value should be a list of charts
        for charts in result.values():
            assert isinstance(charts, list)

    def test_select_charts_empty_narrative(self, agent, sample_charts):
        """Test with empty narrative."""
        with pytest.raises(WorkerError):
            agent.select_charts_for_narrative("", sample_charts)

    def test_select_charts_empty_charts(self, agent, sample_narrative):
        """Test with no available charts."""
        with pytest.raises(WorkerError):
            agent.select_charts_for_narrative(sample_narrative, [])

    def test_select_charts_with_preferences(self, agent, sample_narrative, sample_charts):
        """Test chart selection with user preferences."""
        preferences = {
            'exclude_types': ['box_plot'],
            'max_charts': 2,
            'prefer_types': ['line_chart', 'bar_chart']
        }
        
        result = agent.select_charts_for_narrative(
            sample_narrative,
            sample_charts,
            preferences
        )
        
        # Verify preferences applied
        for charts in result.values():
            assert all(c.get('type') != 'box_plot' for c in charts)
            assert len(charts) <= 2


class TestGenerateReport:
    """Test complete report generation."""

    @pytest.fixture
    def agent(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    @pytest.fixture
    def sample_data(self):
        """Sample data for report generation."""
        return {
            'narrative': """
            # Sales Analysis Q4 2024
            
            Q4 demonstrated strong performance with 15% growth.
            Regional trends show variation across markets.
            Customer anomalies identified in certain segments.
            
            ## Recommendations
            Expand successful regions and investigate anomalies.
            """,
            'charts': [
                {'id': 'c1', 'type': 'line_chart', 'name': 'Growth Trend', 'path': '/charts/trend.png'},
                {'id': 'c2', 'type': 'bar_chart', 'name': 'Regional Performance', 'path': '/charts/regions.png'},
                {'id': 'c3', 'type': 'scatter_plot', 'name': 'Customer Analysis', 'path': '/charts/customers.png'},
                {'id': 'c4', 'type': 'heatmap', 'name': 'Market Heat', 'path': '/charts/heat.png'},
            ],
            'title': 'Q4 2024 Sales Report',
            'metadata': {
                'Author': 'Analytics Team',
                'Date': '2024-12-13',
                'Version': '1.0'
            }
        }

    def test_generate_html_report(self, agent, sample_data):
        """Test HTML report generation."""
        report = agent.generate_html_report(
            sample_data['narrative'],
            sample_data['charts'],
            sample_data['title']
        )
        
        assert report is not None
        assert report['status'] == 'success'
        assert report['format'] == 'html'
        assert report['title'] == sample_data['title']
        assert 'formatted_content' in report
        assert '<!DOCTYPE html>' in report['formatted_content']

    def test_generate_markdown_report(self, agent, sample_data):
        """Test Markdown report generation."""
        report = agent.generate_markdown_report(
            sample_data['narrative'],
            sample_data['charts'],
            sample_data['title']
        )
        
        assert report is not None
        assert report['status'] == 'success'
        assert report['format'] == 'markdown'
        assert '# Q4 2024 Sales Report' in report['formatted_content']

    def test_generate_report_with_metadata(self, agent, sample_data):
        """Test report generation with metadata."""
        report = agent.generate_report(
            sample_data['narrative'],
            sample_data['charts'],
            sample_data['title'],
            output_format='html',
            metadata=sample_data['metadata']
        )
        
        assert report is not None
        assert 'Analytics Team' in report['formatted_content']
        assert '2024-12-13' in report['formatted_content']

    def test_generate_report_with_preferences(self, agent, sample_data):
        """Test report generation with user preferences."""
        preferences = {'max_charts': 2, 'exclude_types': ['heatmap']}
        
        report = agent.generate_report(
            sample_data['narrative'],
            sample_data['charts'],
            sample_data['title'],
            output_format='html',
            user_preferences=preferences
        )
        
        assert report is not None
        assert report['summary']['total_charts'] <= 2

    def test_generate_report_invalid_format(self, agent, sample_data):
        """Test with invalid output format."""
        with pytest.raises(WorkerError):
            agent.generate_report(
                sample_data['narrative'],
                sample_data['charts'],
                sample_data['title'],
                output_format='invalid'
            )

    def test_generate_report_empty_narrative(self, agent, sample_data):
        """Test with empty narrative."""
        with pytest.raises(WorkerError):
            agent.generate_report(
                "",
                sample_data['charts'],
                sample_data['title']
            )

    def test_generate_report_empty_charts(self, agent, sample_data):
        """Test with empty charts list."""
        with pytest.raises(WorkerError):
            agent.generate_report(
                sample_data['narrative'],
                [],
                sample_data['title']
            )

    def test_report_contains_summary(self, agent, sample_data):
        """Test that report contains summary information."""
        report = agent.generate_html_report(
            sample_data['narrative'],
            sample_data['charts'],
            sample_data['title']
        )
        
        assert 'summary' in report
        assert 'sections' in report['summary']
        assert 'total_charts' in report['summary']
        assert 'word_count' in report['summary']

    def test_report_is_tracked(self, agent, sample_data):
        """Test that generated reports are tracked."""
        initial_count = len(agent.generated_reports)
        
        agent.generate_html_report(
            sample_data['narrative'],
            sample_data['charts'],
            sample_data['title']
        )
        
        assert len(agent.generated_reports) == initial_count + 1


class TestCustomizationMethods:
    """Test customization-related methods."""

    @pytest.fixture
    def agent(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    def test_get_customization_options(self, agent):
        """Test getting customization options."""
        options = agent.get_customization_options()
        
        assert 'presets' in options
        assert 'chart_categories' in options
        assert 'customization_options' in options

    def test_get_preset(self, agent):
        """Test getting a preset."""
        preset = agent.get_preset('minimal')
        
        assert preset is not None
        assert preset['name'] == 'Minimal'

    def test_list_presets(self, agent):
        """Test listing presets."""
        presets = agent.list_presets()
        
        assert isinstance(presets, list)
        assert len(presets) == 5

    def test_validate_preferences(self, agent):
        """Test validating preferences."""
        prefs = {'max_charts': 5}
        result = agent.validate_preferences(prefs)
        
        assert result['valid'] is True


class TestStatusMethods:
    """Test status reporting methods."""

    @pytest.fixture
    def agent(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    def test_get_status(self, agent):
        """Test getting agent status."""
        status = agent.get_status()
        
        assert status['name'] == 'ReportGenerator'
        assert status['status'] == 'active'
        assert status['workers'] == 5

    def test_get_detailed_status(self, agent):
        """Test getting detailed status."""
        status = agent.get_detailed_status()
        
        assert status['workers'] is not None
        assert 'topic_analyzer' in status['workers']
        assert 'chart_mapper' in status['workers']
        assert 'chart_selector' in status['workers']
        assert 'report_formatter' in status['workers']
        assert 'customization_engine' in status['workers']
        assert 'capabilities' in status


class TestErrorRecovery:
    """Test error handling and recovery."""

    @pytest.fixture
    def agent(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    def test_handles_missing_narrative(self, agent):
        """Test handling of missing narrative."""
        with pytest.raises(WorkerError):
            agent.generate_report(
                "",
                [{'type': 'line_chart', 'name': 'Chart'}],
                "Test"
            )

    def test_handles_invalid_format(self, agent):
        """Test handling of invalid format."""
        with pytest.raises(WorkerError):
            agent.generate_report(
                "Test narrative",
                [{'type': 'line_chart', 'name': 'Chart'}],
                "Test",
                output_format='invalid_format'
            )

    def test_retry_on_error(self, agent):
        """Test retry decorator on errors."""
        # This tests that retry_on_error decorator is applied
        # by attempting an operation that might fail
        try:
            result = agent.analyze_narrative("Test narrative with content")
            assert result is not None
        except Exception as e:
            # Verify it's a WorkerError (not a raw exception)
            assert isinstance(e, WorkerError)


class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""

    @pytest.fixture
    def agent(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    def test_full_workflow_scenario_1(self, agent):
        """Test complete workflow - Executive Summary."""
        narrative = """
        # Executive Summary
        
        Q4 2024 results exceeded expectations with 20% growth.
        All regions performed well with strong margins.
        Customer satisfaction increased to 92%.
        
        ## Key Achievements
        - Revenue: $650K
        - New Customers: 150
        - Retention: 96%
        """
        
        charts = [
            {'id': 'c1', 'type': 'bar_chart', 'name': 'Revenue by Region', 'path': '/charts/revenue.png'},
            {'id': 'c2', 'type': 'line_chart', 'name': 'Growth Trend', 'path': '/charts/trend.png'},
            {'id': 'c3', 'type': 'pie_chart', 'name': 'Customer Distribution', 'path': '/charts/dist.png'},
        ]
        
        # Generate report
        report = agent.generate_html_report(
            narrative,
            charts,
            "Executive Summary Q4 2024"
        )
        
        # Verify report
        assert report['status'] == 'success'
        assert 'Executive Summary Q4 2024' in report['formatted_content']
        assert report['summary']['total_charts'] > 0
        assert report['summary']['word_count'] > 0

    def test_full_workflow_scenario_2(self, agent):
        """Test complete workflow - Detailed Analysis with Preferences."""
        narrative = """
        # Detailed Analysis
        
        Customer segments show different behaviors.
        Regional anomalies require investigation.
        Predictive models suggest continued growth.
        """
        
        charts = [
            {'id': 'c1', 'type': 'scatter_plot', 'name': 'Customer Segments'},
            {'id': 'c2', 'type': 'heatmap', 'name': 'Regional Anomalies'},
            {'id': 'c3', 'type': 'box_plot', 'name': 'Distribution'},
            {'id': 'c4', 'type': 'line_chart', 'name': 'Forecast'},
            {'id': 'c5', 'type': 'bar_chart', 'name': 'Metrics'},
        ]
        
        preferences = {
            'preset': 'essential',
            'max_charts': 3,
            'exclude_types': ['pie_chart']
        }
        
        # Generate report with preferences
        report = agent.generate_markdown_report(
            narrative,
            charts,
            "Detailed Analysis",
            preferences
        )
        
        # Verify report
        assert report['status'] == 'success'
        assert report['format'] == 'markdown'
        assert report['summary']['total_charts'] <= 3

    def test_workflow_with_all_formats(self, agent):
        """Test workflow generating reports in all formats."""
        narrative = "Test narrative with insights and findings."
        charts = [{'id': 'c1', 'type': 'line_chart', 'name': 'Test Chart'}]
        
        # Generate HTML
        html_report = agent.generate_html_report(narrative, charts, "Test")
        assert html_report['format'] == 'html'
        assert '<!DOCTYPE html>' in html_report['formatted_content']
        
        # Generate Markdown
        md_report = agent.generate_markdown_report(narrative, charts, "Test")
        assert md_report['format'] == 'markdown'
        assert '# Test' in md_report['formatted_content']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
