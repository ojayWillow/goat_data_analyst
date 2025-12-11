"""ChartMapper Worker - Map topics to appropriate chart types.

Responsibility:
- Define topic-to-chart relationships
- Provide chart recommendations for topics
- Handle chart compatibility
- Return chart type rankings

Integrated with Week 1 systems:
- Structured logging
- Error handling with validation
"""

from typing import Any, Dict, List, Optional
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import WorkerError


class ChartMapper:
    """Maps topics to supporting chart types."""

    # Comprehensive topic-to-chart mapping
    TOPIC_CHART_MAPPING = {
        'anomalies': {
            'primary': ['scatter_plot', 'heatmap', 'box_plot'],
            'secondary': ['distribution_plot', 'isolation_plot'],
            'avoid': ['pie_chart', 'gauge_chart'],
            'description': 'Visualize outliers and unusual data points'
        },
        'trends': {
            'primary': ['line_chart', 'area_chart', 'bar_chart'],
            'secondary': ['trend_line', 'moving_average'],
            'avoid': ['pie_chart', 'donut_chart'],
            'description': 'Show data direction and movement over time'
        },
        'distribution': {
            'primary': ['histogram', 'density_plot', 'box_plot'],
            'secondary': ['violin_plot', 'kde_plot'],
            'avoid': ['pie_chart', 'line_chart'],
            'description': 'Display data spread and concentration'
        },
        'correlation': {
            'primary': ['heatmap', 'scatter_plot', 'correlation_matrix'],
            'secondary': ['bubble_chart', 'scatter_matrix'],
            'avoid': ['pie_chart', 'bar_chart'],
            'description': 'Show relationships between variables'
        },
        'patterns': {
            'primary': ['line_chart', 'scatter_plot', 'heatmap'],
            'secondary': ['faceted_plot', 'small_multiples'],
            'avoid': ['gauge_chart'],
            'description': 'Highlight recurring sequences and cycles'
        },
        'comparison': {
            'primary': ['bar_chart', 'grouped_bar', 'box_plot'],
            'secondary': ['dot_plot', 'parallel_plot'],
            'avoid': ['pie_chart'],
            'description': 'Compare values across categories'
        },
        'composition': {
            'primary': ['pie_chart', 'donut_chart', 'stacked_bar'],
            'secondary': ['sunburst', 'treemap'],
            'avoid': ['line_chart', 'scatter_plot'],
            'description': 'Show parts of a whole'
        },
        'performance': {
            'primary': ['bar_chart', 'gauge_chart', 'progress_bar'],
            'secondary': ['speedometer', 'bullet_chart'],
            'avoid': ['pie_chart'],
            'description': 'Display performance metrics and KPIs'
        },
        'risk': {
            'primary': ['heatmap', 'scatter_plot', 'bubble_chart'],
            'secondary': ['risk_matrix', 'waterfall'],
            'avoid': ['pie_chart'],
            'description': 'Visualize risk levels and severity'
        },
        'recommendations': {
            'primary': ['bar_chart', 'table', 'timeline'],
            'secondary': ['sankey_diagram', 'flow_diagram'],
            'avoid': ['pie_chart'],
            'description': 'Support action items and next steps'
        }
    }

    # Chart properties for intelligent selection
    CHART_PROPERTIES = {
        'scatter_plot': {'type': 'distribution', 'variables': 2, 'complexity': 'medium'},
        'line_chart': {'type': 'temporal', 'variables': 1, 'complexity': 'low'},
        'bar_chart': {'type': 'categorical', 'variables': 1, 'complexity': 'low'},
        'heatmap': {'type': 'matrix', 'variables': 'many', 'complexity': 'high'},
        'histogram': {'type': 'distribution', 'variables': 1, 'complexity': 'low'},
        'pie_chart': {'type': 'composition', 'variables': 1, 'complexity': 'low'},
        'box_plot': {'type': 'distribution', 'variables': 1, 'complexity': 'medium'},
        'area_chart': {'type': 'temporal', 'variables': 'many', 'complexity': 'medium'},
        'density_plot': {'type': 'distribution', 'variables': 1, 'complexity': 'medium'},
        'grouped_bar': {'type': 'categorical', 'variables': 2, 'complexity': 'medium'},
        'stacked_bar': {'type': 'composition', 'variables': 2, 'complexity': 'medium'},
        'bubble_chart': {'type': 'distribution', 'variables': 3, 'complexity': 'high'},
        'table': {'type': 'tabular', 'variables': 'many', 'complexity': 'low'},
        'gauge_chart': {'type': 'metric', 'variables': 1, 'complexity': 'low'},
        'waterfall': {'type': 'sequential', 'variables': 'many', 'complexity': 'high'},
        'sunburst': {'type': 'hierarchy', 'variables': 'many', 'complexity': 'high'},
        'treemap': {'type': 'hierarchy', 'variables': 'many', 'complexity': 'medium'}
    }

    def __init__(self) -> None:
        """Initialize ChartMapper."""
        self.name = "ChartMapper"
        self.logger = get_logger("ChartMapper")
        self.structured_logger = get_structured_logger("ChartMapper")
        self.logger.info(f"{self.name} initialized")

    def get_topic_chart_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Get complete topic-to-chart mapping.
        
        Returns:
            Dict mapping topics to chart recommendations
        """
        return self.TOPIC_CHART_MAPPING.copy()

    def get_charts_for_topic(
        self,
        topic: str,
        available_charts: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Get recommended charts for a topic.
        
        Args:
            topic: Topic name
            available_charts: Optional list of available chart objects
        
        Returns:
            Ranked list of chart type names
        
        Raises:
            WorkerError: If topic not recognized
        """
        if topic not in self.TOPIC_CHART_MAPPING:
            raise WorkerError(f"Unknown topic: {topic}")
        
        try:
            mapping = self.TOPIC_CHART_MAPPING[topic]
            primary = mapping.get('primary', [])
            secondary = mapping.get('secondary', [])
            
            # Combine primary + secondary, primary ranked higher
            recommended = primary + secondary
            
            # Filter by availability if provided
            if available_charts:
                available_types = [c.get('type', '') for c in available_charts]
                recommended = [c for c in recommended if c in available_types]
            
            self.logger.info(f"Charts for topic '{topic}': {len(recommended)} available")
            return recommended
        
        except Exception as e:
            self.logger.error(f"Failed to get charts for topic {topic}: {e}")
            raise WorkerError(f"Chart lookup failed: {e}")

    def get_charts_for_topics(
        self,
        topics: Dict[str, float],
        available_charts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, List[str]]:
        """Get recommended charts for multiple topics.
        
        Args:
            topics: Dict with topic names and confidence scores
            available_charts: Optional list of available chart objects
        
        Returns:
            Dict mapping topics to recommended chart types
        """
        try:
            result = {}
            for topic, confidence in sorted(topics.items(), key=lambda x: x[1], reverse=True):
                charts = self.get_charts_for_topic(topic, available_charts)
                if charts:
                    result[topic] = charts
            
            self.logger.info(f"Generated chart recommendations for {len(result)} topics")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to get charts for topics: {e}")
            raise WorkerError(f"Multi-topic lookup failed: {e}")

    def rank_charts_for_topic(
        self,
        topic: str,
        available_charts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank available charts by suitability for a topic.
        
        Args:
            topic: Topic name
            available_charts: List of available chart objects with metadata
        
        Returns:
            Ranked list of chart objects
        """
        if topic not in self.TOPIC_CHART_MAPPING:
            raise WorkerError(f"Unknown topic: {topic}")
        
        try:
            mapping = self.TOPIC_CHART_MAPPING[topic]
            primary = mapping.get('primary', [])
            secondary = mapping.get('secondary', [])
            avoid = mapping.get('avoid', [])
            
            ranked = []
            
            # Primary charts (score: 10)
            for chart in available_charts:
                if chart.get('type') in primary:
                    ranked.append((chart, 10))
            
            # Secondary charts (score: 5)
            for chart in available_charts:
                if chart.get('type') in secondary and chart not in [r[0] for r in ranked]:
                    ranked.append((chart, 5))
            
            # Other charts not in avoid (score: 1)
            for chart in available_charts:
                if (chart.get('type') not in avoid and 
                    chart not in [r[0] for r in ranked]):
                    ranked.append((chart, 1))
            
            # Sort by score descending
            ranked_sorted = sorted(ranked, key=lambda x: x[1], reverse=True)
            return [chart for chart, _ in ranked_sorted]
        
        except Exception as e:
            self.logger.error(f"Chart ranking failed: {e}")
            raise WorkerError(f"Ranking failed: {e}")

    def get_topic_info(self, topic: str) -> Dict[str, Any]:
        """Get detailed information about a topic's chart recommendations.
        
        Args:
            topic: Topic name
        
        Returns:
            Dict with topic metadata and chart info
        
        Raises:
            WorkerError: If topic not found
        """
        if topic not in self.TOPIC_CHART_MAPPING:
            raise WorkerError(f"Unknown topic: {topic}")
        
        mapping = self.TOPIC_CHART_MAPPING[topic]
        return {
            'topic': topic,
            'description': mapping.get('description', ''),
            'primary_charts': mapping.get('primary', []),
            'secondary_charts': mapping.get('secondary', []),
            'avoid_charts': mapping.get('avoid', []),
            'chart_count': len(mapping.get('primary', [])) + len(mapping.get('secondary', []))
        }

    def get_chart_topics(self, chart_type: str) -> List[str]:
        """Get topics that a chart type supports.
        
        Args:
            chart_type: Chart type name
        
        Returns:
            List of topics the chart supports
        """
        topics = []
        for topic, mapping in self.TOPIC_CHART_MAPPING.items():
            primary = mapping.get('primary', [])
            secondary = mapping.get('secondary', [])
            if chart_type in primary or chart_type in secondary:
                topics.append({
                    'topic': topic,
                    'priority': 'primary' if chart_type in primary else 'secondary'
                })
        
        return topics

    def get_chart_properties(self, chart_type: str) -> Optional[Dict[str, Any]]:
        """Get properties of a chart type.
        
        Args:
            chart_type: Chart type name
        
        Returns:
            Dict with chart properties or None
        """
        return self.CHART_PROPERTIES.get(chart_type)

    def suggest_chart_for_data(
        self,
        num_variables: int,
        variable_types: List[str],
        topic: Optional[str] = None
    ) -> List[str]:
        """Suggest charts based on data characteristics.
        
        Args:
            num_variables: Number of variables
            variable_types: List of variable types ('numeric', 'categorical', 'temporal')
            topic: Optional topic to consider
        
        Returns:
            List of suggested chart types
        """
        suggestions = []
        
        # If topic provided, start with topic charts
        if topic and topic in self.TOPIC_CHART_MAPPING:
            suggestions = self.get_charts_for_topic(topic)
        
        # Add data-appropriate charts
        if 'temporal' in variable_types and num_variables >= 1:
            for chart in ['line_chart', 'area_chart']:
                if chart not in suggestions:
                    suggestions.append(chart)
        
        if 'categorical' in variable_types and num_variables >= 1:
            for chart in ['bar_chart', 'pie_chart']:
                if chart not in suggestions:
                    suggestions.append(chart)
        
        if num_variables >= 2:
            if 'scatter_plot' not in suggestions:
                suggestions.append('scatter_plot')
        
        if num_variables > 2:
            if 'bubble_chart' not in suggestions:
                suggestions.append('bubble_chart')
        
        return suggestions[:5]  # Return top 5
