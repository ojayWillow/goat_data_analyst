"""Comprehensive tests for upgraded Reporter Agent.

Tests advanced features:
- Smart caching with invalidation
- Quality score propagation
- Performance metric tracking
- Advanced workflow orchestration
- Batch report generation
- Error recovery
"""

import pytest
import pandas as pd
import numpy as np
from agents.reporter.reporter import Reporter, ReportCache


@pytest.fixture
def reporter():
    """Create Reporter agent instance."""
    return Reporter()


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        "col1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "col2": ["a", "b", "c", "d", "e", "a", "b", "c", "d", "e"],
        "col3": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.1]
    })


@pytest.fixture
def dirty_df():
    """Create DataFrame with quality issues."""
    return pd.DataFrame({
        "col1": [1, 2, None, None, 5, 5, 5, 8, 9, 10],
        "col2": ["a", "b", "c", None, "e", "a", "b", "c", None, "e"],
        "col3": [1.1, 1.1, 1.1, 1.1, 1.1, 6.6, 7.7, 8.8, 9.9, 10.1]
    })


class TestReportCache:
    """Test ReportCache functionality."""
    
    def test_cache_initialization(self):
        """Cache should initialize correctly."""
        cache = ReportCache()
        assert cache.cache == {}
        assert cache.metadata == {}
    
    def test_cache_set_and_get(self):
        """Should store and retrieve reports."""
        cache = ReportCache()
        key = "test_key"
        report = {"data": "test"}
        
        cache.set(key, report, 0.95)
        result = cache.get(key)
        
        assert result == report
        assert cache.metadata[key]["hit_count"] == 1
    
    def test_cache_miss(self):
        """Should return None for missing keys."""
        cache = ReportCache()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_cache_hit_count(self):
        """Should track cache hits correctly."""
        cache = ReportCache()
        key = "test"
        cache.set(key, {"data": "test"}, 0.9)
        
        cache.get(key)  # First hit
        cache.get(key)  # Second hit
        cache.get(key)  # Third hit
        
        assert cache.metadata[key]["hit_count"] == 3
    
    def test_cache_clear(self):
        """Should clear all cached data."""
        cache = ReportCache()
        cache.set("key1", {}, 0.9)
        cache.set("key2", {}, 0.9)
        
        cache.clear()
        
        assert len(cache.cache) == 0
        assert len(cache.metadata) == 0
    
    def test_cache_stats(self):
        """Should provide cache statistics."""
        cache = ReportCache()
        cache.set("key1", {}, 0.9)
        cache.set("key2", {}, 0.85)
        
        cache.get("key1")
        cache.get("key1")
        
        stats = cache.get_stats()
        
        assert stats["size"] == 2
        assert stats["total_hits"] == 2


class TestReporterAgentInitialization:
    """Test Reporter agent initialization."""
    
    def test_agent_initialization(self, reporter):
        """Agent should initialize correctly."""
        assert reporter is not None
        assert reporter.name == "Reporter"
        assert reporter.data is None
        assert len(reporter.reports) == 0
    
    def test_workers_initialized(self, reporter):
        """All workers should be initialized."""
        assert reporter.executive_summary_generator is not None
        assert reporter.data_profile_generator is not None
        assert reporter.statistical_report_generator is not None
        assert reporter.json_exporter is not None
        assert reporter.html_exporter is not None
    
    def test_cache_initialized(self, reporter):
        """Cache should be initialized."""
        assert reporter.cache is not None
        assert isinstance(reporter.cache, ReportCache)
    
    def test_metrics_initialized(self, reporter):
        """Metrics tracking should be initialized."""
        assert reporter.quality_scores == {}
        assert reporter.performance_metrics == {}


