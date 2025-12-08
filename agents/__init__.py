"""Agents module for GOAT Data Analyst.

Contains specialized agents for data analysis, visualization, and insights.
"""

from .orchestrator import Orchestrator
from .data_loader import DataLoader

__all__ = ['Orchestrator', 'DataLoader']
