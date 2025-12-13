"""Unit tests for Orchestrator."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from agents.orchestrator.orchestrator import (
    Orchestrator,
    QualityScore,
    TaskStatus,
    WorkflowStatus
)


class TestOrchestratorInit:
    """Test Orchestrator initialization."""
    
    def test_init_success(self):
        """Test successful initialization."""
        orch = Orchestrator()
        
        assert orch.name == "Orchestrator"
        assert orch.version == "3.0-enhanced"
        assert orch.agent_registry is not None
        assert orch.data_manager is not None
        assert orch.error_intelligence is not None
        assert orch.quality_tracker is not None


class TestQualityScore:
    """Test QualityScore class."""
    
    def test_init(self):
        """Test initialization."""
        qs = QualityScore()
        assert qs.tasks_successful == 0
        assert qs.tasks_failed == 0
        assert qs.get_score() == 1.0
    
    def test_quality_all_successful(self):
        """Test quality when all successful."""
        qs = QualityScore()
        qs.add_success()
        qs.add_success()
        assert qs.get_score() == 1.0
    
    def test_quality_all_failed(self):
        """Test quality when all failed."""
        qs = QualityScore()
        qs.add_failure()
        qs.add_failure()
        assert qs.get_score() == 0.0
    
    def test_quality_mixed(self):
        """Test quality with mixed results."""
        qs = QualityScore()
        qs.add_success()
        qs.add_partial()
        expected = (1.0 + 0.5) / 2
        assert qs.get_score() == round(expected, 3)


class TestAgentManagement:
    """Test agent management."""
    
    def test_register_agent(self):
        """Test agent registration."""
        orch = Orchestrator()
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        result = orch.register_agent('test', mock_agent)
        
        assert result['success'] is True
        assert result['agent_name'] == 'test'
        assert 'registered_at' in result
    
    def test_get_agent(self):
        """Test getting agent."""
        orch = Orchestrator()
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        orch.register_agent('test', mock_agent)
        
        retrieved = orch.get_agent('test')
        assert retrieved == mock_agent
    
    def test_list_agents(self):
        """Test listing agents."""
        orch = Orchestrator()
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        orch.register_agent('test', mock_agent)
        
        result = orch.list_agents()
        assert 'agents' in result
        assert 'total' in result


class TestDataManagement:
    """Test data management."""
    
    def test_cache_data(self):
        """Test caching data."""
        orch = Orchestrator()
        result = orch.cache_data('key', {'data': 'value'})
        
        assert result['success'] is True
        assert result['key'] == 'key'
    
    def test_get_cached_data(self):
        """Test retrieving cached data."""
        orch = Orchestrator()
        orch.cache_data('key', {'data': 'value'})
        
        retrieved = orch.get_cached_data('key')
        assert retrieved == {'data': 'value'}
    
    def test_clear_cache(self):
        """Test clearing cache."""
        orch = Orchestrator()
        orch.cache_data('key', {'data': 'value'})
        
        result = orch.clear_cache()
        assert result['success'] is True


class TestHealthReporting:
    """Test health reporting."""
    
    def test_get_status(self):
        """Test quick status."""
        orch = Orchestrator()
        status = orch.get_status()
        
        assert status['name'] == 'Orchestrator'
        assert status['version'] == '3.0-enhanced'
        assert 'health_score' in status
    
    def test_get_health_report(self):
        """Test health report."""
        orch = Orchestrator()
        report = orch.get_health_report()
        
        assert 'overall_health' in report
        assert 'status' in report
        assert report['overall_health'] == 100.0


class TestLifecycle:
    """Test lifecycle methods."""
    
    def test_reset(self):
        """Test reset."""
        orch = Orchestrator()
        orch.cache_data('key', 'value')
        
        result = orch.reset()
        assert result['success'] is True
    
    def test_shutdown(self):
        """Test shutdown."""
        orch = Orchestrator()
        result = orch.shutdown()
        
        assert result['success'] is True
        assert 'shutdown_at' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
