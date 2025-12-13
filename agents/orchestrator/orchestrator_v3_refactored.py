"""Orchestrator Agent v3 - Enhanced with Full ErrorIntelligence Integration.

Master coordinator for all other agents with enterprise-grade error handling,
quality tracking, and comprehensive resilience mechanisms.

Refactored Architecture:
- AgentRegistry: Manages agent registration & lifecycle
- DataManager: Handles caching and data flow between agents
- TaskRouter: Routes tasks to appropriate agents
- WorkflowExecutor: Executes multi-task workflows
- NarrativeIntegrator: Generates narrative stories from results
- ErrorIntelligence: Tracks, classifies, and analyzes all errors
- QualityTracker: Monitors quality metrics across all operations

Integrated with Week 1 foundation systems:
- Configuration management
- Error recovery with retry logic
- Structured logging (info, warning, error)
- Input/output validation
- Health score calculation
- Comprehensive error classification
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
import json

import pandas as pd

from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import OrchestratorError, ValidationError
from core.error_recovery import retry_on_error
from core.validators import validate_output

from agents.error_intelligence.main import ErrorIntelligence
from agents.error_intelligence.error_record import ErrorRecord, ErrorType, ErrorSeverity

from agents.orchestrator.workers.agent_registry import AgentRegistry
from agents.orchestrator.workers.data_manager import DataManager
from agents.orchestrator.workers.task_router import TaskRouter
from agents.orchestrator.workers.workflow_executor import WorkflowExecutor
from agents.orchestrator.workers.narrative_integrator import NarrativeIntegrator


# ===== CONSTANTS =====
MIN_HEALTH_SCORE = 0.0
MAX_HEALTH_SCORE = 100.0
DEFAULT_QUALITY_THRESHOLD = 0.8
MAX_RETRIES_DEFAULT = 3
BACKOFF_MULTIPLIER_DEFAULT = 2.0
INITIAL_DELAY_SECONDS = 1.0


class TaskStatus(Enum):
    """Task execution status enumeration."""
    CREATED = "created"
    VALIDATING = "validating"
    ROUTING = "routing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class WorkflowStatus(Enum):
    """Workflow execution status enumeration."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


