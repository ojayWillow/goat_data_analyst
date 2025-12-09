"""Integration tests for Week 1 hardening systems.

Verifies that Configuration, Error Recovery, Logging, and Validation
work together seamlessly.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from agents.agent_config import AgentConfig
from core.error_recovery import retry_on_error, ErrorRecoveryStrategy
from core.structured_logger import get_structured_logger, log_operation
from core.validators import validate_input, validate_output


class TestConfigurationIntegration:
    """Test configuration system integration."""
    
    def test_config_with_error_recovery(self):
        """Test using config values with error recovery."""
        config = AgentConfig()
        call_count = [0]
        
        @retry_on_error(
            max_attempts=config.MAX_RETRIES,
            backoff=config.RETRY_BACKOFF_FACTOR
        )
        def operation():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError('Temporary error')
            return 'success'
        
        result = operation()
        assert result == 'success'
    
    def test_config_timeout_with_recovery(self):
        """Test timeout configuration with error recovery."""
        config = AgentConfig()
        
        def quick_operation():
            return 'done'
        
        result = ErrorRecoveryStrategy.retry(
            quick_operation,
            max_attempts=config.MAX_RETRIES,
            timeout=config.OPERATION_TIMEOUT_SECONDS
        )
        assert result == 'done'
    
    def test_config_validation_on_init(self):
        """Test that config validates on initialization."""
        is_valid, errors = AgentConfig.validate()
        assert is_valid
        assert len(errors) == 0


class TestLoggingIntegration:
    """Test logging system integration."""
    
    def test_logging_with_error_recovery(self):
        """Test logging error recovery attempts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('test_recovery', tmpdir)
            
            call_count = [0]
            
            @retry_on_error(max_attempts=2, backoff=1)
            def risky_operation():
                call_count[0] += 1
                logger.info('Attempt', extra={'attempt': call_count[0]})
                if call_count[0] < 2:
                    raise ValueError('Temporary')
                return 'success'
            
            result = risky_operation()
            assert result == 'success'
            
            metrics = logger.get_metrics()
            assert metrics['total_logs'] > 0
    
    def test_operation_logging(self):
        """Test operation context logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('operation_test', tmpdir)
            
            with logger.operation('database_query', {'table': 'users'}):
                result = {'count': 42}
            
            metrics = logger.get_metrics()
            assert 'database_query' in metrics['operations']
            assert metrics['operations']['database_query'][0]['status'] == 'success'


class TestValidationIntegration:
    """Test validation system integration."""
    
    def test_validate_input_with_logging(self):
        """Test input validation with logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('validation_test', tmpdir)
            
            @validate_input({'data': 'dataframe', 'count': 'numeric'})
            def process_data(data, count):
                logger.info('Processing data', extra={'rows': len(data), 'count': count})
                return len(data) * count
            
            df = pd.DataFrame({'a': [1, 2, 3]})
            result = process_data(df, 2)
            assert result == 6
    
    def test_validate_with_error_recovery(self):
        """Test validation with error recovery."""
        call_count = [0]
        
        @validate_output('dataframe')
        @retry_on_error(max_attempts=2, fallback=None, backoff=1)
        def get_data():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError('Retry me')
            return pd.DataFrame({'a': [1, 2, 3]})
        
        result = get_data()
        assert isinstance(result, pd.DataFrame)


class TestFullStackIntegration:
    """Test all systems working together."""
    
    def test_complete_pipeline(self):
        """Test complete pipeline with all systems."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AgentConfig()
            logger = get_structured_logger('full_stack', tmpdir)
            
            @validate_output('dataframe')
            @validate_input({'rows': 'numeric', 'cols': 'numeric'})
            @retry_on_error(max_attempts=config.MAX_RETRIES)
            def create_data(rows, cols):
                with logger.operation('create', {'rows': rows, 'cols': cols}):
                    data = {f'col_{i}': np.random.randn(rows) for i in range(cols)}
                    df = pd.DataFrame(data)
                    logger.info('Data created', extra={'shape': str(df.shape)})
                    return df
            
            result = create_data(1000, 10)
            assert isinstance(result, pd.DataFrame)
            assert result.shape == (1000, 10)
            
            metrics = logger.get_metrics()
            assert metrics['total_logs'] >= 2
    
    def test_data_processing_workflow(self):
        """Test realistic data processing workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AgentConfig()
            logger = get_structured_logger('workflow', tmpdir)
            
            @retry_on_error(max_attempts=config.MAX_RETRIES)
            @validate_output('dataframe')
            def load_data():
                with logger.operation('load_data'):
                    return pd.DataFrame({
                        'id': range(100),
                        'value': np.random.randn(100)
                    })
            
            @validate_input({'data': 'dataframe'})
            @validate_output('dataframe')
            def clean_data(data):
                with logger.operation('clean', {'input_rows': len(data)}):
                    return data.dropna()
            
            @validate_input({'data': 'dataframe'})
            def analyze_data(data):
                with logger.operation('analyze', {'rows': len(data)}):
                    stats = {
                        'mean': data['value'].mean(),
                        'std': data['value'].std(),
                    }
                    logger.info('Analysis complete', extra=stats)
                    return stats
            
            df = load_data()
            df_clean = clean_data(df)
            stats = analyze_data(df_clean)
            
            assert len(df) == 100
            assert 'mean' in stats
            
            metrics = logger.get_metrics()
            assert 'load_data' in metrics['operations']
            assert 'clean' in metrics['operations']


class TestErrorHandlingScenarios:
    """Test realistic error handling scenarios."""
    
    def test_file_not_found_recovery(self):
        """Test recovery from file not found."""
        @retry_on_error(max_attempts=2, fallback=None, backoff=1)
        def load_file(path):
            return pd.read_csv(path)
        
        result = load_file('/nonexistent/file.csv')
        assert result is None
    
    def test_error_with_logging_and_config(self):
        """Test error handling with logging and config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AgentConfig()
            logger = get_structured_logger('errors', tmpdir)
            
            attempt = [0]
            
            @retry_on_error(
                max_attempts=config.MAX_RETRIES,
                backoff=config.RETRY_BACKOFF_FACTOR
            )
            def flaky_operation():
                attempt[0] += 1
                logger.info('Operation attempt', extra={'attempt': attempt[0]})
                if attempt[0] < 2:
                    raise RuntimeError('Temporary failure')
                return 'success'
            
            result = flaky_operation()
            assert result == 'success'
            
            metrics = logger.get_metrics()
            assert metrics['total_logs'] >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
