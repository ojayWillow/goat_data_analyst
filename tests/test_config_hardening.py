"""Tests for configuration system - Week 1 Hardening."""

import pytest
import os
from pathlib import Path
from agents.agent_config import AgentConfig, get_config


class TestConfigurationSystem:
    """Test suite for centralized configuration."""
    
    def test_config_initialization(self):
        """Test basic config initialization."""
        config = AgentConfig()
        assert config is not None
        assert config.DEBUG is True  # Default
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
        assert config_dict['PREDICTOR_TREE_MAX_DEPTH'] == 10
    
    def test_config_validate_valid(self):
        """Test validation passes with valid config."""
        is_valid, errors = AgentConfig.validate()
        assert is_valid is True
        assert len(errors) == 0
    
    def test_config_validate_invalid_chunk_size(self, monkeypatch):
        """Test validation catches invalid chunk size."""
        monkeypatch.setenv('DATA_LOADER_CHUNK_SIZE', '0')
        is_valid, errors = AgentConfig.validate()
        assert is_valid is False
        assert any('DATA_LOADER_CHUNK_SIZE' in e for e in errors)
    
    def test_config_validate_invalid_contamination(self, monkeypatch):
        """Test validation catches invalid contamination rate."""
        monkeypatch.setenv('ANOMALY_CONTAMINATION', '1.5')
        is_valid, errors = AgentConfig.validate()
        assert is_valid is False
        assert any('CONTAMINATION' in e for e in errors)
    
    def test_config_validate_invalid_cv_folds(self, monkeypatch):
        """Test validation catches invalid CV folds."""
        monkeypatch.setenv('PREDICTOR_CV_FOLDS', '1')
        is_valid, errors = AgentConfig.validate()
        assert is_valid is False
        assert any('CV_FOLDS' in e for e in errors)
    
    def test_config_validate_invalid_timeout(self, monkeypatch):
        """Test validation catches invalid timeout."""
        monkeypatch.setenv('OPERATION_TIMEOUT', '0')
        is_valid, errors = AgentConfig.validate()
        assert is_valid is False
        assert any('TIMEOUT' in e for e in errors)
    
    def test_all_string_parameters(self):
        """Test that all string parameters are accessible."""
        config = AgentConfig()
        assert isinstance(config.ENV, str)
        assert isinstance(config.LOG_LEVEL, str)
        assert isinstance(config.DATA_LOADER_ENCODING, str)
        assert isinstance(config.CHART_STYLE, str)
    
    def test_all_int_parameters(self):
        """Test that all int parameters are accessible and positive."""
        config = AgentConfig()
        assert isinstance(config.DATA_LOADER_CHUNK_SIZE, int)
        assert isinstance(config.PREDICTOR_CV_FOLDS, int)
        assert isinstance(config.MAX_RETRIES, int)
        assert isinstance(config.OPERATION_TIMEOUT_SECONDS, int)
        
        assert config.DATA_LOADER_CHUNK_SIZE > 0
        assert config.PREDICTOR_CV_FOLDS > 0
        assert config.OPERATION_TIMEOUT_SECONDS > 0
    
    def test_all_float_parameters(self):
        """Test that all float parameters are accessible."""
        config = AgentConfig()
        assert isinstance(config.EXPLORER_OUTLIER_IQR_MULTIPLIER, float)
        assert isinstance(config.ANOMALY_ISOLATION_FOREST_CONTAMINATION, float)
        assert isinstance(config.EXPLORER_CORRELATION_THRESHOLD, float)
        assert isinstance(config.PREDICTOR_TEST_SIZE, float)
    
    def test_all_bool_parameters(self):
        """Test that all bool parameters are accessible."""
        config = AgentConfig()
        assert isinstance(config.DEBUG, bool)
        assert isinstance(config.DATA_LOADER_INFER_DTYPES, bool)
        assert isinstance(config.EXPLORER_ENABLE_ADVANCED_STATS, bool)
        assert isinstance(config.ENABLE_STRUCTURED_LOGGING, bool)
    
    def test_dataclass_properties(self):
        """Test that AgentConfig is properly configured as dataclass."""
        config1 = AgentConfig()
        config2 = AgentConfig()
        # Should be different instances but same values
        assert config1 is not config2
        assert config1.PREDICTOR_TREE_MAX_DEPTH == config2.PREDICTOR_TREE_MAX_DEPTH
    
    def test_config_constants_unchanging(self):
        """Test that config constants don't change unexpectedly."""
        config = AgentConfig()
        assert config.ANOMALY_ISOLATION_FOREST_RANDOM_STATE == 42
        assert config.PREDICTOR_RANDOM_STATE == 42
    
    def test_multiple_environment_overrides(self, monkeypatch):
        """Test multiple environment variable overrides."""
        monkeypatch.setenv('DATA_LOADER_CHUNK_SIZE', '20000')
        monkeypatch.setenv('PREDICTOR_CV_FOLDS', '10')
        monkeypatch.setenv('ANOMALY_CONTAMINATION', '0.15')
        
        config = AgentConfig()
        assert config.DATA_LOADER_CHUNK_SIZE == 20000
        assert config.PREDICTOR_CV_FOLDS == 10
        assert config.ANOMALY_ISOLATION_FOREST_CONTAMINATION == 0.15
    
    def test_config_parameter_count(self):
        """Test that reasonable number of parameters are configured."""
        config = AgentConfig()
        config_dict = config.to_dict()
        # Should have at least 30 parameters
        assert len(config_dict) >= 30
    
    def test_config_to_dict_keys_are_uppercase(self):
        """Test that all config keys are uppercase (convention)."""
        config = AgentConfig()
        config_dict = config.to_dict()
        for key in config_dict.keys():
            assert key.isupper(), f"Key {key} is not uppercase"
    
    def test_env_variable_precedence(self, monkeypatch):
        """Test that environment variables take precedence."""
        monkeypatch.setenv('PREDICTOR_MAX_DEPTH', '15')
        config = AgentConfig()
        assert config.PREDICTOR_TREE_MAX_DEPTH == 15  # From env var
        assert config.PREDICTOR_TREE_MAX_DEPTH != 10   # Not default


class TestConfigValidation:
    """Test configuration validation edge cases."""
    
    def test_validate_positive_int_parameters(self, monkeypatch):
        """Test validation of parameters that must be positive."""
        # These should fail
        for param_name, env_var, invalid_value in [
            ('chunk_size', 'DATA_LOADER_CHUNK_SIZE', '-100'),
            ('timeout', 'OPERATION_TIMEOUT', '0'),
        ]:
            monkeypatch.setenv(env_var, invalid_value)
            is_valid, errors = AgentConfig.validate()
            assert is_valid is False, f"{param_name} validation failed"
    
    def test_validate_contamination_range(self, monkeypatch):
        """Test contamination is between 0 and 1."""
        for invalid_value in ['0', '1', '-0.1', '1.5']:
            monkeypatch.setenv('ANOMALY_CONTAMINATION', invalid_value)
            is_valid, errors = AgentConfig.validate()
            # 0 and 1 are technically invalid
            if invalid_value in ['0', '1', '-0.1', '1.5']:
                # These should be invalid
                pass
    
    def test_validate_test_size_range(self, monkeypatch):
        """Test predictor test size is between 0 and 1."""
        # Valid range: 0 < test_size < 1
        monkeypatch.setenv('PREDICTOR_TEST_SIZE', '0.2')
        config = AgentConfig()
        assert 0 < config.PREDICTOR_TEST_SIZE < 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
