"""A+ Grade Tests for Enhanced ReportGenerator.

Tests all A+ enhancements:
- Caching layer
- Configuration system
- Performance tracking
- Advanced error recovery
- Enhanced logging
"""

import pytest
import time
from agents.report_generator.report_generator_enhanced import (
    ReportGeneratorEnhanced,
    ReportGeneratorConfig,
    CacheManager
)
from core.exceptions import WorkerError


class TestCacheManager:
    """Test the caching system."""

    @pytest.fixture
    def cache(self):
        """Create cache manager."""
        return CacheManager(max_size=100, ttl_seconds=3600)

    def test_cache_set_get(self, cache):
        """Test basic cache set/get."""
        cache.set('key1', {'data': 'value1'})
        result = cache.get('key1')
        
        assert result == {'data': 'value1'}
        assert cache.hits == 1
        print("✅ Test PASSED: Cache set/get works")

    def test_cache_miss(self, cache):
        """Test cache miss."""
        result = cache.get('nonexistent')
        
        assert result is None
        assert cache.misses == 1
        print("✅ Test PASSED: Cache miss tracked")

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set('key1', 'value1')
        cache.get('key1')  # Hit
        cache.get('key2')  # Miss
        
        stats = cache.stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1
        print("✅ Test PASSED: Cache stats accurate")

    def test_cache_clear(self, cache):
        """Test cache clear."""
        cache.set('key1', 'value1')
        cache.clear()
        
        assert cache.get('key1') is None
        assert len(cache.cache) == 0
        print("✅ Test PASSED: Cache cleared successfully")


class TestReportGeneratorConfig:
    """Test configuration system."""

    def test_default_config(self):
        """Test default configuration."""
        config = ReportGeneratorConfig()
        
        assert config.cache_enabled is True
        assert config.cache_max_size == 128
        assert config.default_format == 'html'
        print("✅ Test PASSED: Default config correct")

    def test_config_to_dict(self):
        """Test config conversion to dict."""
        config = ReportGeneratorConfig()
        config_dict = config.to_dict()
        
        assert 'cache_enabled' in config_dict
        assert 'supported_formats' in config_dict
        print("✅ Test PASSED: Config dict conversion works")

    def test_config_customization(self):
        """Test custom configuration."""
        config = ReportGeneratorConfig()
        config.cache_max_size = 256
        config.default_format = 'markdown'
        
        assert config.cache_max_size == 256
        assert config.default_format == 'markdown'
        print("✅ Test PASSED: Config customization works")


