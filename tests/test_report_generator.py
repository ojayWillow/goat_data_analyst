"""Tests for Report Generator Segment.

Comprehensive testing of all workers and main coordinator:
- TopicAnalyzer
- ChartMapper
- ChartSelector
- ReportFormatter
- CustomizationEngine
- ReportGenerator (main)
"""

import pytest
from agents.report_generator import ReportGenerator
from agents.report_generator.workers import (
    TopicAnalyzer,
    ChartMapper,
    ChartSelector,
    ReportFormatter,
    CustomizationEngine
)


class TestTopicAnalyzer:
    """Test TopicAnalyzer worker."""

    @pytest.fixture
    def analyzer(self):
        return TopicAnalyzer()

    @pytest.fixture
    def sample_narrative(self):
        return """
        You have 23 anomalies in your sales data (2.3% of total records).
        These anomalies show an unusual pattern in Q3. The trend is generally
        increasing over time with a declining section in August.
        There is a strong correlation between marketing spend and sales volume.
        We recommend immediate action to investigate the anomalies and optimize
        spending during peak periods.
        """

    def test_initialization(self, analyzer):
        assert analyzer.name == "TopicAnalyzer"

    def test_analyze_narrative(self, analyzer, sample_narrative):
        result = analyzer.analyze_narrative(sample_narrative)
        
        assert 'topics' in result
        assert 'sections' in result
        assert 'structure' in result
        assert result['word_count'] > 0

    def test_extract_topics(self, analyzer, sample_narrative):
        result = analyzer.analyze_narrative(sample_narrative)
        topics = result['topics']
        
        # Check that expected topics are found
        assert 'anomalies' in topics
        assert 'trends' in topics
        assert 'correlation' in topics
        assert 'recommendations' in topics

    def test_extract_narrative_sections(self, analyzer, sample_narrative):
        sections = analyzer.extract_narrative_sections(sample_narrative)
        
        assert len(sections) > 0
        for section in sections:
            assert 'text' in section
            assert 'topics' in section
            assert 'importance' in section

    def test_get_topic_summary(self, analyzer):
        topics = {'anomalies': 0.8, 'trends': 0.6, 'correlation': 0.5}
        summary = analyzer.get_topic_summary(topics)
        
        assert summary['total_topics'] == 3
        assert summary['primary_topics']
        assert summary['avg_confidence'] > 0


class TestChartMapper:
    """Test ChartMapper worker."""

    @pytest.fixture
    def mapper(self):
        return ChartMapper()

    def test_initialization(self, mapper):
        assert mapper.name == "ChartMapper"

    def test_get_topic_chart_mapping(self, mapper):
        mapping = mapper.get_topic_chart_mapping()
        
        assert 'anomalies' in mapping
        assert 'trends' in mapping
        assert 'correlation' in mapping

    def test_get_charts_for_topic(self, mapper):
        charts = mapper.get_charts_for_topic('anomalies')
        
        assert len(charts) > 0
        assert 'scatter_plot' in charts
        assert 'heatmap' in charts

    def test_get_charts_for_multiple_topics(self, mapper):
        topics = {'anomalies': 0.8, 'trends': 0.6}
        charts = mapper.get_charts_for_topics(topics)
        
        assert 'anomalies' in charts
        assert 'trends' in charts

    def test_rank_charts_for_topic(self, mapper):
        available = [
            {'id': '1', 'type': 'scatter_plot', 'name': 'Scatter'},
            {'id': '2', 'type': 'histogram', 'name': 'Histogram'},
            {'id': '3', 'type': 'line_chart', 'name': 'Line'}
        ]
        
        ranked = mapper.rank_charts_for_topic('anomalies', available)
        
        assert len(ranked) > 0
        # Scatter plot should be first (primary for anomalies)
        assert ranked[0]['type'] in ['scatter_plot', 'heatmap', 'box_plot']

    def test_get_topic_info(self, mapper):
        info = mapper.get_topic_info('anomalies')
        
        assert info['topic'] == 'anomalies'
        assert 'primary_charts' in info
        assert 'secondary_charts' in info
        assert 'avoid_charts' in info


