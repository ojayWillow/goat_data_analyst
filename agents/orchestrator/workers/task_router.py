"""TaskRouter Worker - Routes tasks to appropriate agents.

Responsibilities:
- Route tasks by task type
- Handle task-specific parameters
- Execute agent methods based on task configuration
- Handle task routing errors
"""

from typing import Any, Dict, Optional
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import OrchestratorError
from core.error_recovery import retry_on_error


class TaskRouter:
    """Routes tasks to appropriate agents based on task type.
    
    Implements task routing logic with error handling and
    support for various agent types and operations.
    """

    def __init__(self, agent_registry: Any, data_manager: Any) -> None:
        """Initialize the TaskRouter.
        
        Args:
            agent_registry: AgentRegistry instance
            data_manager: DataManager instance
        """
        self.name = "TaskRouter"
        self.logger = get_logger("TaskRouter")
        self.structured_logger = get_structured_logger("TaskRouter")
        self.agent_registry = agent_registry
        self.data_manager = data_manager
        self.logger.info("TaskRouter initialized")

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
        
        self.logger.info(f"Routing task: {task_type}")
        self.structured_logger.info("Task routing started", {
            'task_type': task_type,
            'param_count': len(params)
        })
        
        try:
            # Data Loading
            if task_type == 'load_data':
                return self._route_load_data(params)
            
            # Exploration
            elif task_type == 'explore_data':
                return self._route_explore_data(params)
            
            # Aggregation
            elif task_type == 'aggregate_data':
                return self._route_aggregate_data(params)
            
            # Anomaly Detection
            elif task_type == 'detect_anomalies':
                return self._route_detect_anomalies(params)
            
            # Prediction
            elif task_type == 'predict':
                return self._route_predict(params)
            
            # Recommendation
            elif task_type == 'get_recommendations':
                return self._route_recommendations(params)
            
            # Visualization
            elif task_type == 'visualize_data':
                return self._route_visualize_data(params)
            
            # Reporting
            elif task_type == 'generate_report':
                return self._route_generate_report(params)
            
            else:
                raise OrchestratorError(f"Unknown task type: {task_type}")
        
        except Exception as e:
            self.logger.error(f"Task routing failed: {e}")
            raise OrchestratorError(f"Failed to route task '{task_type}': {e}")

    def _route_load_data(self, params: Dict[str, Any]) -> Any:
        """Route load_data task.
        
        Args:
            params: Task parameters (file_path)
        
        Returns:
            Load result
        """
        agent = self.agent_registry.get_or_fail('data_loader')
        file_path = params.get('file_path')
        
        if not file_path:
            raise OrchestratorError("Missing 'file_path' parameter")
        
        result = agent.load(file_path)
        
        # Cache the loaded data
        if result.get('status') == 'success':
            self.data_manager.cache('loaded_data', result['data'])
        
        return result

    def _route_explore_data(self, params: Dict[str, Any]) -> Any:
        """Route explore_data task.
        
        Args:
            params: Task parameters
        
        Returns:
            Exploration result
        """
        agent = self.agent_registry.get_or_fail('explorer')
        data = self.data_manager.get_data_for_task(params, 
                                                   self.agent_registry.get('data_loader'))
        
        agent.set_data(data)
        return agent.get_summary_report()

    def _route_aggregate_data(self, params: Dict[str, Any]) -> Any:
        """Route aggregate_data task.
        
        Args:
            params: Task parameters (group_by, agg_col, agg_func)
        
        Returns:
            Aggregation result
        """
        agent = self.agent_registry.get_or_fail('aggregator')
        data = self.data_manager.get_data_for_task(params,
                                                   self.agent_registry.get('data_loader'))
        
        agent.set_data(data)
        
        group_by = params.get('group_by')
        if not group_by:
            raise OrchestratorError("Missing 'group_by' parameter")
        
        return agent.groupby_single(
            group_by,
            params.get('agg_col'),
            params.get('agg_func', 'sum')
        )

    def _route_detect_anomalies(self, params: Dict[str, Any]) -> Any:
        """Route detect_anomalies task.
        
        Args:
            params: Task parameters (method, column, threshold/multiplier)
        
        Returns:
            Anomaly detection result
        """
        agent = self.agent_registry.get_or_fail('anomaly_detector')
        data = self.data_manager.get_data_for_task(params,
                                                   self.agent_registry.get('data_loader'))
        
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

    def _route_predict(self, params: Dict[str, Any]) -> Any:
        """Route predict task.
        
        Args:
            params: Task parameters (prediction_type, column, x_col, y_col, periods)
        
        Returns:
            Prediction result
        """
        agent = self.agent_registry.get_or_fail('predictor')
        data = self.data_manager.get_data_for_task(params,
                                                   self.agent_registry.get('data_loader'))
        
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

    def _route_recommendations(self, params: Dict[str, Any]) -> Any:
        """Route get_recommendations task.
        
        Args:
            params: Task parameters
        
        Returns:
            Recommendations result
        """
        agent = self.agent_registry.get_or_fail('recommender')
        data = self.data_manager.get_data_for_task(params,
                                                   self.agent_registry.get('data_loader'))
        
        agent.set_data(data)
        return agent.generate_action_plan()

    def _route_visualize_data(self, params: Dict[str, Any]) -> Any:
        """Route visualize_data task.
        
        Args:
            params: Task parameters (chart_type, column, x_col, y_col, bins)
        
        Returns:
            Visualization result
        """
        agent = self.agent_registry.get_or_fail('visualizer')
        data = self.data_manager.get_data_for_task(params,
                                                   self.agent_registry.get('data_loader'))
        
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

    def _route_generate_report(self, params: Dict[str, Any]) -> Any:
        """Route generate_report task.
        
        Args:
            params: Task parameters (report_type)
        
        Returns:
            Report result
        """
        agent = self.agent_registry.get_or_fail('reporter')
        data = self.data_manager.get_data_for_task(params,
                                                   self.agent_registry.get('data_loader'))
        
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
