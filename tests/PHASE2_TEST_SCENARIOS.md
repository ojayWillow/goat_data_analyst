# 🧪 PHASE 2 TEST SCENARIOS

**Purpose:** Define what we're testing in Week 2  
**Status:** Ready for execution  
**Date:** December 10, 2025

---

## SCENARIO 1: Happy Path (Normal Operation)

**What:** Test all 8 agents with clean, normal data

**Input Data:**
- File: `tests/data/small_dataset.csv`
- Rows: 2,000
- Columns: 10 (mixed numeric, categorical, dates)
- Quality: Clean (no missing values, no outliers)
- Size: <1MB

**What Each Agent Tests:**

### DataLoader
```
Task: Load CSV file
Input: tests/data/small_dataset.csv
Expected Output:
  - pandas DataFrame loaded
  - Shape: (2000, 10)
  - All columns readable
  - No exceptions
  
Success Criteria:
  ✓ Returns DataFrame
  ✓ No errors
  ✓ Structured log shows load event
  ✓ Completes in <2 seconds
```

### Explorer
```
Task: Analyze data structure and statistics
Input: DataFrame from DataLoader
Expected Output:
  - Column statistics (mean, median, std, etc)
  - Data types identified
  - Missing value report
  - Basic correlations
  
Success Criteria:
  ✓ Returns analysis dict
  ✓ Contains expected keys
  ✓ Structured logging captured
  ✓ Completes in <5 seconds
```

### Aggregator
```
Task: Group and aggregate data
Input: DataFrame, groupby column='category_1', agg_col='value_1', agg='mean'
Expected Output:
  - Aggregated results grouped by category
  - Summary statistics
  
Success Criteria:
  ✓ Returns aggregated DataFrame
  ✓ Groups created correctly
  ✓ Aggregation completed
  ✓ Completes in <5 seconds
```

### Predictor
```
Task: Make predictions on data
Input: DataFrame with features
Expected Output:
  - Prediction values
  - Model information
  
Success Criteria:
  ✓ Returns predictions
  ✓ No errors
  ✓ Predictions are numeric
  ✓ Completes in <10 seconds
```

### AnomalyDetector
```
Task: Detect anomalies in data
Input: DataFrame
Expected Output:
  - Anomaly flags (0 or 1)
  - Anomaly scores
  - Threshold used
  
Success Criteria:
  ✓ Returns anomaly results
  ✓ No exceptions
  ✓ Results make sense
  ✓ Completes in <10 seconds
```

### Recommender
```
Task: Generate recommendations based on analysis
Input: Analysis results from Explorer
Expected Output:
  - List of actionable recommendations
  - Priority/severity
  
Success Criteria:
  ✓ Returns recommendation list
  ✓ Recommendations are meaningful
  ✓ Logged correctly
  ✓ Completes in <5 seconds
```

### Reporter
```
Task: Generate report from analysis
Input: All analysis results
Expected Output:
  - Report dict (JSON-serializable)
  - Executive summary
  - Detailed findings
  
Success Criteria:
  ✓ Returns report dict
  ✓ Report contains expected sections
  ✓ JSON-serializable
  ✓ Completes in <5 seconds
```

### Visualizer
```
Task: Create visualizations
Input: DataFrame
Expected Output:
  - Plot files created
  - Chart objects
  
Success Criteria:
  ✓ Charts generated
  ✓ Files saved
  ✓ No rendering errors
  ✓ Completes in <10 seconds
```

---

## SCENARIO 2: Edge Cases (Data Quality Issues)

**What:** Test agents with real-world messy data

**Input Data:**
- File: `tests/data/medium_dataset.csv`
- Rows: 100,000
- Columns: 15 (mixed types)
- Quality Issues:
  - Missing values (10-20% of some columns)
  - Duplicate rows (1-2%)
  - Outliers (1% extreme values)
  - Mixed data types (some inconsistencies)

**What We're Testing:**

### Agents Handle Missing Data
```
Test: Does agent handle NaN values gracefully?
Expected:
  ✓ No crashes
  ✓ Error logged if column critical
  ✓ Reasonable handling (skip, interpolate, or remove)
```

### Agents Handle Duplicates
```
Test: Does agent handle duplicate rows?
Expected:
  ✓ Identifies duplicates
  ✓ Handles appropriately
  ✓ Logged in structured logs
```

