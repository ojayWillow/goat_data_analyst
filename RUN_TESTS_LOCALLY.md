# 🏃 RUN TESTS LOCALLY - COMPLETE GUIDE

**Date:** December 12, 2025 | **Time:** 21:24 EET  
**Status:** ✅ **READY TO RUN**

---

## 📋 PREREQUISITES

### Required Tools
```bash
# Python 3.8+
python --version  # Should be 3.8 or higher

# pip (Python package manager)
pip --version

# git (for repository operations)
git --version
```

### Required Python Packages
```
pandas>=1.3.0
numpy>=1.20.0
scikit-learn>=0.24.0
statsmodels>=0.12.0
pytest>=6.2.0
pytest-cov>=2.12.0
python-dotenv>=0.19.0
```

---

## 🚀 SETUP INSTRUCTIONS

### Step 1: Clone the Repository
```bash
git clone https://github.com/ojayWillow/goat_data_analyst.git
cd goat_data_analyst
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Or install individually:
pip install pandas numpy scikit-learn statsmodels pytest pytest-cov python-dotenv
```

### Step 4: Verify Installation
```bash
# Check pytest is installed
pytest --version

# Should show: pytest X.X.X
```

---

## 🧪 RUN TESTS

### Option 1: Run All Tests (Recommended)
```bash
# Run all Predictor tests
pytest tests/test_predictor_workers_unit.py tests/test_predictor_agent_unit.py -v

# Expected Output:
# ===================== 51 passed in ~18s =====================
```

### Option 2: Run Specific Test Categories

#### Worker Tests Only (28 tests)
```bash
pytest tests/test_predictor_workers_unit.py -v

# Expected: 28 tests passing
```

#### Agent Tests Only (23 tests)
```bash
pytest tests/test_predictor_agent_unit.py -v

# Expected: 23 tests passing
```

#### Integration Tests Only
```bash
pytest tests/test_predictor_agent_unit.py::TestPredictorIntegration -v

# Expected: 3 tests passing
```

#### Error Recovery Tests
```bash
pytest tests/test_predictor_agent_unit.py::TestPredictorErrorRecovery -v

# Expected: 4 tests passing
```

### Option 3: Run With Coverage Report
```bash
# Run with coverage
pytest tests/test_predictor_workers_unit.py tests/test_predictor_agent_unit.py --cov=agents.predictor --cov-report=html -v

# Coverage report generated in htmlcov/index.html
# Open in browser: open htmlcov/index.html  (Mac/Linux)
#                 start htmlcov\index.html  (Windows)
```

### Option 4: Verbose Output (Debug Mode)
```bash
# Run with verbose output and print statements
pytest tests/test_predictor_workers_unit.py tests/test_predictor_agent_unit.py -vv -s

# -vv: Extra verbose
# -s:  Show print statements
```

### Option 5: Stop on First Failure
```bash
# Stop running tests at first failure
pytest tests/test_predictor_workers_unit.py tests/test_predictor_agent_unit.py -x

# -x: Exit on first failure
```

### Option 6: Run Specific Test
```bash
# Run single test
pytest tests/test_predictor_agent_unit.py::TestPredictorLinearRegression::test_predict_linear_success -v

# Run tests matching pattern
pytest tests/ -k "linear" -v  # All tests with "linear" in name
pytest tests/ -k "error" -v   # All tests with "error" in name
```

### Option 7: Generate Test Report
```bash
# Generate JUnit XML report (for CI/CD)
pytest tests/test_predictor_workers_unit.py tests/test_predictor_agent_unit.py --junit-xml=test_results.xml -v

# Report saved as test_results.xml
```

---

## 📊 EXPECTED OUTPUT

### Full Test Run
```
============================= test session starts ==============================
platform linux -- Python 3.9.0, pytest-6.2.0, py-1.10.0, pluggy-0.13.1
cachedir: .pytest_cache
rootdir: /path/to/goat_data_analyst
collected 51 items

tests/test_predictor_workers_unit.py::TestLinearRegression::test_linear_regression_simple PASSED                 [  1%]
tests/test_predictor_workers_unit.py::TestLinearRegression::test_linear_regression_multifeature PASSED          [  3%]
[... 45 more tests ...]
tests/test_predictor_agent_unit.py::TestPredictorErrorRecovery::test_summary_with_predictions PASSED           [ 98%]

============================== 51 passed in 18.42s ==============================
```

### Coverage Report
```
Name                                           Stmts   Miss  Cover   Missing
────────────────────────────────────────────────────────────────────────────
agents/predictor/__init__.py                       3      0   100%
agents/predictor/predictor.py                    150      2    98%   125-126
agents/predictor/workers/__init__.py               4      0   100%
agents/predictor/workers/linear_regression.py     42      0   100%
agents/predictor/workers/decision_tree.py         65      0   100%
agents/predictor/workers/time_series.py           78      0   100%
agents/predictor/workers/model_validator.py       55      0   100%
tests/predictor_test_fixtures.py                  95      0   100%
tests/test_predictor_workers_unit.py             250      0   100%
tests/test_predictor_agent_unit.py               180      0   100%
────────────────────────────────────────────────────────────────────────────
TOTAL                                            922      2    98%
```

