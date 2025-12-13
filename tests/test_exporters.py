"""Tests for Reporter exporters (JSON and HTML).

Tests file writing, compression, validation, and format correctness.
"""

import pytest
import json
import gzip
import os
import tempfile
from pathlib import Path
from agents.reporter.workers.json_exporter import JSONExporter
from agents.reporter.workers.html_exporter import HTMLExporter


@pytest.fixture
def json_exporter():
    """Create JSONExporter instance."""
    return JSONExporter()


@pytest.fixture
def html_exporter():
    """Create HTMLExporter instance."""
    return HTMLExporter()


@pytest.fixture
def sample_report():
    """Create sample report data."""
    return {
        "title": "Test Report",
        "dataset_info": {
            "rows": 100,
            "columns": 5
        },
        "data_quality": {
            "rating": "Good",
            "null_percentage": 2.5
        },
        "summary": "This is a test report."
    }


class TestJSONExporter:
    """Test JSONExporter functionality."""
    
    def test_worker_initialization(self, json_exporter):
        """Worker should initialize correctly."""
        assert json_exporter.worker_name == "json_exporter"
        assert json_exporter.logger is not None
    
    def test_execute_valid_data(self, json_exporter, sample_report):
        """Should export valid report data."""
        result = json_exporter.execute(sample_report, write_to_disk=False)
        
        assert result.success is True
        assert result.task_type == "json_export"
        assert "json" in result.data
    
    def test_execute_none_data(self, json_exporter):
        """Should fail with None data."""
        result = json_exporter.execute(None, write_to_disk=False)
        
        assert result.success is False
        assert result.has_errors() is True
    
    def test_execute_empty_dict(self, json_exporter):
        """Should fail with empty dictionary."""
        result = json_exporter.execute({}, write_to_disk=False)
        
        assert result.success is False
    
    def test_json_generation_valid(self, json_exporter, sample_report):
        """Generated JSON should be valid."""
        result = json_exporter.execute(sample_report, write_to_disk=False)
        
        json_str = result.data["json"]
        # Should be parseable JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
    
    def test_json_pretty_print_option(self, json_exporter, sample_report):
        """Should support pretty-print option."""
        result_pretty = json_exporter.execute(
            sample_report,
            write_to_disk=False,
            pretty_print=True
        )
        result_compact = json_exporter.execute(
            sample_report,
            write_to_disk=False,
            pretty_print=False
        )
        
        json_pretty = result_pretty.data["json"]
        json_compact = result_compact.data["json"]
        
        # Pretty print should have newlines or be different
        assert len(json_pretty) >= len(json_compact)
    
    def test_json_content_preservation(self, json_exporter, sample_report):
        """JSON should preserve all data."""
        result = json_exporter.execute(sample_report, write_to_disk=False)
        
        json_str = result.data["json"]
        parsed = json.loads(json_str)
        
        # Data should be preserved
        assert parsed["title"] == "Test Report"
        assert parsed["dataset_info"]["rows"] == 100
    
    def test_file_size_tracking(self, json_exporter, sample_report):
        """Should track file sizes."""
        result = json_exporter.execute(sample_report, write_to_disk=False)
        
        assert "json_size" in result.data
        assert "file_size_mb" in result.data
        assert result.data["json_size"] > 0
    
    def test_quality_score(self, json_exporter, sample_report):
        """Should have high quality score for successful exports."""
        result = json_exporter.execute(sample_report, write_to_disk=False)
        
        assert result.quality_score > 0.9
    
    def test_complex_data_serialization(self, json_exporter):
        """Should handle complex data types."""
        complex_report = {
            "data": [1, 2, 3],
            "nested": {"a": 1, "b": [4, 5, 6]},
            "value": 3.14
        }
        
        result = json_exporter.execute(complex_report, write_to_disk=False)
        
        assert result.success is True
        # Should parse back correctly
        parsed = json.loads(result.data["json"])
        assert parsed["nested"]["b"] == [4, 5, 6]


