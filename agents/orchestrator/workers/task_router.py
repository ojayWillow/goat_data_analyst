"""TaskRouter Worker - Routes tasks to appropriate agents.

Responsibilities:
- Route tasks by task type
- Validate pipeline order
- Ensure data flows in correct sequence
- Handle task-specific parameters
- Execute agent methods based on task configuration
"""

from typing import Any, Dict, List, Optional
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import OrchestratorError
from core.error_recovery import retry_on_error
from agents.error_intelligence.main import ErrorIntelligence


class TaskRouter:
    """Routes tasks to appropriate agents based on task type.
    
    CORRECT PIPELINE ORDER (MUST FOLLOW):
    1. load_data
    2. explore
    3. aggregate  
    4. detect_anomalies
    5. predict
    6. recommend
    7. narrative
    8. visualize
    9. report
    """
    
    # CORRECT PIPELINE ORDER - DO NOT CHANGE
    PIPELINE_ORDER = [
        'load_data',
        'explore',
        'aggregate',
        'detect_anomalies',
        'predict',
        'recommend',
        'narrative',
        'visualize',
        'report'
    ]
    
    # Map task types to agent names
    TASK_TO_AGENT = {
        'load_data': 'data_loader',
        'explore': 'explorer',
        'aggregate': 'aggregator',
        'detect_anomalies': 'anomaly_detector',
        'predict': 'predictor',
        'recommend': 'recommender',
        'narrative': 'narrative_generator',
        'visualize': 'visualizer',
        'report': 'reporter'
    }

    def __init__(self, agent_registry: Any, data_manager: Any) -> None:
        """Initialize the TaskRouter.
        
        Args:
            agent_registry: AgentRegistry instance
            data_manager: DataManager instance
        """
        self.name = "TaskRouter"
        self.logger = get_logger("TaskRouter")
        self.structured_logger = get_structured_logger("TaskRouter")
        self.error_intelligence = ErrorIntelligence()
        self.agent_registry = agent_registry
        self.data_manager = data_manager
        self.logger.info("TaskRouter initialized with pipeline order:")
        for idx, task in enumerate(self.PIPELINE_ORDER, 1):
            self.logger.info(f"  {idx}. {task}")

    def validate_pipeline_order(self, tasks: List[Dict[str, Any]]) -> bool:
        """Validate that tasks follow correct pipeline order.
        
        Args:
            tasks: List of tasks
            
        Returns:
            True if order is correct
            
        Raises:
            OrchestratorError: If order is wrong
        """
        task_types = [t.get('type') for t in tasks]
        
        # Check all types are valid
        for task_type in task_types:
            if task_type not in self.TASK_TO_AGENT:
                raise OrchestratorError(
                    f"Invalid task type: {task_type}. "
                    f"Valid types: {list(self.TASK_TO_AGENT.keys())}"
                )
        
        # Check order
        try:
            indices = [self.PIPELINE_ORDER.index(t) for t in task_types]
        except ValueError as e:
            raise OrchestratorError(f"Invalid task in pipeline: {e}")
        
        # Verify tasks are in ascending order
        if indices != sorted(indices):
            raise OrchestratorError(
                f"\n\nERROR: Tasks out of order!\n"
                f"Expected order: {self.PIPELINE_ORDER}\n"
                f"Got: {task_types}\n\n"
            )
        
        return True

    def validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate a single task.
        
        Args:
            task: Task to validate
            
        Returns:
            True if valid
            
        Raises:
            OrchestratorError: If invalid
        """
        task_type = task.get('type')
        
        if not task_type:
            raise OrchestratorError("Task must have 'type' field")
        
        if task_type not in self.TASK_TO_AGENT:
            raise OrchestratorError(
                f"Unknown task type: '{task_type}'. "
                f"Valid types: {list(self.TASK_TO_AGENT.keys())}"
            )
        
        return True

    @retry_on_error(max_attempts=2, backoff=1)
    def route(self, task: Dict[str, Any]) -> Any:
        """Route a task to the appropriate agent.
        
        Args:
            task: Task dict with type and parameters
        
        Returns:
            Task result from agent
        
        Raises:
            OrchestratorError: If routing fails
        """
        task_type = task.get('type')
        params = task.get('parameters', {})
        
        # Validate task
        self.validate_task(task)
        
        self.logger.info(f"Routing task: {task_type}")
        self.structured_logger.info("Task routing started", {
            'task_type': task_type,
            'param_count': len(params)
        })
        
        try:
            # Get agent for task type
            agent_name = self.TASK_TO_AGENT[task_type]
            agent = self.agent_registry.get(agent_name)
            
            if not agent:
                raise OrchestratorError(
                    f"Agent not registered: {agent_name} (for task: {task_type})"
                )
            
            # Route based on task type
            if task_type == 'load_data':
                result = self._route_load_data(agent, params)
            elif task_type == 'explore':
                result = self._route_explore(agent, params)
            elif task_type == 'aggregate':
                result = self._route_aggregate(agent, params)
            elif task_type == 'detect_anomalies':
                result = self._route_detect_anomalies(agent, params)
            elif task_type == 'predict':
                result = self._route_predict(agent, params)
            elif task_type == 'recommend':
                result = self._route_recommend(agent, params)
            elif task_type == 'narrative':
                result = self._route_narrative(agent, params)
            elif task_type == 'visualize':
                result = self._route_visualize(agent, params)
            elif task_type == 'report':
                result = self._route_report(agent, params)
            else:
                raise OrchestratorError(f"Unknown task type: {task_type}")
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="orchestrator",
                worker_name="TaskRouter",
                operation="route_task",
                context={"task_type": task_type}
            )
            
            # Cache result
            self.data_manager.set(task_type, result)
            
            self.logger.info(f"Task completed and cached: {task_type}")
            return result
        
        except Exception as e:
            self.logger.error(f"Task routing failed: {e}")
            self.error_intelligence.track_error(
                agent_name="orchestrator",
                worker_name="TaskRouter",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"task_type": task_type}
            )
            raise OrchestratorError(f"Failed to route task '{task_type}': {e}")

    def _route_load_data(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route load_data task to DataLoaderAgent."""
        file_path = params.get('file_path')
        if not file_path:
            raise OrchestratorError("Missing 'file_path' parameter for load_data")
        result = agent.load(file_path)
        if result.get('status') == 'success':
            self.data_manager.set('loaded_data', result['data'])
        return result

    def _route_explore(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route explore task to ExplorerAgent."""
        data = self.data_manager.get('loaded_data')
        if data is None:
            raise OrchestratorError(
                "No loaded data for explore. Run 'load_data' first."
            )
        agent.set_data(data)
        return agent.get_summary_report()

    def _route_aggregate(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route aggregate task to AggregatorAgent."""
        data = self.data_manager.get('loaded_data')
        if data is None:
            raise OrchestratorError(
                "No loaded data for aggregate. Run 'load_data' first."
            )
        agent.set_data(data)
        group_by = params.get('group_by')
        if not group_by:
            raise OrchestratorError("Missing 'group_by' parameter for aggregate")
        return agent.groupby_single(
            group_by,
            params.get('agg_col'),
            params.get('agg_func', 'sum')
        )

    def _route_detect_anomalies(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route detect_anomalies task to AnomalyDetectorAgent."""
        data = self.data_manager.get('loaded_data')
        if data is None:
            raise OrchestratorError(
                "No loaded data for detect_anomalies. Run 'load_data' first."
            )
        agent.set_data(data)
        method = params.get('method', 'iqr')
        column = params.get('column')
        if method == 'iqr':
            return agent.iqr_detection(column, params.get('multiplier', 1.5))
        elif method == 'zscore':
            return agent.zscore_detection(column, params.get('threshold', 3.0))
        elif method == 'isolation_forest':
            return agent.isolation_forest_detection(params.get('columns', []))
        else:
            raise OrchestratorError(f"Unknown anomaly method: {method}")

    def _route_predict(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route predict task to PredictorAgent."""
        data = self.data_manager.get('loaded_data')
        if data is None:
            raise OrchestratorError(
                "No loaded data for predict. Run 'load_data' first."
            )
        agent.set_data(data)
        pred_type = params.get('prediction_type', 'trend')
        if pred_type == 'trend':
            return agent.trend_analysis(params.get('column'))
        elif pred_type == 'forecast':
            return agent.linear_regression_forecast(
                params.get('x_col'),
                params.get('y_col'),
                params.get('periods', 10)
            )
        else:
            raise OrchestratorError(f"Unknown prediction type: {pred_type}")

    def _route_recommend(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route recommend task to RecommenderAgent."""
        data = self.data_manager.get('loaded_data')
        if data is None:
            raise OrchestratorError(
                "No loaded data for recommend. Run 'load_data' first."
            )
        agent.set_data(data)
        return agent.generate_action_plan()

    def _route_narrative(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route narrative task to NarrativeGeneratorAgent."""
        # Read ALL cached data
        cached_data = {
            'data': self.data_manager.get('load_data'),
            'exploration': self.data_manager.get('explore'),
            'aggregation': self.data_manager.get('aggregate'),
            'anomalies': self.data_manager.get('detect_anomalies'),
            'predictions': self.data_manager.get('predict'),
            'recommendations': self.data_manager.get('recommend')
        }
        return agent.generate_narrative(cached_data)

    def _route_visualize(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route visualize task to VisualizerAgent."""
        data = self.data_manager.get('loaded_data')
        if data is None:
            raise OrchestratorError(
                "No loaded data for visualize. Run 'load_data' first."
            )
        agent.set_data(data)
        chart_type = params.get('chart_type', 'line')
        if chart_type == 'histogram':
            return agent.histogram(params.get('column'), params.get('bins', 30))
        elif chart_type == 'bar':
            return agent.bar_chart(params.get('x_col'), params.get('y_col'))
        elif chart_type == 'scatter':
            return agent.scatter_plot(params.get('x_col'), params.get('y_col'))
        elif chart_type == 'heatmap':
            return agent.heatmap()
        else:
            raise OrchestratorError(f"Unknown chart type: {chart_type}")

    def _route_report(self, agent: Any, params: Dict[str, Any]) -> Any:
        """Route report task to ReporterAgent."""
        data = self.data_manager.get('loaded_data')
        if data is None:
            raise OrchestratorError(
                "No loaded data for report. Run 'load_data' first."
            )
        agent.set_data(data)
        report_type = params.get('report_type', 'executive_summary')
        if report_type == 'executive_summary':
            return agent.generate_executive_summary()
        elif report_type == 'data_profile':
            return agent.generate_data_profile()
        elif report_type == 'comprehensive':
            return agent.generate_comprehensive_report()
        else:
            raise OrchestratorError(f"Unknown report type: {report_type}")

    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get pipeline information.
        
        Returns:
            Dict with pipeline details
        """
        return {
            'order': self.PIPELINE_ORDER,
            'task_to_agent': self.TASK_TO_AGENT,
            'total_stages': len(self.PIPELINE_ORDER)
        }
