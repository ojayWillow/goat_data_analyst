"""Comprehensive tests for Report Generator workers.

Tests all 5 workers:
- TopicAnalyzer
- ChartMapper
- ChartSelector
- ReportFormatter
- CustomizationEngine
"""

import pytest
from typing import Dict, List, Any
from agents.report_generator.workers.topic_analyzer import TopicAnalyzer
from agents.report_generator.workers.chart_mapper import ChartMapper
from agents.report_generator.workers.chart_selector import ChartSelector
from agents.report_generator.workers.report_formatter import ReportFormatter
from agents.report_generator.workers.customization_engine import CustomizationEngine
from core.exceptions import WorkerError


class TestTopicAnalyzer:
    """Test TopicAnalyzer worker."""

    @pytest.fixture
    def analyzer(self):
        """Create TopicAnalyzer instance."""
        return TopicAnalyzer()

    @pytest.fixture
    def sample_narrative(self):
        """Sample narrative for testing."""
        return """
        # Sales Analysis Q4 2024
        
        ## Executive Summary
        Q4 2024 showed strong growth with revenue increasing 15% year-over-year.
        We identified several key trends and anomalies in customer behavior.
        
        ## Key Findings
        - Revenue grew from $500K to $575K
        - Customer acquisition cost decreased 8%
        - Churn rate increased by 2 percentage points
        - Regional performance varied significantly
        
        ## Recommendations
        Focus on retention strategies to address churn.
        Expand successful regional programs.
        """

    def test_initialization(self, analyzer):
        """Test TopicAnalyzer initialization."""
        assert analyzer.name == "TopicAnalyzer"
        assert analyzer.logger is not None
        assert analyzer.error_intelligence is not None

    def test_analyze_narrative_success(self, analyzer, sample_narrative):
        """Test successful narrative analysis."""
        result = analyzer.analyze_narrative(sample_narrative)
        
        assert result is not None
        assert 'topics' in result
        assert 'sections' in result
        assert len(result['topics']) > 0
        assert len(result['sections']) > 0

    def test_extract_narrative_sections(self, analyzer, sample_narrative):
        """Test section extraction."""
        sections = analyzer.extract_narrative_sections(sample_narrative)
        
        assert isinstance(sections, list)
        assert len(sections) > 0
        assert all('section' in s for s in sections)

    def test_analyze_narrative_empty(self, analyzer):
        """Test with empty narrative."""
        with pytest.raises(WorkerError):
            analyzer.analyze_narrative("")

    def test_get_topic_summary(self, analyzer, sample_narrative):
        """Test topic summary generation."""
        analysis = analyzer.analyze_narrative(sample_narrative)
        summary = analyzer.get_topic_summary(analysis)
        
        assert summary is not None
        assert 'primary_topics' in summary
        assert 'secondary_topics' in summary
        assert 'total_topics' in summary


