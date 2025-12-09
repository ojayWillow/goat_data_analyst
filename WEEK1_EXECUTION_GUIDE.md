# 🚀 Week 1 Hardening - Quick Execution Guide

**Status:** 🟨 IN PROGRESS
**Completed Files:** 4
**Completed Tests:** 65+
**GitHub Commits:** 4

---

## 🎯 What Just Happened?

We just completed **MONDAY of Week 1** in just ~2 hours! Here's what we built:

### ✅ Files Created (4)

1. **`agents/agent_config.py`** - Central configuration system
   - 40+ configurable parameters
   - Environment variable overrides
   - Configuration validation
   - JSON import/export

2. **`core/error_recovery.py`** - Error recovery framework
   - Retry logic with exponential backoff
   - Timeout protection
   - Fallback values
   - Decorators: `@retry_on_error`, `@with_fallback`

3. **`tests/test_config_hardening.py`** - Configuration tests
   - 30+ comprehensive test cases
   - All tests PASSING ✅

4. **`tests/test_error_recovery.py`** - Error recovery tests
   - 35+ comprehensive test cases
   - All tests PASSING ✅

---

## 🌟 Quick Start - How to Use

### 1. Configuration System

```python
from agents.agent_config import AgentConfig, get_config

# Get configuration
config = get_config()

# Access any parameter
max_depth = config.PREDICTOR_TREE_MAX_DEPTH  # Default: 10
timeout = config.OPERATION_TIMEOUT_SECONDS   # Default: 30
log_level = config.LOG_LEVEL                 # Default: 'INFO'

# Or use .get() method
value = AgentConfig.get('PREDICTOR_TREE_MAX_DEPTH')

# Override via environment variables
# export PREDICTOR_MAX_DEPTH=15
# export OPERATION_TIMEOUT=60

# Validate configuration
is_valid, errors = AgentConfig.validate()
if not is_valid:
    for error in errors:
        print(f"Error: {error}")

# Get all parameters as dictionary
all_params = AgentConfig().to_dict()
```

### 2. Error Recovery

```python
from core.error_recovery import (
    retry_on_error,
    with_fallback,
    ErrorRecoveryStrategy
)

# Method 1: Using decorator
@retry_on_error(max_attempts=3, backoff=2)
def load_data(filepath):
    return pd.read_csv(filepath)

data = load_data('data.csv')  # Retries automatically on error

# Method 2: Using with_fallback decorator
@with_fallback(fallback_value=[])
def get_items():
    return fetch_from_api()

items = get_items()  # Returns [] if fetch fails

# Method 3: Direct usage
result = ErrorRecoveryStrategy.retry(
    func=lambda: risky_operation(),
    max_attempts=3,
    backoff=2,
    timeout=30,
    fallback="default_value"
)

# Method 4: With fallback value
result = ErrorRecoveryStrategy.with_fallback(
    func=lambda: risky_operation(),
    fallback_value="fallback"
)
```

### 3. Running Tests

```bash
# Run all configuration tests
pytest tests/test_config_hardening.py -v

# Run all error recovery tests
pytest tests/test_error_recovery.py -v

# Run specific test
pytest tests/test_config_hardening.py::TestConfigurationSystem::test_config_defaults -v

# Run with coverage
pytest tests/test_config_hardening.py --cov=agents.agent_config --cov=core.error_recovery -v
```

---

## 📚 Configuration Parameters Reference

### Environment Configuration

```python
ENV = 'development'              # 'development' or 'production'
DEBUG = True                     # Enable debug mode
LOG_LEVEL = 'INFO'              # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
```

### Data Loader Configuration

```python
DATA_LOADER_CHUNK_SIZE = 10000                 # Rows per chunk
DATA_LOADER_ENCODING = 'utf-8'                 # File encoding
DATA_LOADER_MAX_FILE_SIZE_MB = 500             # Max file size in MB
DATA_LOADER_INFER_DTYPES = True                # Auto infer data types
```

### Explorer Configuration

```python
EXPLORER_OUTLIER_IQR_MULTIPLIER = 1.5          # IQR threshold
EXPLORER_MIN_SAMPLES_CATEGORICAL = 10          # Min samples for categorical
EXPLORER_CORRELATION_THRESHOLD = 0.7           # Strong correlation threshold
EXPLORER_ENABLE_ADVANCED_STATS = False         # Advanced statistical tests
```

### Anomaly Detector Configuration

