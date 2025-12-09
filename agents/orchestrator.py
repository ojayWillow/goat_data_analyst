"""Orchestrator Agent - Master coordinator for all other agents.

Integrated with Week 1 foundation systems:
- Configuration management
- Error recovery with retry logic
- Structured logging
- Input/output validation

Manages all agents, routes tasks, handles communication between agents,
and maintains workflow state.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import pandas as pd

# Week 1 Integrations
from agents.agent_config import AgentConfig
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.validators import validate_input, validate_output

# Existing imports
from core.logger import get_logger
from core.exceptions import OrchestratorError

logger = get_structured_logger(__name__)
config = AgentConfig()


class Orchestrator:
    """Master agent that coordinates all other specialized agents.
    
    Responsibilities:
    - Manage agent lifecycle and communication
    - Route tasks to appropriate agents
    - Enable inter-agent communication
    - Aggregate results from multiple agents
    - Handle error management and retries
    - Maintain workflow state
    
    Integrated with Week 1 systems:
    - Centralized configuration
    - Error recovery on all operations
    - Structured logging of all activities
    - Input/output validation
    """
    
    def __init__(self):
        """Initialize the Orchestrator with Week 1 systems."""
        self.name = "Orchestrator"
        self.config = AgentConfig()
        self.agents = {}  # Registry of available agents
        self.workflow_history = []
        self.current_task = None
        self.data_cache = {}  # Shared data between agents
        logger.info(f"{self.name} initialized", extra={'version': '2.0-week1-integrated'})
    
    @retry_on_error(max_attempts=2, backoff=1)
    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """Register a new agent with error recovery.
        
        Args:
            agent_name: Unique name for the agent
            agent_instance: Agent instance
            
        Raises:
            OrchestratorError: If agent registration fails
        """
        with logger.operation('register_agent', {'agent_name': agent_name}):
            try:
                if agent_name in self.agents:
                    raise OrchestratorError(f"Agent '{agent_name}' already registered")
                
                self.agents[agent_name] = agent_instance
                logger.info(
                    'Agent registered',
                    extra={'agent_name': agent_name, 'total_agents': len(self.agents)}
                )
            except Exception as e:
                logger.error(
                    'Agent registration failed',
                    extra={'agent_name': agent_name, 'error': str(e)},
                    exc_info=True
                )
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
    
    def cache_data(self, key: str, data: Any) -> None:
        """Cache data for sharing between agents.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        with logger.operation('cache_data', {'key': key}):
            self.data_cache[key] = data
            logger.info(
                'Data cached',
                extra={'key': key, 'total_cached': len(self.data_cache)}
            )
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None
        """
        return self.data_cache.get(key)
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def create_task(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create and route a task to appropriate agent(s) with error recovery.
        
        Args:
            task_type: Type of task (data_load, explore, visualize, etc.)
            parameters: Task parameters
            
        Returns:
            Task metadata and status (validated)
            
        Raises:
            OrchestratorError: If task creation fails
        """
        with logger.operation('create_task', {'task_type': task_type, 'params_count': len(parameters)}):
            try:
                task = {
                    "id": self._generate_task_id(),
                    "type": task_type,
                    "parameters": parameters,
                    "status": "created",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "result": None,
                    "error": None,
                }
                
                self.current_task = task
                self.workflow_history.append(task)
                logger.info(
                    'Task created',
                    extra={'task_id': task["id"], 'task_type': task_type}
                )
                return task
            except Exception as e:
                logger.error(
                    'Task creation failed',
                    extra={'task_type': task_type, 'error': str(e)},
                    exc_info=True
                )
                raise OrchestratorError(f"Task creation failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a task (route to appropriate agent(s)) with error recovery.
        
        Args:
            task_id: ID of task to execute
            
        Returns:
            Task result (validated)
            
        Raises:
            OrchestratorError: If execution fails
        """
        with logger.operation('execute_task', {'task_id': task_id}):
            try:
                task = self._get_task(task_id)
                if not task:
                    raise OrchestratorError(f"Task {task_id} not found")
                
                task["status"] = "executing"
                task["started_at"] = datetime.now(timezone.utc).isoformat()
                
                logger.info('Task execution started', extra={'task_type': task['type']})
                
                # Route to appropriate agent based on task type
                result = self._route_task(task)
                
                task["status"] = "completed"
                task["result"] = result
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                logger.info(
                    'Task execution completed',
                    extra={'task_id': task_id, 'duration': 'logged'}
                )
                return task
            except Exception as e:
                logger.error(
                    'Task execution failed',
                    extra={'task_id': task_id, 'error': str(e)},
                    exc_info=True
                )
                task["status"] = "failed"
                task["error"] = str(e)
                raise OrchestratorError(f"Task execution failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def execute_workflow(self, workflow_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a complete workflow with multiple tasks with error recovery.
        
        Args:
            workflow_tasks: List of tasks to execute in sequence
            
        Returns:
            Workflow results (validated)
        """
        with logger.operation('execute_workflow', {'task_count': len(workflow_tasks)}):
            try:
                workflow_id = f"workflow_{len(self.workflow_history):05d}"
                workflow_results = {
                    "workflow_id": workflow_id,
                    "status": "executing",
                    "tasks": [],
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
                
                logger.info(
                    'Workflow started',
                    extra={'workflow_id': workflow_id, 'total_tasks': len(workflow_tasks)}
                )
                
                for i, task_config in enumerate(workflow_tasks):
                    logger.info(
                        'Executing workflow task',
                        extra={'task_number': i + 1, 'total': len(workflow_tasks), 'type': task_config['type']}
                    )
                    
                    task = self.create_task(task_config["type"], task_config.get("parameters", {}))
                    task_result = self.execute_task(task["id"])
                    workflow_results["tasks"].append(task_result)
                    
                    # Cache result for next task if needed
                    if "cache_as" in task_config:
                        self.cache_data(task_config["cache_as"], task_result.get("result"))
                        logger.info(
                            'Workflow task result cached',
                            extra={'cache_key': task_config["cache_as"]}
                        )
                
                workflow_results["status"] = "completed"
                workflow_results["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                logger.info(
                    'Workflow completed successfully',
                    extra={'workflow_id': workflow_id}
                )
                return workflow_results
            
            except Exception as e:
                logger.error(
                    'Workflow execution failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise OrchestratorError(f"Workflow failed: {e}")
    
    def _route_task(self, task: Dict[str, Any]) -> Any:
        """Route task to appropriate agent(s).
        
        Args:
            task: Task to route
            
        Returns:
            Task result from agent
            
        Raises:
            OrchestratorError: If routing fails
        """
        task_type = task["type"]
        params = task["parameters"]
        
        with logger.operation('_route_task', {'task_type': task_type}):
            try:
                # Data Loading Tasks
                if task_type == "load_data":
                    agent = self.get_agent("data_loader")
                    if not agent:
                        raise OrchestratorError("DataLoader agent not registered")
                    result = agent.load(params.get("file_path"))
                    if result["status"] == "success":
                        self.cache_data("loaded_data", result["data"])
                    return result
                
                # Exploration Tasks
                elif task_type == "explore_data":
                    agent = self.get_agent("explorer")
                    if not agent:
                        raise OrchestratorError("Explorer agent not registered")
                    
                    data = self._get_data_for_task(params)
                    agent.set_data(data)
                    return agent.get_summary_report()
                
                # Aggregation Tasks
                elif task_type == "aggregate_data":
                    agent = self.get_agent("aggregator")
                    if not agent:
                        raise OrchestratorError("Aggregator agent not registered")
                    
                    data = self._get_data_for_task(params)
                    agent.set_data(data)
                    
                    if "group_by" in params:
                        return agent.groupby_single(
                            params["group_by"],
                            params.get("agg_col"),
                            params.get("agg_func", "sum")
                        )
                    return {"status": "error", "message": "Missing required parameters"}
                
                # Visualization Tasks
                elif task_type == "visualize_data":
                    agent = self.get_agent("visualizer")
                    if not agent:
                        raise OrchestratorError("Visualizer agent not registered")
                    
                    data = self._get_data_for_task(params)
                    agent.set_data(data)
                    
                    chart_type = params.get("chart_type", "line")
                    if chart_type == "histogram":
                        return agent.histogram(params.get("column"), params.get("bins", 30))
                    elif chart_type == "bar":
                        return agent.bar_chart(params.get("x_col"), params.get("y_col"))
                    elif chart_type == "scatter":
                        return agent.scatter_plot(params.get("x_col"), params.get("y_col"))
                    elif chart_type == "heatmap":
                        return agent.heatmap()
                    return {"status": "error", "message": f"Unknown chart type: {chart_type}"}
                
                # Prediction Tasks
                elif task_type == "predict":
                    agent = self.get_agent("predictor")
                    if not agent:
                        raise OrchestratorError("Predictor agent not registered")
                    
                    data = self._get_data_for_task(params)
                    agent.set_data(data)
                    
                    pred_type = params.get("prediction_type", "trend")
                    if pred_type == "trend":
                        return agent.trend_analysis(params.get("column"))
                    elif pred_type == "forecast":
                        return agent.linear_regression_forecast(
                            params.get("x_col"),
                            params.get("y_col"),
                            params.get("periods", 10)
                        )
                    return {"status": "error", "message": f"Unknown prediction type: {pred_type}"}
                
                # Anomaly Detection Tasks
                elif task_type == "detect_anomalies":
                    agent = self.get_agent("anomaly_detector")
                    if not agent:
                        raise OrchestratorError("AnomalyDetector agent not registered")
                    
                    data = self._get_data_for_task(params)
                    agent.set_data(data)
                    
                    method = params.get("method", "iqr")
                    if method == "iqr":
                        return agent.iqr_detection(params.get("column"), params.get("multiplier", 1.5))
                    elif method == "zscore":
                        return agent.zscore_detection(params.get("column"), params.get("threshold", 3.0))
                    elif method == "isolation_forest":
                        return agent.isolation_forest_detection(params.get("columns", []))
                    return {"status": "error", "message": f"Unknown method: {method}"}
                
                # Recommendation Tasks
                elif task_type == "get_recommendations":
                    agent = self.get_agent("recommender")
                    if not agent:
                        raise OrchestratorError("Recommender agent not registered")
                    
                    data = self._get_data_for_task(params)
                    agent.set_data(data)
                    
                    return agent.generate_action_plan()
                
                # Report Generation Tasks
                elif task_type == "generate_report":
                    agent = self.get_agent("reporter")
                    if not agent:
                        raise OrchestratorError("Reporter agent not registered")
                    
                    data = self._get_data_for_task(params)
                    agent.set_data(data)
                    
                    report_type = params.get("report_type", "executive_summary")
                    if report_type == "executive_summary":
                        return agent.generate_executive_summary()
                    elif report_type == "data_profile":
                        return agent.generate_data_profile()
                    elif report_type == "comprehensive":
                        return agent.generate_comprehensive_report()
                    return {"status": "error", "message": f"Unknown report type: {report_type}"}
                
                else:
                    raise OrchestratorError(f"Unknown task type: {task_type}")
            
            except Exception as e:
                logger.error(
                    'Task routing failed',
                    extra={'task_type': task_type, 'error': str(e)},
                    exc_info=True
                )
                raise OrchestratorError(f"Routing failed: {e}")
    
    def _get_data_for_task(self, params: Dict[str, Any]) -> pd.DataFrame:
        """Get data for task execution.
        
        Priority: provided data > cached data > load from file
        
        Args:
            params: Task parameters
            
        Returns:
            DataFrame
            
        Raises:
            OrchestratorError: If no data available
        """
        # Check if data provided directly
        if "data" in params and isinstance(params["data"], pd.DataFrame):
            return params["data"]
        
        # Check if data cached
        if "data_key" in params:
            cached = self.get_cached_data(params["data_key"])
            if cached is not None and isinstance(cached, pd.DataFrame):
                return cached
        
        # Check for default cached data
        cached = self.get_cached_data("loaded_data")
        if cached is not None and isinstance(cached, pd.DataFrame):
            return cached
        
        # Try to load from file
        if "file_path" in params:
            loader = self.get_agent("data_loader")
            if loader:
                result = loader.load(params["file_path"])
                if result["status"] == "success":
                    return result["data"]
        
        raise OrchestratorError("No data available for task execution")
    
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
    
    @validate_output('dict')
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status with validation.
        
        Returns:
            Workflow status including all tasks (validated)
        """
        return {
            "status": "active",
            "total_tasks": len(self.workflow_history),
            "current_task": self.current_task["id"] if self.current_task else None,
            "registered_agents": self.list_agents(),
            "cached_data_keys": list(self.data_cache.keys()),
            "tasks_summary": {
                "total": len(self.workflow_history),
                "completed": len([t for t in self.workflow_history if t["status"] == "completed"]),
                "failed": len([t for t in self.workflow_history if t["status"] == "failed"]),
                "executing": len([t for t in self.workflow_history if t["status"] == "executing"]),
            },
        }
