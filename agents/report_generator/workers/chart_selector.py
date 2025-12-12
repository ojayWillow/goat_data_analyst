"""ChartSelector Worker - Intelligently select relevant charts for narrative.

Responsibility:
- Select best charts based on narrative topics
- Ensure chart relevance
- Avoid redundancy
- Rank charts by suitability
- Apply user preferences

Integrated with Week 1 systems:
- Structured logging
- Error handling with validation
- Error Intelligence monitoring
"""

from typing import Any, Dict, List, Optional
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import WorkerError
from agents.error_intelligence.main import ErrorIntelligence
from .chart_mapper import ChartMapper


class ChartSelector:
    """Intelligently selects charts for narrative sections."""

    def __init__(self, chart_mapper: Optional[ChartMapper] = None) -> None:
        """Initialize ChartSelector.
        
        Args:
            chart_mapper: Optional ChartMapper instance (creates one if not provided)
        """
        self.name = "ChartSelector"
        self.logger = get_logger("ChartSelector")
        self.structured_logger = get_structured_logger("ChartSelector")
        self.chart_mapper = chart_mapper or ChartMapper()
        self.error_intelligence = ErrorIntelligence()
        self.logger.info(f"{self.name} initialized")

    def select_charts_for_narrative(
        self,
        narrative_sections: List[Dict[str, Any]],
        available_charts: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Intelligently select charts for each narrative section.
        
        Args:
            narrative_sections: List of narrative sections with topics
            available_charts: List of available chart objects
            user_preferences: Optional user customization preferences
        
        Returns:
            Dict mapping sections to selected charts
        
        Raises:
            WorkerError: If selection fails
        """
        if not narrative_sections:
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="ChartSelector",
                error_type="ValueError",
                error_message="No narrative sections provided",
                context={}
            )
            raise WorkerError("No narrative sections provided")
        if not available_charts:
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="ChartSelector",
                error_type="ValueError",
                error_message="No available charts provided",
                context={}
            )
            raise WorkerError("No available charts provided")
        
        try:
            self.logger.info(f"Selecting charts for {len(narrative_sections)} sections")
            
            selected_by_section = {}
            all_used_charts = set()  # Track used charts to avoid duplicates
            
            for section in narrative_sections:
                section_name = section.get('section', f"Section {section.get('index', 0)}")
                topics = section.get('topics', {})
                importance = section.get('importance', 'medium')
                
                # Get candidate charts for this section's topics
                candidate_charts = self._get_candidate_charts(
                    topics,
                    available_charts
                )
                
                # Rank by relevance
                ranked = self._rank_by_relevance(
                    candidate_charts,
                    topics,
                    importance
                )
                
                # Remove duplicates (charts already used)
                filtered = [
                    c for c in ranked
                    if c.get('id', c.get('name')) not in all_used_charts
                ]
                
                # Limit charts per section based on importance
                max_charts = self._get_max_charts(importance)
                final_selection = filtered[:max_charts]
                
                # Track used charts
                for chart in final_selection:
                    all_used_charts.add(chart.get('id', chart.get('name')))
                
                selected_by_section[section_name] = final_selection
                
                self.structured_logger.info(
                    f"Selected {len(final_selection)} charts for section",
                    {'section': section_name, 'importance': importance, 'count': len(final_selection)}
                )
            
            # Apply user preferences
            if user_preferences:
                selected_by_section = self._apply_user_preferences(
                    selected_by_section,
                    user_preferences
                )
            
            self.logger.info(f"Chart selection complete: {len(selected_by_section)} sections")
            
            self.error_intelligence.track_success(
                agent_name="report_generator",
                worker_name="ChartSelector",
                operation="select_charts_for_narrative",
                context={
                    'section_count': len(narrative_sections),
                    'selected_sections': len(selected_by_section),
                    'total_charts': sum(len(charts) for charts in selected_by_section.values())
                }
            )
            
            return selected_by_section
        
        except WorkerError:
            raise
        except Exception as e:
            self.logger.error(f"Chart selection failed: {e}")
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="ChartSelector",
                error_type=type(e).__name__,
                error_message=str(e),
                context={'section_count': len(narrative_sections)}
            )
            raise WorkerError(f"Selection failed: {e}")

    def select_charts_for_topics(
        self,
        topics: Dict[str, float],
        available_charts: List[Dict[str, Any]],
        max_charts: int = 5,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Select best charts for a set of topics.
        
        Args:
            topics: Dict of topics with confidence scores
            available_charts: List of available charts
            max_charts: Maximum charts to select
            user_preferences: Optional user preferences
        
        Returns:
            List of selected chart objects
        """
        try:
            # Get candidates
            candidates = self._get_candidate_charts(topics, available_charts)
            
            # Rank by relevance
            ranked = self._rank_by_relevance(candidates, topics, 'high')
            
            # Select top N
            selected = ranked[:max_charts]
            
            # Apply preferences
            if user_preferences:
                selected = self._apply_preferences_to_list(
                    selected,
                    user_preferences
                )
            
            self.error_intelligence.track_success(
                agent_name="report_generator",
                worker_name="ChartSelector",
                operation="select_charts_for_topics",
                context={'topic_count': len(topics), 'selected_count': len(selected)}
            )
            
            return selected
        
        except Exception as e:
            self.logger.error(f"Topic-based selection failed: {e}")
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="ChartSelector",
                error_type=type(e).__name__,
                error_message=str(e),
                context={'topic_count': len(topics)}
            )
            raise WorkerError(f"Selection failed: {e}")

    def _get_candidate_charts(
        self,
        topics: Dict[str, float],
        available_charts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get candidate charts for a set of topics.
        
        Args:
            topics: Topics with confidence scores
            available_charts: Available charts
        
        Returns:
            List of candidate chart objects
        """
        candidates = []
        chart_types_needed = set()
        
        # Collect recommended chart types for all topics
        for topic, confidence in topics.items():
            if confidence >= 0.3:  # Only consider topics with minimum confidence
                recommended = self.chart_mapper.get_charts_for_topic(topic)
                chart_types_needed.update(recommended)
        
        # Find available charts matching needed types
        for chart in available_charts:
            chart_type = chart.get('type', '')
            if chart_type in chart_types_needed:
                candidates.append(chart)
        
        return candidates

    def _rank_by_relevance(
        self,
        charts: List[Dict[str, Any]],
        topics: Dict[str, float],
        importance: str
    ) -> List[Dict[str, Any]]:
        """Rank charts by relevance to topics.
        
        Args:
            charts: Charts to rank
            topics: Topics with confidence scores
            importance: Section importance level
        
        Returns:
            Ranked list of charts
        """
        scored_charts = []
        
        for chart in charts:
            score = 0.0
            chart_type = chart.get('type', '')
            
            # Check if chart supports any topic
            for topic, confidence in topics.items():
                supported = self.chart_mapper.get_charts_for_topic(topic)
                if chart_type in supported:
                    # Score: topic confidence weighted by importance
                    importance_weight = {
                        'critical': 3.0,
                        'high': 2.0,
                        'medium': 1.5,
                        'low': 1.0
                    }.get(importance, 1.0)
                    
                    score += confidence * importance_weight
            
            # Bonus for primary charts in topic mapping
            for topic, confidence in topics.items():
                mapping = self.chart_mapper.TOPIC_CHART_MAPPING.get(topic, {})
                primary = mapping.get('primary', [])
                if chart_type in primary:
                    score += 0.5
            
            if score > 0:
                scored_charts.append((chart, score))
        
        # Sort by score descending
        scored_charts.sort(key=lambda x: x[1], reverse=True)
        return [chart for chart, _ in scored_charts]

    def _get_max_charts(self, importance: str) -> int:
        """Get maximum charts allowed for section importance.
        
        Args:
            importance: Importance level
        
        Returns:
            Maximum number of charts
        """
        max_charts_map = {
            'critical': 3,
            'high': 2,
            'medium': 2,
            'low': 1
        }
        return max_charts_map.get(importance, 2)

    def _apply_user_preferences(
        self,
        selected_by_section: Dict[str, List[Dict[str, Any]]],
        preferences: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Apply user preferences to chart selection.
        
        Args:
            selected_by_section: Current selections
            preferences: User preferences dict
        
        Returns:
            Updated selections
        """
        result = {}
        
        for section, charts in selected_by_section.items():
            filtered = self._apply_preferences_to_list(charts, preferences)
            result[section] = filtered
        
        return result

    def _apply_preferences_to_list(
        self,
        charts: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply user preferences to a list of charts.
        
        Args:
            charts: Charts to filter
            preferences: User preferences
        
        Returns:
            Filtered chart list
        """
        result = charts.copy()
        
        # Exclude specific chart types
        if 'exclude_types' in preferences:
            exclude = preferences['exclude_types']
            result = [c for c in result if c.get('type') not in exclude]
        
        # Include only specific types
        if 'include_only' in preferences:
            include = preferences['include_only']
            result = [c for c in result if c.get('type') in include]
        
        # Limit max charts
        if 'max_charts' in preferences:
            max_charts = preferences['max_charts']
            result = result[:max_charts]
        
        # Prefer specific types (move to front)
        if 'prefer_types' in preferences:
            prefer = preferences['prefer_types']
            preferred = [c for c in result if c.get('type') in prefer]
            others = [c for c in result if c.get('type') not in prefer]
            result = preferred + others
        
        return result

    def get_selection_summary(
        self,
        selected_by_section: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Get summary of chart selection.
        
        Args:
            selected_by_section: Selected charts by section
        
        Returns:
            Summary dict
        """
        total_charts = sum(len(charts) for charts in selected_by_section.values())
        chart_types = set()
        
        for charts in selected_by_section.values():
            for chart in charts:
                chart_types.add(chart.get('type', 'unknown'))
        
        return {
            'sections_count': len(selected_by_section),
            'total_charts': total_charts,
            'unique_chart_types': len(chart_types),
            'chart_types': list(chart_types),
            'avg_charts_per_section': round(total_charts / max(len(selected_by_section), 1), 2)
        }
