# Local Test Setup - Orchestrator V3

**Quick Start Guide for Running Tests Locally**

---

## Step 1: Pull Latest Changes

```bash
# Navigate to your project directory
cd /path/to/goat_data_analyst

# Fetch latest from GitHub
git fetch origin main

# Pull the new commits
git pull origin main

# Verify new files
git log --oneline -5
```

**Should see:**
```
XXXXXXX Add Orchestrator V3 implementation...
YYYYYYY Add comprehensive Orchestrator V3 refactoring summary...
ZZZZZZZ Add comprehensive Orchestrator V3 implementation and testing checklist...
```

---

## Step 2: Verify Files Exist

```bash
# Check new files
ls -lah agents/orchestrator/orchestrator_v3_refactored.py
ls -lah ORCHESTRATOR_V3_REFACTOR_SUMMARY.md
ls -lah ORCHESTRATOR_V3_IMPLEMENTATION_CHECKLIST.md

# All should exist with reasonable file sizes
```

---

## Step 3: Create Test File

**Create:** `tests/test_orchestrator_v3.py`

```bash
# Create test file from checklist
touch tests/test_orchestrator_v3.py
```

**Add test content:**

```python
"""Unit tests for OrchestratorV3."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from agents.orchestrator.orchestrator_v3_refactored import (
    OrchestratorV3,
    QualityScore,
    TaskStatus,
    WorkflowStatus
)


class TestOrchestratorV3Initialization:
    """Test OrchestratorV3 initialization."""
    
    def test_init_success(self):
        """Test successful initialization."""
        orch = OrchestratorV3()
        
        assert orch.name == "OrchestratorV3"
        assert orch.version == "3.0-enhanced"
        assert orch.agent_registry is not None
        assert orch.data_manager is not None
        assert orch.task_router is not None
        assert orch.workflow_executor is not None
        assert orch.narrative_integrator is not None
        assert orch.error_intelligence is not None
        assert orch.quality_tracker is not None
        assert orch.execution_history == []
        assert orch.current_task is None
        assert orch.current_workflow is None


class TestQualityScore:
    """Test QualityScore class."""
    
    def test_init(self):
        """Test initialization."""
        qs = QualityScore()
        
        assert qs.tasks_successful == 0
        assert qs.tasks_failed == 0
        assert qs.tasks_partial == 0
        assert qs.total_rows_processed == 0
        assert qs.total_rows_failed == 0
        assert qs.errors_by_type == {}
    
    def test_quality_all_successful(self):
        """Test quality score when all tasks successful."""
        qs = QualityScore()
        qs.add_success()
        qs.add_success()
        qs.add_success()
        
        assert qs.get_score() == 1.0
    
    def test_quality_all_failed(self):
        """Test quality score when all tasks failed."""
        qs = QualityScore()
        qs.add_failure()
        qs.add_failure()
        qs.add_failure()
        
        assert qs.get_score() == 0.0
    
    def test_quality_mixed(self):
        """Test quality score with mixed results."""
        qs = QualityScore()
        qs.add_success()  # 1.0
        qs.add_success()  # 1.0
        qs.add_partial()  # 0.5
        
        # (1.0 + 1.0 + 0.5) / 3 = 0.833
        expected = round((1.0 + 1.0 + 0.5) / 3, 3)
        assert qs.get_score() == expected
    
    def test_add_error_type(self):
        """Test error type tracking."""
        qs = QualityScore()
        qs.add_error_type('null_value')
        qs.add_error_type('null_value')
        qs.add_error_type('type_error')
        
        assert qs.errors_by_type['null_value'] == 2
        assert qs.errors_by_type['type_error'] == 1
    
    def test_get_summary(self):
        """Test summary generation."""
        qs = QualityScore()
        qs.add_success()
        qs.add_failure()
        qs.add_partial()
        qs.add_error_type('error_1')
        qs.total_rows_processed = 100
        qs.total_rows_failed = 10
        
        summary = qs.get_summary()
        
        assert 'quality_score' in summary
        assert 'tasks' in summary
        assert 'data' in summary
        assert 'errors' in summary
        assert summary['tasks']['successful'] == 1
        assert summary['tasks']['failed'] == 1
        assert summary['tasks']['partial'] == 1
        assert summary['data']['rows_processed'] == 100
        assert summary['data']['rows_failed'] == 10


class TestAgentManagement:
    """Test agent management."""
    
    def test_register_agent_success(self):
        """Test successful agent registration."""
        orch = OrchestratorV3()
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        
        result = orch.register_agent('test_agent', mock_agent)
        
        assert result['success'] is True
        assert result['agent_name'] == 'test_agent'
        assert result['total_agents'] == 1
        assert result['quality_score'] == 1.0
        assert 'registered_at' in result
    
    def test_register_agent_invalid(self):
        """Test registration with invalid agent."""
        orch = OrchestratorV3()
        mock_agent = Mock(spec=[])  # No 'name' attribute
        
        with pytest.raises(Exception):  # ValidationError or OrchestratorError
            orch.register_agent('bad_agent', mock_agent)
    
    def test_get_agent(self):
        """Test retrieving agent."""
        orch = OrchestratorV3()
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        orch.register_agent('test_agent', mock_agent)
        
        retrieved = orch.get_agent('test_agent')
        assert retrieved == mock_agent
        
        not_found = orch.get_agent('nonexistent')
        assert not_found is None
    
    def test_list_agents(self):
        """Test listing agents."""
        orch = OrchestratorV3()
        
        mock_agent1 = Mock()
        mock_agent1.name = "Agent1"
        mock_agent2 = Mock()
        mock_agent2.name = "Agent2"
        
        orch.register_agent('agent1', mock_agent1)
        orch.register_agent('agent2', mock_agent2)
        
        result = orch.list_agents()
        
        assert 'agents' in result
        assert 'total' in result
        assert 'timestamp' in result
        assert result['total'] == 2
        assert 'agent1' in result['agents']
        assert 'agent2' in result['agents']


class TestDataManagement:
    """Test data management."""
    
    def test_cache_data(self):
        """Test caching data."""
        orch = OrchestratorV3()
        data = {'key': 'value'}
        
        result = orch.cache_data('test_key', data)
        
        assert result['success'] is True
        assert result['key'] == 'test_key'
        assert result['cache_size'] == 1
        assert 'cached_at' in result
    
    def test_get_cached_data(self):
        """Test retrieving cached data."""
        orch = OrchestratorV3()
        data = {'test': 'data'}
        orch.cache_data('test_key', data)
        
        retrieved = orch.get_cached_data('test_key')
        assert retrieved == data
        
        not_found = orch.get_cached_data('nonexistent')
        assert not_found is None
    
    def test_list_cached_data(self):
        """Test listing cached data."""
        orch = OrchestratorV3()
        orch.cache_data('key1', {'data': 1})
        orch.cache_data('key2', {'data': 2})
        
        result = orch.list_cached_data()
        
        assert 'keys' in result
        assert 'count' in result
        assert 'timestamp' in result
        assert result['count'] == 2
        assert 'key1' in result['keys']
        assert 'key2' in result['keys']
    
    def test_clear_cache(self):
        """Test clearing cache."""
        orch = OrchestratorV3()
        orch.cache_data('key1', {'data': 1})
        orch.cache_data('key2', {'data': 2})
        
        result = orch.clear_cache()
        
        assert result['success'] is True
        assert 'cleared_at' in result
        
        # Verify cache is empty
        assert orch.get_cached_data('key1') is None
        assert orch.get_cached_data('key2') is None


class TestHealthReporting:
    """Test health reporting."""
    
    def test_get_status(self):
        """Test quick status."""
        orch = OrchestratorV3()
        
        status = orch.get_status()
        
        assert 'name' in status
        assert 'version' in status
        assert 'status' in status
        assert 'health_score' in status
        assert 'agents_registered' in status
        assert 'cache_items' in status
        assert 'quality_score' in status
        assert 'timestamp' in status
        assert status['name'] == 'OrchestratorV3'
        assert status['version'] == '3.0-enhanced'
    
    def test_get_health_report(self):
        """Test comprehensive health report."""
        orch = OrchestratorV3()
        
        report = orch.get_health_report()
        
        assert 'overall_health' in report
        assert 'status' in report
        assert 'timestamp' in report
        assert 'agents' in report
        assert 'cache' in report
        assert 'execution' in report
        assert 'errors' in report
        assert 'quality' in report
        
        # Health should be 100 initially
        assert report['overall_health'] == 100.0
        assert report['status'] == 'healthy'
    
    def test_health_status_labels(self):
        """Test health status labels."""
        orch = OrchestratorV3()
        
        # Test internal method
        assert orch._get_health_status(100) == 'healthy'
        assert orch._get_health_status(80) == 'healthy'
        assert orch._get_health_status(79) == 'degraded'
        assert orch._get_health_status(50) == 'degraded'
        assert orch._get_health_status(49) == 'critical'
        assert orch._get_health_status(0) == 'critical'


class TestLifecycle:
    """Test lifecycle methods."""
    
    def test_reset(self):
        """Test reset."""
        orch = OrchestratorV3()
        
        # Add some data
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        orch.register_agent('test', mock_agent)
        orch.cache_data('key', 'value')
        
        # Reset
        result = orch.reset()
        
        assert result['success'] is True
        assert 'reset_at' in result
        
        # Verify cache cleared but agent kept
        assert orch.get_cached_data('key') is None
        assert orch.get_agent('test') is not None
    
    def test_shutdown(self):
        """Test shutdown."""
        orch = OrchestratorV3()
        
        result = orch.shutdown()
        
        assert result['success'] is True
        assert 'shutdown_at' in result
        assert 'final_health_score' in result
        assert 'total_tasks_executed' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

## Step 4: Install Dependencies

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Verify installations
pytest --version
```

