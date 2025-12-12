# Local Test Setup & Execution Guide

**Last Updated:** December 12, 2025  
**Status:** Complete  

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Setup](#environment-setup)
3. [Installation Steps](#installation-steps)
4. [Running Tests](#running-tests)
5. [Troubleshooting](#troubleshooting)
6. [Expected Results](#expected-results)
7. [Test Output Interpretation](#test-output-interpretation)

---

## 🚀 Quick Start

### TL;DR - 5 Minutes

```bash
# Clone repo (if not already done)
git clone https://github.com/ojayWillow/goat_data_analyst.git
cd goat_data_analyst

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pandas openpyxl pyarrow

# Run tests
python tests/run_dataloader_tests.py
```

---

## 🔧 Environment Setup

### System Requirements

**Minimum:**
- Python 3.8+
- 2GB RAM
- 500MB disk space
- pip/conda package manager

**Recommended:**
- Python 3.10+
- 4GB+ RAM
- 1GB disk space
- Virtual environment manager (venv/conda)

### Platform-Specific Instructions

#### **Windows**

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt
```

#### **macOS/Linux**

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 📦 Installation Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/ojayWillow/goat_data_analyst.git
cd goat_data_analyst
```

### Step 2: Create Virtual Environment

**Option A: Using venv (Built-in)**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**Option B: Using conda**

```bash
conda create -n goat_data python=3.10
conda activate goat_data
```

### Step 3: Install Core Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install from requirements.txt
pip install -r requirements.txt
```

### Step 4: Install Test Dependencies

```bash
# Install testing tools
pip install pytest>=7.0 pytest-cov>=4.0

# Install data processing libraries
pip install pandas>=1.5 openpyxl>=3.0 pyarrow>=10.0

# Install logging utilities
pip install python-dotenv>=0.20
```

### Step 5: Verify Installation

```bash
# Check Python version
python --version  # Should be 3.8+

# Check pytest installation
pytest --version  # Should be 7.0+

# Check pandas installation
python -c "import pandas; print(f'Pandas {pandas.__version__}')"

# Check pytest-cov installation
python -c "import pytest_cov; print('pytest-cov installed')"
```

**Expected Output:**
```
Python 3.10.x
pytest 7.x.x
Pandas 2.x.x
pytest-cov installed
```

---

## 🧪 Running Tests

### Method 1: Using Test Runner Script (Recommended)

```bash
# Basic run (quiet output)
python tests/run_dataloader_tests.py

# Verbose output
python tests/run_dataloader_tests.py -v

# With coverage report
python tests/run_dataloader_tests.py -c

# Both verbose and coverage
python tests/run_dataloader_tests.py -v -c
```

### Method 2: Using pytest Directly

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_data_loader_workers_a_plus.py -v
pytest tests/test_data_loader_integration.py -v

# Run specific test class
pytest tests/test_data_loader_workers_a_plus.py::TestCSVLoaderWorkerValidation -v

# Run specific test
pytest tests/test_data_loader_workers_a_plus.py::TestCSVLoaderWorkerValidation::test_accepts_valid_csv_file -v
```

### Method 3: With Coverage Report

```bash
# Generate coverage report
pytest tests/ --cov=agents.data_loader.workers --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
firefox htmlcov/index.html  # Linux
```

### Method 4: With Detailed Output

```bash
# Very verbose with full tracebacks
pytest tests/ -vv --tb=long

# Show print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -v -x

# Stop after N failures
pytest tests/ -v --maxfail=3
```

---

## 🐛 Troubleshooting

### Issue 1: Module Not Found Errors

**Problem:**
```
ModuleNotFoundError: No module named 'agents'
```

**Solution:**
```bash
# Make sure you're in the project root
cd goat_data_analyst

# Check directory structure
ls -la agents/  # Should show data_loader directory

# Reinstall package in development mode
pip install -e .

# Or add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # macOS/Linux
set PYTHONPATH=%PYTHONPATH%;%cd%  # Windows
```

### Issue 2: Permission Denied

**Problem:**
```
PermissionError: [Errno 13] Permission denied: '.../test_file.csv'
```

**Solution:**
```bash
# Check file permissions
ls -la tests/data/

# Fix permissions (macOS/Linux)
chmod 755 tests/data/
chmod 644 tests/data/*

# Make sure temp directory is writable
ls -la /tmp  # Check /tmp permissions
```

### Issue 3: Virtual Environment Issues

**Problem:**
```
ERROR: No matching distribution found for package_name
```

**Solution:**
```bash
# Deactivate and remove old venv
deactivate
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# Create fresh venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows

# Upgrade pip and reinstall
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue 4: Pandas/Excel Issues

**Problem:**
```
ImportError: openpyxl is not installed
```

**Solution:**
```bash
# Install Excel support
pip install openpyxl xlrd xlwt

# Or update pandas
pip install --upgrade pandas openpyxl
```

### Issue 5: Parquet Issues

**Problem:**
```
ImportError: pyarrow is not installed
```

**Solution:**
```bash
# Install pyarrow
pip install pyarrow

# Or install fastparquet as alternative
pip install fastparquet
```

### Issue 6: Port Already in Use (if running server)

**Problem:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

---

## ✅ Expected Results

### Successful Test Run

**Output Example:**
```
=============================== test session starts ================================
platform linux -- Python 3.10.x, pytest-7.x.x
cachedir: .pytest_cache
rootdir: /path/to/goat_data_analyst
collected 47 items

tests/test_data_loader_workers_a_plus.py ..............................   [ 68%]
tests/test_data_loader_integration.py ...............                 [ 100%]

=============================== 47 passed in 12.34s ================================
```

### Test Count Breakdown

```
Unit Tests:
  ✓ TestCSVLoaderWorkerValidation: 5 tests
  ✓ TestCSVLoaderWorkerExecution: 5 tests
  ✓ TestValidatorWorkerValidation: 4 tests
  ✓ TestValidatorWorkerExecution: 4 tests
  ✓ TestJSONExcelLoaderWorkerValidation: 3 tests
  ✓ TestJSONExcelLoaderWorkerExecution: 2 tests
  ✓ TestParquetLoaderWorkerValidation: 2 tests
  ✓ TestParquetLoaderWorkerExecution: 1 test
  ✓ TestQualityScoreCalculation: 2 tests
  ✓ TestErrorHandling: 2 tests
  ✓ TestMetadataExtraction: 2 tests
  Total Unit Tests: 32

Integration Tests:
  ✓ TestWorkerCoordination: 3 tests
  ✓ TestErrorIntelligenceTracking: 3 tests
  ✓ TestEndToEndWorkflows: 3 tests
  ✓ TestMultiFormatLoading: 2 tests
  ✓ TestQualityPropagation: 2 tests
  ✓ TestRecoveryStrategies: 2 tests
  Total Integration Tests: 15

Total: 47 tests, 47 passed ✓
```

### Coverage Report Example

```
---------- coverage: platform linux -- Python 3.10 -----------
Name                                          Stmts   Miss  Cover
-----------------------------------------------------------------
agents/data_loader/workers/__init__.py           10      0   100%
agents/data_loader/workers/base_worker.py      250      8    97%
agents/data_loader/workers/csv_loader.py       120      7    94%
agents/data_loader/workers/json_excel_loader.py 140    12    91%
agents/data_loader/workers/parquet_loader.py    95      9    90%
agents/data_loader/workers/validator_worker.py  160     11    93%
-----------------------------------------------------------------
TOTAL                                          775     47    92%
```

---

## 📊 Test Output Interpretation

### Understanding Test Results

**✓ PASSED:**
- Test executed successfully
- All assertions passed
- Expected behavior verified

**✗ FAILED:**
- Test did not pass
- Assertion failed or exception raised
- Check error message for details

**⊘ SKIPPED:**
- Test was skipped (marked with @pytest.mark.skip)
- Conditional test not met

**⚠ WARNING:**
- Test passed but with warnings
- May indicate deprecation or best practice violation

### Reading Error Messages

**Example 1: Assertion Error**
```
AssertionError: assert True == False
  File tests/test_data_loader_workers_a_plus.py, line 45
    assert result.success is True
```
**Interpretation:** Test expected success but got failure

**Example 2: Import Error**
```
ModuleNotFoundError: No module named 'agents.data_loader'
```
**Interpretation:** Python path or installation issue

**Example 3: Type Error**
```
TypeError: CSVLoaderWorker.execute() missing 1 required positional argument: 'file_path'
```
**Interpretation:** Method called with wrong arguments

---

## 🔍 Debugging Tests

### Add Print Statements

```bash
# Run with print output visible
pytest tests/test_file.py -v -s
```

### Debug Single Test

```bash
# Stop at first failure with debugger
pytest tests/test_file.py::TestClass::test_method -v --pdb

# Drop into debugger on failure
pytest tests/test_file.py -v --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Capture Detailed Logs

```bash
# Full traceback
pytest tests/ -v --tb=long

# Show all captured output
pytest tests/ -v -s --capture=no

# Write results to file
pytest tests/ -v --html=report.html
```

---

## 📈 Performance Considerations

### Test Execution Time

**Expected Times:**
- Unit tests: ~100-200ms each
- Integration tests: ~150-300ms each
- Total suite: ~15-20 seconds
- With coverage: ~25-30 seconds

### Optimization Tips

```bash
# Run only fast tests
pytest tests/ -v -m "not slow"

# Run tests in parallel (install pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto  # Use all CPU cores

# Run only failed tests
pytest tests/ --lf  # Last failed
pytest tests/ --ff  # Failed first
```

---

## 📚 Additional Resources

### Documentation Files
- [DATALOADER_IMPROVEMENTS_SUMMARY.md](DATALOADER_IMPROVEMENTS_SUMMARY.md) - Detailed improvements
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Implementation status
- [DATALOADER_PHASE2_COMPLETION_REPORT.txt](DATALOADER_PHASE2_COMPLETION_REPORT.txt) - Completion report

### Test Files
- `tests/test_data_loader_workers_a_plus.py` - Unit tests
- `tests/test_data_loader_integration.py` - Integration tests
- `tests/run_dataloader_tests.py` - Test runner script

### Pytest Documentation
- [pytest.org](https://pytest.org)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io)
- [pytest fixtures guide](https://docs.pytest.org/en/stable/fixture.html)

---

## 🆘 Still Having Issues?

### Checklist

- [ ] Python version is 3.8+ (`python --version`)
- [ ] Virtual environment is activated (check terminal prompt)
- [ ] All dependencies installed (`pip list | grep pytest`)
- [ ] Project root is current directory (`pwd`)
- [ ] PYTHONPATH includes project root (`echo $PYTHONPATH`)
- [ ] Test files exist (`ls tests/`)
- [ ] No syntax errors in code (`python -m py_compile agents/data_loader/workers/*.py`)

### Get More Help

1. Check error messages carefully - they usually indicate the problem
2. Verify installation with `pip list`
3. Try fresh virtual environment
4. Check file permissions
5. Look at test file docstrings for test details
6. Run single test with maximum verbosity: `pytest test_file.py::test_name -vv -s`

---

## 📝 Common Commands Reference

```bash
# Basic operations
python tests/run_dataloader_tests.py              # Run all tests
pytest tests/ -v                                  # Verbose output
pytest tests/ -k "CSV"                            # Run specific tests
pytest tests/ --collect-only                      # List all tests

# Coverage
pytest tests/ --cov --cov-report=html             # HTML report
pytest tests/ --cov --cov-report=term-missing     # Terminal report

# Debugging
pytest tests/ -v -s                               # Show print output
pytest tests/ -v --pdb                            # Drop into debugger
pytest tests/ -v -x                               # Stop on first failure

# Performance
pytest tests/ -n auto                             # Parallel execution
pytest tests/ --benchmark                         # Performance testing
pytest tests/ --profile                           # Memory profiling

# Filtering
pytest tests/ -m "unit"                           # Run marked tests
pytest tests/ --ignore=test_file.py               # Exclude file
pytest tests/ -k "not slow"                       # Exclude by pattern
```

---

**Last Updated:** December 12, 2025 @ 16:00 EET  
**Status:** Ready for Local Testing ✅
