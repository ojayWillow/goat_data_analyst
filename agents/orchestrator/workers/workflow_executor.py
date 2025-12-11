"""WorkflowExecutor Worker - Executes multi-task workflows.

Responsibilities:
- Execute sequences of tasks
- Handle task dependencies
- Manage workflow state
- Track task progress
- Handle workflow-level errors
"""

from typing import Any, Dict, List
from datetime import datetime, timezone
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import OrchestratorError
from core.error_recovery import retry_on_error


class WorkflowExecutor:
    """Executes workflows (sequences of tasks).
    
    Manages task execution order, tracks progress, handles
    dependencies, and aggregates results.
    """

    def __init__(self, task_router: Any) -> None:
        """Initialize the WorkflowExecutor.
        
        Args:
            task_router: TaskRouter instance
        """
        self.name = "WorkflowExecutor"
        self.logger = get_logger("WorkflowExecutor")
        self.structured_logger = get_structured_logger("WorkflowExecutor")
        self.task_router = task_router
        self.workflow_history = []
        self.logger.info("WorkflowExecutor initialized")

    @retry_on_error(max_attempts=2, backoff=1)
    def execute(self, workflow_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a workflow (sequence of tasks).
        
        Args:
            workflow_tasks: List of task configs to execute in sequence
        
        Returns:
            Workflow result with all task results
        
        Raises:
            OrchestratorError: If workflow execution fails
        """
        workflow_id = self._generate_workflow_id()
        
        workflow = {
            'workflow_id': workflow_id,
            'status': 'executing',
            'task_count': len(workflow_tasks),
            'tasks': [],
            'started_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': None,
            'error': None
        }
        
        self.logger.info(f"Workflow started: {workflow_id}")
        self.structured_logger.info("Workflow execution started", {
            'workflow_id': workflow_id,
            'total_tasks': len(workflow_tasks)
        })
        
        try:
            for i, task_config in enumerate(workflow_tasks, 1):
                self.logger.info(f"Executing task {i}/{len(workflow_tasks)}: {task_config['type']}")
                
                # Create task
                task = self._create_task(task_config, i, len(workflow_tasks))
                
                # Execute task
                try:
                    task_result = self.task_router.route(task)
                    task['result'] = task_result
                    task['status'] = 'completed'
                except Exception as e:
                    task['status'] = 'failed'
                    task['error'] = str(e)
                    self.logger.error(f"Task failed: {e}")
                    
                    # Check if task is critical (fail-fast)
                    if task_config.get('critical', False):
                        workflow['status'] = 'failed'
                        workflow['error'] = f"Critical task failed: {e}"
                        raise OrchestratorError(f"Critical task failed: {e}")
                
                task['completed_at'] = datetime.now(timezone.utc).isoformat()
                workflow['tasks'].append(task)
                
                self.structured_logger.info("Task completed", {
                    'task_number': i,
                    'task_type': task_config['type'],
                    'status': task['status']
                })
            
            # Workflow completed successfully
            workflow['status'] = 'completed'
            workflow['completed_at'] = datetime.now(timezone.utc).isoformat()
            
            self.logger.info(f"Workflow completed: {workflow_id}")
            self.structured_logger.info("Workflow execution completed", {
                'workflow_id': workflow_id,
                'total_tasks': len(workflow_tasks),
                'successful_tasks': len([t for t in workflow['tasks'] if t['status'] == 'completed'])
            })
            
            self.workflow_history.append(workflow)
            return workflow
        
        except Exception as e:
            workflow['status'] = 'failed'
            workflow['completed_at'] = datetime.now(timezone.utc).isoformat()
            workflow['error'] = str(e)
            
            self.logger.error(f"Workflow failed: {e}")
            self.workflow_history.append(workflow)
            
            raise OrchestratorError(f"Workflow execution failed: {e}")

    def _create_task(self, task_config: Dict[str, Any], task_number: int, total_tasks: int) -> Dict[str, Any]:
        """Create a task from config.
        
        Args:
            task_config: Task configuration dict
            task_number: Current task number
            total_tasks: Total tasks in workflow
        
        Returns:
            Task dict
        """
        task_id = f"task_{len(self.workflow_history):05d}_{task_number:02d}"
        
        return {
            'id': task_id,
            'type': task_config['type'],
            'parameters': task_config.get('parameters', {}),
            'cache_as': task_config.get('cache_as'),
            'critical': task_config.get('critical', False),
            'status': 'created',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': None,
            'result': None,
            'error': None
        }

    def _generate_workflow_id(self) -> str:
        """Generate unique workflow ID.
        
        Returns:
            Unique workflow ID
        """
        return f"workflow_{len(self.workflow_history) + 1:05d}"

    def get_workflow(self, workflow_id: str) -> Dict[str, Any] | None:
        """Retrieve a workflow from history.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow dict or None if not found
        """
        for workflow in self.workflow_history:
            if workflow['workflow_id'] == workflow_id:
                return workflow
        return None

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all executed workflows.
        
        Returns:
            List of workflow dicts
        """
        return self.workflow_history

    def get_summary(self) -> Dict[str, Any]:
        """Get workflow execution summary.
        
        Returns:
            Summary dict with statistics
        """
        total = len(self.workflow_history)
        completed = len([w for w in self.workflow_history if w['status'] == 'completed'])
        failed = len([w for w in self.workflow_history if w['status'] == 'failed'])
        
        return {
            'total_workflows': total,
            'completed': completed,
            'failed': failed,
            'success_rate': f"{(completed/total*100):.1f}%" if total > 0 else "N/A"
        }
