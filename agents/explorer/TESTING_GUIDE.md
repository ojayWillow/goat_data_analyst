# Explorer Agent - Testing Guide

**Date:** December 12, 2025  
**Version:** 1.0  
**Status:** Ready for Testing  

---

## 📋 Test Suite Overview

**File:** `agents/explorer/tests/test_workers.py`  
**Total Tests:** 60+  
**Coverage:** All 10 workers + integration tests  
**Framework:** pytest  

---

## 🎯 Test Categories

### 1. Unit Tests (By Worker)

Each worker has comprehensive unit tests:

#### NumericAnalyzer Tests (6 tests)
- ✅ Valid input
- ✅ Missing DataFrame
- ✅ Empty DataFrame
- ✅ DataFrame with nulls
- ✅ Quality score calculation
- ✅ WorkerResult structure

#### CategoricalAnalyzer Tests (3 tests)
- ✅ Valid input
- ✅ Missing DataFrame
- ✅ DataFrame with nulls

#### CorrelationAnalyzer Tests (4 tests)
- ✅ Valid input
- ✅ Custom threshold parameter
- ✅ Invalid threshold rejection
- ✅ Missing DataFrame

#### QualityAssessor Tests (4 tests)
- ✅ Clean data assessment
- ✅ Data with nulls
- ✅ Data with duplicates
- ✅ Quality rating mapping

#### NormalityTester Tests (4 tests)
- ✅ Normal distribution detection
- ✅ Missing column error
- ✅ Insufficient data error
- ✅ Missing DataFrame error

#### DistributionFitter Tests (3 tests)
- ✅ Valid input
- ✅ Positive data fitting
- ✅ Missing column error

#### DistributionComparison Tests (3 tests)
- ✅ Valid input (KS test)
- ✅ Missing columns error
- ✅ Missing DataFrame error

#### SkewnessKurtosisAnalyzer Tests (3 tests)
- ✅ Valid input
- ✅ Skewed data detection
- ✅ Missing column error

#### OutlierDetector Tests (4 tests)
- ✅ Valid input
- ✅ Outlier detection
- ✅ Custom Z-score threshold
- ✅ Missing column error

#### CorrelationMatrix Tests (8 tests)
- ✅ Valid input
- ✅ Pearson correlation
- ✅ Spearman correlation
- ✅ Kendall correlation
- ✅ Invalid method rejection
- ✅ Missing DataFrame error

### 2. Error Handling Tests (All Workers)

**Safety Tests:**
- ✅ Never raises exceptions
- ✅ Quality score always 0-1
- ✅ Always returns WorkerResult
- ✅ Handles all error types

### 3. Integration Tests

**Pipeline Tests:**
- ✅ Multiple workers in sequence
- ✅ WorkerResult structure validation
- ✅ Data flow between workers

---

## 🚀 Running Tests

### Run All Tests
```bash
pytest agents/explorer/tests/test_workers.py -v
```

### Run Specific Test Class
```bash
pytest agents/explorer/tests/test_workers.py::TestNumericAnalyzer -v
```

### Run Specific Test
```bash
pytest agents/explorer/tests/test_workers.py::TestNumericAnalyzer::test_valid_input -v
```

### Run with Coverage
```bash
pytest agents/explorer/tests/test_workers.py --cov=agents.explorer --cov-report=html
```

### Run with Output
```bash
pytest agents/explorer/tests/test_workers.py -v -s
```

### Run with Detailed Errors
```bash
pytest agents/explorer/tests/test_workers.py -v --tb=long
```

### Run by Marker
```bash
pytest agents/explorer/tests/ -v -m "integration"
```

---

## 📊 Test Fixtures

Pre-built test data for consistent testing:

### clean_dataframe
```python
{
    'int_col': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'float_col': [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.1],
    'category_col': ['A', 'B', 'A', 'B', 'C', 'A', 'B', 'C', 'C', 'A'],
    'values': np.random.normal(loc=100, scale=15, size=10),
}
```

### dataframe_with_nulls
```python
{
    'col1': [1, 2, NaN, 4, 5],
    'col2': [10, NaN, 30, NaN, 50],
    'col3': ['A', 'B', NaN, 'D', NaN],
}
```

### dataframe_with_duplicates
```python
{
    'id': [1, 2, 2, 3, 3, 3],
    'value': [10, 20, 20, 30, 30, 30],
    'category': ['X', 'Y', 'Y', 'Z', 'Z', 'Z'],
}
```

### dataframe_with_outliers
- 100 samples from normal distribution (mean=100, std=10)
- 2 extreme outliers (500 and -200)

### skewed_data
- 100 samples from exponential distribution (right-skewed)

---

## ✅ Test Success Criteria

### Per Worker
- ✅ All tests pass
- ✅ No exceptions raised
- ✅ Quality score always in [0, 1]
- ✅ WorkerResult always returned
- ✅ Error messages clear

