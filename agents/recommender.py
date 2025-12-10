"""Recommender Agent - Insights extraction and recommendations.

Integrated with Week 1 foundation systems:
- Configuration management
- Error recovery with retry logic
- Structured logging
- Input/output validation

Generates actionable insights and recommendations based on data analysis,
trends, anomalies, and statistical patterns.

Wired to use Workers Pattern:
- MissingDataAnalyzer worker
- DuplicateAnalyzer worker
- DistributionAnalyzer worker
- CorrelationAnalyzer worker
- ActionPlanGenerator worker
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime, timezone

# Week 1 Integrations
from agents.agent_config import AgentConfig
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.validators import validate_input, validate_output
from core.logger import get_logger
from core.exceptions import AgentError

# Worker imports
from agents.recommender.workers import (
    MissingDataAnalyzer,
    DuplicateAnalyzer,
    DistributionAnalyzer,
    CorrelationAnalyzer,
    ActionPlanGenerator,
)

logger = get_structured_logger(__name__)
config = AgentConfig()


class Recommender:
    """Agent for generating insights and recommendations.
    
    Capabilities:
    - Pattern recognition (via MissingDataAnalyzer worker)
    - Trend-based recommendations (via DuplicateAnalyzer worker)
    - Anomaly-based insights (via DistributionAnalyzer worker)
    - Correlation insights (via CorrelationAnalyzer worker)
    - Data quality recommendations (via ActionPlanGenerator worker)
    - Performance insights
    - Actionable suggestions
    - Risk assessment
    
    Integrated with Week 1 systems:
    - Centralized configuration
    - Error recovery on all operations
    - Structured logging of all activities
    - Input/output validation
    
    Worker Pattern:
    - Delegates specific analysis tasks to specialized workers
    - Each worker handles one specific analysis type
    - Aggregates worker results into unified recommendations
    """
    
    def __init__(self):
        """Initialize Recommender agent with Week 1 systems and worker instances."""
        self.name = "Recommender"
        self.config = AgentConfig()
        self.data = None
        
        # Initialize workers
        self.missing_data_analyzer = MissingDataAnalyzer()
        self.duplicate_analyzer = DuplicateAnalyzer()
        self.distribution_analyzer = DistributionAnalyzer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.action_plan_generator = ActionPlanGenerator()
        
        logger.info(
            f"{self.name} initialized with workers",
            extra={'version': '2.0-week1-integrated', 'workers': 5}
        )
    
    @validate_input({'df': 'dataframe'})
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data for analysis with validation.
        
        Args:
            df: DataFrame to analyze (validated)
        """
        with logger.operation('set_data', {'rows': len(df), 'columns': len(df.columns)}):
            self.data = df.copy()
            logger.info(
                'Data set for recommendation',
                extra={'rows': df.shape[0], 'columns': df.shape[1]}
            )
    
    @validate_output('dataframe')
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data with validation.
        
        Returns:
            DataFrame or None (validated output)
        """
        return self.data
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def analyze_missing_data(self) -> Dict[str, Any]:
        """Delegate missing data analysis to worker.
        
        Returns:
            Dictionary with insights and recommendations (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('analyze_missing_data'):
            try:
                # Delegate to worker
                worker_result = self.missing_data_analyzer.safe_execute(df=self.data)
                
                if not worker_result.success:
                    raise AgentError(f"Worker failed: {worker_result.errors}")
                
                logger.info(
                    'Missing data analysis complete',
                    extra=worker_result.data
                )
                
                return {
                    "status": "success",
                    "analysis_type": "missing_data",
                    "worker_result": worker_result.data,
                }
            
            except Exception as e:
                logger.error(
                    'Missing data analysis failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Analysis failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def analyze_duplicates(self) -> Dict[str, Any]:
        """Delegate duplicate analysis to worker.
        
        Returns:
            Dictionary with insights and recommendations (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('analyze_duplicates'):
            try:
                # Delegate to worker
                worker_result = self.duplicate_analyzer.safe_execute(df=self.data)
                
                if not worker_result.success:
                    raise AgentError(f"Worker failed: {worker_result.errors}")
                
                logger.info(
                    'Duplicate analysis complete',
                    extra=worker_result.data
                )
                
                return {
                    "status": "success",
                    "analysis_type": "duplicates",
                    "worker_result": worker_result.data,
                }
            
            except Exception as e:
                logger.error(
                    'Duplicate analysis failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Analysis failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def analyze_distributions(self) -> Dict[str, Any]:
        """Delegate distribution analysis to worker.
        
        Returns:
            Dictionary with distribution insights (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('analyze_distributions'):
            try:
                # Delegate to worker
                worker_result = self.distribution_analyzer.safe_execute(df=self.data)
                
                if not worker_result.success:
                    raise AgentError(f"Worker failed: {worker_result.errors}")
                
                logger.info(
                    'Distribution analysis complete',
                    extra=worker_result.data
                )
                
                return {
                    "status": "success",
                    "analysis_type": "distributions",
                    "worker_result": worker_result.data,
                }
            
            except Exception as e:
                logger.error(
                    'Distribution analysis failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Analysis failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def analyze_correlations(self) -> Dict[str, Any]:
        """Delegate correlation analysis to worker.
        
        Returns:
            Dictionary with correlation insights (validated)
            
        Raises:
            AgentError: If no data set or insufficient columns
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('analyze_correlations'):
            try:
                # Delegate to worker
                worker_result = self.correlation_analyzer.safe_execute(df=self.data)
                
                if not worker_result.success:
                    raise AgentError(f"Worker failed: {worker_result.errors}")
                
                logger.info(
                    'Correlation analysis complete',
                    extra=worker_result.data
                )
                
                return {
                    "status": "success",
                    "analysis_type": "correlations",
                    "worker_result": worker_result.data,
                }
            
            except Exception as e:
                logger.error(
                    'Correlation analysis failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Analysis failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def generate_action_plan(self) -> Dict[str, Any]:
        """Delegate comprehensive action plan generation to worker.
        
        Returns:
            Dictionary with action plan and priorities (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('generate_action_plan'):
            try:
                # Delegate to worker - ActionPlanGenerator runs all sub-workers
                worker_result = self.action_plan_generator.safe_execute(df=self.data)
                
                if not worker_result.success:
                    raise AgentError(f"Worker failed: {worker_result.errors}")
                
                logger.info(
                    'Action plan generated',
                    extra={'total_actions': worker_result.data.get('total_actions', 0)}
                )
                
                return {
                    "status": "success",
                    "plan_type": "comprehensive_action_plan",
                    "worker_result": worker_result.data,
                }
            
            except Exception as e:
                logger.error(
                    'Action plan generation failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Generation failed: {e}")
    
    @retry_on_error(max_attempts=2, backoff=1)
    @validate_output('dict')
    def get_summary_insights(self) -> Dict[str, Any]:
        """Get high-level summary insights combining all worker analyses.
        
        Returns:
            Dictionary with key insights (validated)
            
        Raises:
            AgentError: If no data set
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        with logger.operation('get_summary_insights'):
            try:
                import numpy as np
                
                insights = []
                
                # Dataset size
                rows, cols = self.data.shape
                insights.append({"metric": "Size", "value": f"{rows:,} rows × {cols} columns"})
                
                # Data quality
                null_pct = (self.data.isnull().sum().sum() / (rows * cols) * 100) if (rows * cols) > 0 else 0
                if null_pct == 0:
                    quality = "Excellent"
                elif null_pct < 5:
                    quality = "Good"
                elif null_pct < 20:
                    quality = "Fair"
                else:
                    quality = "Poor"
                insights.append({"metric": "Data Quality", "value": quality, "detail": f"{null_pct:.1f}% missing"})
                
                # Duplicates
                dup_count = self.data.duplicated().sum()
                insights.append({"metric": "Duplicates", "value": f"{dup_count} rows", "percentage": f"{(dup_count/rows*100):.2f}%"})
                
                # Columns
                numeric = len(self.data.select_dtypes(include=[np.number]).columns)
                categorical = len(self.data.select_dtypes(include=['object']).columns)
                insights.append({"metric": "Numeric Columns", "value": numeric})
                insights.append({"metric": "Categorical Columns", "value": categorical})
                
                logger.info(
                    'Summary insights generated',
                    extra={'insights_count': len(insights)}
                )
                
                return {
                    "status": "success",
                    "insights_type": "summary",
                    "insights": insights,
                }
            
            except Exception as e:
                logger.error(
                    'Summary insights failed',
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise AgentError(f"Failed: {e}")
