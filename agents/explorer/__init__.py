"""Explorer Agent Department.

Responsible for data exploration and analysis.
Manages workers: NumericAnalyzer, CategoricalAnalyzer, CorrelationAnalyzer, QualityAssessor.
"""

from .explorer import Explorer

__all__ = ['Explorer']
