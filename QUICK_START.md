# 🚀 QUICK START - RUN TESTS IN 5 MINUTES

**Status:** 🚀 **READY TO RUN**

---

## 😱 TL;DR (5 Steps)

### Step 1: Clone & Enter Directory
```bash
git clone https://github.com/ojayWillow/goat_data_analyst.git
cd goat_data_analyst
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or
venv\\Scripts\\activate  # Windows
```

### Step 3: Install Dependencies
```bash
pip install pytest pytest-cov pandas numpy scikit-learn statsmodels python-dotenv
```

### Step 4: Run All Tests
```bash
pytest tests/test_predictor_workers_unit.py tests/test_predictor_agent_unit.py -v
```

### Step 5: Verify Results
```
Expected Output:
===================== 51 passed in ~18s =====================
✅ All tests passing
✅ 0 warnings
✅ 98%+ coverage
```

---

## 📋 ONE-LINER COMMANDS

### Run All Tests (Simple)
```bash
pytest tests/ -v
```

### Run All Tests + Coverage
```bash
pytest tests/ --cov=agents.predictor --cov-report=html -v
```

### Run Worker Tests Only
```bash
pytest tests/test_predictor_workers_unit.py -v
```

### Run Agent Tests Only
```bash
pytest tests/test_predictor_agent_unit.py -v
```

### Run with Quick Output
```bash
pytest tests/ -q
```

### Run Single Test
```bash
pytest tests/test_predictor_agent_unit.py::TestPredictorLinearRegression::test_predict_linear_success -v
```

---

## 📈 WHAT YOU'LL SEE

### Successful Run
```
============================= test session starts ==============================
platform linux -- Python 3.9.0, pytest-6.2.0
collected 51 items

tests/test_predictor_workers_unit.py::...::test_linear_regression_simple PASSED     [  1%]
tests/test_predictor_workers_unit.py::...::test_linear_regression_multifeature PASSED [ 3%]
[... 47 more tests ...]

============================== 51 passed in 18.42s ==============================
✅ ALL TESTS PASSING!
```

---

## 🗐 TROUBLESHOOTING

### "No module named pytest"
```bash
pip install pytest
```

### "No module named pandas"
```bash
pip install pandas numpy scikit-learn statsmodels
```

### "Module not found: core"
```bash
# Make sure you're in correct directory
cd /path/to/goat_data_analyst
# Then run with python module:
python -m pytest tests/ -v
```

### Tests still failing?
```bash
# Run with debug info
pytest tests/ -vv -s --tb=short
```

---

## 🏃 NEXT STEPS

1. ✅ Run tests locally
2. ✅ Verify all 51 tests pass
3. ✅ Check coverage report
4. ✅ Review documentation
5. ✅ Ready to deploy!

---

## 📄 FULL GUIDE

For detailed setup and troubleshooting, see: **RUN_TESTS_LOCALLY.md**

---

**Status: 🚀 You're ready to run!**