---

## Step 5: Run Tests

### Quick Test (5 seconds)
```bash
pytest tests/test_orchestrator_v3.py -v --tb=short
```

### Full Test with Coverage (10-15 seconds)
```bash
pytest tests/test_orchestrator_v3.py \
  --cov=agents.orchestrator.orchestrator_v3_refactored \
  --cov-report=html \
  --cov-report=term-missing \
  -v
```

### Run Specific Test
```bash
# Run only initialization tests
pytest tests/test_orchestrator_v3.py::TestOrchestratorV3Initialization -v

# Run only quality score tests
pytest tests/test_orchestrator_v3.py::TestQualityScore -v

# Run only health tests
pytest tests/test_orchestrator_v3.py::TestHealthReporting -v
```

---

## Step 6: Check Results

### Expected Output
```
========================= test session starts =========================
platform darwin -- Python 3.9.0, pytest-6.2.4, py-1.10.0
cachedir: .pytest_cache
rootdir: /path/to/goat_data_analyst
collected 25 items

tests/test_orchestrator_v3.py::TestOrchestratorV3Initialization::test_init_success PASSED
tests/test_orchestrator_v3.py::TestQualityScore::test_init PASSED
tests/test_orchestrator_v3.py::TestQualityScore::test_quality_all_successful PASSED
...
========================= 25 passed in 0.45s =========================
```

