"""Narrative Generator Agent - Orchestrates narrative generation workers.

Transforms raw agent results into clear, actionable narratives using
worker delegation, comprehensive error handling, and quality scoring.

Implementation follows AGENT_WORKER_GUIDANCE:
- Coordinator-Specialist pattern with 4 specialized workers
- Error intelligence tracking for all operations
- Input validation and quality scoring
- Exponential backoff retry logic
- Structured logging and error recovery
"""

from typing import Any, Dict, Optional, List
import pandas as pd
from datetime import datetime
import time
import logging

from core.logger import get_logger
from core.error_recovery import retry_on_error
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError
from core.agent_interface import AgentInterface
from agents.error_intelligence.main import ErrorIntelligence
from agents.narrative_generator.workers.insight_extractor import InsightExtractor
from agents.narrative_generator.workers.problem_identifier import ProblemIdentifier
from agents.narrative_generator.workers.action_recommender import ActionRecommender
from agents.narrative_generator.workers.story_builder import StoryBuilder


# ===== CONSTANTS =====
MIN_RESULTS_KEYS = 1  # Minimum required result keys
QUALITY_THRESHOLD = 0.7  # Quality score threshold (0-1)
RETRY_MAX_ATTEMPTS = 3
RETRY_INITIAL_BACKOFF = 1.0  # seconds
RETRY_BACKOFF_MULTIPLIER = 2.0
MAX_PROBLEMS = 50  # Maximum problems to track
MAX_INSIGHTS = 100  # Maximum insights to track