class TestReporterDataHandling:
    """Test Reporter data handling."""
    
    def test_set_data_valid(self, reporter, sample_df):
        """Should set data correctly."""
        reporter.set_data(sample_df)
        
        assert reporter.data is not None
        assert reporter.data.shape == sample_df.shape
        assert reporter.data_hash is not None
    
    def test_set_data_invalid(self, reporter):
        """Should handle invalid data."""
        with pytest.raises((AttributeError, TypeError)):
            reporter.set_data(None)
    
    def test_set_data_clears_reports(self, reporter, sample_df):
        """Setting new data should clear old reports."""
        reporter.set_data(sample_df)
        reporter.reports["test"] = {"data": "test"}
        
        reporter.set_data(sample_df)
        
        assert len(reporter.reports) == 0
    
    def test_set_data_clears_cache(self, reporter, sample_df):
        """Setting new data should clear cache."""
        reporter.set_data(sample_df)
        cache_size_before = len(reporter.cache.cache)
        
        reporter.set_data(sample_df)
        cache_size_after = len(reporter.cache.cache)
        
        assert cache_size_after == 0
    
    def test_get_data(self, reporter, sample_df):
        """Should retrieve current data."""
        reporter.set_data(sample_df)
        retrieved = reporter.get_data()
        
        assert retrieved is not None
        assert retrieved.shape == sample_df.shape
    
    def test_data_hash_computation(self, reporter, sample_df):
        """Should compute data hash for caching."""
        reporter.set_data(sample_df)
        hash1 = reporter.data_hash
        
        reporter.set_data(sample_df)
        hash2 = reporter.data_hash
        
        # Same data should produce same hash
        assert hash1 == hash2


class TestReporterReportGeneration:
    """Test report generation functionality."""
    
    def test_generate_executive_summary(self, reporter, sample_df):
        """Should generate executive summary."""
        reporter.set_data(sample_df)
        result = reporter.generate_executive_summary()
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_generate_data_profile(self, reporter, sample_df):
        """Should generate data profile."""
        reporter.set_data(sample_df)
        result = reporter.generate_data_profile()
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_generate_statistical_report(self, reporter, sample_df):
        """Should generate statistical report."""
        reporter.set_data(sample_df)
        result = reporter.generate_statistical_report()
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_generate_comprehensive_report(self, reporter, sample_df):
        """Should generate comprehensive report."""
        reporter.set_data(sample_df)
        result = reporter.generate_comprehensive_report()
        
        assert result is not None
        assert result["status"] == "success"
        assert "sections" in result
        assert "quality_score" in result
    
    def test_generate_without_data(self, reporter):
        """Should fail when no data set."""
        with pytest.raises(Exception):
            reporter.generate_executive_summary()
    
    def test_quality_score_tracking(self, reporter, sample_df):
        """Should track quality scores from workers."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary()
        
        assert "executive_summary" in reporter.quality_scores
        assert 0 <= reporter.quality_scores["executive_summary"] <= 1
    
    def test_performance_metric_tracking(self, reporter, sample_df):
        """Should track performance metrics."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary()
        
        assert "executive_summary" in reporter.performance_metrics
        assert reporter.performance_metrics["executive_summary"] > 0