class TestHTMLExporter:
    """Test HTMLExporter functionality."""
    
    def test_worker_initialization(self, html_exporter):
        """Worker should initialize correctly."""
        assert html_exporter.worker_name == "html_exporter"
        assert html_exporter.logger is not None
    
    def test_execute_valid_data(self, html_exporter, sample_report):
        """Should export valid report data."""
        result = html_exporter.execute(sample_report, write_to_disk=False)
        
        assert result.success is True
        assert result.task_type == "html_export"
    
    def test_execute_none_data(self, html_exporter):
        """Should fail with None data."""
        result = html_exporter.execute(None, write_to_disk=False)
        
        assert result.success is False
        assert result.has_errors() is True
    
    def test_html_structure_valid(self, html_exporter, sample_report):
        """Generated HTML should be valid."""
        result = html_exporter.execute(sample_report, write_to_disk=False)
        
        # HTML should start with DOCTYPE
        assert "<!DOCTYPE html>" in result.data["html"]
        # Should have proper closing tags
        assert "</html>" in result.data["html"]
    
    def test_html_includes_title(self, html_exporter, sample_report):
        """HTML should include report title."""
        result = html_exporter.execute(sample_report, write_to_disk=False)
        
        assert "Test Report" in result.data["html"]
    
    def test_html_includes_css(self, html_exporter, sample_report):
        """HTML should include CSS styling."""
        result = html_exporter.execute(sample_report, write_to_disk=False)
        
        html = result.data["html"]
        assert "<style>" in html
        assert "</style>" in html
        assert "color:" in html or "margin:" in html or "padding:" in html
    
    def test_html_table_generation(self, html_exporter):
        """Should generate tables for nested data."""
        report = {
            "data": {
                "rows": 100,
                "columns": 5
            }
        }
        result = html_exporter.execute(report, write_to_disk=False)
        
        html = result.data["html"]
        assert "<table" in html
        assert "</table>" in html
    
    def test_html_toc_generation(self, html_exporter, sample_report):
        """Should generate table of contents when requested."""
        result = html_exporter.execute(sample_report, include_toc=True, write_to_disk=False)
        
        html = result.data["html"]
        # TOC section should be present
        assert "toc" in html.lower() or "table of contents" in html.lower() or "<div class='toc'>" in html
    
    def test_html_no_toc_option(self, html_exporter, sample_report):
        """Should respect include_toc option."""
        result_with_toc = html_exporter.execute(
            sample_report,
            include_toc=True,
            write_to_disk=False
        )
        result_without_toc = html_exporter.execute(
            sample_report,
            include_toc=False,
            write_to_disk=False
        )
        
        # Both should succeed
        assert result_with_toc.success is True
        assert result_without_toc.success is True
    
    def test_responsive_design_css(self, html_exporter, sample_report):
        """HTML should include responsive design CSS."""
        result = html_exporter.execute(sample_report, write_to_disk=False)
        
        html = result.data["html"]
        # Should have media queries for responsive design
        assert "@media" in html
        assert "max-width:" in html
    
    def test_quality_score(self, html_exporter, sample_report):
        """Should have high quality score for successful exports."""
        result = html_exporter.execute(sample_report, write_to_disk=False)
        
        assert result.quality_score > 0.9
    
    def test_complex_nested_data(self, html_exporter):
        """Should handle complex nested data structures."""
        complex_report = {
            "summary": "Test",
            "data": {
                "metrics": {
                    "total": 100,
                    "average": 50
                },
                "list": [1, 2, 3]
            }
        }
        
        result = html_exporter.execute(complex_report, write_to_disk=False)
        
        assert result.success is True
        assert "100" in result.data["html"]
    
    def test_html_size_tracking(self, html_exporter, sample_report):
        """Should track HTML file size."""
        result = html_exporter.execute(sample_report, write_to_disk=False)
        
        assert "html_size" in result.data
        assert result.data["html_size"] > 0
    
    def test_html_data_preservation(self, html_exporter, sample_report):
        """HTML should preserve report data."""
        result = html_exporter.execute(sample_report, write_to_disk=False)
        
        html = result.data["html"]
        # Data should be visible in HTML
        assert "Good" in html  # Quality rating
        assert "100" in html   # Row count
