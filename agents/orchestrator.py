"""Orchestrator Agent - Master coordinator for all other agents."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from core.logger import get_logger
from core.exceptions import OrchestratorError

logger = get_logger(__name__)


class Orchestrator:
    """Master agent that coordinates all other specialized agents.
    
    Responsibilities:
    - Manage agent lifecycle and communication
    - Route tasks to appropriate agents
    - Aggregate results from multiple agents
    - Handle error management and retries
    - Maintain workflow state
    """
    
    def __init__(self):
        """Initialize the Orchestrator."""
        self.name = "Orchestrator"
        self.agents = {}  # Registry of available agents
        self.workflow_history = []
        self.current_task = None
        logger.info(f"{self.name} initialized")
    
    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """Register a new agent.
        
        Args:
            agent_name: Unique name for the agent
            agent_instance: Agent instance
            
        Raises:
            OrchestratorError: If agent registration fails
        """
        try:
            if agent_name in self.agents:
                raise OrchestratorError(f"Agent '{agent_name}' already registered")
            
            self.agents[agent_name] = agent_instance
            logger.info(f"Registered agent: {agent_name}")
        except Exception as e:
            logger.error(f"Failed to register agent {agent_name}: {e}")
            raise OrchestratorError(f"Agent registration failed: {e}")
    
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get a registered agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """List all registered agents.
        
        Returns:
            List of agent names
        """
        return list(self.agents.keys())
    
    def create_task(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create and route a task to appropriate agent(s).
        
        Args:
            task_type: Type of task (data_load, explore, visualize, etc.)
            parameters: Task parameters
            
        Returns:
            Task metadata and status
            
        Raises:
            OrchestratorError: If task creation fails
        """
        try:
            task = {
                "id": self._generate_task_id(),
                "type": task_type,
                "parameters": parameters,
                "status": "created",
                "created_at": datetime.utcnow().isoformat(),
                "result": None,
                "error": None,
            }
            
            self.current_task = task
            self.workflow_history.append(task)
            logger.info(f"Task created: {task['id']} (type: {task_type})")
            return task
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise OrchestratorError(f"Task creation failed: {e}")
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a task (route to appropriate agent(s)).
        
        Args:
            task_id: ID of task to execute
            
        Returns:
            Task result
            
        Raises:
            OrchestratorError: If execution fails
        """
        try:
            task = self._get_task(task_id)
            if not task:
                raise OrchestratorError(f"Task {task_id} not found")
            
            task["status"] = "executing"
            task["started_at"] = datetime.utcnow().isoformat()
            
            # Route to appropriate agent based on task type
            result = self._route_task(task)
            
            task["status"] = "completed"
            task["result"] = result
            task["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Task completed: {task_id}")
            return task
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task["status"] = "failed"
            task["error"] = str(e)
            raise OrchestratorError(f"Task execution failed: {e}")
    
    def _route_task(self, task: Dict[str, Any]) -> Any:
        """Route task to appropriate agent(s).
        
        Args:
            task: Task to route
            
        Returns:
            Task result from agent
        """
        task_type = task["type"]
        logger.info(f"Routing task to agent: {task_type}")
        
        # TODO: Implement agent routing logic
        # Example routing:
        # if task_type == "data_load":
        #     agent = self.get_agent("data_loader")
        #     return agent.execute(task["parameters"])
        
        return {"status": "pending", "message": f"Task {task_type} routed to agent"}
    
    def _get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task from history.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dict or None
        """
        for task in self.workflow_history:
            if task["id"] == task_id:
                return task
        return None
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID.
        
        Returns:
            Unique task ID
        """
        return f"task_{len(self.workflow_history) + 1:05d}"
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status.
        
        Returns:
            Workflow status including all tasks
        """
        return {
            "total_tasks": len(self.workflow_history),
            "current_task": self.current_task["id"] if self.current_task else None,
            "registered_agents": self.list_agents(),
            "tasks": self.workflow_history,
        }
