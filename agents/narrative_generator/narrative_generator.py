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


class NarrativeGenerator:
    """Narrative Generator Agent - coordinates narrative generation workers.
    
    Manages narrative generation process:
    1. Extract insights from raw results
    2. Identify problems
    3. Recommend actions
    4. Build narrative story
    
    Day 1 Implementation:
    - Agent coordinator pattern
    - Workers will be added incrementally
    - Focus on InsightExtractor first
    """

    def __init__(self) -> None:
        """Initialize the Narrative Generator agent."""
        self.name = "NarrativeGenerator"
        self.logger = get_logger("NarrativeGenerator")
        self.structured_logger = get_structured_logger("NarrativeGenerator")
        self.agent_results: Dict[str, Any] = {}
        self.insights: Dict[str, Any] = {}
        self.problems: list = []
        self.actions: list = []
        self.narrative: Optional[Dict[str, Any]] = None

        self.logger.info("NarrativeGenerator initialized")
        self.structured_logger.info("NarrativeGenerator initialized", {
            "status": "ready",
            "workers": "to_be_added"
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

    @retry_on_error(max_attempts=2, backoff=1)
    def get_summary(self) -> str:
        """Get human-readable info about the agent state.
        
        Returns:
            Summary string
        """
        return (
            f"NarrativeGenerator Summary:\n"
            f"  Status: initialized\n"
            f"  Results loaded: {len(self.agent_results) > 0}\n"
            f"  Insights extracted: {len(self.insights) > 0}\n"
            f"  Problems identified: {len(self.problems)}\n"
            f"  Actions recommended: {len(self.actions)}\n"
            f"  Narrative generated: {self.narrative is not None}"
        )