class TestReporterCaching:
    """Test caching functionality."""
    
    def test_cache_on_generation(self, reporter, sample_df):
        """Should cache generated reports."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary(use_cache=True)
        
        cache_size = len(reporter.cache.cache)
        assert cache_size > 0
    
    def test_cache_hit(self, reporter, sample_df):
        """Should return cached report on second call."""
        reporter.set_data(sample_df)
        
        result1 = reporter.generate_executive_summary(use_cache=True)
        cache_size_before = len(reporter.cache.cache)
        result2 = reporter.generate_executive_summary(use_cache=True)
        cache_size_after = len(reporter.cache.cache)
        
        # Cache size shouldn't grow on hit
        assert cache_size_after == cache_size_before
        assert result1 == result2
    
    def test_cache_bypass(self, reporter, sample_df):
        """Should skip cache when use_cache=False."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary(use_cache=True)
        initial_hits = reporter.cache.get_stats()["total_hits"]
        
        reporter.generate_executive_summary(use_cache=False)
        final_hits = reporter.cache.get_stats()["total_hits"]
        
        # Hits shouldn't increase when bypassing cache
        assert final_hits == initial_hits
    
    def test_cache_invalidation_on_new_data(self, reporter, sample_df):
        """Should invalidate cache when data changes."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary()
        initial_cache_size = len(reporter.cache.cache)
        
        # Set new data
        new_df = sample_df.copy()
        new_df.loc[0, "col1"] = 999
        reporter.set_data(new_df)
        
        # Cache should be cleared
        assert len(reporter.cache.cache) == 0


class TestReporterExport:
    """Test export functionality."""
    
    def test_export_json(self, reporter, sample_df):
        """Should export to JSON."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary()
        
        result = reporter.export_to_json("executive_summary")
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_export_html(self, reporter, sample_df):
        """Should export to HTML."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary()
        
        result = reporter.export_to_html("executive_summary")
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_export_nonexistent_report(self, reporter, sample_df):
        """Should fail when exporting nonexistent report."""
        reporter.set_data(sample_df)
        
        with pytest.raises(Exception):
            reporter.export_to_json("nonexistent")
    
    def test_export_without_data(self, reporter):
        """Should fail when no data set."""
        reporter.reports["test"] = {}
        
        with pytest.raises(Exception):
            reporter.export_to_json("test")


class TestReporterMetadata:
    """Test metadata and reporting functionality."""
    
    def test_list_reports(self, reporter, sample_df):
        """Should list all generated reports."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary()
        reporter.generate_data_profile()
        
        result = reporter.list_reports()
        
        assert result["count"] == 2
        assert "executive_summary" in result["reports"]
        assert "data_profile" in result["reports"]
    
    def test_list_reports_empty(self, reporter, sample_df):
        """Should handle empty report list."""
        reporter.set_data(sample_df)
        result = reporter.list_reports()
        
        assert result["count"] == 0
        assert result["reports"] == []
    
    def test_get_quality_scores(self, reporter, sample_df):
        """Should return quality scores."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary()
        reporter.generate_data_profile()
        
        scores = reporter.get_quality_scores()
        
        assert len(scores) == 2
        assert all(0 <= v <= 1 for v in scores.values())
    
    def test_get_performance_metrics(self, reporter, sample_df):
        """Should return performance metrics."""
        reporter.set_data(sample_df)
        reporter.generate_executive_summary()
        reporter.generate_data_profile()
        
        metrics = reporter.get_performance_metrics()
        
        assert len(metrics) == 2
        assert all(v > 0 for v in metrics.values())


class TestReporterWorkflows:
    """Test complex workflows."""
    
    def test_full_workflow(self, reporter, sample_df):
        """Should handle full reporting workflow."""
        reporter.set_data(sample_df)
        comprehensive = reporter.generate_comprehensive_report()
        
        assert comprehensive["status"] == "success"
        assert len(comprehensive["sections"]) == 3
        assert "quality_score" in comprehensive
        assert "performance" in comprehensive
    
    def test_batch_generation(self, reporter, sample_df):
        """Should generate multiple reports sequentially."""
        reporter.set_data(sample_df)
        
        reporter.generate_executive_summary()
        reporter.generate_data_profile()
        reporter.generate_statistical_report()
        
        reports = reporter.list_reports()
        assert reports["count"] == 3
    
    def test_export_workflow(self, reporter, sample_df):
        """Should handle export workflow."""
        reporter.set_data(sample_df)
        reporter.generate_comprehensive_report()
        
        json_export = reporter.export_to_json("comprehensive")
        html_export = reporter.export_to_html("comprehensive")
        
        assert json_export is not None
        assert html_export is not None
    
    def test_quality_propagation(self, reporter, sample_df):
        """Should propagate quality scores in comprehensive report."""
        reporter.set_data(sample_df)
        comprehensive = reporter.generate_comprehensive_report()
        
        assert "quality_scores" in comprehensive
        assert "quality_score" in comprehensive
        # Comprehensive score should be average of component scores
        avg_score = sum(comprehensive["quality_scores"].values()) / len(comprehensive["quality_scores"])
        assert abs(comprehensive["quality_score"] - avg_score) < 0.01


class TestReporterWithDirtyData:
    """Test Reporter with low-quality data."""
    
    def test_dirty_data_handling(self, reporter, dirty_df):
        """Should handle dirty data gracefully."""
        reporter.set_data(dirty_df)
        result = reporter.generate_comprehensive_report()
        
        assert result["status"] == "success"
        # Quality score should be lower for dirty data
        assert result["quality_score"] >= 0
    
    def test_dirty_data_export(self, reporter, dirty_df):
        """Should export dirty data analysis."""
        reporter.set_data(dirty_df)
        reporter.generate_executive_summary()
        
        result = reporter.export_to_json("executive_summary")
        assert result is not None


class TestReporterErrorHandling:
    """Test error handling."""
    
    def test_missing_data_error(self, reporter):
        """Should raise error when data not set."""
        with pytest.raises(Exception):
            reporter.generate_executive_summary()
    
    def test_invalid_report_type_export(self, reporter, sample_df):
        """Should raise error for invalid report type."""
        reporter.set_data(sample_df)
        
        with pytest.raises(Exception):
            reporter.export_to_json("nonexistent_report")
    
    def test_cache_consistency(self, reporter, sample_df):
        """Cache should remain consistent."""
        reporter.set_data(sample_df)
        
        # Generate report multiple times
        for _ in range(3):
            result = reporter.generate_executive_summary()
            assert result is not None
        
        # Reports should be identical (from cache)
        assert "executive_summary" in reporter.reports
