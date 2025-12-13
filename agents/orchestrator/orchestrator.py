"""Orchestrator Agent - Master coordinator for all other agents.

Upgraded with quality tracking and error handling.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import OrchestratorError, DataValidationError
from core.error_recovery import retry_on_error
from core.validators import validate_output

from agents.error_intelligence.main import ErrorIntelligence
from agents.orchestrator.workers.agent_registry import AgentRegistry
from agents.orchestrator.workers.data_manager import DataManager
from agents.orchestrator.workers.task_router import TaskRouter
from agents.orchestrator.workers.workflow_executor import WorkflowExecutor
from agents.orchestrator.workers.narrative_integrator import NarrativeIntegrator


class TaskStatus(Enum):
    """Task execution status."""
    CREATED = "created"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class QualityScore:
    """Track quality metrics."""
    
    def __init__(self) -> None:
        self.tasks_successful: int = 0
        self.tasks_failed: int = 0
        self.tasks_partial: int = 0
        self.errors_by_type: Dict[str, int] = {}
    
    def add_success(self) -> None:
        self.tasks_successful += 1
    
    def add_failure(self) -> None:
        self.tasks_failed += 1
    
    def add_partial(self) -> None:
        self.tasks_partial += 1
    
    def get_score(self) -> float:
        """Quality score (0-1)."""
        total = self.tasks_successful + self.tasks_failed + self.tasks_partial
        if total == 0:
            return 1.0
        return round((self.tasks_successful + self.tasks_partial * 0.5) / total, 3)
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'quality_score': self.get_score(),
            'tasks': {
                'successful': self.tasks_successful,
                'failed': self.tasks_failed,
                'partial': self.tasks_partial
            }
        }


class Orchestrator:
    """Master agent coordinating all specialized agents."""

    def __init__(self) -> None:
        self.name = "Orchestrator"
        self.version = "3.0-enhanced"
        self.logger = get_logger("Orchestrator")
        self.structured_logger = get_structured_logger("Orchestrator")
        
        # Core components
        self.error_intelligence = ErrorIntelligence()
        self.quality_tracker = QualityScore()
        self.agent_registry = AgentRegistry()
        self.data_manager = DataManager()
        self.task_router = TaskRouter(self.agent_registry, self.data_manager)
        self.workflow_executor = WorkflowExecutor(self.task_router)
        self.narrative_integrator = NarrativeIntegrator()
        
        # State
        self.current_task: Optional[Dict[str, Any]] = None
        self.current_workflow: Optional[Dict[str, Any]] = None
        self.execution_history: List[Dict[str, Any]] = []
        
        self.logger.info(f"Orchestrator initialized (v{self.version})")

    # ========== AGENT MANAGEMENT ==========

    @retry_on_error(max_attempts=3, backoff=2)
    def register_agent(
        self,
        agent_name: str,
        agent_instance: Any
    ) -> Dict[str, Any]:
        """Register an agent."""
        try:
            if not hasattr(agent_instance, 'name'):
                raise DataValidationError(f"Agent must have 'name' attribute")
            
            self.logger.info(f"Registering agent: {agent_name}")
            self.agent_registry.register(agent_name, agent_instance)
            self.quality_tracker.add_success()
            
            self.error_intelligence.track_success(
                agent_name=self.name,
                worker_name="AgentRegistry",
                operation="register_agent",
                context={"agent_name": agent_name}
            )
            
            return {
                'success': True,
                'agent_name': agent_name,
                'registered_at': datetime.now(timezone.utc).isoformat(),
                'total_agents': self.agent_registry.get_count(),
                'quality_score': self.quality_tracker.get_score()
            }
        
        except Exception as e:
            self.logger.error(f"Agent registration failed: {e}")
            self.quality_tracker.add_failure()
            self.error_intelligence.track_error(
                agent_name=self.name,
                worker_name="AgentRegistry",
                error_type="AgentRegistrationError",
                error_message=str(e)
            )
            raise OrchestratorError(f"Failed to register agent: {str(e)}")

    @retry_on_error(max_attempts=2, backoff=1)
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get registered agent."""
        return self.agent_registry.get(agent_name)

    @retry_on_error(max_attempts=2, backoff=1)
    def list_agents(self) -> Dict[str, Any]:
        """List all agents."""
        agents = self.agent_registry.list_all()
        return {
            'agents': agents,
            'total': len(agents),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    # ========== DATA MANAGEMENT ==========

    @retry_on_error(max_attempts=2, backoff=1)
    def cache_data(self, key: str, data: Any) -> Dict[str, Any]:
        """Cache data."""
        self.data_manager.set(key, data)
        return {
            'success': True,
            'key': key,
            'cached_at': datetime.now(timezone.utc).isoformat(),
            'cache_size': self.data_manager.get_count()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data."""
        return self.data_manager.get(key)

    @retry_on_error(max_attempts=2, backoff=1)
    def list_cached_data(self) -> Dict[str, Any]:
        """List cache."""
        return {
            'keys': self.data_manager.list_keys(),
            'count': self.data_manager.get_count(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    def clear_cache(self) -> Dict[str, Any]:
        """Clear cache."""
        self.data_manager.clear()
        self.logger.info("Cache cleared")
        return {
            'success': True,
            'cleared_at': datetime.now(timezone.utc).isoformat()
        }

    # ========== TASK EXECUTION ==========

    @retry_on_error(max_attempts=3, backoff=2)
    @validate_output('dict')
    def execute_task(
        self,
        task_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a single task."""
        task_start = datetime.now(timezone.utc)
        task_id = f"task_{task_start.timestamp()}"
        task = {
            'id': task_id,
            'type': task_type,
            'parameters': parameters if parameters else {},
            'status': TaskStatus.CREATED.value,
            'created_at': task_start.isoformat()
        }
        
        self.current_task = task
        self.logger.info(f"Task created: {task_id} (type: {task_type})")
        
        try:
            task['status'] = TaskStatus.EXECUTING.value
            result = self.task_router.route(task)
            
            task['status'] = TaskStatus.COMPLETED.value
            task['result'] = result
            task['quality_score'] = result.get('quality_score', 1.0) if isinstance(result, dict) else 1.0
            
            self.quality_tracker.add_success()
            self.error_intelligence.track_success(
                agent_name=self.name,
                worker_name="TaskRouter",
                operation="execute_task",
                context={"task_type": task_type}
            )
            
            self.logger.info(f"Task completed: {task_id}")
        
        except Exception as e:
            task['status'] = TaskStatus.FAILED.value
            task['error'] = str(e)
            self.quality_tracker.add_failure()
            
            self.error_intelligence.track_error(
                agent_name=self.name,
                worker_name="TaskRouter",
                error_type="TaskExecutionError",
                error_message=str(e),
                context={"task_type": task_type}
            )
            
            self.logger.error(f"Task failed: {task_id} - {e}")
            raise OrchestratorError(f"Task execution failed: {str(e)}")
        
        finally:
            task_end = datetime.now(timezone.utc)
            task['duration_seconds'] = (task_end - task_start).total_seconds()
            self.execution_history.append(task)
        
        return task

    # ========== WORKFLOW EXECUTION ==========

    @retry_on_error(max_attempts=3, backoff=2)
    @validate_output('dict')
    def execute_workflow(
        self,
        workflow_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        workflow_start = datetime.now(timezone.utc)
        workflow_id = f"workflow_{workflow_start.timestamp()}"
        
        workflow = {
            'id': workflow_id,
            'status': WorkflowStatus.CREATED.value,
            'created_at': workflow_start.isoformat(),
            'total_tasks': len(workflow_tasks),
            'completed_tasks': 0,
            'failed_tasks': 0,
            'results': {}
        }
        
        self.current_workflow = workflow
        self.logger.info(f"Workflow started: {workflow_id} ({len(workflow_tasks)} tasks)")
        
        try:
            workflow['status'] = WorkflowStatus.RUNNING.value
            
            for idx, task_config in enumerate(workflow_tasks):
                task_type = task_config.get('type')
                params = task_config.get('parameters', {})
                
                self.logger.info(f"Task {idx+1}/{len(workflow_tasks)}: {task_type}")
                
                try:
                    task_result = self.execute_task(task_type, params)
                    workflow['results'][task_result['id']] = task_result
                    workflow['completed_tasks'] += 1
                except Exception as e:
                    self.logger.warning(f"Task {idx+1} failed: {task_type}")
                    workflow['failed_tasks'] += 1
            
            if workflow['failed_tasks'] == 0:
                workflow['status'] = WorkflowStatus.COMPLETED.value
                self.quality_tracker.add_success()
            elif workflow['completed_tasks'] > 0:
                workflow['status'] = WorkflowStatus.PARTIALLY_COMPLETED.value
                self.quality_tracker.add_partial()
            else:
                workflow['status'] = WorkflowStatus.FAILED.value
                self.quality_tracker.add_failure()
            
            self.logger.info(f"Workflow completed: {workflow_id}")
            return workflow
        
        except Exception as e:
            workflow['status'] = WorkflowStatus.FAILED.value
            self.quality_tracker.add_failure()
            self.logger.error(f"Workflow failed: {e}")
            raise OrchestratorError(f"Workflow execution failed: {str(e)}")
        
        finally:
            workflow_end = datetime.now(timezone.utc)
            workflow['duration_seconds'] = (workflow_end - workflow_start).total_seconds()
            self.execution_history.append(workflow)

    # ========== NARRATIVE GENERATION ==========

    @retry_on_error(max_attempts=3, backoff=2)
    @validate_output('dict')
    def generate_narrative(
        self,
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate narrative from results."""
        try:
            self.logger.info("Generating narrative")
            result = self.narrative_integrator.generate_narrative_from_results(agent_results)
            self.quality_tracker.add_success()
            return result
        except Exception as e:
            self.quality_tracker.add_failure()
            self.logger.error(f"Narrative generation failed: {e}")
            raise OrchestratorError(f"Narrative generation failed: {str(e)}")

    @retry_on_error(max_attempts=3, backoff=2)
    @validate_output('dict')
    def execute_workflow_with_narrative(
        self,
        workflow_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute workflow and generate narrative."""
        pipeline_start = datetime.now(timezone.utc)
        
        try:
            self.logger.info("Full pipeline started")
            workflow_result = self.execute_workflow(workflow_tasks)
            
            agent_results = {}
            for task_id, task_result in workflow_result.get('results', {}).items():
                if task_result.get('status') == TaskStatus.COMPLETED.value:
                    agent_results[task_id] = task_result.get('result')
            
            narrative_result = self.generate_narrative(agent_results)
            
            pipeline_end = datetime.now(timezone.utc)
            return {
                'workflow_id': workflow_result['id'],
                'workflow_results': workflow_result,
                'narrative': narrative_result,
                'duration_seconds': (pipeline_end - pipeline_start).total_seconds()
            }
        except Exception as e:
            self.quality_tracker.add_failure()
            self.logger.error(f"Full pipeline failed: {e}")
            raise OrchestratorError(f"Full pipeline failed: {str(e)}")

    # ========== STATUS & HEALTH ==========

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def get_health_report(self) -> Dict[str, Any]:
        """Get health report."""
        health_score = self.quality_tracker.get_score() * 100
        
        return {
            'overall_health': health_score,
            'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'critical',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'quality': self.quality_tracker.get_summary()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def get_status(self) -> Dict[str, Any]:
        """Get quick status."""
        return {
            'name': self.name,
            'version': self.version,
            'status': 'active',
            'health_score': self.quality_tracker.get_score() * 100,
            'agents_registered': self.agent_registry.get_count(),
            'cache_items': self.data_manager.get_count(),
            'quality_score': self.quality_tracker.get_score(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed status."""
        return {
            'name': self.name,
            'version': self.version,
            'agents': {
                'registered': self.list_agents()['agents'],
                'count': self.agent_registry.get_count()
            },
            'cache': {
                'items': self.data_manager.get_count(),
                'keys': self.data_manager.list_keys()
            },
            'health': self.quality_tracker.get_score() * 100
        }

    # ========== CLEANUP ==========

    @retry_on_error(max_attempts=2, backoff=1)
    def get_execution_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get execution history."""
        history = self.execution_history
        return history[-limit:] if limit else history

    @retry_on_error(max_attempts=2, backoff=1)
    def clear_history(self) -> Dict[str, Any]:
        """Clear history."""
        count = len(self.execution_history)
        self.execution_history.clear()
        self.logger.info(f"History cleared ({count} records)")
        return {
            'success': True,
            'cleared_count': count,
            'cleared_at': datetime.now(timezone.utc).isoformat()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    def reset(self) -> Dict[str, Any]:
        """Reset orchestrator."""
        self.data_manager.clear()
        self.execution_history.clear()
        self.current_task = None
        self.current_workflow = None
        self.logger.info("Orchestrator reset")
        return {
            'success': True,
            'reset_at': datetime.now(timezone.utc).isoformat()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    def shutdown(self) -> Dict[str, Any]:
        """Shutdown orchestrator."""
        final_health = self.quality_tracker.get_score() * 100
        self.reset()
        self.logger.info(f"Orchestrator shutdown (health: {final_health:.1f})")
        return {
            'success': True,
            'shutdown_at': datetime.now(timezone.utc).isoformat(),
            'final_health_score': final_health
        }