### Agents Handle Outliers
```
Test: Does agent handle extreme values?
Expected:
  ✓ Identifies outliers
  ✓ Doesn't crash
  ✓ May flag as anomalies
```

### Agents Handle Scale Differences
```
Test: Columns with different scales/ranges?
Expected:
  ✓ Normalizes if needed
  ✓ Results reasonable
  ✓ Properly logged
```

### Agents Handle Empty Groups
```
Test: What if groupby creates empty groups?
Expected:
  ✓ Handles gracefully
  ✓ Skips or marks as 0/null
  ✓ No crashes
```

**Success Criteria for Scenario 2:**
```
✓ All agents complete without unhandled exceptions
✓ Errors logged clearly
✓ Results are reasonable despite data quality issues
✓ Agents handle missing values appropriately
✓ No silent failures (all issues logged)
✓ Completes in <60 seconds total for all agents
```

---

## SCENARIO 3: Stress Test (Large Data)

**What:** Test agents with large dataset to check performance

**Input Data:**
- File: `tests/data/medium_dataset.csv` (same as Scenario 2)
- Rows: 100,000
- Columns: 15
- Total Size: ~20-30MB (loaded in memory)

**What We're Testing:**

### Performance Under Load
```
Test: Do agents complete in reasonable time?
Expected:
  ✓ DataLoader: <5 seconds
  ✓ Explorer: <10 seconds
  ✓ Aggregator: <10 seconds
  ✓ Predictor: <20 seconds
  ✓ AnomalyDetector: <20 seconds
  ✓ Reporter: <10 seconds
  ✓ Visualizer: <15 seconds
```

### Memory Usage
```
Test: Memory stays reasonable?
Expected:
  ✓ No memory leaks (peak reasonable)
  ✓ Memory released after operation
  ✓ No excessive swapping
```

### CPU Usage
```
Test: CPU usage reasonable?
Expected:
  ✓ Operations complete efficiently
  ✓ No hanging/blocking
  ✓ All cores utilized appropriately
```

### Logging Overhead
```
Test: Logging doesn't slow things down significantly?
Expected:
  ✓ <5% performance overhead
  ✓ Logging doesn't block operations
  ✓ Structured logs captured
```

**Success Criteria for Scenario 3:**
```
✓ All agents complete under 2 minutes total
✓ Individual agents meet performance targets
✓ Memory usage stays under 2GB
✓ No timeouts or hangs
✓ Logging captures all operations
```

---

## TEST EXECUTION ORDER

### Day 1 (Dec 11) Morning
1. Create test data files
2. Verify test data created correctly
3. Run Scenario 1 (Happy Path)
   - Quick smoke test of all agents
   - Verify basic functionality
   - Check structured logging works

### Day 1 Afternoon
4. Run Scenario 2 (Edge Cases)
   - Test error handling
   - Verify graceful degradation
   - Check error messages clear

### Day 2 (Dec 12) Morning
5. Run Scenario 3 (Stress Test)
   - Measure performance
   - Capture benchmarks
   - Identify bottlenecks

---

## PASS/FAIL CRITERIA

### Scenario 1 (Happy Path) - MUST PASS
```
✓ All 8 agents execute successfully
✓ No unhandled exceptions
✓ Results are meaningful
✓ Structured logging works

If FAILS: Block further testing until fixed
```

### Scenario 2 (Edge Cases) - SHOULD PASS
```
✓ Agents handle data quality issues
✓ Clear error messages logged
✓ Graceful handling of problems

If FAILS: Document as limitation, continue testing
```

### Scenario 3 (Stress Test) - SHOULD PASS
```
✓ Performance meets targets
✓ No memory leaks
✓ Agents scale to 100K rows

If FAILS: Document performance limits, plan optimization
```

---

## TEST DATA LOCATIONS

```
tests/
├── data/
│   ├── small_dataset.csv (2,000 rows, clean)
│   ├── medium_dataset.csv (100,000 rows, with issues)
│   ├── test_data.json (5,000 records)
│   └── test_data.xlsx (5,000 rows)
├── logs/
│   └── [test results will be saved here]
├── PHASE2_TEST_SCENARIOS.md (this file)
├── PHASE2_SUCCESS_CRITERIA.md (detailed criteria)
└── run_phase2_tests.py (test runner script)
```

---

**Next Step:** Create PHASE2_SUCCESS_CRITERIA.md with detailed criteria for each agent.
