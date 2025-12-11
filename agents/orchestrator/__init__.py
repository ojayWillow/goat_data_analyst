"""Orchestrator Agent - Master coordinator for all other agents.

Refactored architecture:
- Main Orchestrator class coordinates all agents
- Workers handle specific responsibilities:
  - TaskRouter: Route tasks to appropriate agents
  - WorkflowExecutor: Execute multi-task workflows
  - DataManager: Handle caching and data flow
  - AgentRegistry: Manage agent registration
  - NarrativeIntegrator: Bridge to narrative generator

Integrated with Week 1 foundation systems:
- Configuration management
- Error recovery with retry logic
- Structured logging
- Input/output validation
"""

from .orchestrator import Orchestrator
from .workers.task_router import TaskRouter
from .workers.workflow_executor import WorkflowExecutor
from .workers.data_manager import DataManager
from .workers.agent_registry import AgentRegistry
from .workers.narrative_integrator import NarrativeIntegrator

__all__ = [
    "Orchestrator",
    "TaskRouter",
    "WorkflowExecutor",
    "DataManager",
    "AgentRegistry",
    "NarrativeIntegrator"
]
