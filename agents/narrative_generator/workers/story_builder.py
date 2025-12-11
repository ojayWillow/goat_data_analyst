"""StoryBuilder Worker - Day 4 Implementation.

Converts recommendations into compelling, human-focused narratives:
- Empathetic problem description
- Business impact explanation
- Prioritized action plan
- Timeline and effort estimates
- Expected improvements
- Clear next steps

Approach: "Where are you coming from? What are your pain points? How to move forward."
"""

from typing import Any, Dict, List, Optional
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import AgentError


class StoryBuilder:
    """Builds human-focused narratives from recommendations.
    
    Takes technical recommendations and transforms them into
    empathetic, actionable stories that:
    - Show understanding of pain points
    - Explain business impact
    - Provide clear path forward
    - Motivate action
    """

    def __init__(self) -> None:
        """Initialize the StoryBuilder worker."""
        self.name = "StoryBuilder"
        self.logger = get_logger("StoryBuilder")
        self.structured_logger = get_structured_logger("StoryBuilder")
        self.logger.info("StoryBuilder worker initialized")

    def build_problem_summary(self, recommendations: List[Dict[str, Any]]) -> str:
        """Build empathetic problem summary.
        
        Args:
            recommendations: List of recommendation dicts from ActionRecommender
        
        Returns:
            Human-friendly problem summary string
        """
        try:
            if not recommendations:
                return "Your data quality looks good. No major issues detected."

            # Group by severity
            critical = [r for r in recommendations if r['priority'] == 5]
            high = [r for r in recommendations if r['priority'] == 4]
            medium = [r for r in recommendations if r['priority'] == 3]

            # Build summary based on what we found
            issues = []
            
            if critical:
                problem_types = set(r['problem_type'] for r in critical)
                issues.append(f"critical {', '.join(problem_types)} issues")
            
            if high:
                problem_types = set(r['problem_type'] for r in high)
                issues.append(f"significant {', '.join(problem_types)} problems")
            
            if medium:
                issues.append("moderate quality concerns")

            if not issues:
                return "Your data has minor quality issues that should be monitored."

            issue_text = " and ".join(issues)
            
            summary = f"Your data has {issue_text} that are preventing reliable analysis. "\
                     f"These issues compound: bad data → unreliable insights → poor decisions."

            self.logger.info("Problem summary generated")
            return summary

        except Exception as e:
            self.logger.error(f"Error building problem summary: {e}")
            return "Your data has quality issues that need attention."

    def build_pain_points(self, recommendations: List[Dict[str, Any]]) -> str:
        """Build business impact explanation.
        
        Args:
            recommendations: List of recommendation dicts
        
        Returns:
            Pain points explanation string
        """
        try:
            if not recommendations:
                return ""

            pain_points = []

            for rec in recommendations[:3]:  # Top 3 recommendations
                impact = rec.get('impact', '')
                if impact:
                    pain_points.append(f"• {impact}")

            if not pain_points:
                return ""

            header = "**Why This Matters:**\n"
            return header + "\n".join(pain_points)

        except Exception as e:
            self.logger.error(f"Error building pain points: {e}")
            return ""

    def build_action_plan(self, recommendations: List[Dict[str, Any]]) -> str:
        """Build prioritized action plan.
        
        Args:
            recommendations: List of recommendation dicts, pre-sorted by priority
        
        Returns:
            Action plan string
        """
        try:
            if not recommendations:
                return "No actions needed. Your data quality is good."

            actions = ["**Your Path Forward (Start Here First):**\n"]

            for i, rec in enumerate(recommendations[:5], 1):  # Top 5 actions
                priority_label = self._priority_to_label(rec['priority'])
                action = rec.get('action', '')
                time = rec.get('time_estimate', '')
                effort = rec.get('effort', '').capitalize()

                action_text = f"{i}. [{priority_label}] {action}\n"\
                             f"   Time: {time} | Effort: {effort}"
                actions.append(action_text)

            return "\n".join(actions)

        except Exception as e:
            self.logger.error(f"Error building action plan: {e}")
            return ""

    def build_next_steps(self, recommendations: List[Dict[str, Any]]) -> str:
        """Build concrete next steps.
        
        Args:
            recommendations: List of recommendation dicts
        
        Returns:
            Next steps string
        """
        try:
            if not recommendations:
                return ""

            # Get the first critical action
            first_action = None
            for rec in recommendations:
                if rec['priority'] >= 4:
                    first_action = rec
                    break

            if not first_action:
                first_action = recommendations[0] if recommendations else None

            if not first_action:
                return ""

            detail = first_action.get('detail', '')
            problem_type = first_action.get('problem_type', 'issue')

            next_steps = f"**Start Here:**\n"\
                        f"Focus on {problem_type} first.\n\n"\
                        f"{detail}\n\n"\
                        f"Once you complete this, you'll have a solid foundation to tackle the remaining issues."

            return next_steps

        except Exception as e:
            self.logger.error(f"Error building next steps: {e}")
            return ""

    def build_improvement_outlook(self, recommendations: List[Dict[str, Any]]) -> str:
        """Build expected improvement outlook.
        
        Args:
            recommendations: List of recommendation dicts
        
        Returns:
            Improvement outlook string
        """
        try:
            if not recommendations:
                return ""

            improvements = []

            for rec in recommendations[:3]:
                impact = rec.get('impact', '')
                if 'improve' in impact.lower() or '%' in impact:
                    improvements.append(f"• {impact}")

            if not improvements:
                return ""

            header = "**Your Payoff (What Gets Better):**\n"
            return header + "\n".join(improvements)

        except Exception as e:
            self.logger.error(f"Error building improvement outlook: {e}")
            return ""

    def build_complete_narrative(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build complete human-focused narrative.
        
        Args:
            recommendations: List of recommendation dicts from ActionRecommender
        
        Returns:
            Complete narrative dict with sections:
            - executive_summary: One-line overview
            - problem_statement: Empathetic problem description
            - pain_points: Why it matters
            - action_plan: What to do, prioritized
            - next_steps: Where to start
            - improvement_outlook: What gets better
            - full_narrative: Complete story formatted for reading
        """
        self.logger.info("Building complete narrative")

        try:
            # Build all sections
            problem_summary = self.build_problem_summary(recommendations)
            pain_points = self.build_pain_points(recommendations)
            action_plan = self.build_action_plan(recommendations)
            next_steps = self.build_next_steps(recommendations)
            improvement = self.build_improvement_outlook(recommendations)

            # Build full narrative
            full_narrative = self._format_full_narrative(
                problem_summary, pain_points, action_plan, next_steps, improvement
            )

            # Determine executive summary
            if not recommendations:
                exec_summary = "✅ Your data quality is good. No major issues detected."
            elif any(r['priority'] == 5 for r in recommendations):
                exec_summary = "⚠️ Critical data issues require immediate attention."
            elif any(r['priority'] == 4 for r in recommendations):
                exec_summary = "⚠️ Significant data quality issues need to be addressed."
            else:
                exec_summary = "ℹ️ Minor data quality issues to monitor and improve."

            narrative = {
                'executive_summary': exec_summary,
                'problem_statement': problem_summary,
                'pain_points': pain_points,
                'action_plan': action_plan,
                'next_steps': next_steps,
                'improvement_outlook': improvement,
                'full_narrative': full_narrative,
                'total_recommendations': len(recommendations),
                'critical_count': sum(1 for r in recommendations if r['priority'] == 5),
                'high_count': sum(1 for r in recommendations if r['priority'] == 4),
                'medium_count': sum(1 for r in recommendations if r['priority'] == 3)
            }

            self.logger.info("Complete narrative built successfully")
            self.structured_logger.info("Narrative generated", {
                'total_sections': 6,
                'total_recommendations': len(recommendations),
                'critical': narrative['critical_count'],
                'high': narrative['high_count'],
                'medium': narrative['medium_count']
            })

            return narrative

        except Exception as e:
            self.logger.error(f"Error building complete narrative: {e}")
            return self._default_narrative(recommendations)

    def build_narrative_for_export(self, narrative: Dict[str, Any]) -> str:
        """Format narrative for export (report, email, etc.).
        
        Args:
            narrative: Narrative dict from build_complete_narrative()
        
        Returns:
            Formatted narrative string for export
        """
        try:
            sections = [
                f"# Data Quality Analysis Report\n",
                f"## Executive Summary\n{narrative['executive_summary']}\n",
                f"## Overview\n{narrative['problem_statement']}\n",
                f"## {narrative['pain_points']}\n" if narrative['pain_points'] else "",
                f"## {narrative['action_plan']}\n",
                f"## {narrative['next_steps']}\n",
                f"## {narrative['improvement_outlook']}\n" if narrative['improvement_outlook'] else ""
            ]

            return "".join(filter(None, sections))

        except Exception as e:
            self.logger.error(f"Error formatting narrative for export: {e}")
            return narrative.get('full_narrative', '')

    # === HELPER METHODS ===

    def _priority_to_label(self, priority: int) -> str:
        """Convert priority number to label.
        
        Args:
            priority: Priority number (1-5)
        
        Returns:
            Priority label string
        """
        labels = {
            5: "Critical",
            4: "High",
            3: "Medium",
            2: "Low",
            1: "Monitor"
        }
        return labels.get(priority, "Normal")

    def _format_full_narrative(self, problem: str, pain: str, actions: str,
                               steps: str, improvement: str) -> str:
        """Format all sections into cohesive narrative.
        
        Args:
            problem: Problem statement
            pain: Pain points section
            actions: Action plan section
            steps: Next steps section
            improvement: Improvement outlook section
        
        Returns:
            Formatted full narrative string
        """
        sections = [
            problem,
            "",
            pain,
            "",
            actions,
            "",
            steps,
            "",
            improvement
        ]

        return "\n".join(filter(None, sections))

    def _default_narrative(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build default narrative when errors occur.
        
        Args:
            recommendations: Recommendation list
        
        Returns:
            Default narrative dict
        """
        return {
            'executive_summary': "Data quality analysis complete.",
            'problem_statement': "Analysis in progress.",
            'pain_points': "",
            'action_plan': "Please review recommendations.",
            'next_steps': "",
            'improvement_outlook': "",
            'full_narrative': "Analysis complete. Please review the action plan above.",
            'total_recommendations': len(recommendations),
            'critical_count': sum(1 for r in recommendations if r['priority'] == 5),
            'high_count': sum(1 for r in recommendations if r['priority'] == 4),
            'medium_count': sum(1 for r in recommendations if r['priority'] == 3)
        }
