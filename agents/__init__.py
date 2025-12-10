"""Agents module for GOAT Data Analyst.

Contains specialized agents for data analysis, visualization, and insights.
"""

from .orchestrator import Orchestrator
from .data_loader import DataLoader
from .explorer import Explorer
from .aggregator import Aggregator
from .visualizer import Visualizer
from .predictor import Predictor
from .anomaly_detector import AnomalyDetector
from .project_manager import ProjectManager
from .recommender.recommender import Recommender
from .reporter.reporter import Reporter
from .explorer.explorer import Explorer
from .predictor.predictor import Predictor


__all__ = [
    'Orchestrator',
    'DataLoader',
    'Explorer',
    'Aggregator',
    'Visualizer',
    'Predictor',
    'AnomalyDetector',
    'Recommender',
    'Reporter',
    'ProjectManager',
]
