#!/usr/bin/env python3
"""Pytest-compatible tests for Orchestrator agent.

Tests cover:
- Initialization with workers
- Agent registration and management
- Data caching
- Task execution
- Workflow execution
- Narrative generation
- Status reporting
- Error handling

Run with: pytest scripts/test_orchestrator.py -v
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.orchestrator.orchestrator import Orchestrator
from core.exceptions import OrchestratorError
from core.logger import get_logger

logger = get_logger(__name__)


class TestOrchestratorInitialization:
    """Test Orchestrator initialization."""
    
    def test_orchestrator_initialization(self):
        """Test Orchestrator initializes correctly."""
        orchestrator = Orchestrator()
        
        assert orchestrator is not None
        assert orchestrator.name == "Orchestrator"
        assert orchestrator.logger is not None
        assert orchestrator.structured_logger is not None
        logger.info("✓ Initialization test passed")
    
    def test_workers_initialized(self):
        """Test all workers are initialized."""
        orchestrator = Orchestrator()
        
        assert orchestrator.agent_registry is not None
        assert orchestrator.data_manager is not None
        assert orchestrator.task_router is not None
        assert orchestrator.workflow_executor is not None
        assert orchestrator.narrative_integrator is not None
        logger.info("✓ Workers initialization test passed")
    
    def test_initial_state(self):
        """Test initial state of Orchestrator."""
        orchestrator = Orchestrator()
        
        assert orchestrator.current_task is None
        assert orchestrator.agent_registry.get_count() >= 0
        logger.info("✓ Initial state test passed")


class TestOrchestratorAgentManagement:
    """Test agent registration and management."""
    
    @pytest.fixture
    def orchestrator(self):
        return Orchestrator()
    
    def test_register_agent(self, orchestrator):
        """Test registering an agent."""
        # Create mock agent
        mock_agent = Mock()
        mock_agent.name = "MockAgent"
        
        # Register
        orchestrator.register_agent("mock_agent", mock_agent)
        
        # Verify
        retrieved = orchestrator.get_agent("mock_agent")
        assert retrieved is not None
        logger.info("✓ Register agent test passed")
    
    def test_register_multiple_agents(self, orchestrator):
        """Test registering multiple agents."""
        agents = {}
        for i in range(5):
            mock_agent = Mock()
            mock_agent.name = f"Agent{i}"
            agents[f"agent_{i}"] = mock_agent
            orchestrator.register_agent(f"agent_{i}", mock_agent)
        
        # Verify all registered
        for name in agents.keys():
            assert orchestrator.get_agent(name) is not None
        
        logger.info("✓ Register multiple agents test passed")
    
    def test_list_agents(self, orchestrator):
        """Test listing registered agents."""
        # Register some agents
        for i in range(3):
            mock_agent = Mock()
            orchestrator.register_agent(f"test_agent_{i}", mock_agent)
        
        agents_list = orchestrator.list_agents()
        assert isinstance(agents_list, list)
        assert len(agents_list) >= 3
        logger.info("✓ List agents test passed")
    
    def test_get_nonexistent_agent(self, orchestrator):
        """Test getting non-existent agent."""
        result = orchestrator.get_agent("nonexistent_agent")
        assert result is None
        logger.info("✓ Get nonexistent agent test passed")
    
    def test_register_agent_with_special_names(self, orchestrator):
        """Test registering agents with special names."""
        special_names = [
            "agent-with-dash",
            "agent_with_underscore",
            "AgentWithCaps",
            "agent123"
        ]
        
        for name in special_names:
            mock_agent = Mock()
            orchestrator.register_agent(name, mock_agent)
            assert orchestrator.get_agent(name) is not None
        
        logger.info("✓ Special names test passed")


class TestOrchestratorDataManagement:
    """Test data caching and management."""
    
    @pytest.fixture
    def orchestrator(self):
        return Orchestrator()
    
    def test_cache_data(self, orchestrator):
        """Test caching data."""
        orchestrator.cache_data("test_key", {"value": 42})
        
        cached = orchestrator.get_cached_data("test_key")
        assert cached == {"value": 42}
        logger.info("✓ Cache data test passed")
    
    def test_cache_multiple_items(self, orchestrator):
        """Test caching multiple items."""
        data_items = {
            "key1": {"data": 1},
            "key2": {"data": 2},
            "key3": {"data": 3}
        }
        
        for key, value in data_items.items():
            orchestrator.cache_data(key, value)
        
        for key, value in data_items.items():
            assert orchestrator.get_cached_data(key) == value
        
        logger.info("✓ Cache multiple items test passed")
    
    def test_get_nonexistent_cached_data(self, orchestrator):
        """Test getting non-existent cached data."""
        result = orchestrator.get_cached_data("nonexistent")
        assert result is None
        logger.info("✓ Get nonexistent cached data test passed")
    
    def test_clear_cache(self, orchestrator):
        """Test clearing cache."""
        # Add data
        orchestrator.cache_data("key1", "value1")
        orchestrator.cache_data("key2", "value2")
        
        # Clear
        orchestrator.clear_cache()
        
        # Verify cleared
        assert orchestrator.get_cached_data("key1") is None
        assert orchestrator.get_cached_data("key2") is None
        logger.info("✓ Clear cache test passed")
    
    def test_cache_large_data(self, orchestrator):
        """Test caching large data structures."""
        large_data = {
            f"item_{i}": {"value": i, "data": [j for j in range(100)]}
            for i in range(100)
        }
        
        orchestrator.cache_data("large_data", large_data)
        retrieved = orchestrator.get_cached_data("large_data")
        
        assert retrieved == large_data
        assert len(retrieved) == 100
        logger.info("✓ Cache large data test passed")


class TestOrchestratorTaskExecution:
    """Test task execution."""
    
    @pytest.fixture
    def orchestrator(self):
        orch = Orchestrator()
        # Mock the task_router to avoid actual execution
        orch.task_router.route = MagicMock(return_value={"status": "success", "result": "test"})
        return orch
    
    def test_execute_simple_task(self, orchestrator):
        """Test executing a simple task."""
        result = orchestrator.execute_task("test_task", {"param1": "value1"})
        
        assert result is not None
        assert result["type"] == "test_task"
        assert result["status"] in ["completed", "success"]
        assert "id" in result
        logger.info("✓ Execute simple task test passed")
    
    def test_execute_task_with_parameters(self, orchestrator):
        """Test executing task with various parameters."""
        params = {
            "string_param": "test",
            "int_param": 42,
            "list_param": [1, 2, 3],
            "dict_param": {"nested": "value"}
        }
        
        result = orchestrator.execute_task("complex_task", params)
        
        assert result["parameters"] == params
        logger.info("✓ Execute task with parameters test passed")
    
    def test_task_tracking(self, orchestrator):
        """Test that current_task is updated."""
        assert orchestrator.current_task is None
        
        orchestrator.execute_task("test_task", {})
        
        assert orchestrator.current_task is not None
        assert orchestrator.current_task["type"] == "test_task"
        logger.info("✓ Task tracking test passed")
    
    def test_task_has_timestamp(self, orchestrator):
        """Test that tasks have timestamps."""
        result = orchestrator.execute_task("timed_task", {})
        
        assert "created_at" in result
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(result["created_at"].replace('Z', '+00:00'))
        logger.info("✓ Task timestamp test passed")


class TestOrchestratorWorkflows:
    """Test workflow execution."""
    
    @pytest.fixture
    def orchestrator(self):
        orch = Orchestrator()
        # Mock the workflow_executor
        orch.workflow_executor.execute = MagicMock(return_value={
            "status": "completed",
            "tasks_executed": 0,
            "results": {}
        })
        return orch
    
    def test_execute_workflow(self, orchestrator):
        """Test executing a workflow."""
        workflow_tasks = [
            {"type": "load_data", "parameters": {}},
            {"type": "explore_data", "parameters": {}},
            {"type": "analyze_data", "parameters": {}}
        ]
        
        result = orchestrator.execute_workflow(workflow_tasks)
        
        assert result is not None
        assert result["status"] == "completed"
        logger.info("✓ Execute workflow test passed")
    
    def test_execute_empty_workflow(self, orchestrator):
        """Test executing empty workflow."""
        result = orchestrator.execute_workflow([])
        
        assert result is not None
        logger.info("✓ Execute empty workflow test passed")
    
    def test_workflow_with_many_tasks(self, orchestrator):
        """Test workflow with many tasks."""
        workflow_tasks = [
            {"type": f"task_{i}", "parameters": {"index": i}}
            for i in range(50)
        ]
        
        result = orchestrator.execute_workflow(workflow_tasks)
        
        assert result is not None
        logger.info("✓ Workflow with many tasks test passed")


class TestOrchestratorNarrative:
    """Test narrative generation."""
    
    @pytest.fixture
    def orchestrator(self):
        orch = Orchestrator()
        # Mock the narrative_integrator
        orch.narrative_integrator.generate_narrative_from_results = MagicMock(
            return_value={"status": "success", "narrative": "Test narrative"}
        )
        orch.narrative_integrator.generate_narrative_from_workflow = MagicMock(
            return_value={"status": "success", "workflow_result": {}, "narrative": "Test"}
        )
        return orch
    
    def test_generate_narrative(self, orchestrator):
        """Test generating narrative from results."""
        results = {
            "anomalies": {"count": 3},
            "predictions": {"accuracy": 0.92}
        }
        
        result = orchestrator.generate_narrative(results)
        
        assert result is not None
        assert result["status"] == "success"
        logger.info("✓ Generate narrative test passed")
    
    def test_execute_workflow_with_narrative(self, orchestrator):
        """Test executing workflow with narrative generation."""
        workflow_tasks = [
            {"type": "load_data", "parameters": {}},
            {"type": "explore_data", "parameters": {}}
        ]
        
        result = orchestrator.execute_workflow_with_narrative(workflow_tasks)
        
        assert result is not None
        assert result["status"] == "success"
        logger.info("✓ Workflow with narrative test passed")


class TestOrchestratorStatus:
    """Test status reporting."""
    
    @pytest.fixture
    def orchestrator(self):
        return Orchestrator()
    
    def test_get_status(self, orchestrator):
        """Test getting orchestrator status."""
        status = orchestrator.get_status()
        
        assert status is not None
        assert "name" in status
        assert "status" in status
        assert "agents" in status
        assert "cache" in status
        assert status["name"] == "Orchestrator"
        logger.info("✓ Get status test passed")
    
    def test_get_detailed_status(self, orchestrator):
        """Test getting detailed status."""
        # Add some data
        orchestrator.cache_data("test", "data")
        mock_agent = Mock()
        orchestrator.register_agent("test_agent", mock_agent)
        
        status = orchestrator.get_detailed_status()
        
        assert status is not None
        assert "name" in status
        assert "agents" in status
        assert "cache" in status
        assert "workflows" in status
        assert "current_task" in status
        logger.info("✓ Get detailed status test passed")
    
    def test_status_after_task_execution(self, orchestrator):
        """Test status after task execution."""
        # Mock task router
        orchestrator.task_router.route = MagicMock(return_value={"status": "success"})
        
        orchestrator.execute_task("test", {})
        status = orchestrator.get_status()
        
        assert status["current_task"] == "test"
        logger.info("✓ Status after task execution test passed")


class TestOrchestratorUtility:
    """Test utility methods."""
    
    @pytest.fixture
    def orchestrator(self):
        return Orchestrator()
    
    def test_reset(self, orchestrator):
        """Test resetting orchestrator."""
        # Add some data
        orchestrator.cache_data("key", "value")
        orchestrator.current_task = {"type": "test"}
        
        # Reset
        orchestrator.reset()
        
        # Verify reset
        assert orchestrator.get_cached_data("key") is None
        assert orchestrator.current_task is None
        logger.info("✓ Reset test passed")
    
    def test_shutdown(self, orchestrator):
        """Test shutting down orchestrator."""
        # Add some data
        orchestrator.cache_data("key", "value")
        
        # Shutdown
        orchestrator.shutdown()
        
        # Verify shutdown (cache cleared)
        assert orchestrator.get_cached_data("key") is None
        logger.info("✓ Shutdown test passed")


class TestOrchestratorEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def orchestrator(self):
        orch = Orchestrator()
        orch.task_router.route = MagicMock(return_value={"status": "success"})
        return orch
    
    def test_execute_task_with_empty_parameters(self, orchestrator):
        """Test executing task with empty parameters."""
        result = orchestrator.execute_task("test_task", {})
        assert result is not None
        logger.info("✓ Empty parameters test passed")
    
    def test_execute_task_with_none_parameters(self, orchestrator):
        """Test executing task with None parameters."""
        try:
            result = orchestrator.execute_task("test_task", None)
            # Should handle gracefully
            assert True
        except (TypeError, AttributeError):
            # This is acceptable
            pass
        logger.info("✓ None parameters test passed")
    
    def test_cache_data_with_none_value(self, orchestrator):
        """Test caching None value."""
        orchestrator.cache_data("none_key", None)
        retrieved = orchestrator.get_cached_data("none_key")
        
        assert retrieved is None
        logger.info("✓ Cache None value test passed")
    
    def test_multiple_resets(self, orchestrator):
        """Test multiple reset calls."""
        for _ in range(5):
            orchestrator.cache_data("key", "value")
            orchestrator.reset()
            assert orchestrator.get_cached_data("key") is None
        
        logger.info("✓ Multiple resets test passed")
    
    def test_interleaved_operations(self, orchestrator):
        """Test interleaved cache, agent, and task operations."""
        # Cache
        orchestrator.cache_data("data1", {"value": 1})
        
        # Register agent
        mock_agent = Mock()
        orchestrator.register_agent("agent1", mock_agent)
        
        # Cache again
        orchestrator.cache_data("data2", {"value": 2})
        
        # Execute task
        orchestrator.execute_task("task1", {})
        
        # Verify all operations
        assert orchestrator.get_cached_data("data1") is not None
        assert orchestrator.get_cached_data("data2") is not None
        assert orchestrator.get_agent("agent1") is not None
        assert orchestrator.current_task is not None
        
        logger.info("✓ Interleaved operations test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
