"""Centralized Configuration System for GOAT Data Analyst - Hardening Phase 1

This module manages all configuration parameters across agents, supporting:
- Environment variable overrides
- Development/Production profiles  
- Configuration validation
- Default values with sensible defaults

Usage:
    from agents.agent_config import AgentConfig
    
    max_depth = AgentConfig.PREDICTOR_TREE_MAX_DEPTH
    # or:
    max_depth = AgentConfig.get('PREDICTOR_TREE_MAX_DEPTH')
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import json


@dataclass
class AgentConfig:
    """Centralized configuration for all agents.
    
    Supports environment variable overrides via ENV_PARAM_NAME pattern.
    Example: PREDICTOR_TREE_MAX_DEPTH environment variable overrides 
             AgentConfig.PREDICTOR_TREE_MAX_DEPTH
    """
    
    # ==================== ENVIRONMENT ====================
    ENV: str = os.getenv('AGENT_ENV', 'development')
    DEBUG: bool = os.getenv('AGENT_DEBUG', 'true').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # ==================== DATA LOADER ====================
    DATA_LOADER_CHUNK_SIZE: int = int(os.getenv('DATA_LOADER_CHUNK_SIZE', '10000'))
    DATA_LOADER_ENCODING: str = os.getenv('DATA_LOADER_ENCODING', 'utf-8')
    DATA_LOADER_MAX_FILE_SIZE_MB: int = int(os.getenv('DATA_LOADER_MAX_FILE_SIZE', '500'))
    DATA_LOADER_INFER_DTYPES: bool = os.getenv('DATA_LOADER_INFER_DTYPES', 'true').lower() == 'true'
    
    # ==================== EXPLORER ====================
    EXPLORER_OUTLIER_IQR_MULTIPLIER: float = float(os.getenv('EXPLORER_IQR_MULTIPLIER', '1.5'))
    EXPLORER_MIN_SAMPLES_CATEGORICAL: int = int(os.getenv('EXPLORER_MIN_CATEGORICAL', '10'))
    EXPLORER_CORRELATION_THRESHOLD: float = float(os.getenv('EXPLORER_CORR_THRESHOLD', '0.7'))
    EXPLORER_ENABLE_ADVANCED_STATS: bool = os.getenv('EXPLORER_ADVANCED_STATS', 'false').lower() == 'true'
    
    # ==================== ANOMALY DETECTOR ====================
    ANOMALY_ISOLATION_FOREST_CONTAMINATION: float = float(os.getenv('ANOMALY_CONTAMINATION', '0.1'))
    ANOMALY_ISOLATION_FOREST_RANDOM_STATE: int = 42
    ANOMALY_ISOLATION_FOREST_N_ESTIMATORS: int = int(os.getenv('ANOMALY_N_ESTIMATORS', '100'))
    ANOMALY_STATISTICAL_SIGMA: float = float(os.getenv('ANOMALY_SIGMA', '3.0'))
    
    # ==================== VISUALIZER ====================
    CHART_DEFAULT_HEIGHT: int = int(os.getenv('CHART_HEIGHT', '400'))
    CHART_DEFAULT_WIDTH: int = int(os.getenv('CHART_WIDTH', '600'))
    CHART_DPI: int = int(os.getenv('CHART_DPI', '100'))
    CHART_STYLE: str = os.getenv('CHART_STYLE', 'seaborn-v0_8-darkgrid')
    
    # ==================== AGGREGATOR ====================
    AGGREGATOR_ROLLING_WINDOW: int = int(os.getenv('AGGREGATOR_WINDOW', '7'))
    AGGREGATOR_ROLLING_MIN_PERIODS: int = int(os.getenv('AGGREGATOR_MIN_PERIODS', '1'))
    
    # ==================== PREDICTOR ====================
    PREDICTOR_TREE_MAX_DEPTH: int = int(os.getenv('PREDICTOR_MAX_DEPTH', '10'))
    PREDICTOR_CV_FOLDS: int = int(os.getenv('PREDICTOR_CV_FOLDS', '5'))
    PREDICTOR_RANDOM_STATE: int = 42
    PREDICTOR_TEST_SIZE: float = float(os.getenv('PREDICTOR_TEST_SIZE', '0.2'))
    
    # ==================== PERFORMANCE & RELIABILITY ====================
    OPERATION_TIMEOUT_SECONDS: int = int(os.getenv('OPERATION_TIMEOUT', '30'))
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_BACKOFF_FACTOR: int = int(os.getenv('RETRY_BACKOFF', '2'))
    
    # ==================== LOGGING ====================
    ENABLE_STRUCTURED_LOGGING: bool = os.getenv('STRUCTURED_LOGGING', 'true').lower() == 'true'
    LOG_DIR: str = os.getenv('LOG_DIR', './logs')
    
    @classmethod
    def from_file(cls, filepath: str) -> 'AgentConfig':
        """Load configuration from JSON file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def validate(cls) -> Tuple[bool, list]:
        """Validate configuration is sane.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        config = cls()
        
        if config.DATA_LOADER_CHUNK_SIZE <= 0:
            errors.append("DATA_LOADER_CHUNK_SIZE must be positive")
        
        if not (0 < config.ANOMALY_ISOLATION_FOREST_CONTAMINATION < 1):
            errors.append("ANOMALY_ISOLATION_FOREST_CONTAMINATION must be between 0 and 1")
        
        if config.PREDICTOR_CV_FOLDS < 2:
            errors.append("PREDICTOR_CV_FOLDS must be >= 2")
        
        if config.OPERATION_TIMEOUT_SECONDS <= 0:
            errors.append("OPERATION_TIMEOUT_SECONDS must be positive")
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def get(cls, param_name: str, default: Any = None) -> Any:
        """Get configuration parameter by name."""
        return getattr(cls, param_name, default)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary."""
        config_dict = {}
        for key in dir(cls):
            if key.isupper() and not key.startswith('_'):
                value = getattr(cls, key)
                if not callable(value):
                    config_dict[key] = value
        return config_dict


def get_config() -> AgentConfig:
    """Get configuration instance."""
    return AgentConfig()
