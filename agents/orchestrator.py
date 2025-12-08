"""Orchestrator Agent - Master coordinator for all other agents.

Manages all agents, routes tasks, handles communication between agents,
and maintains workflow state.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import pandas as pd

from core.logger import get_logger
from core.exceptions import OrchestratorError

logger = get_logger(__name__)


class Orchestrator:
    """Master agent that coordinates all other specialized agents.
    
    Responsibilities:
    - Manage agent lifecycle and communication
    - Route tasks to appropriate agents
    - Enable inter-agent communication
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
        self.data_cache = {}  # Shared data between agents
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
    
    def cache_data(self, key: str, data: Any) -> None:
        """Cache data for sharing between agents.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        self.data_cache[key] = data
        logger.info(f"Data cached: {key}")
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None
        """
        return self.data_cache.get(key)
    
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
    
    def execute_workflow(self, workflow_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a complete workflow with multiple tasks.
        
        Args:
            workflow_tasks: List of tasks to execute in sequence
            
        Returns:
            Workflow results
        """
        try:
            logger.info(f"Starting workflow with {len(workflow_tasks)} tasks")
            
            workflow_id = f"workflow_{len(self.workflow_history):05d}"
            workflow_results = {
                "workflow_id": workflow_id,
                "status": "executing",
                "tasks": [],
                "started_at": datetime.utcnow().isoformat(),
            }
            
            for i, task_config in enumerate(workflow_tasks):
                logger.info(f"Executing workflow task {i+1}/{len(workflow_tasks)}: {task_config['type']}")
                
                task = self.create_task(task_config["type"], task_config.get("parameters", {}))
                task_result = self.execute_task(task["id"])
                workflow_results["tasks"].append(task_result)
                
                # Cache result for next task if needed
                if "cache_as" in task_config:
                    self.cache_data(task_config["cache_as"], task_result.get("result"))
            
            workflow_results["status"] = "completed"
            workflow_results["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Workflow completed: {workflow_id}")
            return workflow_results
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
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
        
        logger.info(f"Routing task: {task_type}")
        
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
            logger.error(f"Task routing failed: {e}")
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
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status.
        
        Returns:
            Workflow status including all tasks
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
