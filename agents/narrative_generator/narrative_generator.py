"""Narrative Generator Agent - Orchestrates narrative generation workers.

Transforms raw agent results into clear, actionable narratives.
"""

from typing import Any, Dict, Optional
import pandas as pd
from datetime import datetime

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from core.agent_interface import AgentInterface


class NarrativeGenerator(AgentInterface):
    """Narrative Generator Agent - coordinates narrative generation workers.
    
    Manages narrative generation process:
    1. Extract insights from raw results
    2. Identify problems
    3. Recommend actions
    4. Build narrative story
    
    Contract-compliant implementation:
    - Implements AgentInterface
    - Standardized response format
    - All public methods return Dict[str, Any]
    """

    def __init__(self) -> None:
        """Initialize the Narrative Generator agent."""
        super().__init__()
        self.name = "NarrativeGenerator"
        self.logger = get_logger("NarrativeGenerator")
        self.structured_logger = get_structured_logger("NarrativeGenerator")
        self.agent_results: Dict[str, Any] = {}
        self.insights: Dict[str, Any] = {}
        self.problems: list = []
        self.actions: list = []
        self.narrative: Optional[Dict[str, Any]] = None
        self.workflow_results: Optional[Dict[str, Any]] = None

        self.logger.info("NarrativeGenerator initialized")
        self.structured_logger.info("NarrativeGenerator initialized", {
            "status": "ready",
            "version": "2.0-contract-compliant"
        })

    @retry_on_error(max_attempts=2, backoff=1)
    def set_results(self, results: Dict[str, Any]) -> None:
        """Store raw agent results for processing.
        
        Args:
            results: Dictionary of agent results from orchestrator
                   Expected keys: anomalies, predictions, recommendations, report, charts
        """
        self.agent_results = results
        self.insights = {}
        self.problems = []
        self.actions = []
        self.narrative = None
        
        self.logger.info(f"Agent results set: {list(results.keys())}")
        self.structured_logger.info("Agent results stored", {
            "result_types": list(results.keys()),
            "timestamp": datetime.now().isoformat()
        })

    @retry_on_error(max_attempts=3, backoff=2)
    def generate_narrative_from_results(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate narrative from raw agent results.
        
        REQUIRED METHOD FOR CONTRACT COMPLIANCE
        Called by: Orchestrator.generate_narrative()
        
        Args:
            agent_results: Dict with outputs from various agents
            
        Returns:
            {
                'status': 'success',
                'data': {
                    'full_narrative': str,
                    'sections': List[Dict],
                    'insights': List[str],
                    'problems': List[str],
                    'actions': List[str]
                },
                'message': str,
                'metadata': Dict
            }
        """
        try:
            self.set_results(agent_results)
            
            # Extract insights from results
            self._extract_insights()
            
            # Identify problems
            self._identify_problems()
            
            # Generate actions
            self._generate_actions()
            
            # Build narrative
            narrative_text = self._build_narrative_text()
            sections = self._build_narrative_sections()
            
            self.narrative = {
                'full_narrative': narrative_text,
                'sections': sections,
                'confidence': 0.85
            }
            
            self.logger.info("Narrative generated from results")
            
            return self.success_response(
                data={
                    'full_narrative': narrative_text,
                    'sections': sections,
                    'insights': list(self.insights.values()),
                    'problems': self.problems,
                    'actions': self.actions
                },
                message="Narrative generated successfully",
                metadata={'insights_count': len(self.insights), 'problems_count': len(self.problems)}
            )
            
        except Exception as e:
            self.logger.error(f"Narrative generation failed: {e}")
            return self.error_response(
                message=f"Failed to generate narrative: {e}",
                error_type="narrative_generation_error"
            )

    @retry_on_error(max_attempts=3, backoff=2)
    def generate_narrative_from_workflow(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate narrative from workflow results.
        
        REQUIRED METHOD FOR CONTRACT COMPLIANCE
        Called by: Orchestrator.execute_workflow_with_narrative()
        
        Args:
            workflow_results: Dict with workflow execution results and task outputs
            
        Returns:
            {
                'status': 'success',
                'workflow_results': workflow_results,
                'narrative': {
                    'full_narrative': str,
                    'sections': List[Dict]
                },
                'message': str
            }
        """
        try:
            self.workflow_results = workflow_results
            
            # Extract agent results from workflow
            agent_results = workflow_results.get('results', {})
            
            # Generate narrative using the same process
            narrative_response = self.generate_narrative_from_results(agent_results)
            
            if narrative_response['status'] == 'success':
                # Combine workflow results with narrative
                return self.success_response(
                    data={
                        'workflow_results': workflow_results,
                        'narrative': narrative_response['data'],
                        'combined': True
                    },
                    message="Workflow narrative generated successfully",
                    metadata={
                        'tasks_executed': len(workflow_results.get('tasks', [])),
                        'narrative_sections': len(narrative_response['data'].get('sections', []))
                    }
                )
            else:
                return narrative_response
                
        except Exception as e:
            self.logger.error(f"Workflow narrative generation failed: {e}")
            return self.error_response(
                message=f"Failed to generate workflow narrative: {e}",
                error_type="workflow_narrative_error"
            )

    @retry_on_error(max_attempts=2, backoff=1)
    def get_summary(self) -> str:
        """Get human-readable summary of narrative generator state.
        
        Returns:
            Summary string
        """
        return (
            f"NarrativeGenerator Summary:\n"
            f"  Status: initialized\n"
            f"  Results loaded: {len(self.agent_results) > 0}\n"
            f"  Insights extracted: {len(self.insights)}\n"
            f"  Problems identified: {len(self.problems)}\n"
            f"  Actions recommended: {len(self.actions)}\n"
            f"  Narrative generated: {self.narrative is not None}"
        )

    # ===== PRIVATE HELPER METHODS =====

    def _extract_insights(self) -> None:
        """Extract key insights from agent results."""
        for key, value in self.agent_results.items():
            if isinstance(value, dict) and 'summary' in value:
                self.insights[key] = value['summary']
            elif isinstance(value, list) and len(value) > 0:
                self.insights[key] = f"Found {len(value)} items in {key}"
            else:
                self.insights[key] = f"Analyzed {key}"

    def _identify_problems(self) -> None:
        """Identify problems from agent results."""
        if 'anomalies' in self.agent_results:
            anomalies = self.agent_results['anomalies']
            if isinstance(anomalies, (list, tuple)) and len(anomalies) > 0:
                self.problems.append(f"Found {len(anomalies)} anomalies in data")
        
        if 'errors' in self.agent_results:
            errors = self.agent_results['errors']
            if errors:
                self.problems.append(f"Encountered {len(errors) if isinstance(errors, list) else 1} errors")

    def _generate_actions(self) -> None:
        """Generate recommended actions."""
        if len(self.problems) > 0:
            self.actions.append("Review identified anomalies")
        if len(self.insights) > 0:
            self.actions.append("Analyze extracted insights")
        self.actions.append("Consider next steps based on findings")

    def _build_narrative_text(self) -> str:
        """Build narrative text."""
        parts = [
            "## Data Analysis Narrative\n",
            f"Analysis performed at {datetime.now().isoformat()}\n"
        ]
        
        if self.insights:
            parts.append("\n### Key Insights\n")
            for key, insight in self.insights.items():
                parts.append(f"- {insight}\n")
        
        if self.problems:
            parts.append("\n### Issues Identified\n")
            for problem in self.problems:
                parts.append(f"- {problem}\n")
        
        if self.actions:
            parts.append("\n### Recommended Actions\n")
            for action in self.actions:
                parts.append(f"- {action}\n")
        
        return "".join(parts)

    def _build_narrative_sections(self) -> list:
        """Build narrative sections."""
        sections = []
        
        if self.insights:
            sections.append({
                'title': 'Key Insights',
                'content': '\n'.join([f"- {v}" for v in self.insights.values()]),
                'type': 'insights'
            })
        
        if self.problems:
            sections.append({
                'title': 'Issues Identified',
                'content': '\n'.join([f"- {p}" for p in self.problems]),
                'type': 'problems'
            })
        
        if self.actions:
            sections.append({
                'title': 'Recommended Actions',
                'content': '\n'.join([f"- {a}" for a in self.actions]),
                'type': 'actions'
            })
        
        return sections
