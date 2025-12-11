"""Narrative Generation Workers.

Day 1: InsightExtractor - Extract key findings from agent results
Day 2: ProblemIdentifier - Identify what's wrong
Day 3: ActionRecommender - What to do about it
Day 4: StoryBuilder - Build readable narrative
"""

from .insight_extractor import InsightExtractor
from .problem_identifier import ProblemIdentifier
from .action_recommender import ActionRecommender

__all__ = ["InsightExtractor", "ProblemIdentifier", "ActionRecommender"]
