"""Tests for configuration system - Week 1 Hardening."""

import pytest
from agents.agent_config import AgentConfig, get_config


class TestConfigurationSystem:
    """Test suite for centralized configuration."""
    
    def test_config_initialization(self):
        """Test basic config initialization."""
        config = AgentConfig()
        assert config is not None
        assert config.DEBUG is True
        assert config.OPERATION_TIMEOUT_SECONDS == 30
    
    def test_config_defaults(self):
        """Test that sensible defaults are set."""
        config = AgentConfig()
        assert config.DATA_LOADER_CHUNK_SIZE == 10000
        assert config.PREDICTOR_CV_FOLDS == 5
        assert config.MAX_RETRIES == 3
        assert config.RETRY_BACKOFF_FACTOR == 2
    
    def test_get_config_function(self):
        """Test get_config() helper function."""
        config = get_config()
        assert config is not None
        assert isinstance(config, AgentConfig)
    
    def test_environment_override_string(self, monkeypatch):
        """Test environment variable override for string."""
        monkeypatch.setenv('CHART_STYLE', 'custom-style')
        config = AgentConfig()
        assert config.CHART_STYLE == 'custom-style'
    
    def test_environment_override_int(self, monkeypatch):
        """Test environment variable override for integer."""
        monkeypatch.setenv('DATA_LOADER_CHUNK_SIZE', '50000')
        config = AgentConfig()
        assert config.DATA_LOADER_CHUNK_SIZE == 50000
    
    def test_environment_override_float(self, monkeypatch):
        """Test environment variable override for float."""
        monkeypatch.setenv('EXPLORER_IQR_MULTIPLIER', '2.5')
        config = AgentConfig()
        assert config.EXPLORER_OUTLIER_IQR_MULTIPLIER == 2.5
    
    def test_environment_override_bool_true(self, monkeypatch):
        """Test environment variable override for bool (true)."""
        monkeypatch.setenv('EXPLORER_ADVANCED_STATS', 'true')
        config = AgentConfig()
        assert config.EXPLORER_ENABLE_ADVANCED_STATS is True
    
    def test_environment_override_bool_false(self, monkeypatch):
        """Test environment variable override for bool (false)."""
        monkeypatch.setenv('EXPLORER_ADVANCED_STATS', 'false')
        config = AgentConfig()
        assert config.EXPLORER_ENABLE_ADVANCED_STATS is False
    
    def test_config_get_method(self):
        """Test .get() class method."""
        value = AgentConfig.get('PREDICTOR_TREE_MAX_DEPTH')
        assert value == 10
    
    def test_config_get_method_with_default(self):
        """Test .get() with default value for nonexistent key."""
        value = AgentConfig.get('NONEXISTENT_KEY', 'default')
        assert value == 'default'
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = AgentConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'PREDICTOR_TREE_MAX_DEPTH' in config_dict
        assert 'DATA_LOADER_CHUNK_SIZE' in config_dict
    
    def test_config_validate_valid(self):
        """Test validation passes with valid config."""
        is_valid, errors = AgentConfig.validate()
        assert is_valid is True
        assert len(errors) == 0
    
    def test_all_parameters_accessible(self):
        """Test that config parameters are accessible."""
        config = AgentConfig()
        assert isinstance(config.DATA_LOADER_CHUNK_SIZE, int)
        assert isinstance(config.DEBUG, bool)
        assert isinstance(config.OPERATION_TIMEOUT_SECONDS, int)
        assert config.DATA_LOADER_CHUNK_SIZE > 0