class TestChartSelector:
    """Test ChartSelector worker."""

    @pytest.fixture
    def selector(self):
        return ChartSelector()

    @pytest.fixture
    def sample_sections(self):
        return [
            {
                'section': 'Executive Summary',
                'topics': {'anomalies': 0.8, 'trends': 0.7},
                'importance': 'high'
            },
            {
                'section': 'Findings',
                'topics': {'correlation': 0.6},
                'importance': 'medium'
            }
        ]

    @pytest.fixture
    def sample_charts(self):
        return [
            {'id': '1', 'type': 'scatter_plot', 'name': 'Scatter Plot'},
            {'id': '2', 'type': 'line_chart', 'name': 'Line Chart'},
            {'id': '3', 'type': 'heatmap', 'name': 'Heatmap'},
            {'id': '4', 'type': 'bar_chart', 'name': 'Bar Chart'},
        ]

    def test_initialization(self, selector):
        assert selector.name == "ChartSelector"

    def test_select_charts_for_narrative(self, selector, sample_sections, sample_charts):
        selected = selector.select_charts_for_narrative(
            sample_sections,
            sample_charts
        )
        
        assert len(selected) > 0
        for section, charts in selected.items():
            assert isinstance(charts, list)

    def test_select_charts_with_preferences(self, selector, sample_sections, sample_charts):
        preferences = {
            'exclude_types': ['heatmap'],
            'max_charts': 2
        }
        
        selected = selector.select_charts_for_narrative(
            sample_sections,
            sample_charts,
            preferences
        )
        
        # Check heatmaps are excluded
        for section, charts in selected.items():
            assert all(c.get('type') != 'heatmap' for c in charts)

    def test_get_selection_summary(self, selector, sample_sections, sample_charts):
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
        return ReportFormatter()

    @pytest.fixture
    def sample_narrative(self):
        return "You have 5 critical issues and 3 warnings in your dataset. The trends show improvement over time."

    @pytest.fixture
    def sample_charts(self):
        return {
            'Executive Summary': [
                {'name': 'Anomalies', 'type': 'scatter_plot', 'path': 'chart1.png'}
            ],
            'Findings': [
                {'name': 'Trends', 'type': 'line_chart', 'path': 'chart2.png'}
            ]
        }

    def test_initialization(self, formatter):
        assert formatter.name == "ReportFormatter"

    def test_format_to_html(self, formatter, sample_narrative, sample_charts):
        html = formatter.format_to_html(
            sample_narrative,
            sample_charts,
            title="Test Report"
        )
        
        assert isinstance(html, str)
        assert '<!DOCTYPE html>' in html
        assert 'Test Report' in html
        assert sample_narrative in html

    def test_format_to_markdown(self, formatter, sample_narrative, sample_charts):
        markdown = formatter.format_to_markdown(
            sample_narrative,
            sample_charts,
            title="Test Report"
        )
        
        assert isinstance(markdown, str)
        assert '# Test Report' in markdown
        assert sample_narrative in markdown

    def test_get_format_options(self, formatter):
        options = formatter.get_format_options()
        
        assert 'formats' in options
        assert 'html' in options['formats']
        assert 'markdown' in options['formats']


class TestCustomizationEngine:
    """Test CustomizationEngine worker."""

    @pytest.fixture
    def engine(self):
        return CustomizationEngine()

    def test_initialization(self, engine):
        assert engine.name == "CustomizationEngine"

    def test_list_presets(self, engine):
        presets = engine.list_presets()
        
        assert len(presets) > 0
        preset_names = [p['key'] for p in presets]
        assert 'minimal' in preset_names
        assert 'essential' in preset_names
        assert 'complete' in preset_names

    def test_get_preset(self, engine):
        preset = engine.get_preset('essential')
        
        assert preset['name'] == 'Essential'
        assert 'max_charts' in preset
        assert 'exclude_types' in preset

    def test_validate_preferences(self, engine):
        prefs = {'max_charts': 5, 'exclude_types': ['pie_chart']}
        validation = engine.validate_preferences(prefs)
        
        assert validation['valid'] is True
        assert validation['severity'] == 'success'

    def test_validate_invalid_preferences(self, engine):
        prefs = {'max_charts': -5}
        validation = engine.validate_preferences(prefs)
        
        assert validation['valid'] is False
        assert len(validation['issues']) > 0

    def test_get_customization_options(self, engine):
        charts = [
            {'type': 'line_chart'},
            {'type': 'bar_chart'},
            {'type': 'scatter_plot'}
        ]
        options = engine.get_customization_options(charts)
        
        assert 'presets' in options
        assert 'customization_options' in options
        assert 'available_chart_types' in options

    def test_apply_preferences(self, engine):
        items = [
            {'type': 'line_chart', 'id': '1'},
            {'type': 'pie_chart', 'id': '2'},
            {'type': 'bar_chart', 'id': '3'}
        ]
        prefs = {'exclude_types': ['pie_chart'], 'max_charts': 1}
        
        result = engine.apply_preferences(items, prefs)
        
        assert len(result) == 1
        assert result[0]['type'] != 'pie_chart'

    def test_merge_preferences(self, engine):
        overrides = {'max_charts': 3}
        merged = engine.merge_preferences('essential', overrides)
        
        assert merged['max_charts'] == 3
        assert merged['name'] == 'Essential'