```python
ANOMALY_ISOLATION_FOREST_CONTAMINATION = 0.1   # Contamination rate
ANOMALY_ISOLATION_FOREST_N_ESTIMATORS = 100    # Number of estimators
ANOMALY_STATISTICAL_SIGMA = 3.0                # Sigma for statistical detection
```

### Visualizer Configuration

```python
CHART_DEFAULT_HEIGHT = 400                     # Chart height in pixels
CHART_DEFAULT_WIDTH = 600                      # Chart width in pixels
CHART_DPI = 100                                # DPI for exports
CHART_STYLE = 'seaborn-v0_8-darkgrid'         # Matplotlib style
```

### Predictor Configuration

```python
PREDICTOR_TREE_MAX_DEPTH = 10                  # Max tree depth
PREDICTOR_CV_FOLDS = 5                         # Cross-validation folds
PREDICTOR_TEST_SIZE = 0.2                      # Test set size
PREDICTOR_RANDOM_STATE = 42                    # Random seed
```

### Performance & Reliability Configuration

```python
OPERATION_TIMEOUT_SECONDS = 30                 # Operation timeout
MAX_RETRIES = 3                                # Max retry attempts
RETRY_BACKOFF_FACTOR = 2                       # Exponential backoff (2^n)
```

---

## 🔬 How Configuration Works

### Environment Variable Override

1. **Default value in code:**
   ```python
   PREDICTOR_TREE_MAX_DEPTH = 10
   ```

2. **Override via environment variable:**
   ```bash
   export PREDICTOR_MAX_DEPTH=15
   ```

3. **Access in code:**
   ```python
   config = AgentConfig()
   print(config.PREDICTOR_TREE_MAX_DEPTH)  # Prints: 15
   ```

### Environment Variable Patterns

All environment variables follow the pattern:
```
[PARAMETER_NAME] = [ENV_VAR_NAME]
PREDICTOR_TREE_MAX_DEPTH = PREDICTOR_MAX_DEPTH
OPERATION_TIMEOUT_SECONDS = OPERATION_TIMEOUT
ANOMALY_ISOLATION_FOREST_CONTAMINATION = ANOMALY_CONTAMINATION
```

---

## 🛡️ Error Recovery Patterns

### Pattern 1: Retry with Exponential Backoff

```python
@retry_on_error(max_attempts=3, backoff=2)
def load_csv(filepath):
    return pd.read_csv(filepath)

# Attempt 1: Immediately
# Attempt 2: Wait 2^0 = 1 second, retry
# Attempt 3: Wait 2^1 = 2 seconds, retry
# If all fail: Raise RecoveryError
```

### Pattern 2: Retry with Fallback

```python
@retry_on_error(max_attempts=3, fallback=[])
def fetch_items():
    return api.get_items()

# If all retries fail, return empty list []
```

### Pattern 3: Fallback Only (No Retry)

```python
@with_fallback(fallback_value=None)
def risky_operation():
    return compute_something()

# On error, return None (no retries)
```

### Pattern 4: Direct Usage

```python
result = ErrorRecoveryStrategy.retry(
    func=lambda: pd.read_csv('data.csv'),
    max_attempts=3,
    backoff=2,
    timeout=30,
    fallback=None
)
```

---

## 🚫 Example Integration

Here's how these systems work together in practice:

```python
from agents.agent_config import AgentConfig
from core.error_recovery import retry_on_error, ErrorRecoveryStrategy
from core.logger import get_logger

logger = get_logger(__name__)
config = AgentConfig()

# Example: Loading data with configuration and error recovery
@retry_on_error(
    max_attempts=config.MAX_RETRIES,
    backoff=config.RETRY_BACKOFF_FACTOR,
    timeout=config.OPERATION_TIMEOUT_SECONDS,
    fallback=None
)
def load_data_resilient(filepath):
    """Load data with automatic retry and timeout protection."""
    # Use configured chunk size
    chunk_size = config.DATA_LOADER_CHUNK_SIZE
    encoding = config.DATA_LOADER_ENCODING
    
    logger.info(f"Loading {filepath} with chunk_size={chunk_size}")
    return pd.read_csv(
        filepath,
        chunksize=chunk_size,
        encoding=encoding
    )

# Usage
try:
    data = load_data_resilient('large_dataset.csv')
    logger.info(f"Successfully loaded data")
except Exception as e:
    logger.error(f"Failed to load data: {e}")
    # Handle error appropriately
```

---

## 📋 Running the Tests

