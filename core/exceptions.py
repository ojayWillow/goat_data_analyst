"""Custom exceptions for GOAT Data Analyst."""


class GOATException(Exception):
    """Base exception for GOAT Data Analyst."""
    pass


class ConfigError(GOATException):
    """Raised when configuration is invalid or missing."""
    pass


class DatabaseError(GOATException):
    """Raised for database operation errors."""
    pass


class DataLoadError(GOATException):
    """Raised when data cannot be loaded."""
    pass


class DataError(DataLoadError):
    """Alias for DataLoadError for backward compatibility."""
    pass


class DataValidationError(GOATException):
    """Raised when data validation fails."""
    pass


class AgentError(GOATException):
    """Raised for agent operation errors."""
    pass


class OrchestratorError(GOATException):
    """Raised for orchestrator operation errors."""
    pass


class VisualizationError(GOATException):
    """Raised when visualization generation fails."""
    pass


class PredictionError(GOATException):
    """Raised when prediction fails."""
    pass


class AnomalyDetectionError(GOATException):
    """Raised when anomaly detection fails."""
    pass


class ReportGenerationError(GOATException):
    """Raised when report generation fails."""
    pass


class WorkerError(GOATException):
    """Raised when a worker operation fails."""
    pass