# ===== QUALITY TRACKING =====
class QualityScore:
    """Tracks quality metrics for operations."""
    
    def __init__(self) -> None:
        """Initialize quality tracker."""
        self.tasks_successful: int = 0
        self.tasks_failed: int = 0
        self.tasks_partial: int = 0
        self.total_rows_processed: int = 0
        self.total_rows_failed: int = 0
        self.errors_by_type: Dict[str, int] = {}
    
    def add_success(self) -> None:
        """Record successful task."""
        self.tasks_successful += 1
    
    def add_failure(self) -> None:
        """Record failed task."""
        self.tasks_failed += 1
    
    def add_partial(self) -> None:
        """Record partially successful task."""
        self.tasks_partial += 1
    
    def add_error_type(self, error_type: str) -> None:
        """Record error type occurrence."""
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
    
    def get_score(self) -> float:
        """Calculate overall quality score (0-1).
        
        Returns:
            Quality score where 1.0 = perfect
        """
        total_tasks = self.tasks_successful + self.tasks_failed + self.tasks_partial
        if total_tasks == 0:
            return 1.0
        
        # Successful = 1.0, Partial = 0.5, Failed = 0.0
        score = (
            (self.tasks_successful * 1.0 + self.tasks_partial * 0.5) / total_tasks
        )
        return round(score, 3)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get quality summary.
        
        Returns:
            Quality metrics dict
        """
        total_tasks = self.tasks_successful + self.tasks_failed + self.tasks_partial
        total_rows = self.total_rows_processed + self.total_rows_failed
        
        return {
            'quality_score': self.get_score(),
            'tasks': {
                'successful': self.tasks_successful,
                'failed': self.tasks_failed,
                'partial': self.tasks_partial,
                'total': total_tasks
            },
            'data': {
                'rows_processed': self.total_rows_processed,
                'rows_failed': self.total_rows_failed,
                'total_rows': total_rows,
                'data_loss_pct': (self.total_rows_failed / total_rows * 100) if total_rows > 0 else 0.0
            },
            'errors': {
                'by_type': self.errors_by_type,
                'total_errors': sum(self.errors_by_type.values())
            }
        }


# ===== ORCHESTRATOR =====
class OrchestratorV3:
    """Master agent that coordinates all specialized agents.
    
    Manages complete data analysis workflow with enterprise-grade
    error handling, quality tracking, and intelligent recovery.
    
    Attributes:
        name (str): Agent identifier
        version (str): Implementation version
        workers (Dict): All worker instances
        error_intelligence (ErrorIntelligence): Error tracking system
        quality_tracker (QualityScore): Quality metrics
        execution_history (List): Historical task/workflow executions
    
    Features:
    - Multi-worker architecture (separation of concerns)
    - Comprehensive error classification and tracking
    - Quality score calculation per task and overall
    - Intelligent retry with exponential backoff
    - Data caching for inter-agent communication
    - Health scoring and status reporting
    - Graceful degradation on partial failures
    - Structured logging throughout
    """

    def __init__(self) -> None:
        """Initialize Orchestrator with all workers and systems.
        
        Raises:
            OrchestratorError: If initialization fails
        """
        self.name = "OrchestratorV3"
        self.version = "3.0-enhanced"
        
        # Logging
        self.logger = get_logger("OrchestratorV3")
        self.structured_logger = get_structured_logger("OrchestratorV3")
        
        # Error Intelligence & Quality Tracking
        self.error_intelligence = ErrorIntelligence()
        self.quality_tracker = QualityScore()
        
        # Workers (core orchestration components)
        self.agent_registry = AgentRegistry()
        self.data_manager = DataManager()
        self.task_router = TaskRouter(self.agent_registry, self.data_manager)
        self.workflow_executor = WorkflowExecutor(self.task_router)
        self.narrative_integrator = NarrativeIntegrator()
        
        # State management
        self.current_task: Optional[Dict[str, Any]] = None
        self.current_workflow: Optional[Dict[str, Any]] = None
        self.execution_history: List[Dict[str, Any]] = []
        
        self.logger.info(f"OrchestratorV3 initialized (version {self.version})")
        self.structured_logger.info("Orchestrator initialized", {
            'version': self.version,
            'workers': [
                'AgentRegistry',
                'DataManager',
                'TaskRouter',
                'WorkflowExecutor',
                'NarrativeIntegrator',
                'ErrorIntelligence',
                'QualityTracker'
            ]
        })

    # ========== AGENT MANAGEMENT ==========

    @retry_on_error(max_attempts=MAX_RETRIES_DEFAULT, backoff=BACKOFF_MULTIPLIER_DEFAULT)
    def register_agent(
        self,
        agent_name: str,
        agent_instance: Any
    ) -> Dict[str, Any]:
        """Register an agent for orchestration.
        
        Args:
            agent_name: Unique identifier for agent
            agent_instance: Agent instance (must have .name attribute)
        
        Returns:
            {\n                'success': bool,
                'agent_name': str,
                'registered_at': str (ISO timestamp),
                'total_agents': int,
                'quality_score': float
            }
        
        Raises:
            OrchestratorError: If registration fails
            ValidationError: If agent instance invalid
        
        Example:
            >>> orchestrator = OrchestratorV3()
            >>> from agents.data_loader.data_loader import DataLoader
            >>> loader = DataLoader()
            >>> result = orchestrator.register_agent('data_loader', loader)
            >>> result['success']
            True
        """
        try:
            # Validate agent
            if not hasattr(agent_instance, 'name'):
                raise ValidationError(
                    f"Agent must have 'name' attribute; {agent_name} missing it"
                )
            
            self.logger.info(f"Registering agent: {agent_name}")
            
            # Register via worker
            self.agent_registry.register(agent_name, agent_instance)
            
            # Track success
            self.quality_tracker.add_success()
            self.error_intelligence.track_success(
                agent_name=self.name,
                worker_name="Orchestrator",
                operation="register_agent",
                context={
                    "agent_name": agent_name,
                    "total_agents": self.agent_registry.get_count()
                }
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
            
            # Track error
            error_record = ErrorRecord(
                error_type=ErrorType.AGENT_LIFECYCLE_ERROR,
                severity=ErrorSeverity.HIGH,
                worker_name="Orchestrator",
                message=f"Agent registration failed for '{agent_name}': {str(e)}",
                context={"agent_name": agent_name}
            )
            self.error_intelligence.record_error(error_record)
            
            raise OrchestratorError(
                f"Failed to register agent '{agent_name}': {str(e)}"
            )

    @retry_on_error(max_attempts=2, backoff=1)
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Retrieve registered agent.
        
        Args:
            agent_name: Name of agent
        
        Returns:
            Agent instance or None
        """
        return self.agent_registry.get(agent_name)

    @retry_on_error(max_attempts=2, backoff=1)
    def list_agents(self) -> Dict[str, Any]:
        """List all registered agents with summary.
        
        Returns:
            {\n                'agents': List[str],
                'total': int,
                'timestamp': str
            }
        """
        agents = self.agent_registry.list_all()
        return {
            'agents': agents,
            'total': len(agents),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    # ========== DATA MANAGEMENT ==========

    @retry_on_error(max_attempts=2, backoff=1)
    def cache_data(self, key: str, data: Any) -> Dict[str, Any]:
        """Cache data for inter-agent sharing.
        
        Args:
            key: Cache key
            data: Data to cache
        
        Returns:
            {\n                'success': bool,
                'key': str,
                'cached_at': str,
                'cache_size': int
            }
        """
        self.data_manager.set(key, data)
        return {
            'success': True,
            'key': key,
            'cached_at': datetime.now(timezone.utc).isoformat(),
            'cache_size': self.data_manager.get_count()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data.
        
        Args:
            key: Cache key
        
        Returns:
            Cached data or None
        """
        return self.data_manager.get(key)

    @retry_on_error(max_attempts=2, backoff=1)
    def list_cached_data(self) -> Dict[str, Any]:
        """List all cached data.
        
        Returns:
            {'keys': List[str], 'count': int}
        """
        return {
            'keys': self.data_manager.list_keys(),
            'count': self.data_manager.get_count(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    def clear_cache(self) -> Dict[str, Any]:
        """Clear all cached data.
        
        Returns:
            {'success': bool, 'cleared_at': str}
        """
        self.data_manager.clear()
        self.logger.info("Cache cleared")
        return {
            'success': True,
            'cleared_at': datetime.now(timezone.utc).isoformat()
        }

    # ========== TASK EXECUTION ==========

    @retry_on_error(max_attempts=MAX_RETRIES_DEFAULT, backoff=BACKOFF_MULTIPLIER_DEFAULT)
    @validate_output('dict')
    def execute_task(
        self,
        task_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a single task with full error handling and quality tracking.
        
        Args:
            task_type: Task identifier (load_data, explore_data, etc.)
            parameters: Task-specific parameters (default: {})
        
        Returns:
            {\n                'task_id': str,
                'status': str,  # created, validating, executing, completed, failed
                'task_type': str,
                'result': Any,  # Task output
                'quality_score': float,  # 0-1
                'duration_seconds': float,
                'errors': List[Dict],  # Error details
                'warnings': List[str],
                'metadata': {...}
            }
        
        Raises:
            OrchestratorError: If task execution fails
            ValidationError: If parameters invalid
        
        Example:
            >>> result = orchestrator.execute_task(
            ...     'load_data',
            ...     {'file_path': '/path/to/data.csv'}
            ... )
            >>> if result['status'] == 'completed':
            ...     print(f"Quality: {result['quality_score']}")
        """
        task_start = datetime.now(timezone.utc)
        
        # Create task record
        task_id = f"task_{task_start.timestamp()}"
        task = {
            'id': task_id,
            'type': task_type,
            'parameters': parameters if parameters else {},
            'status': TaskStatus.CREATED.value,
            'created_at': task_start.isoformat(),
            'errors': [],
            'warnings': [],
            'rows_processed': 0,
            'rows_failed': 0
        }
        
        self.current_task = task
        self.logger.info(f"Task created: {task_id} (type: {task_type})")
        
        try:
            # Validate task
            task['status'] = TaskStatus.VALIDATING.value
            self._validate_task(task)
            
            # Route and execute
            task['status'] = TaskStatus.ROUTING.value
            self.logger.info(f"Routing task: {task_type}")
            
            task['status'] = TaskStatus.EXECUTING.value
            result = self.task_router.route(task)
            
            # Update task with result
            task['status'] = TaskStatus.COMPLETED.value
            task['result'] = result
            task['quality_score'] = self._extract_quality_score(result)
            
            # Track success
            self.quality_tracker.add_success()
            self.error_intelligence.track_success(
                agent_name=self.name,
                worker_name="Orchestrator",
                operation="execute_task",
                context={
                    "task_type": task_type,
                    "quality_score": task['quality_score']
                }
            )
            
            self.logger.info(
                f"Task completed: {task_id} "
                f"(quality: {task['quality_score']:.2%})"
            )
        
        except Exception as e:
            task['status'] = TaskStatus.FAILED.value
            task['error'] = str(e)
            
            # Track failure
            self.quality_tracker.add_failure()
            
            error_record = ErrorRecord(
                error_type=ErrorType.TASK_EXECUTION_ERROR,
                severity=ErrorSeverity.HIGH,
                worker_name="Orchestrator",
                message=f"Task execution failed: {str(e)}",
                context={"task_type": task_type, "task_id": task_id}
            )
            self.error_intelligence.record_error(error_record)
            
            self.logger.error(f"Task failed: {task_id} - {e}")
            raise OrchestratorError(f"Task execution failed: {str(e)}")
        
        finally:
            # Calculate duration
            task_end = datetime.now(timezone.utc)
            task['duration_seconds'] = (
                (task_end - task_start).total_seconds()
            )
            task['executed_at'] = task_end.isoformat()
            
            # Add to history
            self.execution_history.append(task)
        
        return task

    def _validate_task(self, task: Dict[str, Any]) -> None:
        """Validate task configuration.
        
        Args:
            task: Task dict
        
        Raises:
            ValidationError: If validation fails
        """
        if not task.get('type'):
            raise ValidationError("Task must have 'type' field")
        
        # Validate required agents exist
        required_agents = self._get_required_agents(task['type'])
        for agent_name in required_agents:
            if not self.agent_registry.is_registered(agent_name):
                raise ValidationError(
                    f"Required agent '{agent_name}' not registered "
                    f"for task type '{task['type']}'"
                )

    def _get_required_agents(self, task_type: str) -> List[str]:
        """Get required agents for task type.
        
        Args:
            task_type: Type of task
        
        Returns:
            List of required agent names
        """
        task_requirements = {
            'load_data': ['data_loader'],
            'explore_data': ['explorer', 'data_loader'],
            'aggregate_data': ['aggregator', 'data_loader'],
            'detect_anomalies': ['anomaly_detector', 'data_loader'],
            'predict': ['predictor', 'data_loader'],
            'get_recommendations': ['recommender', 'data_loader'],
            'visualize_data': ['visualizer', 'data_loader'],
            'generate_report': ['reporter', 'data_loader']
        }
        return task_requirements.get(task_type, [])

    def _extract_quality_score(self, result: Any) -> float:
        """Extract quality score from result.
        
        Args:
            result: Task result
        
        Returns:
            Quality score (0-1) or 1.0 if not found
        """
        if isinstance(result, dict):
            return float(result.get('quality_score', 1.0))
        return 1.0

    # ========== WORKFLOW EXECUTION ==========

    @retry_on_error(max_attempts=MAX_RETRIES_DEFAULT, backoff=BACKOFF_MULTIPLIER_DEFAULT)
    @validate_output('dict')
    def execute_workflow(
        self,
        workflow_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a workflow (sequence of tasks).
        
        Args:
            workflow_tasks: List of task configs with:
                - type: str (task type)
                - parameters: Dict (optional)
        
        Returns:
            {\n                'workflow_id': str,
                'status': str,  # completed, failed, partially_completed
                'total_tasks': int,
                'completed_tasks': int,
                'failed_tasks': int,
                'results': Dict[str, Any],  # keyed by task ID
                'quality_score': float,  # overall
                'duration_seconds': float,
                'errors': List[Dict],
                'warnings': List[str]
            }
        
        Raises:
            OrchestratorError: If workflow execution fails
        
        Example:
            >>> workflow = [
            ...     {'type': 'load_data', 'parameters': {'file_path': '...'}},
            ...     {'type': 'explore_data', 'parameters': {}},
            ...     {'type': 'detect_anomalies', 'parameters': {'column': 'value'}}
            ... ]
            >>> result = orchestrator.execute_workflow(workflow)
            >>> result['quality_score']
            0.95
        """
        workflow_start = datetime.now(timezone.utc)
        workflow_id = f"workflow_{workflow_start.timestamp()}"
        
        workflow = {
            'id': workflow_id,
            'status': WorkflowStatus.CREATED.value,
            'created_at': workflow_start.isoformat(),
            'total_tasks': len(workflow_tasks),
            'completed_tasks': 0,
            'failed_tasks': 0,
            'results': {},
            'errors': [],
            'warnings': [],
            'task_results': []
        }
        
        self.current_workflow = workflow
        self.logger.info(
            f"Workflow started: {workflow_id} "
            f"({len(workflow_tasks)} tasks)"
        )
        
        try:
            workflow['status'] = WorkflowStatus.RUNNING.value
            
            # Execute each task in sequence
            for idx, task_config in enumerate(workflow_tasks):
                task_type = task_config.get('type')
                params = task_config.get('parameters', {})
                
                self.logger.info(
                    f"Executing task {idx+1}/{len(workflow_tasks)}: {task_type}"
                )
                
                try:
                    task_result = self.execute_task(task_type, params)
                    
                    workflow['results'][task_result['id']] = task_result
                    workflow['task_results'].append(task_result)
                    workflow['completed_tasks'] += 1
                    
                except Exception as e:
                    self.logger.warning(
                        f"Task {idx+1} failed: {task_type} - {e}"
                    )
                    workflow['failed_tasks'] += 1
                    workflow['errors'].append({
                        'task_index': idx,
                        'task_type': task_type,
                        'error': str(e)
                    })
            
            # Determine workflow status
            if workflow['failed_tasks'] == 0:
                workflow['status'] = WorkflowStatus.COMPLETED.value
            elif workflow['completed_tasks'] > 0:
                workflow['status'] = WorkflowStatus.PARTIALLY_COMPLETED.value
            else:
                workflow['status'] = WorkflowStatus.FAILED.value
            
            # Calculate overall quality
            if workflow['task_results']:
                scores = [
                    t.get('quality_score', 1.0)
                    for t in workflow['task_results']
                ]
                workflow['quality_score'] = round(sum(scores) / len(scores), 3)
            else:
                workflow['quality_score'] = 0.0
            
            self.logger.info(
                f"Workflow completed: {workflow_id} "
                f"({workflow['completed_tasks']}/{workflow['total_tasks']} succeeded, "
                f"quality: {workflow['quality_score']:.2%})"
            )
            
            # Track success/partial
            if workflow['failed_tasks'] == 0:
                self.quality_tracker.add_success()
            else:
                self.quality_tracker.add_partial()
            
            return workflow
        
        except Exception as e:
            workflow['status'] = WorkflowStatus.FAILED.value
            workflow['fatal_error'] = str(e)
            
            self.quality_tracker.add_failure()
            
            error_record = ErrorRecord(
                error_type=ErrorType.WORKFLOW_EXECUTION_ERROR,
                severity=ErrorSeverity.CRITICAL,
                worker_name="Orchestrator",
                message=f"Workflow execution failed: {str(e)}",
                context={"workflow_id": workflow_id, "total_tasks": len(workflow_tasks)}
            )
            self.error_intelligence.record_error(error_record)
            
            self.logger.error(f"Workflow failed: {workflow_id} - {e}")
            raise OrchestratorError(f"Workflow execution failed: {str(e)}")
        
        finally:
            workflow_end = datetime.now(timezone.utc)
            workflow['duration_seconds'] = (
                (workflow_end - workflow_start).total_seconds()
            )
            workflow['executed_at'] = workflow_end.isoformat()
            self.execution_history.append(workflow)

    # ========== NARRATIVE GENERATION ==========

    @retry_on_error(max_attempts=MAX_RETRIES_DEFAULT, backoff=BACKOFF_MULTIPLIER_DEFAULT)
    @validate_output('dict')
    def generate_narrative(
        self,
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate narrative story from agent results.
        
        Converts raw analytical output into an empathetic narrative
        that explains what the data means and what to do.
        
        Args:
            agent_results: Dictionary of agent outputs
        
        Returns:
            {\n                'success': bool,
                'narrative': str,  # The story
                'key_insights': List[str],
                'recommendations': List[str],
                'confidence': float,
                'generated_at': str
            }
        
        Raises:
            OrchestratorError: If narrative generation fails
        """
        try:
            self.logger.info("Generating narrative from results")
            
            result = self.narrative_integrator.generate_narrative_from_results(
                agent_results
            )
            
            self.quality_tracker.add_success()
            self.error_intelligence.track_success(
                agent_name=self.name,
                worker_name="Orchestrator",
                operation="generate_narrative",
                context={"result_count": len(agent_results)}
            )
            
            return result
        
        except Exception as e:
            self.quality_tracker.add_failure()
            
            error_record = ErrorRecord(
                error_type=ErrorType.NARRATIVE_GENERATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                worker_name="Orchestrator",
                message=f"Narrative generation failed: {str(e)}",
                context={"result_count": len(agent_results)}
            )
            self.error_intelligence.record_error(error_record)
            
            self.logger.error(f"Narrative generation failed: {e}")
            raise OrchestratorError(f"Narrative generation failed: {str(e)}")

    @retry_on_error(max_attempts=MAX_RETRIES_DEFAULT, backoff=BACKOFF_MULTIPLIER_DEFAULT)
    @validate_output('dict')
    def execute_workflow_with_narrative(
        self,
        workflow_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute complete pipeline: workflow → narrative.
        
        Runs all tasks, collects results, generates narrative story.
        
        Args:
            workflow_tasks: Workflow task list
        
        Returns:
            {\n                'workflow_id': str,
                'workflow_results': {...},  # Workflow result
                'narrative': {...},  # Narrative result
                'quality_score': float,  # Overall
                'duration_seconds': float
            }
        
        Raises:
            OrchestratorError: If execution fails
        
        Example:
            >>> result = orchestrator.execute_workflow_with_narrative(workflow)
            >>> print(result['narrative']['narrative'])
        """
        pipeline_start = datetime.now(timezone.utc)
        pipeline_id = f"pipeline_{pipeline_start.timestamp()}"
        
        self.logger.info(f"Full pipeline started: {pipeline_id}")
        
        try:
            # Execute workflow
            self.logger.info("Step 1: Executing workflow")
            workflow_result = self.execute_workflow(workflow_tasks)
            
            # Extract results for narrative
            agent_results = {}
            for task_id, task_result in workflow_result.get('results', {}).items():
                if task_result.get('status') == 'completed':
                    agent_results[task_id] = task_result.get('result')
            
            # Generate narrative
            self.logger.info("Step 2: Generating narrative")
            narrative_result = self.generate_narrative(agent_results)
            
            # Combine results
            pipeline_end = datetime.now(timezone.utc)
            combined_result = {
                'pipeline_id': pipeline_id,
                'workflow_id': workflow_result['id'],
                'workflow_results': workflow_result,
                'narrative': narrative_result,
                'overall_quality_score': workflow_result.get('quality_score', 0.0),
                'duration_seconds': (
                    (pipeline_end - pipeline_start).total_seconds()
                ),
                'executed_at': pipeline_end.isoformat()
            }
            
            self.logger.info(f"Full pipeline completed: {pipeline_id}")
            self.quality_tracker.add_success()
            
            return combined_result
        
        except Exception as e:
            self.quality_tracker.add_failure()
            
            error_record = ErrorRecord(
                error_type=ErrorType.WORKFLOW_EXECUTION_ERROR,
                severity=ErrorSeverity.CRITICAL,
                worker_name="Orchestrator",
                message=f"Full pipeline failed: {str(e)}",
                context={"pipeline_id": pipeline_id}
            )
            self.error_intelligence.record_error(error_record)
            
            self.logger.error(f"Full pipeline failed: {e}")
            raise OrchestratorError(f"Full pipeline failed: {str(e)}")

    # ========== STATUS & HEALTH ==========

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report.
        
        Returns:
            {\n                'overall_health': float,  # 0-100 score
                'status': str,  # healthy, degraded, critical
                'agents': {...},  # Agent status
                'cache': {...},  # Cache status
                'execution': {...},  # Execution stats
                'errors': {...},  # Error intelligence
                'quality': {...}  # Quality metrics
            }
        """
        health_score = self._calculate_health_score()
        
        return {
            'overall_health': health_score,
            'status': self._get_health_status(health_score),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'agents': self.agent_registry.get_summary(),
            'cache': self.data_manager.get_summary(),
            'execution': {
                'current_task': self.current_task['type'] if self.current_task else None,
                'current_workflow': self.current_workflow['id'] if self.current_workflow else None,
                'total_executed': len(self.execution_history)
            },
            'errors': self.error_intelligence.get_summary(),
            'quality': self.quality_tracker.get_summary()
        }

    def _calculate_health_score(self) -> float:
        """Calculate overall health score (0-100).
        
        Returns:
            Health score
        """
        quality = self.quality_tracker.get_score() * 100  # 0-100
        
        # Adjust based on error count
        error_summary = self.error_intelligence.get_summary()
        total_errors = error_summary.get('total_errors', 0)
        error_penalty = min(total_errors * 5, 30)  # Max 30 point penalty
        
        health = quality - error_penalty
        return max(MIN_HEALTH_SCORE, min(health, MAX_HEALTH_SCORE))

    def _get_health_status(self, health_score: float) -> str:
        """Get health status label.
        
        Args:
            health_score: Health score (0-100)
        
        Returns:
            Status string
        """
        if health_score >= 80:
            return "healthy"
        elif health_score >= 50:
            return "degraded"
        else:
            return "critical"

    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def get_status(self) -> Dict[str, Any]:
        """Get quick status.
        
        Returns:
            Quick status dict
        """
        return {
            'name': self.name,
            'version': self.version,
            'status': 'active',
            'health_score': self._calculate_health_score(),
            'agents_registered': self.agent_registry.get_count(),
            'cache_items': self.data_manager.get_count(),
            'quality_score': self.quality_tracker.get_score(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    # ========== EXECUTION HISTORY & CLEANUP ==========

    @retry_on_error(max_attempts=2, backoff=1)
    def get_execution_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get execution history.
        
        Args:
            limit: Max number of records (default: all)
        
        Returns:
            List of execution records
        """
        history = self.execution_history
        if limit:
            history = history[-limit:]
        return history

    @retry_on_error(max_attempts=2, backoff=1)
    def clear_history(self) -> Dict[str, Any]:
        """Clear execution history.
        
        Returns:
            {'success': bool, 'cleared_count': int, 'cleared_at': str}
        """
        count = len(self.execution_history)
        self.execution_history.clear()
        self.logger.info(f"Execution history cleared ({count} records)")
        return {
            'success': True,
            'cleared_count': count,
            'cleared_at': datetime.now(timezone.utc).isoformat()
        }

    @retry_on_error(max_attempts=2, backoff=1)
    def reset(self) -> Dict[str, Any]:
        """Reset orchestrator (keep agents, clear data and history).
        
        Returns:
            {'success': bool, 'reset_at': str}
        """
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
        """Shutdown orchestrator (cleanup all resources).
        
        Returns:
            {'success': bool, 'shutdown_at': str, 'final_health': float}
        """
        final_health = self._calculate_health_score()
        
        self.reset()
        self.logger.info(
            f"Orchestrator shutdown (final health: {final_health:.1f})"
        )
        return {
            'success': True,
            'shutdown_at': datetime.now(timezone.utc).isoformat(),
            'final_health_score': final_health,
            'total_tasks_executed': len(self.execution_history)
        }
