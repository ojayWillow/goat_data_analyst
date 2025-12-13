"""Complete Report Generator Test Suite - All Tests in One Place.

Simple, straightforward tests for the Report Generator system.
Everything here - no need to jump between files.
"""

import pytest
from agents.report_generator.report_generator import ReportGenerator
from core.exceptions import WorkerError
from core.error_recovery import RecoveryError


class TestReportGeneratorComplete:
    """Complete test suite for Report Generator."""

    @pytest.fixture
    def agent(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    @pytest.fixture
    def sample_narrative(self):
        """Sample narrative text."""
        return """
        # Q4 2024 Sales Report
        
        ## Executive Summary
        Q4 showed exceptional growth with revenue up 15% YoY.
        Customer acquisition improved 20% compared to Q3.
        
        ## Key Findings
        - Revenue increased from $500K to $575K
        - New customers: 150 (up from 125)
        - Churn rate: 2.5% (down from 3%)
        - Regional performance varied significantly
        
        ## Recommendations
        Focus on retention and regional expansion strategies.
        """

    @pytest.fixture
    def sample_charts(self):
        """Sample available charts."""
        return [
            {'id': 'c1', 'type': 'line_chart', 'name': 'Revenue Trend', 'path': '/charts/trend.png'},
            {'id': 'c2', 'type': 'bar_chart', 'name': 'Regional Performance', 'path': '/charts/regions.png'},
            {'id': 'c3', 'type': 'scatter_plot', 'name': 'Customer Analysis', 'path': '/charts/customers.png'},
            {'id': 'c4', 'type': 'box_plot', 'name': 'Anomalies', 'path': '/charts/anomalies.png'},
            {'id': 'c5', 'type': 'heatmap', 'name': 'Correlation', 'path': '/charts/corr.png'},
        ]

    # ========== INITIALIZATION TESTS ==========

    def test_01_agent_initializes(self, agent):
        """Test 1: Agent initializes with all workers."""
        assert agent.name == "ReportGenerator"
        assert agent.topic_analyzer is not None
        assert agent.chart_mapper is not None
        assert agent.chart_selector is not None
        assert agent.report_formatter is not None
        assert agent.customization_engine is not None
        print("✅ Test 1 PASSED: Agent initialized with 5 workers")

    def test_02_workers_connected(self, agent):
        """Test 2: All workers are properly connected."""
        assert agent.topic_analyzer.name == "TopicAnalyzer"
        assert agent.chart_mapper.name == "ChartMapper"
        assert agent.chart_selector.name == "ChartSelector"
        assert agent.report_formatter.name == "ReportFormatter"
        assert agent.customization_engine.name == "CustomizationEngine"
        print("✅ Test 2 PASSED: All workers connected correctly")

    # ========== NARRATIVE ANALYSIS TESTS ==========

    def test_03_analyze_narrative_success(self, agent, sample_narrative):
        """Test 3: Successfully analyze narrative."""
        result = agent.analyze_narrative(sample_narrative)
        
        assert result is not None
        assert 'topics' in result
        assert 'sections' in result
        assert len(result['topics']) > 0
        assert len(result['sections']) > 0
        print(f"✅ Test 3 PASSED: Analyzed narrative - found {len(result['topics'])} topics, {len(result['sections'])} sections")

    def test_04_analyze_empty_narrative_fails(self, agent):
        """Test 4: Empty narrative raises error or recovery error."""
        with pytest.raises((WorkerError, RecoveryError)):
            agent.analyze_narrative("")
        print("✅ Test 4 PASSED: Empty narrative correctly raises error")

    # ========== CHART SELECTION TESTS ==========

    def test_05_select_charts_for_narrative(self, agent, sample_narrative, sample_charts):
        """Test 5: Select charts for narrative sections."""
        result = agent.select_charts_for_narrative(
            sample_narrative,
            sample_charts
        )
        
        assert isinstance(result, dict)
        assert len(result) > 0
        for charts in result.values():
            assert isinstance(charts, list)
        print(f"✅ Test 5 PASSED: Selected charts for {len(result)} sections")

    def test_06_select_charts_empty_narrative_fails(self, agent, sample_charts):
        """Test 6: Empty narrative fails chart selection."""
        with pytest.raises((WorkerError, RecoveryError)):
            agent.select_charts_for_narrative("", sample_charts)
        print("✅ Test 6 PASSED: Chart selection correctly rejects empty narrative")

    def test_07_select_charts_empty_charts_fails(self, agent, sample_narrative):
        """Test 7: No charts fails selection."""
        with pytest.raises((WorkerError, RecoveryError)):
            agent.select_charts_for_narrative(sample_narrative, [])
        print("✅ Test 7 PASSED: Chart selection correctly rejects empty chart list")

    def test_08_select_charts_with_preferences(self, agent, sample_narrative, sample_charts):
        """Test 8: Apply user preferences during chart selection."""
        preferences = {
            'exclude_types': ['box_plot'],
            'max_charts': 2
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
        print("✅ Test 8 PASSED: User preferences correctly applied")

    # ========== REPORT GENERATION TESTS ==========

    def test_09_generate_html_report(self, agent, sample_narrative, sample_charts):
        """Test 9: Generate HTML report."""
        report = agent.generate_html_report(
            sample_narrative,
            sample_charts,
            "Q4 2024 Report"
        )
        
        assert report is not None
        assert report['status'] == 'success'
        assert report['format'] == 'html'
        assert 'Q4 2024 Report' in report['formatted_content']
        assert '<!DOCTYPE html>' in report['formatted_content']
        print("✅ Test 9 PASSED: HTML report generated successfully")

    def test_10_generate_markdown_report(self, agent, sample_narrative, sample_charts):
        """Test 10: Generate Markdown report."""
        report = agent.generate_markdown_report(
            sample_narrative,
            sample_charts,
            "Q4 2024 Report"
        )
        
        assert report is not None
        assert report['status'] == 'success'
        assert report['format'] == 'markdown'
        assert 'Q4 2024 Report' in report['formatted_content']
        assert '#' in report['formatted_content']
        print("✅ Test 10 PASSED: Markdown report generated successfully")

    def test_11_generate_report_with_metadata(self, agent, sample_narrative, sample_charts):
        """Test 11: Generate report with metadata."""
        metadata = {
            'Author': 'Analytics Team',
            'Date': '2024-12-13',
            'Version': '1.0'
        }
        
        report = agent.generate_report(
            sample_narrative,
            sample_charts,
            "Q4 Report",
            output_format='html',
            metadata=metadata
        )
        
        assert 'Analytics Team' in report['formatted_content']
        assert '2024-12-13' in report['formatted_content']
        print("✅ Test 11 PASSED: Report with metadata generated successfully")

    def test_12_generate_report_with_preferences(self, agent, sample_narrative, sample_charts):
        """Test 12: Generate report with user preferences."""
        preferences = {'max_charts': 2, 'exclude_types': ['heatmap']}
        
        report = agent.generate_report(
            sample_narrative,
            sample_charts,
            "Q4 Report",
            output_format='html',
            user_preferences=preferences
        )
        
        assert report['status'] == 'success'
        assert report['summary']['total_charts'] <= 2
        print(f"✅ Test 12 PASSED: Report with preferences - {report['summary']['total_charts']} charts")

    def test_13_generate_report_invalid_format_fails(self, agent, sample_narrative, sample_charts):
        """Test 13: Invalid format raises error."""
        with pytest.raises((WorkerError, RecoveryError)):
            agent.generate_report(
                sample_narrative,
                sample_charts,
                "Report",
                output_format='invalid_format'
            )
        print("✅ Test 13 PASSED: Invalid format correctly rejected")

    def test_14_generate_report_empty_narrative_fails(self, agent, sample_charts):
        """Test 14: Empty narrative fails report generation."""
        with pytest.raises((WorkerError, RecoveryError)):
            agent.generate_report(
                "",
                sample_charts,
                "Report"
            )
        print("✅ Test 14 PASSED: Empty narrative correctly rejected")

    def test_15_generate_report_empty_charts_fails(self, agent, sample_narrative):
        """Test 15: Empty charts list fails report generation."""
        with pytest.raises((WorkerError, RecoveryError)):
            agent.generate_report(
                sample_narrative,
                [],
                "Report"
            )
        print("✅ Test 15 PASSED: Empty charts list correctly rejected")

    # ========== CUSTOMIZATION TESTS ==========

    def test_16_get_customization_options(self, agent):
        """Test 16: Get customization options."""
        options = agent.get_customization_options()
        
        assert 'presets' in options
        assert len(options['presets']) == 5
        print(f"✅ Test 16 PASSED: Got {len(options['presets'])} customization presets")

    def test_17_get_preset(self, agent):
        """Test 17: Get specific preset."""
        preset = agent.get_preset('minimal')
        
        assert preset is not None
        assert preset['name'] == 'Minimal'
        assert preset['max_charts'] == 1
        print("✅ Test 17 PASSED: Retrieved 'minimal' preset successfully")

    def test_18_list_presets(self, agent):
        """Test 18: List all presets."""
        presets = agent.list_presets()
        
        assert isinstance(presets, list)
        assert len(presets) == 5
        preset_names = [p['name'] for p in presets]
        assert 'Minimal' in preset_names
        assert 'Complete' in preset_names
        print(f"✅ Test 18 PASSED: Listed {len(presets)} presets")

    def test_19_validate_valid_preferences(self, agent):
        """Test 19: Validate valid preferences."""
        prefs = {'max_charts': 5, 'exclude_types': ['pie_chart']}
        result = agent.validate_preferences(prefs)
        
        assert result['valid'] is True
        assert len(result['issues']) == 0
        print("✅ Test 19 PASSED: Valid preferences accepted")

    def test_20_validate_invalid_preferences(self, agent):
        """Test 20: Validate invalid preferences."""
        prefs = {'max_charts': -1}  # Invalid: negative
        result = agent.validate_preferences(prefs)
        
        assert result['valid'] is False
        assert len(result['issues']) > 0
        print("✅ Test 20 PASSED: Invalid preferences rejected")

    # ========== STATUS TESTS ==========

    def test_21_get_status(self, agent):
        """Test 21: Get agent status."""
        status = agent.get_status()
        
        assert status['name'] == 'ReportGenerator'
        assert status['status'] == 'active'
        assert status['workers'] == 5
        print("✅ Test 21 PASSED: Agent status retrieved")

    def test_22_get_detailed_status(self, agent):
        """Test 22: Get detailed status."""
        status = agent.get_detailed_status()
        
        assert status['workers'] is not None
        assert 'topic_analyzer' in status['workers']
        assert 'report_formatter' in status['workers']
        assert 'capabilities' in status
        print("✅ Test 22 PASSED: Detailed status retrieved")

    # ========== REPORT TRACKING TESTS ==========

    def test_23_reports_tracked(self, agent, sample_narrative, sample_charts):
        """Test 23: Generated reports are tracked."""
        initial_count = len(agent.generated_reports)
        
        agent.generate_html_report(
            sample_narrative,
            sample_charts,
            "Test Report"
        )
        
        assert len(agent.generated_reports) == initial_count + 1
        print("✅ Test 23 PASSED: Report tracked successfully")

    def test_24_report_contains_summary(self, agent, sample_narrative, sample_charts):
        """Test 24: Report contains summary information."""
        report = agent.generate_html_report(
            sample_narrative,
            sample_charts,
            "Test Report"
        )
        
        assert 'summary' in report
        assert 'sections' in report['summary']
        assert 'total_charts' in report['summary']
        assert 'word_count' in report['summary']
        print(f"✅ Test 24 PASSED: Report summary contains all required fields")

    # ========== COMPLETE WORKFLOW TESTS ==========

    def test_25_complete_workflow_executive_summary(self, agent):
        """Test 25: Complete workflow - Executive Summary."""
        narrative = """
        # Executive Summary Q4 2024
        
        Results exceeded expectations with 20% growth.
        All regions performed well with strong margins.
        Customer satisfaction reached 92%.
        """
        
        charts = [
            {'id': 'c1', 'type': 'bar_chart', 'name': 'Revenue'},
            {'id': 'c2', 'type': 'line_chart', 'name': 'Trend'},
            {'id': 'c3', 'type': 'pie_chart', 'name': 'Distribution'},
        ]
        
        # Generate report
        report = agent.generate_html_report(
            narrative,
            charts,
            "Executive Summary"
        )
        
        # Verify
        assert report['status'] == 'success'
        assert 'Executive Summary' in report['formatted_content']
        assert report['summary']['total_charts'] > 0
        print("✅ Test 25 PASSED: Complete executive summary workflow successful")

    def test_26_complete_workflow_detailed_analysis(self, agent):
        """Test 26: Complete workflow - Detailed Analysis with Preferences."""
        narrative = """
        # Detailed Analysis
        
        Customer segments show different behaviors.
        Regional anomalies identified for investigation.
        Predictive models suggest continued growth.
        """
        
        charts = [
            {'id': 'c1', 'type': 'scatter_plot', 'name': 'Segments'},
            {'id': 'c2', 'type': 'heatmap', 'name': 'Anomalies'},
            {'id': 'c3', 'type': 'box_plot', 'name': 'Distribution'},
            {'id': 'c4', 'type': 'line_chart', 'name': 'Forecast'},
            {'id': 'c5', 'type': 'bar_chart', 'name': 'Metrics'},
        ]
        
        preferences = {'max_charts': 3, 'exclude_types': ['pie_chart']}
        
        # Generate report
        report = agent.generate_markdown_report(
            narrative,
            charts,
            "Detailed Analysis",
            preferences
        )
        
        # Verify
        assert report['status'] == 'success'
        assert report['format'] == 'markdown'
        assert report['summary']['total_charts'] <= 3
        print("✅ Test 26 PASSED: Complete detailed analysis workflow successful")

    def test_27_all_formats_work(self, agent, sample_narrative, sample_charts):
        """Test 27: All output formats work correctly."""
        # HTML
        html_report = agent.generate_html_report(
            sample_narrative,
            sample_charts,
            "Test"
        )
        assert html_report['format'] == 'html'
        assert '<!DOCTYPE html>' in html_report['formatted_content']
        
        # Markdown
        md_report = agent.generate_markdown_report(
            sample_narrative,
            sample_charts,
            "Test"
        )
        assert md_report['format'] == 'markdown'
        assert '#' in md_report['formatted_content']
        
        print("✅ Test 27 PASSED: All formats (HTML, Markdown) work correctly")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_report_generator_complete.py -v
    # Or simply: python tests/test_report_generator_complete.py
    pytest.main([__file__, "-v", "--tb=short"])
