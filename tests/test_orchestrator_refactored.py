"""Tests for Refactored Orchestrator - Testing all workers and integration.

Test Coverage:
1. AgentRegistry - Agent registration and retrieval
2. DataManager - Data caching and flow
3. TaskRouter - Task routing to agents
4. WorkflowExecutor - Workflow execution
5. Orchestrator - Integration of all components
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
from agents.orchestrator import (
    Orchestrator,
    AgentRegistry,
    DataManager,
    TaskRouter,
    WorkflowExecutor
)
from core.exceptions import OrchestratorError, AgentError, DataLoadError
from core.error_recovery import RecoveryError


class TestAgentRegistry:
    """Test AgentRegistry worker."""

    @pytest.fixture
    def registry(self):
        """Create AgentRegistry instance."""
        return AgentRegistry()

    def test_register_agent(self, registry):
        """Test agent registration."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        registry.register("test_agent", mock_agent)
        
        assert registry.is_registered("test_agent")
        assert registry.get("test_agent") == mock_agent

    def test_register_duplicate_agent_fails(self, registry):
        """Test registering duplicate agent fails."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        registry.register("test_agent", mock_agent)
        
        with pytest.raises(RecoveryError):
            registry.register("test_agent", mock_agent)

    def test_get_nonexistent_agent_returns_none(self, registry):
        """Test getting nonexistent agent returns None."""
        assert registry.get("nonexistent") is None

    def test_get_or_fail_raises_error(self, registry):
        """Test get_or_fail raises error for nonexistent agent."""
        with pytest.raises(AgentError):
            registry.get_or_fail("nonexistent")

    def test_list_agents(self, registry):
        """Test listing agents."""
        mock_agent1 = Mock(name="Agent1")
        mock_agent1.name = "Agent1"
        mock_agent2 = Mock(name="Agent2")
        mock_agent2.name = "Agent2"
        
        registry.register("agent1", mock_agent1)
        registry.register("agent2", mock_agent2)
        
        assert len(registry.list_all()) == 2
        assert "agent1" in registry.list_all()
        assert "agent2" in registry.list_all()

    def test_get_count(self, registry):
        """Test agent count."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        assert registry.get_count() == 0
        
        registry.register("test", mock_agent)
        assert registry.get_count() == 1

    def test_get_summary(self, registry):
        """Test registry summary."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        registry.register("test", mock_agent)
        summary = registry.get_summary()
        
        assert summary['total_agents'] == 1
        assert 'test' in summary['agent_names']


class TestDataManager:
    """Test DataManager worker."""

    @pytest.fixture
    def manager(self):
        """Create DataManager instance."""
        return DataManager()

    def test_set_data(self, manager):
        """Test setting (caching) data."""
        data = {'key': 'value'}
        manager.set('test_key', data)
        
        assert manager.get('test_key') == data

    def test_get_nonexistent_returns_none(self, manager):
        """Test getting nonexistent data returns None."""
        assert manager.get('nonexistent') is None

    def test_get_or_default(self, manager):
        """Test get_or_default with fallback."""
        assert manager.get_or_default('nonexistent', 'default') == 'default'
        
        manager.set('test', 'value')
        assert manager.get_or_default('test', 'default') == 'value'

    def test_get_dataframe(self, manager):
        """Test retrieving cached DataFrame."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        manager.set('df', df)
        
        result = manager.get_dataframe('df')
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_get_dataframe_wrong_type_raises_error(self, manager):
        """Test get_dataframe raises error for non-DataFrame."""
        manager.set('not_df', {'key': 'value'})
        
        with pytest.raises(DataLoadError):
            manager.get_dataframe('not_df')

    def test_exists(self, manager):
        """Test checking if data exists."""
        assert not manager.exists('test')
        
        manager.set('test', 'value')
        assert manager.exists('test')

    def test_delete(self, manager):
        """Test deleting cached data."""
        manager.set('test', 'value')
        assert manager.exists('test')
        
        assert manager.delete('test') is True
        assert not manager.exists('test')
        
        # Deleting nonexistent returns False
        assert manager.delete('nonexistent') is False

    def test_clear(self, manager):
        """Test clearing all cache."""
        manager.set('test1', 'value1')
        manager.set('test2', 'value2')
        
        assert manager.get_count() == 2
        
        manager.clear()
        assert manager.get_count() == 0

    def test_list_keys(self, manager):
        """Test listing cache keys."""
        manager.set('key1', 'value1')
        manager.set('key2', 'value2')
        
        keys = manager.list_keys()
        assert 'key1' in keys
        assert 'key2' in keys
        assert len(keys) == 2

    def test_get_summary(self, manager):
        """Test data manager summary."""
        manager.set('key1', 'string_value')
        manager.set('key2', {'dict': 'value'})
        
        summary = manager.get_summary()
        
        assert summary['total_items'] == 2
        assert 'key1' in summary['keys']
        assert 'key2' in summary['keys']


class TestTaskRouter:
    """Test TaskRouter worker."""

    @pytest.fixture
    def setup(self):
        """Setup TaskRouter with mocked dependencies."""
        registry = AgentRegistry()
        data_mgr = DataManager()
        router = TaskRouter(registry, data_mgr)
        
        return {'registry': registry, 'data_mgr': data_mgr, 'router': router}

    def test_route_unknown_task_fails(self, setup):
        """Test routing unknown task type fails."""
        task = {'type': 'unknown_task', 'parameters': {}}
        
        with pytest.raises(RecoveryError):
            setup['router'].route(task)

    def test_route_missing_agent_fails(self, setup):
        """Test routing to missing agent fails."""
        task = {'type': 'load_data', 'parameters': {'file_path': 'test.csv'}}
        
        with pytest.raises(RecoveryError):
            setup['router'].route(task)

    def test_route_load_data_missing_file_path_fails(self, setup):
        """Test load_data without file_path fails."""
        mock_loader = Mock()
        setup['registry'].register('data_loader', mock_loader)
        
        task = {'type': 'load_data', 'parameters': {}}
        
        with pytest.raises(RecoveryError):
            setup['router'].route(task)