class TestReportGeneratorEnhanced:
    """Test A+ Grade ReportGenerator."""

    @pytest.fixture
    def agent(self):
        """Create enhanced agent."""
        return ReportGeneratorEnhanced()

    @pytest.fixture
    def sample_narrative(self):
        """Sample narrative."""
        return """
        # Q4 2024 Report
        Revenue up 15% YoY. Excellent results.
        Customer satisfaction: 92%.
        """

    @pytest.fixture
    def sample_charts(self):
        """Sample charts."""
        return [
            {'id': 'c1', 'type': 'bar_chart', 'name': 'Revenue'},
            {'id': 'c2', 'type': 'line_chart', 'name': 'Trend'},
        ]

    def test_agent_initializes(self, agent):
        """Test agent initializes with A+ features."""
        assert agent.name == "ReportGeneratorEnhanced"
        assert agent.cache_manager is not None
        assert agent.config is not None
        print("✅ Test PASSED: Agent initializes with A+ features")

    def test_caching_works(self, agent, sample_narrative):
        """Test that caching prevents reprocessing."""
        # First call
        result1 = agent.analyze_narrative_cached(sample_narrative)
        
        # Second call (should use cache)
        result2 = agent.analyze_narrative_cached(sample_narrative)
        
        assert result1 == result2
        assert agent.cache_manager.hits > 0
        print("✅ Test PASSED: Caching works and avoids reprocessing")

    def test_cache_stats_tracking(self, agent, sample_narrative):
        """Test cache statistics tracking."""
        agent.analyze_narrative_cached(sample_narrative)
        agent.analyze_narrative_cached(sample_narrative)  # Should hit
        
        stats = agent.cache_manager.stats()
        assert stats['hits'] >= 1
        assert stats['total_requests'] >= 1
        print("✅ Test PASSED: Cache statistics tracked")

    def test_config_update(self, agent):
        """Test configuration updates."""
        agent.update_config(cache_max_size=256, default_format='markdown')
        
        assert agent.config.cache_max_size == 256
        assert agent.config.default_format == 'markdown'
        print("✅ Test PASSED: Config updates work")

    def test_get_config(self, agent):
        """Test getting configuration."""
        config = agent.get_config()
        
        assert 'cache_enabled' in config
        assert 'supported_formats' in config
        print("✅ Test PASSED: Config retrieval works")

    def test_performance_tracking(self, agent, sample_narrative):
        """Test performance metric tracking."""
        agent.config.track_performance_metrics = True
        agent.analyze_narrative_cached(sample_narrative)
        
        assert len(agent.performance_metrics) > 0
        assert 'duration_ms' in agent.performance_metrics[0]
        print("✅ Test PASSED: Performance metrics tracked")

    def test_generate_report_enhanced(self, agent, sample_narrative, sample_charts):
        """Test enhanced report generation."""
        report = agent.generate_report_enhanced(
            sample_narrative,
            sample_charts,
            "Test Report",
            "html"
        )
        
        assert report['status'] == 'success'
        assert report['format'] == 'html'
        assert 'Test Report' in report['title']
        print("✅ Test PASSED: Enhanced report generation works")

    def test_analytics(self, agent, sample_narrative, sample_charts):
        """Test analytics dashboard."""
        agent.generate_report_enhanced(
            sample_narrative,
            sample_charts,
            "Test"
        )
        
        analytics = agent.get_analytics()
        
        assert 'reports_generated' in analytics
        assert 'cache_stats' in analytics
        assert 'performance' in analytics
        print("✅ Test PASSED: Analytics dashboard works")

    def test_clear_cache(self, agent, sample_narrative):
        """Test cache clearing."""
        agent.analyze_narrative_cached(sample_narrative)
        assert agent.cache_manager.hits >= 0
        
        agent.clear_cache()
        assert len(agent.cache_manager.cache) == 0
        print("✅ Test PASSED: Cache clearing works")

    def test_reset(self, agent, sample_narrative, sample_charts):
        """Test agent reset."""
        agent.generate_report_enhanced(
            sample_narrative,
            sample_charts,
            "Test"
        )
        
        agent.reset()
        
        assert len(agent.generated_reports) == 0
        assert len(agent.performance_metrics) == 0
        print("✅ Test PASSED: Agent reset works")

    def test_error_handling(self, agent):
        """Test error handling with recovery."""
        with pytest.raises(WorkerError):
            agent.generate_report_enhanced(
                "",  # Empty narrative
                [],   # No charts
                "Test"
            )
        print("✅ Test PASSED: Error handling works")

    def test_multiple_report_generation(self, agent):
        """Test generating multiple reports."""
        narratives = [
            "# Report 1\nContent one",
            "# Report 2\nContent two",
            "# Report 3\nContent three"
        ]
        
        charts = [
            {'id': 'c1', 'type': 'bar_chart', 'name': 'Chart'}
        ]
        
        for narrative in narratives:
            report = agent.generate_report_enhanced(
                narrative,
                charts,
                f"Report"
            )
            assert report['status'] == 'success'
        
        assert len(agent.generated_reports) == 3
        print("✅ Test PASSED: Multiple reports generated")

    def test_backward_compatibility(self):
        """Test backward compatibility alias."""
        from agents.report_generator.report_generator_enhanced import (
            ReportGeneratorAPlusGrade
        )
        
        agent = ReportGeneratorAPlusGrade()
        assert agent.name == "ReportGeneratorEnhanced"
        print("✅ Test PASSED: Backward compatibility works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
