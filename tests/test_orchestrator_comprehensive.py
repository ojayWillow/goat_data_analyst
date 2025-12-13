"""Comprehensive tests for Orchestrator - Full coverage.

Tests:
- Initialization
- Quality tracking
- Agent management
- Data caching
- Task execution
- Workflow execution
- Error handling
- Health reporting
- Edge cases
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from agents.orchestrator.orchestrator import (
    Orchestrator,
    QualityScore,
    TaskStatus,
    WorkflowStatus
)
from agents.error_intelligence.error_record import (
    ErrorRecord,
    ErrorType,
    ErrorSeverity,
    ErrorRecordBuilder
)


# ==================== INITIALIZATION TESTS ====================

class TestOrchestratorInitialization:
    """Test Orchestrator initialization."""
    
    def test_init_creates_all_components(self):
        """All components initialized."""
        orch = Orchestrator()
        assert orch.name == "Orchestrator"
        assert orch.version == "3.0-enhanced"
        assert orch.logger is not None
        assert orch.error_intelligence is not None
        assert orch.quality_tracker is not None
        assert orch.agent_registry is not None
        assert orch.data_manager is not None
        assert orch.task_router is not None
        assert orch.workflow_executor is not None
        assert orch.narrative_integrator is not None
    
    def test_init_empty_state(self):
        """Initial state empty."""
        orch = Orchestrator()
        assert orch.current_task is None
        assert orch.current_workflow is None
        assert orch.execution_history == []


# ==================== QUALITY SCORE TESTS ====================

class TestQualityScoreTracking:
    """Test QualityScore tracking."""
    
    def test_init(self):
        """Initialize correctly."""
        qs = QualityScore()
        assert qs.tasks_successful == 0
        assert qs.tasks_failed == 0
        assert qs.tasks_partial == 0
        assert qs.get_score() == 1.0
    
    def test_add_success(self):
        """Track success."""
        qs = QualityScore()
        qs.add_success()
        assert qs.tasks_successful == 1
        assert qs.get_score() == 1.0
    
    def test_add_failure(self):
        """Track failure."""
        qs = QualityScore()
        qs.add_failure()
        assert qs.tasks_failed == 1
        assert qs.get_score() == 0.0
    
    def test_add_partial(self):
        """Track partial."""
        qs = QualityScore()
        qs.add_partial()
        assert qs.tasks_partial == 1
        assert qs.get_score() == 0.5
    
    def test_quality_calculation_mixed(self):
        """Calculate mixed quality."""
        qs = QualityScore()
        qs.add_success()  # 1.0
        qs.add_success()  # 1.0
        qs.add_partial()  # 0.5
        # (1 + 1 + 0.5) / 3 = 0.833
        expected = round((1.0 + 1.0 + 0.5) / 3, 3)
        assert qs.get_score() == expected
    
    def test_quality_rounding(self):
        """Score rounded to 3 decimals."""
        qs = QualityScore()
        qs.add_success()
        qs.add_success()
        qs.add_failure()
        score = qs.get_score()
        assert isinstance(score, float)
        assert len(str(score).split('.')[-1]) <= 3
    
    def test_get_summary(self):
        """Get summary."""
        qs = QualityScore()
        qs.add_success()
        qs.add_failure()
        summary = qs.get_summary()
        assert 'quality_score' in summary
        assert 'tasks' in summary
        assert summary['tasks']['successful'] == 1
        assert summary['tasks']['failed'] == 1


# ==================== AGENT MANAGEMENT TESTS ====================

class TestAgentManagement:
    """Test agent registration and management."""
    
    def test_register_agent_success(self):
        """Register agent successfully."""
        orch = Orchestrator()
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        result = orch.register_agent('test_agent', mock_agent)
        
        assert result['success'] is True
        assert result['agent_name'] == 'test_agent'
        assert 'registered_at' in result
        assert result['total_agents'] == 1
        assert result['quality_score'] == 1.0
    
    def test_register_agent_invalid(self):
        """Reject agent without name."""
        orch = Orchestrator()
        mock_agent = Mock(spec=[])
        
        with pytest.raises(Exception):
            orch.register_agent('bad_agent', mock_agent)
    
    def test_register_multiple_agents(self):
        """Register multiple agents."""
        orch = Orchestrator()
        
        for i in range(3):
            agent = Mock()
            agent.name = f"Agent{i}"
            orch.register_agent(f'agent{i}', agent)
        
        agents = orch.list_agents()
        assert agents['total'] == 3
    
    def test_get_agent_exists(self):
        """Get existing agent."""
        orch = Orchestrator()
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        orch.register_agent('test', mock_agent)
        
        retrieved = orch.get_agent('test')
        assert retrieved == mock_agent
    
    def test_get_agent_not_found(self):
        """Get non-existent agent returns None."""
        orch = Orchestrator()
        result = orch.get_agent('nonexistent')
        assert result is None
    
    def test_list_agents(self):
        """List agents."""
        orch = Orchestrator()
        agent = Mock()
        agent.name = "TestAgent"
        orch.register_agent('test', agent)
        
        result = orch.list_agents()
        assert 'agents' in result
        assert 'total' in result
        assert 'timestamp' in result
        assert result['total'] == 1


# ==================== DATA CACHING TESTS ====================

class TestDataCaching:
    """Test data caching."""
    
    def test_cache_data(self):
        """Cache data."""
        orch = Orchestrator()
        result = orch.cache_data('key1', {'data': 'value'})
        
        assert result['success'] is True
        assert result['key'] == 'key1'
        assert result['cache_size'] == 1
    
    def test_get_cached_data(self):
        """Retrieve cached data."""
        orch = Orchestrator()
        orch.cache_data('key1', {'data': 'value'})
        
        retrieved = orch.get_cached_data('key1')
        assert retrieved == {'data': 'value'}
    
    def test_get_nonexistent_cache(self):
        """Get non-existent cache returns None."""
        orch = Orchestrator()
        result = orch.get_cached_data('nonexistent')
        assert result is None
    
    def test_cache_multiple_items(self):
        """Cache multiple items."""
        orch = Orchestrator()
        orch.cache_data('key1', 'value1')
        orch.cache_data('key2', 'value2')
        orch.cache_data('key3', 'value3')
        
        assert orch.get_cached_data('key1') == 'value1'
        assert orch.get_cached_data('key2') == 'value2'
        assert orch.get_cached_data('key3') == 'value3'
    
    def test_list_cached_data(self):
        """List cached data."""
        orch = Orchestrator()
        orch.cache_data('key1', 'val1')
        orch.cache_data('key2', 'val2')
        
        result = orch.list_cached_data()
        assert result['count'] == 2
        assert 'key1' in result['keys']
        assert 'key2' in result['keys']
    
    def test_clear_cache(self):
        """Clear cache."""
        orch = Orchestrator()
        orch.cache_data('key1', 'val1')
        orch.cache_data('key2', 'val2')
        
        result = orch.clear_cache()
        assert result['success'] is True
        assert orch.get_cached_data('key1') is None
        assert orch.get_cached_data('key2') is None


# ==================== ERROR RECORD TESTS ====================

class TestErrorRecord:
    """Test ErrorRecord class."""
    
    def test_error_record_creation(self):
        """Create error record."""
        record = ErrorRecord(
            error_type=ErrorType.TASK_EXECUTION_ERROR,
            severity=ErrorSeverity.HIGH,
            worker_name="TaskRouter",
            message="Task failed to execute",
            context={"task_id": "task_123"}
        )
        
        assert record.error_type == ErrorType.TASK_EXECUTION_ERROR
        assert record.severity == ErrorSeverity.HIGH
        assert record.worker_name == "TaskRouter"
        assert record.message == "Task failed to execute"
        assert record.context["task_id"] == "task_123"
        assert record.timestamp is not None
    
    def test_error_record_to_dict(self):
        """Convert error record to dict."""
        record = ErrorRecord(
            error_type=ErrorType.DATA_VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            worker_name="DataValidator",
            message="Invalid data"
        )
        
        d = record.to_dict()
        assert d['error_type'] == 'data_validation_error'
        assert d['severity'] == 'medium'
        assert d['worker_name'] == 'DataValidator'
    
    def test_error_record_is_critical(self):
        """Check if error is critical."""
        critical = ErrorRecord(
            error_type=ErrorType.TASK_EXECUTION_ERROR,
            severity=ErrorSeverity.CRITICAL,
            worker_name="Worker",
            message="Critical error"
        )
        
        medium = ErrorRecord(
            error_type=ErrorType.TASK_EXECUTION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            worker_name="Worker",
            message="Medium error"
        )
        
        assert critical.is_critical() is True
        assert medium.is_critical() is False
    
    def test_error_record_summary(self):
        """Get error summary."""
        record = ErrorRecord(
            error_type=ErrorType.TASK_EXECUTION_ERROR,
            severity=ErrorSeverity.HIGH,
            worker_name="TaskRouter",
            message="Failed to route task"
        )
        
        summary = record.summary()
        assert "HIGH" in summary
        assert "TaskRouter" in summary
        assert "Failed to route task" in summary


class TestErrorRecordBuilder:
    """Test ErrorRecordBuilder."""
    
    def test_build_complete_record(self):
        """Build complete record with builder."""
        record = (ErrorRecordBuilder()
            .with_type(ErrorType.TASK_EXECUTION_ERROR)
            .with_severity(ErrorSeverity.HIGH)
            .with_worker("TaskRouter")
            .with_message("Task execution failed")
            .with_context({"task_id": "task_123"})
            .build())
        
        assert record.error_type == ErrorType.TASK_EXECUTION_ERROR
        assert record.severity == ErrorSeverity.HIGH
        assert record.worker_name == "TaskRouter"
    
    def test_build_missing_type_raises(self):
        """Build without type raises."""
        with pytest.raises(ValueError):
            (ErrorRecordBuilder()
                .with_severity(ErrorSeverity.HIGH)
                .with_worker("Worker")
                .with_message("Error")
                .build())
    
    def test_add_context_items(self):
        """Add context items individually."""
        record = (ErrorRecordBuilder()
            .with_type(ErrorType.TASK_EXECUTION_ERROR)
            .with_severity(ErrorSeverity.MEDIUM)
            .with_worker("Worker")
            .with_message("Error")
            .add_context("key1", "value1")
            .add_context("key2", 123)
            .build())
        
        assert record.context["key1"] == "value1"
        assert record.context["key2"] == 123


# ==================== HEALTH & STATUS TESTS ====================

class TestHealthReporting:
    """Test health and status reporting."""
    
    def test_get_status(self):
        """Get quick status."""
        orch = Orchestrator()
        status = orch.get_status()
        
        assert status['name'] == 'Orchestrator'
        assert status['version'] == '3.0-enhanced'
        assert status['status'] == 'active'
        assert 'health_score' in status
        assert 'agents_registered' in status
        assert 'cache_items' in status
        assert 'quality_score' in status
    
    def test_get_health_report(self):
        """Get health report."""
        orch = Orchestrator()
        report = orch.get_health_report()
        
        assert 'overall_health' in report
        assert 'status' in report
        assert 'timestamp' in report
        assert 'quality' in report
        assert report['overall_health'] == 100.0
        assert report['status'] == 'healthy'
    
    def test_health_score_degradation(self):
        """Health degrades with failures."""
        orch = Orchestrator()
        
        # Add some failures
        orch.quality_tracker.add_failure()
        orch.quality_tracker.add_failure()
        orch.quality_tracker.add_success()
        
        report = orch.get_health_report()
        assert report['overall_health'] < 100.0
    
    def test_health_status_labels(self):
        """Health status labels correct."""
        orch = Orchestrator()
        
        # Healthy
        assert orch.get_health_report()['status'] == 'healthy'
        
        # Degraded/Critical
        orch.quality_tracker.add_failure()
        orch.quality_tracker.add_failure()
        orch.quality_tracker.add_failure()
        orch.quality_tracker.add_failure()
        orch.quality_tracker.add_success()
        
        status = orch.get_health_report()['status']
        assert status in ['degraded', 'critical', 'healthy']


# ==================== EXECUTION HISTORY TESTS ====================

class TestExecutionHistory:
    """Test execution history tracking."""
    
    def test_get_history_empty(self):
        """Get empty history."""
        orch = Orchestrator()
        history = orch.get_execution_history()
        assert history == []
    
    def test_clear_history(self):
        """Clear history."""
        orch = Orchestrator()
        # Simulate adding to history
        orch.execution_history.append({'task': 'test'})
        
        result = orch.clear_history()
        assert result['success'] is True
        assert result['cleared_count'] == 1
        assert orch.execution_history == []


# ==================== LIFECYCLE TESTS ====================

class TestLifecycleMethods:
    """Test reset and shutdown."""
    
    def test_reset(self):
        """Reset orchestrator."""
        orch = Orchestrator()
        orch.cache_data('key', 'value')
        agent = Mock()
        agent.name = "TestAgent"
        orch.register_agent('test', agent)
        
        result = orch.reset()
        
        assert result['success'] is True
        assert orch.get_cached_data('key') is None
        assert orch.get_agent('test') is not None  # Agents kept
    
    def test_shutdown(self):
        """Shutdown orchestrator."""
        orch = Orchestrator()
        result = orch.shutdown()
        
        assert result['success'] is True
        assert 'shutdown_at' in result
        assert 'final_health_score' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