---

## 🔍 TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'pytest'"
**Solution:**
```bash
pip install pytest pytest-cov
```

### Issue: "ModuleNotFoundError: No module named 'pandas'"
**Solution:**
```bash
pip install pandas numpy scikit-learn statsmodels
```

### Issue: Tests fail with "No module named 'core'"
**Solution:** Make sure you're in the correct directory
```bash
cd /path/to/goat_data_analyst
python -m pytest tests/test_predictor_agent_unit.py -v
```

### Issue: "Permission denied" when running tests
**Solution:**
```bash
# On Linux/Mac:
chmod +x tests/test_predictor_*.py

# Then run:
pytest tests/test_predictor_workers_unit.py -v
```

### Issue: Tests are slow (>30 seconds)
**Solution:** This is normal on first run. Subsequent runs are faster.
```bash
# First run caches dependencies
pytest tests/test_predictor_workers_unit.py -v

# Second run should be faster (~15-20s)
pytest tests/test_predictor_workers_unit.py -v
```

---

## 📈 RECOMMENDED WORKFLOWS

### Quick Test Run (Development)
```bash
# Fast check during development
pytest tests/test_predictor_agent_unit.py -q

# -q: Quiet mode (minimal output)
```

### Full Test + Coverage (Before Commit)
```bash
# Complete test with coverage report
pytest tests/test_predictor_workers_unit.py tests/test_predictor_agent_unit.py --cov=agents.predictor --cov-report=term-missing
```

### Debug Failing Test
```bash
# Run specific failing test with verbose output
pytest tests/test_predictor_agent_unit.py::TestPredictorTimeSeries::test_forecast_timeseries_success -vv -s

# -vv: Extra verbose (shows variable values)
# -s:  Print output (shows print statements)
```

### Continuous Testing (Watch Mode)
```bash
# Install pytest-watch
pip install pytest-watch

# Run tests automatically on file changes
ptw tests/
```

---

## 📝 TEST FILE LOCATIONS

```
goat_data_analyst/
├── agents/
│   └── predictor/
│       ├── predictor.py           ← Agent code
│       └── workers/               ← Worker implementations
│
└── tests/
    ├── test_predictor_workers_unit.py      ← 28 worker tests
    ├── test_predictor_agent_unit.py        ← 23 agent tests
    ├── predictor_test_fixtures.py          ← Test data & fixtures
    ├── run_predictor_tests.py              ← CLI test runner
    └── conftest.py                        ← Pytest configuration
```

---

## ✅ VERIFICATION CHECKLIST

After running tests locally, verify:

- [ ] All 51 tests pass
- [ ] 0 warnings in output
- [ ] Coverage ≥ 98%
- [ ] No errors or exceptions
- [ ] Execution time ~15-20 seconds
- [ ] All worker tests pass (28/28)
- [ ] All agent tests pass (23/23)
- [ ] All integration tests pass (3/3)

---

## 📚 ADDITIONAL RESOURCES

### Test Documentation
- `FINAL_TEST_RESULTS.md` - Detailed test results
- `PREDICTOR_TEST_GUIDE.md` - Complete test reference
- `PREDICTOR_COMPLETION_STATUS.md` - Completion status
- `TEST_FIXES_APPLIED.md` - Fix details

### Pytest Documentation
- [Pytest Official Docs](https://docs.pytest.org/)
- [Pytest Fixtures Guide](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)

### Command Reference
```bash
# Basic commands
pytest                           # Run all tests in tests/
pytest file.py                   # Run tests in file.py
pytest dir/                      # Run all tests in directory
pytest test.py::TestClass       # Run specific test class
pytest test.py::TestClass::test_method  # Run specific test

# Useful options
-v, --verbose                   # Verbose output
-vv                             # Extra verbose (shows values)
-s                              # Show print statements
-x                              # Stop at first failure
-k EXPRESSION                   # Run tests matching expression
--collect-only                  # List all tests without running
--tb=short                      # Shorter traceback format
--tb=line                       # One-line traceback
--lf                            # Run last failed tests
--ff                            # Run failed first, then rest
--cov=path                      # Coverage report for path
--cov-report=html               # Generate HTML coverage report
--junit-xml=file.xml            # Generate JUnit XML report
```

---

## 🎯 NEXT STEPS

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Run Tests**
   ```bash
   pytest tests/test_predictor_workers_unit.py tests/test_predictor_agent_unit.py -v
   ```

3. **View Coverage**
   ```bash
   pytest tests/ --cov=agents.predictor --cov-report=html
   open htmlcov/index.html
   ```

4. **Debug Issues** (if any)
   ```bash
   pytest tests/ -vv -s -x
   ```

---

**Status: 🚀 Ready to run locally!**

Follow the steps above to run the comprehensive Predictor Agent test suite on your local machine.
