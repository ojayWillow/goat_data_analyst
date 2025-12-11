"""Orchestrator Agent - Master coordinator for all other agents.

Refactored with worker architecture:
- AgentRegistry: Manages agent registration
- DataManager: Handles caching and data flow
- TaskRouter: Routes tasks to agents
- WorkflowExecutor: Executes multi-task workflows

Integrated with Week 1 foundation systems:
- Configuration management
- Error recovery with retry logic
- Structured logging
- Input/output validation
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import OrchestratorError
from core.error_recovery import retry_on_error
from core.validators import validate_output
from agents.orchestrator.workers.agent_registry import AgentRegistry
from agents.orchestrator.workers.data_manager import DataManager
from agents.orchestrator.workers.task_router import TaskRouter
from agents.orchestrator.workers.workflow_executor import WorkflowExecutor


class Orchestrator:
    """Master agent that coordinates all other specialized agents.
    
    Responsibilities:
    - Manage agent lifecycle (via AgentRegistry)
    - Route tasks to agents (via TaskRouter)
    - Handle data flow between agents (via DataManager)
    - Execute workflows (via WorkflowExecutor)
    - Aggregate and manage results
    
    Architecture:
    - Uses worker pattern for separation of concerns
    - Each worker handles specific responsibility
    - Clean interfaces between components
    - Integrated with Week 1 systems
    """

    def __init__(self) -> None:
        """Initialize the Orchestrator with all workers."""
        self.name = "Orchestrator"
        self.logger = get_logger("Orchestrator")
        self.structured_logger = get_structured_logger("Orchestrator")
        
        # Initialize workers
        self.agent_registry = AgentRegistry()
        self.data_manager = DataManager()
        self.task_router = TaskRouter(self.agent_registry, self.data_manager)
        self.workflow_executor = WorkflowExecutor(self.task_router)
        
        # Tracking
        self.current_task: Optional[Dict[str, Any]] = None
        
        self.logger.info("Orchestrator initialized with worker architecture")
        self.structured_logger.info("Orchestrator initialized", {
            'version': '2.1-refactored',
            'workers': ['AgentRegistry', 'DataManager', 'TaskRouter', 'WorkflowExecutor']
        })

    # ========== Agent Management ==========

    @retry_on_error(max_attempts=2, backoff=1)
    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """Register an agent.
        
        Args:
            agent_name: Unique name for the agent
            agent_instance: Agent instance
        
        Raises:
            OrchestratorError: If registration fails
        """
        try:
            self.agent_registry.register(agent_name, agent_instance)
            self.logger.info(f"Agent registered: {agent_name}")
        except Exception as e:
            raise OrchestratorError(f"Agent registration failed: {e}")

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get a registered agent.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Agent instance or None
        """
        return self.agent_registry.get(agent_name)

    def list_agents(self) -> List[str]:
        """List all registered agents.
        
        Returns:
            List of agent names
        """
        return self.agent_registry.list_all()

    # ========== Data Management ==========

    def cache_data(self, key: str, data: Any) -> None:
        """Cache data for inter-agent sharing.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        self.data_manager.cache(key, data)

    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data.
        
        Args:
            key: Cache key
        
        Returns:
            Cached data or None
        """
        return self.data_manager.get(key)

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.data_manager.clear()
        self.logger.info("Cache cleared")

    # ========== Task Management ==========

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def execute_task(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task.
        
        Args:
            task_type: Type of task (load_data, explore_data, etc.)
            parameters: Task parameters
        
        Returns:
            Task result dict (validated)
        
        Raises:
            OrchestratorError: If task execution fails
        """
        task = {
            'id': f"task_{datetime.now().timestamp()}",
            'type': task_type,
            'parameters': parameters,
            'status': 'created',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.current_task = task
        
        self.logger.info(f"Executing task: {task_type}")
        self.structured_logger.info("Task execution started", {
            'task_type': task_type,
            'param_count': len(parameters)
        })
        
        try:
            task['status'] = 'executing'
            result = self.task_router.route(task)
            task['status'] = 'completed'
            task['result'] = result
            return task
        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
            self.logger.error(f"Task execution failed: {e}")
            raise OrchestratorError(f"Task execution failed: {e}")

    # ========== Workflow Management ==========

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def execute_workflow(self, workflow_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a workflow (sequence of tasks).
        
        Args:
            workflow_tasks: List of task configs
        
        Returns:
            Workflow result dict (validated)
        
        Raises:
            OrchestratorError: If workflow execution fails
        """
        self.logger.info(f"Executing workflow with {len(workflow_tasks)} tasks")
        self.structured_logger.info("Workflow execution started", {
            'total_tasks': len(workflow_tasks)
        })
        
        try:
            return self.workflow_executor.execute(workflow_tasks)
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            raise OrchestratorError(f"Workflow execution failed: {e}")

    # ========== Status & Reporting ==========

    @validate_output('dict')
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status.
        
        Returns:
            Status dict (validated)
        """
        return {
            'name': self.name,
            'status': 'active',
            'agents': self.agent_registry.get_summary(),
            'cache': self.data_manager.get_summary(),
            'workflows': self.workflow_executor.get_summary(),
            'current_task': self.current_task['type'] if self.current_task else None
        }

    @validate_output('dict')
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed status including all workflows and cache.
        
        Returns:
            Detailed status dict (validated)
        """
        return {
            'name': self.name,
            'status': 'active',
            'agents': {
                'registered': self.list_agents(),
                'count': self.agent_registry.get_count()
            },
            'cache': {
                'items': self.data_manager.get_count(),
                'keys': self.data_manager.list_keys()
            },
            'workflows': {
                'executed': self.workflow_executor.get_summary(),
                'history': self.workflow_executor.list_workflows()
            },
            'current_task': self.current_task
        }

    # ========== Utility Methods ==========

    def reset(self) -> None:
        """Reset orchestrator state (keep agents, clear cache and history)."""
        self.data_manager.clear()
        self.current_task = None
        self.logger.info("Orchestrator reset")

    def shutdown(self) -> None:
        """Shutdown orchestrator (cleanup resources)."""
        self.reset()
        self.logger.info("Orchestrator shutdown")