```bash
# Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests
pytest tests/test_config_hardening.py -v
pytest tests/test_error_recovery.py -v

# Run with coverage
pytest tests/test_config_hardening.py tests/test_error_recovery.py \
  --cov=agents.agent_config \
  --cov=core.error_recovery \
  --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows
```

---

## 💼 What's Next?

### Immediate (Next 2-3 hours):

1. **Logging & Observability System**
   - JSON structured logging
   - Performance metrics collection
   - Audit trail support
   - Tests (15+ cases)

2. **Validation Framework**
   - Input validation decorators
   - Output validation
   - Type checking
   - Tests (20+ cases)

### By End of Week:

3. **Performance Benchmarks**
   - Data Loader: 1M rows in < 5 seconds
   - Explorer: 1M rows in < 3 seconds
   - Anomaly Detector: 1M rows in < 10 seconds
   - Aggregator: 1M rows in < 2 seconds
   - Predictor: 100K rows with 100 features in < 5 seconds
   - Visualizer: 100K points in < 2 seconds

4. **Integration Tests**
   - Configuration + Error Recovery
   - Configuration + Logging
   - Full system validation

5. **Documentation**
   - Configuration guide
   - Error handling guide
   - Logging guide
   - Validation guide

---

## 🚀 Quick Commands

```bash
# Check configuration
python -c "from agents.agent_config import AgentConfig; \
           config = AgentConfig(); \
           print(f'TIMEOUT: {config.OPERATION_TIMEOUT_SECONDS}s'); \
           print(f'MAX_RETRIES: {config.MAX_RETRIES}'); \
           is_valid, errors = AgentConfig.validate(); \
           print(f'Config valid: {is_valid}')"

# Run quick test
pytest tests/test_config_hardening.py::TestConfigurationSystem::test_config_defaults -v

# Check all tests pass
pytest tests/test_config_hardening.py tests/test_error_recovery.py --tb=short

# Get test count
pytest tests/test_config_hardening.py tests/test_error_recovery.py --collect-only | grep "test_" | wc -l
```

---

## 🛶 Known Issues & Workarounds

**None so far!** All tests passing, all systems operational.

---

## 🏁 Success Criteria (Week 1)

### ✅ Completed
- ✅ Configuration system implemented
- ✅ Error recovery framework implemented
- ✅ 65+ test cases created and passing
- ✅ Code is production-ready

### 🟨 In Progress (Tue-Wed)
- 🟨 Logging & observability system
- 🟨 Validation framework

### ⬜ Remaining (Wed-Fri)
- ⬜ Performance benchmarks
- ⬜ Integration tests
- ⬜ Final documentation

---

## 🌟 Pro Tips

1. **Environment Variables Override Everything**
   ```bash
   export PREDICTOR_MAX_DEPTH=20
   export OPERATION_TIMEOUT=60
   python your_script.py  # Uses overridden values
   ```

2. **Decorator Ordering Matters**
   ```python
   # This works:
   @with_fallback(fallback_value="fallback")
   @retry_on_error(max_attempts=3)
   def func():
       pass
   
   # Outer decorator (with_fallback) is applied first
   ```

3. **Validate Config Early**
   ```python
   is_valid, errors = AgentConfig.validate()
   assert is_valid, f"Invalid config: {errors}"
   ```

4. **Use Context in Retries**
   ```python
   ErrorRecoveryStrategy.retry(
       func,
       context="loading_user_data"  # Appears in logs
   )
   ```

---

## 📑 References

**Files Modified/Created:**
- `agents/agent_config.py` - Configuration system
- `core/error_recovery.py` - Error recovery
- `tests/test_config_hardening.py` - Config tests
- `tests/test_error_recovery.py` - Recovery tests
- `HARDENING_WEEK1_PROGRESS.md` - Progress tracker
- `WEEK1_EXECUTION_GUIDE.md` - This file

**GitHub Commits:**
1. [feat: Configuration system](https://github.com/ojayWillow/goat_data_analyst/commit/0952dab)
2. [feat: Error recovery](https://github.com/ojayWillow/goat_data_analyst/commit/7c9bdc4)
3. [test: Config tests](https://github.com/ojayWillow/goat_data_analyst/commit/78a0830)
4. [test: Recovery tests](https://github.com/ojayWillow/goat_data_analyst/commit/0b29352)

---

**Status:** 🟨 ON TRACK
**Next Update:** End of Tuesday (Logging & Validation complete)
**Target Completion:** End of Friday (Week 1 complete)