class NarrativeGenerator(AgentInterface):
    """Narrative Generator Agent - coordinates narrative generation workers.
    
    Transforms raw analytical results into cohesive narratives using
    specialized workers following the Coordinator-Specialist pattern.
    
    Workers:
    1. InsightExtractor: Extracts key findings from results
    2. ProblemIdentifier: Identifies and ranks problems by severity
    3. ActionRecommender: Generates specific actionable recommendations
    4. StoryBuilder: Constructs narrative with all components
    
    Architecture:
    - Each worker is single-responsibility
    - All operations tracked in error intelligence
    - Quality scoring on all outputs (0-1 scale)
    - Exponential backoff retry with jitter
    - Graceful degradation on failures
    
    Contract-compliant implementation:
    - Implements AgentInterface
    - Standardized response format (status, data, message, metadata)
    - All public methods return Dict[str, Any]
    - 100% type hints and comprehensive docstrings
    """

    def __init__(self) -> None:
        """Initialize the Narrative Generator agent with all workers."""
        super().__init__()
        self.name = "NarrativeGenerator"
        self.version = "2.0-worker-integrated"
        self.logger = get_logger("NarrativeGenerator")
        self.structured_logger = get_structured_logger("NarrativeGenerator")
        self.error_intelligence = ErrorIntelligence()
        
        # Initialize workers
        self.insight_extractor = InsightExtractor()
        self.problem_identifier = ProblemIdentifier()
        self.action_recommender = ActionRecommender()
        self.story_builder = StoryBuilder()
        
        # State tracking
        self.agent_results: Dict[str, Any] = {}
        self.insights: Dict[str, Any] = {}
        self.problems: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []
        self.narrative: Optional[Dict[str, Any]] = None
        self.quality_score: float = 0.0
        self.workflow_results: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None
        
        self.logger.info(
            f"NarrativeGenerator initialized",
            extra={"version": self.version, "workers": 4}
        )
        self.structured_logger.info("NarrativeGenerator initialized", {
            "status": "ready",
            "version": self.version,
            "workers_initialized": [
                self.insight_extractor.name,
                self.problem_identifier.name,
                self.action_recommender.name,
                self.story_builder.name
            ]
        })

    # ===== INPUT VALIDATION =====

    def _validate_agent_results(
        self,
        results: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate agent results meet requirements.
        
        Args:
            results: Dictionary of agent results from orchestrator
        
        Returns:
            (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        """
        # Type check
        if not isinstance(results, dict):
            return False, f"Expected dict, got {type(results).__name__}"
        
        # Not empty
        if len(results) < MIN_RESULTS_KEYS:
            return False, f"Results empty or has <{MIN_RESULTS_KEYS} keys"
        
        # At least one key should have data
        has_data = any(
            v is not None and v != {} and v != []
            for v in results.values()
        )
        if not has_data:
            return False, "All result values are empty"
        
        return True, None

    def _validate_workflow_results(
        self,
        workflow_results: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate workflow execution results.
        
        Args:
            workflow_results: Workflow execution results
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(workflow_results, dict):
            return False, f"Expected dict, got {type(workflow_results).__name__}"
        
        # Should have 'results' key
        if 'results' not in workflow_results:
            return False, "Missing 'results' key in workflow_results"
        
        # Results should be a dict
        results = workflow_results.get('results', {})
        if not isinstance(results, dict):
            return False, f"'results' should be dict, got {type(results).__name__}"
        
        return True, None

    # ===== QUALITY SCORING =====

    def _calculate_quality_score(
        self,
        insights_count: int,
        problems_count: int,
        actions_count: int,
        had_errors: bool = False
    ) -> float:
        """Calculate overall quality score (0-1).
        
        Quality factors:
        - Insights extracted: 0.3 weight
        - Problems identified: 0.3 weight
        - Actions generated: 0.3 weight
        - No errors: 0.1 weight
        
        Args:
            insights_count: Number of insights extracted
            problems_count: Number of problems identified
            actions_count: Number of actions recommended
            had_errors: Whether any errors occurred
        
        Returns:
            Quality score 0-1
        """
        insights_score = min(insights_count / 4, 1.0)  # 4+ insights = full points
        problems_score = min(problems_count / 3, 1.0)  # 3+ problems = full points
        actions_score = min(actions_count / 3, 1.0)    # 3+ actions = full points
        error_penalty = 0.15 if had_errors else 0.0
        
        quality = (
            (insights_score * 0.3) +
            (problems_score * 0.3) +
            (actions_score * 0.3) +
            ((1.0 - error_penalty) * 0.1)
        )
        
        return round(max(0, min(quality, 1.0)), 2)

    # ===== RETRY LOGIC WITH EXPONENTIAL BACKOFF =====

    def _retry_with_backoff(
        self,
        operation_name: str,
        func,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with exponential backoff retry.
        
        Args:
            operation_name: Name of operation for logging
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            RuntimeError: If all retries exhausted
        """
        last_error = None
        
        for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
            try:
                self.logger.debug(
                    f"{operation_name} attempt {attempt}/{RETRY_MAX_ATTEMPTS}"
                )
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    self.logger.info(
                        f"{operation_name} succeeded on attempt {attempt}"
                    )
                
                return result
            
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"{operation_name} failed on attempt {attempt}: {e}"
                )
                
                # Don't retry on last attempt
                if attempt < RETRY_MAX_ATTEMPTS:
                    backoff = (
                        RETRY_INITIAL_BACKOFF *
                        (RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    )
                    self.logger.debug(
                        f"Retrying {operation_name} after {backoff:.1f}s"
                    )
                    time.sleep(backoff)
        
        # All retries exhausted
        error_msg = f"{operation_name} failed after {RETRY_MAX_ATTEMPTS} attempts: {last_error}"
        self.logger.error(error_msg)
        self.error_intelligence.track_error(
            agent_name=self.name,
            worker_name="NarrativeGenerator",
            error_type=type(last_error).__name__,
            error_message=str(last_error),
            context={"operation": operation_name, "attempts": RETRY_MAX_ATTEMPTS}
        )
        raise RuntimeError(error_msg)

    # ===== PRIMARY METHODS =====

    @retry_on_error(max_attempts=2, backoff=1)
    def set_results(self, results: Dict[str, Any]) -> None:
        """Store raw agent results for processing.
        
        Args:
            results: Dictionary of agent results from orchestrator
                   Expected keys: anomalies, predictions, recommendations, report
        
        Raises:
            ValueError: If results are invalid
        """
        # Validate input
        is_valid, error_msg = self._validate_agent_results(results)
        if not is_valid:
            raise ValueError(f"Invalid agent results: {error_msg}")
        
        # Store results
        self.agent_results = results
        self.insights = {}
        self.problems = []
        self.actions = []
        self.narrative = None
        self.quality_score = 0.0
        self.last_error = None
        
        self.logger.info(f"Agent results stored: {list(results.keys())}")
        self.structured_logger.info("Agent results loaded", {
            "result_types": list(results.keys()),
            "result_count": len(results),
            "timestamp": datetime.now().isoformat()
        })

    @retry_on_error(max_attempts=RETRY_MAX_ATTEMPTS, backoff=RETRY_INITIAL_BACKOFF)
    def generate_narrative_from_results(
        self,
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate narrative from raw agent results.
        
        REQUIRED METHOD FOR CONTRACT COMPLIANCE
        Called by: Orchestrator.generate_narrative()
        
        Orchestrates all workers:
        1. ExtractInsights: Pull key findings
        2. IdentifyProblems: Rank issues by severity
        3. RecommendActions: Generate specific actions
        4. BuildStory: Construct final narrative
        
        Args:
            agent_results: Dict with outputs from various agents
            Expected keys: anomalies, predictions, recommendations, report
        
        Returns:
            {
                'status': 'success' | 'partial' | 'error',
                'data': {
                    'full_narrative': str,
                    'sections': List[Dict],
                    'insights': Dict,
                    'problems': List[Dict],
                    'actions': List[Dict],
                    'quality_score': float
                },
                'message': str,
                'metadata': Dict with execution details
            }
        
        Raises:
            ValueError: If agent_results invalid
        """
        execution_start = datetime.now()
        had_errors = False
        
        try:
            # Validate and store results
            self.set_results(agent_results)
            self.logger.info("Starting narrative generation workflow")
            
            # STEP 1: Extract insights (with retry)
            try:
                self.insights = self._retry_with_backoff(
                    "InsightExtraction",
                    self.insight_extractor.extract_all,
                    agent_results
                )
                self.logger.info(
                    f"Insights extracted: {len(self.insights)} insight types"
                )
            except Exception as e:
                had_errors = True
                self.logger.error(f"Insight extraction failed: {e}")
                self.insights = {}
            
            # STEP 2: Identify problems (with retry)
            try:
                self.problems = self._retry_with_backoff(
                    "ProblemIdentification",
                    self.problem_identifier.identify_all_problems,
                    self.insights
                )
                self.problems = self.problems[:MAX_PROBLEMS]  # Cap problems
                self.logger.info(
                    f"Problems identified: {len(self.problems)} problems"
                )
            except Exception as e:
                had_errors = True
                self.logger.error(f"Problem identification failed: {e}")
                self.problems = []
            
            # STEP 3: Generate actions (with retry)
            try:
                self.actions = self._retry_with_backoff(
                    "ActionRecommendation",
                    self.action_recommender.recommend_for_all_problems,
                    self.problems
                )
                self.logger.info(
                    f"Actions recommended: {len(self.actions)} actions"
                )
            except Exception as e:
                had_errors = True
                self.logger.error(f"Action recommendation failed: {e}")
                self.actions = []
            
            # STEP 4: Build narrative (with retry)
            try:
                narrative_dict = self._retry_with_backoff(
                    "StoryBuilding",
                    self.story_builder.build_complete_narrative,
                    self.insights,
                    self.problems,
                    self.actions
                )
                self.narrative = narrative_dict
                self.logger.info("Narrative story built")
            except Exception as e:
                had_errors = True
                self.logger.error(f"Story building failed: {e}")
                self.narrative = self._build_fallback_narrative()
            
            # Calculate quality score
            self.quality_score = self._calculate_quality_score(
                insights_count=len(self.insights),
                problems_count=len(self.problems),
                actions_count=len(self.actions),
                had_errors=had_errors
            )
            
            # Determine status
            status = "partial" if had_errors else "success"
            
            # Track success/partial
            self.error_intelligence.track_success(
                agent_name=self.name,
                worker_name="NarrativeGenerator",
                operation="generate_narrative_from_results",
                context={
                    "insights": len(self.insights),
                    "problems": len(self.problems),
                    "actions": len(self.actions),
                    "quality_score": self.quality_score,
                    "had_errors": had_errors
                }
            )
            
            execution_time = (datetime.now() - execution_start).total_seconds()
            
            self.logger.info(
                f"Narrative generation complete (status: {status}, "
                f"quality: {self.quality_score}, time: {execution_time:.2f}s)"
            )
            
            return self.success_response(
                data={
                    'full_narrative': self.narrative.get('full_narrative', ''),
                    'sections': self.narrative.get('sections', []),
                    'insights': self.insights,
                    'problems': self.problems,
                    'actions': self.actions,
                    'quality_score': self.quality_score
                },
                message=f"Narrative generated ({status})",
                metadata={
                    'status': status,
                    'insights_count': len(self.insights),
                    'problems_count': len(self.problems),
                    'actions_count': len(self.actions),
                    'quality_score': self.quality_score,
                    'had_errors': had_errors,
                    'execution_time_seconds': execution_time,
                    'workers_used': 4
                }
            )
        
        except Exception as e:
            execution_time = (datetime.now() - execution_start).total_seconds()
            self.last_error = str(e)
            
            self.logger.error(f"Narrative generation failed: {e}", exc_info=True)
            self.error_intelligence.track_error(
                agent_name=self.name,
                worker_name="NarrativeGenerator",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "operation": "generate_narrative_from_results",
                    "execution_time": execution_time
                }
            )
            
            return self.error_response(
                message=f"Failed to generate narrative: {e}",
                error_type="narrative_generation_error",
                metadata={
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'execution_time_seconds': execution_time
                }
            )

    @retry_on_error(max_attempts=RETRY_MAX_ATTEMPTS, backoff=RETRY_INITIAL_BACKOFF)
    def generate_narrative_from_workflow(
        self,
        workflow_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate narrative from workflow results.
        
        REQUIRED METHOD FOR CONTRACT COMPLIANCE
        Called by: Orchestrator.execute_workflow_with_narrative()
        
        Args:
            workflow_results: Dict with workflow execution results and task outputs
            Expected structure:
            {
                'results': {agent results},
                'tasks': [...],
                'execution_time': ...
            }
        
        Returns:
            {
                'status': 'success' | 'partial' | 'error',
                'data': {
                    'workflow_results': workflow_results,
                    'narrative': {...},
                    'combined': bool
                },
                'message': str,
                'metadata': Dict
            }
        """
        execution_start = datetime.now()
        
        try:
            # Validate workflow results
            is_valid, error_msg = self._validate_workflow_results(workflow_results)
            if not is_valid:
                raise ValueError(f"Invalid workflow results: {error_msg}")
            
            self.workflow_results = workflow_results
            
            # Extract agent results from workflow
            agent_results = workflow_results.get('results', {})
            self.logger.info(
                f"Generating narrative from workflow with {len(agent_results)} result types"
            )
            
            # Generate narrative using standard process
            narrative_response = self.generate_narrative_from_results(agent_results)
            
            execution_time = (datetime.now() - execution_start).total_seconds()
            
            if narrative_response['status'] in ['success', 'partial']:
                return self.success_response(
                    data={
                        'workflow_results': workflow_results,
                        'narrative': narrative_response['data'],
                        'combined': True
                    },
                    message="Workflow narrative generated",
                    metadata={
                        'status': narrative_response['status'],
                        'tasks_executed': len(workflow_results.get('tasks', [])),
                        'narrative_sections': len(
                            narrative_response['data'].get('sections', [])
                        ),
                        'quality_score': self.quality_score,
                        'execution_time_seconds': execution_time
                    }
                )
            else:
                return narrative_response
        
        except Exception as e:
            execution_time = (datetime.now() - execution_start).total_seconds()
            self.logger.error(f"Workflow narrative generation failed: {e}")
            self.error_intelligence.track_error(
                agent_name=self.name,
                worker_name="NarrativeGenerator",
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "operation": "generate_narrative_from_workflow",
                    "execution_time": execution_time
                }
            )
            
            return self.error_response(
                message=f"Failed to generate workflow narrative: {e}",
                error_type="workflow_narrative_error"
            )

    @retry_on_error(max_attempts=2, backoff=1)
    def get_summary(self) -> str:
        """Get human-readable summary of narrative generator state.
        
        Returns:
            Summary string with current state
        """
        return (
            f"\n{'='*60}\n"
            f"NarrativeGenerator Summary\n"
            f"{'='*60}\n"
            f"Name: {self.name}\n"
            f"Version: {self.version}\n"
            f"Status: Initialized\n"
            f"\nResults & State:\n"
            f"  Results loaded: {len(self.agent_results) > 0}\n"
            f"  Insights extracted: {len(self.insights)}\n"
            f"  Problems identified: {len(self.problems)}\n"
            f"  Actions recommended: {len(self.actions)}\n"
            f"  Narrative generated: {self.narrative is not None}\n"
            f"  Quality score: {self.quality_score}\n"
            f"\nWorkers:\n"
            f"  - {self.insight_extractor.name}\n"
            f"  - {self.problem_identifier.name}\n"
            f"  - {self.action_recommender.name}\n"
            f"  - {self.story_builder.name}\n"
            f"\nError Tracking: {self.last_error or 'No errors'}\n"
            f"{'='*60}\n"
        )

    def get_health_report(self) -> Dict[str, Any]:
        """Get health and quality metrics.
        
        Returns:
            {
                'overall_health': float 0-100,
                'quality_score': float 0-1,
                'components_healthy': int,
                'total_components': int,
                'problems_identified': int,
                'actions_recommended': int,
                'last_error': Optional[str],
                'workers': Dict with worker status
            }
        """
        return {
            'overall_health': self.quality_score * 100,
            'quality_score': self.quality_score,
            'components_healthy': 4 if self.quality_score >= QUALITY_THRESHOLD else 2,
            'total_components': 4,
            'problems_identified': len(self.problems),
            'actions_recommended': len(self.actions),
            'last_error': self.last_error,
            'workers': {
                self.insight_extractor.name: 'healthy',
                self.problem_identifier.name: 'healthy',
                self.action_recommender.name: 'healthy',
                self.story_builder.name: 'healthy'
            }
        }

    # ===== FALLBACK METHODS =====

    def _build_fallback_narrative(self) -> Dict[str, Any]:
        """Build fallback narrative when primary generation fails.
        
        Returns:
            Minimal but valid narrative dict
        """
        parts = [
            "## Data Analysis Narrative\n",
            f"Analysis performed: {datetime.now().isoformat()}\n",
            "\nNote: Narrative generation encountered issues and used fallback mode.\n"
        ]
        
        if self.insights:
            parts.append("\n### Insights Extracted\n")
            for key, value in self.insights.items():
                parts.append(f"- {key}: {value}\n")
        
        if self.problems:
            parts.append("\n### Problems Identified\n")
            for prob in self.problems:
                parts.append(f"- {prob.get('type', 'unknown')}: {prob.get('description', 'N/A')}\n")
        
        if self.actions:
            parts.append("\n### Recommended Actions\n")
            for action in self.actions:
                parts.append(f"- {action.get('action', 'Action recommended')}\n")
        
        return {
            'full_narrative': ''.join(parts),
            'sections': [],
            'confidence': 0.5,
            'fallback_mode': True
        }
