"""AgentRegistry Worker - Manages agent registration and tracking.

Responsibilities:
- Register agent instances
- Retrieve agents by name
- List all registered agents
- Validate agent availability
"""

from typing import Any, Dict, List, Optional
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from core.error_recovery import retry_on_error


class AgentRegistry:
    """Manages agent registration and lifecycle.
    
    Maintains a registry of all agent instances and provides
    methods to register, retrieve, and list agents.
    """

    def __init__(self) -> None:
        """Initialize the AgentRegistry."""
        self.name = "AgentRegistry"
        self.logger = get_logger("AgentRegistry")
        self.structured_logger = get_structured_logger("AgentRegistry")
        self.agents: Dict[str, Any] = {}
        self.logger.info("AgentRegistry initialized")

    @retry_on_error(max_attempts=2, backoff=1)
    def register(self, agent_name: str, agent_instance: Any) -> None:
        """Register an agent with error recovery.
        
        Args:
            agent_name: Unique name for the agent
            agent_instance: Agent instance to register
        
        Raises:
            AgentError: If agent registration fails
        """
        try:
            if agent_name in self.agents:
                raise AgentError(f"Agent '{agent_name}' already registered")
            
            if not hasattr(agent_instance, 'name'):
                raise AgentError(f"Agent must have a 'name' attribute")
            
            self.agents[agent_name] = agent_instance
            self.logger.info(f"Agent registered: {agent_name}")
            self.structured_logger.info("Agent registered", {
                'agent_name': agent_name,
                'total_agents': len(self.agents)
            })

        except Exception as e:
            self.logger.error(f"Agent registration failed: {e}")
            raise AgentError(f"Failed to register agent '{agent_name}': {e}")

    def get(self, agent_name: str) -> Optional[Any]:
        """Retrieve a registered agent.
        
        Args:
            agent_name: Name of the agent to retrieve
        
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_name)

    def list_all(self) -> List[str]:
        """List all registered agent names.
        
        Returns:
            List of agent names
        """
        return list(self.agents.keys())

    def is_registered(self, agent_name: str) -> bool:
        """Check if an agent is registered.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            True if registered, False otherwise
        """
        return agent_name in self.agents

    def get_or_fail(self, agent_name: str) -> Any:
        """Get an agent or raise error if not found.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Agent instance
        
        Raises:
            AgentError: If agent not registered
        """
        agent = self.get(agent_name)
        if agent is None:
            raise AgentError(f"Agent '{agent_name}' not registered")
        return agent

    def get_count(self) -> int:
        """Get total number of registered agents.
        
        Returns:
            Number of registered agents
        """
        return len(self.agents)

    def get_summary(self) -> Dict[str, Any]:
        """Get registry summary.
        
        Returns:
            Summary dict with agent names and count
        """
        return {
            'total_agents': len(self.agents),
            'agent_names': self.list_all()
        }