class TestReportGenerator:
    """Test ReportGenerator main coordinator."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    @pytest.fixture
    def sample_narrative(self):
        return """
        Your dataset contains 1000 records with 23 anomalies.
        The trend shows consistent growth with seasonal variations.
        Key correlations: Marketing spend vs Sales volume (0.87).
        Recommendation: Increase marketing investment in Q4.
        """

    @pytest.fixture
    def sample_charts(self):
        return [
            {'id': '1', 'type': 'scatter_plot', 'name': 'Anomalies'},
            {'id': '2', 'type': 'line_chart', 'name': 'Trends'},
            {'id': '3', 'type': 'heatmap', 'name': 'Correlation'},
            {'id': '4', 'type': 'bar_chart', 'name': 'Breakdown'}
        ]

    def test_initialization(self, generator):
        assert generator.name == "ReportGenerator"
        assert generator.topic_analyzer is not None
        assert generator.chart_mapper is not None
        assert generator.chart_selector is not None
        assert generator.report_formatter is not None
        assert generator.customization_engine is not None

    def test_analyze_narrative(self, generator, sample_narrative):
        result = generator.analyze_narrative(sample_narrative)
        
        assert 'topics' in result
        assert 'sections' in result
        assert len(result['topics']) > 0

    def test_select_charts(self, generator, sample_narrative, sample_charts):
        selected = generator.select_charts_for_narrative(
            sample_narrative,
            sample_charts
        )
        
        assert isinstance(selected, dict)
        assert len(selected) > 0

    def test_generate_html_report(self, generator, sample_narrative, sample_charts):
        report = generator.generate_html_report(
            sample_narrative,
            sample_charts,
            "Test Report"
        )
        
        assert report['status'] == 'success'
        assert report['format'] == 'html'
        assert '<!DOCTYPE html>' in report['formatted_content']
        assert 'Test Report' in report['formatted_content']

    def test_generate_markdown_report(self, generator, sample_narrative, sample_charts):
        report = generator.generate_markdown_report(
            sample_narrative,
            sample_charts,
            "Test Report"
        )
        
        assert report['status'] == 'success'
        assert report['format'] == 'markdown'
        assert '# Test Report' in report['formatted_content']

    def test_generate_report_with_preferences(self, generator, sample_narrative, sample_charts):
        preferences = {
            'exclude_types': ['pie_chart'],
            'max_charts': 2
        }
        
        report = generator.generate_html_report(
            sample_narrative,
            sample_charts,
            preferences=preferences
        )
        
        assert report['status'] == 'success'
        assert report['summary']['total_charts'] <= 2

    def test_get_customization_options(self, generator, sample_charts):
        options = generator.get_customization_options(sample_charts)
        
        assert 'presets' in options
        assert 'customization_options' in options

    def test_list_presets(self, generator):
        presets = generator.list_presets()
        
        assert len(presets) > 0
        preset_keys = [p['key'] for p in presets]
        assert 'minimal' in preset_keys

    def test_get_status(self, generator):
        status = generator.get_status()
        
        assert status['name'] == 'ReportGenerator'
        assert status['status'] == 'active'
        assert status['workers'] == 5

    def test_get_detailed_status(self, generator):
        status = generator.get_detailed_status()
        
        assert 'workers' in status
        assert 'capabilities' in status
        assert status['capabilities']['customization'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
