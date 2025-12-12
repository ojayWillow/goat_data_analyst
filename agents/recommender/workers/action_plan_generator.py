"""ActionPlanGenerator - Consolidates all recommendations into prioritized action plan."""

import pandas as pd
from typing import Any, Dict, List
from datetime import datetime, timezone
from .base_worker import BaseWorker, WorkerResult, ErrorType
from .missing_data_analyzer import MissingDataAnalyzer
from .duplicate_analyzer import DuplicateAnalyzer
from .distribution_analyzer import DistributionAnalyzer
from .correlation_analyzer import CorrelationAnalyzer
from agents.error_intelligence.main import ErrorIntelligence


class ActionPlanGenerator(BaseWorker):
    """Generates comprehensive action plan from all analysis workers."""
    
    def __init__(self):
        super().__init__("action_plan_generator")
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, df: pd.DataFrame, **kwargs) -> WorkerResult:
        """Generate comprehensive action plan.
        
        Args:
            df: DataFrame to analyze
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with prioritized action plan
        """
        result = self._create_result(
            success=True,
            task_type="action_plan_generation",
            data={}
        )
        
        try:
            if df is None or df.empty:
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    "DataFrame is empty or None",
                    severity="error"
                )
                self.error_intelligence.track_error(
                    agent_name="recommender",
                    worker_name="ActionPlanGenerator",
                    operation="generate_action_plan",
                    error_type="DataValidationError",
                    error_message="DataFrame is empty or None"
                )
                return result
            
            # Run all worker analyses
            analyzers = [
                MissingDataAnalyzer(),
                DuplicateAnalyzer(),
                DistributionAnalyzer(),
                CorrelationAnalyzer(),
            ]
            
            all_insights = []
            all_recs = []
            all_results = []
            
            for analyzer in analyzers:
                worker_result = analyzer.safe_execute(df=df)
                all_results.append(worker_result.to_dict())
                
                if "insights" in worker_result.data:
                    all_insights.extend(worker_result.data["insights"])
                
                if "recommendations" in worker_result.data:
                    all_recs.extend(worker_result.data["recommendations"])
            
            # Prioritize by action type
            priorities = {
                "deduplication": 1,          # Highest
                "data_cleaning": 2,
                "imputation": 3,
                "outlier_handling": 4,
                "transformation": 5,
                "feature_engineering": 6,   # Lowest
            }
            
            # Sort by priority
            sorted_recs = sorted(
                all_recs,
                key=lambda x: priorities.get(x.get("action"), 99)
            )
            
            # Remove duplicates while preserving order
            seen = set()
            unique_recs = []
            for rec in sorted_recs:
                rec_str = str(rec)
                if rec_str not in seen:
                    seen.add(rec_str)
                    unique_recs.append(rec)
            
            result.data = {
                "status": "success",
                "plan_type": "comprehensive_action_plan",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_shape": {"rows": df.shape[0], "columns": df.shape[1]},
                "total_actions": len(unique_recs),
                "total_insights": len(all_insights),
                "actions": unique_recs,
                "insights": all_insights,
                "worker_results": all_results,
            }
            
            self.logger.info(f"Action plan generated with {len(unique_recs)} actions")
            self.error_intelligence.track_success(
                agent_name="recommender",
                worker_name="ActionPlanGenerator",
                operation="generate_action_plan"
            )
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Plan generation failed: {str(e)}",
                severity="error"
            )
            result.success = False
            self.error_intelligence.track_error(
                agent_name="recommender",
                worker_name="ActionPlanGenerator",
                operation="generate_action_plan",
                error_type=type(e).__name__,
                error_message=str(e)
            )
        
        return result
