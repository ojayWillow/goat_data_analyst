"""CustomizationEngine Worker - Handle user preferences and customization.

Responsibility:
- Manage user preference presets
- Apply customization rules
- Validate preferences
- Generate customization options
- Save/load preferences

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


class CustomizationEngine:
    """Manages user preferences and customization."""

    # Predefined customization presets
    PRESETS = {
        'minimal': {
            'name': 'Minimal',
            'description': 'Text only, minimal charts',
            'max_charts': 1,
            'exclude_types': [],
            'include_only': None,
            'prefer_types': []
        },
        'essential': {
            'name': 'Essential',
            'description': 'Essential charts only',
            'max_charts': 3,
            'exclude_types': ['pie_chart', 'gauge_chart'],
            'include_only': None,
            'prefer_types': ['line_chart', 'bar_chart', 'scatter_plot']
        },
        'complete': {
            'name': 'Complete',
            'description': 'All relevant charts',
            'max_charts': 10,
            'exclude_types': [],
            'include_only': None,
            'prefer_types': []
        },
        'visual_heavy': {
            'name': 'Visual Heavy',
            'description': 'Maximum charts and visualizations',
            'max_charts': 15,
            'exclude_types': [],
            'include_only': None,
            'prefer_types': ['heatmap', 'scatter_plot', 'bubble_chart']
        },
        'presentation': {
            'name': 'Presentation',
            'description': 'Charts suitable for presentations',
            'max_charts': 5,
            'exclude_types': ['table', 'matrix'],
            'include_only': None,
            'prefer_types': ['bar_chart', 'line_chart', 'pie_chart']
        }
    }

    # Chart type categories
    CHART_CATEGORIES = {
        'distribution': ['histogram', 'box_plot', 'density_plot', 'violin_plot'],
        'categorical': ['bar_chart', 'grouped_bar', 'stacked_bar', 'pie_chart', 'donut_chart'],
        'temporal': ['line_chart', 'area_chart', 'trend_line'],
        'relationship': ['scatter_plot', 'heatmap', 'bubble_chart', 'correlation_matrix'],
        'composition': ['pie_chart', 'donut_chart', 'stacked_bar', 'sunburst', 'treemap'],
        'metric': ['gauge_chart', 'progress_bar', 'speedometer', 'bullet_chart'],
        'advanced': ['sankey_diagram', 'flow_diagram', 'waterfall', 'parallel_plot']
    }

    def __init__(self) -> None:
        """Initialize CustomizationEngine."""
        self.name = "CustomizationEngine"
        self.logger = get_logger("CustomizationEngine")
        self.structured_logger = get_structured_logger("CustomizationEngine")
        self.error_intelligence = ErrorIntelligence()
        self.logger.info(f"{self.name} initialized")

    def get_customization_options(
        self,
        available_charts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Get available customization options for user.
        
        Args:
            available_charts: Optional list of available charts
        
        Returns:
            Dict with customization options
        """
        try:
            chart_types = []
            if available_charts:
                chart_types = list(set(c.get('type', 'unknown') for c in available_charts))
            
            options = {
                'presets': self._get_preset_summaries(),
                'chart_categories': self.CHART_CATEGORIES,
                'available_chart_types': sorted(chart_types),
                'customization_options': {
                    'max_charts': {
                        'min': 0,
                        'max': 20,
                        'default': 5,
                        'description': 'Maximum number of charts in report'
                    },
                    'exclude_types': {
                        'description': 'Chart types to exclude',
                        'options': sorted(chart_types) if chart_types else []
                    },
                    'include_only': {
                        'description': 'Include only these chart types',
                        'options': sorted(chart_types) if chart_types else []
                    },
                    'prefer_types': {
                        'description': 'Preferred chart types (ranked higher)',
                        'options': sorted(chart_types) if chart_types else []
                    }
                }
            }
            
            self.logger.info(f"Generated customization options")
            
            self.error_intelligence.track_success(
                agent_name="report_generator",
                worker_name="CustomizationEngine",
                operation="get_customization_options",
                context={'chart_types_count': len(chart_types)}
            )
            
            return options
        
        except Exception as e:
            self.logger.error(f"Failed to generate customization options: {e}")
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="CustomizationEngine",
                error_type=type(e).__name__,
                error_message=str(e),
                context={}
            )
            raise WorkerError(f"Options generation failed: {e}")

    def get_preset(self, preset_name: str) -> Dict[str, Any]:
        """Get a customization preset.
        
        Args:
            preset_name: Name of the preset
        
        Returns:
            Preset dict
        
        Raises:
            WorkerError: If preset not found
        """
        if preset_name not in self.PRESETS:
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="CustomizationEngine",
                error_type="ValueError",
                error_message=f"Unknown preset: {preset_name}",
                context={'preset_name': preset_name}
            )
            raise WorkerError(f"Unknown preset: {preset_name}")
        
        self.error_intelligence.track_success(
            agent_name="report_generator",
            worker_name="CustomizationEngine",
            operation="get_preset",
            context={'preset_name': preset_name}
        )
        
        return self.PRESETS[preset_name].copy()

    def list_presets(self) -> List[Dict[str, str]]:
        """List available presets.
        
        Returns:
            List of preset summaries
        """
        return self._get_preset_summaries()

    def _get_preset_summaries(self) -> List[Dict[str, str]]:
        """Get summaries of all presets.
        
        Returns:
            List of preset summaries
        """
        summaries = []
        for key, preset in self.PRESETS.items():
            summaries.append({
                'key': key,
                'name': preset.get('name', key),
                'description': preset.get('description', '')
            })
        return summaries

    def validate_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user preferences.
        
        Args:
            preferences: User preferences dict
        
        Returns:
            Validation result dict
        
        Raises:
            WorkerError: If validation fails critically
        """
        issues = []
        warnings = []
        
        # Validate max_charts
        if 'max_charts' in preferences:
            max_charts = preferences['max_charts']
            if not isinstance(max_charts, int):
                issues.append("max_charts must be an integer")
            elif max_charts < 0:
                issues.append("max_charts cannot be negative")
            elif max_charts > 50:
                warnings.append("max_charts is very high (>50)")
        
        # Validate exclude_types
        if 'exclude_types' in preferences:
            exclude = preferences['exclude_types']
            if not isinstance(exclude, list):
                issues.append("exclude_types must be a list")
            elif not all(isinstance(t, str) for t in exclude):
                issues.append("exclude_types must contain strings")
        
        # Validate include_only
        if 'include_only' in preferences:
            include = preferences['include_only']
            if include is not None:
                if not isinstance(include, list):
                    issues.append("include_only must be a list or None")
                elif not all(isinstance(t, str) for t in include):
                    issues.append("include_only must contain strings")
        
        # Check for conflicts
        if 'exclude_types' in preferences and 'include_only' in preferences:
            exclude = set(preferences.get('exclude_types', []))
            include = set(preferences.get('include_only', []) or [])
            overlap = exclude & include
            if overlap:
                warnings.append(f"Charts appear in both exclude and include: {overlap}")
        
        valid = len(issues) == 0
        
        return {
            'valid': valid,
            'issues': issues,
            'warnings': warnings,
            'severity': 'error' if issues else ('warning' if warnings else 'success')
        }

    def apply_preferences(
        self,
        items: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply user preferences to a list of items.
        
        Args:
            items: Items to filter (charts, sections, etc)
            preferences: User preferences dict
        
        Returns:
            Filtered items list
        """
        if not preferences:
            return items
        
        result = items.copy()
        
        try:
            # Validate preferences
            validation = self.validate_preferences(preferences)
            if not validation['valid']:
                self.logger.warning(f"Invalid preferences: {validation['issues']}")
                return items
            
            # Apply max_charts
            if 'max_charts' in preferences:
                max_charts = preferences['max_charts']
                result = result[:max_charts]
            
            # Apply exclude_types
            if 'exclude_types' in preferences:
                exclude = preferences['exclude_types']
                result = [i for i in result if i.get('type') not in exclude]
            
            # Apply include_only
            if 'include_only' in preferences and preferences['include_only']:
                include = preferences['include_only']
                result = [i for i in result if i.get('type') in include]
            
            # Apply prefer_types (reorder)
            if 'prefer_types' in preferences and preferences['prefer_types']:
                prefer = preferences['prefer_types']
                preferred = [i for i in result if i.get('type') in prefer]
                others = [i for i in result if i.get('type') not in prefer]
                result = preferred + others
            
            self.logger.info(f"Applied preferences: {len(items)} -> {len(result)} items")
            
            self.error_intelligence.track_success(
                agent_name="report_generator",
                worker_name="CustomizationEngine",
                operation="apply_preferences",
                context={'input_count': len(items), 'output_count': len(result)}
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to apply preferences: {e}")
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="CustomizationEngine",
                error_type=type(e).__name__,
                error_message=str(e),
                context={'input_count': len(items)}
            )
            return items

    def merge_preferences(
        self,
        preset: str,
        custom_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Merge preset with custom overrides.
        
        Args:
            preset: Preset name
            custom_overrides: Custom overrides dict
        
        Returns:
            Merged preferences dict
        
        Raises:
            WorkerError: If preset not found
        """
        try:
            base = self.get_preset(preset)
            
            if custom_overrides:
                # Validate overrides
                validation = self.validate_preferences(custom_overrides)
                if validation['warnings']:
                    self.logger.warning(f"Preference warnings: {validation['warnings']}")
                
                # Merge (overrides take precedence)
                base.update(custom_overrides)
            
            self.logger.info(f"Merged preset '{preset}' with {len(custom_overrides or {})} overrides")
            
            self.error_intelligence.track_success(
                agent_name="report_generator",
                worker_name="CustomizationEngine",
                operation="merge_preferences",
                context={'preset_name': preset, 'override_count': len(custom_overrides or {})}
            )
            
            return base
        
        except WorkerError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to merge preferences: {e}")
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="CustomizationEngine",
                error_type=type(e).__name__,
                error_message=str(e),
                context={'preset_name': preset}
            )
            raise WorkerError(f"Merge failed: {e}")

    def get_preference_impact(
        self,
        original_count: int,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate impact of preferences on output.
        
        Args:
            original_count: Original number of items
            preferences: User preferences
        
        Returns:
            Impact estimation dict
        """
        estimated_count = original_count
        impacts = []
        
        # Estimate max_charts impact
        if 'max_charts' in preferences:
            max_charts = preferences['max_charts']
            old_count = estimated_count
            estimated_count = min(estimated_count, max_charts)
            if estimated_count < old_count:
                impacts.append({
                    'factor': 'max_charts',
                    'reduction': old_count - estimated_count,
                    'description': f"Limited to {max_charts} items"
                })
        
        # Estimate exclude/include impact
        if 'exclude_types' in preferences and preferences['exclude_types']:
            # Rough estimate: assume ~15% per excluded type
            reduction = len(preferences['exclude_types']) * 0.15 * estimated_count
            if reduction > 0:
                impacts.append({
                    'factor': 'exclude_types',
                    'reduction': int(reduction),
                    'description': f"Excluding {len(preferences['exclude_types'])} chart types"
                })
        
        return {
            'original_count': original_count,
            'estimated_count': max(0, int(estimated_count)),
            'estimated_reduction': original_count - max(0, int(estimated_count)),
            'impacts': impacts
        }

    def get_recommendation(
        self,
        available_charts: Optional[List[Dict[str, Any]]] = None,
        report_type: Optional[str] = None
    ) -> str:
        """Get recommended preset based on context.
        
        Args:
            available_charts: Available charts
            report_type: Type of report being created
        
        Returns:
            Recommended preset name
        """
        if report_type == 'presentation':
            return 'presentation'
        elif report_type == 'detailed':
            return 'complete'
        elif report_type == 'executive':
            return 'essential'
        elif report_type == 'minimal':
            return 'minimal'
        else:
            # Default: choose based on chart count
            if available_charts:
                if len(available_charts) <= 2:
                    return 'minimal'
                elif len(available_charts) <= 5:
                    return 'essential'
                elif len(available_charts) <= 10:
                    return 'complete'
                else:
                    return 'visual_heavy'
            return 'essential'
