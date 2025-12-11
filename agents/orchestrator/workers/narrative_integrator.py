"""NarrativeIntegrator Worker - Bridges Orchestrator to Narrative Generator.

Responsibilities:
- Collect agent results from pipeline
- Format results for narrative generator
- Execute narrative generation
- Aggregate final story with pipeline results

This is the bridge between data analysis (orchestrator) and storytelling (narrative).
"""

from typing import Any, Dict, Optional
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import OrchestratorError
from core.error_recovery import retry_on_error
from agents.error_intelligence.main import ErrorIntelligence
from agents.narrative_generator.integration_tester import IntegrationTester


class NarrativeIntegrator:
    """Integrates orchestrator pipeline with narrative generator.
    
    Responsibilities:
    - Collect results from multiple agents in the pipeline
    - Format results for narrative generation
    - Execute narrative pipeline
    - Combine story with analysis results
    """

    def __init__(self) -> None:
        """Initialize the NarrativeIntegrator."""
        self.name = "NarrativeIntegrator"
        self.logger = get_logger("NarrativeIntegrator")
        self.structured_logger = get_structured_logger("NarrativeIntegrator")
        self.error_intelligence = ErrorIntelligence()
        
        # Initialize narrative generator
        self.narrative_tester = IntegrationTester()
        
        self.logger.info("NarrativeIntegrator initialized")

    @retry_on_error(max_attempts=2, backoff=1)
    def generate_narrative_from_results(
        self,
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate narrative from agent results.
        
        Takes results from orchestrator agents and generates
        an empathetic story that tells the user what to do.
        
        Args:
            agent_results: Dict with explorer, anomalies, predictions, etc.
                          Expected keys:
                          - 'explorer': data exploration results
                          - 'anomalies': anomaly detection results
                          - 'predictions': prediction model results
                          - (optional) 'data_shape': shape of analyzed data
        
        Returns:
            Complete narrative dict with story
        
        Raises:
            OrchestratorError: If narrative generation fails
        """
        try:
            self.logger.info("Generating narrative from agent results")
            self.structured_logger.info("Narrative generation started", {
                'result_keys': list(agent_results.keys())
            })
            
            # Use narrative generator pipeline
            narrative = self.narrative_tester.run_narrative_pipeline(agent_results)
            
            if narrative is None:
                raise OrchestratorError("Narrative generation returned None")
            
            # Enrich narrative with metadata
            narrative['agent_results'] = agent_results
            narrative['generated_at'] = self._get_timestamp()
            
            self.logger.info("Narrative generated successfully")
            self.structured_logger.info("Narrative generation completed", {
                'has_summary': bool(narrative.get('executive_summary')),
                'total_recommendations': narrative.get('total_recommendations', 0)
            })
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="orchestrator",
                worker_name="NarrativeIntegrator",
                operation="generate_narrative_from_results",
                context={"result_keys": list(agent_results.keys())}
            )
            
            return narrative
        
        except Exception as e:
            self.logger.error(f"Narrative generation failed: {e}")
            self.error_intelligence.track_error(
                agent_name="orchestrator",
                worker_name="NarrativeIntegrator",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "generate_narrative_from_results"}
            )
            raise OrchestratorError(f"Failed to generate narrative: {e}")

    @retry_on_error(max_attempts=2, backoff=1)
    def generate_narrative_from_workflow(
        self,
        workflow_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate narrative from complete workflow result.
        
        Takes a completed workflow and generates narrative
        that summarizes the entire analysis pipeline.
        
        Args:
            workflow_result: Complete workflow execution result
                            Contains all task results from orchestrator
        
        Returns:
            Complete result with narrative added
        
        Raises:
            OrchestratorError: If narrative generation fails
        """
        try:
            self.logger.info("Generating narrative from workflow results")
            
            # Extract agent results from workflow tasks
            agent_results = self._extract_agent_results_from_workflow(workflow_result)
            
            # Generate narrative
            narrative = self.generate_narrative_from_results(agent_results)
            
            # Combine workflow and narrative
            enriched_result = {
                'workflow': workflow_result,
                'narrative': narrative,
                'combined_at': self._get_timestamp()
            }
            
            self.logger.info("Workflow enriched with narrative")
            
            # Track success
            self.error_intelligence.track_success(
                agent_name="orchestrator",
                worker_name="NarrativeIntegrator",
                operation="generate_narrative_from_workflow",
                context={"workflow_id": workflow_result.get('workflow_id')}
            )
            
            return enriched_result
        
        except Exception as e:
            self.logger.error(f"Workflow narrative generation failed: {e}")
            self.error_intelligence.track_error(
                agent_name="orchestrator",
                worker_name="NarrativeIntegrator",
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "generate_narrative_from_workflow"}
            )
            raise OrchestratorError(f"Failed to generate workflow narrative: {e}")

    def _extract_agent_results_from_workflow(
        self,
        workflow_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract agent results from workflow tasks.
        
        Maps workflow task results to agent result format
        that narrative generator expects.
        
        Args:
            workflow_result: Workflow execution result
        
        Returns:
            Dict formatted for narrative generator
        """
        try:
            agent_results = {}
            tasks = workflow_result.get('tasks', [])
            
            for task in tasks:
                task_type = task.get('type')
                result = task.get('result', {})
                
                # Map task results to agent result format
                if task_type == 'explore_data':
                    agent_results['explorer'] = result
                elif task_type == 'detect_anomalies':
                    agent_results['anomalies'] = result
                elif task_type == 'predict':
                    agent_results['predictions'] = result
                elif task_type == 'get_recommendations':
                    agent_results['recommendations'] = result
            
            self.logger.info(f"Extracted results from {len(tasks)} workflow tasks")
            return agent_results
        
        except Exception as e:
            self.logger.error(f"Error extracting workflow results: {e}")
            raise OrchestratorError(f"Failed to extract workflow results: {e}")

    def validate_narrative(
        self,
        narrative: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Validate narrative quality.
        
        Args:
            narrative: Narrative dict to validate
        
        Returns:
            Dict with validation results
        """
        try:
            validation = {
                'has_executive_summary': bool(narrative.get('executive_summary')),
                'has_problem_statement': bool(narrative.get('problem_statement')),
                'has_action_plan': bool(narrative.get('action_plan')),
                'has_full_narrative': bool(narrative.get('full_narrative')),
                'has_recommendations': narrative.get('total_recommendations', 0) > 0,
                'narrative_length_ok': len(narrative.get('full_narrative', '')) > 100,
                'all_sections_present': all(
                    narrative.get(key) 
                    for key in ['executive_summary', 'problem_statement', 'full_narrative']
                )
            }
            
            return validation
        
        except Exception as e:
            self.logger.error(f"Narrative validation failed: {e}")
            return {}

    def get_narrative_summary(
        self,
        narrative: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get a summary of the narrative.
        
        Args:
            narrative: Narrative dict
        
        Returns:
            Summary dict with key insights
        """
        try:
            return {
                'headline': narrative.get('executive_summary', 'N/A'),
                'problem_count': narrative.get('total_recommendations', 0),
                'critical_issues': narrative.get('critical_count', 0),
                'high_priority': narrative.get('high_count', 0),
                'action_items': self._extract_action_items(narrative),
                'confidence_level': self._calculate_confidence(narrative)
            }
        
        except Exception as e:
            self.logger.error(f"Error getting narrative summary: {e}")
            return {}

    def _extract_action_items(self, narrative: Dict[str, Any]) -> list:
        """Extract actionable items from narrative.
        
        Args:
            narrative: Narrative dict
        
        Returns:
            List of action items
        """
        try:
            action_plan = narrative.get('action_plan', '')
            if not action_plan:
                return []
            
            # Parse action items from plan
            items = []
            lines = action_plan.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('**'):
                    items.append(line)
            
            return items[:5]  # Top 5 actions
        
        except Exception as e:
            self.logger.error(f"Error extracting action items: {e}")
            return []

    def _calculate_confidence(self, narrative: Dict[str, Any]) -> float:
        """Calculate narrative confidence score.
        
        Args:
            narrative: Narrative dict
        
        Returns:
            Confidence score (0-1)
        """
        try:
            # Base score
            score = 0.5
            
            # Add points for narrative completeness
            if narrative.get('executive_summary'):
                score += 0.1
            if narrative.get('problem_statement'):
                score += 0.1
            if narrative.get('action_plan'):
                score += 0.1
            if narrative.get('full_narrative'):
                score += 0.1
            
            # Add points for recommendations
            recommendation_count = narrative.get('total_recommendations', 0)
            if recommendation_count > 0:
                score = min(1.0, score + (0.1 * min(recommendation_count / 5, 1.0)))
            
            return round(score, 2)
        
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 0.5

    def _get_timestamp(self) -> str:
        """Get current timestamp.
        
        Returns:
            ISO format timestamp
        """
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