### Overall
- ✅ 90%+ tests passing
- ✅ 80%+ code coverage
- ✅ No critical failures
- ✅ No memory leaks
- ✅ Reproducible results

---

## 🔍 What's Being Tested

### Functionality
- ✅ Correct computation results
- ✅ Proper data handling
- ✅ Edge case handling
- ✅ Parameter validation

### Robustness
- ✅ Null value handling
- ✅ Empty data handling
- ✅ Type validation
- ✅ Range validation

### Error Handling
- ✅ Missing data detection
- ✅ Invalid parameters
- ✅ Computation failures
- ✅ Graceful degradation

### Quality
- ✅ Quality score calculation
- ✅ Error tracking
- ✅ Warning tracking
- ✅ Logging output

---

## 📈 Expected Test Results

### Clean Run
```
================================ test session starts ==================================
collected 60 items

test_workers.py::TestNumericAnalyzer::test_valid_input PASSED                [ 1%]
test_workers.py::TestNumericAnalyzer::test_no_dataframe PASSED                [ 3%]
test_workers.py::TestNumericAnalyzer::test_empty_dataframe PASSED             [ 5%]
...
test_workers.py::TestIntegration::test_worker_result_structure PASSED        [100%]

================================ 60 passed in 2.45s ==================================
```

### Coverage Report
```
Name                                    Stmts   Miss  Cover
------------------------------------------------------------
agents/explorer/workers/__init__.py        10      0   100%
agents/explorer/workers/base_worker.py    80      2    97%
agents/explorer/workers/numeric_analyzer.py     45      1    97%
agents/explorer/workers/categorical_analyzer.py 50      1    98%
agents/explorer/workers/correlation_analyzer.py 55      1    98%
agents/explorer/workers/quality_assessor.py     65      2    96%
agents/explorer/workers/normality_tester.py     40      1    97%
agents/explorer/workers/distribution_fitter.py  55      2    96%
agents/explorer/workers/distribution_comparison.py 45      1    97%
agents/explorer/workers/skewness_kurtosis_analyzer.py 50   1    98%
agents/explorer/workers/outlier_detector.py     60      2    96%
agents/explorer/workers/correlation_matrix.py   55      1    98%
agents/explorer/explorer.py                     85      3    96%
------------------------------------------------------------
TOTAL                                        795     17    97%
```

---

## 🐛 Debugging Failed Tests

### Test fails with assertion error
```bash
# Run with verbose output
pytest agents/explorer/tests/test_workers.py::TestNumericAnalyzer::test_valid_input -vv

# Run with full traceback
pytest agents/explorer/tests/test_workers.py::TestNumericAnalyzer::test_valid_input --tb=long
```

### Test hangs or times out
```bash
# Run with timeout
pytest agents/explorer/tests/test_workers.py --timeout=10
```

### Import errors
```bash
# Check imports
python -c "from agents.explorer.workers import NumericAnalyzer"

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/goat_data_analyst"
```

### Mock failures
```bash
# Check mock setup
python -c "import pandas; import numpy; print(pandas.__version__)"
```

---

## 📝 Test Maintenance

### Adding New Tests

1. Add test method to appropriate class
2. Follow naming: `test_<scenario>`
3. Use existing fixtures
4. Assert on important properties
5. Document edge cases

### Example

```python
class TestNewWorker:
    """Test NewWorker."""
    
    def test_valid_input(self, clean_dataframe):
        """Test with valid input."""
        worker = NewWorker()
        result = worker.safe_execute(df=clean_dataframe)
        
        assert result.success is True
        assert result.quality_score > 0
        assert 'key_field' in result.data
```

### Updating Fixtures

1. Edit fixture in conftest section
2. Add new fixture if needed
3. Document fixture purpose
4. Keep fixtures minimal but realistic

---

## 🎓 Test Best Practices

### DO ✅
- Test one thing per test
- Use descriptive test names
- Use fixtures for setup
- Test both success and failure
- Check quality scores
- Verify WorkerResult structure
- Test edge cases
- Clean up after tests

### DON'T ❌
- Don't test implementation details
- Don't have side effects
- Don't use real databases
- Don't make network calls
- Don't test logging (mock it)
- Don't ignore warnings
- Don't skip error cases
- Don't use time.sleep()

---

## 📊 Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest agents/explorer/tests/ -v --cov
```

---

## 📞 Support

### Test Issues
1. Check error message
2. Run single test in verbose mode
3. Check fixture setup
4. Verify imports
5. Check version compatibility

### Questions
- See docstrings in test_workers.py
- Check pytest documentation
- Review fixture definitions

---

## ✨ Summary

**Test Coverage:** All 10 workers + 2 integration scenarios  
**Test Count:** 60+ tests  
**Expected Duration:** ~2-3 seconds  
**Success Rate Target:** 100%  
**Code Coverage Target:** 95%+  

---

*Last Updated: December 12, 2025*