class TestChartMapper:
    """Test ChartMapper worker."""

    @pytest.fixture
    def mapper(self):
        """Create ChartMapper instance."""
        return ChartMapper()

    def test_initialization(self, mapper):
        """Test ChartMapper initialization."""
        assert mapper.name == "ChartMapper"
        assert mapper.logger is not None
        mapping = mapper.get_topic_chart_mapping()
        assert len(mapping) > 0

    def test_get_charts_for_topic_valid(self, mapper):
        """Test getting charts for valid topic."""
        charts = mapper.get_charts_for_topic('trends')
        
        assert isinstance(charts, list)
        assert len(charts) > 0
        assert 'line_chart' in charts or 'area_chart' in charts

    def test_get_charts_for_topic_invalid(self, mapper):
        """Test with invalid topic."""
        with pytest.raises(WorkerError):
            mapper.get_charts_for_topic('invalid_topic')

    def test_get_charts_for_topics(self, mapper):
        """Test getting charts for multiple topics."""
        topics = {'trends': 0.9, 'anomalies': 0.7, 'distribution': 0.6}
        result = mapper.get_charts_for_topics(topics)
        
        assert isinstance(result, dict)
        assert 'trends' in result
        assert len(result['trends']) > 0

    def test_rank_charts_for_topic(self, mapper):
        """Test chart ranking for topic."""
        available_charts = [
            {'type': 'line_chart', 'name': 'Line Chart'},
            {'type': 'bar_chart', 'name': 'Bar Chart'},
            {'type': 'scatter_plot', 'name': 'Scatter Plot'},
        ]
        
        ranked = mapper.rank_charts_for_topic('trends', available_charts)
        
        assert isinstance(ranked, list)
        assert len(ranked) > 0
        # Line chart should be first (primary for trends)
        assert ranked[0].get('type') in ['line_chart', 'area_chart']

    def test_get_topic_info(self, mapper):
        """Test getting topic information."""
        info = mapper.get_topic_info('anomalies')
        
        assert 'topic' in info
        assert info['topic'] == 'anomalies'
        assert 'description' in info
        assert 'primary_charts' in info

    def test_suggest_chart_for_data(self, mapper):
        """Test chart suggestions based on data."""
        suggestions = mapper.suggest_chart_for_data(
            num_variables=2,
            variable_types=['numeric', 'numeric'],
            topic='correlation'
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0


class TestChartSelector:
    """Test ChartSelector worker."""

    @pytest.fixture
    def selector(self):
        """Create ChartSelector instance."""
        return ChartSelector()

    @pytest.fixture
    def sample_sections(self):
        """Sample narrative sections."""
        return [
            {
                'section': 'Overview',
                'topics': {'trends': 0.9, 'performance': 0.8},
                'importance': 'high'
            },
            {
                'section': 'Anomalies',
                'topics': {'anomalies': 0.95, 'distribution': 0.6},
                'importance': 'critical'
            },
            {
                'section': 'Details',
                'topics': {'comparison': 0.7},
                'importance': 'medium'
            }
        ]

    @pytest.fixture
    def sample_charts(self):
        """Sample available charts."""
        return [
            {'id': 'chart_1', 'type': 'line_chart', 'name': 'Line Chart 1'},
            {'id': 'chart_2', 'type': 'scatter_plot', 'name': 'Scatter Plot 1'},
            {'id': 'chart_3', 'type': 'bar_chart', 'name': 'Bar Chart 1'},
            {'id': 'chart_4', 'type': 'heatmap', 'name': 'Heatmap 1'},
            {'id': 'chart_5', 'type': 'box_plot', 'name': 'Box Plot 1'},
        ]

    def test_initialization(self, selector):
        """Test ChartSelector initialization."""
        assert selector.name == "ChartSelector"
        assert selector.logger is not None
        assert selector.chart_mapper is not None

    def test_select_charts_for_narrative(self, selector, sample_sections, sample_charts):
        """Test selecting charts for narrative."""
        result = selector.select_charts_for_narrative(
            sample_sections,
            sample_charts
        )
        
        assert isinstance(result, dict)
        assert 'Overview' in result
        assert len(result['Overview']) > 0
        assert isinstance(result['Overview'], list)

    def test_select_charts_empty_sections(self, selector, sample_charts):
        """Test with empty sections."""
        with pytest.raises(WorkerError):
            selector.select_charts_for_narrative([], sample_charts)

    def test_select_charts_empty_charts(self, selector, sample_sections):
        """Test with empty charts."""
        with pytest.raises(WorkerError):
            selector.select_charts_for_narrative(sample_sections, [])

    def test_select_charts_with_preferences(self, selector, sample_sections, sample_charts):
        """Test chart selection with user preferences."""
        preferences = {
            'exclude_types': ['box_plot'],
            'max_charts': 2
        }
        
        result = selector.select_charts_for_narrative(
            sample_sections,
            sample_charts,
            preferences
        )
        
        # Check preferences were applied
        for charts in result.values():
            for chart in charts:
                assert chart.get('type') != 'box_plot'

    def test_get_selection_summary(self, selector, sample_sections, sample_charts):
        """Test selection summary generation."""
        selected = selector.select_charts_for_narrative(
            sample_sections,
            sample_charts
        )
        
        summary = selector.get_selection_summary(selected)
        
        assert 'sections_count' in summary
        assert 'total_charts' in summary
        assert 'unique_chart_types' in summary


class TestReportFormatter:
    """Test ReportFormatter worker."""

    @pytest.fixture
    def formatter(self):
        """Create ReportFormatter instance."""
        return ReportFormatter()

    @pytest.fixture
    def sample_narrative(self):
        """Sample narrative for formatting."""
        return """# Analysis Results
        
Q4 sales increased by 15% compared to Q3.
Key metrics improved across all regions."""

    @pytest.fixture
    def sample_charts(self):
        """Sample charts for formatting."""
        return {
            'Overview': [
                {'id': 'c1', 'type': 'line_chart', 'name': 'Revenue Trend', 'path': '/charts/trend.png'},
                {'id': 'c2', 'type': 'bar_chart', 'name': 'Regional Performance', 'path': '/charts/regional.png'}
            ],
            'Details': [
                {'id': 'c3', 'type': 'scatter_plot', 'name': 'Customer Analysis', 'path': '/charts/customers.png'}
            ]
        }

    def test_initialization(self, formatter):
        """Test ReportFormatter initialization."""
        assert formatter.name == "ReportFormatter"
        assert formatter.logger is not None

    def test_format_to_html(self, formatter, sample_narrative, sample_charts):
        """Test HTML formatting."""
        html = formatter.format_to_html(
            sample_narrative,
            sample_charts,
            title="Q4 Report"
        )
        
        assert isinstance(html, str)
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '</html>' in html
        assert 'Q4 Report' in html
        assert 'Revenue Trend' in html

    def test_format_to_markdown(self, formatter, sample_narrative, sample_charts):
        """Test Markdown formatting."""
        markdown = formatter.format_to_markdown(
            sample_narrative,
            sample_charts,
            title="Q4 Report"
        )
        
        assert isinstance(markdown, str)
        assert '# Q4 Report' in markdown
        assert sample_narrative in markdown
        assert 'Revenue Trend' in markdown

    def test_format_empty_narrative(self, formatter, sample_charts):
        """Test with empty narrative."""
        with pytest.raises(WorkerError):
            formatter.format_to_html("", sample_charts)

    def test_format_with_metadata(self, formatter, sample_narrative, sample_charts):
        """Test formatting with metadata."""
        metadata = {
            'Author': 'Analytics Team',
            'Date': '2024-12-13',
            'Version': '1.0'
        }
        
        html = formatter.format_to_html(
            sample_narrative,
            sample_charts,
            metadata=metadata
        )
        
        assert 'Analytics Team' in html
        assert '2024-12-13' in html

    def test_get_format_options(self, formatter):
        """Test getting format options."""
        options = formatter.get_format_options()
        
        assert 'formats' in options
        assert 'html' in options['formats']
        assert 'markdown' in options['formats']


class TestCustomizationEngine:
    """Test CustomizationEngine worker."""

    @pytest.fixture
    def engine(self):
        """Create CustomizationEngine instance."""
        return CustomizationEngine()

    def test_initialization(self, engine):
        """Test CustomizationEngine initialization."""
        assert engine.name == "CustomizationEngine"
        assert engine.logger is not None
        assert len(engine.PRESETS) == 5

    def test_get_customization_options(self, engine):
        """Test getting customization options."""
        options = engine.get_customization_options()
        
        assert 'presets' in options
        assert 'chart_categories' in options
        assert 'customization_options' in options

    def test_get_preset(self, engine):
        """Test getting a preset."""
        preset = engine.get_preset('minimal')
        
        assert preset['name'] == 'Minimal'
        assert 'max_charts' in preset
        assert preset['max_charts'] == 1

    def test_get_preset_invalid(self, engine):
        """Test with invalid preset."""
        with pytest.raises(WorkerError):
            engine.get_preset('invalid_preset')

    def test_list_presets(self, engine):
        """Test listing presets."""
        presets = engine.list_presets()
        
        assert isinstance(presets, list)
        assert len(presets) == 5
        assert all('key' in p and 'name' in p for p in presets)

    def test_validate_preferences_valid(self, engine):
        """Test validating valid preferences."""
        prefs = {'max_charts': 5, 'exclude_types': ['pie_chart']}
        result = engine.validate_preferences(prefs)
        
        assert result['valid'] is True
        assert len(result['issues']) == 0

    def test_validate_preferences_invalid(self, engine):
        """Test validating invalid preferences."""
        prefs = {'max_charts': -1}  # Invalid: negative
        result = engine.validate_preferences(prefs)
        
        assert result['valid'] is False
        assert len(result['issues']) > 0

    def test_apply_preferences(self, engine):
        """Test applying preferences."""
        items = [
            {'type': 'line_chart', 'name': 'Chart 1'},
            {'type': 'pie_chart', 'name': 'Chart 2'},
            {'type': 'bar_chart', 'name': 'Chart 3'},
            {'type': 'scatter_plot', 'name': 'Chart 4'},
        ]
        
        prefs = {
            'exclude_types': ['pie_chart'],
            'max_charts': 2
        }
        
        result = engine.apply_preferences(items, prefs)
        
        assert len(result) <= 2
        assert all(c.get('type') != 'pie_chart' for c in result)

    def test_merge_preferences(self, engine):
        """Test merging preset with custom overrides."""
        custom = {'max_charts': 3}
        merged = engine.merge_preferences('minimal', custom)
        
        assert merged['max_charts'] == 3  # Override applied
        assert 'exclude_types' in merged  # From preset

    def test_get_preference_impact(self, engine):
        """Test estimating preference impact."""
        prefs = {'max_charts': 5, 'exclude_types': ['pie_chart']}
        impact = engine.get_preference_impact(20, prefs)
        
        assert 'original_count' in impact
        assert 'estimated_count' in impact
        assert impact['original_count'] == 20
        assert impact['estimated_count'] <= 20

    def test_get_recommendation(self, engine):
        """Test getting preset recommendation."""
        rec = engine.get_recommendation(report_type='presentation')
        assert rec == 'presentation'
        
        rec = engine.get_recommendation(report_type='executive')
        assert rec == 'essential'


class TestWorkerIntegration:
    """Test integration between workers."""

    @pytest.fixture
    def all_workers(self):
        """Create all workers."""
        return {
            'analyzer': TopicAnalyzer(),
            'mapper': ChartMapper(),
            'selector': ChartSelector(),
            'formatter': ReportFormatter(),
            'engine': CustomizationEngine()
        }

    def test_pipeline_flow(self, all_workers):
        """Test complete pipeline flow."""
        # Sample data
        narrative = """
        # Q4 Results
        Revenue increased 15%. Trends show growth.
        Anomalies detected in regional sales.
        """
        
        charts = [
            {'id': 'c1', 'type': 'line_chart', 'name': 'Trend'},
            {'id': 'c2', 'type': 'scatter_plot', 'name': 'Anomalies'},
            {'id': 'c3', 'type': 'bar_chart', 'name': 'Regional'},
        ]
        
        # Step 1: Analyze
        analysis = all_workers['analyzer'].analyze_narrative(narrative)
        assert analysis is not None
        
        # Step 2: Extract sections
        sections = all_workers['analyzer'].extract_narrative_sections(narrative)
        assert len(sections) > 0
        
        # Step 3: Select charts
        selected = all_workers['selector'].select_charts_for_narrative(
            sections,
            charts
        )
        assert len(selected) > 0
        
        # Step 4: Format
        html = all_workers['formatter'].format_to_html(
            narrative,
            selected,
            title="Q4 Report"
        )
        assert '<!DOCTYPE html>' in html
        assert 'Q4 Report' in html

    def test_worker_error_handling(self, all_workers):
        """Test error handling across workers."""
        # Test each worker's error handling
        
        # TopicAnalyzer
        with pytest.raises(WorkerError):
            all_workers['analyzer'].analyze_narrative("")
        
        # ChartMapper
        with pytest.raises(WorkerError):
            all_workers['mapper'].get_charts_for_topic('invalid')
        
        # ReportFormatter
        with pytest.raises(WorkerError):
            all_workers['formatter'].format_to_html("", {})
        
        # CustomizationEngine
        with pytest.raises(WorkerError):
            all_workers['engine'].get_preset('invalid')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
