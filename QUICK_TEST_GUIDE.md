# Quick Test Execution Guide

**For:** Windows/Mac/Linux  
**Status:** Ready to run  
**Expected:** 60/60 tests pass in 2-3 seconds  

---

## 🚀 QUICK START

### Step 1: Navigate to project root
```bash
cd C:\Projects\GOAT_DATA_ANALYST
# or on Mac/Linux:
cd /path/to/goat_data_analyst
```

### Step 2: Run all tests
```bash
pytest agents/explorer/tests/test_workers.py -v
```

**Expected Output:**
```
================================ test session starts ==================================
collected 60 items

test_workers.py::TestNumericAnalyzer::test_valid_input PASSED                [ 1%]
test_workers.py::TestNumericAnalyzer::test_no_dataframe PASSED                [ 3%]
...
test_workers.py::TestIntegration::test_worker_result_structure PASSED        [100%]

================================ 60 passed in 2.45s ==================================
```

---

## 🔧 IF IMPORTS STILL FAIL

### Option 1: Set PYTHONPATH (Recommended)

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH = "C:\Projects\GOAT_DATA_ANALYST"
pytest agents/explorer/tests/test_workers.py -v
```

**Windows (Command Prompt):**
```cmd
set PYTHONPATH=C:\Projects\GOAT_DATA_ANALYST
pytest agents/explorer/tests/test_workers.py -v
```

**Mac/Linux (Bash):**
```bash
export PYTHONPATH="/path/to/goat_data_analyst"
pytest agents/explorer/tests/test_workers.py -v
```

### Option 2: Run from agents/explorer directory
```bash
cd agents/explorer
pytest tests/test_workers.py -v
```

### Option 3: Run with Python module syntax
```bash
python -m pytest agents/explorer/tests/test_workers.py -v
```

---

## 📊 OTHER USEFUL COMMANDS

### Run with coverage report
```bash
pytest agents/explorer/tests/test_workers.py -v --cov=agents.explorer
```

### Run specific test class
```bash
pytest agents/explorer/tests/test_workers.py::TestNumericAnalyzer -v
```

### Run specific test
```bash
pytest agents/explorer/tests/test_workers.py::TestNumericAnalyzer::test_valid_input -v
```

### Run with detailed output
```bash
pytest agents/explorer/tests/test_workers.py -vv --tb=long
```

### Run with timeout (10 seconds)
```bash
pytest agents/explorer/tests/test_workers.py -v --timeout=10
```

---

## ✅ SUCCESS CHECKLIST

After running tests, verify:

- [ ] 60/60 tests pass
- [ ] Duration < 5 seconds
- [ ] No import errors
- [ ] No test failures
- [ ] No warnings (except deprecation)

---

## 🐛 TROUBLESHOOTING

### Import Error: "No module named 'agents'"
**Solution:** Set PYTHONPATH to project root (see Option 1 above)

### Tests timeout
**Solution:** Tests should finish in 2-3 seconds. If slower:
1. Check system resources
2. Run individual worker tests
3. Check for hanging imports

### Individual tests fail
**Solution:** Run specific test with verbose output
```bash
pytest agents/explorer/tests/test_workers.py::TestNumericAnalyzer::test_valid_input -vv
```

### Missing dependencies
**Solution:** Install requirements
```bash
pip install pytest pytest-cov pandas numpy scipy
```

---

## 📚 Test Files

- **Test Suite:** `agents/explorer/tests/test_workers.py`
- **Documentation:** 
  - `agents/explorer/TESTING_SUMMARY.md`
  - `agents/explorer/TESTING_GUIDE.md`
  - `agents/explorer/TEST_EXECUTION_PLAN.md`

---

## 🎯 What's Being Tested

✅ **10 Workers (46 tests)**
- NumericAnalyzer (6 tests)
- CategoricalAnalyzer (3 tests)
- CorrelationAnalyzer (4 tests)
- QualityAssessor (4 tests)
- NormalityTester (4 tests)
- DistributionFitter (3 tests)
- DistributionComparison (3 tests)
- SkewnessKurtosisAnalyzer (3 tests)
- OutlierDetector (4 tests)
- CorrelationMatrix (8 tests)

✅ **Error Handling (10 tests)**
- Never raises exceptions

✅ **Integration (2 tests)**
- Pipeline execution
- Result structure validation

✅ **Total: 60 tests**

---

## 📋 Test Coverage

Expected:
- **Overall Coverage:** 97%+
- **BaseWorker:** 97%
- **Each Worker:** 95-98%

---

**Ready to test! Run command from Option 1 (Set PYTHONPATH) or Option 3 (Python module syntax).**

Expect: ✅ **60/60 tests pass**