class TestWorkflowExecutor:
    """Test WorkflowExecutor worker."""

    @pytest.fixture
    def executor(self):
        """Create WorkflowExecutor with mocked TaskRouter."""
        mock_router = Mock()
        return WorkflowExecutor(mock_router)

    def test_execute_single_task(self, executor):
        """Test executing workflow with single task."""
        executor.task_router.route.return_value = {'status': 'success', 'data': 'test'}
        
        workflow_tasks = [
            {'type': 'test_task', 'parameters': {}}
        ]
        
        result = executor.execute(workflow_tasks)
        
        assert result['status'] == 'completed'
        assert len(result['tasks']) == 1
        assert result['tasks'][0]['status'] == 'completed'

    def test_execute_multiple_tasks(self, executor):
        """Test executing workflow with multiple tasks."""
        executor.task_router.route.return_value = {'status': 'success'}
        
        workflow_tasks = [
            {'type': 'task1', 'parameters': {}},
            {'type': 'task2', 'parameters': {}},
            {'type': 'task3', 'parameters': {}}
        ]
        
        result = executor.execute(workflow_tasks)
        
        assert result['status'] == 'completed'
        assert len(result['tasks']) == 3
        assert all(t['status'] == 'completed' for t in result['tasks'])

    def test_execute_with_task_failure_non_critical(self, executor):
        """Test workflow continues on non-critical task failure."""
        def side_effect(task):
            if task['type'] == 'fail_task':
                raise Exception("Task failed")
            return {'status': 'success'}
        
        executor.task_router.route.side_effect = side_effect
        
        workflow_tasks = [
            {'type': 'task1', 'parameters': {}, 'critical': False},
            {'type': 'fail_task', 'parameters': {}, 'critical': False},
            {'type': 'task3', 'parameters': {}}
        ]
        
        result = executor.execute(workflow_tasks)
        
        # Workflow should complete despite non-critical failure
        assert result['status'] == 'completed'
        assert result['tasks'][1]['status'] == 'failed'
        assert result['tasks'][2]['status'] == 'completed'

    def test_execute_with_critical_task_failure(self, executor):
        """Test workflow stops on critical task failure."""
        def side_effect(task):
            if task['type'] == 'critical_fail':
                raise Exception("Critical task failed")
            return {'status': 'success'}
        
        executor.task_router.route.side_effect = side_effect
        
        workflow_tasks = [
            {'type': 'task1', 'parameters': {}},
            {'type': 'critical_fail', 'parameters': {}, 'critical': True},
            {'type': 'task3', 'parameters': {}}
        ]
        
        with pytest.raises(RecoveryError):
            executor.execute(workflow_tasks)

    def test_list_workflows(self, executor):
        """Test listing workflow history."""
        executor.task_router.route.return_value = {'status': 'success'}
        
        executor.execute([{'type': 'task', 'parameters': {}}])
        executor.execute([{'type': 'task', 'parameters': {}}])
        
        workflows = executor.list_workflows()
        assert len(workflows) == 2

    def test_get_summary(self, executor):
        """Test workflow summary."""
        executor.task_router.route.return_value = {'status': 'success'}
        
        executor.execute([{'type': 'task', 'parameters': {}}])
        executor.execute([{'type': 'task', 'parameters': {}}])
        
        summary = executor.get_summary()
        
        assert summary['total_workflows'] == 2
        assert summary['completed'] == 2
        assert summary['failed'] == 0


class TestOrchestratorIntegration:
    """Test Orchestrator integration."""

    @pytest.fixture
    def orchestrator(self):
        """Create Orchestrator instance."""
        return Orchestrator()

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes with all workers."""
        assert orchestrator.agent_registry is not None
        assert orchestrator.data_manager is not None
        assert orchestrator.task_router is not None
        assert orchestrator.workflow_executor is not None

    def test_register_and_retrieve_agent(self, orchestrator):
        """Test agent registration through orchestrator."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        orchestrator.register_agent("test", mock_agent)
        
        assert "test" in orchestrator.list_agents()
        assert orchestrator.get_agent("test") == mock_agent

    def test_cache_operations(self, orchestrator):
        """Test data caching through orchestrator."""
        data = {'key': 'value'}
        
        orchestrator.cache_data('test', data)
        assert orchestrator.get_cached_data('test') == data

    def test_get_status(self, orchestrator):
        """Test getting orchestrator status."""
        status = orchestrator.get_status()
        
        assert status['name'] == 'Orchestrator'
        assert status['status'] == 'active'
        assert 'agents' in status
        assert 'cache' in status
        assert 'workflows' in status

    def test_reset(self, orchestrator):
        """Test orchestrator reset."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        orchestrator.register_agent("test", mock_agent)
        orchestrator.cache_data("data", "value")
        
        assert len(orchestrator.list_agents()) == 1
        assert orchestrator.get_cached_data("data") == "value"
        
        orchestrator.reset()
        
        # Agent should still be registered
        assert len(orchestrator.list_agents()) == 1
        # Cache should be cleared
        assert orchestrator.get_cached_data("data") is None

    def test_shutdown(self, orchestrator):
        """Test orchestrator shutdown."""
        orchestrator.cache_data("data", "value")
        
        orchestrator.shutdown()
        
        # Cache should be cleared
        assert orchestrator.get_cached_data("data") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
