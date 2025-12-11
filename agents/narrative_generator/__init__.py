"""Narrative Generator Agent - Makes results understandable to users.

Converts raw agent results into clear, actionable narratives.

Workers:
- InsightExtractor: Pull key findings from agent results
- ProblemIdentifier: Identify what's wrong
- ActionRecommender: What to do about it
- StoryBuilder: Build readable narrative
"""

from .narrative_generator import NarrativeGenerator

__all__ = ["NarrativeGenerator"]