### Coverage Report
```
Name                                              Stmts   Miss  Cover
------------------------------------------------------------------------
orchestrator_v3_refactored.py                     XXX     X   XX%
------------------------------------------------------------------------
TOTAL                                              XXX     X   XX%
```

**To view HTML coverage report:**
```bash
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
# or
firefox htmlcov/index.html  # Linux
```

---

## Step 7: Troubleshooting

### Import Error: No module named 'agents'
```bash
# Make sure you're in project root
cd /path/to/goat_data_analyst
pwd  # should show full path to project

# Add to PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:/path/to/goat_data_analyst"
```

### ModuleNotFoundError: No module named 'core'
```bash
# Install project in development mode
pip install -e .

# Or run pytest from project root
cd /path/to/goat_data_analyst
pytest tests/test_orchestrator_v3.py
```

### Tests fail with import errors
```bash
# Check that new files exist
ls -la agents/orchestrator/orchestrator_v3_refactored.py
ls -la tests/test_orchestrator_v3.py

# Verify git pull succeeded
git status
```

---

## Step 8: Run Full Test Suite

```bash
# After basic tests pass, run full suite
pytest tests/test_orchestrator_v3.py tests/test_orchestrator_v3_integration.py -v

# With coverage
pytest tests/test_orchestrator_v3*.py \
  --cov=agents.orchestrator.orchestrator_v3_refactored \
  --cov-report=term-missing \
  -v
```

---

## Commands Summary

```bash
# Pull changes
git pull origin main

# Verify files
ls -lah agents/orchestrator/orchestrator_v3_refactored.py

# Install test deps
pip install pytest pytest-cov

# Quick test
pytest tests/test_orchestrator_v3.py -v

# Full test with coverage
pytest tests/test_orchestrator_v3.py --cov=agents.orchestrator.orchestrator_v3_refactored -v

# View coverage
open htmlcov/index.html
```

---

**Status:** Ready to test locally  
**Estimated Duration:** 5-15 minutes  
**Test Cases:** 25+  
**Expected Coverage:** 90%+
